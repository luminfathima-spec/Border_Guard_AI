import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_list_cameras():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Login
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]

        # List cameras
        res = await ac.get("/api/v1/cameras", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        cameras = res.json()
        assert len(cameras) >= 4
        assert any(c["camera_identifier"] == "CAM-NP-01" for c in cameras)

@pytest.mark.asyncio
async def test_create_and_update_camera():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]

        # Create camera with unique identifier
        unique_id = f"CAM-DRONE-{uuid.uuid4().hex[:6].upper()}"
        new_cam_payload = {
            "name": "Test Drone Relay Cam",
            "camera_identifier": unique_id,
            "location": "Aero Sector 1",
            "status": "ONLINE",
            "zone": "Sector 1 Aerial",
            "restricted_zones": [],
            "virtual_lines": [],
        }
        res = await ac.post("/api/v1/cameras", json=new_cam_payload, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 201
        cam_data = res.json()
        assert cam_data["camera_identifier"] == unique_id

        # Update camera
        patch_res = await ac.patch(f"/api/v1/cameras/{cam_data['id']}", json={"status": "DEGRADED"}, headers={"Authorization": f"Bearer {token}"})
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "DEGRADED"
