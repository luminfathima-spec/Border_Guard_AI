from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class AISummaryRequest(BaseModel):
    custom_instructions: Optional[str] = None

class AISummaryResponse(BaseModel):
    incident_id: int
    incident_number: str
    ai_summary: str
    ai_recommendations: List[str]
    model_used: str
    source_facts: Dict[str, Any]

class AIChatMessage(BaseModel):
    role: str # "user" | "assistant" | "system"
    content: str

class AIChatRequest(BaseModel):
    message: str
    conversation_history: List[AIChatMessage] = []
    camera_id: Optional[int] = None
    incident_id: Optional[int] = None

class AIChatResponse(BaseModel):
    response: str
    suggested_actions: List[str] = []
    context_data_used: Dict[str, Any] = {}
    model_used: str

class IncidentReportResponse(BaseModel):
    incident_number: str
    report_title: str
    generated_at: str
    markdown_content: str
    pdf_download_url: Optional[str] = None

# ==============================================================================
# Phase 5: Structured Gemini Reasoning Schemas
# ==============================================================================

class ObservedEventItem(BaseModel):
    """Structured representation of an individual verified or observed event."""
    event_id: Optional[int] = None
    event_type: str
    timestamp: str
    confidence: float = 1.0
    description: str

class IncidentAnalysisResponse(BaseModel):
    """
    Structured Pydantic schema enforced for Google Gemini response_schema.
    Mandatory schema compliance per Phase 5 specifications.
    """
    summary: str
    observed_events: List[ObservedEventItem] = []
    referenced_camera_ids: List[int] = []
    supporting_evidence_ids: List[int] = []
    timestamp_references: List[str] = []
    uncertainty_and_conflicts: List[str] = []
    suggested_human_actions: List[str] = []
    threat_level: str = "HIGH"
    insufficient_evidence: bool = False

class AnalyzeIncidentRequest(BaseModel):
    custom_instructions: Optional[str] = None
    force_mock: bool = False
    include_keyframes: bool = True

class GroundedCitationAudit(BaseModel):
    verified_cameras: List[int] = []
    verified_evidence: List[int] = []
    verified_events: List[int] = []
    ungrounded_cameras: List[int] = []
    ungrounded_evidence: List[int] = []
    ungrounded_events: List[int] = []
    hallucinations_detected: List[str] = []
    grounding_score: float = 1.0

class AIAnalysisDetailedResponse(BaseModel):
    id: int
    incident_id: Optional[int] = None
    model_name: str
    prompt_type: str
    prompt_version: str
    analysis_result: str
    structured_output: IncidentAnalysisResponse
    grounded_citations: Dict[str, Any]
    confidence_score: float
    token_count: int
    execution_time_ms: int
    status: str
    is_mock: bool
    created_at: Any

