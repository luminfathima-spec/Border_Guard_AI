from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.event import SecurityEvent
from app.models.camera import Camera
from app.schemas.event import SecurityEventResponse
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("", response_model=List[SecurityEventResponse])
def list_events(
    camera_id: Optional[int] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    incident_id: Optional[int] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all detected security events with filtering by camera, type, and severity."""
    query = db.query(SecurityEvent)
    if camera_id:
        query = query.filter(SecurityEvent.camera_id == camera_id)
    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)
    if severity:
        query = query.filter(SecurityEvent.severity == severity)
    if incident_id:
        query = query.filter(SecurityEvent.incident_id == incident_id)

    events = query.order_by(SecurityEvent.timestamp.desc()).offset(offset).limit(limit).all()

    # Enrich with camera names
    results = []
    for ev in events:
        resp = SecurityEventResponse.model_validate(ev)
        if ev.camera:
            resp.camera_name = ev.camera.name
        results.append(resp)
    return results

@router.get("/{event_id}", response_model=SecurityEventResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve detailed information about a single security event."""
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    resp = SecurityEventResponse.model_validate(event)
    if event.camera:
        resp.camera_name = event.camera.name
    return resp
