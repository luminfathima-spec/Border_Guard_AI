import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

class EvidenceType(str, Enum):
    SNAPSHOT = "SNAPSHOT"
    VIDEO_CLIP = "VIDEO_CLIP"
    REPORT = "REPORT"
    METADATA = "METADATA"

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    event_id = Column(Integer, ForeignKey("security_events.id", ondelete="SET NULL"), nullable=True, index=True)

    evidence_type = Column(String(50), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    checksum_sha256 = Column(String(64), nullable=True) # Integrity preservation for legal custody
    
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    
    # Edge Store-and-Forward / Synchronization Fields
    client_evidence_id = Column(String(100), unique=True, nullable=True, index=True)
    sync_status = Column(String(50), default="SYNCED", nullable=False, index=True)
    synced_at = Column(DateTime, nullable=True)

    incident = relationship("Incident", back_populates="evidence_items")
    event = relationship("SecurityEvent", back_populates="evidence_items")
