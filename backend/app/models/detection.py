import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True, index=True)
    
    timestamp_offset = Column(Float, nullable=False) # Timestamp in seconds within video
    frame_number = Column(Integer, nullable=False, index=True)
    object_type = Column(String(50), nullable=False, index=True) # person, car, truck, animal, etc.
    confidence = Column(Float, nullable=False)
    
    # Normalized bounding box coordinates [0.0 - 1.0]
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    
    tracking_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    video = relationship("Video", back_populates="detections")

    __table_args__ = (
        Index("ix_detections_video_frame", "video_id", "frame_number"),
    )
