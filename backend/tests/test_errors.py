import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_404_consistent_error_schema():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/non_existent_endpoint_for_test")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["status_code"] == 404
    assert data["error_code"] == "HTTP_ERROR"
    assert "timestamp" in data
    assert data["path"] == "/api/v1/non_existent_endpoint_for_test"


@pytest.mark.asyncio
async def test_422_validation_error_schema():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # POST with invalid payload to login endpoint (missing required email & password fields)
        response = await ac.post("/api/v1/auth/login", json={"invalid_field": 123})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert data["status_code"] == 422
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "errors" in data
    assert "timestamp" in data
    assert data["path"] == "/api/v1/auth/login"
