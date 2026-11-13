import os
import re
import shutil
import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, Request, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db, SessionLocal
from app.models.video import Video, VideoStatus
from app.models.user import User
from app.schemas.video import (
    VideoResponse,
    VideoUploadResponse,
    VideoProcessRequest,
    DemoVideoInfo,
    VideoIngestionStatusResponse,
)
from app.models.track import ObjectTrack
from app.schemas.track import ObjectTrackResponse
from app.models.detection import Detection
from app.schemas.detection import DetectionResponse
from app.models.event import SecurityEvent
from app.schemas.event import SecurityEventResponse as EventResponse
from app.services.video_service import VideoService
from app.services.ffmpeg_service import FFmpegService
from app.services.analytics_pipeline import AnalyticsPipelineService
from app.api.deps import get_current_active_user
from app.core.config import settings
from app.core.security import decode_access_token
from app.core.logging import logger

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


def run_background_pipeline(video_id: int):
    """Executes computer vision analytics pipeline in background worker."""
    db = SessionLocal()
    try:
        AnalyticsPipelineService.process_video(
            db=db,
            video_id=video_id,
            enable_tracking=True,
        )
    except Exception as e:
        logger.error(f"Background pipeline failed for video {video_id}: {e}", exc_info=True)
    finally:
        db.close()


def get_user_from_header_or_query(
    request: Request,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> User:
    """Authenticates user from either Authorization header or ?token= query parameter."""
    auth_header = request.headers.get("Authorization")
    raw_token = None
    if auth_header and auth_header.startswith("Bearer "):
        raw_token = auth_header[7:]
    elif token:
        raw_token = token

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )

    try:
        payload = decode_access_token(raw_token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


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

    # Compute checksum
    import hashlib
    with open(dest_abs_path, "rb") as f:
        checksum = hashlib.sha256(f.read()).hexdigest()

    video_record = Video(
        filename=dest_filename,
        original_filename=selected_demo["filename"],
        path=dest_rel_path,
        duration=selected_demo["duration_seconds"],
        resolution=selected_demo["resolution"],
        fps=25.0,
        total_frames=150,
        file_size_bytes=os.path.getsize(dest_abs_path),
        checksum_sha256=checksum,
        status=VideoStatus.PENDING.value,
        camera_id=camera_id or 1,
    )
    db.add(video_record)
    db.commit()
    db.refresh(video_record)

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


@router.get("/{video_id}/status", response_model=VideoIngestionStatusResponse)
def get_video_status(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve detailed ingestion status and error diagnostics for a video job."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video record not found")

    return VideoIngestionStatusResponse(
        video_id=video.id,
        id=video.id,
        filename=video.filename,
        status=video.status,
        error_message=video.error_message,
        file_size_bytes=video.file_size_bytes,
        checksum_sha256=video.checksum_sha256,
        duration=video.duration,
        resolution=video.resolution,
        fps=video.fps,
        processing_started_at=video.processing_started_at,
        processing_completed_at=video.processing_completed_at,
        created_at=video.created_at,
    )


@router.post("/upload", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    camera_id: Optional[int] = Form(None),
    source_timestamp: Optional[str] = Form(None),
    auto_process: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Uploads surveillance footage with chunked streaming, SHA-256 calculation, container validation,
    and duration limits. Dispatches processing asynchronously without blocking the HTTP response.
    """
    parsed_source_time = None
    if source_timestamp:
        try:
            parsed_source_time = datetime.datetime.fromisoformat(source_timestamp.replace("Z", "+00:00"))
        except Exception:
            pass

    video_record = VideoService.create_video_record(
        db,
        file,
        camera_id=camera_id,
        source_timestamp=parsed_source_time,
    )

    if auto_process:
        background_tasks.add_task(run_background_pipeline, video_record.id)

    vr = VideoResponse.model_validate(video_record)
    if video_record.processed_path:
        vr.processed_url = f"/static/processed/{os.path.basename(video_record.processed_path)}"

    return {
        "message": "Video uploaded and queued for processing successfully",
        "video": vr,
    }


def range_streamer(file_path: Path, start: int, end: int, chunk_size: int = 256 * 1024):
    """Generator yielding bytes within a specified file range."""
    with open(file_path, "rb") as f:
        f.seek(start)
        bytes_to_read = end - start + 1
        while bytes_to_read > 0:
            read_bytes = min(chunk_size, bytes_to_read)
            data = f.read(read_bytes)
            if not data:
                break
            bytes_to_read -= len(data)
            yield data


@router.get("/{video_id}/stream")
def stream_video(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_user_from_header_or_query),
):
    """
    Safe video preview and playback endpoint supporting HTTP 206 Partial Content (Range requests).
    Enforces strict path traversal verification and authenticated access via Bearer header or ?token=.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video record not found")

    target_path = VideoService.get_safe_video_path(video)
    file_size = target_path.stat().st_size
    range_header = request.headers.get("Range")

    if range_header:
        # Parse range header: e.g. bytes=0-1048576 or bytes=1024-
        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if match:
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else file_size - 1
            end = min(end, file_size - 1)
            content_length = end - start + 1

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Content-Type": video.mime_type or "video/mp4",
            }
            return StreamingResponse(
                range_streamer(target_path, start, end),
                status_code=status.HTTP_206_PARTIAL_CONTENT,
                headers=headers,
            )

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Type": video.mime_type or "video/mp4",
    }
    return StreamingResponse(
        range_streamer(target_path, 0, file_size - 1),
        status_code=status.HTTP_200_OK,
        headers=headers,
    )


