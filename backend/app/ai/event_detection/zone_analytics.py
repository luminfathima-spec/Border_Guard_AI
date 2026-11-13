import math
from typing import List, Dict, Any, Tuple, Optional


def normalize_poly_point(
    p: Dict[str, float],
    width: float = 1.0,
    height: float = 1.0,
) -> Tuple[float, float]:
    """Normalizes coordinate point dict {'x': ..., 'y': ...} to 0.0 - 1.0 range."""
    px = float(p.get("x", 0))
    py = float(p.get("y", 0))

    if px > 1.0 and px <= 100.0 and width == 1.0:
        px = px / 100.0
    elif px > 100.0 and width > 1.0:
        px = px / width

    if py > 1.0 and py <= 100.0 and height == 1.0:
        py = py / 100.0
    elif py > 100.0 and height > 1.0:
        py = py / height

    return (max(0.0, min(1.0, px)), max(0.0, min(1.0, py)))


def point_in_polygon(
    point: Tuple[float, float],
    polygon: List[Dict[str, float]],
    width: float = 1.0,
    height: float = 1.0,
) -> bool:
    """
    Ray-casting algorithm to test if a 2D point (x, y) lies inside an arbitrary polygon.
    Supports convex and concave polygons across normalized [0.0-1.0], percentage [0-100], or pixel coordinates.
    """
    x, y = point
    if width > 1.0 and x > 1.0:
        x = x / width
    elif x > 1.0 and x <= 100.0:
        x = x / 100.0

    if height > 1.0 and y > 1.0:
        y = y / height
    elif y > 1.0 and y <= 100.0:
        y = y / 100.0

    norm_poly = [normalize_poly_point(p, width, height) for p in polygon]
    num_vertices = len(norm_poly)
    if num_vertices < 3:
        return False

    inside = False
    p1x, p1y = norm_poly[0]

    for i in range(1, num_vertices + 1):
        p2x, p2y = norm_poly[i % num_vertices]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def line_segments_intersect(
    p1: Tuple[float, float], p2: Tuple[float, float],
    q1: Tuple[float, float], q2: Tuple[float, float]
) -> bool:
    """Checks if line segment (p1 -> p2) intersects with tripwire segment (q1 -> q2)."""
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    return (ccw(p1, q1, q2) != ccw(p2, q1, q2)) and (ccw(p1, p2, q1) != ccw(p1, p2, q2))


def get_side_of_line(line_p1: Tuple[float, float], line_p2: Tuple[float, float], pt: Tuple[float, float]) -> float:
    """
    Returns signed distance/cross product to determine which side of directed line (p1->p2) a point lies on.
    > 0: Left side, < 0: Right side, == 0: Collinear.
    """
    return (line_p2[0] - line_p1[0]) * (pt[1] - line_p1[1]) - (line_p2[1] - line_p1[1]) * (pt[0] - line_p1[0])


