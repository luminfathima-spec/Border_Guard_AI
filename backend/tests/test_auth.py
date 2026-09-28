import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_auth_login_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@sentinel.ai"
    assert data["user"]["role"] == "ADMIN"

@pytest.mark.asyncio
async def test_auth_login_invalid_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "WrongPassword123!"
        })
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_me_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "analyst@sentinel.ai",
            "password": "AnalystPassword123!"
        })
        token = login_res.json()["access_token"]

        # 2. Access /me
        me_res = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "analyst@sentinel.ai"
        assert me_res.json()["role"] == "SECURITY_ANALYST"

@pytest.mark.asyncio
async def test_rbac_protection():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Operator login
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "operator@sentinel.ai",
            "password": "OperatorPassword123!"
        })
        token = login_res.json()["access_token"]

        # Operator tries to list users (allowed for ADMIN/ANALYST only)
        users_res = await ac.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
        assert users_res.status_code == 403
