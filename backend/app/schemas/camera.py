import datetime
import re
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, field_validator
from app.models.camera import CameraStatus

class ZoneCoordinate(BaseModel):
    x: float
    y: float

class RestrictedZoneConfig(BaseModel):
    id: str
    name: str
    polygon: List[ZoneCoordinate]
    alert_severity: str = "HIGH"

class VirtualLineConfig(BaseModel):
    id: str
    name: str
    p1: ZoneCoordinate
    p2: ZoneCoordinate
    direction: str = "BOTH"
    alert_severity: str = "CRITICAL"

class CameraBase(BaseModel):
    name: str
    camera_identifier: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    stream_url: Optional[str] = None
    status: CameraStatus = CameraStatus.ONLINE
    zone: Optional[str] = None
    restricted_zones: List[Dict[str, Any]] = []
    virtual_lines: List[Dict[str, Any]] = []

class CameraCreate(CameraBase):
    pass

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    camera_identifier: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    stream_url: Optional[str] = None
    status: Optional[CameraStatus] = None
    zone: Optional[str] = None
    restricted_zones: Optional[List[Dict[str, Any]]] = None
    virtual_lines: Optional[List[Dict[str, Any]]] = None

class CameraResponse(CameraBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @field_validator("stream_url", mode="after")
    @classmethod
    def sanitize_stream_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        return re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", v)

    model_config = ConfigDict(from_attributes=True)

class RTSPTestRequest(BaseModel):
    stream_url: str
    timeout_seconds: Optional[int] = 5

class RTSPTestResponse(BaseModel):
    connected: bool
    stream_url: str
    latency_ms: int
    resolution: Optional[str] = None
    fps: Optional[float] = None
    error: Optional[str] = None
    message: Optional[str] = None
