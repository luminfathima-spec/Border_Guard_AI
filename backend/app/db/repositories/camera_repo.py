from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.repositories.base import BaseRepository
from app.models.camera import Camera, CameraStatus


class CameraRepository(BaseRepository[Camera]):
    def __init__(self):
        super().__init__(Camera)

    def get_by_identifier(self, db: Session, camera_identifier: str) -> Optional[Camera]:
        return db.query(Camera).filter(Camera.camera_identifier == camera_identifier).first()

    def get_active(self, db: Session) -> List[Camera]:
        return db.query(Camera).filter(Camera.status == CameraStatus.ONLINE.value).all()

    def update_zones(
        self,
        db: Session,
        camera: Camera,
        restricted_zones: list,
        virtual_lines: list,
    ) -> Camera:
        camera.restricted_zones = restricted_zones
        camera.virtual_lines = virtual_lines
        db.add(camera)
        db.commit()
        db.refresh(camera)
        return camera


camera_repository = CameraRepository()
