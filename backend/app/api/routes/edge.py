from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.core.config import settings
from app.schemas.edge import (
    NetworkStateUpdateRequest,
    SyncTriggerRequest,
    BufferStatsResponse,
    DiskMetricsResponse,
    EdgeStatusResponse,
    SyncResponse,
    PurgeResponse,
    BufferedEventItem,
    EdgeBenchmarkRequest,
    EdgeBenchmarkResponse,
)
from app.services.edge.network_controller import NetworkStateController
from app.services.edge.edge_buffer import EdgeEventBuffer
from app.services.edge.storage_manager import EdgeStorageManager
from app.services.edge.sync_engine import StoreAndForwardSyncEngine
from app.ai.edge_eval.benchmark import EdgeBenchmark

router = APIRouter(prefix="/edge", tags=["Edge Store-and-Forward"])

def _build_status_response() -> EdgeStatusResponse:
    buffer_stats = EdgeEventBuffer.get_buffer_stats()
    disk_metrics = EdgeStorageManager.get_disk_metrics()
    return EdgeStatusResponse(
        edge_node_id=settings.EDGE_NODE_ID,
        network_state=NetworkStateController.get_state(),
        last_state_change=NetworkStateController.get_last_state_change(),
        offline_reason=NetworkStateController.get_offline_reason(),
        buffer_stats=BufferStatsResponse(**buffer_stats),
        disk_metrics=DiskMetricsResponse(**disk_metrics),
    )

@router.get("/status", response_model=EdgeStatusResponse)
def get_edge_status(
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns live edge node telemetry, network connectivity state,
    local SQLite buffer statistics, and disk quota consumption metrics.
    """
    return _build_status_response()

@router.post("/network-state", response_model=EdgeStatusResponse)
def update_network_state(
    req: NetworkStateUpdateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Toggles the simulated edge network state (ONLINE, OFFLINE, DEGRADED)
    for disconnected edge operations, network blackout testing, and drills.
    """
    NetworkStateController.set_state(req.state, reason=req.reason)
    return _build_status_response()

@router.post("/sync", response_model=SyncResponse)
def trigger_synchronization(
    req: SyncTriggerRequest = SyncTriggerRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Triggers store-and-forward reconciliation of pending buffered edge events
    to the central surveillance database with duplicate prevention and zero temporal skew.
    """
    result = StoreAndForwardSyncEngine.sync_pending_records(
        db=db,
        batch_size=req.batch_size,
        force_sync=req.force_sync,
    )
    return SyncResponse(**result)

@router.get("/buffer/events", response_model=List[BufferedEventItem])
def get_buffered_events(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves pending buffered events directly from the local edge SQLite store.
    """
    raw_events = EdgeEventBuffer.get_pending_events(limit=limit)
    return [BufferedEventItem(**ev) for ev in raw_events]

@router.post("/buffer/purge", response_model=PurgeResponse)
def purge_edge_buffer(
    current_user: User = Depends(get_current_active_user),
):
    """
    Enforces the edge storage retention policy and priority pruning:
    deletes expired low-priority snapshots while protecting critical breach media.
    """
    result = EdgeStorageManager.enforce_retention()
    return PurgeResponse(**result)

@router.post("/benchmark", response_model=EdgeBenchmarkResponse)
def run_edge_recovery_benchmark(
    req: EdgeBenchmarkRequest = EdgeBenchmarkRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Executes an empirical edge blackout, crash-restart, and reconciliation benchmark.
    Measures recovery time, sync delay, duplicate prevention accuracy, and event loss rate.
    """
    try:
        return EdgeBenchmark.run_benchmark(
            db=db,
            num_events=req.num_events,
            simulate_restart=req.simulate_restart,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Edge recovery benchmark failed: {e}",
        )
