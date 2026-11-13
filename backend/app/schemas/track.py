import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class TrajectoryPoint(BaseModel):
    frame: int
    timestamp: float
    bbox: List[float]
    centroid: List[float]


class ObjectTrackBase(BaseModel):
    tracking_id: int
    video_id: Optional[int] = None
    camera_id: Optional[int] = None
    object_type: str
    first_seen_frame: int
    last_seen_frame: int
    first_seen_timestamp: float
    last_seen_timestamp: float
    dwell_time_seconds: float
    max_confidence: float
    is_active: bool = True


class ObjectTrackResponse(ObjectTrackBase):
    id: int
    trajectory_json: List[Dict[str, Any]]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ObjectTrackSummary(BaseModel):
    total_tracks: int
    active_tracks: int
    breakdown_by_class: Dict[str, int]
    average_dwell_time: float
