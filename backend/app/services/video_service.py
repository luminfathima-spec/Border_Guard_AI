import os
import re
import uuid
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Union
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
import cv2

from app.core.config import settings
from app.core.logging import logger
from app.models.video import Video, VideoStatus
from app.models.camera import Camera

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

# Magic byte signatures for video containers
MAGIC_SIGNATURES = [
    (4, b"ftyp"),  # MP4 / MOV (ISO Base Media File Format)
    (4, b"moov"),  # QuickTime MOV
    (0, b"RIFF"),  # AVI (checked with AVI sub-signature)
    (0, b"\x1a\x45\xdf\xa3"),  # Matroska MKV / WebM (EBML)
]


class VideoService:
    @staticmethod
    def validate_file_extension(filename: str) -> str:
        """Validates extension against whitelist."""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )
        return ext

    @staticmethod
    def validate_magic_bytes(header: bytes) -> bool:
        """
        Validates initial bytes against known video container signatures.
        """
        if len(header) < 12:
            return False

        # Check MP4 / MOV ftyp / moov
        if header[4:8] == b"ftyp" or header[4:8] == b"moov":
            return True

        # Check AVI (RIFF ... AVI )
        if header[0:4] == b"RIFF" and header[8:12] == b"AVI ":
            return True

        # Check MKV / WebM
        if header[0:4] == b"\x1a\x45\xdf\xa3":
            return True

        return False

    @staticmethod
    def save_upload_file(upload_file: UploadFile) -> Tuple[str, str, int, str, str]:
        """
        Saves uploaded video securely in 1MB chunks:
        - Validates file extension and container magic bytes.
        - Streams in chunks without loading entire file in RAM.
        - Computes SHA-256 cryptographic digest incrementally.
        - Enforces MAX_UPLOAD_SIZE_MB limit.
        - Generates non-guessable UUID filename to prevent path traversal.

        Returns (safe_filename, relative_path, file_size_bytes, checksum_sha256, mime_type).
        """
        original_name = upload_file.filename or "video.mp4"
        ext = VideoService.validate_file_extension(original_name)

        # Inspect header bytes
        header = upload_file.file.read(16)
        if not VideoService.validate_magic_bytes(header):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupt or invalid video file: container header bytes do not match a valid video format.",
            )

        safe_filename = f"{uuid.uuid4().hex}{ext}"
        upload_dir = settings.get_absolute_path(settings.UPLOAD_DIR)
        os.makedirs(upload_dir, exist_ok=True)
        dest_path = upload_dir / safe_filename

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        bytes_written = len(header)
        hasher = hashlib.sha256()
        hasher.update(header)

        try:
            with open(dest_path, "wb") as buffer:
                buffer.write(header)
                while chunk := upload_file.file.read(1024 * 1024):  # 1MB chunk
                    bytes_written += len(chunk)
                    if bytes_written > max_bytes:
                        buffer.close()
                        if os.path.exists(dest_path):
                            os.remove(dest_path)
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB",
                        )
                    hasher.update(chunk)
                    buffer.write(chunk)
        except HTTPException:
            raise
        except Exception as e:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save upload file: {str(e)}",
            )

        relative_path = os.path.relpath(dest_path, settings.get_absolute_path("."))
        checksum = hasher.hexdigest()
        mime_type = upload_file.content_type or "video/mp4"

        return safe_filename, str(relative_path).replace("\\", "/"), bytes_written, checksum, mime_type

    @staticmethod
    def validate_video_stream(abs_path: str) -> Dict[str, Any]:
        """
        Validates video stream readability with OpenCV and enforces duration limits.
        """
        cap = cv2.VideoCapture(abs_path)
        if not cap.isOpened():
            cap.release()
            try:
                if os.path.exists(abs_path):
                    os.remove(abs_path)
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid video file: OpenCV was unable to decode the video stream.",
            )

        try:
            ret, frame = cap.read()
            if not ret or frame is None:
                cap.release()
                try:
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                except Exception:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Corrupt video file: No video frames could be decoded.",
                )

            fps = float(cap.get(cv2.CAP_PROP_FPS)) or 25.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or frame.shape[1]
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or frame.shape[0]
            duration = float(total_frames / fps) if fps > 0 and total_frames > 0 else 0.0

            # Enforce duration limit
            if duration > settings.MAX_VIDEO_DURATION_SECONDS:
                cap.release()
                try:
                    if os.path.exists(abs_path):
                        os.remove(abs_path)
                except Exception:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Video duration ({round(duration, 1)}s) exceeds maximum allowed limit of {settings.MAX_VIDEO_DURATION_SECONDS}s",
                )

            return {
                "duration": round(duration, 2),
                "resolution": f"{width}x{height}",
                "fps": round(fps, 2),
                "total_frames": total_frames,
                "width": width,
                "height": height,
            }
        finally:
            cap.release()

    @staticmethod
    def create_video_record(
        db: Session,
        upload_file: UploadFile,
        camera_id: Optional[int] = None,
        source_timestamp: Optional[Any] = None,
    ) -> Video:
        """
        Validates upload, probes stream metadata, and persists Video entity to database.
        """
        if camera_id:
            camera = db.query(Camera).filter(Camera.id == camera_id).first()
            if not camera:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned camera not found")

        safe_filename, rel_path, file_size, checksum, mime = VideoService.save_upload_file(upload_file)
        abs_path = str(settings.get_absolute_path(rel_path))

        # Validate video stream and duration
        meta = VideoService.validate_video_stream(abs_path)

        video_record = Video(
            filename=safe_filename,
            original_filename=upload_file.filename or safe_filename,
            path=rel_path,
            duration=meta.get("duration"),
            resolution=meta.get("resolution"),
            fps=meta.get("fps"),
            total_frames=meta.get("total_frames"),
            file_size_bytes=file_size,
            checksum_sha256=checksum,
            source_timestamp=source_timestamp,
            mime_type=mime,
            status=VideoStatus.PENDING.value,
            camera_id=camera_id,
        )

        db.add(video_record)
        db.commit()
        db.refresh(video_record)
        logger.info(f"Video successfully ingested: {video_record.id} ({video_record.original_filename}, {video_record.checksum_sha256[:12]}...)")
        return video_record

    @staticmethod
    def get_safe_video_path(video: Union[Video, str]) -> Path:
        """
        Enforces strict path traversal protection.
        Ensures target video file resolves strictly within authorized media directories.
        """
        raw_path = video.path if hasattr(video, "path") else str(video)
        if not raw_path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video path not registered")

        # Resolve path
        if raw_path.startswith("/") or raw_path.startswith("\\") or (len(raw_path) > 1 and raw_path[1] == ":"):
            target_path = Path(raw_path).resolve()
        else:
            target_path = settings.get_absolute_path(raw_path).resolve()

        # Whitelist allowed root directories
        allowed_roots = [
            settings.get_absolute_path(settings.UPLOAD_DIR).resolve(),
            settings.get_absolute_path(settings.EVIDENCE_DIR).resolve(),
            settings.get_absolute_path(settings.PROCESSED_DIR).resolve(),
            settings.get_absolute_path("demo_videos").resolve(),
            settings.get_absolute_path("data").resolve(),
        ]

        # Verify target is child of at least one allowed root
        is_safe = False
        for root in allowed_roots:
            try:
                target_path.relative_to(root)
                is_safe = True
                break
            except ValueError:
                continue

        if not is_safe:
            logger.warning(f"Path traversal attempt blocked: {target_path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to the requested file path is restricted.",
            )

        if not target_path.exists() or not target_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video file does not exist on disk.",
            )

        return target_path
