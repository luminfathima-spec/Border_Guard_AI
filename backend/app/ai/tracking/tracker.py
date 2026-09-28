import math
from typing import List, Dict, Any, Tuple

def calculate_iou(boxA: List[float], boxB: List[float]) -> float:
    """Calculates Intersection over Union (IoU) between two bounding boxes [x1, y1, x2, y2]."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    unionArea = boxAArea + boxBArea - interArea
    if unionArea <= 0.0:
        return 0.0
    return interArea / unionArea

class TrackedObject:
    def __init__(self, track_id: int, class_name: str, bbox: List[float], timestamp: float):
        self.track_id = track_id
        self.class_name = class_name
        self.bbox = bbox # [x1, y1, x2, y2]
        self.centroid = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
        self.first_seen_timestamp = timestamp
        self.last_seen_timestamp = timestamp
        self.history: List[Tuple[float, Tuple[float, float]]] = [(timestamp, self.centroid)] # (t, (cx, cy))
        self.disappeared_count = 0

    def update(self, bbox: List[float], timestamp: float):
        self.bbox = bbox
        self.centroid = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
        self.last_seen_timestamp = timestamp
        self.history.append((timestamp, self.centroid))
        if len(self.history) > 100:
            self.history.pop(0)
        self.disappeared_count = 0

    @property
    def dwell_time(self) -> float:
        return max(0.0, self.last_seen_timestamp - self.first_seen_timestamp)

    @property
    def trajectory_vector(self) -> Tuple[float, float]:
        """Calculates displacement vector (dx, dy) over the last N history points."""
        if len(self.history) < 2:
            return (0.0, 0.0)
        oldest = self.history[0][1]
        latest = self.history[-1][1]
        return (latest[0] - oldest[0], latest[1] - oldest[1])

class SurveillanceTracker:
    def __init__(self, max_disappeared: int = 10, iou_threshold: float = 0.3):
        self.next_track_id = 1
        self.tracks: Dict[int, TrackedObject] = {}
        self.max_disappeared = max_disappeared
        self.iou_threshold = iou_threshold

    def update(self, detections: List[Dict[str, Any]], timestamp: float) -> List[Dict[str, Any]]:
        """
        Updates active tracks with new frame detections.
        Attaches 'tracking_id' and 'dwell_time' to each detection dict in place.
        """
        if not detections:
            # Mark all active tracks as disappeared
            to_delete = []
            for track_id, track in self.tracks.items():
                track.disappeared_count += 1
                if track.disappeared_count > self.max_disappeared:
                    to_delete.append(track_id)
            for track_id in to_delete:
                del self.tracks[track_id]
            return detections

        if not self.tracks:
            # Register all current detections as new tracks
            for det in detections:
                track = TrackedObject(self.next_track_id, det["class_name"], det["bbox"], timestamp)
                self.tracks[self.next_track_id] = track
                det["tracking_id"] = self.next_track_id
                det["dwell_time"] = 0.0
                self.next_track_id += 1
            return detections

        # Match existing tracks to detections using IoU matrix
        track_ids = list(self.tracks.keys())
        track_boxes = [self.tracks[tid].bbox for tid in track_ids]

        matched_tracks = set()
        matched_dets = set()

        # Compute IoU between each track and each detection
        for d_idx, det in enumerate(detections):
            best_iou = 0.0
            best_t_idx = -1

            for t_idx, t_box in enumerate(track_boxes):
                if t_idx in matched_tracks:
                    continue
                # Also check class compatibility
                if self.tracks[track_ids[t_idx]].class_name != det["class_name"]:
                    continue

                iou = calculate_iou(t_box, det["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_t_idx = t_idx

            if best_iou >= self.iou_threshold and best_t_idx >= 0:
                matched_tracks.add(best_t_idx)
                matched_dets.add(d_idx)
                tid = track_ids[best_t_idx]
                self.tracks[tid].update(det["bbox"], timestamp)
                det["tracking_id"] = tid
                det["dwell_time"] = self.tracks[tid].dwell_time

        # For unmatched detections, register new tracks
        for d_idx, det in enumerate(detections):
            if d_idx not in matched_dets:
                track = TrackedObject(self.next_track_id, det["class_name"], det["bbox"], timestamp)
                self.tracks[self.next_track_id] = track
                det["tracking_id"] = self.next_track_id
                det["dwell_time"] = 0.0
                self.next_track_id += 1

        # For unmatched tracks, increment disappeared count
        to_delete = []
        for t_idx, tid in enumerate(track_ids):
            if t_idx not in matched_tracks:
                self.tracks[tid].disappeared_count += 1
                if self.tracks[tid].disappeared_count > self.max_disappeared:
                    to_delete.append(tid)

        for tid in to_delete:
            del self.tracks[tid]

        return detections
