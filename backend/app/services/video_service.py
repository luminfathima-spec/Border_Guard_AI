import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.video import Video, VideoStatus
from app.models.camera import Camera
from app.services.ffmpeg_service import FFmpegService

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

class VideoService:
    @staticmethod
    def validate_file_extension(filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        return ext

    @staticmethod
    def save_upload_file(upload_file: UploadFile) -> Tuple[str, str, int]:
        """
        Saves uploaded file securely with UUID to prevent path traversal and collisions.
        Returns (saved_filename, relative_path, file_size_bytes).
        """
        original_name = upload_file.filename or "video.mp4"
        ext = VideoService.validate_file_extension(original_name)

        safe_filename = f"{uuid.uuid4().hex}{ext}"
        upload_dir = settings.get_absolute_path(settings.UPLOAD_DIR)
        os.makedirs(upload_dir, exist_ok=True)
        dest_path = upload_dir / safe_filename

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        bytes_written = 0

        with open(dest_path, "wb") as buffer:
            while chunk := upload_file.file.read(1024 * 1024):  # 1MB chunks
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    buffer.close()
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
                    )
                buffer.write(chunk)

        relative_path = os.path.relpath(dest_path, settings.get_absolute_path("."))
        return safe_filename, str(relative_path).replace("\\", "/"), bytes_written

    @staticmethod
    def create_video_record(
        db: Session,
        upload_file: UploadFile,
        camera_id: Optional[int] = None
    ) -> Video:
        """
        Processes upload, probes metadata, and persists Video entity to database.
        """
        if camera_id:
            camera = db.query(Camera).filter(Camera.id == camera_id).first()
            if not camera:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned camera not found")

        safe_filename, rel_path, file_size = VideoService.save_upload_file(upload_file)
        abs_path = settings.get_absolute_path(rel_path)

        # Extract metadata
        try:
            meta = FFmpegService.get_video_metadata(str(abs_path))
        except Exception as e:
            logger.warning(f"Could not extract full video metadata: {e}")
            meta = {
                "duration": None,
                "resolution": None,
                "fps": None,
                "total_frames": None,
            }

        video_record = Video(
            filename=safe_filename,
            original_filename=upload_file.filename or safe_filename,
            path=rel_path,
            duration=meta.get("duration"),
            resolution=meta.get("resolution"),
            fps=meta.get("fps"),
            total_frames=meta.get("total_frames"),
            file_size_bytes=file_size,
            status=VideoStatus.PENDING.value,
            camera_id=camera_id,
        )

        db.add(video_record)
        db.commit()
        db.refresh(video_record)
        logger.info(f"Video uploaded and registered: {video_record.id} ({video_record.original_filename})")
        return video_record
