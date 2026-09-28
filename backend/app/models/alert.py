import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class AlertStatus(str, Enum):
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("security_events.id", ondelete="CASCADE"), nullable=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)

    severity = Column(String(20), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(String(512), nullable=False)
    status = Column(String(50), default=AlertStatus.NEW.value, nullable=False, index=True)

    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)

    event = relationship("SecurityEvent", back_populates="alerts")
    camera = relationship("Camera", back_populates="alerts")
    incident = relationship("Incident", back_populates="alerts")
