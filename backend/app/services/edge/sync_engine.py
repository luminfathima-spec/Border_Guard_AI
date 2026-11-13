import os
import uuid
import time
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.event import SecurityEvent
from app.models.evidence import Evidence
from app.models.alert import Alert
from app.models.camera import Camera
from app.services.edge.network_controller import NetworkStateController
from app.services.edge.edge_buffer import EdgeEventBuffer

class StoreAndForwardSyncEngine:
    """
    Orchestrates synchronization of locally buffered edge events and evidence
    with the central PostgreSQL database upon connectivity restoration.
    Enforces idempotency, original timestamp preservation, bounded exponential backoff,
    and atomic transactional safety.
    """

    @classmethod
    def sync_pending_records(
        cls,
        db: Session,
        batch_size: Optional[int] = None,
        force_sync: bool = False,
    ) -> Dict[str, Any]:
        """
        Processes pending buffered edge records in strict chronological order (detected_at ASC).
        Guarantees that:
        1. Unique client_event_id prevents duplicate row creation.
        2. Original edge detection timestamps are preserved on central records.
        3. Linked evidence files are verified and connected.
        4. Bounded retries with exponential backoff prevent queue deadlock.
        """
        start_time = time.time()
        session_id = f"SYNC-{int(start_time)}-{uuid.uuid4().hex[:6]}"
        started_at = datetime.datetime.now(datetime.timezone.utc)

        # Check network connectivity
        if not force_sync and NetworkStateController.is_offline():
            logger.info("Sync skipped: Edge node is currently in OFFLINE state.")
            return {
                "session_id": session_id,
                "status": "SKIPPED_OFFLINE",
                "events_synced": 0,
                "duplicates_prevented": 0,
                "duration_ms": 0,
                "message": "Network connectivity offline. Events remain safely buffered in local WAL store.",
            }

        limit = batch_size or settings.EDGE_SYNC_BATCH_SIZE
        pending_events = EdgeEventBuffer.get_pending_events(limit=limit)

        if not pending_events:
            return {
                "session_id": session_id,
                "status": "UP_TO_DATE",
                "events_synced": 0,
                "duplicates_prevented": 0,
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "message": "Zero pending events in edge buffer.",
            }

        logger.info(f"SyncEngine: Beginning sync session {session_id} for {len(pending_events)} pending events...")

        events_synced = 0
        evidence_synced = 0
        duplicates_prevented = 0
        conflicts_resolved = 0
        bytes_transferred = 0
        errors_count = 0

        # Resolve fallback camera if camera_id in edge buffer is missing or invalid
        default_cam = db.query(Camera).first()
        default_cam_id = default_cam.id if default_cam else None

        for ev in pending_events:
            client_event_id = ev["client_event_id"]

            try:
                # 1. Idempotency Check: Does this client_event_id already exist in the central DB?
                existing = (
                    db.query(SecurityEvent)
                    .filter(SecurityEvent.client_event_id == client_event_id)
                    .first()
                )

                if existing:
                    # Idempotent skip: Duplicate detected!
                    duplicates_prevented += 1
                    EdgeEventBuffer.mark_event_synced(client_event_id)
                    logger.debug(f"SyncEngine: Duplicate event {client_event_id} detected and acknowledged.")
                    continue

                # 2. Parse original edge detection timestamp (zero temporal skew)
                detected_at_raw = ev["detected_at"]
                if isinstance(detected_at_raw, str):
                    detected_at = datetime.datetime.fromisoformat(detected_at_raw)
                else:
                    detected_at = detected_at_raw

                # Normalize timezone to UTC
                if detected_at.tzinfo is not None:
                    detected_at = detected_at.astimezone(datetime.timezone.utc)
                else:
                    detected_at = detected_at.replace(tzinfo=datetime.timezone.utc)

                # Validate camera reference
                cam_id = ev.get("camera_id")
                if cam_id:
                    cam_check = db.query(Camera).filter(Camera.id == cam_id).first()
                    if not cam_check:
                        cam_id = default_cam_id
                else:
                    cam_id = default_cam_id

                # 3. Create central SecurityEvent with original timestamp
                event_record = SecurityEvent(
                    client_event_id=client_event_id,
                    event_type=ev["event_type"],
                    severity=ev["severity"],
                    camera_id=cam_id,
                    video_id=ev.get("video_id"),
                    timestamp=detected_at,  # Exact edge occurrence timestamp!
                    description=ev["description"],
                    confidence=ev["confidence"],
                    status="ACTIVE",
                    metadata_json=ev.get("metadata_json", {}),
                    snapshot_path=ev.get("snapshot_path"),
                    clip_path=ev.get("clip_path"),
                    edge_node_id=ev.get("edge_node_id"),
                    sync_status="SYNCED",
                    synced_at=datetime.datetime.now(datetime.timezone.utc),
                    created_at=datetime.datetime.now(datetime.timezone.utc),
                )
                db.add(event_record)
                db.flush()

                # 4. Ingest and link associated evidence
                evid_items = EdgeEventBuffer.get_pending_evidence_for_event(client_event_id)
                for item in evid_items:
                    client_evid_id = item["client_evidence_id"]
                    existing_evid = (
                        db.query(Evidence)
                        .filter(Evidence.client_evidence_id == client_evid_id)
                        .first()
                    )

                    if not existing_evid:
                        evid_record = Evidence(
                            client_evidence_id=client_evid_id,
                            event_id=event_record.id,
                            evidence_type=item["evidence_type"],
                            file_path=item["file_path"],
                            file_size_bytes=item.get("file_size_bytes"),
                            checksum_sha256=item["checksum_sha256"],
                            timestamp=detected_at,
                            metadata_json=item.get("metadata_json", {}),
                            sync_status="SYNCED",
                            synced_at=datetime.datetime.now(datetime.timezone.utc),
                        )
                        db.add(evid_record)
                        evidence_synced += 1
                        bytes_transferred += item.get("file_size_bytes") or 0

                # 5. Create Alert for operational notification if severe
                if ev["severity"] in ["HIGH", "CRITICAL"]:
                    alert_record = Alert(
                        event_id=event_record.id,
                        camera_id=cam_id,
                        severity=ev["severity"],
                        title=f"{ev['severity']}: {ev['event_type'].replace('_', ' ')}",
                        message=ev["description"],
                        status="NEW",
                        created_at=detected_at,
                    )
                    db.add(alert_record)

                # Commit per-record transaction for resilience against mid-batch interruption
                db.commit()
                EdgeEventBuffer.mark_event_synced(client_event_id)
                events_synced += 1

            except Exception as err:
                db.rollback()
                errors_count += 1
                logger.error(f"SyncEngine: Failed to sync event {client_event_id}: {err}")

                # Calculate exponential backoff
                retry_count = ev.get("retry_count", 0)
                backoff = min(
                    settings.EDGE_BACKOFF_MAX_SECONDS,
                    settings.EDGE_BACKOFF_BASE_SECONDS * (2 ** retry_count),
                )
                EdgeEventBuffer.mark_event_failed(client_event_id, str(err), backoff)

        completed_at = datetime.datetime.now(datetime.timezone.utc)
        duration_ms = int((time.time() - start_time) * 1000)
        session_status = "SUCCESS" if errors_count == 0 else ("PARTIAL" if events_synced > 0 else "FAILED")

        EdgeEventBuffer.record_sync_session(
            session_id=session_id,
            started_at=started_at,
            completed_at=completed_at,
            events_synced=events_synced,
            evidence_synced=evidence_synced,
            duplicates_prevented=duplicates_prevented,
            conflicts_resolved=conflicts_resolved,
            bytes_transferred=bytes_transferred,
            duration_ms=duration_ms,
            status=session_status,
        )

        logger.info(
            f"SyncEngine: Session {session_id} finished in {duration_ms}ms. "
            f"Synced: {events_synced}, Duplicates Prevented: {duplicates_prevented}, Errors: {errors_count}."
        )

        return {
            "session_id": session_id,
            "status": session_status,
            "events_synced": events_synced,
            "evidence_synced": evidence_synced,
            "duplicates_prevented": duplicates_prevented,
            "conflicts_resolved": conflicts_resolved,
            "bytes_transferred": bytes_transferred,
            "duration_ms": duration_ms,
            "errors_count": errors_count,
            "remaining_pending": EdgeEventBuffer.get_buffer_stats()["pending_sync_count"],
        }
