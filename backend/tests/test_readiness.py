import pytest
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.routes.health import readiness_check
from fastapi import Response


@pytest.mark.asyncio
async def test_liveness_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SentinelAI"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert "checks" in data
    assert "database" in data["checks"]
    assert data["checks"]["database"]["status"] == "connected"
    assert "storage" in data["checks"]
    assert "cv_model" in data["checks"]
    assert "ai_engine" in data["checks"]


def test_readiness_endpoint_db_failure_simulation():
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("Connection lost")
    response = Response()
    
    result = readiness_check(response=response, db=mock_db)
    assert response.status_code == 503
    assert result["status"] == "unready"
    assert result["checks"]["database"]["status"] == "error"
