from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceResponse
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/evidence", tags=["Evidence"])

@router.get("", response_model=List[EvidenceResponse])
def list_evidence(
    incident_id: Optional[int] = None,
    event_id: Optional[int] = None,
    evidence_type: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List forensic evidence items (snapshots, video clips, reports) with tamper-evident checksums."""
    query = db.query(Evidence)
    if incident_id:
        query = query.filter(Evidence.incident_id == incident_id)
    if event_id:
        query = query.filter(Evidence.event_id == event_id)
    if evidence_type:
        query = query.filter(Evidence.evidence_type == evidence_type)

    evidence_items = query.order_by(Evidence.created_at.desc()).offset(offset).limit(limit).all()
    results = []
    for ev in evidence_items:
        # Convert relative file_path to web static URL
        file_path_clean = ev.file_path.replace("\\", "/")
        if file_path_clean.startswith("data/"):
            static_url = f"/static/{file_path_clean[5:]}"
        else:
            static_url = f"/static/{file_path_clean}"

        resp = EvidenceResponse(
            id=ev.id,
            incident_id=ev.incident_id,
            event_id=ev.event_id,
            evidence_type=ev.evidence_type,
            file_path=ev.file_path,
            file_url=static_url,
            file_size_bytes=ev.file_size_bytes,
            checksum_sha256=ev.checksum_sha256,
            metadata_json=ev.metadata_json,
            timestamp=ev.timestamp,
            created_at=ev.created_at,
        )
        results.append(resp)
    return results
