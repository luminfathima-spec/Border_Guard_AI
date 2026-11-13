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
from app.models.event_graph import EvidenceObservation, ObservationType
from app.models.verification import VerificationLedgerRecord
from app.schemas.verification import (
    VerificationConfig,
    VerificationVerdict,
    VerificationAction,
)
from app.ai.verification.evaluator import EvidentiarySufficiencyEvaluator
from app.ai.verification.controller import AdaptiveVerificationController
from app.ai.verification.experiment import VerificationComparisonHarness
from app.core.config import settings

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def setup_test_camera_and_incident(db_session: Session):
    """Sets up isolated camera and incident in database."""
    cam = Camera(
        name="Sector 09 Watchtower Sensor",
        camera_identifier=f"CAM-V-{uuid.uuid4().hex[:6].upper()}",
        location="Sector 09 Border Post",
        zone="Sector 09",
        status=CameraStatus.ONLINE.value,
        latitude=34.115,
        longitude=74.825,
    )
    db_session.add(cam)
    db_session.commit()
    db_session.refresh(cam)

    inc = Incident(
        incident_number=f"INC-V-{uuid.uuid4().hex[:8].upper()}",
        title="Verification Controller Incident",
        description="Incident for adaptive controller testing.",
        severity=SeverityLevel.HIGH.value,
        status=IncidentStatus.OPEN.value,
    )
    db_session.add(inc)
    db_session.commit()
    db_session.refresh(inc)

    return cam, inc


