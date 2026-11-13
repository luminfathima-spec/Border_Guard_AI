import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

class CameraStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    camera_identifier = Column(String(50), unique=True, index=True, nullable=False) # e.g. CAM-SECTOR-01
    location = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    stream_url = Column(String(512), nullable=True)
    status = Column(String(50), default=CameraStatus.ONLINE.value, nullable=False)
    zone = Column(String(100), nullable=True) # e.g. "Sector-4 North Perimeter"
    
    # Store polygonal restricted zones and virtual tripwire lines as JSON configurations
    restricted_zones = Column(JSON, default=list, nullable=False)
    virtual_lines = Column(JSON, default=list, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    videos = relationship("Video", back_populates="camera")
    tracks = relationship("ObjectTrack", back_populates="camera")
    events = relationship("SecurityEvent", back_populates="camera")
    alerts = relationship("Alert", back_populates="camera")
