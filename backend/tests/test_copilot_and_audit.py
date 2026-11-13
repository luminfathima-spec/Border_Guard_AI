import os
import uuid
import pytest
import datetime
from sqlalchemy.orm import Session
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import SessionLocal
from app.models.camera import Camera, CameraStatus
from app.models.incident import Incident, IncidentStatus
from app.models.event import SecurityEvent
from app.models.evidence import Evidence
from app.models.report import Report, ReviewStatus
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.models.event_graph import EventLink, EvidenceObservation
from app.core.security import get_password_hash

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def copilot_test_setup(db_session: Session):
    # Ensure analyst user
    analyst = db_session.query(User).filter(User.email == "copilot_analyst@sentinel.ai").first()
    if not analyst:
        analyst = User(
            name="Copilot Analyst",
            email="copilot_analyst@sentinel.ai",
            password_hash=get_password_hash("mock_hash_123"),
            role=UserRole.SECURITY_ANALYST.value,
        )
        db_session.add(analyst)
    else:
        analyst.password_hash = get_password_hash("mock_hash_123")
    db_session.commit()
    db_session.refresh(analyst)

    # Ensure viewer user
    viewer = db_session.query(User).filter(User.email == "copilot_viewer@sentinel.ai").first()
    if not viewer:
        viewer = User(
            name="Copilot Viewer",
            email="copilot_viewer@sentinel.ai",
            password_hash=get_password_hash("mock_hash_viewer"),
            role=UserRole.VIEWER.value,
        )
        db_session.add(viewer)
    else:
        viewer.password_hash = get_password_hash("mock_hash_viewer")
    db_session.commit()
    db_session.refresh(viewer)

    # Ensure test camera
    cam = db_session.query(Camera).filter(Camera.name == "Sector 4 Main Post").first()
    if not cam:
        cam = Camera(
            name="Sector 4 Main Post",
            camera_identifier="CAM-COPILOT-04",
            location="Watchtower Alpha",
            stream_url="rtsp://localhost:8554/sec4",
            status=CameraStatus.ONLINE.value,
            zone="Sector 4",
        )
        db_session.add(cam)
        db_session.commit()
        db_session.refresh(cam)

    # Ensure test incident
    inc = db_session.query(Incident).filter(Incident.incident_number == "INC-COPILOT-99").first()
    if not inc:
        inc = Incident(
            incident_number="INC-COPILOT-99",
            title="Copilot Validation Incident",
            description="Testing Copilot natural language function calling",
            severity="HIGH",
            status=IncidentStatus.OPEN.value,
        )
        db_session.add(inc)
    else:
        inc.severity = "HIGH"
        inc.status = IncidentStatus.OPEN.value
    db_session.commit()
    db_session.refresh(inc)

    # Add security event
    ev = SecurityEvent(
        camera_id=cam.id,
        incident_id=inc.id,
        event_type="VIRTUAL_FENCE_BREACH",
        severity="HIGH",
        description="Target crossed tripwire at Sector 4 border line",
        confidence=0.96,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(ev)
    db_session.commit()
    db_session.refresh(ev)

    # Add evidence observation & link
    obs = EvidenceObservation(
        incident_id=inc.id,
        observation_type="CONFLICT_RECORD",
        provenance_type="DIRECT_OBSERVATION",
        title="Thermal and Optical Signature Discrepancy",
        description="Optical sensor indicates single target, but thermal sensor reports secondary signature",
        status="ACTIVE",
        details_json={"is_verified_in_db": False, "creation_reason": "Cross-sensor discrepancy"},
        confidence=0.88,
    )
    db_session.add(obs)
    db_session.commit()

    # Add test report
    rep = db_session.query(Report).filter(Report.report_number == "REP-COPILOT-01").first()
    if not rep:
        rep = Report(
            report_number="REP-COPILOT-01",
            incident_id=inc.id,
            title="Sector 4 Breach Investigation Dossier",
            status="COMPLETED",
            review_status=ReviewStatus.PENDING_REVIEW.value,
            sections_json={
                "factual_statements": [
                    {
                        "statement_id": 1,
                        "text": "Target breached primary security fence at 04:32 UTC.",
                        "statement_type": "CV_DETECTION",
                        "citation_status": "VERIFIED",
                        "supporting_evidence_ids": [],
                    }
                ],
                "evidence_used": [],
            },
            checksum_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        )
        db_session.add(rep)
        db_session.commit()
        db_session.refresh(rep)

    return {"analyst": analyst, "viewer": viewer, "camera": cam, "incident": inc, "report": rep}

@pytest.mark.asyncio
async def test_copilot_summarize_camera_events(copilot_test_setup):
    """Allow an authorized operator to summarize recorded events from a selected camera."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "copilot_analyst@sentinel.ai",
            "password": "mock_hash_123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        cam_id = copilot_test_setup["camera"].id
        res = await ac.post(
            "/api/v1/ai/copilot/chat",
            json={"message": f"Summarize recorded events from camera {cam_id}"},
            headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["tool_calls"]) >= 1
        assert data["tool_calls"][0]["tool_name"] == "summarize_camera_events"
        assert data["tool_calls"][0]["status"] == "SUCCESS"
        assert "Camera Telemetry Summary" in data["response"]

@pytest.mark.asyncio
async def test_copilot_show_incidents_with_unresolved_evidence(copilot_test_setup):
    """Allow an authorized operator to show incidents with unresolved evidence."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "copilot_analyst@sentinel.ai",
            "password": "mock_hash_123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        res = await ac.post(
            "/api/v1/ai/copilot/chat",
            json={"message": "Show incidents with unresolved evidence"},
            headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["tool_calls"]) >= 1
        assert data["tool_calls"][0]["tool_name"] == "get_incidents_with_unresolved_evidence"
        assert "Unresolved Evidence Gaps" in data["response"]

