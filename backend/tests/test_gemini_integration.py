import os
import json
import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import get_db, SessionLocal
from app.models.camera import Camera, CameraStatus
from app.models.incident import Incident, IncidentStatus
from app.models.event import SecurityEvent, EventType, SeverityLevel
from app.models.evidence import Evidence
from app.models.ai_analysis import AIAnalysis, AnalysisStatus
from app.models.event_graph import EventLink
from app.schemas.ai import IncidentAnalysisResponse, ObservedEventItem
from app.services.gemini.prompts import PROMPT_VERSION, build_incident_prompt, sanitize_telemetry
from app.services.gemini.client import MockGeminiClient, RealGeminiClient, get_gemini_client
from app.services.gemini.cross_examiner import CrossExaminer
from app.services.gemini.frame_selector import EventTriggeredFrameSelector
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
def sample_incident_with_evidence(db_session: Session):
    """Creates a realistic test incident with camera, events, and evidence in DB."""
    cam_ident = f"CAM-TEST-{uuid.uuid4().hex[:6].upper()}"
    cam = Camera(
        name="Sector 08 Test Tower",
        camera_identifier=cam_ident,
        location="Perimeter Grid 08",
        zone="Sector 08",
        status=CameraStatus.ONLINE.value,
        latitude=34.120,
        longitude=74.830,
    )
    db_session.add(cam)
    db_session.commit()
    db_session.refresh(cam)

    inc = Incident(
        incident_number=f"INC-GEM-{uuid.uuid4().hex[:8].upper()}",
        title="Automated Test Breach - Sector 08",
        description="Unauthorized individual traversed perimeter demarcation line.",
        severity=SeverityLevel.HIGH.value,
        status=IncidentStatus.OPEN.value,
    )
    db_session.add(inc)
    db_session.commit()
    db_session.refresh(inc)

    # Add security event
    ev = SecurityEvent(
        event_type=EventType.RESTRICTED_ZONE_ENTRY.value,
        severity=SeverityLevel.HIGH.value,
        camera_id=cam.id,
        incident_id=inc.id,
        timestamp=datetime.now(timezone.utc),
        description="Intrusion confirmed by CV tracking engine",
        confidence=0.94,
    )
    db_session.add(ev)
    db_session.commit()
    db_session.refresh(ev)

    # Add evidence item
    evidence = Evidence(
        incident_id=inc.id,
        event_id=ev.id,
        evidence_type="SNAPSHOT",
        file_path="demo_videos/demo_border_incursion.mp4",
        checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)

    return inc, cam, ev, evidence


def test_gemini_client_mock_mode_structured_generation():
    """Verifies that MockGeminiClient produces a fully schema-compliant IncidentAnalysisResponse."""
    client = MockGeminiClient()
    prompt = """
```json
{
  "incident_number": "INC-TEST-001",
  "severity": "CRITICAL",
  "camera_id": 1,
  "events": [
    {
      "id": 101,
      "type": "RESTRICTED_ZONE_ENTRY",
      "timestamp": "2026-08-30T04:33:12Z",
      "confidence": 0.98,
      "description": "Target crossed demarcation line into buffer zone."
    }
  ],
  "evidence_items": [
    {"id": 201, "evidence_type": "SNAPSHOT"}
  ]
}
```
"""
    response, meta = client.generate_structured_analysis(prompt)

    assert isinstance(response, IncidentAnalysisResponse)
    assert response.threat_level == "CRITICAL"
    assert response.referenced_camera_ids == [1]
    assert response.supporting_evidence_ids == [201]
    assert len(response.observed_events) == 1
    assert response.observed_events[0].event_type == "RESTRICTED_ZONE_ENTRY"
    assert len(response.suggested_human_actions) >= 3
    assert response.insufficient_evidence is False
    assert meta["is_mock"] is True
    assert meta["execution_time_ms"] > 0


def test_schema_validation_of_gemini_responses():
    """Asserts strict Pydantic validation on valid, missing, and malformed fields."""
    valid_payload = {
        "summary": "Tactical summary of perimeter breach.",
        "observed_events": [
            {
                "event_id": 1,
                "event_type": "LINE_CROSSING",
                "timestamp": "2026-08-30T04:33:00Z",
                "confidence": 0.95,
                "description": "Tripwire crossing observed.",
            }
        ],
        "referenced_camera_ids": [1],
        "supporting_evidence_ids": [10],
        "timestamp_references": ["2026-08-30T04:33:00Z"],
        "uncertainty_and_conflicts": ["Low ambient light"],
        "suggested_human_actions": ["Dispatch QRT", "Inspect perimeter"],
        "threat_level": "HIGH",
        "insufficient_evidence": False,
    }

    validated = IncidentAnalysisResponse.model_validate(valid_payload)
    assert validated.summary == "Tactical summary of perimeter breach."
    assert validated.threat_level == "HIGH"

    # Missing mandatory summary field must raise ValidationError
    invalid_payload = valid_payload.copy()
    del invalid_payload["summary"]
    with pytest.raises(Exception):
        IncidentAnalysisResponse.model_validate(invalid_payload)


