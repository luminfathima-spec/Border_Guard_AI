import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

@pytest.mark.asyncio
async def test_full_video_analytics_pipeline():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Upload video assigned to CAM-NP-01 (camera_id=1)
        test_video_path = settings.get_absolute_path("data/uploads/sample_border_surveillance.mp4")
        assert os.path.exists(test_video_path), "Sample video must exist"

        with open(test_video_path, "rb") as f:
            files = {"file": ("border_recon_pipeline_test.mp4", f.read(), "video/mp4")}
            upload_res = await ac.post(
                "/api/v1/videos/upload",
                files=files,
                data={"camera_id": 1},
                headers=headers
            )
        assert upload_res.status_code == 201
        video_id = upload_res.json()["video"]["id"]

        # 3. Trigger Analytics Pipeline Processing
        proc_res = await ac.post(
            f"/api/v1/videos/{video_id}/process",
            json={"confidence_threshold": 0.25, "process_every_n_frames": 4},
            headers=headers
        )
        assert proc_res.status_code == 200
        proc_data = proc_res.json()
        assert proc_data["status"] == "COMPLETED"
        assert proc_data["total_frames_inspected"] > 0

        # 4. Verify Analytics Overview Endpoint reflects new state
        analytics_res = await ac.get("/api/v1/analytics/overview", headers=headers)
        assert analytics_res.status_code == 200
        overview = analytics_res.json()
        assert overview["total_cameras"] >= 4
        assert overview["active_cameras"] >= 1
        assert "events_by_type" in overview
