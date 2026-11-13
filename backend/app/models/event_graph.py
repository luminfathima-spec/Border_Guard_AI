import datetime
from enum import Enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class RelationshipType(str, Enum):
    OBSERVED_BY = "OBSERVED_BY"
    DETECTED_IN = "DETECTED_IN"
    TRIGGERED = "TRIGGERED"
    PART_OF = "PART_OF"
    SUPPORTS = "SUPPORTS"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    CORROBORATES = "CORROBORATES"
    EXTRACTED_FROM = "EXTRACTED_FROM"
    ANALYZED_BY = "ANALYZED_BY"
    DOCUMENTED_IN = "DOCUMENTED_IN"
    SUPERSEDES = "SUPERSEDES"
    FLAGS_MISSING = "FLAGS_MISSING"


class ProvenanceType(str, Enum):
    DIRECT_OBSERVATION = "DIRECT_OBSERVATION"
    INFERRED_ASSOCIATION = "INFERRED_ASSOCIATION"
    ANALYST_ASSERTION = "ANALYST_ASSERTION"
    DERIVED_SYNTHESIS = "DERIVED_SYNTHESIS"


class ObservationType(str, Enum):
    DIRECT_FACT = "DIRECT_FACT"
    INFERRED_HYPOTHESIS = "INFERRED_HYPOTHESIS"
    CONFLICT_RECORD = "CONFLICT_RECORD"
    MISSING_DATA_GAP = "MISSING_DATA_GAP"


class EventLink(Base):
    __tablename__ = "event_links"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(
        Integer,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_node_type = Column(String(50), nullable=False, index=True)
    source_node_id = Column(Integer, nullable=False, index=True)
    source_ref = Column(String(255), nullable=True)

    target_node_type = Column(String(50), nullable=False, index=True)
    target_node_id = Column(Integer, nullable=False, index=True)
    target_ref = Column(String(255), nullable=True)

    relationship_type = Column(String(50), nullable=False, index=True)
    provenance_type = Column(
        String(50),
        default=ProvenanceType.DIRECT_OBSERVATION.value,
        nullable=False,
        index=True,
    )
    creation_reason = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)

    source_timestamp = Column(DateTime, nullable=True)
    target_timestamp = Column(DateTime, nullable=True)

    valid_from = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    valid_to = Column(DateTime, nullable=True)

    is_conflict = Column(Boolean, default=False, nullable=False, index=True)
    conflict_details = Column(JSON, default=dict, nullable=False)

    is_missing_evidence = Column(Boolean, default=False, nullable=False, index=True)
    metadata_json = Column(JSON, default=dict, nullable=False)

    created_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    incident = relationship("Incident", back_populates="graph_edges")

    __table_args__ = (
        Index("ix_event_links_incident_source", "incident_id", "source_node_type", "source_node_id"),
        Index("ix_event_links_incident_target", "incident_id", "target_node_type", "target_node_id"),
        Index("ix_event_links_incident_rel", "incident_id", "relationship_type"),
    )


class EvidenceObservation(Base):
    __tablename__ = "evidence_observations"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(
        Integer,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    observation_type = Column(
        String(50),
        default=ObservationType.DIRECT_FACT.value,
        nullable=False,
        index=True,
    )
    provenance_type = Column(
        String(50),
        default=ProvenanceType.DIRECT_OBSERVATION.value,
        nullable=False,
        index=True,
    )

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    source_system = Column(String(100), default="CCTV_CV", nullable=False)
    timestamp = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
        index=True,
    )
    confidence = Column(Float, default=1.0, nullable=False)

    camera_id = Column(
        Integer,
        ForeignKey("cameras.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    video_id = Column(
        Integer,
        ForeignKey("videos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    frame_number = Column(Integer, nullable=True)

    status = Column(String(50), default="ACTIVE", nullable=False, index=True)
    superseded_by_id = Column(
        Integer,
        ForeignKey("evidence_observations.id", ondelete="SET NULL"),
        nullable=True,
    )

    details_json = Column(JSON, default=dict, nullable=False)

    created_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    incident = relationship("Incident", back_populates="observations")
    camera = relationship("Camera")
    video = relationship("Video")
    superseded_by = relationship("EvidenceObservation", remote_side=[id])
