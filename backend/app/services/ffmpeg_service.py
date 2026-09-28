import os
import subprocess
import json
import cv2
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from app.core.logging import logger

class FFmpegService:
    @staticmethod
    def get_video_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extracts duration, resolution, fps, and total frame count using OpenCV with ffprobe metadata extraction.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found at {file_path}")

        # Use OpenCV for direct, robust frame inspection
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file {file_path}")

        try:
            fps = float(cap.get(cv2.CAP_PROP_FPS)) or 25.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
            duration = float(total_frames / fps) if fps > 0 and total_frames > 0 else 0.0
            resolution = f"{width}x{height}" if width and height else "Unknown"
            file_size_bytes = os.path.getsize(file_path)

            return {
                "duration": round(duration, 2),
                "resolution": resolution,
                "fps": round(fps, 2),
                "total_frames": total_frames,
                "width": width,
                "height": height,
                "file_size_bytes": file_size_bytes,
            }
        finally:
            cap.release()

    @staticmethod
    def extract_frame_at_timestamp(
        video_path: str,
        timestamp_seconds: float,
        output_image_path: str,
    ) -> bool:
        """
        Extracts a single high-quality frame JPEG at the given timestamp using OpenCV.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video {video_path} for frame extraction")
            return False

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            target_frame = int(timestamp_seconds * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()

            if not ret or frame is None:
                # Fallback to seeking in milliseconds
                cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_seconds * 1000)
                ret, frame = cap.read()

            if ret and frame is not None:
                os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
                cv2.imwrite(output_image_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
                return True
            return False
        except Exception as e:
            logger.error(f"Error extracting frame at {timestamp_seconds}s from {video_path}: {e}")
            return False
        finally:
            cap.release()

    @staticmethod
    def extract_evidence_clip(
        video_path: str,
        start_seconds: float,
        duration_seconds: float,
        output_clip_path: str,
    ) -> bool:
        """
        Extracts a short video clip using FFmpeg with fast seeking and H.264 stream copying/encoding.
        """
        os.makedirs(os.path.dirname(output_clip_path), exist_ok=True)
        start_time = max(0.0, start_seconds)

        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-i", video_path,
            "-t", str(duration_seconds),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-c:a", "aac",
            "-movflags", "+faststart",
            output_clip_path,
        ]

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if result.returncode == 0 and os.path.exists(output_clip_path):
                return True
            else:
                logger.warning(f"FFmpeg clip extraction warning: {result.stderr[:200]}")
                # Fallback to simple stream copy
                fallback_cmd = [
                    "ffmpeg", "-y", "-ss", str(start_time), "-i", video_path,
                    "-t", str(duration_seconds), "-c", "copy", output_clip_path
                ]
                res2 = subprocess.run(fallback_cmd, capture_output=True, text=True)
                return res2.returncode == 0 and os.path.exists(output_clip_path)
        except Exception as e:
            logger.error(f"FFmpeg process execution failed: {e}")
            return False
