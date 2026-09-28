import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
from app.models.incident import IncidentStatus

class IncidentBase(BaseModel):
    title: str
    description: str
    severity: str = "HIGH"
    status: IncidentStatus = IncidentStatus.OPEN
    analyst_notes: Optional[str] = None

class IncidentCreate(IncidentBase):
    pass

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[IncidentStatus] = None
    analyst_notes: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_recommendations: Optional[List[str]] = None

class IncidentResponse(IncidentBase):
    id: int
    incident_number: str
    ai_summary: Optional[str] = None
    ai_recommendations: List[Any] = []
    ai_last_generated_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    events_count: Optional[int] = 0
    alerts_count: Optional[int] = 0
    evidence_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
