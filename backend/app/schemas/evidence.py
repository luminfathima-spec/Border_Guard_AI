import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.evidence import EvidenceType

class EvidenceBase(BaseModel):
    incident_id: Optional[int] = None
    event_id: Optional[int] = None
    evidence_type: EvidenceType
    file_path: str
    file_size_bytes: Optional[int] = None
    checksum_sha256: Optional[str] = None
    metadata_json: Dict[str, Any] = {}

class EvidenceResponse(EvidenceBase):
    id: int
    file_url: str
    timestamp: datetime.datetime
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
