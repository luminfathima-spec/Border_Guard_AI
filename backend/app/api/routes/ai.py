from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.ai import (
    AISummaryRequest,
    AISummaryResponse,
    AIChatRequest,
    AIChatResponse,
    IncidentReportResponse,
    AnalyzeIncidentRequest,
    AIAnalysisDetailedResponse,
)
from app.services.gemini_service import GeminiService
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.ai_analysis import AIAnalysis

router = APIRouter(prefix="/ai", tags=["Google Gemini AI Intelligence"])

@router.get("/gemini-status")
def get_gemini_status(
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns operational Google Gemini configuration and connectivity diagnostics.
    Never exposes API keys or sensitive credentials.
    """
    return GeminiService.verify_gemini_connection()

@router.post("/incidents/{incident_id}/analyze", response_model=AIAnalysisDetailedResponse)
def analyze_incident_structured(
    incident_id: int,
    req: AnalyzeIncidentRequest = AnalyzeIncidentRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Executes full Phase 5 multimodal Gemini reasoning:
    - Extracts event-triggered keyframes.
    - Prompts Gemini with versioned templates and JSON schema.
    - Validates citations via deterministic CrossExaminer.
    - Persists analysis record and links to Event Graph.
    """
    try:
        return GeminiService.analyze_incident(
            db=db,
            incident_id=incident_id,
            custom_instructions=req.custom_instructions,
            force_mock=req.force_mock,
            include_keyframes=req.include_keyframes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gemini analysis failure: {e}")

@router.get("/incidents/{incident_id}/analyses", response_model=List[AIAnalysisDetailedResponse])
def get_incident_analyses(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns historical audit log of all Gemini analyses run for this incident.
    """
    records = (
        db.query(AIAnalysis)
        .filter(AIAnalysis.incident_id == incident_id)
        .order_by(AIAnalysis.created_at.desc())
        .all()
    )
    result = []
    for r in records:
        result.append(
            {
                "id": r.id,
                "incident_id": r.incident_id,
                "model_name": r.model_name,
                "prompt_type": r.prompt_type,
                "prompt_version": r.prompt_version,
                "analysis_result": r.analysis_result,
                "structured_output": r.structured_output,
                "grounded_citations": r.grounded_citations,
                "confidence_score": r.confidence_score,
                "token_count": r.token_count,
                "execution_time_ms": r.execution_time_ms,
                "status": r.status,
                "is_mock": "mock" in r.model_name.lower(),
                "created_at": r.created_at,
            }
        )
    return result

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

from app.schemas.copilot import CopilotChatRequest, CopilotChatResponse
from app.services.copilot.service import SurveillanceCopilotService

@router.post("/copilot/chat", response_model=CopilotChatResponse)
def chat_with_surveillance_copilot(
    req: CopilotChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Phase 9 Surveillance Copilot with Function Calling:
    - Summarize camera events
    - Show incidents with unresolved evidence
    - Find events by zone and time range
    - Explain evidence supporting a stored report
    - Summarize linked observations
    - Two-step confirmation for consequential actions
    """
    try:
        return SurveillanceCopilotService.chat(
            db=db,
            user=current_user,
            req=req,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Copilot error: {e}")

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