def test_cross_examiner_detects_hallucinated_camera_and_evidence_ids(db_session, sample_incident_with_evidence):
    """
    EVIDENCE SAFEGUARD TEST:
    Injects hallucinated Camera ID (99999) and Evidence ID (88888) into model output.
    Verifies that CrossExaminer detects hallucinations, strips them from verified citations,
    flags status as FLAGGED, and calculates grounding score.
    """
    inc, cam, ev, evidence = sample_incident_with_evidence

    # Mock response containing real IDs + hallucinated IDs
    analysis = IncidentAnalysisResponse(
        summary="Model generated summary claiming breach observed.",
        observed_events=[
            ObservedEventItem(
                event_id=ev.id,
                event_type="RESTRICTED_ZONE_ENTRY",
                timestamp="2026-08-30T04:33:00Z",
                confidence=0.95,
                description="Verified breach",
            )
        ],
        referenced_camera_ids=[cam.id, 99999],  # 99999 does not exist in DB
        supporting_evidence_ids=[evidence.id, 88888],  # 88888 does not exist in DB
        timestamp_references=["2026-08-30T04:33:00Z"],
        uncertainty_and_conflicts=[],
        suggested_human_actions=["Dispatch QRT"],
        threat_level="HIGH",
        insufficient_evidence=False,
    )

    audit, status = CrossExaminer.verify(db_session, analysis, inc.id)

    # Assertions on evidence safeguards
    assert status == AnalysisStatus.FLAGGED.value
    assert 99999 in audit.ungrounded_cameras
    assert 88888 in audit.ungrounded_evidence
    assert cam.id in audit.verified_cameras
    assert evidence.id in audit.verified_evidence
    assert len(audit.hallucinations_detected) == 2
    assert audit.grounding_score < 1.0

    # Assert that ungrounded IDs were stripped from verified object
    assert analysis.referenced_camera_ids == [cam.id]
    assert analysis.supporting_evidence_ids == [evidence.id]
    assert "CROSS-EXAMINER GROUNDING SAFEGUARD WARNING" in analysis.summary


def test_insufficient_evidence_handling(db_session):
    """Verifies that an incident with empty telemetry triggers insufficient_evidence=True."""
    inc = Incident(
        incident_number=f"INC-EMPTY-{uuid.uuid4().hex[:8].upper()}",
        title="Empty Inconclusive Incident",
        description="Trigger with no associated events or detections.",
        severity=SeverityLevel.LOW.value,
        status=IncidentStatus.OPEN.value,
    )
    db_session.add(inc)
    db_session.commit()
    db_session.refresh(inc)

    res = GeminiService.analyze_incident(db_session, inc.id, force_mock=True, include_keyframes=False)

    assert res["structured_output"]["insufficient_evidence"] is True
    assert res["structured_output"]["threat_level"] == "LOW"
    assert "insufficient" in res["analysis_result"].lower() or "insufficient" in res["structured_output"]["summary"].lower()


def test_bounded_retry_and_backoff_on_transient_failure(monkeypatch):
    """
    Verifies that RealGeminiClient executes bounded exponential backoff retries
    when encountering transient HTTP 429 / resource exhausted errors.
    """
    from unittest.mock import MagicMock
    from types import SimpleNamespace
    import google.genai as genai

    real_client = RealGeminiClient(api_key="AIzaSyFakeTestKeyForRetryTest123", model_name="gemini-2.5-flash")

    # Mock response object
    valid_json_text = json.dumps({
        "summary": "Verified breach following retry.",
        "observed_events": [],
        "referenced_camera_ids": [1],
        "supporting_evidence_ids": [1],
        "timestamp_references": ["2026-08-30T04:33:00Z"],
        "uncertainty_and_conflicts": [],
        "suggested_human_actions": ["Dispatch QRT"],
        "threat_level": "HIGH",
        "insufficient_evidence": False,
    })
    mock_resp = SimpleNamespace(
        text=valid_json_text,
        usage_metadata=SimpleNamespace(total_token_count=320),
    )

    attempt_counter = {"calls": 0}

    def mock_generate_content(*args, **kwargs):
        attempt_counter["calls"] += 1
        if attempt_counter["calls"] < 3:
            # Simulate 429 rate limit error
            raise RuntimeError("429 Resource Exhausted: Rate limit exceeded on quota")
        return mock_resp

    mock_sdk_client = MagicMock()
    mock_sdk_client.models.generate_content = mock_generate_content

    # Patch genai.Client
    monkeypatch.setattr(genai, "Client", lambda *args, **kwargs: mock_sdk_client)
    # Patch time.sleep to run instantaneously
    monkeypatch.setattr("time.sleep", lambda s: None)

    response, meta = real_client.generate_structured_analysis(
        prompt="Test prompt",
        images=None,
    )

    assert attempt_counter["calls"] == 3
    assert response.summary == "Verified breach following retry."
    assert meta["token_count"] == 320
    assert meta["is_mock"] is False


