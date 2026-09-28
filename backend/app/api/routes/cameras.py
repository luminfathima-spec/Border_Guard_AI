from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.camera import Camera, CameraStatus
from app.schemas.camera import CameraCreate, CameraUpdate, CameraResponse
from app.api.deps import get_current_active_user, RoleChecker
from app.models.user import User

router = APIRouter(prefix="/cameras", tags=["Cameras"])

@router.get("", response_model=List[CameraResponse])
def list_cameras(
    status: Optional[str] = None,
    zone: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all surveillance cameras with optional filtering by status and zone."""
    query = db.query(Camera)
    if status:
        query = query.filter(Camera.status == status)
    if zone:
        query = query.filter(Camera.zone.ilike(f"%{zone}%"))
    return query.order_by(Camera.id.asc()).all()

@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve specific camera details including polygon zones and tripwires."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return camera

@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker(["ADMIN", "SECURITY_ANALYST"]))])
def create_camera(
    camera_in: CameraCreate,
    db: Session = Depends(get_db),
):
    """Register a new border camera feed (Admin/Analyst)."""
    existing = db.query(Camera).filter(Camera.camera_identifier == camera_in.camera_identifier).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Camera identifier already exists")

    camera = Camera(
        name=camera_in.name,
        camera_identifier=camera_in.camera_identifier,
        location=camera_in.location,
        latitude=camera_in.latitude,
        longitude=camera_in.longitude,
        stream_url=camera_in.stream_url,
        status=camera_in.status.value,
        zone=camera_in.zone,
        restricted_zones=camera_in.restricted_zones,
        virtual_lines=camera_in.virtual_lines,
    )
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera

@router.patch("/{camera_id}", response_model=CameraResponse, dependencies=[Depends(RoleChecker(["ADMIN", "SECURITY_ANALYST", "OPERATOR"]))])
def update_camera(
    camera_id: int,
    camera_in: CameraUpdate,
    db: Session = Depends(get_db),
):
    """Update camera status, locations, restricted zones, or virtual lines."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")

    if camera_in.name is not None:
        camera.name = camera_in.name
    if camera_in.camera_identifier is not None:
        camera.camera_identifier = camera_in.camera_identifier
    if camera_in.location is not None:
        camera.location = camera_in.location
    if camera_in.latitude is not None:
        camera.latitude = camera_in.latitude
    if camera_in.longitude is not None:
        camera.longitude = camera_in.longitude
    if camera_in.stream_url is not None:
        camera.stream_url = camera_in.stream_url
    if camera_in.status is not None:
        camera.status = camera_in.status.value
    if camera_in.zone is not None:
        camera.zone = camera_in.zone
    if camera_in.restricted_zones is not None:
        camera.restricted_zones = camera_in.restricted_zones
    if camera_in.virtual_lines is not None:
        camera.virtual_lines = camera_in.virtual_lines

    db.commit()
    db.refresh(camera)
    return camera
