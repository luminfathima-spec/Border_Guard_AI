from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.detection import Detection
from app.schemas.detection import DetectionResponse, DetectionSummary
from app.api.deps import get_current_active_user
from app.models.user import User
from app.ai.detection.yolo_detector import SURVEILLANCE_CLASSES

router = APIRouter(prefix="/detections", tags=["Detections"])

@router.get("/classes")
def list_detectable_classes():
    """List all AI-detectable surveillance object classes."""
    return {
        "classes": list(set(SURVEILLANCE_CLASSES.values())),
        "total_classes": len(set(SURVEILLANCE_CLASSES.values())),
    }

@router.get("", response_model=List[DetectionResponse])
def list_detections(
    video_id: Optional[int] = None,
    camera_id: Optional[int] = None,
    object_type: Optional[str] = None,
    frame_number: Optional[int] = None,
    limit: int = Query(200, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Query computer vision detections with filtering."""
    query = db.query(Detection)
    if video_id:
        query = query.filter(Detection.video_id == video_id)
    if camera_id:
        query = query.filter(Detection.camera_id == camera_id)
    if object_type:
        query = query.filter(Detection.object_type == object_type)
    if frame_number is not None:
        query = query.filter(Detection.frame_number == frame_number)

    return query.order_by(Detection.frame_number.asc()).offset(offset).limit(limit).all()
