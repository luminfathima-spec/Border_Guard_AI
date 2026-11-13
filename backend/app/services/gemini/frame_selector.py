import os
import cv2
import numpy as np
from typing import List, Optional
from sqlalchemy.orm import Session
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger
from app.models.incident import Incident
from app.models.evidence import Evidence
from app.models.event import SecurityEvent

class EventTriggeredFrameSelector:
    """
    Event-Triggered Multimodal Keyframe Extractor.
    Extracts relevant keyframe snapshots corresponding to confirmed security events
    rather than streaming continuous video feeds, minimizing bandwidth, cost, and privacy exposure.
    """

    MAX_DIMENSION: int = 1024
    JPEG_QUALITY: int = 85

    @classmethod
    def select_incident_keyframes(
        cls,
        db: Session,
        incident_id: int,
        max_frames: int = 3,
    ) -> List[bytes]:
        """
        Selects up to max_frames JPEG byte streams for an incident:
        1. Checks existing SNAPSHOT evidence records.
        2. Extracts keyframes from source video files at event timestamps if snapshots unavailable.
        3. Downsamples and compresses to JPEG bytes.
        """
        frames: List[bytes] = []

        # 1. Check existing SNAPSHOT evidence items
        snapshots = (
            db.query(Evidence)
            .filter(Evidence.incident_id == incident_id, Evidence.evidence_type.in_(["SNAPSHOT", "IMAGE"]))
            .order_by(Evidence.timestamp.asc())
            .limit(max_frames)
            .all()
        )

        for snap in snapshots:
            file_path = settings.get_absolute_path(snap.file_path)
            if file_path.exists() and file_path.is_file():
                try:
                    img = cv2.imread(str(file_path))
                    if img is not None:
                        compressed = cls._compress_image(img)
                        if compressed:
                            frames.append(compressed)
                except Exception as e:
                    logger.warning(f"Failed to read snapshot file {file_path}: {e}")

        if len(frames) >= max_frames:
            return frames[:max_frames]

        # 2. Extract keyframes from associated video files if more frames needed
        video_evidence = (
            db.query(Evidence)
            .filter(Evidence.incident_id == incident_id, Evidence.evidence_type.in_(["VIDEO_CLIP", "VIDEO"]))
            .first()
        )

        if video_evidence:
            vpath = settings.get_absolute_path(video_evidence.file_path)
            if vpath.exists() and vpath.is_file():
                extracted = cls._extract_from_video(str(vpath), num_frames=max_frames - len(frames))
                frames.extend(extracted)

        return frames[:max_frames]

    @classmethod
    def _extract_from_video(cls, video_path: str, num_frames: int = 2) -> List[bytes]:
        """Extracts evenly spaced keyframes from a video file."""
        extracted: List[bytes] = []
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return extracted

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                return extracted

            # Sample at 25%, 50%, 75% points
            sample_points = [
                int(total_frames * (i + 1) / (num_frames + 1))
                for i in range(num_frames)
            ]

            for frame_idx in sample_points:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret and frame is not None:
                    compressed = cls._compress_image(frame)
                    if compressed:
                        extracted.append(compressed)
        except Exception as e:
            logger.warning(f"Error sampling frames from {video_path}: {e}")
        finally:
            cap.release()

        return extracted

    @classmethod
    def _compress_image(cls, img: np.ndarray) -> Optional[bytes]:
        """Resizes to MAX_DIMENSION and encodes as JPEG bytes."""
        try:
            h, w = img.shape[:2]
            if max(h, w) > cls.MAX_DIMENSION:
                scale = cls.MAX_DIMENSION / float(max(h, w))
                new_w, new_h = int(w * scale), int(h * scale)
                img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), cls.JPEG_QUALITY]
            success, buffer = cv2.imencode(".jpg", img, encode_params)
            if success:
                return buffer.tobytes()
        except Exception as e:
            logger.warning(f"Failed to compress frame to JPEG: {e}")
        return None
