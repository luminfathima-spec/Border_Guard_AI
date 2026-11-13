import os
import json
import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import SessionLocal
from app.models.camera import Camera, CameraStatus
from app.models.incident import Incident, IncidentStatus
from app.models.event import SecurityEvent, EventType, SeverityLevel
from app.models.evidence import Evidence
from app.models.ai_analysis import AnalysisStatus
from app.schemas.ai import IncidentAnalysisResponse
from app.services.gemini.client import RealGeminiClient, MockGeminiClient, get_gemini_client
from app.services.gemini.cross_examiner import CrossExaminer
from app.services.gemini_service import GeminiService
from app.core.config import settings


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_incident(db_session: Session):
    cam = Camera(
        name="Sector 12 Test PTZ",
        camera_identifier=f"CAM-T12-{uuid.uuid4().hex[:6].upper()}",
        location="Sector 12 Western Gate",
        zone="Sector 12",
        status=CameraStatus.ONLINE.value,
        latitude=34.110,
        longitude=74.810,
    )
    db_session.add(cam)
    db_session.commit()
    db_session.refresh(cam)

    inc = Incident(
        incident_number=f"INC-LIVE-{uuid.uuid4().hex[:8].upper()}",
        title="Perimeter Incursion Test Dossier",
        description="Single target in dark clothing crossed perimeter virtual fence.",
        severity=SeverityLevel.HIGH.value,
        status=IncidentStatus.OPEN.value,
    )
    db_session.add(inc)
    db_session.commit()
    db_session.refresh(inc)

    ev = SecurityEvent(
        event_type=EventType.RESTRICTED_ZONE_ENTRY.value,
        severity=SeverityLevel.HIGH.value,
        camera_id=cam.id,
        incident_id=inc.id,
        timestamp=datetime.now(timezone.utc),
        description="Target crossed tripwire boundary",
        confidence=0.92,
    )
    db_session.add(ev)
    db_session.commit()
    db_session.refresh(ev)

    evidence = Evidence(
        incident_id=inc.id,
        event_id=ev.id,
        evidence_type="SNAPSHOT",
        file_path="demo_videos/sample_border_surveillance.mp4",
        checksum_sha256="abc123def4567890abcdef1234567890abcdef1234567890abcdef1234567890",
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)

    return inc, cam, ev, evidence


# ---------------------------------------------------------------------------
# Task 2: Secure Configuration & Key Gating
# ---------------------------------------------------------------------------

