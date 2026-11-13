import os
import uuid
import pytest
import datetime
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.camera import Camera, CameraStatus
from app.models.incident import Incident, IncidentStatus
from app.models.event import SecurityEvent, EventType, SeverityLevel
from app.models.evidence import Evidence, EvidenceType
from app.models.user import User, UserRole
from app.models.ai_analysis import AIAnalysis, AnalysisStatus
from app.services.edge.network_controller import NetworkStateController, NetworkState
from app.services.edge.edge_buffer import EdgeEventBuffer
from app.services.edge.storage_manager import EdgeStorageManager
from app.services.edge.sync_engine import StoreAndForwardSyncEngine
from app.services.gemini_service import GeminiService
from app.ai.edge_eval.benchmark import EdgeBenchmark
from app.core.config import settings

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def clean_edge_buffer():
    """Ensures each test operates on an isolated SQLite buffer."""
    EdgeEventBuffer.clear_all()
    NetworkStateController.reset()
    yield
    EdgeEventBuffer.clear_all()
    NetworkStateController.reset()

@pytest.fixture
def test_setup(db_session: Session):
    # Ensure test user
    user = db_session.query(User).filter(User.email == "edge_operator@sentinel.ai").first()
    if not user:
        user = User(
            name="Edge Operator",
            email="edge_operator@sentinel.ai",
            password_hash="mockhash_edge",
            role=UserRole.ADMIN.value,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    # Ensure test camera
    cam = db_session.query(Camera).filter(Camera.name == "Edge Sector 01 Sensor").first()
    if not cam:
        cam = Camera(
            name="Edge Sector 01 Sensor",
            camera_identifier="CAM-EDGE-01",
            location="Perimeter Tower East",
            stream_url="rtsp://localhost:8554/edge1",
            status=CameraStatus.ONLINE.value,
            zone="Sector 1",
        )
        db_session.add(cam)
        db_session.commit()
        db_session.refresh(cam)

    return {"user": user, "camera": cam}

def test_offline_event_buffering(db_session: Session, test_setup):
    """Verify events generated during network outage are buffered in SQLite and not in central DB."""
    NetworkStateController.set_state(NetworkState.OFFLINE, reason="Unit test blackout")
    client_event_id = f"test-offline-{uuid.uuid4().hex[:8]}"
    detected_at = datetime.datetime.now(datetime.timezone.utc)

    try:
        # Buffer event locally
        row_id = EdgeEventBuffer.buffer_event(
            client_event_id=client_event_id,
            event_type="VIRTUAL_FENCE_BREACH",
            severity="HIGH",
            camera_id=test_setup["camera"].id,
            video_id=None,
            detected_at=detected_at,
            description="Offline perimeter breach",
            confidence=0.92,
        )
        assert row_id > 0

        # Verify present in SQLite buffer
        stats = EdgeEventBuffer.get_buffer_stats()
        assert stats["pending_sync_count"] >= 1

        # Verify NOT present in central database
        central_rec = db_session.query(SecurityEvent).filter(SecurityEvent.client_event_id == client_event_id).first()
        assert central_rec is None

        # Attempt normal sync while offline -> should skip
        sync_res = StoreAndForwardSyncEngine.sync_pending_records(db=db_session, force_sync=False)
        assert sync_res["status"] == "SKIPPED_OFFLINE"

    finally:
        NetworkStateController.reset()

def test_process_restart_persistence(db_session: Session):
    """Verify that EdgeEventBuffer retains records across process restart (closing and reopening SQLite WAL)."""
    client_event_id = f"test-restart-{uuid.uuid4().hex[:8]}"
    detected_at = datetime.datetime.now(datetime.timezone.utc)

    # Buffer event
    EdgeEventBuffer.buffer_event(
        client_event_id=client_event_id,
        event_type="LOITERING_DETECTED",
        severity="MEDIUM",
        camera_id=1,
        video_id=None,
        detected_at=detected_at,
        description="Persistent loitering record",
        confidence=0.88,
    )

    # Simulate cold crash and reboot
    EdgeEventBuffer.restart()

    # Verify event persists
    pending = EdgeEventBuffer.get_pending_events(limit=200)
    found = any(e["client_event_id"] == client_event_id for e in pending)
    assert found is True

def test_timestamp_and_id_preservation(db_session: Session, test_setup):
    """Verify detected_at and client_event_id are preserved identically upon sync (zero temporal skew)."""
    NetworkStateController.reset()
    client_event_id = f"test-skew-{uuid.uuid4().hex[:8]}"
    # Specific known historical timestamp
    historical_detected_at = datetime.datetime(2026, 9, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)

    EdgeEventBuffer.buffer_event(
        client_event_id=client_event_id,
        event_type="PERIMETER_PROXIMITY",
        severity="LOW",
        camera_id=test_setup["camera"].id,
        video_id=None,
        detected_at=historical_detected_at,
        description="Zero-skew timestamp test",
        confidence=0.85,
    )

    sync_res = StoreAndForwardSyncEngine.sync_pending_records(db=db_session, force_sync=True)
    assert sync_res["events_synced"] >= 1

    # Query central DB
    central_rec = db_session.query(SecurityEvent).filter(SecurityEvent.client_event_id == client_event_id).first()
    assert central_rec is not None
    assert central_rec.client_event_id == client_event_id

    # Verify timestamp matches historical detected_at exactly
    rec_time = central_rec.timestamp
    if rec_time.tzinfo is None:
        rec_time = rec_time.replace(tzinfo=datetime.timezone.utc)
    assert abs((rec_time - historical_detected_at).total_seconds()) < 1.0
    assert central_rec.sync_status == "SYNCED"

def test_idempotent_duplicate_rejection(db_session: Session, test_setup):
    """Verify syncing an already synced client_event_id prevents duplicate rows and increments duplicates_prevented."""
    NetworkStateController.reset()
    client_event_id = f"test-dup-{uuid.uuid4().hex[:8]}"
    detected_at = datetime.datetime.now(datetime.timezone.utc)

    # Buffer and sync first time
    EdgeEventBuffer.buffer_event(
        client_event_id=client_event_id,
        event_type="VIRTUAL_FENCE_BREACH",
        severity="HIGH",
        camera_id=test_setup["camera"].id,
        video_id=None,
        detected_at=detected_at,
        description="First transmission",
        confidence=0.95,
    )
    res1 = StoreAndForwardSyncEngine.sync_pending_records(db=db_session, force_sync=True)
    assert res1["events_synced"] >= 1

    # Count rows in central DB
    count1 = db_session.query(SecurityEvent).filter(SecurityEvent.client_event_id == client_event_id).count()
    assert count1 == 1

    # Simulate network packet retransmission: reset buffer row to PENDING
    conn = EdgeEventBuffer.get_connection()
    with conn:
        conn.execute("UPDATE buffered_events SET status = 'PENDING' WHERE client_event_id = ?;", (client_event_id,))

    res2 = StoreAndForwardSyncEngine.sync_pending_records(db=db_session, force_sync=True)
    assert res2["duplicates_prevented"] >= 1

    # Verify still exactly 1 row in central DB
    count2 = db_session.query(SecurityEvent).filter(SecurityEvent.client_event_id == client_event_id).count()
    assert count2 == 1

def test_bounded_retries_and_exponential_backoff():
    """Verify exponential backoff calculation and quarantine status after maximum retries."""
    client_event_id = f"test-retry-{uuid.uuid4().hex[:8]}"
    detected_at = datetime.datetime.now(datetime.timezone.utc)

    EdgeEventBuffer.buffer_event(
        client_event_id=client_event_id,
        event_type="UNAUTHORIZED_CROSSING",
        severity="CRITICAL",
        camera_id=1,
        video_id=None,
        detected_at=detected_at,
        description="Failing sync test",
        confidence=0.91,
    )

    # Fail 1: backoff scheduled in future
    EdgeEventBuffer.mark_event_failed(client_event_id, "Connection refused", backoff_seconds=10.0)
    pending = EdgeEventBuffer.get_pending_events(limit=500)
    # Should not be in immediate pending list because next_retry_at is 10s in future
    assert not any(e["client_event_id"] == client_event_id for e in pending)

    # Fail until max retries reached
    for _ in range(settings.EDGE_MAX_RETRIES):
        EdgeEventBuffer.mark_event_failed(client_event_id, "Repeated timeout", backoff_seconds=0.0)

    # Check status transitioned to QUARANTINED
    conn = EdgeEventBuffer.get_connection()
    cursor = conn.execute("SELECT status, retry_count FROM buffered_events WHERE client_event_id = ?;", (client_event_id,))
    row = cursor.fetchone()
    assert row["status"] == "QUARANTINED"
    assert row["retry_count"] >= settings.EDGE_MAX_RETRIES

def test_out_of_order_event_reconciliation(db_session: Session, test_setup):
    """Verify events buffered out-of-order are sorted and ingested in detected_at chronological order."""
    now = datetime.datetime.now(datetime.timezone.utc)
    t1 = now - datetime.timedelta(minutes=30)
    t2 = now - datetime.timedelta(minutes=20)
    t3 = now - datetime.timedelta(minutes=10)

    id_t3 = f"order-t3-{uuid.uuid4().hex[:6]}"
    id_t1 = f"order-t1-{uuid.uuid4().hex[:6]}"
    id_t2 = f"order-t2-{uuid.uuid4().hex[:6]}"

    # Buffer out of order: T3, then T1, then T2
    EdgeEventBuffer.buffer_event(id_t3, "BREACH", "HIGH", test_setup["camera"].id, None, t3, "Event 3", 0.9)
    EdgeEventBuffer.buffer_event(id_t1, "BREACH", "LOW", test_setup["camera"].id, None, t1, "Event 1", 0.8)
    EdgeEventBuffer.buffer_event(id_t2, "BREACH", "MEDIUM", test_setup["camera"].id, None, t2, "Event 2", 0.85)

    # get_pending_events must order by detected_at ASC
    pending = EdgeEventBuffer.get_pending_events(limit=100)
    indexed_pending = [e["client_event_id"] for e in pending if e["client_event_id"] in [id_t1, id_t2, id_t3]]
    assert indexed_pending == [id_t1, id_t2, id_t3]

def test_interrupted_sync_partial_recovery(db_session: Session, test_setup):
    """Verify atomic per-record commits: if later sync fails, previously synced records remain committed."""
    ev_a = f"partial-a-{uuid.uuid4().hex[:6]}"
    ev_b = f"partial-b-{uuid.uuid4().hex[:6]}"
    now = datetime.datetime.now(datetime.timezone.utc)
    t_a = now - datetime.timedelta(seconds=20)
    t_b = now - datetime.timedelta(seconds=10)

    EdgeEventBuffer.buffer_event(ev_a, "BREACH", "HIGH", test_setup["camera"].id, None, t_a, "Event A", 0.9)
    EdgeEventBuffer.buffer_event(ev_b, "BREACH", "HIGH", test_setup["camera"].id, None, t_b, "Event B", 0.9)

    # Sync first item by limiting batch_size=1
    res = StoreAndForwardSyncEngine.sync_pending_records(db=db_session, batch_size=1, force_sync=True)
    assert res["events_synced"] == 1

    # Verify ev_a is in central DB
    rec_a = db_session.query(SecurityEvent).filter(SecurityEvent.client_event_id == ev_a).first()
    assert rec_a is not None

    # Verify ev_b is still pending in local buffer
    stats = EdgeEventBuffer.get_buffer_stats()
    assert stats["pending_sync_count"] == 1

def test_local_cv_operation_without_gemini():
    """Verify local edge buffer accepts CV pipeline metadata without calling Gemini."""
    client_event_id = f"cv-local-{uuid.uuid4().hex[:6]}"
    detected_at = datetime.datetime.now(datetime.timezone.utc)

    # Buffer detection event with bounding boxes and track continuity metadata
    cv_metadata = {
        "bounding_box": [120, 200, 310, 450],
        "class_name": "person",
        "track_id": 42,
        "virtual_fence_id": "fence_north_01",
        "crossing_angle_deg": 84.5,
    }

    row_id = EdgeEventBuffer.buffer_event(
        client_event_id=client_event_id,
        event_type="VIRTUAL_FENCE_BREACH",
        severity="HIGH",
        camera_id=1,
        video_id=1,
        detected_at=detected_at,
        description="Local CV detection without external API dependency",
        confidence=0.94,
        metadata_json=cv_metadata,
    )
    assert row_id > 0

    pending = EdgeEventBuffer.get_pending_events(limit=50)
    item = next((e for e in pending if e["client_event_id"] == client_event_id), None)
    assert item is not None
    assert item["metadata_json"]["track_id"] == 42
    assert item["metadata_json"]["class_name"] == "person"

def test_ai_analysis_labeled_pending_network_and_unavailable(db_session: Session, test_setup):
    """Verify Gemini service marks analysis as PENDING_NETWORK when offline without fabricating results."""
    NetworkStateController.set_state(NetworkState.OFFLINE, reason="Simulated network blackout")

    try:
        # Create an incident to analyze
        inc = Incident(
            incident_number=f"INC-OFFLINE-{uuid.uuid4().hex[:6].upper()}",
            title="Offline AI Incident",
            description="Testing AI status labeling during outage",
            severity="HIGH",
            status="OPEN",
        )
        db_session.add(inc)
        db_session.commit()
        db_session.refresh(inc)

        analysis = GeminiService.analyze_incident(
            db=db_session,
            incident_id=inc.id,
        )

        # Status must be PENDING_NETWORK or UNAVAILABLE - strictly NOT COMPLETED or fabricated
        assert analysis["status"] in [AnalysisStatus.PENDING_NETWORK.value, AnalysisStatus.UNAVAILABLE.value]
        summary_text = analysis["summary"].lower()
        assert "network" in summary_text or "offline" in summary_text or "unavailable" in summary_text

    finally:
        NetworkStateController.reset()

def test_disk_quota_and_retention_purge():
    """Verify disk metrics monitoring and retention purge functionality."""
    metrics = EdgeStorageManager.get_disk_metrics()
    assert "total_bytes" in metrics
    assert "buffer_size_mb" in metrics
    assert "quota_utilization_percent" in metrics
    assert metrics["max_quota_mb"] > 0

    purge_res = EdgeStorageManager.enforce_retention()
    assert "files_deleted" in purge_res
    assert "bytes_freed" in purge_res
    assert purge_res["status"] in ["QUOTA_COMPLIANT", "QUOTA_PRESSURE"]

def test_edge_benchmark_harness(db_session: Session, test_setup):
    """Run full empirical edge benchmark verifying 0.0% event loss and 100% duplicate prevention."""
    bench_result = EdgeBenchmark.run_benchmark(
        db=db_session,
        num_events=10,
        simulate_restart=True,
    )
    assert bench_result["total_events_generated"] == 10
    assert bench_result["events_recovered"] == 10
    assert bench_result["event_loss_pct"] == 0.0
    assert bench_result["duplicate_detection_accuracy_pct"] == 100.0
    assert bench_result["timestamp_preservation_accuracy_pct"] == 100.0
    assert bench_result["status"] == "PASSED"
