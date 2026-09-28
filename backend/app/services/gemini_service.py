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

class GeminiService:
    @staticmethod
    def is_configured() -> bool:
        return bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5)

    @classmethod
    def _call_gemini_api(cls, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        """
        Executes generation using the official Google GenAI Python SDK.
        """
        if not cls.is_configured():
            return None

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
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
            logger.error(f"Google Gemini API error: {e}", exc_info=True)
            return None

    @classmethod
    def generate_incident_summary(
        cls,
        db: Session,
        incident_id: int,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates tactical incident assessment and investigation recommendations using structured event telemetry.
        """
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        events = db.query(SecurityEvent).filter(SecurityEvent.incident_id == incident_id).all()
        alerts = db.query(Alert).filter(Alert.incident_id == incident_id).all()
        evidence_items = db.query(Evidence).filter(Evidence.incident_id == incident_id).all()

        # Build structured fact payload
        facts = {
            "incident_number": incident.incident_number,
            "title": incident.title,
            "severity": incident.severity,
            "created_at": incident.created_at.isoformat(),
            "events_count": len(events),
            "events": [
                {
                    "type": ev.event_type,
                    "severity": ev.severity,
                    "timestamp": ev.timestamp.isoformat(),
                    "description": ev.description,
                    "confidence": ev.confidence,
                    "metadata": ev.metadata_json,
                }
                for ev in events
            ],
            "alerts": [
                {"title": a.title, "severity": a.severity, "status": a.status}
                for a in alerts
            ],
            "evidence_items_count": len(evidence_items),
        }

        system_instruction = (
            "You are SentinelAI Cognitive Reasoning Officer, an elite military and border surveillance "
            "intelligence analysis system. Your role is to analyze deterministic computer-vision facts "
            "(zone intrusions, line crossing tripwires, loitering times) and generate a concise tactical "
            "executive summary, threat level evaluation, and 3-4 numbered operational recommendations. "
            "Never invent facts not present in telemetry. Format output clearly in Markdown."
        )

        prompt = f"""
Analyze the following structured border surveillance telemetry data:
```json
{json.dumps(facts, indent=2)}
```

Additional Operator Instructions: {custom_instructions or 'Provide rapid tactical analysis.'}

Please output your response in valid JSON with exactly two fields:
1. "summary": A concise, military/security-grade Markdown summary of the incident.
2. "recommendations": A list of 3-4 actionable operational steps for field security teams.
"""

        gemini_response_text = cls._call_gemini_api(prompt, system_instruction)
        model_used = settings.GEMINI_MODEL if gemini_response_text else "Heuristic Rule-Based Fallback"

        if gemini_response_text:
            try:
                # Clean potential markdown JSON formatting
                cleaned_text = gemini_response_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.startswith("```"):
                    cleaned_text = cleaned_text[3:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]

                parsed = json.loads(cleaned_text.strip())
                summary = parsed.get("summary", gemini_response_text)
                recommendations = parsed.get("recommendations", [])
            except Exception:
                summary = gemini_response_text
                recommendations = [
                    "Dispatch Quick Reaction Team (QRT) to verify sector integrity.",
                    "Review secondary surveillance feeds and thermal cameras.",
                    "Log suspect trajectory in national border surveillance ledger."
                ]
        else:
            # High quality deterministic heuristic fallback
            summary = (
                f"**[Automated Intelligence Assessment]** Incident `{incident.incident_number}` represents a "
                f"**{incident.severity}** severity security event. Computer vision detected {len(events)} correlated breach "
                f"event(s). Breaches include: {', '.join(set(e.event_type for e in events))}. Immediate perimeter cordon "
                f"and active verification is advised."
            )
            recommendations = [
                "Deploy Quick Reaction Team (QRT) to intercept intrusion coordinates.",
                "Review recorded high-resolution evidence clips and snapshot forensic metadata.",
                "Inspect adjacent sector tripwires for coordinated secondary breach attempts.",
                "Escalate incident severity in SOC if target identity remains unconfirmed."
            ]

        # Update Incident in Database
        incident.ai_summary = summary
        incident.ai_recommendations = recommendations
        incident.ai_last_generated_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        db.refresh(incident)

        return {
            "incident_id": incident.id,
            "incident_number": incident.incident_number,
            "ai_summary": summary,
            "ai_recommendations": recommendations,
            "model_used": model_used,
            "source_facts": facts,
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
