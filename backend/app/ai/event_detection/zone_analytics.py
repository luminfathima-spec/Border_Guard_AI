import math
from typing import List, Dict, Any, Tuple, Optional
from app.core.config import settings

def normalize_poly_point(p: Dict[str, float], width: float = 1.0, height: float = 1.0) -> Tuple[float, float]:
    px = float(p.get("x", 0))
    py = float(p.get("y", 0))
    # If 0-100 percentage
    if px > 1.0 and px <= 100.0 and width == 1.0:
        px = px / 100.0
    elif px > 100.0 and width > 1.0:
        px = px / width
    if py > 1.0 and py <= 100.0 and height == 1.0:
        py = py / 100.0
    elif py > 100.0 and height > 1.0:
        py = py / height
    return (px, py)

def point_in_polygon(point: Tuple[float, float], polygon: List[Dict[str, float]], width: float = 1.0, height: float = 1.0) -> bool:
    """
    Ray-casting algorithm to test if a 2D point (x, y) lies inside a polygon.
    Automatically handles normalized (0.0-1.0), percentage (0-100), or pixel coordinates.
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
    """
    Checks if line segment (p1 -> p2) intersects with segment (q1 -> q2).
    """
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    return (ccw(p1, q1, q2) != ccw(p2, q1, q2)) and (ccw(p1, p2, q1) != ccw(p1, p2, q2))

class SpatialAnalyticsEngine:
    def __init__(
        self,
        restricted_zones: Optional[List[Dict[str, Any]]] = None,
        virtual_lines: Optional[List[Dict[str, Any]]] = None,
        frame_width: int = 1280,
        frame_height: int = 720,
    ):
        self.restricted_zones = restricted_zones or []
        self.virtual_lines = virtual_lines or []
        self.frame_width = frame_width
        self.frame_height = frame_height
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
        Analyzes a single tracked object against configured restricted zones and tripwires.
        Returns generated events if breach or loitering rules are satisfied.
        """
        events = []
        centroid_px = ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)
        norm_centroid = (centroid_px[0] / self.frame_width, centroid_px[1] / self.frame_height)

        if track_id not in self.track_states:
            self.track_states[track_id] = {
                "last_pos": norm_centroid,
                "in_zones": set(),
                "crossed_lines": set(),
                "loitering_alerted": False,
            }

        state = self.track_states[track_id]
        prev_pos = state["last_pos"]

        # 1. Restricted Polygonal Zone Analysis
        for zone in self.restricted_zones:
            zone_id = str(zone.get("id", "default-zone"))
            zone_name = zone.get("name", "Restricted Buffer Strip")
            polygon = zone.get("polygon", [])
            severity = zone.get("alert_severity", "HIGH")

            is_inside = point_in_polygon(norm_centroid, polygon, width=1.0, height=1.0)

            if is_inside and zone_id not in state["in_zones"]:
                # Transition: Entered restricted zone
                state["in_zones"].add(zone_id)
                events.append({
                    "event_type": "RESTRICTED_ZONE_ENTRY",
                    "severity": severity,
                    "confidence": confidence,
                    "description": f"{object_type.capitalize()} (Track ID #{track_id}) breached restricted zone '{zone_name}'",
                    "metadata": {
                        "tracking_id": track_id,
                        "object_type": object_type,
                        "zone_id": zone_id,
                        "zone_name": zone_name,
                        "centroid": [round(centroid_px[0], 1), round(centroid_px[1], 1)],
                        "timestamp": timestamp,
                    }
                })
            elif not is_inside and zone_id in state["in_zones"]:
                state["in_zones"].remove(zone_id)

        # 2. Virtual Line Crossing (Tripwire) Analysis
        for line in self.virtual_lines:
            line_id = str(line.get("id", "default-line"))
            line_name = line.get("name", "Perimeter Demarcation Line")
            lp1 = normalize_poly_point(line.get("p1", {"x": 10, "y": 50}))
            lp2 = normalize_poly_point(line.get("p2", {"x": 90, "y": 50}))
            severity = line.get("alert_severity", "CRITICAL")

            # Check if trajectory vector crossed the line
            if prev_pos != norm_centroid:
                if line_segments_intersect(prev_pos, norm_centroid, lp1, lp2):
                    if line_id not in state["crossed_lines"]:
                        state["crossed_lines"].add(line_id)
                        events.append({
                            "event_type": "LINE_CROSSING",
                            "severity": severity,
                            "confidence": confidence,
                            "description": f"{object_type.capitalize()} (Track ID #{track_id}) crossed virtual line '{line_name}'",
                            "metadata": {
                                "tracking_id": track_id,
                                "object_type": object_type,
                                "line_id": line_id,
                                "line_name": line_name,
                                "prev_pos": [round(prev_pos[0], 3), round(prev_pos[1], 3)],
                                "current_pos": [round(norm_centroid[0], 3), round(norm_centroid[1], 3)],
                                "timestamp": timestamp,
                            }
                        })

        # Update previous position
        state["last_pos"] = norm_centroid
        return events
