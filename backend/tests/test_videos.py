import os
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

@pytest.mark.asyncio
async def test_upload_and_list_videos():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]

        test_video_path = settings.get_absolute_path("data/uploads/sample_border_surveillance.mp4")
        assert os.path.exists(test_video_path), "Sample test video must exist"

        with open(test_video_path, "rb") as f:
            video_bytes = f.read()

        # Upload video
        files = {"file": ("test_surveillance.mp4", video_bytes, "video/mp4")}
        data = {"camera_id": 1}
        res = await ac.post(
            "/api/v1/videos/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 201
        upload_json = res.json()
        assert "video" in upload_json
        video_id = upload_json["video"]["id"]
        assert upload_json["video"]["fps"] is not None

        # Get video by ID
        get_res = await ac.get(f"/api/v1/videos/{video_id}", headers={"Authorization": f"Bearer {token}"})
        assert get_res.status_code == 200
        assert get_res.json()["id"] == video_id

        # Extract frame
        extract_res = await ac.post(
            f"/api/v1/videos/{video_id}/extract-frame",
            data={"timestamp_seconds": 1.0},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert extract_res.status_code == 200
        assert extract_res.json()["success"] is True