@router.post("/{video_id}/process")
@router.post("/{video_id}/detect")
def process_video_pipeline(
    video_id: int,
    req: VideoProcessRequest = VideoProcessRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Runs full computer vision, tracking, zone analysis, and alert generation pipeline on the video.
    Supports temporal confirmation frames, custom resolution scaling, and boundary configurations.
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
        temporal_confirmation_frames=req.temporal_confirmation_frames,
        target_resolution=req.target_resolution,
        loiter_threshold_seconds=req.loiter_threshold_seconds,
        restricted_zones=req.restricted_zones,
        virtual_lines=req.virtual_lines,
    )
    return result


@router.get("/{video_id}/detections", response_model=List[DetectionResponse])
def get_video_detections(
    video_id: int,
    object_type: Optional[str] = None,
    tracking_id: Optional[int] = None,
    limit: int = Query(200, le=2000),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve detections for a specific video file with optional target/type filtering."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video record not found")

    query = db.query(Detection).filter(Detection.video_id == video_id)
    if object_type:
        query = query.filter(Detection.object_type == object_type.lower())
    if tracking_id is not None:
        query = query.filter(Detection.tracking_id == tracking_id)

    return query.order_by(Detection.frame_number.asc()).offset(offset).limit(limit).all()


@router.get("/{video_id}/tracks", response_model=List[ObjectTrackResponse])
def get_video_tracks(
    video_id: int,
    object_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve multi-frame object trajectories and dwell times for a video."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video record not found")

    query = db.query(ObjectTrack).filter(ObjectTrack.video_id == video_id)
    if object_type:
        query = query.filter(ObjectTrack.object_type == object_type.lower())
    if is_active is not None:
        query = query.filter(ObjectTrack.is_active == is_active)

    return query.order_by(ObjectTrack.first_seen_frame.asc()).all()


@router.get("/{video_id}/events", response_model=List[EventResponse])
def get_video_events(
    video_id: int,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve security events generated from this video, with linked evidence."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video record not found")

    query = db.query(SecurityEvent).filter(SecurityEvent.video_id == video_id)
    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)
    if severity:
        query = query.filter(SecurityEvent.severity == severity)

    return query.order_by(SecurityEvent.id.desc()).all()


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