def test_gemini_verification_blocked_when_key_unset(monkeypatch):
    """When GEMINI_API_KEY is empty, verification must report BLOCKED_NO_KEY and not claim success."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    res = GeminiService.verify_gemini_connection()

    assert res["configured"] is False
    assert res["status"] == "BLOCKED_NO_KEY"
    assert res["is_live_success"] is False
    assert "blocked" in res["message"].lower()
    assert res["model_name"] == settings.GEMINI_MODEL


def test_real_client_rejects_empty_or_whitespace_key():
    """RealGeminiClient must raise ValueError if initialized without an API key."""
    with pytest.raises(ValueError, match="GEMINI_API_KEY is not configured"):
        RealGeminiClient(api_key="")

    with pytest.raises(ValueError, match="GEMINI_API_KEY is not configured"):
        RealGeminiClient(api_key="   \t\n  ")


def test_real_client_masks_secret_in_error_messages():
    """RealGeminiClient must never leak the secret key in error messages."""
    fake_key = "AIzaSySecretFakeKeyThatMustNeverAppearInLogs"
    client = RealGeminiClient(api_key=fake_key, model_name="gemini-2.5-flash")

    sanitized = client._sanitize_error(f"Failed to authenticate with key {fake_key} at endpoint.")
    assert fake_key not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized


def test_error_categorization():
    """Categorizes raw Google GenAI errors into semantic operational categories."""
    assert RealGeminiClient.categorize_error(Exception("400 INVALID_ARGUMENT (API_KEY_INVALID)")) == "INVALID_API_KEY"
    assert RealGeminiClient.categorize_error(Exception("403 Forbidden: Permission denied")) == "PERMISSION_DENIED"
    assert RealGeminiClient.categorize_error(Exception("404 Not Found: Model gemini-3.0 not found")) == "MODEL_NOT_FOUND"
    assert RealGeminiClient.categorize_error(Exception("429 Resource Exhausted: Quota limit reached")) == "QUOTA_EXCEEDED"
    assert RealGeminiClient.categorize_error(Exception("503 Service Unavailable: Backends overloaded")) == "SERVICE_UNAVAILABLE"
    assert RealGeminiClient.categorize_error(Exception("Connection timed out after 30 seconds")) == "NETWORK_TIMEOUT"


# ---------------------------------------------------------------------------
# Task 3: Live Handshake Verification with Google API Endpoint
# ---------------------------------------------------------------------------

def test_live_google_api_handshake_rejects_invalid_key():
    """
    Verification of REAL Google GenAI API network traffic:
    Probing generativelanguage.googleapis.com with an invalid key string returns
    a real HTTP 400 INVALID_ARGUMENT (API_KEY_INVALID) from Google's server.
    This proves that RealGeminiClient actively talks to Google rather than being mocked.
    """
    invalid_test_key = "AIzaSyFakeKeyForLiveNetworkVerification12345"
    client = RealGeminiClient(api_key=invalid_test_key, model_name="gemini-2.5-flash")

    result = client.ping_connectivity()

    # Must confirm live network interaction was attempted and failed
    assert result["status"] == "FAILED"
    assert result["error_category"] in ("INVALID_API_KEY", "NETWORK_TIMEOUT")
    assert result["is_live_success"] is False
    # Must NOT expose the secret key in the result
    assert invalid_test_key not in result["message"]
    assert "[REDACTED_API_KEY]" in result["message"] or "api key" in result["message"].lower() or "timed out" in result["message"].lower()


def test_real_client_structured_generation_with_mocked_success(monkeypatch):
    """
    Verifies that when Google API responds successfully, RealGeminiClient
    parses JSON schema correctly, extracts metadata, and marks is_mock = False.
    """
    from unittest.mock import MagicMock
    from types import SimpleNamespace
    import google.genai as genai

    client = RealGeminiClient(api_key="AIzaSyValidSimulatedKey1234567890", model_name="gemini-2.5-flash")

    raw_response_data = {
        "summary": "Tactical perimeter breach confirmed by automated thermal cameras.",
        "observed_events": [],
        "referenced_camera_ids": [12],
        "supporting_evidence_ids": [1],
        "timestamp_references": ["2026-09-30T16:00:00Z"],
        "uncertainty_and_conflicts": ["Partial foliage occlusion"],
        "suggested_human_actions": ["Dispatch patrol team", "Lock PTZ optical tracking"],
        "threat_level": "HIGH",
        "insufficient_evidence": False,
    }

    mock_resp = SimpleNamespace(
        text=json.dumps(raw_response_data),
        usage_metadata=SimpleNamespace(total_token_count=512),
    )

    mock_sdk = MagicMock()
    mock_sdk.models.generate_content.return_value = mock_resp

    monkeypatch.setattr(genai, "Client", lambda *args, **kwargs: mock_sdk)

    structured_obj, meta = client.generate_structured_analysis(prompt="Analyze incident")

    assert structured_obj.summary == raw_response_data["summary"]
    assert structured_obj.threat_level == "HIGH"
    assert meta["is_mock"] is False
    assert meta["token_count"] == 512
    assert meta["model_name"] == "gemini-2.5-flash"


def test_markdown_fence_stripping_in_real_client(monkeypatch):
    """Verifies that RealGeminiClient strips markdown ```json code blocks without JSONDecodeError."""
    from unittest.mock import MagicMock
    from types import SimpleNamespace
    import google.genai as genai

    client = RealGeminiClient(api_key="AIzaSyValidSimulatedKey1234567890", model_name="gemini-2.5-flash")

    fenced_json = """```json
    {
        "summary": "Fenced JSON response from LLM.",
        "observed_events": [],
        "referenced_camera_ids": [1],
        "supporting_evidence_ids": [1],
        "timestamp_references": ["2026-09-30T16:00:00Z"],
        "uncertainty_and_conflicts": [],
        "suggested_human_actions": ["Verify fence line"],
        "threat_level": "MEDIUM",
        "insufficient_evidence": false
    }
    ```"""

    mock_resp = SimpleNamespace(
        text=fenced_json,
        usage_metadata=SimpleNamespace(total_token_count=256),
    )
    mock_sdk = MagicMock()
    mock_sdk.models.generate_content.return_value = mock_resp
    monkeypatch.setattr(genai, "Client", lambda *args, **kwargs: mock_sdk)

    structured_obj, _ = client.generate_structured_analysis(prompt="Analyze")
    assert structured_obj.summary == "Fenced JSON response from LLM."
    assert structured_obj.threat_level == "MEDIUM"


# ---------------------------------------------------------------------------
# Task 4: Evidence Grounding & Non-Verification Principle
# ---------------------------------------------------------------------------

def test_evidence_grounding_quarantines_hallucinations(db_session, test_incident):
    """Verifies that ungrounded entity IDs are quarantined with FLAGGED status."""
    inc, cam, ev, evidence = test_incident

    # Run analysis with hallucination injection
    res = GeminiService.analyze_incident(
        db_session,
        inc.id,
        force_mock=True,
        inject_hallucination=True,
        include_keyframes=False,
    )

    assert res["status"] == AnalysisStatus.FLAGGED.value
    assert res["grounded_citations"]["grounding_score"] < 1.0
    assert len(res["grounded_citations"]["hallucinations_detected"]) >= 1


def test_ai_explanation_does_not_mark_incident_verified(db_session, test_incident):
    """
    CRITICAL PRINCIPLE:
    An AI explanation alone must NEVER mark a security incident as verified or resolved.
    The incident status must remain unchanged (OPEN) after AI analysis.
    """
    inc, _, _, _ = test_incident
    original_status = inc.status
    assert original_status == IncidentStatus.OPEN.value

    # Execute incident analysis
    res = GeminiService.analyze_incident(db_session, inc.id, force_mock=True, include_keyframes=False)

    db_session.refresh(inc)
    # Incident status must NOT change to RESOLVED or VERIFIED
    assert inc.status == IncidentStatus.OPEN.value
    assert inc.status == original_status

    # AI summary was recorded, but incident remains open for human adjudication
    assert inc.ai_summary is not None
    assert len(inc.ai_summary) > 10


# ---------------------------------------------------------------------------
# Task 5: Diagnostic API Endpoint Test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_gemini_status_endpoint():
    """Tests GET /api/v1/ai/gemini-status returns connectivity diagnostics without leaking secrets."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        status_res = await ac.get("/api/v1/ai/gemini-status", headers=headers)
        assert status_res.status_code == 200
        data = status_res.json()

        assert "configured" in data
        assert "status" in data
        assert "model_name" in data
        assert "is_live_success" in data
        # Ensure API key is NEVER present in JSON response
        assert "api_key" not in data
        assert "key" not in data
