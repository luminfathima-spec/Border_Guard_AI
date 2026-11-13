import time
import re
from typing import Dict, Any, Optional
import cv2

from app.core.config import settings
from app.core.logging import logger


class RTSPService:
    @staticmethod
    def mask_url(url: Optional[str]) -> Optional[str]:
        """
        Sanitizes and masks embedded passwords in RTSP or HTTP URLs.
        e.g. rtsp://admin:SecretPass123@192.168.1.50:554/live -> rtsp://admin:****@192.168.1.50:554/live
        """
        if not url:
            return url
        return re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", url)

    @staticmethod
    def test_stream_connection(
        stream_url: str,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Tests RTSP or HTTP video stream connectivity safely with OpenCV:
        1. Connects with configured timeout.
        2. Probes single test frame to confirm decoding.
        3. Measures connection round-trip latency.
        4. Sanitizes credentials before logging or returning results.
        """
        timeout = timeout_seconds or settings.RTSP_CONNECT_TIMEOUT_SECONDS
        masked_url = RTSPService.mask_url(stream_url)
        logger.info(f"Testing RTSP stream connection to {masked_url} (timeout: {timeout}s)")

        start_time = time.time()
        cap = cv2.VideoCapture()

        # Set timeout properties if supported by OpenCV backend
        try:
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout * 1000)
        except Exception:
            pass

        try:
            opened = cap.open(stream_url)
            elapsed_ms = int((time.time() - start_time) * 1000)

            if not opened or not cap.isOpened():
                logger.warning(f"RTSP stream connection failed to {masked_url} after {elapsed_ms}ms")
                err_msg = f"Failed to connect or stream timed out after {timeout} seconds"
                return {
                    "connected": False,
                    "stream_url": masked_url,
                    "latency_ms": elapsed_ms,
                    "resolution": None,
                    "fps": None,
                    "error": err_msg,
                    "message": err_msg,
                }

            # Attempt reading single frame to confirm decode capability
            ret, frame = cap.read()
            if not ret or frame is None:
                logger.warning(f"RTSP stream opened but failed to decode test frame from {masked_url}")
                err_msg = "Stream connected but no video frame could be decoded"
                return {
                    "connected": False,
                    "stream_url": masked_url,
                    "latency_ms": elapsed_ms,
                    "resolution": None,
                    "fps": None,
                    "error": err_msg,
                    "message": err_msg,
                }

            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or frame.shape[1]
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or frame.shape[0]
            fps = float(cap.get(cv2.CAP_PROP_FPS)) or 25.0

            logger.info(f"RTSP stream connection verified: {masked_url} ({width}x{height} @ {fps:.1f} FPS, {elapsed_ms}ms)")
            return {
                "connected": True,
                "stream_url": masked_url,
                "latency_ms": elapsed_ms,
                "resolution": f"{width}x{height}",
                "fps": round(fps, 2),
                "error": None,
                "message": f"Successfully connected to stream ({width}x{height} @ {fps:.1f} FPS)",
            }

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Error testing RTSP stream connection {masked_url}: {e}")
            err_msg = f"Connection error: {str(e)}"
            return {
                "connected": False,
                "stream_url": masked_url,
                "latency_ms": elapsed_ms,
                "resolution": None,
                "fps": None,
                "error": err_msg,
                "message": err_msg,
            }
        finally:
            cap.release()

    @staticmethod
    def reconnect_stream(
        stream_url: str,
        max_retries: Optional[int] = None,
        backoff_seconds: Optional[float] = None,
    ) -> bool:
        """
        Executes exponential backoff reconnection loop for dropped streams.
        """
        retries = max_retries or settings.RTSP_RECONNECT_RETRIES
        backoff = backoff_seconds or settings.RTSP_RECONNECT_BACKOFF_SECONDS
        masked_url = RTSPService.mask_url(stream_url)

        for attempt in range(1, retries + 1):
            logger.info(f"Attempting reconnection to {masked_url} (attempt {attempt}/{retries})...")
            res = RTSPService.test_stream_connection(stream_url, timeout_seconds=3)
            if res.get("connected"):
                logger.info(f"Successfully reconnected to {masked_url} on attempt {attempt}")
                return True
            time.sleep(backoff * attempt)

        logger.error(f"Failed to reconnect to {masked_url} after {retries} attempts.")
        return False
