import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

class EventType(str, Enum):
    PERSON_DETECTED = "PERSON_DETECTED"
    VEHICLE_DETECTED = "VEHICLE_DETECTED"
    MULTIPLE_PERSONS = "MULTIPLE_PERSONS"
    LINE_CROSSING = "LINE_CROSSING"
    RESTRICTED_ZONE_ENTRY = "RESTRICTED_ZONE_ENTRY"
    LOITERING = "LOITERING"
    UNUSUAL_ACTIVITY = "UNUSUAL_ACTIVITY"
    OBJECT_LEFT_BEHIND = "OBJECT_LEFT_BEHIND"
    CAMERA_TAMPERING = "CAMERA_TAMPERING"
    CAMERA_OFFLINE = "CAMERA_OFFLINE"
    VIRTUAL_FENCE_BREACH = "VIRTUAL_FENCE_BREACH"
    LOITERING_DETECTED = "LOITERING_DETECTED"
    PERIMETER_PROXIMITY = "PERIMETER_PROXIMITY"
    UNAUTHORIZED_CROSSING = "UNAUTHORIZED_CROSSING"
    BREACH = "BREACH"

class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default=SeverityLevel.MEDIUM.value, nullable=False, index=True)
    
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)

    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)
    description = Column(String(512), nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False)
    
    metadata_json = Column(JSON, default=dict, nullable=False) # tracking id, breach coordinates, dwell time
    snapshot_path = Column(String(512), nullable=True)
    clip_path = Column(String(512), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    # Edge Store-and-Forward / Synchronization Fields
    client_event_id = Column(String(100), unique=True, nullable=True, index=True)
    sync_status = Column(String(50), default="SYNCED", nullable=False, index=True)  # SYNCED, BUFFERED_EDGE, SYNC_PENDING, SYNC_FAILED
    synced_at = Column(DateTime, nullable=True)
    edge_node_id = Column(String(100), nullable=True, index=True)

    camera = relationship("Camera", back_populates="events")
    video = relationship("Video", back_populates="events")
    incident = relationship("Incident", back_populates="events")
    alerts = relationship("Alert", back_populates="event", cascade="all, delete-orphan")
    evidence_items = relationship("Evidence", back_populates="event")
    analyses = relationship("AIAnalysis", back_populates="event")
