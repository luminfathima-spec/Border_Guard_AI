import pytest
import datetime
from app.db.database import SessionLocal
from app.models.camera import Camera, CameraStatus
from app.models.video import Video, VideoStatus
from app.models.track import ObjectTrack
from app.models.event import SecurityEvent, EventType, SeverityLevel
from app.models.incident import Incident, IncidentStatus
from app.models.evidence import Evidence, EvidenceType
from app.models.ai_analysis import AIAnalysis, AnalysisStatus
from app.models.report import Report, ReportType, ReportStatus
from app.models.audit import AuditLog
from app.models.user import User, UserRole
from app.db.repositories.camera_repo import camera_repository
from app.db.repositories.event_repo import event_repository
from app.db.repositories.track_repo import track_repository


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_camera_and_event_models(db_session):
    cam = Camera(
        name="Test Outpost Alpha",
        camera_identifier=f"CAM-TEST-{datetime.datetime.now().timestamp()}",
        location="Sector 7 North",
        status=CameraStatus.ONLINE.value,
        restricted_zones=[{"name": "Exclusion-1", "points": [[0.1, 0.1], [0.5, 0.5]]}],
        virtual_lines=[{"name": "Tripwire-1", "line": [[0.0, 0.5], [1.0, 0.5]]}],
    )
    db_session.add(cam)
    db_session.commit()
    db_session.refresh(cam)
    assert cam.id is not None

    event = SecurityEvent(
        event_type=EventType.RESTRICTED_ZONE_ENTRY.value,
        severity=SeverityLevel.HIGH.value,
        camera_id=cam.id,
        description="Target breached perimeter exclusion zone",
        confidence=0.94,
        metadata_json={"zone": "Exclusion-1", "target": "person"},
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    assert event.id is not None
    assert event.camera.id == cam.id
    assert event.camera.name == "Test Outpost Alpha"

    # Test repository querying
    recent_events = event_repository.get_by_camera(db_session, cam.id)
    assert len(recent_events) >= 1
    assert recent_events[0].id == event.id


def test_object_track_model_and_repository(db_session):
    video = Video(
        filename="test_patrol_stream.mp4",
        original_filename="test_patrol_stream.mp4",
        path="data/uploads/test_patrol_stream.mp4",
        status=VideoStatus.COMPLETED.value,
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)

    track = ObjectTrack(
        tracking_id=101,
        video_id=video.id,
        object_type="person",
        first_seen_frame=1,
        last_seen_frame=45,
        first_seen_timestamp=0.0,
        last_seen_timestamp=1.5,
        dwell_time_seconds=1.5,
        max_confidence=0.92,
        trajectory_json=[
            {"frame": 1, "bbox": [0.1, 0.2, 0.3, 0.4], "timestamp": 0.0},
            {"frame": 45, "bbox": [0.15, 0.25, 0.35, 0.45], "timestamp": 1.5},
        ],
        is_active=True,
    )
    db_session.add(track)
    db_session.commit()
    db_session.refresh(track)

    assert track.id is not None
    assert track.video.id == video.id
    assert len(track.trajectory_json) == 2

    # Query using repository
    found_track = track_repository.get_by_video_and_tracking_id(db_session, video.id, 101)
    assert found_track is not None
    assert found_track.object_type == "person"


def test_ai_analysis_and_report_models(db_session):
    user = db_session.query(User).first()
    if not user:
        user = User(
            name="Test Investigator",
            email=f"investigator_{datetime.datetime.now().timestamp()}@borderguard.gov",
            password_hash="hashed_pw_test",
            role=UserRole.SECURITY_ANALYST.value,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    inc = Incident(
        incident_number=f"INC-TEST-{int(datetime.datetime.now().timestamp())}",
        title="Unauthorized Border Sector Incursion",
        description="Multiple targets approached the secondary perimeter barrier.",
        severity="CRITICAL",
        status=IncidentStatus.OPEN.value,
    )
    db_session.add(inc)
    db_session.commit()
    db_session.refresh(inc)

    # Add AIAnalysis
    analysis = AIAnalysis(
        incident_id=inc.id,
        model_name="gemini-2.5-flash",
        prompt_type="TACTICAL_SUMMARY",
        raw_prompt="Synthesize the threat vectors for this incursion.",
        analysis_result="Tactical assessment: 2 persons detected moving north at 1.8 m/s.",
        structured_output={"threat_level": "CRITICAL", "suspect_count": 2},
        confidence_score=0.96,
        grounded_citations=["EV-1001", "EV-1002"],
        token_count=420,
        execution_time_ms=850,
        status=AnalysisStatus.SUCCESS.value,
    )
    db_session.add(analysis)

    # Add Report
    report = Report(
        report_number=f"REP-TEST-{int(datetime.datetime.now().timestamp())}",
        title="Executive Forensic Incursion Dossier",
        report_type=ReportType.INCIDENT_DOSSIER.value,
        status=ReportStatus.COMPLETED.value,
        generated_by_user_id=user.id,
        incident_id=inc.id,
        file_path="data/reports/rep_test_001.pdf",
        checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(analysis)
    db_session.refresh(report)

    assert analysis.id is not None
    assert analysis.incident.id == inc.id
    assert report.id is not None
    assert report.generated_by.id == user.id
    assert report.incident.id == inc.id


def test_audit_log_model(db_session):
    user = db_session.query(User).first()
    log = AuditLog(
        user_id=user.id if user else None,
        user_email=user.email if user else "test@borderguard.gov",
        action="UPDATE_ZONE_DEFINITION",
        resource_type="Camera",
        resource_id="1",
        details={"zone": "Sector 4 Exclusion Perimeter"},
        ip_address="127.0.0.1",
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)

    assert log.id is not None
    assert log.action == "UPDATE_ZONE_DEFINITION"
