import os
import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.db.database import get_db

router = APIRouter(prefix="/health", tags=["Health & Readiness"])


@router.get("", summary="Liveness probe")
async def health_check():
    """
    Lightweight liveness probe confirming that the FastAPI application process is alive.
    Returns HTTP 200 with service metadata.
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


@router.get("/ready", summary="Readiness probe")
def readiness_check(response: Response, db: Session = Depends(get_db)):
    """
    Comprehensive readiness probe verifying all critical subsystems:
    1. Database connectivity and query execution.
    2. Storage directory accessibility and write permissions.
    3. Computer vision model weights availability.
    4. Google Gemini API configuration.

    Returns HTTP 200 when ready to receive traffic, or HTTP 503 if any critical component is failing.
    """
    checks: Dict[str, Any] = {}
    is_ready = True

    # 1. Database Connectivity Check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {
            "status": "connected",
            "type": "sqlite" if "sqlite" in str(db.bind.url) else "postgresql",
        }
    except Exception as e:
        is_ready = False
        checks["database"] = {
            "status": "error",
            "detail": str(e),
        }

    # 2. Storage Directory Check
    storage_checks = {}
    for dir_name, dir_rel in [
        ("uploads", settings.UPLOAD_DIR),
        ("evidence", settings.EVIDENCE_DIR),
        ("snapshots", settings.SNAPSHOTS_DIR),
        ("processed", settings.PROCESSED_DIR),
    ]:
        p = settings.get_absolute_path(dir_rel)
        try:
            os.makedirs(p, exist_ok=True)
            # Test write access with a dummy probe file
            test_file = p / ".probe_test"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink(missing_ok=True)
            storage_checks[dir_name] = "writable"
        except Exception as st_err:
            is_ready = False
            storage_checks[dir_name] = f"error: {st_err}"

    checks["storage"] = storage_checks

    # 3. Model Weights Check
    model_path = settings.get_absolute_path(settings.YOLO_MODEL_PATH)
    checks["cv_model"] = {
        "path": str(model_path),
        "available": model_path.exists() and model_path.is_file(),
    }

    # 4. Gemini AI Engine Configuration Check
    checks["ai_engine"] = {
        "provider": "Google Gemini",
        "model": settings.GEMINI_MODEL,
        "configured": bool(settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else False),
    }

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "unready",
        "service": settings.APP_NAME,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "checks": checks,
    }
