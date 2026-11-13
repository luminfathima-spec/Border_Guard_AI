import os
import hashlib
import uuid
import pytest
from pathlib import Path
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from fastapi import HTTPException
from app.main import app
from app.core.config import settings
from app.services.video_service import VideoService
from app.services.rtsp_service import RTSPService


@pytest.fixture
def sample_video_bytes():
    """Load real sample MP4 video bytes from project uploads."""
    video_path = settings.get_absolute_path("data/uploads/sample_border_surveillance.mp4")
    assert os.path.exists(video_path), f"Sample video not found at {video_path}"
    with open(video_path, "rb") as f:
        return f.read()


@pytest.mark.asyncio
async def test_upload_valid_video_with_sha256(sample_video_bytes):
    """Test valid MP4 upload verifies SHA-256 checksum and extracts metadata."""
    expected_sha256 = hashlib.sha256(sample_video_bytes).hexdigest()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]

        files = {"file": ("patrol_stream_alpha.mp4", sample_video_bytes, "video/mp4")}
        res = await ac.post(
            "/api/v1/videos/upload",
            files=files,
            data={"camera_id": 1, "auto_process": "false"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 201
        data = res.json()
        assert "video" in data
        video = data["video"]

        assert video["checksum_sha256"] == expected_sha256
        assert video["duration"] is not None
        assert video["duration"] > 0
        assert video["resolution"] is not None
        assert "x" in video["resolution"]
        assert video["fps"] is not None
        assert video["fps"] > 0
        assert video["total_frames"] is not None
        assert video["total_frames"] > 0
        assert video["file_size_bytes"] == len(sample_video_bytes)
        assert video["status"] in ["PENDING", "PROCESSING", "COMPLETED"]


@pytest.mark.asyncio
async def test_upload_invalid_extension():
    """Test uploading a file with an unpermitted extension returns 400 Bad Request."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]

        bad_bytes = b"echo 'malicious script' > script.sh"
        files = {"file": ("exploit.sh", bad_bytes, "application/x-sh")}
        res = await ac.post(
            "/api/v1/videos/upload",
            files=files,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 400
        assert "Unsupported file format" in res.json()["detail"]


@pytest.mark.asyncio
async def test_upload_fake_mp4_magic_bytes():
    """Test uploading a file named .mp4 but with text/garbage bytes fails magic byte validation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]

        fake_video_bytes = b"This is plain text pretending to be an MP4 video file container."
        files = {"file": ("fake_cctv.mp4", fake_video_bytes, "video/mp4")}
        res = await ac.post(
            "/api/v1/videos/upload",
            files=files,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 400
        assert "header bytes do not match" in res.json()["detail"]


@pytest.mark.asyncio
async def test_upload_oversized_file(sample_video_bytes):
    """Test file upload exceeding MAX_UPLOAD_SIZE_MB is rejected with 413."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]

        # Mock MAX_UPLOAD_SIZE_MB to be smaller than the test video
        with patch.object(settings, "MAX_UPLOAD_SIZE_MB", 0.0001):  # ~100 bytes limit
            files = {"file": ("oversized_video.mp4", sample_video_bytes, "video/mp4")}
            res = await ac.post(
                "/api/v1/videos/upload",
                files=files,
                headers={"Authorization": f"Bearer {token}"}
            )
            assert res.status_code == 413
            assert "exceeds maximum allowed size" in res.json()["detail"]


@pytest.mark.asyncio
async def test_upload_duration_limit_exceeded(sample_video_bytes):
    """Test file upload exceeding MAX_VIDEO_DURATION_SECONDS is rejected with 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]

        # Mock MAX_VIDEO_DURATION_SECONDS to 0.1s so sample video triggers limit
        with patch.object(settings, "MAX_VIDEO_DURATION_SECONDS", 0.1):
            files = {"file": ("long_footage.mp4", sample_video_bytes, "video/mp4")}
            res = await ac.post(
                "/api/v1/videos/upload",
                files=files,
                headers={"Authorization": f"Bearer {token}"}
            )
            assert res.status_code == 422
            assert "exceeds maximum allowed limit" in res.json()["detail"]


@pytest.mark.asyncio
async def test_video_streaming_partial_content(sample_video_bytes):
    """Test HTTP 206 Partial Content range requests for video playback."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]

        # 1. Upload a video to stream
        files = {"file": ("stream_test.mp4", sample_video_bytes, "video/mp4")}
        res = await ac.post(
            "/api/v1/videos/upload",
            files=files,
            data={"auto_process": "false"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 201
        video_id = res.json()["video"]["id"]
        total_size = len(sample_video_bytes)

        # 2. Test full stream (no Range header)
        full_stream_res = await ac.get(
            f"/api/v1/videos/{video_id}/stream",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert full_stream_res.status_code in [200, 206]
        assert full_stream_res.headers.get("accept-ranges") == "bytes"
        assert full_stream_res.headers.get("content-type") == "video/mp4"

        # 3. Test Partial Range: bytes=0-1023 (1024 bytes)
        range_res = await ac.get(
            f"/api/v1/videos/{video_id}/stream",
            headers={
                "Authorization": f"Bearer {token}",
                "Range": "bytes=0-1023"
            }
        )
        assert range_res.status_code == 206
        assert range_res.headers.get("content-range") == f"bytes 0-1023/{total_size}"
        assert range_res.headers.get("content-length") == "1024"
        assert len(range_res.content) == 1024
        assert range_res.content == sample_video_bytes[:1024]

        # 4. Test Query Parameter Token (for native <video> elements)
        token_param_res = await ac.get(
            f"/api/v1/videos/{video_id}/stream?token={token}",
            headers={"Range": "bytes=0-511"}
        )
        assert token_param_res.status_code == 206
        assert len(token_param_res.content) == 512

        # 5. Non-existent video stream returns 404
        missing_res = await ac.get(
            "/api/v1/videos/999999/stream",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert missing_res.status_code == 404


@pytest.mark.asyncio
async def test_video_ingestion_status(sample_video_bytes):
    """Test video ingestion status endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]

        # Upload
        files = {"file": ("status_check.mp4", sample_video_bytes, "video/mp4")}
        res = await ac.post(
            "/api/v1/videos/upload",
            files=files,
            data={"auto_process": "false"},
            headers={"Authorization": f"Bearer {token}"}
        )
        video_id = res.json()["video"]["id"]

        # Check status
        status_res = await ac.get(
            f"/api/v1/videos/{video_id}/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert (status_data.get("id") or status_data.get("video_id")) == video_id
        assert status_data["filename"] is not None
        assert status_data["status"] in ["PENDING", "PROCESSING", "COMPLETED"]
        assert status_data["checksum_sha256"] is not None


def test_path_traversal_guard():
    """Verify get_safe_video_path blocks directory traversal attacks."""
    with pytest.raises(HTTPException) as exc_info:
        VideoService.get_safe_video_path("../../etc/shadow")
    assert exc_info.value.status_code == 403

    with pytest.raises(HTTPException) as exc_info:
        VideoService.get_safe_video_path("..\\..\\Windows\\System32\\cmd.exe")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_rtsp_stream_testing_and_credential_masking():
    """Test RTSP stream connection probe masks sensitive credentials."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]

        raw_rtsp = "rtsp://admin:super_secret_password_123@127.0.0.1:55444/stream1"

        # 1. Direct test-stream endpoint
        res = await ac.post(
            "/api/v1/cameras/test-stream",
            json={"stream_url": raw_rtsp, "timeout_seconds": 1},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["connected"] is False  # Target port is closed
        assert "super_secret_password_123" not in data["stream_url"]
        assert "***" in data["stream_url"]
        assert "super_secret_password_123" not in str(data)

        # 2. Camera model serialization masks stream_url
        unique_id = f"CAM-RTSP-{uuid.uuid4().hex[:6].upper()}"
        cam_res = await ac.post(
            "/api/v1/cameras",
            json={
                "name": "Perimeter Cam 99",
                "camera_identifier": unique_id,
                "location": "Sector West",
                "status": "ONLINE",
                "stream_url": raw_rtsp,
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert cam_res.status_code == 201
        cam_data = cam_res.json()
        assert "super_secret_password_123" not in cam_data["stream_url"]
        assert "***" in cam_data["stream_url"]
        camera_id = cam_data["id"]

        # 3. Test camera connection endpoint
        conn_res = await ac.post(
            f"/api/v1/cameras/{camera_id}/test-connection",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert conn_res.status_code == 200
        conn_data = conn_res.json()
        assert conn_data["connected"] is False
        assert "super_secret_password_123" not in conn_data["stream_url"]
        assert "***" in conn_data["stream_url"]
        assert "super_secret_password_123" not in str(conn_data)