class SpatialAnalyticsEngine:
    """
    Spatial & Temporal Boundary Analytics Engine.
    Evaluates tracked object trajectories against:
    1. Polygonal Restricted Zones (with ray-casting & temporal confirmation).
    2. Demarcation Tripwires (with directional line crossing analysis).
    3. Loitering Thresholds.

    TEMPORAL CONFIRMATION:
    To suppress transient sensor noise and false alarms, an object must remain inside
    a restricted zone for at least `confirmation_frames` consecutive evaluated frames
    before an alert event is generated.
    """
    def __init__(
        self,
        restricted_zones: Optional[List[Dict[str, Any]]] = None,
        virtual_lines: Optional[List[Dict[str, Any]]] = None,
        frame_width: int = 1280,
        frame_height: int = 720,
        confirmation_frames: int = 3,
        loiter_threshold_seconds: float = 10.0,
    ):
        self.restricted_zones = restricted_zones or []
        self.virtual_lines = virtual_lines or []
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.confirmation_frames = max(1, confirmation_frames)
        self.loiter_threshold_seconds = loiter_threshold_seconds

        # Track-specific state cache
        # {track_id: {
        #    'last_pos': (x, y),
        #    'consecutive_inside': {zone_id: int},
        #    'confirmed_zones': set(zone_id),
        #    'crossed_lines': set(line_id),
        #    'loitering_alerted': bool
        # }}
        self.track_states: Dict[int, Dict[str, Any]] = {}

    def analyze_tracked_detection(
        self,
        track_id: int,
        object_type: str,
        confidence: float,
        bbox: List[float],
        timestamp: float,
        dwell_time: float,
    ) -> List[Dict[str, Any]]:
        """
        Evaluates a tracked target against configured zones and tripwires.
        Returns a list of confirmed security events (if geometric and temporal conditions are met).
        """
        events = []
        # Calculate centroid in normalized coordinates
        if bbox[0] > 1.0 or bbox[2] > 1.0:
            # Pixel bounding box [x1, y1, x2, y2]
            cx = (bbox[0] + bbox[2]) / (2.0 * self.frame_width)
            cy = (bbox[1] + bbox[3]) / (2.0 * self.frame_height)
            centroid_px = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
        else:
            # Normalized bounding box [x1, y1, x2, y2]
            cx = (bbox[0] + bbox[2]) / 2.0
            cy = (bbox[1] + bbox[3]) / 2.0
            centroid_px = (cx * self.frame_width, cy * self.frame_height)

        norm_centroid = (max(0.0, min(1.0, cx)), max(0.0, min(1.0, cy)))

        if track_id not in self.track_states:
            self.track_states[track_id] = {
                "last_pos": norm_centroid,
                "consecutive_inside": {},
                "confirmed_zones": set(),
                "crossed_lines": set(),
                "loitering_alerted": False,
            }

        state = self.track_states[track_id]
        prev_pos = state["last_pos"]

        # -------------------------------------------------------------
        # 1. Restricted Polygonal Zone Analysis with Temporal Confirmation
        # -------------------------------------------------------------
        for zone in self.restricted_zones:
            zone_id = str(zone.get("id", "default-zone"))
            zone_name = zone.get("name", "Restricted Buffer Strip")
            polygon = zone.get("polygon", [])
            severity = zone.get("alert_severity", "HIGH")

            if len(polygon) < 3:
                continue

            is_inside = point_in_polygon(norm_centroid, polygon, width=1.0, height=1.0)

            if is_inside:
                count = state["consecutive_inside"].get(zone_id, 0) + 1
                state["consecutive_inside"][zone_id] = count

                # Check temporal confirmation
                if count >= self.confirmation_frames and zone_id not in state["confirmed_zones"]:
                    state["confirmed_zones"].add(zone_id)
                    events.append({
                        "event_type": "RESTRICTED_ZONE_ENTRY",
                        "severity": severity,
                        "confidence": confidence,
                        "description": f"{object_type.capitalize()} (Track ID #{track_id}) confirmed inside restricted zone '{zone_name}' after {count} consecutive frames",
                        "metadata": {
                            "tracking_id": track_id,
                            "object_type": object_type,
                            "zone_id": zone_id,
                            "zone_name": zone_name,
                            "centroid": [round(centroid_px[0], 1), round(centroid_px[1], 1)],
                            "dwell_time": round(dwell_time, 2),
                            "timestamp": round(timestamp, 2),
                            "confirmed_frames": count,
                        },
                    })

                # Check loitering within confirmed zone
                if (
                    zone_id in state["confirmed_zones"]
                    and dwell_time >= self.loiter_threshold_seconds
                    and not state["loitering_alerted"]
                ):
                    state["loitering_alerted"] = True
                    events.append({
                        "event_type": "LOITERING",
                        "severity": "HIGH",
                        "confidence": confidence,
                        "description": f"{object_type.capitalize()} (Track ID #{track_id}) loitering in '{zone_name}' for {round(dwell_time, 1)} seconds",
                        "metadata": {
                            "tracking_id": track_id,
                            "object_type": object_type,
                            "zone_id": zone_id,
                            "zone_name": zone_name,
                            "dwell_time": round(dwell_time, 2),
                            "timestamp": round(timestamp, 2),
                        },
                    })

            else:
                # Target is outside zone; reset temporal counter
                if zone_id in state["consecutive_inside"]:
                    del state["consecutive_inside"][zone_id]
                state["confirmed_zones"].discard(zone_id)

        # -------------------------------------------------------------
        # 2. Virtual Line Crossing (Tripwire) Analysis
        # -------------------------------------------------------------
        for line in self.virtual_lines:
            line_id = str(line.get("id", "default-line"))
            line_name = line.get("name", "Perimeter Demarcation Line")
            lp1 = normalize_poly_point(line.get("p1", {"x": 10, "y": 50}))
            lp2 = normalize_poly_point(line.get("p2", {"x": 90, "y": 50}))
            direction = line.get("direction", "BOTH")
            severity = line.get("alert_severity", "CRITICAL")

            # Check if trajectory vector crossed the line segment
            if prev_pos != norm_centroid:
                if line_segments_intersect(prev_pos, norm_centroid, lp1, lp2):
                    # Directional verification
                    side_prev = get_side_of_line(lp1, lp2, prev_pos)
                    side_curr = get_side_of_line(lp1, lp2, norm_centroid)

                    direction_valid = True
                    if direction == "A_TO_B" and not (side_prev > 0 and side_curr < 0):
                        direction_valid = False
                    elif direction == "B_TO_A" and not (side_prev < 0 and side_curr > 0):
                        direction_valid = False

                    if direction_valid and line_id not in state["crossed_lines"]:
                        state["crossed_lines"].add(line_id)
                        events.append({
                            "event_type": "LINE_CROSSING",
                            "severity": severity,
                            "confidence": confidence,
                            "description": f"{object_type.capitalize()} (Track ID #{track_id}) crossed demarcation line '{line_name}'",
                            "metadata": {
                                "tracking_id": track_id,
                                "object_type": object_type,
                                "line_id": line_id,
                                "line_name": line_name,
                                "direction": direction,
                                "prev_pos": [round(prev_pos[0], 3), round(prev_pos[1], 3)],
                                "current_pos": [round(norm_centroid[0], 3), round(norm_centroid[1], 3)],
                                "timestamp": round(timestamp, 2),
                            },
                        })

        state["last_pos"] = norm_centroid
        return events
