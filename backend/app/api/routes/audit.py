import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.core.config import settings

router = APIRouter(prefix="/audit", tags=["Audit History & Operational Settings"])

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class SystemSettingsResponse(BaseModel):
    app_name: str
    app_version: str
    app_env: str
    edge_mode: bool
    edge_node_id: str
    edge_buffer_max_disk_mb: int
    edge_buffer_retention_days: int
    gemini_model: str
    max_upload_size_mb: int
    max_video_duration_seconds: int
    total_audit_logs_count: int

class UpdateSettingsRequest(BaseModel):
    edge_buffer_retention_days: Optional[int] = None
    edge_sync_batch_size: Optional[int] = None

@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns immutable system audit trail tracking operator actions, report changes,
    security review approvals, and system events.
    """
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return logs

@router.get("/settings", response_model=SystemSettingsResponse)
def get_system_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns platform environment settings, edge configuration, model version, and limits.
    """
    total_logs = db.query(AuditLog).count()
    return SystemSettingsResponse(
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        app_env=settings.APP_ENV,
        edge_mode=settings.EDGE_MODE,
        edge_node_id=settings.EDGE_NODE_ID,
        edge_buffer_max_disk_mb=settings.EDGE_BUFFER_MAX_DISK_MB,
        edge_buffer_retention_days=settings.EDGE_BUFFER_RETENTION_DAYS,
        gemini_model=settings.GEMINI_MODEL,
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        max_video_duration_seconds=settings.MAX_VIDEO_DURATION_SECONDS,
        total_audit_logs_count=total_logs,
    )

@router.post("/settings", response_model=SystemSettingsResponse)
def update_system_settings(
    req: UpdateSettingsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Updates operational settings (admin only).
    """
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators may modify platform settings.",
        )

    updated_fields = {}
    if req.edge_buffer_retention_days is not None:
        settings.EDGE_BUFFER_RETENTION_DAYS = req.edge_buffer_retention_days
        updated_fields["edge_buffer_retention_days"] = req.edge_buffer_retention_days

    # Log audit entry
    log_entry = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE_SYSTEM_SETTINGS",
        resource_type="Settings",
        resource_id="GLOBAL",
        details=updated_fields,
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(log_entry)
    db.commit()

    total_logs = db.query(AuditLog).count()
    return SystemSettingsResponse(
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        app_env=settings.APP_ENV,
        edge_mode=settings.EDGE_MODE,
        edge_node_id=settings.EDGE_NODE_ID,
        edge_buffer_max_disk_mb=settings.EDGE_BUFFER_MAX_DISK_MB,
        edge_buffer_retention_days=settings.EDGE_BUFFER_RETENTION_DAYS,
        gemini_model=settings.GEMINI_MODEL,
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        max_video_duration_seconds=settings.MAX_VIDEO_DURATION_SECONDS,
        total_audit_logs_count=total_logs,
    )
