import re
import json
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.user import User, UserRole
from app.models.camera import Camera
from app.models.incident import Incident
from app.models.report import Report
from app.schemas.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotToolCall,
    CopilotPendingConfirmation,
)
from app.services.copilot.tools import CopilotTools

class SurveillanceCopilotService:
    """
    Orchestrates the Natural-Language Surveillance Copilot:
    - Enforces RBAC permissions per user.
    - Executes authorized tools for camera events, unresolved incidents, zone intervals,
      report evidence explanations, and observation graphs.
    - Requires operator confirmation for consequential actions.
    - Protects against arbitrary SQL or shell injection.
    """

    @classmethod
    def chat(
        cls,
        db: Session,
        user: User,
        req: CopilotChatRequest,
    ) -> CopilotChatResponse:
        tool_calls: List[CopilotToolCall] = []
        pending_confirmation: Optional[CopilotPendingConfirmation] = None
        message = req.message.strip()
        msg_lower = message.lower()

        # 1. Handle explicit confirmation of a prior consequential action
        if req.confirmed_action:
            action_payload = req.confirmed_action.get("payload", {})
            action_payload["confirmed"] = True
            tool_call = CopilotTools.escalate_incident(db, user, action_payload)
            tool_calls.append(tool_call)

            if tool_call.status == "SUCCESS":
                res_data = tool_call.result or {}
                return CopilotChatResponse(
                    response=(
                        f"**Action Confirmed & Executed**: Incident `{res_data.get('incident_number')}` "
                        f"has been escalated to **{res_data.get('escalation_tier')}**. "
                        f"A priority command alert has been dispatched to Quick Reaction Teams."
                    ),
                    tool_calls=tool_calls,
                    pending_confirmation=None,
                    suggested_queries=[
                        "Show active incidents",
                        "View alert register",
                        "Check adjacent camera feeds",
                    ],
                    model_used=settings.GEMINI_MODEL,
                )
            else:
                err_msg = (tool_call.result or {}).get("error", "Action failed")
                return CopilotChatResponse(
                    response=f"**Action Failed**: {err_msg}",
                    tool_calls=tool_calls,
                    pending_confirmation=None,
                    suggested_queries=["Check system status", "Retry escalation"],
                    model_used=settings.GEMINI_MODEL,
                )

        # 2. Natural Language Intent Parsing & Authorized Tool Dispatching
        # Intent A: Summarize recorded events from a selected camera
        # Matches: "summarize recorded events from camera 1", "camera 2 events", etc.
        cam_match = re.search(r"camera\s*#?(\d+)", msg_lower) or re.search(r"cam\s*#?(\d+)", msg_lower)
        if ("summarize" in msg_lower or "events" in msg_lower or "activity" in msg_lower) and (cam_match or req.camera_id):
            target_cam_id = int(cam_match.group(1)) if cam_match else (req.camera_id or 1)
            call = CopilotTools.summarize_camera_events(db, user, {"camera_id": target_cam_id, "time_window_hours": 24})
            tool_calls.append(call)

            res = call.result or {}
            if call.status == "SUCCESS":
                types_str = ", ".join([f"`{k}` ({v})" for k, v in res.get("type_breakdown", {}).items()]) or "None"
                recent_list = "\n".join([
                    f"- **{e['severity']}** [{e['event_type']}]: {e['description']} ({e['timestamp'][:16]})"
                    for e in res.get("recent_events", [])
                ]) or "- No anomalous breach events recorded in the last 24 hours."

                answer = (
                    f"### Camera Telemetry Summary: **{res.get('camera_name')}** (`{res.get('camera_identifier')}`)\n\n"
                    f"- **Operational Status**: `{res.get('status')}` in **{res.get('zone')}**\n"
                    f"- **Total Recorded Events (Last 24h)**: **{res.get('total_events')}**\n"
                    f"- **Event Classifications**: {types_str}\n\n"
                    f"#### Recent Event Log:\n{recent_list}"
                )
            else:
                answer = f"**Query Notice**: {res.get('error', 'Camera not found.')}"

            return CopilotChatResponse(
                response=answer,
                tool_calls=tool_calls,
                suggested_queries=[
                    f"Show incidents with unresolved evidence",
                    f"Find events in {res.get('zone', 'Sector 4')}",
                    "Explain which evidence supports Report #1",
                ],
                model_used=settings.GEMINI_MODEL,
            )

        # Intent B: Show incidents with unresolved evidence
        # Matches: "show incidents with unresolved evidence", "unresolved incidents", "evidence gaps"
        if "unresolved" in msg_lower or ("missing" in msg_lower and "evidence" in msg_lower) or "evidence gaps" in msg_lower:
            call = CopilotTools.get_incidents_with_unresolved_evidence(db, user, {"limit": 5})
            tool_calls.append(call)

            res = call.result or {}
            incidents = res.get("incidents", [])
            if incidents:
                inc_text = "\n\n".join([
                    f"**Incident `{i['incident_number']}`**: *{i['title']}* (Severity: **{i['severity']}**)\n"
                    f"- Status: `{i['status']}` | Conflicting Links: {i['conflicts_count']} | Missing Markers: {i['missing_evidence_count']}\n"
                    f"- Identified Gaps:\n" + "\n".join([f"  • {g}" for g in i['evidence_gaps']])
                    for i in incidents
                ])
                answer = (
                    f"### Open Incidents with Unresolved Evidence Gaps ({len(incidents)} found):\n\n"
                    f"{inc_text}\n\n"
                    f"> **Recommendation**: Use the Adaptive Verification Controller or resample CCTV keyframes to reconcile sensory conflicts."
                )
            else:
                answer = (
                    "### Incident Evidence Audit: Nominal\n\n"
                    "No open security incidents currently exhibit contradictory observations or missing evidence gaps in the Event Graph."
                )

            return CopilotChatResponse(
                response=answer,
                tool_calls=tool_calls,
                suggested_queries=[
                    "Summarize what happened across linked observations in Incident #1",
                    "Explain which evidence supports Report #1",
                    "Summarize recorded events from camera 1",
                ],
                model_used=settings.GEMINI_MODEL,
            )

        # Intent C: Find events associated with a specified zone and time range
        # Matches: "find events associated with sector 4", "zone sector 1", etc.
        zone_match = re.search(r"sector\s*#?(\d+)", msg_lower) or re.search(r"zone\s*([\w\-]+)", msg_lower)
        if "zone" in msg_lower or "sector" in msg_lower or zone_match:
            zone_target = zone_match.group(0).title() if zone_match else "Sector 4"
            call = CopilotTools.find_events_by_zone_and_time(
                db, user,
                {"zone_name": zone_target, "limit": 10}
            )
            tool_calls.append(call)

            res = call.result or {}
            events = res.get("events", [])
            cams = ", ".join(res.get("matched_cameras", [])) or "None"

            if events:
                ev_lines = "\n".join([
                    f"- **{e['timestamp'][:16]}** | `{e['event_type']}` (**{e['severity']}**) at {e['camera_name']}: {e['description']} ({int(e['confidence']*100)}% conf)"
                    for e in events[:6]
                ])
                answer = (
                    f"### Events Located in **{res.get('zone_name')}** ({res.get('events_count')} matches):\n\n"
                    f"- **Surveillance Sensors in Zone**: {cams}\n\n"
                    f"#### Chronological Detections:\n{ev_lines}"
                )
            else:
                answer = (
                    f"### Zone Search: **{res.get('zone_name')}**\n\n"
                    f"No recent security events found matching '{res.get('zone_name')}'. Active cameras in zone: {cams}."
                )

            return CopilotChatResponse(
                response=answer,
                tool_calls=tool_calls,
                suggested_queries=[
                    f"Summarize recorded events from camera 1",
                    "Show incidents with unresolved evidence",
                    "Explain which evidence supports Report #1",
                ],
                model_used=settings.GEMINI_MODEL,
            )

        # Intent D: Explain which evidence supports a stored report
        # Matches: "explain which evidence supports report 1", "report evidence", "evidence for report"
        rep_match = re.search(r"report\s*#?(\d+)", msg_lower)
        if ("report" in msg_lower and ("evidence" in msg_lower or "supports" in msg_lower or "explain" in msg_lower)) or rep_match:
            rep_id = int(rep_match.group(1)) if rep_match else 1
            call = CopilotTools.explain_report_evidence(db, user, {"report_id": rep_id})
            tool_calls.append(call)

            res = call.result or {}
            if call.status == "SUCCESS":
                stmts = res.get("statements_audit", [])
                stmt_text = "\n\n".join([
                    f"**Statement #{s['statement_id']}** [`{s['statement_type']}`] — *{s['citation_status']}*:\n"
                    f"> \"{s['text']}\"\n"
                    f"- Supporting Evidence Files: " + (
                        ", ".join([f"`{e['type']}` ({e['file_path']}, SHA: {e['sha256']})" for e in s['supporting_evidence']])
                        if s['supporting_evidence'] else "*Direct sensor telemetry; no detached files.*"
                    )
                    for s in stmts[:4]
                ])

                answer = (
                    f"### Evidentiary Foundation: Report **{res.get('report_number')}** (*{res.get('title')}*)\n\n"
                    f"- **Review Status**: `{res.get('review_status')}`\n"
                    f"- **Validated Citation Rate**: **{res.get('valid_citation_rate')}%**\n"
                    f"- **Total Evidence Attachments**: {res.get('total_evidence_files')} file(s)\n"
                    f"- **Cryptographic SHA-256**: `{res.get('sha256_digest')}`\n\n"
                    f"#### Factual Grounding Ledger:\n{stmt_text}"
                )
            else:
                answer = f"**Report Query Notice**: {res.get('error', 'Report not found.')}"

            return CopilotChatResponse(
                response=answer,
                tool_calls=tool_calls,
                suggested_queries=[
                    "Summarize what happened across linked observations in Incident #1",
                    "Show incidents with unresolved evidence",
                    "Summarize recorded events from camera 1",
                ],
                model_used=settings.GEMINI_MODEL,
            )

        # Intent E: Summarize what happened across linked observations
        # Matches: "summarize linked observations", "what happened across linked observations", "incident 1 observations"
        inc_match = re.search(r"incident\s*#?(\d+)", msg_lower)
        if ("linked observation" in msg_lower or "observations" in msg_lower) or (inc_match and "what happened" in msg_lower):
            inc_id = int(inc_match.group(1)) if inc_match else (req.incident_id or 1)
            call = CopilotTools.summarize_linked_observations(db, user, {"incident_id": inc_id})
            tool_calls.append(call)

            res = call.result or {}
            if call.status == "SUCCESS":
                rel_lines = "\n".join([
                    f"- `{r['source']}` **{r['relationship']}** `{r['target']}` ({int(r['confidence']*100)}% conf) — *{r['reason']}*"
                    for r in res.get("key_relationships", [])
                ]) or "- Direct camera detection pipeline."

                obs_lines = "\n".join([
                    f"- **[{o['type']}]**: {o['assertion']} (Verified in DB: `{o['is_verified']}`)"
                    for o in res.get("linked_observations", [])
                ]) or "- Initial automated tripwire crossings logged."

                answer = (
                    f"### Provenance Graph Synthesis: Incident **{res.get('incident_number')}** (*{res.get('title')}*)\n\n"
                    f"- **Total Provenance Edges**: {res.get('total_links')}\n"
                    f"- **Direct Physical Facts**: {res.get('direct_observations_count')} | **Inferred**: {res.get('inferred_associations_count')} | **Derived Syntheses**: {res.get('derived_syntheses_count')}\n\n"
                    f"#### Key Event Graph Relationships:\n{rel_lines}\n\n"
                    f"#### Field Observations Register:\n{obs_lines}"
                )
            else:
                answer = f"**Incident Query Notice**: {res.get('error', 'Incident not found.')}"

            return CopilotChatResponse(
                response=answer,
                tool_calls=tool_calls,
                suggested_queries=[
                    "Explain which evidence supports Report #1",
                    "Show incidents with unresolved evidence",
                    f"Escalate Incident {inc_id} to Tactical QRT",
                ],
                model_used=settings.GEMINI_MODEL,
            )

        # Intent F: Consequential Action (Escalate Incident)
        if "escalate" in msg_lower:
            inc_id = int(inc_match.group(1)) if inc_match else (req.incident_id or 1)
            call = CopilotTools.escalate_incident(
                db, user,
                {
                    "incident_id": inc_id,
                    "escalation_level": "TACTICAL_QRT",
                    "rationale": f"Operator requested escalation: {message}",
                    "confirmed": False,
                }
            )
            tool_calls.append(call)

            if call.status == "CONFIRMATION_REQUIRED":
                confirm_data = (call.result or {}).get("pending_confirmation", {})
                pending_confirmation = CopilotPendingConfirmation(**confirm_data)
                answer = (
                    f"⚠️ **Confirmation Required for Consequential Action**\n\n"
                    f"You have requested to escalate **Incident #{inc_id}** to **TACTICAL_QRT**.\n\n"
                    f"**Proposed Action Details**:\n"
                    f"- **Target**: Incident #{inc_id}\n"
                    f"- **Tier**: Tactical Quick Reaction Team (QRT)\n"
                    f"- **Effect**: Elevates severity to `CRITICAL`, updates status to `IN_PROGRESS`, dispatches immediate alerts.\n\n"
                    f"Please confirm to proceed."
                )
            else:
                answer = f"**Escalation Notice**: {(call.result or {}).get('error', 'Cannot escalate.')}"

            return CopilotChatResponse(
                response=answer,
                tool_calls=tool_calls,
                pending_confirmation=pending_confirmation,
                suggested_queries=[
                    "Show incidents with unresolved evidence",
                    "Summarize recorded events from camera 1",
                ],
                model_used=settings.GEMINI_MODEL,
            )

        # Default Helpful Copilot Response with live context
        total_cams = db.query(Camera).count()
        online_cams = db.query(Camera).filter(Camera.status == "ONLINE").count()
        open_incs = db.query(Incident).filter(Incident.status.in_(["OPEN", "IN_PROGRESS"])).count()

        answer = (
            f"**SentinelAI Surveillance Copilot Active**\n\n"
            f"Currently monitoring **{total_cams}** cameras ({online_cams} online) across border sectors with **{open_incs}** active incidents.\n\n"
            f"You can ask me to:\n"
            f"1. **Summarize recorded events from a selected camera** (e.g., *'Summarize recorded events from camera 1'*)\n"
            f"2. **Show incidents with unresolved evidence** (e.g., *'Show incidents with unresolved evidence'*)\n"
            f"3. **Find events associated with a specified zone and time range** (e.g., *'Find events in Sector 4'*)\n"
            f"4. **Explain which evidence supports a stored report** (e.g., *'Explain which evidence supports Report #1'*)\n"
            f"5. **Summarize what happened across linked observations** (e.g., *'Summarize what happened across linked observations in Incident #1'*)\n"
            f"6. **Escalate high-priority incidents** with two-step confirmation"
        )

        return CopilotChatResponse(
            response=answer,
            tool_calls=[],
            pending_confirmation=None,
            suggested_queries=[
                "Summarize recorded events from camera 1",
                "Show incidents with unresolved evidence",
                "Find events associated with Sector 4",
                "Explain which evidence supports Report #1",
                "Summarize what happened across linked observations in Incident #1",
            ],
            model_used=settings.GEMINI_MODEL,
        )
