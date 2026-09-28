import os
import cv2
import hashlib
import datetime
import subprocess
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Set
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.video import Video, VideoStatus
from app.models.camera import Camera
from app.models.detection import Detection
from app.models.event import SecurityEvent, EventType, SeverityLevel
from app.models.alert import Alert, AlertStatus
from app.models.incident import Incident, IncidentStatus
from app.models.evidence import Evidence, EvidenceType
from app.ai.detection.yolo_detector import YOLODetector
from app.ai.tracking.tracker import SurveillanceTracker
from app.ai.event_detection.zone_analytics import SpatialAnalyticsEngine
from app.services.ffmpeg_service import FFmpegService

def calculate_file_sha256(filepath: str) -> str:
    """Calculates SHA-256 hash of a file for cryptographic chain of custody."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()

class AnalyticsPipelineService:
    @staticmethod
    def process_video(
        db: Session,
        video_id: int,
        conf_threshold: Optional[float] = None,
        process_every_n_frames: Optional[int] = None,
        enable_tracking: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end video analytics pipeline:
        Video -> YOLOv8 Detection -> Persistent Tracking -> Spatial Zone Analytics
        -> Tactical Overlay Annotation -> H.264 MP4 Transcoding -> Events & Incidents.
        """
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise ValueError(f"Video {video_id} not found")

        video.status = VideoStatus.PROCESSING.value
        video.processing_started_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()

        abs_video_path = str(settings.get_absolute_path(video.path))
        if not os.path.exists(abs_video_path):
            video.status = VideoStatus.FAILED.value
            video.error_message = f"File not found on disk: {abs_video_path}"
            db.commit()
            raise FileNotFoundError(video.error_message)

        # Load camera configuration if associated
        camera = None
        restricted_zones = []
        virtual_lines = []
        if video.camera_id:
            camera = db.query(Camera).filter(Camera.id == video.camera_id).first()
            if camera:
                restricted_zones = camera.restricted_zones or []
                virtual_lines = camera.virtual_lines or []

        # If no camera zones defined, use standard surveillance zones
        if not restricted_zones and not virtual_lines:
            restricted_zones = [
                {
                    "id": "default-zone-1",
                    "name": "Buffer Strip Exclusion Zone",
                    "polygon": [
                        {"x": 15, "y": 30},
                        {"x": 85, "y": 30},
                        {"x": 85, "y": 85},
                        {"x": 15, "y": 85},
                    ],
                    "alert_severity": "HIGH",
                }
            ]
            virtual_lines = [
                {
                    "id": "default-line-1",
                    "name": "Perimeter Demarcation Line",
                    "p1": {"x": 10, "y": 50},
                    "p2": {"x": 90, "y": 50},
                    "direction": "BOTH",
                    "alert_severity": "CRITICAL",
                }
            ]

        # Initialize AI detector and tracker
        try:
            detector = YOLODetector(conf_threshold=conf_threshold or settings.CONFIDENCE_THRESHOLD)
            tracker = SurveillanceTracker() if enable_tracking else None
        except Exception as e:
            logger.error(f"Failed to initialize AI engines: {e}")
            video.status = VideoStatus.FAILED.value
            video.error_message = f"AI Engine init failed: {str(e)}"
            db.commit()
            raise

        cap = cv2.VideoCapture(abs_video_path)
        if not cap.isOpened():
            video.status = VideoStatus.FAILED.value
            video.error_message = "OpenCV could not open video stream"
            db.commit()
            raise RuntimeError(video.error_message)

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        sample_step = max(1, process_every_n_frames or settings.PROCESS_EVERY_N_FRAMES)

        spatial_engine = SpatialAnalyticsEngine(
            restricted_zones=restricted_zones,
            virtual_lines=virtual_lines,
            frame_width=width,
            frame_height=height,
        )

        # Prepare Annotated Video Output Writer
        processed_filename = f"processed_{video.filename}"
        if not processed_filename.endswith(".mp4"):
            processed_filename = f"{os.path.splitext(processed_filename)[0]}.mp4"
            
        processed_rel_path = f"{settings.PROCESSED_DIR}/{processed_filename}"
        processed_abs_path = str(settings.get_absolute_path(processed_rel_path))
        os.makedirs(os.path.dirname(processed_abs_path), exist_ok=True)
        
        temp_annotated_raw = str(settings.get_absolute_path(f"{settings.PROCESSED_DIR}/temp_raw_{processed_filename}"))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_writer = cv2.VideoWriter(temp_annotated_raw, fourcc, fps, (width, height))

        frame_idx = 0
        total_detections_count = 0
        tracked_ids_seen: Set[int] = set()
        generated_events_count = 0
        generated_alerts_count = 0
        generated_incidents_count = 0

        # Current or new incident for high-severity events
        incident = None
        last_tracked_dets = []

        logger.info(f"Starting analytics & annotation pipeline for Video #{video.id} ({total_frames} frames)...")

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                timestamp_sec = frame_idx / fps

                # 1. Run YOLO & Tracker at sample_step intervals
                if frame_idx % sample_step == 0:
                    raw_dets = detector.detect_frame(frame)
                    if tracker:
                        tracked_dets = tracker.update(raw_dets, timestamp_sec)
                    else:
                        tracked_dets = raw_dets
                    last_tracked_dets = tracked_dets
                else:
                    tracked_dets = last_tracked_dets

                annotated_frame = frame.copy()
                is_active_breach_frame = False

                # 2. Draw Spatial Boundaries (Polygons & Lines) on frame
                for zone in restricted_zones:
                    poly_coords = zone.get("polygon", [])
                    if len(poly_coords) >= 3:
                        pts = np.array([
                            [int(p["x"] * width / 100 if p["x"] > 1 else p["x"] * width),
                             int(p["y"] * height / 100 if p["y"] > 1 else p["y"] * height)]
                            for p in poly_coords
                        ], np.int32)
                        # Draw semi-transparent zone overlay
                        overlay = annotated_frame.copy()
                        cv2.fillPoly(overlay, [pts], (252, 92, 124)) # Light violet/purple BGR
                        cv2.addWeighted(overlay, 0.15, annotated_frame, 0.85, 0, annotated_frame)
                        cv2.polylines(annotated_frame, [pts], True, (252, 92, 124), 2)
                        # Zone Label
                        center_x = int(np.mean(pts[:, 0]))
                        center_y = int(np.mean(pts[:, 1]))
                        cv2.putText(
                            annotated_frame,
                            zone.get("name", "RESTRICTED BUFFER STRIP"),
                            (center_x - 110, center_y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55,
                            (252, 92, 124),
                            2,
                        )

                for line in virtual_lines:
                    p1 = line.get("p1", {"x": 10, "y": 50})
                    p2 = line.get("p2", {"x": 90, "y": 50})
                    pt1 = (int(p1["x"] * width / 100 if p1["x"] > 1 else p1["x"] * width),
                           int(p1["y"] * height / 100 if p1["y"] > 1 else p1["y"] * height))
                    pt2 = (int(p2["x"] * width / 100 if p2["x"] > 1 else p2["x"] * width),
                           int(p2["y"] * height / 100 if p2["y"] > 1 else p2["y"] * height))
                    cv2.line(annotated_frame, pt1, pt2, (6, 119, 217), 2) # Amber BGR
                    cv2.putText(
                        annotated_frame,
                        line.get("name", "DEMARCATION TRIPWIRE"),
                        (pt1[0] + 10, pt1[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (6, 119, 217),
                        2,
                    )

                # 3. Process Detections & Draw Bounding Boxes + Tags
                for det in tracked_dets:
                    bbox_px = det.get("bbox_pixels") or [
                        int(det["bbox"][0] * width),
                        int(det["bbox"][1] * height),
                        int(det["bbox"][2] * width),
                        int(det["bbox"][3] * height),
                    ]
                    class_name = det.get("class_name", "target").upper()
                    conf = det.get("confidence", 0.90)
                    tracking_id = det.get("tracking_id")
                    dwell_time = det.get("dwell_time", 0.0)

                    if tracking_id is not None:
                        tracked_ids_seen.add(tracking_id)

                    x1, y1 = max(0, int(bbox_px[0])), max(0, int(bbox_px[1]))
                    x2, y2 = min(width, int(bbox_px[2])), min(height, int(bbox_px[3]))

                    # Spatial Analysis on sample step
                    is_breaching = False
                    if frame_idx % sample_step == 0:
                        total_detections_count += 1
                        
                        det_record = Detection(
                            video_id=video.id,
                            camera_id=video.camera_id,
                            timestamp_offset=round(timestamp_sec, 2),
                            frame_number=frame_idx,
                            object_type=class_name.lower(),
                            confidence=conf,
                            bbox_x1=x1,
                            bbox_y1=y1,
                            bbox_x2=x2,
                            bbox_y2=y2,
                            tracking_id=tracking_id,
                        )
                        db.add(det_record)

                        if tracking_id is not None:
                            spatial_events = spatial_engine.analyze_tracked_detection(
                                track_id=tracking_id,
                                object_type=class_name.lower(),
                                confidence=conf,
                                bbox=[x1, y1, x2, y2],
                                timestamp=timestamp_sec,
                                dwell_time=dwell_time,
                            )

                            for ev in spatial_events:
                                generated_events_count += 1
                                is_breaching = True
                                is_active_breach_frame = True

                                # Snapshot JPEG
                                snap_filename = f"ev_snap_v{video.id}_f{frame_idx}_{tracking_id}.jpg"
                                snap_rel_path = f"{settings.SNAPSHOTS_DIR}/{snap_filename}"
                                snap_abs_path = str(settings.get_absolute_path(snap_rel_path))
                                FFmpegService.extract_frame_at_timestamp(abs_video_path, timestamp_sec, snap_abs_path)

                                snap_checksum = None
                                snap_size = None
                                if os.path.exists(snap_abs_path):
                                    snap_checksum = calculate_file_sha256(snap_abs_path)
                                    snap_size = os.path.getsize(snap_abs_path)

                                # Create incident if high/critical
                                if ev["severity"] in ["HIGH", "CRITICAL"]:
                                    if not incident:
                                        generated_incidents_count += 1
                                        import uuid
                                        inc_number = f"INC-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')}-{video.id:04d}-{uuid.uuid4().hex[:4].upper()}"
                                        incident = Incident(
                                            incident_number=inc_number,
                                            title=f"{ev['event_type'].replace('_', ' ')} Breach detected during Video #{video.id} processing",
                                            description=ev["description"],
                                            severity=ev["severity"],
                                            status=IncidentStatus.OPEN.value,
                                            ai_summary=f"Automated edge AI verified {class_name} #{tracking_id} crossed perimeter demarcation line into restricted exclusion zone. Immediate patrol dispatch recommended.",
                                            ai_recommendations=[
                                                "Dispatch Quick Reaction Team to intercepted sector coordinates.",
                                                "Lock PTZ optics onto target tracking vector.",
                                            ],
                                        )
                                        db.add(incident)
                                        db.commit()
                                        db.refresh(incident)

                                event_record = SecurityEvent(
                                    event_type=ev["event_type"],
                                    severity=ev["severity"],
                                    camera_id=video.camera_id,
                                    video_id=video.id,
                                    incident_id=incident.id if incident else None,
                                    timestamp=datetime.datetime.now(datetime.timezone.utc),
                                    description=ev["description"],
                                    confidence=ev["confidence"],
                                    status="ACTIVE",
                                    metadata_json=ev["metadata"],
                                    snapshot_path=snap_rel_path if os.path.exists(snap_abs_path) else None,
                                )
                                db.add(event_record)
                                db.commit()
                                db.refresh(event_record)

                                if os.path.exists(snap_abs_path):
                                    evidence_record = Evidence(
                                        incident_id=incident.id if incident else None,
                                        event_id=event_record.id,
                                        evidence_type=EvidenceType.SNAPSHOT.value,
                                        file_path=snap_rel_path,
                                        file_size_bytes=snap_size,
                                        checksum_sha256=snap_checksum,
                                        metadata_json={
                                            "camera_id": video.camera_id,
                                            "tracking_id": tracking_id,
                                            "object_type": class_name.lower(),
                                            "confidence": conf,
                                            "timestamp_offset": round(timestamp_sec, 2),
                                            "event_type": ev["event_type"],
                                            "breached_zone": ev.get("metadata", {}).get("zone_name"),
                                        }
                                    )
                                    db.add(evidence_record)

                                alert_record = Alert(
                                    event_id=event_record.id,
                                    camera_id=video.camera_id,
                                    incident_id=incident.id if incident else None,
                                    severity=ev["severity"],
                                    title=f"{ev['severity']}: {ev['event_type'].replace('_', ' ')}",
                                    message=ev["description"],
                                    status=AlertStatus.NEW.value,
                                )
                                db.add(alert_record)
                                generated_alerts_count += 1

                    # Draw Tactical Bounding Box & Label
                    box_color = (47, 47, 211) if is_breaching else (252, 92, 124) # Red if breaching, Violet if tracking
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 2)

                    # Label Tag
                    tag_text = f"{class_name} #{tracking_id or 1} {int(conf * 100)}%"
                    (tw, th), _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                    cv2.rectangle(annotated_frame, (x1, max(0, y1 - th - 8)), (x1 + tw + 10, y1), box_color, -1)
                    cv2.putText(annotated_frame, tag_text, (x1 + 5, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                # 4. Top Telemetry Watermark HUD
                cam_label = camera.camera_identifier if camera else "CAM-NP-01"
                hud_text = f"SENTINEL-AI EDGE INFERENCE | {cam_label} | 30 FPS | {datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')} UTC"
                cv2.rectangle(annotated_frame, (20, 20), (width - 20, 50), (20, 20, 20), -1)
                cv2.putText(annotated_frame, hud_text, (30, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (22, 163, 74), 2)
                cv2.putText(annotated_frame, "YOLOv8 + ByteTrack ACTIVE", (width - 280, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (252, 92, 124), 2)

                # 5. Flash Alert Banner if incursion active
                if is_active_breach_frame:
                    cv2.rectangle(annotated_frame, (width // 2 - 220, 60), (width // 2 + 220, 95), (47, 47, 211), -1)
                    cv2.putText(annotated_frame, "ALERT: RESTRICTED ZONE ENTRY", (width // 2 - 195, 84), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

                out_writer.write(annotated_frame)
                frame_idx += 1

            cap.release()
            out_writer.release()

            # Transcode annotated raw video into browser-playable H.264 MP4 using FFmpeg
            logger.info(f"Transcoding annotated output video to browser H.264: {processed_abs_path}...")
            transcode_cmd = [
                "ffmpeg", "-y",
                "-i", temp_annotated_raw,
                "-vcodec", "libx264",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-preset", "veryfast",
                "-crf", "23",
                processed_abs_path,
            ]
            subprocess.run(transcode_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if os.path.exists(temp_annotated_raw):
                os.remove(temp_annotated_raw)

            # Update Video Record in DB
            video.status = VideoStatus.COMPLETED.value
            video.processed_path = processed_rel_path
            video.total_detections_count = total_detections_count
            video.total_tracked_objects_count = len(tracked_ids_seen) or 1
            video.total_incidents_count = generated_incidents_count
            video.processing_completed_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()

            # Record Video Evidence
            if incident and os.path.exists(processed_abs_path):
                try:
                    vid_checksum = calculate_file_sha256(processed_abs_path)
                    vid_evidence = Evidence(
                        incident_id=incident.id,
                        evidence_type=EvidenceType.VIDEO_CLIP.value,
                        file_path=processed_rel_path,
                        file_size_bytes=os.path.getsize(processed_abs_path),
                        checksum_sha256=vid_checksum,
                        metadata_json={
                            "camera_id": video.camera_id,
                            "video_id": video.id,
                            "resolution": f"{width}x{height}",
                            "fps": fps,
                            "total_detections": total_detections_count,
                            "tracked_objects": len(tracked_ids_seen),
                        }
                    )
                    db.add(vid_evidence)
                    db.commit()
                except Exception as ex:
                    logger.warning(f"Could not record video clip evidence: {ex}")

            logger.info(
                f"Video #{video.id} analytics complete: {total_detections_count} detections, "
                f"{len(tracked_ids_seen)} tracked targets, {generated_events_count} events, {generated_incidents_count} incidents."
            )

            return {
                "video_id": video.id,
                "status": "COMPLETED",
                "processed_path": processed_rel_path,
                "processed_url": f"/static/processed/{processed_filename}",
                "total_frames_inspected": frame_idx,
                "total_detections": total_detections_count,
                "tracked_objects": len(tracked_ids_seen) or 1,
                "generated_events": generated_events_count,
                "generated_alerts": generated_alerts_count,
                "incident_created": incident.incident_number if incident else None,
            }

        except Exception as e:
            cap.release()
            out_writer.release()
            db.rollback()
            logger.error(f"Pipeline error processing video #{video.id}: {e}", exc_info=True)
            video.status = VideoStatus.FAILED.value
            video.error_message = str(e)
            db.commit()
            raise
