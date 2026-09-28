import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class DetectionBase(BaseModel):
    video_id: int
    camera_id: Optional[int] = None
    timestamp_offset: float
    frame_number: int
    object_type: str
    confidence: float
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float
    tracking_id: Optional[int] = None

class DetectionResponse(DetectionBase):
    id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class DetectionSummary(BaseModel):
    total_detections: int
    unique_tracks: int
    counts_by_class: dict
    duration_seconds: float
