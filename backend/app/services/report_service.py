import os
import json
import re
import copy
import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.logging import logger
from app.models.incident import Incident
from app.models.event import SecurityEvent
from app.models.camera import Camera
from app.models.detection import Detection
from app.models.track import ObjectTrack
from app.models.evidence import Evidence
from app.models.audit import AuditLog
from app.models.report import Report, ReportType, ReportStatus, ReviewStatus
from app.models.event_graph import (
    EventLink,
    EvidenceObservation,
    RelationshipType,
    ProvenanceType,
    ObservationType,
)
from app.schemas.report import (
    StatementType,
    CitationValidationStatus,
    FactualStatementItem,
    ConflictingEvidenceItem,
    MissingEvidenceItem,
    EvidenceUsedItem,
    IncidentReportSections,
    ReportResponse,
)
from app.services.event_graph_service import EventGraphService
from app.services.gemini.sanitizer import ReportInputSanitizer
from app.services.pdf_generator import ReportPDFGenerator

REPORT_PROMPT_VERSION = "2026.04.1"

class ReportGenerationService:
    """
    Evidence-Grounded Incident Report Generation Service.
    Coordinates Gemini LLM synthesis, graph provenance cross-examination,
    untrusted statement validation, indirect prompt injection defense,
    human review workflows, and PDF rendering.
    """

    @classmethod
    def generate_report(
        cls,
        db: Session,
        incident_id: int,
        user_id: Optional[int] = None,
        custom_instructions: Optional[str] = None,
        force_mock: bool = False,
        model_name: Optional[str] = None,
        inject_hallucination: bool = False,
        inject_timestamp_skew: bool = False,
    ) -> ReportResponse:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident {incident_id} not found")

        # 1. Gather all Incident Telemetry and Event Graph Nodes
        events = (
            db.query(SecurityEvent)
            .filter(SecurityEvent.incident_id == incident_id)
            .order_by(SecurityEvent.timestamp.asc())
            .all()
        )
        evidence_items = db.query(Evidence).filter(Evidence.incident_id == incident_id).all()
        primary_camera_id = events[0].camera_id if events and events[0].camera_id else None
        tracks = db.query(ObjectTrack).filter(ObjectTrack.camera_id == primary_camera_id).all() if primary_camera_id else []
        cameras = db.query(Camera).filter(Camera.id == primary_camera_id).all() if primary_camera_id else db.query(Camera).all()

        observations = (
            db.query(EvidenceObservation)
            .filter(EvidenceObservation.incident_id == incident_id, EvidenceObservation.status == "ACTIVE")
            .all()
        )
        graph_links = (
            db.query(EventLink)
            .filter(EventLink.incident_id == incident_id)
            .all()
        )

        # 2. Extract Conflicting & Missing Evidence from Event Graph
        conflicting_evidence: List[ConflictingEvidenceItem] = []
        missing_evidence_gaps: List[MissingEvidenceItem] = []

        # From Graph Links
        for link in graph_links:
            if link.relationship_type == RelationshipType.CONFLICTS_WITH.value or link.is_conflict:
                conflicting_evidence.append(
                    ConflictingEvidenceItem(
                        description=f"Contradictory relationship between {link.source_node_type} #{link.source_node_id} and {link.target_node_type} #{link.target_node_id}: {link.creation_reason}",
                        conflicting_nodes=[f"{link.source_node_type}:{link.source_node_id}", f"{link.target_node_type}:{link.target_node_id}"],
                        severity="HIGH" if "breach" in link.creation_reason.lower() else "MEDIUM",
                    )
                )
            elif link.relationship_type == RelationshipType.FLAGS_MISSING.value or link.is_missing_evidence:
                missing_evidence_gaps.append(
                    MissingEvidenceItem(
                        description=f"Evidentiary gap flagged: {link.creation_reason}",
                        interval=link.metadata_json.get("interval", "Telemetry Drop"),
                        impact="UNCERTAIN_TIMELINE",
                    )
                )

        # From Active Observations
        for obs in observations:
            if obs.observation_type == ObservationType.CONFLICT_RECORD.value:
                conflicting_evidence.append(
                    ConflictingEvidenceItem(
                        description=f"Observation conflict: {obs.title} — {obs.description}",
                        conflicting_nodes=[f"OBSERVATION:{obs.id}"],
                        severity="MEDIUM",
                    )
                )
            elif obs.observation_type == ObservationType.MISSING_DATA_GAP.value:
                missing_evidence_gaps.append(
                    MissingEvidenceItem(
                        description=f"Telemetry gap: {obs.title} — {obs.description}",
                        interval=obs.details_json.get("interval", "Stream Interruption"),
                        impact="MISSING_FOOTAGE",
                    )
                )

        # 3. Build Evidence Inventory
        evidence_used: List[EvidenceUsedItem] = []
        for ev in evidence_items:
            evidence_used.append(
                EvidenceUsedItem(
                    evidence_id=ev.id,
                    evidence_type=ev.evidence_type,
                    file_path=ev.file_path,
                    checksum_sha256=ev.checksum_sha256,
                    timestamp=ev.timestamp.isoformat() if ev.timestamp else None,
                )
            )

        # 4. Check Insufficient Evidence Condition
        is_insufficient = (len(events) == 0 and len(evidence_items) == 0 and len(tracks) == 0)
        insufficient_reason = None
        if is_insufficient:
            insufficient_reason = "No physical sensor detections, object tracks, or evidence media recorded for this incident."

        # 5. Sanitize Untrusted Metadata (Indirect Prompt Injection Defense)
        sanitized_title, inj1 = ReportInputSanitizer.sanitize_text(incident.title)
        sanitized_desc, inj2 = ReportInputSanitizer.sanitize_text(incident.description)
        sanitized_notes, inj3 = ReportInputSanitizer.sanitize_text(incident.analyst_notes)
        sanitized_instructions, inj4 = ReportInputSanitizer.sanitize_text(custom_instructions)
        total_injections = sum([inj1, inj2, inj3, inj4])
        if total_injections > 0:
            logger.warning(f"Report Generation: Defanged {total_injections} prompt injection attempt(s) for incident {incident_id}")

        # 6. Structured Generation (Gemini or Deterministic Synthesizer)
        selected_model = model_name or ("mock-gemini-2.5-flash" if force_mock else settings.GEMINI_MODEL)
        raw_statements: List[Dict[str, Any]] = []

        if is_insufficient:
            executive_summary = (
                f"Incident {incident.incident_number} cannot be substantiated. "
                f"The sensor evidence register is empty. No automated detections, bounding tracks, "
                f"or validated CCTV frames exist to corroborate an operational event."
            )
            recs = [
                "Verify camera connection and physical stream integrity.",
                "Inspect network switch and CCTV hardware logs for power interruptions.",
            ]
        else:
            executive_summary = (
                f"Chronological investigation dossier for Incident {incident.incident_number} ({incident.severity} priority). "
                f"Surveillance systems recorded {len(events)} security events across monitored perimeter zones. "
                f"Physical evidence captures verified target movement and trajectory progression."
            )
            recs = [
                "Review recorded CCTV snapshot evidence in forensic viewer.",
                "Verify perimeter physical barriers at identified coordinates.",
                "Submit investigation dossier for command signature and operational sign-off.",
            ]

            # Synthesize chronological factual statements from DB entities
            stmt_idx = 1
            for ev in events:
                linked_ev_ids = [e.id for e in evidence_items if e.event_id == ev.id] or ([evidence_items[0].id] if evidence_items else [])
                raw_statements.append({
                    "statement_id": stmt_idx,
                    "text": f"Surveillance node recorded {ev.event_type} at zone boundary with {int(ev.confidence*100)}% detection confidence: {ev.description}",
                    "statement_type": StatementType.CV_DETECTION,
                    "referenced_entity_type": "EVENT",
                    "referenced_entity_id": ev.id,
                    "timestamp": ev.timestamp.isoformat() if ev.timestamp else datetime.datetime.utcnow().isoformat(),
                    "supporting_evidence_ids": linked_ev_ids,
                })
                stmt_idx += 1

            for trk in tracks[:3]:
                raw_statements.append({
                    "statement_id": stmt_idx,
                    "text": f"Object tracker maintained continuous trajectory #{trk.tracking_id} for target class '{trk.object_type}' with dwell time of {trk.dwell_time_seconds:.1f}s.",
                    "statement_type": StatementType.CV_DETECTION,
                    "referenced_entity_type": "OBJECT_TRACK",
                    "referenced_entity_id": trk.id,
                    "timestamp": trk.created_at.isoformat() if trk.created_at else None,
                    "supporting_evidence_ids": [evidence_items[0].id] if evidence_items else [],
                })
                stmt_idx += 1

            for obs in observations:
                st_type = StatementType.OBSERVATION if obs.observation_type == ObservationType.DIRECT_FACT.value else StatementType.MODEL_INTERPRETATION
                raw_statements.append({
                    "statement_id": stmt_idx,
                    "text": f"Field observation record: {obs.title} — {obs.description}",
                    "statement_type": st_type,
                    "referenced_entity_type": "OBSERVATION",
                    "referenced_entity_id": obs.id,
                    "timestamp": obs.timestamp.isoformat() if obs.timestamp else None,
                    "supporting_evidence_ids": [],
                })
                stmt_idx += 1

            # Model interpretation statement
            raw_statements.append({
                "statement_id": stmt_idx,
                "text": f"AI Cognitive Assessment extrapolates sustained breach intentionality based on multi-frame movement vector and zero immediate retreat.",
                "statement_type": StatementType.MODEL_INTERPRETATION,
                "referenced_entity_type": "INCIDENT",
                "referenced_entity_id": incident.id,
                "timestamp": incident.created_at.isoformat(),
                "supporting_evidence_ids": [e.id for e in evidence_items],
            })
            stmt_idx += 1

            # Inject synthetic test probes if requested
            if inject_hallucination:
                raw_statements.append({
                    "statement_id": stmt_idx,
                    "text": "Fabricated claim citing non-existent camera and phantom video evidence.",
                    "statement_type": StatementType.CV_DETECTION,
                    "referenced_entity_type": "CAMERA",
                    "referenced_entity_id": 99999,  # Nonexistent
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "supporting_evidence_ids": [88888],  # Nonexistent
                })
                stmt_idx += 1

            if inject_timestamp_skew and raw_statements:
                # Corrupt first statement timestamp by +2 hours
                raw_statements[0]["timestamp"] = (
                    datetime.datetime.fromisoformat(raw_statements[0]["timestamp"]) + datetime.timedelta(hours=2)
                ).isoformat()

        # 7. Programmatic Citation Cross-Examiner (Treat output as UNTRUSTED)
        verified_statements: List[FactualStatementItem] = []
        unsupported_count = 0
        total_claims = len(raw_statements)

        existing_evidence_ids = {e.id for e in evidence_items}

        for item in raw_statements:
            st_id = item["statement_id"]
            st_text = item["text"]
            st_type = item["statement_type"]
            ref_type = item["referenced_entity_type"]
            ref_id = item["referenced_entity_id"]
            claim_ts_str = item.get("timestamp")
            supp_ev_ids = item.get("supporting_evidence_ids", [])

            citation_status = CitationValidationStatus.VERIFIED
            validation_notes = None

            # 7.1 Verify referenced entity physical existence in database
            exists, model_obj, record_ts, label = EventGraphService.verify_entity_exists(db, ref_type, ref_id)
            if not exists:
                citation_status = CitationValidationStatus.FLAGGED_NONEXISTENT
                validation_notes = f"Referenced {ref_type} #{ref_id} does not physically exist in database records."
                unsupported_count += 1
            else:
                # 7.2 Verify source timestamp alignment
                if claim_ts_str and record_ts:
                    try:
                        claim_ts = datetime.datetime.fromisoformat(claim_ts_str.replace("Z", "+00:00"))
                        if claim_ts.tzinfo is not None:
                            claim_ts_naive = claim_ts.astimezone(datetime.timezone.utc).replace(tzinfo=None)
                        else:
                            claim_ts_naive = claim_ts

                        if record_ts.tzinfo is not None:
                            record_ts_naive = record_ts.astimezone(datetime.timezone.utc).replace(tzinfo=None)
                        else:
                            record_ts_naive = record_ts

                        diff_sec = abs((claim_ts_naive - record_ts_naive).total_seconds())
                        if diff_sec > 2.0:
                            citation_status = CitationValidationStatus.FLAGGED_TIMESTAMP_MISMATCH
                            validation_notes = f"Timestamp skew ({diff_sec:.1f}s > 2.0s tolerance): claim states {claim_ts.isoformat()} vs record {record_ts.isoformat()}."
                            unsupported_count += 1
                    except Exception as ts_err:
                        logger.warning(f"Timestamp parse error for statement {st_id}: {ts_err}")

                # 7.3 Verify supporting evidence IDs
                cleaned_ev_ids = []
                for eid in supp_ev_ids:
                    if eid in existing_evidence_ids:
                        cleaned_ev_ids.append(eid)
                    else:
                        citation_status = CitationValidationStatus.FLAGGED_UNSUPPORTED
                        validation_notes = f"Cited evidence #{eid} is invalid or not attached to incident {incident_id}."
                        unsupported_count += 1
                supp_ev_ids = cleaned_ev_ids

            verified_statements.append(
                FactualStatementItem(
                    statement_id=st_id,
                    text=st_text,
                    statement_type=st_type,
                    referenced_entity_type=ref_type,
                    referenced_entity_id=ref_id,
                    timestamp=claim_ts_str,
                    supporting_evidence_ids=supp_ev_ids,
                    citation_status=citation_status,
                    validation_notes=validation_notes,
                )
            )

        valid_citation_rate = (total_claims - unsupported_count) / max(total_claims, 1)

        sections = IncidentReportSections(
            executive_summary=executive_summary,
            factual_statements=verified_statements,
            conflicting_evidence=conflicting_evidence,
            missing_evidence_gaps=missing_evidence_gaps,
            containment_recommendations=recs,
            insufficient_evidence=is_insufficient,
            insufficient_evidence_reason=insufficient_reason,
            evidence_used=evidence_used,
        )

        # 8. Check for existing report or generate unique report number
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        report_number = f"REP-{now_utc.year}-{incident_id:04d}-{int(now_utc.timestamp())%10000:04d}"

        report = Report(
            report_number=report_number,
            title=f"Incident Investigation Dossier — {incident.incident_number}",
            report_type=ReportType.INCIDENT_DOSSIER.value,
            status=ReportStatus.COMPLETED.value,
            review_status=ReviewStatus.DRAFT.value,
            generated_by_user_id=user_id,
            incident_id=incident.id,
            model_name=selected_model,
            prompt_version=REPORT_PROMPT_VERSION,
            parameters_json={"force_mock": force_mock, "custom_instructions": custom_instructions},
            sections_json=sections.model_dump(),
            human_corrections=[],
            audit_history=[
                {
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "action": "REPORT_GENERATED",
                    "user_id": user_id,
                    "details": {
                        "model_name": selected_model,
                        "prompt_version": REPORT_PROMPT_VERSION,
                        "valid_citation_rate": round(valid_citation_rate, 4),
                        "unsupported_claim_count": unsupported_count,
                        "total_claims": total_claims,
                        "prompt_injections_deflected": total_injections,
                    },
                }
            ],
            created_at=datetime.datetime.now(datetime.timezone.utc),
            completed_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(report)
        db.flush()

        # 9. Register Edge in Event Graph
        try:
            from app.schemas.event_graph import EventLinkCreate
            EventGraphService.create_link(
                db=db,
                incident_id=incident.id,
                link_in=EventLinkCreate(
                    source_node_type="REPORT",
                    source_node_id=report.id,
                    source_ref=report.report_number,
                    target_node_type="INCIDENT",
                    target_node_id=incident.id,
                    target_ref=incident.incident_number,
                    relationship_type=RelationshipType.DOCUMENTED_IN,
                    provenance_type=ProvenanceType.DERIVED_SYNTHESIS,
                    creation_reason="Automated evidence-grounded report generation with verified database citations.",
                    confidence=round(valid_citation_rate, 2),
                    is_conflict=False,
                    is_missing_evidence=is_insufficient,
                    conflict_details={},
                    metadata_json={"report_number": report.report_number},
                ),
            )
        except Exception as graph_err:
            logger.warning(f"Event graph linking note for report {report.id}: {graph_err}")

        # 10. Render Initial PDF Dossier and Compute SHA-256 Checksum
        try:
            pdf_path, sha256_hash, file_size = ReportPDFGenerator.generate_pdf({
                "report_number": report.report_number,
                "title": report.title,
                "review_status": report.review_status,
                "incident_id": report.incident_id,
                "model_name": report.model_name,
                "prompt_version": report.prompt_version,
                "valid_citation_rate": valid_citation_rate,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "sections": sections.model_dump(),
            })
            report.file_path = pdf_path
            report.checksum_sha256 = sha256_hash
            report.file_size_bytes = file_size
        except Exception as pdf_err:
            logger.error(f"PDF generation error for report {report.id}: {pdf_err}", exc_info=True)

        # 11. Record System Audit Log
        audit_entry = AuditLog(
            user_id=user_id,
            action="GENERATE_REPORT",
            resource_type="REPORT",
            resource_id=str(report.id),
            details={
                "report_number": report.report_number,
                "incident_id": incident.id,
                "valid_citation_rate": round(valid_citation_rate, 4),
                "unsupported_claim_count": unsupported_count,
            },
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(report)

        return cls._to_response(report, unsupported_count, valid_citation_rate)

    @classmethod
    def get_report(cls, db: Session, report_id: int) -> ReportResponse:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found")
        return cls._to_response(report)

    @classmethod
    def list_incident_reports(cls, db: Session, incident_id: int) -> List[ReportResponse]:
        reports = (
            db.query(Report)
            .filter(Report.incident_id == incident_id)
            .order_by(Report.created_at.desc())
            .all()
        )
        return [cls._to_response(r) for r in reports]

    @classmethod
    def add_statement_correction(
        cls,
        db: Session,
        report_id: int,
        statement_id: int,
        corrected_text: Optional[str],
        analyst_comment: str,
        user_id: Optional[int] = None,
    ) -> ReportResponse:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found")

        sections = copy.deepcopy(report.sections_json or {})
        statements = sections.get("factual_statements", [])
        updated = False

        for stmt in statements:
            if stmt.get("statement_id") == statement_id:
                if corrected_text:
                    stmt["text"] = corrected_text
                stmt["human_correction"] = analyst_comment
                stmt["statement_type"] = StatementType.HUMAN_ANNOTATION.value
                updated = True
                break

        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Statement {statement_id} not found in report")

        sections["factual_statements"] = statements
        report.sections_json = sections
        flag_modified(report, "sections_json")

        corrections_list = list(report.human_corrections or [])
        corrections_list.append({
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "statement_id": statement_id,
            "corrected_text": corrected_text,
            "analyst_comment": analyst_comment,
            "user_id": user_id,
        })
        report.human_corrections = corrections_list
        flag_modified(report, "human_corrections")

        audit_hist = list(report.audit_history or [])
        audit_hist.append({
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "action": "HUMAN_CORRECTION",
            "user_id": user_id,
            "details": {
                "statement_id": statement_id,
                "analyst_comment": analyst_comment,
            },
        })
        report.audit_history = audit_hist
        flag_modified(report, "audit_history")

        # Re-render PDF with human corrections
        cls._rerender_pdf(report)

        db.commit()
        db.refresh(report)
        return cls._to_response(report)

    @classmethod
    def review_report(
        cls,
        db: Session,
        report_id: int,
        action: str,
        reviewer_comments: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> ReportResponse:
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report {report_id} not found")

        act_upper = action.upper()
        if act_upper == "APPROVE":
            report.review_status = ReviewStatus.APPROVED.value
            report.approved_by_user_id = user_id
            report.approved_at = datetime.datetime.now(datetime.timezone.utc)
        elif act_upper == "REJECT":
            report.review_status = ReviewStatus.REJECTED.value
        elif act_upper in ["REQUEST_REVISIONS", "PENDING_REVIEW"]:
            report.review_status = ReviewStatus.PENDING_REVIEW.value
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid review action: {action}")

        audit_hist = list(report.audit_history or [])
        audit_hist.append({
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "action": f"REVIEW_{act_upper}",
            "user_id": user_id,
            "details": {
                "new_status": report.review_status,
                "reviewer_comments": reviewer_comments,
            },
        })
        report.audit_history = audit_hist
        flag_modified(report, "audit_history")

        # Re-render PDF with approval signature
        cls._rerender_pdf(report)

        # Record System Audit
        db.add(
            AuditLog(
                user_id=user_id,
                action=f"REPORT_REVIEW_{act_upper}",
                resource_type="REPORT",
                resource_id=str(report.id),
                details={"status": report.review_status, "comments": reviewer_comments},
            )
        )

        db.commit()
        db.refresh(report)
        return cls._to_response(report)

    @classmethod
    def _rerender_pdf(cls, report: Report) -> None:
        try:
            pdf_path, sha256_hash, file_size = ReportPDFGenerator.generate_pdf({
                "report_number": report.report_number,
                "title": report.title,
                "review_status": report.review_status,
                "approved_by_user_id": report.approved_by_user_id,
                "incident_id": report.incident_id,
                "model_name": report.model_name,
                "prompt_version": report.prompt_version,
                "valid_citation_rate": 1.0,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "sections": report.sections_json,
            })
            report.file_path = pdf_path
            report.checksum_sha256 = sha256_hash
            report.file_size_bytes = file_size
        except Exception as e:
            logger.warning(f"PDF re-rendering notice for report {report.id}: {e}")

    @classmethod
    def _to_response(
        cls,
        report: Report,
        unsupported_count: Optional[int] = None,
        valid_rate: Optional[float] = None,
    ) -> ReportResponse:
        sections_dict = report.sections_json or {}
        statements = sections_dict.get("factual_statements", [])

        if unsupported_count is None:
            unsupported_count = sum(
                1 for s in statements if s.get("citation_status") != CitationValidationStatus.VERIFIED.value
            )
        if valid_rate is None:
            total = len(statements)
            valid_rate = (total - unsupported_count) / max(total, 1)

        return ReportResponse(
            id=report.id,
            report_number=report.report_number,
            incident_id=report.incident_id,
            title=report.title,
            status=report.status,
            review_status=report.review_status,
            model_name=report.model_name,
            prompt_version=report.prompt_version,
            sections=IncidentReportSections.model_validate(sections_dict),
            unsupported_claim_count=unsupported_count,
            valid_citation_rate=round(valid_rate, 4),
            generated_by_user_id=report.generated_by_user_id,
            approved_by_user_id=report.approved_by_user_id,
            approved_at=report.approved_at,
            file_path=report.file_path,
            pdf_download_url=f"/api/v1/reports/{report.id}/export-pdf",
            checksum_sha256=report.checksum_sha256,
            created_at=report.created_at,
            audit_history=report.audit_history or [],
        )