def test_persistence_with_prompt_version_and_citations(db_session, sample_incident_with_evidence):
    """
    Verifies that AIAnalysis record is persisted to DB with:
    - prompt_version = "2026.04.1"
    - model_name
    - execution_time_ms
    - token_count
    - grounded_citations
    - EventLink created in event graph
    """
    inc, cam, ev, evidence = sample_incident_with_evidence

    res = GeminiService.analyze_incident(db_session, inc.id, force_mock=True, include_keyframes=False)

    assert res["prompt_version"] == PROMPT_VERSION
    assert res["execution_time_ms"] > 0
    assert res["token_count"] > 0
    assert res["status"] in [AnalysisStatus.SUCCESS.value, AnalysisStatus.FLAGGED.value]

    # Verify database persistence
    ai_record = db_session.query(AIAnalysis).filter(AIAnalysis.id == res["id"]).first()
    assert ai_record is not None
    assert ai_record.prompt_version == PROMPT_VERSION
    assert ai_record.incident_id == inc.id
    assert isinstance(ai_record.grounded_citations, dict)

    # Verify Provenance Event Graph edge
    edge = (
        db_session.query(EventLink)
        .filter(
            EventLink.source_node_type == "AI_ANALYSIS",
            EventLink.source_node_id == ai_record.id,
            EventLink.target_node_id == inc.id,
        )
        .first()
    )
    assert edge is not None
    assert edge.relationship_type == "ANALYZED_BY"
    assert edge.provenance_type == "DERIVED_SYNTHESIS"


@pytest.mark.asyncio
async def test_api_analyze_and_history_endpoints(sample_incident_with_evidence):
    """Tests POST /api/v1/ai/incidents/{id}/analyze and GET /api/v1/ai/incidents/{id}/analyses."""
    inc, _, _, _ = sample_incident_with_evidence

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Trigger structured analysis
        res = await ac.post(
            f"/api/v1/ai/incidents/{inc.id}/analyze",
            headers=headers,
            json={"custom_instructions": "Check for secondary breach trajectory.", "force_mock": True},
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["incident_id"] == inc.id
        assert data["prompt_version"] == PROMPT_VERSION
        assert "structured_output" in data
        assert "grounded_citations" in data

        # 2. Query analyses history
        hist_res = await ac.get(
            f"/api/v1/ai/incidents/{inc.id}/analyses",
            headers=headers,
        )
        assert hist_res.status_code == 200
        hist = hist_res.json()
        assert len(hist) >= 1
        assert hist[0]["prompt_version"] == PROMPT_VERSION


def test_real_or_mock_integration_end_to_end_with_video(db_session, sample_incident_with_evidence):
    """
    EVALUATION TEST:
    Executes end-to-end integration and reports explicitly whether real API or mock was used.
    """
    inc, cam, ev, evidence = sample_incident_with_evidence

    # Run analysis without forcing mock (will use real API if GEMINI_API_KEY is valid, or mock otherwise)
    res = GeminiService.analyze_incident(
        db_session,
        inc.id,
        custom_instructions="Evaluate target speed and QRT interception vector.",
        include_keyframes=True,
    )

    is_mock_used = res["is_mock"]
    model_name = res["model_name"]
    exec_time = res["execution_time_ms"]
    tokens = res["token_count"]
    grounding = res["confidence_score"]

    print("\n" + "=" * 65)
    print("PHASE 5 EVALUATION RESULT:")
    print(f"  Provider Used   : {'MOCK PROVIDER' if is_mock_used else 'LIVE GOOGLE GEMINI API'}")
    print(f"  Model Name      : {model_name}")
    print(f"  Prompt Version  : {res['prompt_version']}")
    print(f"  Execution Time  : {exec_time} ms")
    print(f"  Total Tokens    : {tokens}")
    print(f"  Grounding Score : {grounding * 100:.1f}%")
    print(f"  Status          : {res['status']}")
    print("=" * 65 + "\n")

    assert res["id"] > 0
    assert len(res["analysis_result"]) > 20
    assert "suggested_human_actions" in res["structured_output"]
    assert len(res["structured_output"]["suggested_human_actions"]) >= 3
