import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class VideoStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    path = Column(String(512), nullable=False)
    processed_path = Column(String(512), nullable=True)
    duration = Column(Float, nullable=True) # Duration in seconds
    resolution = Column(String(50), nullable=True) # e.g. "1920x1080"
    fps = Column(Float, nullable=True)
    total_frames = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    status = Column(String(50), default=VideoStatus.PENDING.value, nullable=False)
    error_message = Column(String(512), nullable=True)
    
    total_detections_count = Column(Integer, default=0)
    total_tracked_objects_count = Column(Integer, default=0)
    total_incidents_count = Column(Integer, default=0)
    
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)

    checksum_sha256 = Column(String(64), nullable=True) # Cryptographic hash for evidentiary chain of custody
    source_timestamp = Column(DateTime, nullable=True) # Recorded time from CCTV source metadata
    mime_type = Column(String(100), nullable=True)

    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    camera = relationship("Camera", back_populates="videos")
    detections = relationship("Detection", back_populates="video", cascade="all, delete-orphan")
    tracks = relationship("ObjectTrack", back_populates="video", cascade="all, delete-orphan")
    events = relationship("SecurityEvent", back_populates="video")
