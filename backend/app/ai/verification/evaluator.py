import math
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.schemas.verification import VerificationConfig
from app.models.event import SecurityEvent
from app.models.track import ObjectTrack
from app.models.camera import Camera
from app.models.event_graph import EvidenceObservation, ObservationType
from app.models.evidence import Evidence
from app.core.logging import logger

class EvidentiarySufficiencyEvaluator:
    """
    Evaluates multi-modal evidence criteria to determine whether a security observation
    has sufficient factual grounding or requires additional local/generative verification.
    """

    @classmethod
    def evaluate(
        cls,
        db: Session,
        event: SecurityEvent,
        config: VerificationConfig,
        track: Optional[ObjectTrack] = None,
        camera: Optional[Camera] = None,
    ) -> Dict[str, Any]:
        """
        Computes the Evidentiary Sufficiency vector for an observed security event:
        - Detection confidence and observation quality
        - Object-track continuity and dwell time
        - Virtual boundary geometry (penetration margin)
        - Conflicting observations (e.g. conflicting radar/optical reports)
        - Camera availability & frame gap notices
        - Evidence completeness
        """
        # 1. Detection Confidence & Observation Quality
        c_det = float(event.confidence)
        meta = event.metadata_json or {}

        # Quality estimation: bounding box area and aspect ratio sanity
        bbox = meta.get("bbox") or meta.get("centroid") or [0, 0, 100, 100]
        obs_quality = 1.0
        if isinstance(bbox, list) and len(bbox) == 4:
            w = abs(bbox[2] - bbox[0])
            h = abs(bbox[3] - bbox[1])
            area = w * h
            # Penalty for tiny bounding boxes (< 200 sq px) or extreme aspect ratios
            if area < 200:
                obs_quality *= 0.7
            if w > 0 and h > 0:
                aspect = max(w / h, h / w)
                if aspect > 6.0:  # Unnatural slender sliver
                    obs_quality *= 0.8
        elif "confirmed_frames" in meta:
            # If confirmed_frames available, factor in
            cframes = meta.get("confirmed_frames", 1)
            obs_quality = min(1.0, 0.7 + (cframes * 0.1))

        # 2. Object Track Continuity
        track_continuity = 0.5
        consecutive_frames = meta.get("confirmed_frames", 1)
        dwell_time = float(meta.get("dwell_time", 0.0))

        if track:
            tf = (track.last_seen_frame - track.first_seen_frame + 1) if (track.last_seen_frame is not None and track.first_seen_frame is not None) else (len(track.trajectory_json) if track.trajectory_json else 1)
            consecutive_frames = max(consecutive_frames, max(1, tf))
            dwell_time = max(dwell_time, float(track.dwell_time_seconds or 0.0))
            track_continuity = min(1.0, consecutive_frames / float(config.min_track_frames))
            # Disappearance penalty
            if not track.is_active and consecutive_frames < config.min_track_frames:
                track_continuity *= 0.6
        else:
            track_continuity = min(1.0, consecutive_frames / float(config.min_track_frames))

        # 3. Virtual Boundary Geometry (Penetration Margin)
        # Deep penetration into zone or well-crossed tripwire gets higher margin
        geometry_score = 0.8  # default baseline
        if "dwell_time" in meta and dwell_time > 2.0:
            geometry_score = min(1.0, 0.7 + (dwell_time * 0.05))
        if event.event_type == "LINE_CROSSING":
            geometry_score = 0.9

        # 4. Conflicting Observations Check
        conflicts_detected: List[str] = []
        is_conflict = False
        if event.incident_id:
            incident_observations = (
                db.query(EvidenceObservation)
                .filter(
                    EvidenceObservation.incident_id == event.incident_id,
                    EvidenceObservation.observation_type.in_([
                        ObservationType.CONFLICT_RECORD.value,
                        "CONFLICT_RECORD",
                    ]),
                    EvidenceObservation.status == "ACTIVE",
                )
                .all()
            )
            for obs in incident_observations:
                is_conflict = True
                conflicts_detected.append(f"{obs.source_system}: {obs.title} — {obs.description}")

        # 5. Camera Availability & Missing Evidence
        camera_available = True
        missing_evidence: List[str] = []
        if camera:
            if camera.status != "ONLINE":
                camera_available = False
                missing_evidence.append(f"Camera {camera.camera_identifier} status is {camera.status}")

        # Check for MISSING_DATA_GAP in observations
        if event.incident_id:
            missing_gaps = (
                db.query(EvidenceObservation)
                .filter(
                    EvidenceObservation.incident_id == event.incident_id,
                    EvidenceObservation.observation_type.in_([
                        ObservationType.MISSING_DATA_GAP.value,
                        "MISSING_DATA_GAP",
                    ]),
                    EvidenceObservation.status == "ACTIVE",
                )
                .all()
            )
            for gap in missing_gaps:
                missing_evidence.append(f"Data gap notice: {gap.title}")

        # Check evidence files attached
        evidence_count = 0
        if event.incident_id:
            evidence_count = db.query(Evidence).filter(Evidence.incident_id == event.incident_id).count()
        if evidence_count == 0 and not event.snapshot_path:
            missing_evidence.append("No forensic snapshot or video clip registered for event")

        evidence_completeness = 1.0 - (0.25 * min(4, len(missing_evidence)))
        if not camera_available:
            evidence_completeness *= 0.5

        # 6. Composite Sufficiency Score Calculation
        # S_ev = w_d * C_det + w_trk * track_cont + w_geom * geom - w_conf * conflict
        conflict_penalty = config.weight_conflict_penalty if is_conflict else 0.0

        raw_score = (
            (config.weight_detection_confidence * c_det * obs_quality)
            + (config.weight_track_continuity * track_continuity)
            + (config.weight_boundary_geometry * geometry_score)
            - conflict_penalty
        )

        sufficiency_score = max(0.0, min(1.0, raw_score * evidence_completeness))

        is_high = (sufficiency_score >= config.high_confidence_threshold and not is_conflict and camera_available)
        is_marginal = (config.marginal_threshold <= sufficiency_score < config.high_confidence_threshold or len(missing_evidence) > 0)

        return {
            "sufficiency_score": round(sufficiency_score, 4),
            "detection_confidence": round(c_det, 4),
            "observation_quality": round(obs_quality, 4),
            "track_continuity": round(track_continuity, 4),
            "consecutive_frames": consecutive_frames,
            "dwell_time": round(dwell_time, 2),
            "geometry_score": round(geometry_score, 4),
            "is_conflict": is_conflict,
            "conflicts_detected": conflicts_detected,
            "camera_available": camera_available,
            "missing_evidence": missing_evidence,
            "evidence_completeness": round(evidence_completeness, 4),
            "is_high_confidence": is_high,
            "is_marginal": is_marginal,
        }
