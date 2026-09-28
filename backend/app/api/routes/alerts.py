import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.alert import Alert, AlertStatus
from app.models.audit import AuditLog
from app.schemas.alert import AlertResponse, AlertUpdate
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertResponse])
def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    camera_id: Optional[int] = None,
    incident_id: Optional[int] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List operational alerts with status/severity filters."""
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if camera_id:
        query = query.filter(Alert.camera_id == camera_id)
    if incident_id:
        query = query.filter(Alert.incident_id == incident_id)

    alerts = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()
    results = []
    for a in alerts:
        resp = AlertResponse.model_validate(a)
        if a.camera:
            resp.camera_name = a.camera.name
        results.append(resp)
    return results

@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert_status(
    alert_id: int,
    alert_in: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Acknowledge, investigate, or resolve a surveillance alert.
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    alert.status = alert_in.status.value
    if alert_in.status in [AlertStatus.ACKNOWLEDGED, AlertStatus.INVESTIGATING, AlertStatus.RESOLVED]:
        alert.acknowledged_by = current_user.name
        alert.acknowledged_at = datetime.datetime.now(datetime.timezone.utc)

    # Log audit entry
    audit = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action=f"ALERT_{alert.status}",
        resource_type="Alert",
        resource_id=str(alert.id),
        details={"status": alert.status, "alert_title": alert.title},
        ip_address="127.0.0.1",
    )
    db.add(audit)
    db.commit()
    db.refresh(alert)

    resp = AlertResponse.model_validate(alert)
    if alert.camera:
        resp.camera_name = alert.camera.name
    return resp
