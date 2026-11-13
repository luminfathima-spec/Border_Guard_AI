import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

class ReportType(str, Enum):
    INCIDENT_DOSSIER = "INCIDENT_DOSSIER"
    DAILY_SITREP = "DAILY_SITREP"
    FORENSIC_SUMMARY = "FORENSIC_SUMMARY"

class ReportStatus(str, Enum):
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ReviewStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    report_number = Column(String(50), unique=True, index=True, nullable=False)  # e.g. REP-2026-0001
    title = Column(String(200), nullable=False)
    report_type = Column(String(50), default=ReportType.INCIDENT_DOSSIER.value, nullable=False, index=True)
    status = Column(String(50), default=ReportStatus.COMPLETED.value, nullable=False, index=True)

    # Phase 7: Review & Approval Workflow
    review_status = Column(String(50), default=ReviewStatus.DRAFT.value, nullable=False, index=True)
    generated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    approved_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    approved_at = Column(DateTime, nullable=True)

    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)

    file_path = Column(String(512), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)

    # Phase 7: Model & Prompt Provenance
    model_name = Column(String(100), default="gemini-2.5-flash", nullable=False)
    prompt_version = Column(String(50), default="2026.04.1", nullable=False)

    parameters_json = Column(JSON, default=dict, nullable=False)
    sections_json = Column(JSON, default=dict, nullable=False)
    human_corrections = Column(JSON, default=list, nullable=False)
    audit_history = Column(JSON, default=list, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    generated_by = relationship("User", foreign_keys=[generated_by_user_id], back_populates="reports")
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    incident = relationship("Incident", back_populates="reports")

