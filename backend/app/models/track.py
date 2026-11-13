import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from app.db.database import Base

class ObjectTrack(Base):
    __tablename__ = "object_tracks"

    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(Integer, nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True, index=True)
    object_type = Column(String(50), nullable=False, index=True)  # person, car, truck, animal, etc.

    first_seen_frame = Column(Integer, nullable=False)
    last_seen_frame = Column(Integer, nullable=False)
    first_seen_timestamp = Column(Float, nullable=False)  # in seconds offset within video
    last_seen_timestamp = Column(Float, nullable=False)
    dwell_time_seconds = Column(Float, default=0.0, nullable=False)
    max_confidence = Column(Float, default=0.0, nullable=False)

    # Serialized list of historical centroids/bounding boxes [{"frame": int, "bbox": [x1, y1, x2, y2], "timestamp": float}]
    trajectory_json = Column(JSON, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    video = relationship("Video", back_populates="tracks")
    camera = relationship("Camera", back_populates="tracks")

    __table_args__ = (
        Index("ix_object_tracks_video_tracking", "video_id", "tracking_id"),
    )
