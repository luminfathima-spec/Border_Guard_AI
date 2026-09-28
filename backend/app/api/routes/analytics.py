import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.models.camera import Camera, CameraStatus
from app.models.event import SecurityEvent
from app.models.alert import Alert, AlertStatus
from app.models.incident import Incident, IncidentStatus
from app.schemas.analytics import AnalyticsOverview, TimelineItem
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview", response_model=AnalyticsOverview)
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Computes real-time SOC metrics: Camera uptime, daily event tallies, alert distribution, and activity timelines.
    """
    total_cameras = db.query(Camera).count()
    active_cameras = db.query(Camera).filter(Camera.status == CameraStatus.ONLINE.value).count()

    today_start = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    total_events_today = db.query(SecurityEvent).filter(SecurityEvent.timestamp >= today_start).count()
    if total_events_today == 0:
        total_events_today = db.query(SecurityEvent).count()

    active_alerts = db.query(Alert).filter(Alert.status.in_([AlertStatus.NEW.value, AlertStatus.INVESTIGATING.value])).count()
    critical_incidents = db.query(Incident).filter(Incident.status.in_([IncidentStatus.OPEN.value, IncidentStatus.IN_PROGRESS.value])).count()

    # Events by type
    event_type_counts = db.query(SecurityEvent.event_type, func.count(SecurityEvent.id)).group_by(SecurityEvent.event_type).all()
    events_by_type = {t: count for t, count in event_type_counts}

    # Events by severity
    severity_counts = db.query(SecurityEvent.severity, func.count(SecurityEvent.id)).group_by(SecurityEvent.severity).all()
    events_by_severity = {s: count for s, count in severity_counts}

    # Camera health breakdown
    cam_status_counts = db.query(Camera.status, func.count(Camera.id)).group_by(Camera.status).all()
    camera_health_summary = {st: count for st, count in cam_status_counts}

    # Recent activity timeline
    recent_events = db.query(SecurityEvent).order_by(SecurityEvent.timestamp.desc()).limit(10).all()
    timeline = []
    for ev in reversed(recent_events):
        timeline.append(TimelineItem(
            timestamp=ev.timestamp.strftime("%H:%M:%S"),
            count=1,
            severity=ev.severity,
        ))

    return AnalyticsOverview(
        total_cameras=total_cameras,
        active_cameras=active_cameras,
        total_events_today=total_events_today,
        active_alerts=active_alerts,
        critical_incidents=critical_incidents,
        events_by_type=events_by_type,
        events_by_severity=events_by_severity,
        camera_health_summary=camera_health_summary,
        recent_activity_timeline=timeline,
    )
