from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class CopilotToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    status: str = "SUCCESS"  # SUCCESS, FAILED, CONFIRMATION_REQUIRED
    execution_time_ms: int = 0

class CopilotPendingConfirmation(BaseModel):
    action_id: str
    action_type: str  # e.g., ESCALATE_INCIDENT, PURGE_BUFFER
    incident_id: Optional[int] = None
    title: str
    description: str
    payload: Dict[str, Any]

class CopilotChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]] = []
    camera_id: Optional[int] = None
    incident_id: Optional[int] = None
    confirmed_action: Optional[Dict[str, Any]] = None

class CopilotChatResponse(BaseModel):
    response: str
    tool_calls: List[CopilotToolCall] = []
    pending_confirmation: Optional[CopilotPendingConfirmation] = None
    suggested_queries: List[str] = []
    model_used: str

class SummarizeCameraEventsArgs(BaseModel):
    camera_id: int = Field(..., description="Target camera database ID")
    time_window_hours: int = Field(24, ge=1, le=168, description="Time window in hours")

class GetUnresolvedIncidentsArgs(BaseModel):
    limit: int = Field(10, ge=1, le=50, description="Maximum incidents to return")

class FindEventsByZoneArgs(BaseModel):
    zone_name: str = Field(..., description="Border sector or restricted zone name")
    start_time: Optional[str] = Field(None, description="ISO timestamp for window start")
    end_time: Optional[str] = Field(None, description="ISO timestamp for window end")
    limit: int = Field(20, ge=1, le=100, description="Max events to return")

class ExplainReportEvidenceArgs(BaseModel):
    report_id: int = Field(..., description="Target investigation report ID")

class SummarizeLinkedObservationsArgs(BaseModel):
    incident_id: int = Field(..., description="Target incident ID")

class EscalateIncidentArgs(BaseModel):
    incident_id: int = Field(..., description="Incident ID to escalate")
    escalation_level: str = Field("TACTICAL_QRT", description="Escalation tier: TACTICAL_QRT or COMMAND_STAFF")
    rationale: str = Field(..., description="Operational justification for escalation")
    confirmed: bool = Field(False, description="Whether operator explicitly confirmed this consequential action")
