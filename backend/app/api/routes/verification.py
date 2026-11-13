from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.verification import VerificationLedgerRecord
from app.schemas.verification import (
    EvaluateEventRequest,
    VerificationEvaluationResult,
    BenchmarkRunRequest,
)
from app.ai.verification.controller import AdaptiveVerificationController
from app.ai.verification.experiment import VerificationComparisonHarness

router = APIRouter(prefix="/verification", tags=["Adaptive Evidence Verification Controller"])

@router.post("/evaluate-event", response_model=VerificationEvaluationResult)
def evaluate_security_event(
    req: EvaluateEventRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Executes the Adaptive Evidence Verification Controller loop on an individual security event:
    - Evaluates detection confidence, track continuity, and sensor conflicts.
    - Adaptively triggers local frame burst resampling if marginal.
    - Selectively requests Gemini multimodal reasoning if ambiguous or conflicting.
    - Enforces verification budgets and marks unresolved if inconclusive.
    - Records and persists step-by-step decision audit ledger.
    """
    try:
        return AdaptiveVerificationController.evaluate_event(
            db=db,
            event_id=req.event_id,
            config=req.config,
            force_mock_gemini=req.force_mock_gemini,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Verification controller error: {e}")

@router.get("/ledgers/{event_id}")
def get_event_decision_ledgers(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves the complete, immutable decision audit ledger for an evaluated security event.
    """
    records = (
        db.query(VerificationLedgerRecord)
        .filter(VerificationLedgerRecord.event_id == event_id)
        .order_by(VerificationLedgerRecord.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "event_id": r.event_id,
            "incident_id": r.incident_id,
            "verdict": r.verdict,
            "confidence": r.confidence,
            "is_unresolved": r.is_unresolved,
            "is_conflict": r.is_conflict,
            "frames_examined": r.frames_examined,
            "gemini_calls_made": r.gemini_calls_made,
            "estimated_cost_usd": r.estimated_cost_usd,
            "execution_time_ms": r.execution_time_ms,
            "summary_explanation": r.summary_explanation,
            "ledger": r.ledger_json,
            "created_at": r.created_at,
        }
        for r in records
    ]

@router.post("/benchmark")
def run_comparative_benchmark(
    req: BenchmarkRunRequest = BenchmarkRunRequest(),
    current_user: User = Depends(get_current_active_user),
):
    """
    Executes the experimental comparison benchmark:
    - Evaluates Mode A (Baseline Fixed Frame Sampling).
    - Evaluates Mode B (Proposed Adaptive Verification Controller).
    - Evaluates 3 Component Ablations (No Local Resample, No Gemini, No Track Continuity).
    - Reports precision, recall, FPR, latency, frame counts, API cost, and unresolved rates.
    """
    try:
        return VerificationComparisonHarness.run_full_comparative_benchmark()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Benchmark error: {e}")
