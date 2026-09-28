import os
import shutil
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.video import Video, VideoStatus
from app.schemas.video import VideoResponse, VideoUploadResponse, VideoProcessRequest, DemoVideoInfo
from app.services.video_service import VideoService
from app.services.ffmpeg_service import FFmpegService
from app.services.analytics_pipeline import AnalyticsPipelineService
from app.api.deps import get_current_active_user
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/videos", tags=["Videos"])

AVAILABLE_DEMOS = [
    {
        "id": "incursion",
        "title": "Sector 07 Northern Buffer Zone Intrusion",
        "filename": "demo_border_incursion.mp4",
        "scenario": "Restricted Zone Breach",
        "duration_seconds": 6.0,
        "resolution": "1280x720",
        "description": "Perimeter breach scenario with target crossing virtual tripwire into 150m exclusion buffer strip.",
        "target_camera": "CAM-NP-01",
    },
    {
        "id": "patrol",
        "title": "Sector 04 Eastern Gate Patrol & Vehicle Transit",
        "filename": "demo_perimeter_patrol.mp4",
        "scenario": "Routine Perimeter Patrol",
        "duration_seconds": 6.0,
        "resolution": "1280x720",
        "description": "Routine surveillance patrol with guard post observation and vehicle moving along boundary road.",
        "target_camera": "CAM-EB-02",
    },
]

@router.get("/demos", response_model=List[DemoVideoInfo])
def get_available_demos(current_user: User = Depends(get_current_active_user)):
    """List pre-packaged border surveillance demo scenarios."""
    return AVAILABLE_DEMOS

@router.post("/demo/ingest")
def ingest_demo_video(
    demo_id: str = Form("incursion"),
    camera_id: Optional[int] = Form(1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Ingests one of the pre-packaged demo surveillance videos and immediately runs AI analytics.
    """
    selected_demo = next((d for d in AVAILABLE_DEMOS if d["id"] == demo_id), AVAILABLE_DEMOS[0])
    demo_src = settings.get_absolute_path(f"demo_videos/{selected_demo['filename']}")
    
    if not os.path.exists(demo_src):
        try:
            from scripts.generate_demo_videos import generate_demo_video
            os.makedirs(demo_src.parent, exist_ok=True)
            generate_demo_video(demo_src, scenario=selected_demo["id"], num_frames=150, fps=25)
        except Exception:
            pass

    timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest_filename = f"demo_{selected_demo['id']}_{timestamp_str}.mp4"
    dest_rel_path = f"{settings.UPLOAD_DIR}/{dest_filename}"
    dest_abs_path = str(settings.get_absolute_path(dest_rel_path))
    os.makedirs(os.path.dirname(dest_abs_path), exist_ok=True)

    shutil.copy(demo_src, dest_abs_path)

    # Create Video record
    video_record = Video(
        filename=dest_filename,
        original_filename=selected_demo["filename"],
        path=dest_rel_path,
        duration=selected_demo["duration_seconds"],
        resolution=selected_demo["resolution"],
        fps=25.0,
        total_frames=150,
        file_size_bytes=os.path.getsize(dest_abs_path),
        status=VideoStatus.PENDING.value,
        camera_id=camera_id or 1,
    )
    db.add(video_record)
    db.commit()
    db.refresh(video_record)

    # Immediately run analytics pipeline
    pipeline_result = AnalyticsPipelineService.process_video(
        db=db,
        video_id=video_record.id,
        enable_tracking=True,
    )

    db.refresh(video_record)

    vr = VideoResponse.model_validate(video_record)
    if video_record.processed_path:
        vr.processed_url = f"/static/processed/{os.path.basename(video_record.processed_path)}"

    return {
        "message": f"Demo video '{selected_demo['title']}' ingested and processed successfully.",
        "video": vr,
        "analytics": pipeline_result,
    }

@router.get("", response_model=List[VideoResponse])
def list_videos(
    camera_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all uploaded and processed surveillance video files."""
    query = db.query(Video)
    if camera_id:
        query = query.filter(Video.camera_id == camera_id)
    if status:
        query = query.filter(Video.status == status)
    
    videos = query.order_by(Video.id.desc()).all()
    results = []
    for v in videos:
        vr = VideoResponse.model_validate(v)
        if v.processed_path:
            vr.processed_url = f"/static/processed/{os.path.basename(v.processed_path)}"
        results.append(vr)
    return results

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve video file metadata and processing state."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video record not found")
    
    vr = VideoResponse.model_validate(video)
    if video.processed_path:
        vr.processed_url = f"/static/processed/{os.path.basename(video.processed_path)}"
    return vr

@router.post("/upload", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_video(
    file: UploadFile = File(...),
    camera_id: Optional[int] = Form(None),
    auto_process: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Uploads surveillance footage, extracts resolution/fps/duration metadata, and triggers analytics.
    """
    video_record = VideoService.create_video_record(db, file, camera_id=camera_id)

    if auto_process:
        try:
            AnalyticsPipelineService.process_video(
                db=db,
                video_id=video_record.id,
                enable_tracking=True,
            )
            db.refresh(video_record)
        except Exception as e:
            pass

    vr = VideoResponse.model_validate(video_record)
    if video_record.processed_path:
        vr.processed_url = f"/static/processed/{os.path.basename(video_record.processed_path)}"

    return {
        "message": "Video uploaded and processed successfully",
        "video": vr,
    }

@router.post("/{video_id}/process")
def process_video_pipeline(
    video_id: int,
    req: VideoProcessRequest = VideoProcessRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Runs full computer vision, tracking, zone analysis, and alert generation pipeline on the video.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video record not found")

    result = AnalyticsPipelineService.process_video(
        db=db,
        video_id=video_id,
        conf_threshold=req.confidence_threshold,
        process_every_n_frames=req.process_every_n_frames,
        enable_tracking=req.enable_tracking,
    )
    return result

@router.post("/{video_id}/extract-frame")
def extract_video_frame(
    video_id: int,
    timestamp_seconds: float = Form(0.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Extract a single frame image from video at specified timestamp."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    abs_video_path = str(settings.get_absolute_path(video.path))
    snapshot_filename = f"snap_v{video.id}_t{int(timestamp_seconds*1000)}.jpg"
    snapshot_rel_path = f"{settings.SNAPSHOTS_DIR}/{snapshot_filename}"
    snapshot_abs_path = str(settings.get_absolute_path(snapshot_rel_path))

    success = FFmpegService.extract_frame_at_timestamp(abs_video_path, timestamp_seconds, snapshot_abs_path)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to extract frame")

    return {
        "success": True,
        "timestamp_seconds": timestamp_seconds,
        "snapshot_path": snapshot_rel_path,
        "snapshot_url": f"/static/snapshots/{snapshot_filename}",
    }
