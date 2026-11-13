from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.repositories.base import BaseRepository
from app.models.track import ObjectTrack


class ObjectTrackRepository(BaseRepository[ObjectTrack]):
    def __init__(self):
        super().__init__(ObjectTrack)

    def get_by_video_and_tracking_id(
        self,
        db: Session,
        video_id: int,
        tracking_id: int,
    ) -> Optional[ObjectTrack]:
        return (
            db.query(ObjectTrack)
            .filter(
                ObjectTrack.video_id == video_id,
                ObjectTrack.tracking_id == tracking_id,
            )
            .first()
        )

    def get_active_tracks(self, db: Session, video_id: Optional[int] = None) -> List[ObjectTrack]:
        query = db.query(ObjectTrack).filter(ObjectTrack.is_active == True)
        if video_id:
            query = query.filter(ObjectTrack.video_id == video_id)
        return query.all()


track_repository = ObjectTrackRepository()
