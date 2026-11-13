import math
from typing import List, Dict, Any, Tuple, Optional


def calculate_iou(boxA: List[float], boxB: List[float]) -> float:
    """Calculates Intersection over Union (IoU) between two bounding boxes [x1, y1, x2, y2]."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = max(0.0, boxA[2] - boxA[0]) * max(0.0, boxA[3] - boxA[1])
    boxBArea = max(0.0, boxB[2] - boxB[0]) * max(0.0, boxB[3] - boxB[1])

    unionArea = boxAArea + boxBArea - interArea
    if unionArea <= 0.0:
        return 0.0
    return interArea / unionArea


def calculate_centroid_distance(cA: Tuple[float, float], cB: Tuple[float, float]) -> float:
    """Calculates Euclidean distance between two 2D centroids."""
    return math.hypot(cA[0] - cB[0], cA[1] - cB[1])


class TrackedObject:
    """
    State representation of a single multi-frame tracked surveillance target.
    Maintains persistent track ID, spatial trajectory, dwell time, and temporal confirmation counters.
    """
    def __init__(
        self,
        track_id: int,
        class_name: str,
        bbox: List[float],
        timestamp: float,
        frame_idx: int = 0,
        confidence: float = 0.9,
    ):
        self.track_id = track_id
        self.class_name = class_name
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.centroid = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
        self.first_seen_timestamp = timestamp
        self.last_seen_timestamp = timestamp
        self.first_seen_frame = frame_idx
        self.last_seen_frame = frame_idx
        self.max_confidence = confidence
        self.disappeared_count = 0
        self.is_active = True

        # Complete historical trajectory
        self.trajectory: List[Dict[str, Any]] = [
            {
                "frame": frame_idx,
                "timestamp": round(timestamp, 2),
                "bbox": [round(v, 4) for v in bbox],
                "centroid": [round(self.centroid[0], 4), round(self.centroid[1], 4)],
            }
        ]

        # Spatial zone states for temporal confirmation
        self.zone_entry_counts: Dict[str, int] = {}  # zone_id -> consecutive frames
        self.confirmed_zones: set = set()            # zone_ids with confirmed alert
        self.line_crossed_counts: Dict[str, int] = {} # line_id -> consecutive frames
        self.confirmed_lines: set = set()            # line_ids with confirmed alert
        self.loitering_alerted: bool = False

    def update(
        self,
        bbox: List[float],
        timestamp: float,
        frame_idx: int = 0,
        confidence: float = 0.9,
    ):
        self.bbox = bbox
        self.centroid = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
        self.last_seen_timestamp = timestamp
        self.last_seen_frame = frame_idx
        self.max_confidence = max(self.max_confidence, confidence)
        self.disappeared_count = 0
        self.is_active = True

        self.trajectory.append({
            "frame": frame_idx,
            "timestamp": round(timestamp, 2),
            "bbox": [round(v, 4) for v in bbox],
            "centroid": [round(self.centroid[0], 4), round(self.centroid[1], 4)],
        })
        # Keep maximum 500 trajectory points in memory per track
        if len(self.trajectory) > 500:
            self.trajectory.pop(0)

    @property
    def dwell_time(self) -> float:
        return max(0.0, self.last_seen_timestamp - self.first_seen_timestamp)

    @property
    def velocity_vector(self) -> Tuple[float, float]:
        """Calculates normalized velocity (dx, dy) over the last 5 trajectory points."""
        if len(self.trajectory) < 2:
            return (0.0, 0.0)
        p_old = self.trajectory[max(0, len(self.trajectory) - 5)]["centroid"]
        p_new = self.trajectory[-1]["centroid"]
        return (round(p_new[0] - p_old[0], 4), round(p_new[1] - p_old[1], 4))

    def to_dict(self) -> Dict[str, Any]:
        """Serializes track state for database persistence and API responses."""
        return {
            "tracking_id": self.track_id,
            "object_type": self.class_name,
            "first_seen_frame": self.first_seen_frame,
            "last_seen_frame": self.last_seen_frame,
            "first_seen_timestamp": round(self.first_seen_timestamp, 2),
            "last_seen_timestamp": round(self.last_seen_timestamp, 2),
            "dwell_time_seconds": round(self.dwell_time, 2),
            "max_confidence": round(self.max_confidence, 4),
            "trajectory_json": self.trajectory,
            "is_active": self.is_active,
        }


class SurveillanceTracker:
    """
    Multi-object tracking engine optimized for fixed CCTV & aerial border surveillance.
    Associates frame detections across time using IoU with centroid distance fallbacks,
    preventing ID-switches and handling temporary occlusions.
    """
    def __init__(
        self,
        max_disappeared: int = 15,
        iou_threshold: float = 0.25,
        max_centroid_distance: float = 0.12,
    ):
        self.next_track_id = 1
        self.tracks: Dict[int, TrackedObject] = {}
        self.finished_tracks: List[TrackedObject] = []
        self.max_disappeared = max_disappeared
        self.iou_threshold = iou_threshold
        self.max_centroid_distance = max_centroid_distance

    def update(
        self,
        detections: List[Dict[str, Any]],
        timestamp: float,
        frame_idx: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Updates active tracks with new frame detections.
        Attaches 'tracking_id', 'dwell_time', and 'velocity' to each detection dict.
        """
        if not detections:
            to_delete = []
            for track_id, track in self.tracks.items():
                track.disappeared_count += 1
                if track.disappeared_count > self.max_disappeared:
                    track.is_active = False
                    self.finished_tracks.append(track)
                    to_delete.append(track_id)
            for track_id in to_delete:
                del self.tracks[track_id]
            return detections

        if not self.tracks:
            # Register all initial detections as new tracks
            for det in detections:
                track = TrackedObject(
                    track_id=self.next_track_id,
                    class_name=det["class_name"],
                    bbox=det["bbox"],
                    timestamp=timestamp,
                    frame_idx=frame_idx,
                    confidence=det.get("confidence", 0.9),
                )
                self.tracks[self.next_track_id] = track
                det["tracking_id"] = self.next_track_id
                det["dwell_time"] = 0.0
                det["velocity"] = (0.0, 0.0)
                self.next_track_id += 1
            return detections

        track_ids = list(self.tracks.keys())
        matched_tracks = set()
        matched_dets = set()

        # Step 1: Greedy IoU matching for same-class objects
        for d_idx, det in enumerate(detections):
            best_iou = 0.0
            best_t_idx = -1

            for t_idx, tid in enumerate(track_ids):
                if t_idx in matched_tracks:
                    continue
                if self.tracks[tid].class_name != det["class_name"]:
                    continue

                iou = calculate_iou(self.tracks[tid].bbox, det["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_t_idx = t_idx

            if best_iou >= self.iou_threshold and best_t_idx >= 0:
                matched_tracks.add(best_t_idx)
                matched_dets.add(d_idx)
                tid = track_ids[best_t_idx]
                self.tracks[tid].update(
                    bbox=det["bbox"],
                    timestamp=timestamp,
                    frame_idx=frame_idx,
                    confidence=det.get("confidence", 0.9),
                )
                det["tracking_id"] = tid
                det["dwell_time"] = self.tracks[tid].dwell_time
                det["velocity"] = self.tracks[tid].velocity_vector

        # Step 2: Centroid distance fallback for remaining unmatched detections
        for d_idx, det in enumerate(detections):
            if d_idx in matched_dets:
                continue

            det_centroid = (
                (det["bbox"][0] + det["bbox"][2]) / 2.0,
                (det["bbox"][1] + det["bbox"][3]) / 2.0,
            )
            best_dist = 999.0
            best_t_idx = -1

            for t_idx, tid in enumerate(track_ids):
                if t_idx in matched_tracks:
                    continue
                if self.tracks[tid].class_name != det["class_name"]:
                    continue

                dist = calculate_centroid_distance(self.tracks[tid].centroid, det_centroid)
                if dist < best_dist:
                    best_dist = dist
                    best_t_idx = t_idx

            if best_dist <= self.max_centroid_distance and best_t_idx >= 0:
                matched_tracks.add(best_t_idx)
                matched_dets.add(d_idx)
                tid = track_ids[best_t_idx]
                self.tracks[tid].update(
                    bbox=det["bbox"],
                    timestamp=timestamp,
                    frame_idx=frame_idx,
                    confidence=det.get("confidence", 0.9),
                )
                det["tracking_id"] = tid
                det["dwell_time"] = self.tracks[tid].dwell_time
                det["velocity"] = self.tracks[tid].velocity_vector

        # Step 3: Register remaining unmatched detections as new tracks
        for d_idx, det in enumerate(detections):
            if d_idx not in matched_dets:
                track = TrackedObject(
                    track_id=self.next_track_id,
                    class_name=det["class_name"],
                    bbox=det["bbox"],
                    timestamp=timestamp,
                    frame_idx=frame_idx,
                    confidence=det.get("confidence", 0.9),
                )
                self.tracks[self.next_track_id] = track
                det["tracking_id"] = self.next_track_id
                det["dwell_time"] = 0.0
                det["velocity"] = (0.0, 0.0)
                self.next_track_id += 1

        # Step 4: Increment disappeared counter for unmatched active tracks
        to_delete = []
        for t_idx, tid in enumerate(track_ids):
            if t_idx not in matched_tracks:
                self.tracks[tid].disappeared_count += 1
                if self.tracks[tid].disappeared_count > self.max_disappeared:
                    self.tracks[tid].is_active = False
                    self.finished_tracks.append(self.tracks[tid])
                    to_delete.append(tid)

        for tid in to_delete:
            del self.tracks[tid]

        return detections

    def get_all_tracks(self) -> List[TrackedObject]:
        """Returns all tracked objects observed throughout the video processing lifecycle."""
        return list(self.tracks.values()) + self.finished_tracks
