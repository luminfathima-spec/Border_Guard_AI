import os
import pytest
import numpy as np
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.models.track import ObjectTrack
from app.models.detection import Detection
from app.models.event import SecurityEvent
from app.models.evidence import Evidence
from app.ai.detection.yolo_detector import YOLODetector, SURVEILLANCE_CLASSES
from app.ai.tracking.tracker import SurveillanceTracker, TrackedObject
from app.ai.event_detection.zone_analytics import (
    SpatialAnalyticsEngine,
    point_in_polygon,
    line_segments_intersect,
)
from app.ai.evaluation import PipelineEvaluator


@pytest.fixture
def auth_token_and_headers():
    async def _get_token(ac: AsyncClient):
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@sentinel.ai",
            "password": "AdminPassword123!"
        })
        token = login_res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return _get_token


# =====================================================================
# 1. Detection Engine Tests
# =====================================================================

def test_yolo_detector_initialization_and_classes():
    """Verify YOLOv8 detector initializes on CPU and includes standard surveillance classes."""
    detector = YOLODetector(device="cpu")
    assert detector.device == "cpu"
    assert 0 in SURVEILLANCE_CLASSES  # person
    assert 2 in SURVEILLANCE_CLASSES  # car
    assert 7 in SURVEILLANCE_CLASSES  # truck

    # Test blank frame returns clean list
    blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    dets = detector.detect_frame(blank_frame)
    assert isinstance(dets, list)


def test_yolo_resolution_scaling():
    """Verify target_resolution scaling works for CPU optimization."""
    detector = YOLODetector(device="cpu", target_resolution=(320, 240))
    test_frame = np.ones((720, 1280, 3), dtype=np.uint8) * 128
    dets = detector.detect_frame(test_frame)
    assert isinstance(dets, list)


# =====================================================================
# 2. Multi-Frame Tracking Tests
# =====================================================================

def test_tracker_persistence_and_trajectory():
    """Verify tracker associates detections across consecutive frames and records trajectories."""
    tracker = SurveillanceTracker(max_disappeared=5, iou_threshold=0.3)

    # Frame 0: Target at [0.1, 0.1, 0.2, 0.3]
    f0_dets = [{"class_name": "person", "confidence": 0.90, "bbox": [0.1, 0.1, 0.2, 0.3]}]
    res0 = tracker.update(f0_dets, timestamp=0.0, frame_idx=0)
    assert len(res0) == 1
    t_id = res0[0]["tracking_id"]
    assert t_id == 1
    assert res0[0]["dwell_time"] == 0.0

    # Frame 1: Target slightly moved to [0.11, 0.11, 0.21, 0.31]
    f1_dets = [{"class_name": "person", "confidence": 0.92, "bbox": [0.11, 0.11, 0.21, 0.31]}]
    res1 = tracker.update(f1_dets, timestamp=0.1, frame_idx=1)
    assert len(res1) == 1
    assert res1[0]["tracking_id"] == t_id  # Persistent track ID preserved!
    assert res1[0]["dwell_time"] > 0.0

    # Frame 2: Check trajectory length
    assert len(tracker.tracks[t_id].trajectory) == 2
    track_dict = tracker.tracks[t_id].to_dict()
    assert track_dict["tracking_id"] == t_id
    assert track_dict["object_type"] == "person"
    assert track_dict["first_seen_frame"] == 0
    assert track_dict["last_seen_frame"] == 1


def test_tracker_disappearance_and_termination():
    """Verify tracker marks disappeared objects as inactive after grace period."""
    tracker = SurveillanceTracker(max_disappeared=2)
    tracker.update([{"class_name": "car", "confidence": 0.85, "bbox": [0.4, 0.4, 0.6, 0.6]}], timestamp=0.0, frame_idx=0)
    assert 1 in tracker.tracks

    # 3 frames with no detections
    tracker.update([], timestamp=0.1, frame_idx=1)
    tracker.update([], timestamp=0.2, frame_idx=2)
    tracker.update([], timestamp=0.3, frame_idx=3)

    # Track 1 should now be moved to finished_tracks
    assert 1 not in tracker.tracks
    all_tracks = tracker.get_all_tracks()
    assert len(all_tracks) == 1
    assert all_tracks[0].is_active is False


# =====================================================================
# 3. Geometric Spatial Boundary Tests
# =====================================================================

def test_polygon_geometry_ray_casting():
    """Verify point_in_polygon handles normalized coordinates correctly."""
    square_poly = [
        {"x": 0.2, "y": 0.2},
        {"x": 0.8, "y": 0.2},
        {"x": 0.8, "y": 0.8},
        {"x": 0.2, "y": 0.8},
    ]

    # Center is inside
    assert point_in_polygon((0.5, 0.5), square_poly) is True
    # Outside top-left
    assert point_in_polygon((0.1, 0.1), square_poly) is False
    # Outside bottom-right
    assert point_in_polygon((0.9, 0.9), square_poly) is False


