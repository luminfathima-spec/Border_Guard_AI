import os
import json
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.incident import Incident
from app.models.event import SecurityEvent
from app.models.camera import Camera
from app.models.alert import Alert
from app.models.evidence import Evidence
from app.models.audit import AuditLog
from app.models.ai_analysis import AIAnalysis, AnalysisStatus
from app.services.gemini.prompts import PROMPT_VERSION, SYSTEM_INSTRUCTION, build_incident_prompt
from app.services.gemini.client import get_gemini_client
from app.services.gemini.cross_examiner import CrossExaminer
from app.services.gemini.frame_selector import EventTriggeredFrameSelector
from app.services.edge.network_controller import NetworkStateController

class GeminiService:
    @staticmethod
    def is_configured() -> bool:
        return bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5)

    @classmethod
    def verify_gemini_connection(cls) -> Dict[str, Any]:
        """
        Diagnostic probe to test Google Gemini API configuration and live connectivity.
        Reports exact status, model name, and error categorization without leaking secrets.
        """
        if not cls.is_configured():
            return {
                "configured": False,
                "status": "BLOCKED_NO_KEY",
                "message": "Live Gemini verification blocked: GEMINI_API_KEY is not configured.",
                "model_name": settings.GEMINI_MODEL,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "is_live_success": False,
                "is_mock": True,
            }

        try:
            from app.services.gemini.client import RealGeminiClient
            real_client = RealGeminiClient()
            probe_result = real_client.ping_connectivity()
            probe_result["configured"] = True
            probe_result["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            return probe_result
        except Exception as e:
            from app.services.gemini.client import RealGeminiClient
            category = RealGeminiClient.categorize_error(e)
            sanitized_msg = str(e)
            if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
                sanitized_msg = sanitized_msg.replace(settings.GEMINI_API_KEY.strip(), "[REDACTED_API_KEY]")
            logger.error(f"Live Gemini connectivity verification failed ({category}): {sanitized_msg}")
            return {
                "configured": True,
                "status": "FAILED",
                "error_category": category,
                "message": f"Live Gemini request failed: {sanitized_msg}",
                "model_name": settings.GEMINI_MODEL,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "is_live_success": False,
                "is_mock": False,
            }

    @classmethod
    def _call_gemini_api(cls, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        """
        Executes text generation using the official Google GenAI Python SDK if configured.
        """
        if not cls.is_configured():
            return None

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(
                api_key=settings.GEMINI_API_KEY,
                http_options=types.HttpOptions(timeout=30000),
            )
            config = types.GenerateContentConfig(
                temperature=0.2,
                top_p=0.95,
                max_output_tokens=1500,
            )
            if system_instruction:
                config.system_instruction = system_instruction

            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=config,
            )
            return response.text
        except Exception as e:
            err_msg = str(e)
            if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
                err_msg = err_msg.replace(settings.GEMINI_API_KEY.strip(), "[REDACTED_API_KEY]")
            logger.error(f"Google Gemini API error: {err_msg}", exc_info=True)
            return None

    @classmethod
    def analyze_incident(
        cls,
        db: Session,
        incident_id: int,
        custom_instructions: Optional[str] = None,
        force_mock: bool = False,
        include_keyframes: bool = True,
        inject_hallucination: bool = False,
    ) -> Dict[str, Any]:
        """
        Orchestrates full Phase 5 Gemini Intelligence Workflow:
        1. Queries PostgreSQL for verified sensor facts, camera IDs, events, and evidence.
        2. Selects relevant event-triggered keyframes.
        3. Formulates a versioned, privacy-sanitized prompt.
        4. Calls Google Gemini (or MockGeminiClient) enforcing JSON schema compliance.
        5. Runs CrossExaminer Evidence Safeguard to quarantine ungrounded claims.
        6. Persists structured AIAnalysis record and links to the Provenance Event Graph.
        """
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        # Phase 8: Explicit Offline and Unreachable Handling (Zero Fabrication)
        if NetworkStateController.is_offline():
            status_val = AnalysisStatus.PENDING_NETWORK.value
            ai_record = AIAnalysis(
                incident_id=incident.id,
                model_name=settings.GEMINI_MODEL,
                prompt_type="STRUCTURED_INCIDENT_ANALYSIS",
                prompt_version=PROMPT_VERSION,
                raw_prompt="[PROMPT_BUFFERED_OFFLINE]",
                analysis_result="AI reasoning is PENDING: external Google Gemini service unreachable during edge network outage.",
                structured_output={
                    "status": status_val,
                    "pending": True,
                    "reason": "Edge network is currently OFFLINE.",
                    "suggested_human_actions": ["Wait for edge network reconnection", "Inspect local CCTV camera telemetry"],
                },
                confidence_score=0.0,
                grounded_citations={},
                token_count=0,
                execution_time_ms=0,
                status=status_val,
                created_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.add(ai_record)
            db.commit()
            db.refresh(ai_record)
            return {
                "id": ai_record.id,
                "analysis_id": ai_record.id,
                "incident_id": incident.id,
                "model_name": ai_record.model_name,
                "prompt_type": ai_record.prompt_type,
                "prompt_version": ai_record.prompt_version,
                "analysis_result": ai_record.analysis_result,
                "summary": ai_record.analysis_result,
                "structured_output": ai_record.structured_output,
                "grounded_citations": {},
                "confidence_score": 0.0,
                "token_count": 0,
                "execution_time_ms": 0,
                "status": status_val,
                "is_mock": False,
                "is_pending": True,
                "created_at": ai_record.created_at,
            }

        if settings.EDGE_MODE and not cls.is_configured() and not force_mock:
            status_val = AnalysisStatus.UNAVAILABLE.value
            ai_record = AIAnalysis(
                incident_id=incident.id,
                model_name=settings.GEMINI_MODEL,
                prompt_type="STRUCTURED_INCIDENT_ANALYSIS",
                prompt_version=PROMPT_VERSION,
                raw_prompt="[SERVICE_UNAVAILABLE]",
                analysis_result="AI reasoning UNAVAILABLE: Google Gemini API key is not configured on this edge node.",
                structured_output={
                    "status": status_val,
                    "unavailable": True,
                    "suggested_human_actions": ["Deploy cloud synchronization bridge", "Configure edge API key credentials"],
                },
                confidence_score=0.0,
                grounded_citations={},
                token_count=0,
                execution_time_ms=0,
                status=status_val,
                created_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.add(ai_record)
            db.commit()
            db.refresh(ai_record)
            return {
                "id": ai_record.id,
                "analysis_id": ai_record.id,
                "incident_id": incident.id,
                "model_name": ai_record.model_name,
                "prompt_type": ai_record.prompt_type,
                "prompt_version": ai_record.prompt_version,
                "analysis_result": ai_record.analysis_result,
                "summary": ai_record.analysis_result,
                "structured_output": ai_record.structured_output,
                "grounded_citations": {},
                "confidence_score": 0.0,
                "token_count": 0,
                "execution_time_ms": 0,
                "status": status_val,
                "is_mock": False,
                "is_unavailable": True,
                "created_at": ai_record.created_at,
            }

        events = (
            db.query(SecurityEvent)
            .filter(SecurityEvent.incident_id == incident_id)
            .order_by(SecurityEvent.timestamp.asc())
            .all()
        )
        alerts = db.query(Alert).filter(Alert.incident_id == incident_id).all()
        evidence_items = db.query(Evidence).filter(Evidence.incident_id == incident_id).all()

        # 1. Event-Triggered Multimodal Keyframe Selection
        keyframes: List[bytes] = []
        if include_keyframes:
            try:
                keyframes = EventTriggeredFrameSelector.select_incident_keyframes(db, incident_id, max_frames=3)
            except Exception as kf_err:
                logger.warning(f"Keyframe selection notice for incident {incident_id}: {kf_err}")

        # 2. Extract primary camera ID
        primary_cam_id = None
        if events and events[0].camera_id:
            primary_cam_id = events[0].camera_id
        elif alerts and alerts[0].camera_id:
            primary_cam_id = alerts[0].camera_id

        # 3. Assemble structured sensor telemetry
        facts = {
            "incident_id": incident.id,
            "incident_number": incident.incident_number,
            "title": incident.title,
            "severity": incident.severity,
            "camera_id": primary_cam_id,
            "created_at": incident.created_at.isoformat() if incident.created_at else datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "events_count": len(events),
            "events": [
                {
                    "id": ev.id,
                    "type": ev.event_type,
                    "severity": ev.severity,
                    "timestamp": ev.timestamp.isoformat() if ev.timestamp else "",
                    "description": ev.description,
                    "confidence": ev.confidence,
                }
                for ev in events
            ],
            "evidence_items": [
                {
                    "id": ev.id,
                    "evidence_type": ev.evidence_type,
                    "file_path": ev.file_path,
                    "checksum": ev.checksum_sha256,
                }
                for ev in evidence_items
            ],
            "alerts": [
                {"id": a.id, "title": a.title, "severity": a.severity, "status": a.status}
                for a in alerts
            ],
            "evidence_items_count": len(evidence_items),
        }

        # 4. Construct Versioned Prompt
        prompt = build_incident_prompt(facts, custom_instructions)

        # 5. Invoke Gemini Client (Real or Mock)
        client = get_gemini_client(force_mock=force_mock, inject_hallucination=inject_hallucination)
        structured_obj, metadata = client.generate_structured_analysis(
            prompt=prompt,
            images=keyframes if keyframes else None,
            system_instruction=SYSTEM_INSTRUCTION,
        )

        # 6. Execute Deterministic Cross-Examiner Safeguard
        audit, status_str = CrossExaminer.verify(db, structured_obj, incident_id)

        # 7. Persist AI Analysis Record
        ai_record = AIAnalysis(
            incident_id=incident.id,
            model_name=metadata["model_name"],
            prompt_type="STRUCTURED_INCIDENT_ANALYSIS",
            prompt_version=PROMPT_VERSION,
            raw_prompt=prompt,
            analysis_result=structured_obj.summary,
            structured_output=structured_obj.model_dump(),
            confidence_score=audit.grounding_score,
            grounded_citations=audit.model_dump(),
            token_count=metadata.get("token_count", 0),
            execution_time_ms=metadata.get("execution_time_ms", 0),
            status=status_str,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(ai_record)
        db.commit()
        db.refresh(ai_record)

        # 8. Link in Provenance Event Graph (EventLink)
        try:
            from app.models.event_graph import EventLink
            edge = EventLink(
                incident_id=incident.id,
                source_node_type="AI_ANALYSIS",
                source_node_id=ai_record.id,
                target_node_type="INCIDENT",
                target_node_id=incident.id,
                relationship_type="ANALYZED_BY",
                provenance_type="DERIVED_SYNTHESIS",
                creation_reason=f"Gemini structured tactical incident analysis (v{PROMPT_VERSION})",
                confidence=audit.grounding_score,
                source_timestamp=ai_record.created_at,
                target_timestamp=incident.created_at,
            )
            db.add(edge)
            db.commit()
        except Exception as edge_err:
            logger.warning(f"EventLink creation notice: {edge_err}")

        # 9. Update Incident with Verified Output
        incident.ai_summary = structured_obj.summary
        incident.ai_recommendations = structured_obj.suggested_human_actions
        incident.ai_last_generated_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        db.refresh(incident)

        return {
            "id": ai_record.id,
            "incident_id": incident.id,
            "model_name": metadata["model_name"],
            "prompt_type": ai_record.prompt_type,
            "prompt_version": ai_record.prompt_version,
            "analysis_result": ai_record.analysis_result,
            "structured_output": structured_obj.model_dump(),
            "grounded_citations": audit.model_dump(),
            "confidence_score": audit.grounding_score,
            "token_count": ai_record.token_count,
            "execution_time_ms": ai_record.execution_time_ms,
            "status": ai_record.status,
            "is_mock": metadata.get("is_mock", False),
            "created_at": ai_record.created_at,
        }

    @classmethod
    def generate_incident_summary(
        cls,
        db: Session,
        incident_id: int,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Backward-compatible wrapper returning AISummaryResponse format backed by the full Phase 5 pipeline.
        """
        detailed = cls.analyze_incident(db, incident_id, custom_instructions=custom_instructions)
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        return {
            "incident_id": detailed["incident_id"],
            "incident_number": incident.incident_number if incident else f"INC-{incident_id}",
            "ai_summary": detailed["analysis_result"],
            "ai_recommendations": detailed["structured_output"].get("suggested_human_actions", []),
            "model_used": detailed["model_name"],
            "source_facts": detailed["grounded_citations"],
        }

    @classmethod
    def chat_assistant(
        cls,
        db: Session,
        message: str,
        conversation_history: List[Dict[str, str]],
        camera_id: Optional[int] = None,
        incident_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Interactive AI Assistant for Security Analysts to query operational surveillance facts in natural language.
        """
        # Fetch relevant database context
        total_cameras = db.query(Camera).count()
        online_cameras = db.query(Camera).filter(Camera.status == "ONLINE").count()
        recent_events = db.query(SecurityEvent).order_by(SecurityEvent.timestamp.desc()).limit(15).all()
        recent_alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(15).all()
        open_incidents = db.query(Incident).filter(Incident.status.in_(["OPEN", "IN_PROGRESS"])).all()

        context_data = {
            "total_cameras": total_cameras,
            "online_cameras": online_cameras,
            "open_incidents": [
                {"id": i.id, "number": i.incident_number, "title": i.title, "severity": i.severity, "status": i.status}
                for i in open_incidents
            ],
            "recent_alerts": [
                {"id": a.id, "severity": a.severity, "title": a.title, "status": a.status}
                for a in recent_alerts
            ],
            "recent_events": [
                {"id": e.id, "type": e.event_type, "severity": e.severity, "desc": e.description}
                for e in recent_events
            ]
        }

        system_instruction = (
            "You are the SentinelAI Command Assistant, a security operations copilot for border surveillance analysts. "
            "You have direct visibility into live surveillance telemetry, camera statuses, alerts, and open incidents. "
            "Answer analyst questions accurately, concisely, and professionally based strictly on available context data. "
            "Provide helpful operational suggestions where appropriate."
        )

        history_formatted = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history[-5:]])
        prompt = f"""
Current Surveillance Operations Database State:
```json
{json.dumps(context_data, indent=2)}
```

Recent Conversation:
{history_formatted}

Analyst Query: {message}

Provide a helpful, precise response. Include 2-3 short suggested next actions.
"""

        gemini_text = cls._call_gemini_api(prompt, system_instruction)
        model_used = settings.GEMINI_MODEL if gemini_text else "Heuristic Rule-Based Assistant"

        if not gemini_text:
            # Deterministic heuristic answer generator for standard queries
            msg_lower = message.lower()
            if "camera" in msg_lower or "cam" in msg_lower:
                gemini_text = (
                    f"**System Status**: Currently monitoring **{total_cameras}** surveillance cameras "
                    f"({online_cameras} online, {total_cameras - online_cameras} degraded/offline). "
                    f"Perimeter watchtowers and checkpoint feeds are actively being processed by YOLOv8."
                )
                suggested_actions = ["View Live Camera Grid", "Check Sector 4 Feed", "Configure Tripwires"]
            elif "alert" in msg_lower or "incident" in msg_lower or "critical" in msg_lower:
                gemini_text = (
                    f"**Alert Overview**: There are currently **{len(open_incidents)}** active investigations and "
                    f"**{len(recent_alerts)}** recent alerts logged in the system. High priority cases include "
                    f"`{open_incidents[0].incident_number if open_incidents else 'None'}`."
                )
                suggested_actions = ["Triage Critical Alerts", "Generate Incident Report", "Dispatch QRT"]
            else:
                gemini_text = (
                    f"I am monitoring all active border sectors. I can summarize security incidents, list offline cameras, "
                    f"analyze loitering trends, or compile forensic incident reports."
                )
                suggested_actions = ["Summarize Latest Incidents", "Show Critical Alerts", "Check Camera Status"]
        else:
            suggested_actions = ["Review Incident Dossier", "Examine Video Evidence", "Acknowledge Alerts"]

        return {
            "response": gemini_text,
            "suggested_actions": suggested_actions,
            "context_data_used": {
                "total_cameras": total_cameras,
                "open_incidents_count": len(open_incidents),
                "recent_alerts_count": len(recent_alerts),
            },
            "model_used": model_used,
        }

    @classmethod
    def generate_incident_report_markdown(cls, db: Session, incident_id: int) -> Dict[str, Any]:
        """
        Generates a comprehensive, audit-ready Markdown incident report for export or printing.
        """
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        events = db.query(SecurityEvent).filter(SecurityEvent.incident_id == incident_id).all()
        alerts = db.query(Alert).filter(Alert.incident_id == incident_id).all()
        evidence_items = db.query(Evidence).filter(Evidence.incident_id == incident_id).all()

        report_md = f"""# SENTINEL-AI SURVEILLANCE INCIDENT DOSSIER
**CONFIDENTIAL // BORDER SECURITY COMMAND**

---

### Incident Header
- **Incident Number**: `{incident.incident_number}`
- **Classification**: **{incident.severity} PRIORITY**
- **Investigation Status**: `{incident.status}`
- **Date & Time of Breach**: `{incident.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}`
- **Generated On**: `{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`

---

### Executive Summary & Objective Description
{incident.description}

### AI Cognitive Threat Assessment (Google Gemini)
{incident.ai_summary or 'No AI summary generated yet. Click "Generate AI Summary" in dashboard.'}

---

### Recommended Containment Actions
"""
        for rec in (incident.ai_recommendations or []):
            report_md += f"- [ ] {rec}\n"

        report_md += f"""
---

### Chronological Security Events ({len(events)} recorded)
| Time (UTC) | Event Classification | Severity | Confidence | Description |
| :--- | :--- | :--- | :--- | :--- |
"""
        for ev in events:
            report_md += f"| {ev.timestamp.strftime('%H:%M:%S')} | `{ev.event_type}` | **{ev.severity}** | {int(ev.confidence*100)}% | {ev.description} |\n"

        report_md += f"""
---

### Forensic Evidence Register ({len(evidence_items)} items)
| Type | File Path | Checksum (SHA-256) | Timestamp |
| :--- | :--- | :--- | :--- |
"""
        for ev in evidence_items:
            checksum = ev.checksum_sha256[:16] + "..." if ev.checksum_sha256 else "N/A"
            report_md += f"| `{ev.evidence_type}` | `{ev.file_path}` | `{checksum}` | {ev.timestamp.strftime('%H:%M:%S')} |\n"

        report_md += f"""
---

### Analyst Notes & Resolution Ledger
**Assigned Analyst Notes**:
> {incident.analyst_notes or 'No analyst field notes attached yet.'}

**Signed By Command Officer**: _______________________________
"""

        return {
            "incident_number": incident.incident_number,
            "report_title": f"Surveillance Incident Report - {incident.incident_number}",
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "markdown_content": report_md,
            "pdf_download_url": f"/api/v1/ai/incidents/{incident.id}/report.pdf",
        }
