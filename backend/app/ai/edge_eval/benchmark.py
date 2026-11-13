import os
import time
import uuid
import hashlib
import datetime
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.event import SecurityEvent
from app.models.evidence import Evidence
from app.models.camera import Camera
from app.services.edge.network_controller import NetworkStateController, NetworkState
from app.services.edge.edge_buffer import EdgeEventBuffer
from app.services.edge.sync_engine import StoreAndForwardSyncEngine

class EdgeBenchmark:
    """
    Automated empirical validation benchmark for Edge Store-and-Forward:
    1. Simulates network disconnection (OFFLINE).
    2. Generates N events and evidence files into local WAL buffer.
    3. Simulates cold edge restart (closing connection and reloading from SQLite file).
    4. Restores connectivity (ONLINE).
    5. Synchronizes records to central database.
    6. Verifies 0.0% event loss, zero timestamp skew, and 100% duplicate prevention.
    """

    @classmethod
    def run_benchmark(
        cls,
        db: Session,
        num_events: int = 20,
        simulate_restart: bool = True,
    ) -> Dict[str, Any]:
        logger.info(f"Starting Edge Store-and-Forward Benchmark with {num_events} events...")
        initial_state = NetworkStateController.get_state()
        test_session_id = f"BENCH-{int(time.time())}-{uuid.uuid4().hex[:6]}"

        try:
            # 1. Disconnect Network
            NetworkStateController.set_state(
                NetworkState.OFFLINE,
                reason="Edge Store-and-Forward Empirical Benchmark Drill"
            )

            # Ensure default camera exists
            default_cam = db.query(Camera).first()
            cam_id = default_cam.id if default_cam else None

            # Prepare test evidence directory
            snapshots_dir = settings.get_absolute_path(settings.SNAPSHOTS_DIR)
            os.makedirs(snapshots_dir, exist_ok=True)

            generated_events: List[Dict[str, Any]] = []
            now = datetime.datetime.now(datetime.timezone.utc)

            # 2. Buffer N events during outage
            for i in range(num_events):
                client_event_id = f"bench-ev-{test_session_id}-{i:03d}"
                client_evid_id = f"bench-evid-{test_session_id}-{i:03d}"
                # Distribute timestamps backwards: each event occurred 10s earlier
                event_time = now - datetime.timedelta(seconds=(num_events - i) * 10)
                event_type = "VIRTUAL_FENCE_BREACH" if i % 2 == 0 else "LOITERING_DETECTED"
                severity = "HIGH" if i % 2 == 0 else "MEDIUM"
                description = f"Benchmark synthetic event #{i+1} during simulated edge blackout"
                confidence = round(0.85 + (i % 10) * 0.01, 2)

                # Create synthetic snapshot file
                dummy_content = f"Synthetic benchmark evidence image {client_evid_id} payload".encode("utf-8")
                checksum = hashlib.sha256(dummy_content).hexdigest()
                snap_filename = f"{client_evid_id}.jpg"
                snap_path = os.path.join(snapshots_dir, snap_filename)
                with open(snap_path, "wb") as f:
                    f.write(dummy_content)
                rel_snap_path = os.path.join(settings.SNAPSHOTS_DIR, snap_filename)

                # Buffer into local edge SQLite
                EdgeEventBuffer.buffer_event(
                    client_event_id=client_event_id,
                    event_type=event_type,
                    severity=severity,
                    camera_id=cam_id,
                    video_id=None,
                    detected_at=event_time,
                    description=description,
                    confidence=confidence,
                    metadata_json={"benchmark_session": test_session_id, "index": i},
                    snapshot_path=rel_snap_path,
                    edge_node_id=settings.EDGE_NODE_ID,
                )

                EdgeEventBuffer.buffer_evidence(
                    client_evidence_id=client_evid_id,
                    client_event_id=client_event_id,
                    evidence_type="IMAGE",
                    file_path=rel_snap_path,
                    checksum_sha256=checksum,
                    detected_at=event_time,
                    file_size_bytes=len(dummy_content),
                    metadata_json={"benchmark": True},
                )

                generated_events.append({
                    "client_event_id": client_event_id,
                    "client_evidence_id": client_evid_id,
                    "detected_at": event_time,
                    "checksum": checksum,
                })

            # Verify buffer holds events
            stats_before_sync = EdgeEventBuffer.get_buffer_stats()
            buffered_count = stats_before_sync["pending_sync_count"]

            # 3. Simulate process crash & reboot if requested
            if simulate_restart:
                logger.info("Simulating edge node crash and restart (reloading WAL database)...")
                EdgeEventBuffer.restart()
                stats_after_restart = EdgeEventBuffer.get_buffer_stats()
                if stats_after_restart["pending_sync_count"] != buffered_count:
                    logger.warning("Event count mismatch after simulated restart!")

            # 4. Restore connectivity
            start_recovery_time = time.time()
            NetworkStateController.set_state(
                NetworkState.ONLINE,
                reason="Benchmark connectivity restoration"
            )

            # 5. Synchronize records
            sync_result = StoreAndForwardSyncEngine.sync_pending_records(
                db=db,
                batch_size=num_events + 50,
                force_sync=True,
            )
            recovery_time_ms = int((time.time() - start_recovery_time) * 1000)

            # 6. Verify timestamp accuracy and evidence integrity
            client_ids = [e["client_event_id"] for e in generated_events]
            synced_records = (
                db.query(SecurityEvent)
                .filter(SecurityEvent.client_event_id.in_(client_ids))
                .all()
            )
            events_recovered = len(synced_records)
            event_loss_pct = round(((num_events - events_recovered) / max(num_events, 1)) * 100.0, 2)

            # Check timestamp matches (zero skew)
            timestamp_match_count = 0
            sync_delays_ms: List[float] = []
            for rec in synced_records:
                orig_item = next((e for e in generated_events if e["client_event_id"] == rec.client_event_id), None)
                if orig_item:
                    # Verify timestamp preserves original detected_at
                    orig_dt = orig_item["detected_at"]
                    rec_dt = rec.timestamp
                    if rec_dt.tzinfo is None:
                        rec_dt = rec_dt.replace(tzinfo=datetime.timezone.utc)
                    if abs((rec_dt - orig_dt).total_seconds()) < 1.0:
                        timestamp_match_count += 1

                    if rec.synced_at:
                        s_at = rec.synced_at
                        if s_at.tzinfo is None:
                            s_at = s_at.replace(tzinfo=datetime.timezone.utc)
                        delay = (s_at - orig_dt).total_seconds() * 1000
                        sync_delays_ms.append(max(0.0, delay))

            timestamp_accuracy_pct = round((timestamp_match_count / max(events_recovered, 1)) * 100.0, 2)
            mean_sync_delay = round(sum(sync_delays_ms) / max(len(sync_delays_ms), 1), 2)

            # Check evidence hash match
            evid_ids = [e["client_evidence_id"] for e in generated_events]
            synced_evids = (
                db.query(Evidence)
                .filter(Evidence.client_evidence_id.in_(evid_ids))
                .all()
            )
            evid_hash_matches = 0
            for ev_rec in synced_evids:
                orig_ev = next((e for e in generated_events if e["client_evidence_id"] == ev_rec.client_evidence_id), None)
                if orig_ev and orig_ev["checksum"] == ev_rec.checksum_sha256:
                    evid_hash_matches += 1
            evid_hash_match_pct = round((evid_hash_matches / max(len(synced_evids), 1)) * 100.0, 2)

            # 7. Test Idempotency / Duplicate Rejection
            # Simulate retransmission of an un-ACKed batch
            test_dup_id = client_ids[0]
            conn = EdgeEventBuffer.get_connection()
            with conn:
                conn.execute(
                    "UPDATE buffered_events SET status = 'PENDING' WHERE client_event_id = ?;",
                    (test_dup_id,),
                )
            re_sync_result = StoreAndForwardSyncEngine.sync_pending_records(db=db, force_sync=True)
            dup_prevented = re_sync_result.get("duplicates_prevented", 0)

            # Verify no double row created
            total_matches_in_db = (
                db.query(SecurityEvent)
                .filter(SecurityEvent.client_event_id == test_dup_id)
                .count()
            )
            dup_accuracy_pct = 100.0 if (total_matches_in_db == 1 and dup_prevented >= 1) else 0.0

            db_size = EdgeEventBuffer.get_buffer_stats()["db_file_size_bytes"]

            return {
                "test_name": "Edge Store-and-Forward Recovery & Zero Loss Benchmark",
                "total_events_generated": num_events,
                "events_recovered": events_recovered,
                "event_loss_pct": event_loss_pct,
                "duplicate_events_prevented": dup_prevented,
                "duplicate_detection_accuracy_pct": dup_accuracy_pct,
                "recovery_time_ms": recovery_time_ms,
                "mean_sync_delay_ms": mean_sync_delay,
                "timestamp_preservation_accuracy_pct": timestamp_accuracy_pct,
                "evidence_hash_match_pct": evid_hash_match_pct,
                "buffer_db_size_bytes": db_size,
                "status": "PASSED" if event_loss_pct == 0.0 and dup_accuracy_pct == 100.0 else "FAILED",
            }

        finally:
            NetworkStateController.set_state(initial_state, reason="Benchmark completion cleanup")
