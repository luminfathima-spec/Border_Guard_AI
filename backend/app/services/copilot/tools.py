import time
import uuid
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.camera import Camera
from app.models.event import SecurityEvent
from app.models.incident import Incident
from app.models.evidence import Evidence
from app.models.report import Report
from app.models.alert import Alert
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.models.event_graph import EventLink, EvidenceObservation
from app.schemas.copilot import (
    SummarizeCameraEventsArgs,
    GetUnresolvedIncidentsArgs,
    FindEventsByZoneArgs,
    ExplainReportEvidenceArgs,
    SummarizeLinkedObservationsArgs,
    EscalateIncidentArgs,
    CopilotToolCall,
    CopilotPendingConfirmation,
)

class CopilotTools:
    """
    Strictly authorized, permission-guarded surveillance tools for the Copilot.
    Validates arguments via Pydantic, executes only allowed database operations,
    and never permits arbitrary SQL or shell commands.
    """

    @classmethod
    def summarize_camera_events(
        cls,
        db: Session,
        user: User,
        args_dict: Dict[str, Any],
    ) -> CopilotToolCall:
        start_time = time.time()
        args = SummarizeCameraEventsArgs(**args_dict)

        camera = db.query(Camera).filter(Camera.id == args.camera_id).first()
        if not camera:
            return CopilotToolCall(
                tool_name="summarize_camera_events",
                arguments=args_dict,
                result={"error": f"Camera with ID {args.camera_id} not found."},
                status="FAILED",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=args.time_window_hours)
        events = (
            db.query(SecurityEvent)
            .filter(SecurityEvent.camera_id == args.camera_id, SecurityEvent.timestamp >= cutoff)
            .order_by(SecurityEvent.timestamp.desc())
            .all()
        )

        severity_counts: Dict[str, int] = {}
        type_counts: Dict[str, int] = {}
        for ev in events:
            severity_counts[ev.severity] = severity_counts.get(ev.severity, 0) + 1
            type_counts[ev.event_type] = type_counts.get(ev.event_type, 0) + 1

        recent_samples = [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "severity": ev.severity,
                "confidence": ev.confidence,
                "timestamp": ev.timestamp.isoformat(),
                "description": ev.description,
            }
            for ev in events[:5]
        ]

        result = {
            "camera_id": camera.id,
            "camera_name": camera.name,
            "camera_identifier": camera.camera_identifier,
            "zone": camera.zone,
            "status": camera.status,
            "time_window_hours": args.time_window_hours,
            "total_events": len(events),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "recent_events": recent_samples,
        }

        return CopilotToolCall(
            tool_name="summarize_camera_events",
            arguments=args_dict,
            result=result,
            status="SUCCESS",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )

    @classmethod
    def get_incidents_with_unresolved_evidence(
        cls,
        db: Session,
        user: User,
        args_dict: Dict[str, Any],
    ) -> CopilotToolCall:
        start_time = time.time()
        args = GetUnresolvedIncidentsArgs(**args_dict)

        open_incidents = (
            db.query(Incident)
            .filter(Incident.status.in_(["OPEN", "IN_PROGRESS"]))
            .order_by(Incident.created_at.desc())
            .limit(args.limit * 2)
            .all()
        )

        unresolved_list: List[Dict[str, Any]] = []

        for inc in open_incidents:
            # Query EventLink for conflict or missing evidence markers
            links = db.query(EventLink).filter(EventLink.incident_id == inc.id).all()
            conflict_links = [l for l in links if l.relationship_type == "CONFLICTS_WITH"]
            missing_links = [l for l in links if l.relationship_type == "FLAGS_MISSING"]

            # Query contradictory or unverified EvidenceObservation items
            observations = db.query(EvidenceObservation).filter(EvidenceObservation.incident_id == inc.id).all()
            unresolved_obs = [
                o for o in observations
                if o.observation_type in ["CONFLICT_RECORD", "MISSING_DATA_GAP"]
            ]

            if conflict_links or missing_links or unresolved_obs or inc.severity in ["HIGH", "CRITICAL"]:
                gaps = []
                for c in conflict_links:
                    gaps.append(f"Conflicting observations between nodes: {c.creation_reason}")
                for m in missing_links:
                    gaps.append(f"Missing evidence gap: {m.creation_reason}")
                for o in unresolved_obs:
                    gaps.append(f"{o.observation_type}: {o.description}")

                unresolved_list.append({
                    "incident_id": inc.id,
                    "incident_number": inc.incident_number,
                    "title": inc.title,
                    "severity": inc.severity,
                    "status": inc.status,
                    "conflicts_count": len(conflict_links),
                    "missing_evidence_count": len(missing_links) + len(unresolved_obs),
                    "evidence_gaps": gaps[:4],
                    "created_at": inc.created_at.isoformat() if inc.created_at else None,
                })

            if len(unresolved_list) >= args.limit:
                break

        return CopilotToolCall(
            tool_name="get_incidents_with_unresolved_evidence",
            arguments=args_dict,
            result={
                "total_unresolved_found": len(unresolved_list),
                "incidents": unresolved_list,
            },
            status="SUCCESS",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )

    @classmethod
    def find_events_by_zone_and_time(
        cls,
        db: Session,
        user: User,
        args_dict: Dict[str, Any],
    ) -> CopilotToolCall:
        start_time = time.time()
        args = FindEventsByZoneArgs(**args_dict)

        # Find cameras associated with zone
        cameras_in_zone = (
            db.query(Camera)
            .filter(Camera.zone.ilike(f"%{args.zone_name}%"))
            .all()
        )
        camera_ids = [c.id for c in cameras_in_zone]

        query = db.query(SecurityEvent)
        if camera_ids:
            query = query.filter(
                (SecurityEvent.camera_id.in_(camera_ids)) |
                (SecurityEvent.description.ilike(f"%{args.zone_name}%"))
            )
        else:
            query = query.filter(SecurityEvent.description.ilike(f"%{args.zone_name}%"))

        if args.start_time:
            try:
                st = datetime.datetime.fromisoformat(args.start_time.replace("Z", "+00:00"))
                query = query.filter(SecurityEvent.timestamp >= st)
            except Exception:
                pass

        if args.end_time:
            try:
                et = datetime.datetime.fromisoformat(args.end_time.replace("Z", "+00:00"))
                query = query.filter(SecurityEvent.timestamp <= et)
            except Exception:
                pass

        matched_events = query.order_by(SecurityEvent.timestamp.desc()).limit(args.limit).all()

        cam_map = {c.id: c.name for c in cameras_in_zone}
        formatted_events = [
            {
                "id": ev.id,
                "client_event_id": ev.client_event_id,
                "event_type": ev.event_type,
                "severity": ev.severity,
                "camera_name": cam_map.get(ev.camera_id, f"Cam #{ev.camera_id}"),
                "confidence": ev.confidence,
                "timestamp": ev.timestamp.isoformat(),
                "description": ev.description,
            }
            for ev in matched_events
        ]

        return CopilotToolCall(
            tool_name="find_events_by_zone_and_time",
            arguments=args_dict,
            result={
                "zone_name": args.zone_name,
                "matched_cameras": [c.name for c in cameras_in_zone],
                "events_count": len(formatted_events),
                "events": formatted_events,
            },
            status="SUCCESS",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )

    @classmethod
    def explain_report_evidence(
        cls,
        db: Session,
        user: User,
        args_dict: Dict[str, Any],
    ) -> CopilotToolCall:
        start_time = time.time()
        args = ExplainReportEvidenceArgs(**args_dict)

        report = db.query(Report).filter(Report.id == args.report_id).first()
        if not report:
            return CopilotToolCall(
                tool_name="explain_report_evidence",
                arguments=args_dict,
                result={"error": f"Investigation report #{args.report_id} does not exist."},
                status="FAILED",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        sections = getattr(report, "sections_json", None) or getattr(report, "sections", None) or {}
        statements = sections.get("factual_statements", [])
        evidence_used = sections.get("evidence_used", [])

        # Calculate valid citation rate safely
        total_stmts = len(statements)
        unsupported = sum(1 for s in statements if s.get("citation_status") != "VERIFIED")
        valid_rate = round(((total_stmts - unsupported) / max(total_stmts, 1)) * 100.0, 1)

        # Corroborate evidence records from database
        evid_ids = [e.get("evidence_id") for e in evidence_used if e.get("evidence_id")]
        db_evids = db.query(Evidence).filter(Evidence.id.in_(evid_ids)).all() if evid_ids else []
        db_evid_map = {e.id: e for e in db_evids}

        statement_explanations = []
        for stmt in statements[:8]:
            sup_ids = stmt.get("supporting_evidence_ids", [])
            verified_support = []
            for sid in sup_ids:
                if sid in db_evid_map:
                    ev_item = db_evid_map[sid]
                    verified_support.append({
                        "evidence_id": sid,
                        "type": ev_item.evidence_type,
                        "file_path": ev_item.file_path,
                        "sha256": ev_item.checksum_sha256[:12] + "..." if ev_item.checksum_sha256 else "None",
                    })

            statement_explanations.append({
                "statement_id": stmt.get("statement_id"),
                "text": stmt.get("text"),
                "statement_type": stmt.get("statement_type"),
                "citation_status": stmt.get("citation_status"),
                "supporting_evidence": verified_support,
            })

        result = {
            "report_id": report.id,
            "report_number": report.report_number,
            "incident_id": report.incident_id,
            "title": report.title,
            "review_status": report.review_status,
            "valid_citation_rate": valid_rate,
            "total_evidence_files": len(evidence_used),
            "sha256_digest": report.checksum_sha256,
            "statements_audit": statement_explanations,
        }

        return CopilotToolCall(
            tool_name="explain_report_evidence",
            arguments=args_dict,
            result=result,
            status="SUCCESS",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )

    @classmethod
    def summarize_linked_observations(
        cls,
        db: Session,
        user: User,
        args_dict: Dict[str, Any],
    ) -> CopilotToolCall:
        start_time = time.time()
        args = SummarizeLinkedObservationsArgs(**args_dict)

        incident = db.query(Incident).filter(Incident.id == args.incident_id).first()
        if not incident:
            return CopilotToolCall(
                tool_name="summarize_linked_observations",
                arguments=args_dict,
                result={"error": f"Incident #{args.incident_id} not found."},
                status="FAILED",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        links = db.query(EventLink).filter(EventLink.incident_id == args.incident_id).all()
        observations = db.query(EvidenceObservation).filter(EvidenceObservation.incident_id == args.incident_id).all()

        direct_facts = [l for l in links if l.provenance_type == "DIRECT_OBSERVATION"]
        inferred = [l for l in links if l.provenance_type == "INFERRED_ASSOCIATION"]
        synthesized = [l for l in links if l.provenance_type == "DERIVED_SYNTHESIS"]

        obs_summary = [
            {
                "id": o.id,
                "type": o.observation_type,
                "title": o.title,
                "assertion": o.description,
                "is_verified": o.status == "VERIFIED" or (isinstance(o.details_json, dict) and o.details_json.get("is_verified_in_db", False)),
                "created_reason": (o.details_json.get("creation_reason") if isinstance(o.details_json, dict) else None) or o.source_system or "Direct sensor telemetry",
            }
            for o in observations
        ]

        result = {
            "incident_id": incident.id,
            "incident_number": incident.incident_number,
            "title": incident.title,
            "total_links": len(links),
            "direct_observations_count": len(direct_facts),
            "inferred_associations_count": len(inferred),
            "derived_syntheses_count": len(synthesized),
            "linked_observations": obs_summary,
            "key_relationships": [
                {
                    "source": f"{l.source_node_type} #{l.source_node_id}",
                    "relationship": l.relationship_type,
                    "target": f"{l.target_node_type} #{l.target_node_id}",
                    "confidence": l.confidence,
                    "reason": l.creation_reason,
                }
                for l in links[:6]
            ],
        }

        return CopilotToolCall(
            tool_name="summarize_linked_observations",
            arguments=args_dict,
            result=result,
            status="SUCCESS",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )

    @classmethod
    def escalate_incident(
        cls,
        db: Session,
        user: User,
        args_dict: Dict[str, Any],
    ) -> CopilotToolCall:
        """
        Consequential action tool: Requires explicit operator confirmation before execution.
        Also validates that user role is authorized (rejects VIEWER).
        """
        start_time = time.time()
        args = EscalateIncidentArgs(**args_dict)

        # Permission verification
        if user.role == UserRole.VIEWER.value:
            return CopilotToolCall(
                tool_name="escalate_incident",
                arguments=args_dict,
                result={"error": "Permission Denied: VIEWER role cannot trigger incident escalations."},
                status="FAILED",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        incident = db.query(Incident).filter(Incident.id == args.incident_id).first()
        if not incident:
            return CopilotToolCall(
                tool_name="escalate_incident",
                arguments=args_dict,
                result={"error": f"Incident #{args.incident_id} not found."},
                status="FAILED",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        # Consequential action safety check: If not confirmed, return pending confirmation payload
        if not args.confirmed:
            action_id = f"CONFIRM-{uuid.uuid4().hex[:8]}"
            return CopilotToolCall(
                tool_name="escalate_incident",
                arguments=args_dict,
                result={
                    "pending_confirmation": {
                        "action_id": action_id,
                        "action_type": "ESCALATE_INCIDENT",
                        "incident_id": incident.id,
                        "title": f"Confirm Escalation to {args.escalation_level}",
                        "description": (
                            f"Are you sure you want to escalate Incident {incident.incident_number} "
                            f"to tier '{args.escalation_level}'? Rationale: '{args.rationale}'."
                        ),
                        "payload": args_dict,
                    }
                },
                status="CONFIRMATION_REQUIRED",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        # Action is CONFIRMED -> Execute consequential change
        incident.severity = "CRITICAL"
        incident.status = "IN_PROGRESS"

        escalation_alert = Alert(
            incident_id=incident.id,
            severity="CRITICAL",
            title=f"ESCALATION: {args.escalation_level} Dispatched",
            message=f"Operator {user.name} ({user.email}) escalated incident. Rationale: {args.rationale}",
            status="NEW",
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(escalation_alert)

        # Record immutable audit entry
        audit_entry = AuditLog(
            user_id=user.id,
            user_email=user.email,
            action="COPILOT_ESCALATE_INCIDENT",
            resource_type="Incident",
            resource_id=str(incident.id),
            details={
                "escalation_level": args.escalation_level,
                "rationale": args.rationale,
                "incident_number": incident.incident_number,
            },
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(audit_entry)
        db.commit()

        return CopilotToolCall(
            tool_name="escalate_incident",
            arguments=args_dict,
            result={
                "incident_id": incident.id,
                "incident_number": incident.incident_number,
                "new_severity": incident.severity,
                "new_status": incident.status,
                "escalation_tier": args.escalation_level,
                "alert_id": escalation_alert.id,
                "message": f"Incident {incident.incident_number} successfully escalated to {args.escalation_level}.",
            },
            status="SUCCESS",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )
