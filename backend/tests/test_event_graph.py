import datetime
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import SessionLocal
from app.models.camera import Camera
from app.models.video import Video
from app.models.detection import Detection
from app.models.track import ObjectTrack
from app.models.event import SecurityEvent, EventType, SeverityLevel
from app.models.incident import Incident
from app.models.evidence import Evidence, EvidenceType
from app.models.ai_analysis import AIAnalysis
from app.models.report import Report
from app.models.event_graph import EventLink, EvidenceObservation, RelationshipType, ProvenanceType, ObservationType


@pytest.fixture
def auth_token_and_test_data():
    """Helper to populate realistic multi-tier surveillance data in DB."""
    db = SessionLocal()
    uid = uuid.uuid4().hex[:6]

    cam = Camera(
        name=f"Border Outpost Alpha {uid}",
        camera_identifier=f"CAM-EG-{uid.upper()}",
        location="Sector 7 Ridge",
        stream_url=f"rtsp://admin:secret@192.168.1.{uid[:2]}:554/live",
        status="ONLINE",
    )
    db.add(cam)
    db.flush()

    t0 = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=10)

    vid = Video(
        filename=f"patrol_breach_{uid}.mp4",
        original_filename=f"patrol_breach_{uid}.mp4",
        path=f"data/uploads/patrol_breach_{uid}.mp4",
        camera_id=cam.id,
        duration=45.0,
        fps=30.0,
        resolution="1920x1080",
        checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        source_timestamp=t0,
        status="PROCESSED",
    )
    db.add(vid)
    db.flush()

    det = Detection(
        video_id=vid.id,
        camera_id=cam.id,
        timestamp_offset=12.5,
        frame_number=375,
        object_type="human",
        confidence=0.92,
        bbox_x1=0.2,
        bbox_y1=0.3,
        bbox_x2=0.3,
        bbox_y2=0.7,
        tracking_id=101,
        created_at=t0 + datetime.timedelta(seconds=12),
    )
    db.add(det)
    db.flush()

    trk = ObjectTrack(
        tracking_id=101,
        video_id=vid.id,
        camera_id=cam.id,
        object_type="human",
        first_seen_frame=350,
        last_seen_frame=450,
        first_seen_timestamp=11.6,
        last_seen_timestamp=15.0,
        dwell_time_seconds=3.4,
        max_confidence=0.94,
        trajectory_json=[{"frame": 375, "bbox": [0.2, 0.3, 0.3, 0.7]}],
        created_at=t0 + datetime.timedelta(seconds=11),
    )
    db.add(trk)
    db.flush()

    inc = Incident(
        incident_number=f"INC-{uid.upper()}",
        title="Unauthorized Perimeter Crossing Event",
        description="Target detected traversing North sector virtual buffer zone",
        severity="HIGH",
        status="OPEN",
        created_at=t0 + datetime.timedelta(seconds=15),
    )
    db.add(inc)
    db.flush()

    ev = SecurityEvent(
        event_type=EventType.RESTRICTED_ZONE_ENTRY.value,
        severity=SeverityLevel.HIGH.value,
        camera_id=cam.id,
        video_id=vid.id,
        incident_id=inc.id,
        timestamp=t0 + datetime.timedelta(seconds=12),
        description="Target sustained within restricted buffer polygon for 4 consecutive frames",
        confidence=0.95,
        metadata_json={"tracking_id": 101, "zone": "Buffer-Alpha"},
        snapshot_path=f"data/snapshots/snap_{uid}.jpg",
    )
    db.add(ev)
    db.flush()

    evi = Evidence(
        incident_id=inc.id,
        event_id=ev.id,
        evidence_type=EvidenceType.SNAPSHOT.value,
        file_path=f"data/snapshots/snap_{uid}.jpg",
        file_size_bytes=145200,
        checksum_sha256="4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
        timestamp=t0 + datetime.timedelta(seconds=12),
    )
    db.add(evi)
    db.flush()

    ana = AIAnalysis(
        incident_id=inc.id,
        event_id=ev.id,
        model_name="gemini-2.5-flash",
        prompt_type="TACTICAL_SUMMARY",
        raw_prompt="Analyze perimeter breach",
        analysis_result="Single adult subject traversed northern boundary with sustained movement towards interior.",
        structured_output={"threat_level": "ELEVATED", "subjects": 1},
        confidence_score=0.96,
        created_at=t0 + datetime.timedelta(seconds=20),
    )
    db.add(ana)
    db.flush()

    rep = Report(
        report_number=f"REP-{uid.upper()}",
        title=f"Tactical Incident Report {inc.incident_number}",
        report_type="INCIDENT_DOSSIER",
        status="COMPLETED",
        incident_id=inc.id,
        file_path=f"data/reports/rep_{uid}.pdf",
        checksum_sha256="7d865e959b2466918c9863afca942d0fb89d7c9ac0c99bafc3749504ded97730",
        created_at=t0 + datetime.timedelta(seconds=25),
    )
    db.add(rep)
    db.commit()

    data = {
        "camera_id": cam.id,
        "video_id": vid.id,
        "detection_id": det.id,
        "track_id": trk.id,
        "incident_id": inc.id,
        "event_id": ev.id,
        "evidence_id": evi.id,
        "analysis_id": ana.id,
        "report_id": rep.id,
    }
    db.close()
    return data