def test_tripwire_line_intersection():
    """Verify line_segments_intersect correctly detects tripwire crossing vectors."""
    line_p1 = (0.1, 0.5)
    line_p2 = (0.9, 0.5)

    # Segment crossing vertically
    cross_p1 = (0.5, 0.2)
    cross_p2 = (0.5, 0.8)
    assert line_segments_intersect(cross_p1, cross_p2, line_p1, line_p2) is True

    # Segment parallel and non-intersecting
    no_cross_p1 = (0.5, 0.1)
    no_cross_p2 = (0.5, 0.3)
    assert line_segments_intersect(no_cross_p1, no_cross_p2, line_p1, line_p2) is False


# =====================================================================
# 4. Temporal Confirmation & False Alarm Suppression Tests
# =====================================================================

def test_temporal_confirmation_suppresses_transient_noise():
    """
    Requirement 5 & 6:
    An object appearing inside a restricted zone for only 1 or 2 frames (< confirmation_frames=3)
    must NOT trigger a persistent alarm event (suppressing transient false alarm).
    """
    engine = SpatialAnalyticsEngine(
        restricted_zones=[{
            "id": "zone-alpha",
            "name": "Alpha Zone",
            "polygon": [{"x": 0.2, "y": 0.2}, {"x": 0.8, "y": 0.2}, {"x": 0.8, "y": 0.8}, {"x": 0.2, "y": 0.8}],
            "alert_severity": "HIGH",
        }],
        confirmation_frames=3,
    )

    # Frame 1: Noise detection inside zone (k=1)
    ev1 = engine.analyze_tracked_detection(
        track_id=99,
        object_type="person",
        confidence=0.88,
        bbox=[0.4, 0.4, 0.6, 0.6], # Inside
        timestamp=0.0,
        dwell_time=0.0,
    )
    assert len(ev1) == 0, "Transient noise on frame 1 must be suppressed"

    # Frame 2: Detection still inside zone (k=2)
    ev2 = engine.analyze_tracked_detection(
        track_id=99,
        object_type="person",
        confidence=0.89,
        bbox=[0.4, 0.4, 0.6, 0.6],
        timestamp=0.1,
        dwell_time=0.1,
    )
    assert len(ev2) == 0, "Transient noise on frame 2 must still be suppressed"

    # Frame 3: Target exits before reaching k=3
    ev3 = engine.analyze_tracked_detection(
        track_id=99,
        object_type="person",
        confidence=0.89,
        bbox=[0.05, 0.05, 0.15, 0.15], # Now outside
        timestamp=0.2,
        dwell_time=0.2,
    )
    assert len(ev3) == 0, "Transient noise that exits before confirmation must produce zero events"


def test_temporal_confirmation_confirms_sustained_breach():
    """
    Target remaining in restricted zone for 3 consecutive frames triggers an event ONCE,
    and subsequent frames do NOT duplicate the event (anti-spam).
    """
    engine = SpatialAnalyticsEngine(
        restricted_zones=[{
            "id": "zone-bravo",
            "name": "Bravo Exclusion",
            "polygon": [{"x": 0.2, "y": 0.2}, {"x": 0.8, "y": 0.2}, {"x": 0.8, "y": 0.8}, {"x": 0.2, "y": 0.8}],
            "alert_severity": "HIGH",
        }],
        confirmation_frames=3,
        loiter_threshold_seconds=10.0,
    )

    # Frame 1: k=1
    assert len(engine.analyze_tracked_detection(1, "person", 0.9, [0.4, 0.4, 0.6, 0.6], 0.0, 0.0)) == 0
    # Frame 2: k=2
    assert len(engine.analyze_tracked_detection(1, "person", 0.9, [0.4, 0.4, 0.6, 0.6], 0.1, 0.1)) == 0
    # Frame 3: k=3 -> CONFIRMED!
    ev3 = engine.analyze_tracked_detection(1, "person", 0.9, [0.4, 0.4, 0.6, 0.6], 0.2, 0.2)
    assert len(ev3) == 1
    assert ev3[0]["event_type"] == "RESTRICTED_ZONE_ENTRY"
    assert ev3[0]["metadata"]["confirmed_frames"] == 3

    # Frame 4: Target still in zone -> should NOT re-trigger event
    ev4 = engine.analyze_tracked_detection(1, "person", 0.9, [0.4, 0.4, 0.6, 0.6], 0.3, 0.3)
    assert len(ev4) == 0, "Subsequent frames must not flood duplicate events"


# =====================================================================
# 5. Full Video Pipeline & DB Track Persistence Tests
# =====================================================================

