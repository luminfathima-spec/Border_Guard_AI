from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.repositories.base import BaseRepository
from app.models.event import SecurityEvent


class SecurityEventRepository(BaseRepository[SecurityEvent]):
    def __init__(self):
        super().__init__(SecurityEvent)

    def get_recent(
        self,
        db: Session,
        limit: int = 50,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[SecurityEvent]:
        query = db.query(SecurityEvent)
        if severity:
            query = query.filter(SecurityEvent.severity == severity)
        if event_type:
            query = query.filter(SecurityEvent.event_type == event_type)
        return query.order_by(SecurityEvent.timestamp.desc()).limit(limit).all()

    def get_by_camera(self, db: Session, camera_id: int, limit: int = 50) -> List[SecurityEvent]:
        return (
            db.query(SecurityEvent)
            .filter(SecurityEvent.camera_id == camera_id)
            .order_by(SecurityEvent.timestamp.desc())
            .limit(limit)
            .all()
        )


event_repository = SecurityEventRepository()