@pytest.mark.asyncio
async def test_copilot_find_events_by_zone_and_time(copilot_test_setup):
    """Allow an authorized operator to find events associated with a specified zone."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "copilot_analyst@sentinel.ai",
            "password": "mock_hash_123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        res = await ac.post(
            "/api/v1/ai/copilot/chat",
            json={"message": "Find events associated with Sector 4 in the last 24 hours"},
            headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["tool_calls"]) >= 1
        assert data["tool_calls"][0]["tool_name"] == "find_events_by_zone_and_time"
        assert "Sector 4" in data["response"]

@pytest.mark.asyncio
async def test_copilot_explain_report_evidence(copilot_test_setup):
    """Allow an authorized operator to explain which evidence supports a stored report."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "copilot_analyst@sentinel.ai",
            "password": "mock_hash_123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        rep_id = copilot_test_setup["report"].id
        res = await ac.post(
            "/api/v1/ai/copilot/chat",
            json={"message": f"Explain which evidence supports Report #{rep_id}"},
            headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["tool_calls"]) >= 1
        assert data["tool_calls"][0]["tool_name"] == "explain_report_evidence"
        assert "Evidentiary Foundation" in data["response"]

@pytest.mark.asyncio
async def test_copilot_summarize_linked_observations(copilot_test_setup):
    """Allow an authorized operator to summarize what happened across linked observations."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "copilot_analyst@sentinel.ai",
            "password": "mock_hash_123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        inc_id = copilot_test_setup["incident"].id
        res = await ac.post(
            "/api/v1/ai/copilot/chat",
            json={"message": f"Summarize what happened across linked observations in Incident #{inc_id}"},
            headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["tool_calls"]) >= 1
        assert data["tool_calls"][0]["tool_name"] == "summarize_linked_observations"
        assert "Provenance Graph Synthesis" in data["response"]

@pytest.mark.asyncio
async def test_copilot_consequential_action_requires_confirmation_and_executes(copilot_test_setup, db_session: Session):
    """Require confirmation for consequential actions (escalation), then execute upon confirmation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "copilot_analyst@sentinel.ai",
            "password": "mock_hash_123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        inc_id = copilot_test_setup["incident"].id

        # 1. Propose action without confirmation
        res1 = await ac.post(
            "/api/v1/ai/copilot/chat",
            json={"message": f"Escalate Incident #{inc_id} to Tactical QRT"},
            headers=headers
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["pending_confirmation"] is not None
        assert data1["pending_confirmation"]["action_type"] == "ESCALATE_INCIDENT"
        assert "Confirmation Required" in data1["response"]

        # Verify incident is NOT yet escalated to CRITICAL
        inc_check = db_session.query(Incident).filter(Incident.id == inc_id).first()
        assert inc_check.severity != "CRITICAL"

        # 2. Confirm action
        res2 = await ac.post(
            "/api/v1/ai/copilot/chat",
            json={
                "message": "Yes, confirm escalation",
                "confirmed_action": data1["pending_confirmation"]
            },
            headers=headers
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert "Action Confirmed & Executed" in data2["response"]

        # Verify incident is now escalated
        db_session.refresh(inc_check)
        assert inc_check.severity == "CRITICAL"
        assert inc_check.status == "IN_PROGRESS"

@pytest.mark.asyncio
async def test_copilot_viewer_role_rejected_for_consequential_action(copilot_test_setup):
    """Security check: ensure VIEWER cannot execute consequential actions."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "copilot_viewer@sentinel.ai",
            "password": "mock_hash_viewer"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        inc_id = copilot_test_setup["incident"].id
        res = await ac.post(
            "/api/v1/ai/copilot/chat",
            json={
                "message": "Confirm escalation",
                "confirmed_action": {
                    "action_type": "ESCALATE_INCIDENT",
                    "payload": {
                        "incident_id": inc_id,
                        "escalation_level": "TACTICAL_QRT",
                        "rationale": "Viewer escalation attempt",
                    }
                }
            },
            headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert "Permission Denied" in data["response"]

@pytest.mark.asyncio
async def test_audit_logs_and_settings_endpoints():
    """Verify audit log retrieval and system settings management endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test GET /audit/logs
        logs_res = await ac.get("/api/v1/audit/logs", headers=headers)
        assert logs_res.status_code == 200
        logs = logs_res.json()
        assert isinstance(logs, list)

        # Test GET /audit/settings
        settings_res = await ac.get("/api/v1/audit/settings", headers=headers)
        assert settings_res.status_code == 200
        settings_data = settings_res.json()
        assert "app_name" in settings_data
        assert "gemini_model" in settings_data
        assert settings_data["max_upload_size_mb"] > 0

        # Test POST /audit/settings
        update_res = await ac.post(
            "/api/v1/audit/settings",
            json={"edge_buffer_retention_days": 14},
            headers=headers
        )
        assert update_res.status_code == 200
        assert update_res.json()["edge_buffer_retention_days"] == 14
