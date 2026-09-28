import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_number = Column(String(50), unique=True, index=True, nullable=False) # e.g. INC-2026-0001
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), default="HIGH", nullable=False, index=True)
    status = Column(String(50), default=IncidentStatus.OPEN.value, nullable=False, index=True)

    # Google Gemini AI generated intelligence
    ai_summary = Column(Text, nullable=True)
    ai_recommendations = Column(JSON, default=list, nullable=False)
    ai_last_generated_at = Column(DateTime, nullable=True)

    analyst_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    events = relationship("SecurityEvent", back_populates="incident")
    alerts = relationship("Alert", back_populates="incident")
    evidence_items = relationship("Evidence", back_populates="incident")
