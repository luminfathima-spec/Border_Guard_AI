import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.services.edge.network_controller import NetworkState

class NetworkStateUpdateRequest(BaseModel):
    state: NetworkState = Field(..., description="Target network state (ONLINE, OFFLINE, DEGRADED)")
    reason: Optional[str] = Field(None, description="Operational justification or drill identifier")

class SyncTriggerRequest(BaseModel):
    batch_size: Optional[int] = Field(50, ge=1, le=500, description="Maximum events to sync in this batch")
    force_sync: bool = Field(False, description="Attempt sync even if marked offline")

class BufferStatsResponse(BaseModel):
    total_buffered_events: int
    pending_sync_count: int
    synced_count: int
    quarantined_count: int
    pending_evidence_count: int
    oldest_pending_timestamp: Optional[str] = None
    db_file_size_bytes: int

class DiskMetricsResponse(BaseModel):
    total_bytes: int
    free_bytes: int
    used_bytes: int
    used_percent: float
    buffer_size_bytes: int
    buffer_size_mb: float
    max_quota_mb: float
    quota_utilization_percent: float
    is_warning: bool
    is_quota_breached: bool

class EdgeStatusResponse(BaseModel):
    edge_node_id: str
    network_state: NetworkState
    last_state_change: datetime.datetime
    offline_reason: Optional[str] = None
    buffer_stats: BufferStatsResponse
    disk_metrics: DiskMetricsResponse

class SyncResponse(BaseModel):
    session_id: str
    status: str
    events_synced: int
    evidence_synced: int = 0
    duplicates_prevented: int = 0
    conflicts_resolved: int = 0
    bytes_transferred: int = 0
    duration_ms: int
    errors_count: int = 0
    remaining_pending: int = 0
    message: Optional[str] = None

class PurgeResponse(BaseModel):
    files_deleted: int
    bytes_freed: int
    bytes_freed_mb: float
    remaining_buffer_mb: float
    status: str

class BufferedEventItem(BaseModel):
    id: int
    client_event_id: str
    event_type: str
    severity: str
    camera_id: Optional[int] = None
    video_id: Optional[int] = None
    detected_at: str
    description: str
    confidence: float
    metadata_json: Dict[str, Any]
    snapshot_path: Optional[str] = None
    clip_path: Optional[str] = None
    edge_node_id: Optional[str] = None
    status: str
    retry_count: int
    next_retry_at: Optional[str] = None
    last_error: Optional[str] = None
    created_at: str

class EdgeBenchmarkRequest(BaseModel):
    num_events: int = Field(20, ge=5, le=200, description="Number of events to generate during blackout")
    simulate_restart: bool = Field(True, description="Simulate application restart before sync")

class EdgeBenchmarkResponse(BaseModel):
    test_name: str
    total_events_generated: int
    events_recovered: int
    event_loss_pct: float
    duplicate_events_prevented: int
    duplicate_detection_accuracy_pct: float
    recovery_time_ms: int
    mean_sync_delay_ms: float
    timestamp_preservation_accuracy_pct: float
    evidence_hash_match_pct: float
    buffer_db_size_bytes: int
    status: str
