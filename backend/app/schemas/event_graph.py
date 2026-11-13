import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.event_graph import RelationshipType, ProvenanceType, ObservationType


class EventLinkBase(BaseModel):
    source_node_type: str = Field(..., description="Entity type of source (CAMERA, VIDEO, FRAME, DETECTION, OBJECT_TRACK, EVENT, INCIDENT, EVIDENCE, AI_ANALYSIS, REPORT, OBSERVATION)")
    source_node_id: int = Field(..., description="ID of the source entity in its respective table")
    source_ref: Optional[str] = Field(None, description="Optional reference string (e.g. frame:142, checksum)")

    target_node_type: str = Field(..., description="Entity type of target")
    target_node_id: int = Field(..., description="ID of the target entity in its respective table")
    target_ref: Optional[str] = Field(None, description="Optional reference string")

    relationship_type: RelationshipType = Field(..., description="Formal semantic relationship type")
    provenance_type: ProvenanceType = Field(ProvenanceType.DIRECT_OBSERVATION, description="Epistemic status of relationship")
    creation_reason: str = Field(..., min_length=3, description="Explicit justification for creating this relationship")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in this relationship (0.0 to 1.0)")

    source_timestamp: Optional[datetime.datetime] = Field(None, description="Physical timestamp when source occurred")
    target_timestamp: Optional[datetime.datetime] = Field(None, description="Physical timestamp when target occurred")

    is_conflict: bool = Field(False, description="Whether this edge represents a conflicting observation")
    conflict_details: Dict[str, Any] = Field(default_factory=dict, description="Metadata describing conflict nature")

    is_missing_evidence: bool = Field(False, description="Whether this edge flags missing evidence / sensor gap")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Extensible edge metadata")


class EventLinkCreate(EventLinkBase):
    pass


class EventLinkResponse(EventLinkBase):
    id: int
    incident_id: int
    valid_from: datetime.datetime
    valid_to: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceObservationBase(BaseModel):
    observation_type: ObservationType = Field(ObservationType.DIRECT_FACT, description="Category of observation")
    provenance_type: ProvenanceType = Field(ProvenanceType.DIRECT_OBSERVATION, description="Epistemic provenance type")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    source_system: str = Field("CCTV_CV", max_length=100)
    timestamp: Optional[datetime.datetime] = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    camera_id: Optional[int] = None
    video_id: Optional[int] = None
    frame_number: Optional[int] = None
    details_json: Dict[str, Any] = Field(default_factory=dict)


class EvidenceObservationCreate(EvidenceObservationBase):
    pass


class EvidenceObservationResponse(EvidenceObservationBase):
    id: int
    incident_id: int
    status: str
    superseded_by_id: Optional[int] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class GraphNode(BaseModel):
    id: str  # Unique key, e.g. "event:42", "camera:1", "observation:5"
    node_type: str
    entity_id: int
    label: str
    timestamp: Optional[datetime.datetime] = None
    provenance_type: str = "DIRECT_OBSERVATION"
    status: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventGraphResponse(BaseModel):
    incident_id: int
    incident_number: str
    nodes: List[GraphNode]
    edges: List[EventLinkResponse]
    total_nodes: int
    total_edges: int
    conflicts_count: int
    missing_evidence_count: int
    direct_facts_count: int
    inferred_count: int


class EvidenceChainStep(BaseModel):
    step_number: int
    node_type: str
    node_id: int
    label: str
    timestamp: Optional[datetime.datetime] = None
    provenance_type: str
    relationship_from_parent: Optional[str] = None
    creation_reason: Optional[str] = None
    is_verified_in_db: bool = True
    source_identifier: Optional[str] = None
    evidence_sha256: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class EvidenceChainResponse(BaseModel):
    incident_id: int
    incident_number: str
    chain: List[EvidenceChainStep]
    is_chain_intact: bool
    unresolved_conflicts: int
    missing_evidence_gaps: int


class GraphValidationResult(BaseModel):
    incident_id: int
    is_valid: bool
    dangling_references: List[Dict[str, Any]]
    out_of_order_timestamps: List[Dict[str, Any]]
    unresolved_conflicts: List[Dict[str, Any]]
    missing_evidence_notices: List[Dict[str, Any]]
    duplicate_edges: List[Dict[str, Any]]
    cycles_detected: List[Dict[str, Any]]
