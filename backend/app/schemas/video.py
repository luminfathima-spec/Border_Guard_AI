import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.video import VideoStatus

class VideoBase(BaseModel):
    filename: str
    original_filename: str
    camera_id: Optional[int] = None

class VideoResponse(VideoBase):
    id: int
    path: str
    processed_path: Optional[str] = None
    processed_url: Optional[str] = None
    duration: Optional[float] = None
    resolution: Optional[str] = None
    fps: Optional[float] = None
    total_frames: Optional[int] = None
    file_size_bytes: Optional[int] = None
    status: VideoStatus
    error_message: Optional[str] = None
    total_detections_count: Optional[int] = 0
    total_tracked_objects_count: Optional[int] = 0
    total_incidents_count: Optional[int] = 0
    processing_started_at: Optional[datetime.datetime] = None
    processing_completed_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class VideoUploadResponse(BaseModel):
    message: str
    video: VideoResponse

class VideoProcessRequest(BaseModel):
    confidence_threshold: Optional[float] = None
    process_every_n_frames: Optional[int] = None
    enable_tracking: bool = True

class DemoVideoInfo(BaseModel):
    id: str
    title: str
    filename: str
    scenario: str
    duration_seconds: float
    resolution: str
    description: str
    target_camera: str