@pytest.mark.asyncio
async def test_create_typed_relationship_with_validation(auth_token_and_test_data):
    """Test creating explicit typed links with provenance and validation."""
    data = auth_token_and_test_data
    inc_id = data["incident_id"]
    ev_id = data["event_id"]
    cam_id = data["camera_id"]
    vid_id = data["video_id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create OBSERVED_BY link
        link_payload = {
            "source_node_type": "EVENT",
            "source_node_id": ev_id,
            "target_node_type": "CAMERA",
            "target_node_id": cam_id,
            "relationship_type": "OBSERVED_BY",
            "provenance_type": "DIRECT_OBSERVATION",
            "creation_reason": "Physical event optical sensor capture",
            "confidence": 1.0,
        }
        res = await ac.post(f"/api/v1/incidents/{inc_id}/graph/links", json=link_payload, headers=headers)
        assert res.status_code == 201
        res_data = res.json()
        assert res_data["relationship_type"] == "OBSERVED_BY"
        assert res_data["provenance_type"] == "DIRECT_OBSERVATION"
        assert res_data["creation_reason"] == "Physical event optical sensor capture"

        # 2. Create EXTRACTED_FROM link
        link_payload2 = {
            "source_node_type": "EVENT",
            "source_node_id": ev_id,
            "target_node_type": "VIDEO",
            "target_node_id": vid_id,
            "relationship_type": "EXTRACTED_FROM",
            "provenance_type": "DIRECT_OBSERVATION",
            "creation_reason": "Telemetry extracted from validated MP4 byte stream",
            "confidence": 1.0,
        }
        res2 = await ac.post(f"/api/v1/incidents/{inc_id}/graph/links", json=link_payload2, headers=headers)
        assert res2.status_code == 201


@pytest.mark.asyncio
async def test_prevent_dangling_reference_to_nonexistent_evidence(auth_token_and_test_data):
    """Test that attempting to link to a deleted or nonexistent entity is blocked with 404."""
    data = auth_token_and_test_data
    inc_id = data["incident_id"]
    ev_id = data["event_id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Nonexistent target (Camera 999999)
        bad_payload = {
            "source_node_type": "EVENT",
            "source_node_id": ev_id,
            "target_node_type": "CAMERA",
            "target_node_id": 999999,
            "relationship_type": "OBSERVED_BY",
            "provenance_type": "DIRECT_OBSERVATION",
            "creation_reason": "Testing dangling reference prevention",
        }
        res = await ac.post(f"/api/v1/incidents/{inc_id}/graph/links", json=bad_payload, headers=headers)
        assert res.status_code == 404
        assert "Dangling references are prohibited" in res.json()["detail"]

        # Nonexistent source (Detection 888888)
        bad_payload_src = {
            "source_node_type": "DETECTION",
            "source_node_id": 888888,
            "target_node_type": "EVENT",
            "target_node_id": ev_id,
            "relationship_type": "TRIGGERED",
            "provenance_type": "DIRECT_OBSERVATION",
            "creation_reason": "Testing dangling source prevention",
        }
        res_src = await ac.post(f"/api/v1/incidents/{inc_id}/graph/links", json=bad_payload_src, headers=headers)
        assert res_src.status_code == 404
        assert "Dangling references are prohibited" in res_src.json()["detail"]


@pytest.mark.asyncio
async def test_distinguish_direct_observation_vs_inferred_association(auth_token_and_test_data):
    """Test explicit separation between raw physical observations and algorithmic/AI inferences."""
    data = auth_token_and_test_data
    inc_id = data["incident_id"]
    ev_id = data["event_id"]
    trk_id = data["track_id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Track -> Event is an INFERRED_ASSOCIATION
        res = await ac.post(
            f"/api/v1/incidents/{inc_id}/graph/links",
            json={
                "source_node_type": "OBJECT_TRACK",
                "source_node_id": trk_id,
                "target_node_type": "EVENT",
                "target_node_id": ev_id,
                "relationship_type": "TRIGGERED",
                "provenance_type": "INFERRED_ASSOCIATION",
                "creation_reason": "Multi-frame tracking trajectory inferred to be person crossing virtual line",
                "confidence": 0.89,
            },
            headers=headers,
        )
        assert res.status_code == 201
        assert res.json()["provenance_type"] == "INFERRED_ASSOCIATION"

        # Check graph counts
        graph_res = await ac.get(f"/api/v1/incidents/{inc_id}/graph", headers=headers)
        assert graph_res.status_code == 200
        g = graph_res.json()
        assert g["inferred_count"] >= 1


@pytest.mark.asyncio
async def test_conflicting_observations_and_missing_evidence(auth_token_and_test_data):
    """Test recording conflicting sensor reports and missing-data evidence gaps."""
    data = auth_token_and_test_data
    inc_id = data["incident_id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Record Conflicting Observation
        conflict_payload = {
            "observation_type": "CONFLICT_RECORD",
            "provenance_type": "DIRECT_OBSERVATION",
            "title": "Ground Radar Contradiction",
            "description": "Sector Ground Radar reported zero radar reflection at coordinates (32.41, 74.88) during visual alarm timestamp",
            "source_system": "RADAR_STATION_B",
            "confidence": 0.95,
            "details_json": {"disputed_feature": "target_presence", "radar_rcs_db": -45.0},
        }
        res_conf = await ac.post(f"/api/v1/incidents/{inc_id}/observations", json=conflict_payload, headers=headers)
        assert res_conf.status_code == 201
        assert res_conf.json()["observation_type"] == "CONFLICT_RECORD"

        # 2. Record Missing Data Gap
        gap_payload = {
            "observation_type": "MISSING_DATA_GAP",
            "provenance_type": "DIRECT_OBSERVATION",
            "title": "RTSP Packet Drop (Frame Gap 410-480)",
            "description": "WAN link jitter caused dropped frames between timestamp 13.6s and 16.0s",
            "source_system": "CCTV_STREAM_MONITOR",
            "confidence": 1.0,
            "details_json": {"start_frame": 410, "end_frame": 480, "duration_lost_ms": 2333},
        }
        res_gap = await ac.post(f"/api/v1/incidents/{inc_id}/observations", json=gap_payload, headers=headers)
        assert res_gap.status_code == 201

        # Check graph retrieval detects conflict and missing evidence
        graph_res = await ac.get(f"/api/v1/incidents/{inc_id}/graph", headers=headers)
        assert graph_res.status_code == 200
        g = graph_res.json()
        assert g["conflicts_count"] >= 1
        assert g["missing_evidence_count"] >= 1


@pytest.mark.asyncio
async def test_preserve_history_supersede_without_silent_overwrite(auth_token_and_test_data):
    """Test that modifying an observation preserves history and marks old as SUPERSEDED."""
    data = auth_token_and_test_data
    inc_id = data["incident_id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Initial observation
        init_res = await ac.post(
            f"/api/v1/incidents/{inc_id}/observations",
            json={
                "observation_type": "DIRECT_FACT",
                "provenance_type": "ANALYST_ASSERTION",
                "title": "Initial Target Assessment",
                "description": "Analyst logged suspect carrying unrecognized metallic device",
                "source_system": "SOC_ANALYST_CONSOLE",
                "confidence": 0.70,
            },
            headers=headers,
        )
        assert init_res.status_code == 201
        old_id = init_res.json()["id"]

        # 2. Supersede with higher resolution inspection
        supersede_payload = {
            "observation_type": "DIRECT_FACT",
            "provenance_type": "ANALYST_ASSERTION",
            "title": "Corrected Target Assessment",
            "description": "Subsequent zoom review confirmed metallic device is authorized irrigation pipe segment",
            "source_system": "SOC_SENIOR_ANALYST",
            "confidence": 0.98,
            "details_json": {"original_observation_id": old_id},
        }
        sup_res = await ac.post(
            f"/api/v1/incidents/{inc_id}/observations/{old_id}/supersede?reason=Re-evaluated%20under%204K%20digital%20zoom",
            json=supersede_payload,
            headers=headers,
        )
        assert sup_res.status_code == 201
        new_obs = sup_res.json()
        assert new_obs["status"] == "ACTIVE"
        assert new_obs["id"] != old_id

        # Verify old observation in DB still exists with SUPERSEDED status
        db = SessionLocal()
        old_record = db.query(EvidenceObservation).filter(EvidenceObservation.id == old_id).first()
        assert old_record is not None
        assert old_record.status == "SUPERSEDED"
        assert old_record.superseded_by_id == new_obs["id"]

        # Verify SUPERSEDES edge in graph
        sup_edge = (
            db.query(EventLink)
            .filter(
                EventLink.source_node_id == new_obs["id"],
                EventLink.target_node_id == old_id,
                EventLink.relationship_type == RelationshipType.SUPERSEDES.value,
            )
            .first()
        )
        assert sup_edge is not None
        db.close()


@pytest.mark.asyncio
async def test_detect_duplicate_links(auth_token_and_test_data):
    """Test duplicate link detection and rejection."""
    data = auth_token_and_test_data
    inc_id = data["incident_id"]
    ev_id = data["event_id"]
    vid_id = data["video_id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "source_node_type": "EVENT",
            "source_node_id": ev_id,
            "target_node_type": "VIDEO",
            "target_node_id": vid_id,
            "relationship_type": "EXTRACTED_FROM",
            "provenance_type": "DIRECT_OBSERVATION",
            "creation_reason": "Original video link",
        }
        # First creation succeeds
        res1 = await ac.post(f"/api/v1/incidents/{inc_id}/graph/links", json=payload, headers=headers)
        assert res1.status_code == 201

        # Duplicate attempt MUST fail with 400
        res2 = await ac.post(f"/api/v1/incidents/{inc_id}/graph/links", json=payload, headers=headers)
        assert res2.status_code == 400
        assert "Duplicate relationship" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_detect_out_of_order_timestamps(auth_token_and_test_data):
    """Test detection of anachronistic causal links where target precedes source."""
    data = auth_token_and_test_data
    inc_id = data["incident_id"]
    ev_id = data["event_id"]
    cam_id = data["camera_id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        now = datetime.datetime.now(datetime.timezone.utc)
        earlier = now - datetime.timedelta(hours=2)

        # Inject out of order edge
        inv_payload = {
            "source_node_type": "EVENT",
            "source_node_id": ev_id,
            "target_node_type": "CAMERA",
            "target_node_id": cam_id,
            "relationship_type": "TRIGGERED",
            "provenance_type": "INFERRED_ASSOCIATION",
            "creation_reason": "Simulated anachronistic edge",
            "source_timestamp": now.isoformat(),
            "target_timestamp": earlier.isoformat(),
        }
        res = await ac.post(f"/api/v1/incidents/{inc_id}/graph/links", json=inv_payload, headers=headers)
        assert res.status_code == 201

        # Run validation
        val_res = await ac.post(f"/api/v1/incidents/{inc_id}/graph/validate", headers=headers)
        assert val_res.status_code == 200
        v = val_res.json()
        assert len(v["out_of_order_timestamps"]) >= 1


@pytest.mark.asyncio
async def test_retrieve_incident_evidence_chain_and_verify_real_stored_records(auth_token_and_test_data):
    """
    VERIFICATION REQUIREMENT:
    Retrieve the complete evidence graph and verify that each evidence reference resolves
    to a real stored record in PostgreSQL.
    """
    data = auth_token_and_test_data
    inc_id = data["incident_id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Auto-synthesize graph first to build full chain
        auto_res = await ac.post(f"/api/v1/incidents/{inc_id}/graph/auto-synthesize", headers=headers)
        assert auto_res.status_code == 200

        # Retrieve evidence chain
        chain_res = await ac.get(f"/api/v1/incidents/{inc_id}/evidence-chain", headers=headers)
        assert chain_res.status_code == 200
        chain_data = chain_res.json()

        assert chain_data["is_chain_intact"] is True
        chain = chain_data["chain"]
        assert len(chain) >= 5

        # Programmatically verify that EVERY reference in the chain resolves to a real DB record
        db = SessionLocal()
        for step in chain:
            ntype = step["node_type"]
            nid = step["node_id"]
            assert step["is_verified_in_db"] is True

            if ntype == "CAMERA":
                record = db.query(Camera).filter(Camera.id == nid).first()
                assert record is not None, f"Dangling reference to Camera #{nid}"
            elif ntype == "VIDEO":
                record = db.query(Video).filter(Video.id == nid).first()
                assert record is not None, f"Dangling reference to Video #{nid}"
                assert step["evidence_sha256"] is not None
            elif ntype == "OBJECT_TRACK":
                record = db.query(ObjectTrack).filter(ObjectTrack.id == nid).first()
                assert record is not None, f"Dangling reference to Track #{nid}"
            elif ntype == "EVENT":
                record = db.query(SecurityEvent).filter(SecurityEvent.id == nid).first()
                assert record is not None, f"Dangling reference to Event #{nid}"
            elif ntype == "EVIDENCE":
                record = db.query(Evidence).filter(Evidence.id == nid).first()
                assert record is not None, f"Dangling reference to Evidence #{nid}"
                assert record.checksum_sha256 is not None
            elif ntype == "AI_ANALYSIS":
                record = db.query(AIAnalysis).filter(AIAnalysis.id == nid).first()
                assert record is not None, f"Dangling reference to AIAnalysis #{nid}"
            elif ntype == "REPORT":
                record = db.query(Report).filter(Report.id == nid).first()
                assert record is not None, f"Dangling reference to Report #{nid}"
                assert record.checksum_sha256 is not None
            elif ntype == "INCIDENT":
                record = db.query(Incident).filter(Incident.id == nid).first()
                assert record is not None, f"Dangling reference to Incident #{nid}"

        db.close()


@pytest.mark.asyncio
async def test_graph_cycle_detection(auth_token_and_test_data):
    """Test cycle detection in directed event graph."""
    data = auth_token_and_test_data
    inc_id = data["incident_id"]
    ev_id = data["event_id"]
    cam_id = data["camera_id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create cycle: Event -> Camera, Camera -> Event
        await ac.post(
            f"/api/v1/incidents/{inc_id}/graph/links",
            json={
                "source_node_type": "EVENT",
                "source_node_id": ev_id,
                "target_node_type": "CAMERA",
                "target_node_id": cam_id,
                "relationship_type": "OBSERVED_BY",
                "provenance_type": "DIRECT_OBSERVATION",
                "creation_reason": "Forward edge",
            },
            headers=headers,
        )
        await ac.post(
            f"/api/v1/incidents/{inc_id}/graph/links",
            json={
                "source_node_type": "CAMERA",
                "source_node_id": cam_id,
                "target_node_type": "EVENT",
                "target_node_id": ev_id,
                "relationship_type": "CORROBORATES",
                "provenance_type": "DIRECT_OBSERVATION",
                "creation_reason": "Cycle return edge",
            },
            headers=headers,
        )

        val_res = await ac.post(f"/api/v1/incidents/{inc_id}/graph/validate", headers=headers)
        assert val_res.status_code == 200
        val = val_res.json()
        assert len(val["cycles_detected"]) >= 1
        assert val["is_valid"] is False