@pytest.mark.asyncio
async def test_full_cv_pipeline_and_track_persistence(auth_token_and_headers):
    """
    Full workflow verification:
    Upload video -> Trigger detection/processing -> Verify ObjectTrack, SecurityEvent, and Evidence stored.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await auth_token_and_headers(ac)

        # 1. Upload sample video
        sample_path = settings.get_absolute_path("data/uploads/sample_border_surveillance.mp4")
        assert os.path.exists(sample_path), "Sample video must exist"

        with open(sample_path, "rb") as f:
            files = {"file": ("phase3_eval_video.mp4", f.read(), "video/mp4")}
            res = await ac.post("/api/v1/videos/upload", files=files, data={"camera_id": 1}, headers=headers)
        assert res.status_code == 201
        video_id = res.json()["video"]["id"]

        # 2. Trigger detection pipeline via /detect endpoint with confirmation_frames=2
        proc_res = await ac.post(
            f"/api/v1/videos/{video_id}/detect",
            json={
                "confidence_threshold": 0.25,
                "process_every_n_frames": 3,
                "temporal_confirmation_frames": 2,
                "enable_tracking": True,
            },
            headers=headers
        )
        assert proc_res.status_code == 200
        proc_data = proc_res.json()
        assert proc_data["status"] == "COMPLETED"
        assert proc_data["total_detections"] > 0
        assert proc_data["tracked_objects"] > 0

        # 3. Query /videos/{video_id}/tracks
        tracks_res = await ac.get(f"/api/v1/videos/{video_id}/tracks", headers=headers)
        assert tracks_res.status_code == 200
        tracks = tracks_res.json()
        assert len(tracks) > 0
        first_track = tracks[0]
        assert "tracking_id" in first_track
        assert "trajectory_json" in first_track
        assert "dwell_time_seconds" in first_track
        assert first_track["max_confidence"] > 0.0

        # 4. Query /videos/{video_id}/events
        events_res = await ac.get(f"/api/v1/videos/{video_id}/events", headers=headers)
        assert events_res.status_code == 200
        events = events_res.json()
        assert isinstance(events, list)

        # 5. Query /detections/summary
        summary_res = await ac.get(f"/api/v1/detections/summary?video_id={video_id}", headers=headers)
        assert summary_res.status_code == 200
        summary = summary_res.json()
        assert summary["total_detections"] > 0
        assert summary["unique_tracks"] > 0

        # 6. Query global /detections/tracks
        global_tracks_res = await ac.get(f"/api/v1/detections/tracks?video_id={video_id}", headers=headers)
        assert global_tracks_res.status_code == 200
        assert len(global_tracks_res.json()) > 0


# =====================================================================
# 6. Quantitative Evaluation Suite Unit Tests
# =====================================================================

def test_evaluation_metrics_precision_recall_fpr():
    """Verify PipelineEvaluator mathematically computes Precision, Recall, and F1."""
    gt = [
        {"class_name": "person", "bbox": [0.1, 0.1, 0.3, 0.3]},
        {"class_name": "car", "bbox": [0.5, 0.5, 0.8, 0.8]},
    ]
    # Perfect match
    preds_perfect = [
        {"class_name": "person", "confidence": 0.95, "bbox": [0.1, 0.1, 0.3, 0.3]},
        {"class_name": "car", "confidence": 0.90, "bbox": [0.5, 0.5, 0.8, 0.8]},
    ]
    perf_metrics = PipelineEvaluator.evaluate_detections(preds_perfect, gt)
    assert perf_metrics["precision"] == 1.0
    assert perf_metrics["recall"] == 1.0
    assert perf_metrics["f1_score"] == 1.0
    assert perf_metrics["tp"] == 2
    assert perf_metrics["fp"] == 0
    assert perf_metrics["fn"] == 0

    # 1 False Positive added
    preds_with_fp = preds_perfect + [{"class_name": "truck", "confidence": 0.8, "bbox": [0.0, 0.0, 0.1, 0.1]}]
    fp_metrics = PipelineEvaluator.evaluate_detections(preds_with_fp, gt)
    assert fp_metrics["precision"] == round(2 / 3, 4)
    assert fp_metrics["recall"] == 1.0
    assert fp_metrics["fp"] == 1


# =====================================================================
# 7. Safety, Neutrality & Ethics Policy Audit
# =====================================================================

@pytest.mark.asyncio
async def test_safety_and_neutrality_policy(auth_token_and_headers):
    """
    SAFETY AUDIT:
    Confirm that computer vision outputs, security events, and AI summaries:
    1. Do not infer hostility, criminality, nationality, or identity from appearance.
    2. Contain only objective physical taxonomy labels ('person', 'vehicle', etc.).
    3. Clearly isolate detection confidence from maliciousness probability.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await auth_token_and_headers(ac)

        events_res = await ac.get("/api/v1/events", headers=headers)
        assert events_res.status_code == 200
        events = events_res.json()

        forbidden_discriminatory_terms = [
            "terrorist", "criminal", "hostile intent", "illegal alien",
            "nationality", "race", "ethnicity", "skin color",
        ]

        for ev in events:
            desc = ev.get("description", "").lower()
            for term in forbidden_discriminatory_terms:
                assert term not in desc, f"Policy violation: Forbidden term '{term}' found in event description: {desc}"

            # Verify confidence is a float between 0 and 1
            assert 0.0 <= ev["confidence"] <= 1.0
