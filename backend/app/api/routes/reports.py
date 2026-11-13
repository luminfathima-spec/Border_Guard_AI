import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.report import (
    ReportGenerateRequest,
    ReportResponse,
    ReportCorrectionRequest,
    ReportReviewRequest,
)
from app.services.report_service import ReportGenerationService

router = APIRouter(prefix="/reports", tags=["Evidence-Grounded Incident Reports"])


@router.post("/incidents/{incident_id}/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_incident_report(
    incident_id: int,
    req: ReportGenerateRequest = ReportGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generates an evidence-grounded incident investigation dossier:
    - Extracts chronological events and graph links.
    - Sanitizes untrusted metadata (indirect prompt injection defense).
    - Runs programmatic Citation Cross-Examiner against database records.
    - Flags unsupported claims or timestamp discrepancies.
    - Returns insufficient_evidence when appropriate.
    - Persists report record, registers in Event Graph, and renders PDF.
    """
    return ReportGenerationService.generate_report(
        db=db,
        incident_id=incident_id,
        user_id=current_user.id,
        custom_instructions=req.custom_instructions,
        force_mock=req.force_mock,
        model_name=req.model_name,
    )


@router.get("/{report_id}", response_model=ReportResponse)
def get_report_details(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieves full report details and verified factual statement sections."""
    return ReportGenerationService.get_report(db, report_id)


@router.get("/incidents/{incident_id}", response_model=List[ReportResponse])
def list_incident_reports(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lists all generated report dossiers for an incident."""
    return ReportGenerationService.list_incident_reports(db, incident_id)


@router.patch("/{report_id}/statements/{statement_id}", response_model=ReportResponse)
def add_human_correction(
    report_id: int,
    statement_id: int,
    req: ReportCorrectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Allows an operator or analyst to correct a claim, annotate notes, and record in audit history."""
    return ReportGenerationService.add_statement_correction(
        db=db,
        report_id=report_id,
        statement_id=statement_id,
        corrected_text=req.corrected_text,
        analyst_comment=req.analyst_comment,
        user_id=current_user.id,
    )


@router.post("/{report_id}/review", response_model=ReportResponse)
def review_report(
    report_id: int,
    req: ReportReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Transitions report review status ('APPROVE', 'REQUEST_REVISIONS', 'REJECT') and updates signature."""
    return ReportGenerationService.review_report(
        db=db,
        report_id=report_id,
        action=req.action,
        reviewer_comments=req.reviewer_comments,
        user_id=current_user.id,
    )


@router.get("/{report_id}/export-pdf")
def export_report_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Downloads the official PDF dossier generated with ReportLab with cryptographic SHA-256 header."""
    report = ReportGenerationService.get_report(db, report_id)
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF dossier file not found on disk. Please re-generate the report.",
        )
    return FileResponse(
        path=report.file_path,
        media_type="application/pdf",
        filename=f"{report.report_number}.pdf",
    )


@router.get("/{report_id}/audit-history", response_model=List[Dict[str, Any]])
def get_report_audit_history(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns chronological audit ledger of all modifications, human annotations, and approvals."""
    report = ReportGenerationService.get_report(db, report_id)
    return report.audit_history
