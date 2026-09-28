from fastapi import APIRouter
from app.core.config import settings
import datetime

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def health_check():
    """
    Returns the operational status, timestamp, and environment metadata of SentinelAI backend.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "cv_engine": "YOLOv8 + OpenCV",
        "ai_engine": "Google Gemini" if settings.GEMINI_API_KEY else "Google Gemini (Key pending)",
    }
