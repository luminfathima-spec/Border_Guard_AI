import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.alert import AlertStatus

class AlertBase(BaseModel):
    event_id: Optional[int] = None
    camera_id: Optional[int] = None
    incident_id: Optional[int] = None
    severity: str
    title: str
    message: str
    status: AlertStatus = AlertStatus.NEW

class AlertUpdate(BaseModel):
    status: AlertStatus
    acknowledged_by: Optional[str] = None

class AlertResponse(AlertBase):
    id: int
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    camera_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
