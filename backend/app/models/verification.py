import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.db.database import Base

class VerificationLedgerRecord(Base):
    """
    Immutable audit record documenting every input, state transition,
    action, resource expenditure, and outcome executed by the Adaptive
    Evidence Verification Controller.
    """
    __tablename__ = "verification_ledgers"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("security_events.id", ondelete="CASCADE"), nullable=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)

    verdict = Column(String(50), nullable=False, index=True)  # CONFIRMED, REJECTED_NOISE, UNRESOLVED, FLAGGED_CONFLICT
    confidence = Column(Float, default=1.0, nullable=False)
    is_unresolved = Column(Boolean, default=False, nullable=False, index=True)
    is_conflict = Column(Boolean, default=False, nullable=False, index=True)

    frames_examined = Column(Integer, default=0, nullable=False)
    gemini_calls_made = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)
    execution_time_ms = Column(Integer, default=0, nullable=False)

    summary_explanation = Column(Text, nullable=False)
    ledger_json = Column(JSON, default=list, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)

    event = relationship("SecurityEvent")
    incident = relationship("Incident")