def test_demonstrate_case_1_straightforward_event(db_session: Session, setup_test_camera_and_incident):
    """
    CASE 1: STRAIGHTFORWARD EVENT
    High detection confidence (0.95), sustained track (8 frames), camera online, zero conflicts.
    Expected: DIRECT_VERIFY at Step 1, 0 Gemini calls, verified in < 15ms.
    """
    cam, inc = setup_test_camera_and_incident

    ev = SecurityEvent(
        event_type=EventType.RESTRICTED_ZONE_ENTRY.value,
        severity=SeverityLevel.HIGH.value,
        camera_id=cam.id,
        incident_id=inc.id,
        timestamp=datetime.now(timezone.utc),
        description="Person confirmed inside restricted zone",
        confidence=0.95,
        metadata_json={"tracking_id": 101, "confirmed_frames": 8, "dwell_time": 4.5, "bbox": [100, 100, 200, 300]},
    )
    db_session.add(ev)
    db_session.commit()
    db_session.refresh(ev)

    # Attach evidence snapshot
    evidence = Evidence(
        incident_id=inc.id,
        event_id=ev.id,
        evidence_type="SNAPSHOT",
        file_path="demo_videos/demo_border_incursion.mp4",
        checksum_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(evidence)
    db_session.commit()

    res = AdaptiveVerificationController.evaluate_event(db_session, ev.id)

    assert res.verdict == VerificationVerdict.CONFIRMED
    assert res.is_unresolved is False
    assert res.is_conflict is False
    assert res.frames_examined == 1
    assert res.gemini_calls_made == 0
    assert res.estimated_cost_usd == 0.0
    assert len(res.decision_ledger) == 1
    assert res.decision_ledger[0].action == VerificationAction.DIRECT_VERIFY
    assert "verified directly" in res.summary_explanation.lower()


def test_demonstrate_case_2_uncertain_event_with_local_resampling(db_session: Session, setup_test_camera_and_incident):
    """
    CASE 2: UNCERTAIN EVENT
    Marginal confidence (0.62), brief track (1 frame), lighting shadow ambiguity.
    Expected: Triggers REQUEST_LOCAL_FRAMES, samples 5-frame local burst from source video,
    confirms sustained trajectory, resolves without external cloud cost.
    """
    cam, inc = setup_test_camera_and_incident

    ev = SecurityEvent(
        event_type=EventType.RESTRICTED_ZONE_ENTRY.value,
        severity=SeverityLevel.MEDIUM.value,
        camera_id=cam.id,
        incident_id=inc.id,
        timestamp=datetime.now(timezone.utc),
        description="Marginal candidate detected near boundary",
        confidence=0.62,
        metadata_json={"tracking_id": 202, "confirmed_frames": 1, "dwell_time": 0.4, "bbox": [50, 50, 120, 200]},
    )
    db_session.add(ev)
    db_session.commit()
    db_session.refresh(ev)

    res = AdaptiveVerificationController.evaluate_event(db_session, ev.id)

    assert res.verdict == VerificationVerdict.CONFIRMED
    assert res.is_unresolved is False
    assert res.frames_examined == 6  # 1 initial + 5 burst frames
    assert res.gemini_calls_made == 0
    assert res.estimated_cost_usd == 0.0
    actions = [entry.action for entry in res.decision_ledger]
    assert VerificationAction.REQUEST_LOCAL_FRAMES in actions
    assert "adaptive local frame burst" in res.summary_explanation.lower()


def test_demonstrate_case_3_conflicting_evidence_event(db_session: Session, setup_test_camera_and_incident):
    """
    CASE 3: CONFLICTING-EVIDENCE EVENT
    Optical camera records alert, but adjacent sensor logs CONFLICT_RECORD in database.
    Expected: Detects conflict, executes selective Gemini multimodal reasoning, flags as FLAGGED_CONFLICT.
    """
    cam, inc = setup_test_camera_and_incident

    ev = SecurityEvent(
        event_type=EventType.RESTRICTED_ZONE_ENTRY.value,
        severity=SeverityLevel.HIGH.value,
        camera_id=cam.id,
        incident_id=inc.id,
        timestamp=datetime.now(timezone.utc),
        description="Zone breach detected on optical sensor CAM-09",
        confidence=0.88,
        metadata_json={"tracking_id": 303, "confirmed_frames": 4, "dwell_time": 2.0},
    )
    db_session.add(ev)
    db_session.commit()
    db_session.refresh(ev)

    # Insert conflicting observation into event graph table
    conflict_obs = EvidenceObservation(
        incident_id=inc.id,
        observation_type=ObservationType.CONFLICT_RECORD.value,
        provenance_type="DIRECT_OBSERVATION",
        source_system="RADAR-SECTOR-09",
        title="Contradictory Sensor Reading: Radar Sector Clear",
        description="Doppler perimeter radar shows zero moving signatures at coordinates.",
        timestamp=datetime.now(timezone.utc),
        confidence=0.92,
        status="ACTIVE",
    )
    db_session.add(conflict_obs)
    db_session.commit()

    res = AdaptiveVerificationController.evaluate_event(db_session, ev.id, force_mock_gemini=True)

    assert res.verdict == VerificationVerdict.FLAGGED_CONFLICT
    assert res.is_conflict is True
    assert res.gemini_calls_made == 1
    assert res.estimated_cost_usd > 0
    actions = [entry.action for entry in res.decision_ledger]
    assert VerificationAction.REQUEST_GEMINI in actions
    assert "active sensor conflicts" in res.summary_explanation.lower()


def test_demonstrate_case_4_unresolved_event_on_budget_exhaustion(db_session: Session, setup_test_camera_and_incident):
    """
    CASE 4: UNRESOLVED EVENT
    Severely occluded trigger, missing data gap, budget reached.
    Expected: Controller marks UNRESOLVED cleanly rather than forcing an ungrounded conclusion.
    """
    cam, inc = setup_test_camera_and_incident

    ev = SecurityEvent(
        event_type=EventType.RESTRICTED_ZONE_ENTRY.value,
        severity=SeverityLevel.LOW.value,
        camera_id=cam.id,
        incident_id=inc.id,
        timestamp=datetime.now(timezone.utc),
        description="Brief indistinct sensor transient",
        confidence=0.45,
        metadata_json={"tracking_id": 404, "confirmed_frames": 1, "dwell_time": 0.1},
    )
    db_session.add(ev)
    db_session.commit()
    db_session.refresh(ev)

    # Insert data gap notice
    gap_obs = EvidenceObservation(
        incident_id=inc.id,
        observation_type=ObservationType.MISSING_DATA_GAP.value,
        provenance_type="DIRECT_OBSERVATION",
        source_system="RTSP-STREAM-INGEST",
        title="Dropped Frame Interval Notice",
        description="Network transmission dropped 4.2 seconds of video packets.",
        timestamp=datetime.now(timezone.utc),
        confidence=1.0,
        status="ACTIVE",
    )
    db_session.add(gap_obs)
    db_session.commit()

    res = AdaptiveVerificationController.evaluate_event(
        db_session,
        ev.id,
        config=VerificationConfig(max_frame_eval_budget=3, marginal_threshold=0.80),
    )

    assert res.verdict == VerificationVerdict.UNRESOLVED
    assert res.is_unresolved is True
    actions = [entry.action for entry in res.decision_ledger]
    assert VerificationAction.MARK_UNRESOLVED in actions
    assert "unresolved" in res.summary_explanation.lower()


def test_safety_mandate_zero_hostility_classification():
    """
    SAFETY MANDATE AUDIT (Rule 10):
    Asserts that AdaptiveVerificationController never autonomously classifies
    a human subject as 'hostile', 'malicious', or 'enemy combatant'.
    """
    raw_unsafe_text = "Suspect identified as a hostile person with malicious intent and enemy combatant demeanor."
    sanitized = AdaptiveVerificationController.sanitize_safety_mandate(raw_unsafe_text)

    assert "hostile person" not in sanitized.lower()
    assert "malicious intent" not in sanitized.lower()
    assert "enemy combatant" not in sanitized.lower()
    assert "unauthorized person" in sanitized.lower()
    assert "unauthorized boundary crossing" in sanitized.lower()


def test_comparative_benchmark_mode_a_vs_mode_b_and_ablations():
    """
    EXPERIMENTAL COMPARISON & ABLATION HARNESS:
    Verifies that the comparison benchmark executes across Mode A, Mode B,
    and all 3 component ablations, measuring precision, recall, FPR, latency,
    frame counts, API costs, and unresolved rates.
    """
    bench = VerificationComparisonHarness.run_full_comparative_benchmark()

    # Dataset checks
    assert bench["test_dataset_size"] == 40
    assert bench["dev_dataset_size"] == 40

    # Mode A (Baseline) checks
    mode_a = bench["mode_a_baseline_fixed"]
    assert "precision" in mode_a
    assert "recall" in mode_a
    assert "false_positive_rate" in mode_a
    assert "gemini_calls_made" in mode_a
    assert mode_a["gemini_calls_made"] > 15  # Mode A calls LLM on almost every candidate

    # Mode B (Adaptive) checks
    mode_b = bench["mode_b_proposed_adaptive"]
    assert "precision" in mode_b
    assert "recall" in mode_b
    assert "unresolved_rate" in mode_b
    assert mode_b["gemini_calls_made"] < mode_a["gemini_calls_made"]  # Mode B calls LLM selectively!
    assert mode_b["precision"] >= mode_a["precision"]  # Mode B suppresses false alarms

    # Ablation checks
    ablations = bench["ablations"]
    assert "ablation_no_local_resampling" in ablations
    assert "ablation_no_selective_gemini" in ablations
    assert "ablation_no_track_continuity" in ablations

    # Comparative deltas
    deltas = bench["comparative_deltas"]
    assert deltas["gemini_api_call_reduction_pct"] > 50.0
    assert deltas["false_positive_reduction_pct"] > 0.0

    print("\n" + "=" * 65)
    print("PHASE 6 COMPARATIVE BENCHMARK SUMMARY:")
    print(f"  Mode A (Fixed Sampling) Precision : {mode_a['precision']*100:.1f}%")
    print(f"  Mode B (Adaptive) Precision        : {mode_b['precision']*100:.1f}%")
    print(f"  Mode A Gemini API Invocations     : {mode_a['gemini_calls_made']}")
    print(f"  Mode B Gemini API Invocations     : {mode_b['gemini_calls_made']} (-{deltas['gemini_api_call_reduction_pct']}%)")
    print(f"  Mode A False Positives            : {mode_a['false_positives']}")
    print(f"  Mode B False Positives            : {mode_b['false_positives']} (-{deltas['false_positive_reduction_pct']}%)")
    print(f"  Mode B Honest Unresolved Rate     : {deltas['unresolved_rate_mode_b']*100:.1f}%")
    print("=" * 65 + "\n")


@pytest.mark.asyncio
async def test_decision_ledger_persistence_and_api_retrieval(setup_test_camera_and_incident, db_session: Session):
    """
    Tests full API lifecycle:
    1. POST /api/v1/verification/evaluate-event
    2. GET /api/v1/verification/ledgers/{event_id}
    3. POST /api/v1/verification/benchmark
    """
    cam, inc = setup_test_camera_and_incident

    ev = SecurityEvent(
        event_type=EventType.LINE_CROSSING.value,
        severity=SeverityLevel.HIGH.value,
        camera_id=cam.id,
        incident_id=inc.id,
        timestamp=datetime.now(timezone.utc),
        description="Demarcation line crossing event",
        confidence=0.96,
        metadata_json={"tracking_id": 505, "confirmed_frames": 5, "dwell_time": 3.0},
    )
    db_session.add(ev)
    db_session.commit()
    db_session.refresh(ev)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Evaluate event via API
        eval_res = await ac.post(
            "/api/v1/verification/evaluate-event",
            headers=headers,
            json={"event_id": ev.id, "force_mock_gemini": True},
        )
        assert eval_res.status_code == 200, eval_res.text
        eval_data = eval_res.json()
        assert eval_data["verdict"] == "CONFIRMED"
        assert len(eval_data["decision_ledger"]) >= 1

        # 2. Retrieve decision ledger via API
        ledger_res = await ac.get(
            f"/api/v1/verification/ledgers/{ev.id}",
            headers=headers,
        )
        assert ledger_res.status_code == 200
        ledger_items = ledger_res.json()
        assert len(ledger_items) >= 1
        assert ledger_items[0]["verdict"] == "CONFIRMED"
        assert len(ledger_items[0]["ledger"]) >= 1

        # 3. Run benchmark via API
        bench_res = await ac.post(
            "/api/v1/verification/benchmark",
            headers=headers,
            json={"num_episodes": 20},
        )
        assert bench_res.status_code == 200
        bench_data = bench_res.json()
        assert "mode_a_baseline_fixed" in bench_data
        assert "mode_b_proposed_adaptive" in bench_data
