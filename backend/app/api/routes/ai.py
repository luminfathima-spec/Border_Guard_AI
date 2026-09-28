from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ai import (
    AISummaryRequest,
    AISummaryResponse,
    AIChatRequest,
    AIChatResponse,
    IncidentReportResponse,
)
from app.services.gemini_service import GeminiService
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["Google Gemini AI Intelligence"])

@router.post("/incidents/{incident_id}/summarize", response_model=AISummaryResponse)
def summarize_incident(
    incident_id: int,
    req: AISummaryRequest = AISummaryRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generates tactical threat summary and operational recommendations using Google Gemini based on structured telemetry.
    """
    try:
        return GeminiService.generate_incident_summary(
            db=db,
            incident_id=incident_id,
            custom_instructions=req.custom_instructions,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI reasoning failure: {e}")

@router.post("/assistant/chat", response_model=AIChatResponse)
def chat_with_copilot(
    req: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Interactive natural-language query assistant for security analysts backed by live surveillance telemetry.
    """
    try:
        history_dicts = [{"role": m.role, "content": m.content} for m in req.conversation_history]
        return GeminiService.chat_assistant(
            db=db,
            message=req.message,
            conversation_history=history_dicts,
            camera_id=req.camera_id,
            incident_id=req.incident_id,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Assistant error: {e}")

@router.post("/incidents/{incident_id}/report", response_model=IncidentReportResponse)
def generate_incident_report(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generates a formal, printable investigation report with event timelines, threat assessment, and evidence chain.
    """
    try:
        return GeminiService.generate_incident_report_markdown(db, incident_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Report error: {e}")
