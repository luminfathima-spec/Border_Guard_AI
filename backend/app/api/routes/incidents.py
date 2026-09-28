from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.incident import Incident
from app.models.event import SecurityEvent
from app.models.alert import Alert
from app.models.evidence import Evidence
from app.models.audit import AuditLog
from app.schemas.incident import IncidentResponse, IncidentCreate, IncidentUpdate
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List grouped security incidents and investigations."""
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)

    incidents = query.order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()
    results = []
    for inc in incidents:
        resp = IncidentResponse.model_validate(inc)
        resp.events_count = len(inc.events)
        resp.alerts_count = len(inc.alerts)
        resp.evidence_count = len(inc.evidence_items)
        results.append(resp)
    return results

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve detailed investigation record for an incident."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    resp = IncidentResponse.model_validate(inc)
    resp.events_count = len(inc.events)
    resp.alerts_count = len(inc.alerts)
    resp.evidence_count = len(inc.evidence_items)
    return resp

@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: int,
    inc_in: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update incident status, severity, analyst notes, or AI summary."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    if inc_in.title is not None:
        inc.title = inc_in.title
    if inc_in.description is not None:
        inc.description = inc_in.description
    if inc_in.severity is not None:
        inc.severity = inc_in.severity
    if inc_in.status is not None:
        inc.status = inc_in.status.value
    if inc_in.analyst_notes is not None:
        inc.analyst_notes = inc_in.analyst_notes
    if inc_in.ai_summary is not None:
        inc.ai_summary = inc_in.ai_summary
    if inc_in.ai_recommendations is not None:
        inc.ai_recommendations = inc_in.ai_recommendations

    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE_INCIDENT",
        resource_type="Incident",
        resource_id=str(inc.id),
        details={"status": inc.status, "severity": inc.severity},
        ip_address="127.0.0.1",
    )
    db.add(audit)
    db.commit()
    db.refresh(inc)

    resp = IncidentResponse.model_validate(inc)
    resp.events_count = len(inc.events)
    resp.alerts_count = len(inc.alerts)
    resp.evidence_count = len(inc.evidence_items)
    return resp
