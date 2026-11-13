from fastapi import APIRouter, Depends, status, Query, Body
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.api.deps import get_current_active_user
from app.schemas.event_graph import (
    EventLinkCreate,
    EventLinkResponse,
    EvidenceObservationCreate,
    EvidenceObservationResponse,
    EventGraphResponse,
    EvidenceChainResponse,
    GraphValidationResult,
)
from app.services.event_graph_service import EventGraphService

router = APIRouter(prefix="/incidents", tags=["Event Graph & Provenance"])


@router.get("/{incident_id}/graph", response_model=EventGraphResponse)
def get_incident_graph(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve the full provenance-aware event graph for an incident,
    including nodes, explicit typed edges, conflict markers, and missing evidence gaps.
    """
    return EventGraphService.build_incident_graph(db, incident_id)


@router.post(
    "/{incident_id}/graph/links",
    response_model=EventLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event_link(
    incident_id: int,
    link_in: EventLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create an explicit typed relationship between two entities.
    Validates that both source and target physically exist (preventing dangling references),
    checks for duplicate edges, and records the explicit creation reason.
    """
    return EventGraphService.create_link(db, incident_id, link_in)


@router.get("/{incident_id}/evidence-chain", response_model=EvidenceChainResponse)
def get_incident_evidence_chain(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve an incident's end-to-end evidence chain of custody,
    from physical camera capture through video segments, detections, tracks,
    boundary events, evidence files, cognitive analyses, and final reports.
    Every step is verified against real stored database records.
    """
    return EventGraphService.get_complete_evidence_chain(db, incident_id)


@router.post(
    "/{incident_id}/observations",
    response_model=EvidenceObservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_observation(
    incident_id: int,
    obs_in: EvidenceObservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Record an observation, hypothesis, conflicting sensor observation, or missing data gap
    for an incident without requiring a raw video upload.
    """
    return EventGraphService.record_observation(db, incident_id, obs_in)


@router.post(
    "/{incident_id}/observations/{observation_id}/supersede",
    response_model=EvidenceObservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def supersede_observation(
    incident_id: int,
    observation_id: int,
    new_obs_in: EvidenceObservationCreate,
    reason: str = Query(..., min_length=3, description="Justification for superseding prior observation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Preserve history instead of silently overwriting earlier observations.
    Marks the older observation as SUPERSEDED and links the new observation via a SUPERSEDES edge.
    """
    return EventGraphService.supersede_observation(
        db, incident_id, observation_id, new_obs_in, reason
    )


@router.post("/{incident_id}/graph/validate", response_model=GraphValidationResult)
def validate_incident_graph(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Run formal graph integrity checks on an incident:
    - Dangling references to nonexistent or deleted records.
    - Out-of-order timestamps in causal sequences.
    - Duplicate edges.
    - Circular dependency loops.
    - Unresolved conflicts and missing evidence gaps.
    """
    return EventGraphService.validate_incident_graph(db, incident_id)


@router.post("/{incident_id}/graph/auto-synthesize", response_model=EventGraphResponse)
def auto_synthesize_graph(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Automatically build/synthesize explicit event graph links
    from all database entities already linked to this incident.
    """
    return EventGraphService.auto_synthesize_incident_graph(db, incident_id)
