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
