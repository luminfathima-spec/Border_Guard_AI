import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

class AnalysisStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    FLAGGED = "FLAGGED"
    PENDING_NETWORK = "PENDING_NETWORK"
    UNAVAILABLE = "UNAVAILABLE"

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    event_id = Column(Integer, ForeignKey("security_events.id", ondelete="SET NULL"), nullable=True, index=True)

    model_name = Column(String(100), default="gemini-2.5-flash", nullable=False)
    prompt_type = Column(String(50), nullable=False, index=True)  # TACTICAL_SUMMARY, VERIFICATION, COPILOT_QA
    prompt_version = Column(String(50), default="2026.04.1", nullable=False)
    raw_prompt = Column(Text, nullable=False)
    analysis_result = Column(Text, nullable=False)
    structured_output = Column(JSON, default=dict, nullable=False)

    confidence_score = Column(Float, default=1.0, nullable=False)
    grounded_citations = Column(JSON, default=list, nullable=False)  # List of cited EventIDs / EvidenceIDs
    token_count = Column(Integer, default=0, nullable=False)
    execution_time_ms = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default=AnalysisStatus.SUCCESS.value, nullable=False, index=True)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)

    incident = relationship("Incident", back_populates="analyses")
    event = relationship("SecurityEvent", back_populates="analyses")
