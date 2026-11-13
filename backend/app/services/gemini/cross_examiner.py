from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session

from app.models.camera import Camera
from app.models.evidence import Evidence
from app.models.event import SecurityEvent
from app.models.ai_analysis import AnalysisStatus
from app.schemas.ai import IncidentAnalysisResponse, GroundedCitationAudit
from app.core.logging import logger

class CrossExaminer:
    """
    Deterministic Evidence Safeguard Engine for Generative AI.
    Cross-examines all claims, entity IDs, camera references, and evidence IDs cited by
    Google Gemini against the immutable PostgreSQL database records.
    Prevents hallucinated entities from penetrating the legal chain of custody.
    """

    @classmethod
    def verify(
        cls,
        db: Session,
        analysis: IncidentAnalysisResponse,
        incident_id: int,
    ) -> Tuple[GroundedCitationAudit, str]:
        """
        Cross-examines an IncidentAnalysisResponse against the database:
        - Validates referenced_camera_ids against Camera table.
        - Validates supporting_evidence_ids against Evidence table.
        - Validates observed_events against SecurityEvent table.
        - Quarantines ungrounded claims and computes a strict Grounding Score.

        Returns (GroundedCitationAudit, status_str).
        """
        verified_cameras: List[int] = []
        ungrounded_cameras: List[int] = []
        verified_evidence: List[int] = []
        ungrounded_evidence: List[int] = []
        verified_events: List[int] = []
        ungrounded_events: List[int] = []
        hallucinations: List[str] = []

        # 1. Verify Camera IDs
        if analysis.referenced_camera_ids:
            found_cams = db.query(Camera.id).filter(Camera.id.in_(analysis.referenced_camera_ids)).all()
            found_cam_ids = {row[0] for row in found_cams}
            for cam_id in analysis.referenced_camera_ids:
                if cam_id in found_cam_ids:
                    verified_cameras.append(cam_id)
                else:
                    ungrounded_cameras.append(cam_id)
                    hallucinations.append(f"Ungrounded Camera ID {cam_id} does not exist in database")

        # 2. Verify Evidence IDs
        if analysis.supporting_evidence_ids:
            found_ev = db.query(Evidence.id).filter(Evidence.id.in_(analysis.supporting_evidence_ids)).all()
            found_ev_ids = {row[0] for row in found_ev}
            for ev_id in analysis.supporting_evidence_ids:
                if ev_id in found_ev_ids:
                    verified_evidence.append(ev_id)
                else:
                    ungrounded_evidence.append(ev_id)
                    hallucinations.append(f"Ungrounded Evidence ID {ev_id} does not exist in database")

        # 3. Verify Observed Event IDs (if specified)
        event_ids_cited = [ev.event_id for ev in analysis.observed_events if ev.event_id is not None]
        if event_ids_cited:
            found_events = db.query(SecurityEvent.id).filter(SecurityEvent.id.in_(event_ids_cited)).all()
            found_event_ids = {row[0] for row in found_events}
            for eid in event_ids_cited:
                if eid in found_event_ids:
                    verified_events.append(eid)
                else:
                    ungrounded_events.append(eid)
                    hallucinations.append(f"Ungrounded Event ID {eid} does not exist in database")

        # 4. Calculate Grounding Score
        total_claims = len(analysis.referenced_camera_ids) + len(analysis.supporting_evidence_ids) + len(event_ids_cited)
        total_verified = len(verified_cameras) + len(verified_evidence) + len(verified_events)

        if total_claims == 0:
            grounding_score = 1.0
        else:
            grounding_score = round(float(total_verified) / float(total_claims), 4)

        # 5. Quarantine Hallucinations from the Verified Payload
        # Strip ungrounded entities so downstream consumers only receive verified IDs
        analysis.referenced_camera_ids = verified_cameras
        analysis.supporting_evidence_ids = verified_evidence

        # 6. Determine Status & Attach Safeguard Warning
        if hallucinations:
            status = AnalysisStatus.FLAGGED.value
            logger.warning(
                f"CrossExaminer FLAGGED incident {incident_id} AI analysis with {len(hallucinations)} "
                f"hallucinations: {hallucinations}"
            )
            # Append transparent evidentiary warning to summary
            disclaimer = (
                f"\n\n> [!CAUTION] **CROSS-EXAMINER GROUNDING SAFEGUARD WARNING**:\n"
                f"> Generative AI cited {len(hallucinations)} ungrounded entities not found in verified sensor records:\n"
                + "\n".join([f"> - {h}" for h in hallucinations])
                + "\n> Ungrounded citations have been automatically quarantined from the evidentiary record."
            )
            analysis.summary += disclaimer
        else:
            status = AnalysisStatus.SUCCESS.value

        audit = GroundedCitationAudit(
            verified_cameras=verified_cameras,
            verified_evidence=verified_evidence,
            verified_events=verified_events,
            ungrounded_cameras=ungrounded_cameras,
            ungrounded_evidence=ungrounded_evidence,
            ungrounded_events=ungrounded_events,
            hallucinations_detected=hallucinations,
            grounding_score=grounding_score,
        )

        return audit, status
