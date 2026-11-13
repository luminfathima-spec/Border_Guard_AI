import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class StatementType(str, Enum):
    OBSERVATION = "OBSERVATION"
    CV_DETECTION = "CV_DETECTION"
    MODEL_INTERPRETATION = "MODEL_INTERPRETATION"
    HUMAN_ANNOTATION = "HUMAN_ANNOTATION"

class CitationValidationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FLAGGED_UNSUPPORTED = "FLAGGED_UNSUPPORTED"
    FLAGGED_TIMESTAMP_MISMATCH = "FLAGGED_TIMESTAMP_MISMATCH"
    FLAGGED_NONEXISTENT = "FLAGGED_NONEXISTENT"

class FactualStatementItem(BaseModel):
    statement_id: int
    text: str
    statement_type: StatementType = StatementType.CV_DETECTION
    referenced_entity_type: str = "EVENT"  # CAMERA, EVENT, DETECTION, OBJECT_TRACK, EVIDENCE, OBSERVATION
    referenced_entity_id: int
    timestamp: Optional[str] = None
    supporting_evidence_ids: List[int] = Field(default_factory=list)
    citation_status: CitationValidationStatus = CitationValidationStatus.VERIFIED
    validation_notes: Optional[str] = None
    human_correction: Optional[str] = None

class ConflictingEvidenceItem(BaseModel):
    description: str
    conflicting_nodes: List[str] = Field(default_factory=list)
    severity: str = "MEDIUM"

class MissingEvidenceItem(BaseModel):
    description: str
    interval: Optional[str] = None
    impact: str = "UNCERTAIN_INTERVAL"

class EvidenceUsedItem(BaseModel):
    evidence_id: int
    evidence_type: str
    file_path: str
    checksum_sha256: Optional[str] = None
    timestamp: Optional[str] = None

class IncidentReportSections(BaseModel):
    executive_summary: str
    factual_statements: List[FactualStatementItem] = Field(default_factory=list)
    conflicting_evidence: List[ConflictingEvidenceItem] = Field(default_factory=list)
    missing_evidence_gaps: List[MissingEvidenceItem] = Field(default_factory=list)
    containment_recommendations: List[str] = Field(default_factory=list)
    insufficient_evidence: bool = False
    insufficient_evidence_reason: Optional[str] = None
    evidence_used: List[EvidenceUsedItem] = Field(default_factory=list)

class ReportGenerateRequest(BaseModel):
    custom_instructions: Optional[str] = None
    force_mock: bool = False
    model_name: Optional[str] = None

class ReportResponse(BaseModel):
    id: int
    report_number: str
    incident_id: Optional[int]
    title: str
    status: str
    review_status: str
    model_name: str
    prompt_version: str
    sections: IncidentReportSections
    unsupported_claim_count: int = 0
    valid_citation_rate: float = 1.0
    generated_by_user_id: Optional[int] = None
    approved_by_user_id: Optional[int] = None
    approved_at: Optional[datetime.datetime] = None
    file_path: Optional[str] = None
    pdf_download_url: Optional[str] = None
    checksum_sha256: Optional[str] = None
    created_at: datetime.datetime
    audit_history: List[Dict[str, Any]] = Field(default_factory=list)

class ReportCorrectionRequest(BaseModel):
    statement_id: int
    corrected_text: Optional[str] = None
    analyst_comment: str

class ReportReviewRequest(BaseModel):
    action: str = Field(..., description="'APPROVE', 'REQUEST_REVISIONS', or 'REJECT'")
    reviewer_comments: Optional[str] = None

class ReportAuditEntry(BaseModel):
    timestamp: str
    user_id: Optional[int] = None
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)
