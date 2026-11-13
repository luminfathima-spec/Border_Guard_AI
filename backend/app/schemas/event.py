import datetime
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, ConfigDict
from app.models.event import EventType, SeverityLevel

class SecurityEventBase(BaseModel):
    event_type: Union[EventType, str]
    severity: Union[SeverityLevel, str]
    camera_id: Optional[int] = None
    video_id: Optional[int] = None
    incident_id: Optional[int] = None
    description: str
    confidence: float = 1.0
    status: str = "ACTIVE"
    metadata_json: Dict[str, Any] = {}

class SecurityEventCreate(SecurityEventBase):
    pass

class SecurityEventResponse(SecurityEventBase):
    id: int
    timestamp: datetime.datetime
    snapshot_path: Optional[str] = None
    clip_path: Optional[str] = None
    created_at: datetime.datetime
    camera_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
