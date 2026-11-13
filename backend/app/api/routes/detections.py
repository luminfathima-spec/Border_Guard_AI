from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.models.detection import Detection
from app.models.track import ObjectTrack
from app.schemas.detection import DetectionResponse, DetectionSummary
from app.schemas.track import ObjectTrackResponse
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


@router.get("/tracks", response_model=List[ObjectTrackResponse])
def list_tracks(
    video_id: Optional[int] = None,
    camera_id: Optional[int] = None,
    object_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(200, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Query tracked object trajectories across videos and camera feeds."""
    query = db.query(ObjectTrack)
    if video_id:
        query = query.filter(ObjectTrack.video_id == video_id)
    if camera_id:
        query = query.filter(ObjectTrack.camera_id == camera_id)
    if object_type:
        query = query.filter(ObjectTrack.object_type == object_type.lower())
    if is_active is not None:
        query = query.filter(ObjectTrack.is_active == is_active)

    return query.order_by(ObjectTrack.id.desc()).offset(offset).limit(limit).all()


@router.get("/summary", response_model=DetectionSummary)
def get_detection_summary(
    video_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Aggregate statistics on detections and tracking across videos."""
    det_query = db.query(Detection)
    track_query = db.query(ObjectTrack)
    if video_id:
        det_query = det_query.filter(Detection.video_id == video_id)
        track_query = track_query.filter(ObjectTrack.video_id == video_id)

    total_detections = det_query.count()
    unique_tracks = track_query.count()

    class_counts_query = (
        det_query.with_entities(Detection.object_type, func.count(Detection.id))
        .group_by(Detection.object_type)
        .all()
    )
    counts_by_class = {cls: count for cls, count in class_counts_query}

    max_offset = det_query.with_entities(func.max(Detection.timestamp_offset)).scalar() or 0.0

    return DetectionSummary(
        total_detections=total_detections,
        unique_tracks=unique_tracks,
        counts_by_class=counts_by_class,
        duration_seconds=float(max_offset),
    )
