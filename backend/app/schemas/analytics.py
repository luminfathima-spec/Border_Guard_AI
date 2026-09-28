from typing import Dict, List, Any
from pydantic import BaseModel

class TimelineItem(BaseModel):
    timestamp: str
    count: int
    severity: str

class AnalyticsOverview(BaseModel):
    total_cameras: int
    active_cameras: int
    total_events_today: int
    active_alerts: int
    critical_incidents: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    camera_health_summary: Dict[str, int]
    recent_activity_timeline: List[TimelineItem]
