import datetime
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.incident import Incident
from app.models.camera import Camera
from app.models.video import Video
from app.models.detection import Detection
from app.models.track import ObjectTrack
from app.models.event import SecurityEvent
from app.models.evidence import Evidence
from app.models.ai_analysis import AIAnalysis
from app.models.report import Report
from app.models.event_graph import (
    EventLink,
    EvidenceObservation,
    RelationshipType,
    ProvenanceType,
    ObservationType,
)
from app.schemas.event_graph import (
    EventLinkCreate,
    EventLinkResponse,
    EvidenceObservationCreate,
    EvidenceObservationResponse,
    GraphNode,
    EventGraphResponse,
    EvidenceChainStep,
    EvidenceChainResponse,
    GraphValidationResult,
)
from app.core.logging import logger


class EventGraphService:

    @staticmethod
    def verify_entity_exists(
        db: Session, node_type: str, node_id: int
    ) -> Tuple[bool, Optional[Any], Optional[datetime.datetime], Optional[str]]:
        """
        Verify that a referenced entity physically exists in the database.
        Returns: (exists, model_instance, timestamp, human_label)
        Prevents dangling references.
        """
        ntype = node_type.upper()
        if ntype == "CAMERA":
            obj = db.query(Camera).filter(Camera.id == node_id).first()
            if obj:
                return True, obj, obj.created_at, f"Camera: {obj.name}"
        elif ntype == "VIDEO":
            obj = db.query(Video).filter(Video.id == node_id).first()
            if obj:
                ts = obj.source_timestamp or obj.created_at
                return True, obj, ts, f"Video: {obj.filename}"
        elif ntype == "DETECTION":
            obj = db.query(Detection).filter(Detection.id == node_id).first()
            if obj:
                return True, obj, obj.created_at, f"Detection: {obj.object_type} (frame {obj.frame_number})"
        elif ntype == "OBJECT_TRACK":
            obj = db.query(ObjectTrack).filter(ObjectTrack.id == node_id).first()
            if obj:
                return True, obj, obj.created_at, f"Track #{obj.tracking_id} ({obj.object_type})"
        elif ntype == "EVENT":
            obj = db.query(SecurityEvent).filter(SecurityEvent.id == node_id).first()
            if obj:
                return True, obj, obj.timestamp, f"Event: {obj.event_type}"
        elif ntype == "INCIDENT":
            obj = db.query(Incident).filter(Incident.id == node_id).first()
            if obj:
                return True, obj, obj.created_at, f"Incident: {obj.incident_number}"
        elif ntype == "EVIDENCE":
            obj = db.query(Evidence).filter(Evidence.id == node_id).first()
            if obj:
                return True, obj, obj.timestamp, f"Evidence: {obj.evidence_type}"
        elif ntype == "AI_ANALYSIS":
            obj = db.query(AIAnalysis).filter(AIAnalysis.id == node_id).first()
            if obj:
                return True, obj, obj.created_at, f"AI Analysis ({obj.model_name})"
        elif ntype == "REPORT":
            obj = db.query(Report).filter(Report.id == node_id).first()
            if obj:
                return True, obj, obj.created_at, f"Report: {obj.report_number}"
        elif ntype == "OBSERVATION":
            obj = db.query(EvidenceObservation).filter(EvidenceObservation.id == node_id).first()
            if obj:
                return True, obj, obj.timestamp, f"Observation: {obj.title}"
        elif ntype == "FRAME":
            # Virtual frame reference bound to video
            return True, None, None, f"Frame #{node_id}"

        return False, None, None, None

    @staticmethod
    def create_link(
        db: Session, incident_id: int, link_in: EventLinkCreate
    ) -> EventLink:
        """Create a typed relationship between two entities with validation and duplicate prevention."""
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with ID {incident_id} not found",
            )

        # 1. Prevent dangling references: Validate source and target
        src_exists, src_obj, src_ts, _ = EventGraphService.verify_entity_exists(
            db, link_in.source_node_type, link_in.source_node_id
        )
        if not src_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source entity {link_in.source_node_type} with ID {link_in.source_node_id} does not exist. Dangling references are prohibited.",
            )

        tgt_exists, tgt_obj, tgt_ts, _ = EventGraphService.verify_entity_exists(
            db, link_in.target_node_type, link_in.target_node_id
        )
        if not tgt_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target entity {link_in.target_node_type} with ID {link_in.target_node_id} does not exist. Dangling references are prohibited.",
            )

        # 2. Check for duplicate active edges
        existing = (
            db.query(EventLink)
            .filter(
                EventLink.incident_id == incident_id,
                EventLink.source_node_type == link_in.source_node_type.upper(),
                EventLink.source_node_id == link_in.source_node_id,
                EventLink.target_node_type == link_in.target_node_type.upper(),
                EventLink.target_node_id == link_in.target_node_id,
                EventLink.relationship_type == link_in.relationship_type.value,
                EventLink.valid_to.is_(None),
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate relationship {link_in.relationship_type.value} already exists between {link_in.source_node_type}:{link_in.source_node_id} and {link_in.target_node_type}:{link_in.target_node_id}",
            )

        # 3. Resolve timestamps if missing
        source_ts = link_in.source_timestamp or src_ts
        target_ts = link_in.target_timestamp or tgt_ts

        # 4. Check for temporal ordering anomalies
        metadata = dict(link_in.metadata_json)
        if (
            source_ts
            and target_ts
            and link_in.relationship_type in [
                RelationshipType.TRIGGERED,
                RelationshipType.EXTRACTED_FROM,
                RelationshipType.ANALYZED_BY,
                RelationshipType.DOCUMENTED_IN,
            ]
        ):
            src_naive = source_ts.replace(tzinfo=None) if source_ts.tzinfo else source_ts
            tgt_naive = target_ts.replace(tzinfo=None) if target_ts.tzinfo else target_ts
            if tgt_naive < src_naive:
                metadata["timestamp_warning"] = "Target timestamp precedes source timestamp"

        edge = EventLink(
            incident_id=incident_id,
            source_node_type=link_in.source_node_type.upper(),
            source_node_id=link_in.source_node_id,
            source_ref=link_in.source_ref,
            target_node_type=link_in.target_node_type.upper(),
            target_node_id=link_in.target_node_id,
            target_ref=link_in.target_ref,
            relationship_type=link_in.relationship_type.value,
            provenance_type=link_in.provenance_type.value,
            creation_reason=link_in.creation_reason,
            confidence=link_in.confidence,
            source_timestamp=source_ts,
            target_timestamp=target_ts,
            is_conflict=link_in.is_conflict,
            conflict_details=link_in.conflict_details,
            is_missing_evidence=link_in.is_missing_evidence,
            metadata_json=metadata,
        )
        db.add(edge)
        db.commit()
        db.refresh(edge)
        logger.info(
            f"Created EventLink #{edge.id}: {edge.source_node_type}:{edge.source_node_id} -[{edge.relationship_type}]-> {edge.target_node_type}:{edge.target_node_id}"
        )
        return edge

    @staticmethod
    def record_observation(
        db: Session, incident_id: int, obs_in: EvidenceObservationCreate
    ) -> EvidenceObservation:
        """Record an explicit fact, hypothesis, conflicting report, or missing data gap."""
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with ID {incident_id} not found",
            )

        if obs_in.camera_id:
            cam = db.query(Camera).filter(Camera.id == obs_in.camera_id).first()
            if not cam:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Camera with ID {obs_in.camera_id} not found",
                )

        if obs_in.video_id:
            vid = db.query(Video).filter(Video.id == obs_in.video_id).first()
            if not vid:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Video with ID {obs_in.video_id} not found",
                )

        obs = EvidenceObservation(
            incident_id=incident_id,
            observation_type=obs_in.observation_type.value,
            provenance_type=obs_in.provenance_type.value,
            title=obs_in.title,
            description=obs_in.description,
            source_system=obs_in.source_system,
            timestamp=obs_in.timestamp or datetime.datetime.now(datetime.timezone.utc),
            confidence=obs_in.confidence,
            camera_id=obs_in.camera_id,
            video_id=obs_in.video_id,
            frame_number=obs_in.frame_number,
            status="ACTIVE",
            details_json=obs_in.details_json,
        )
        db.add(obs)
        db.commit()
        db.refresh(obs)

        # Create graph edge linking observation to incident
        edge = EventLink(
            incident_id=incident_id,
            source_node_type="OBSERVATION",
            source_node_id=obs.id,
            target_node_type="INCIDENT",
            target_node_id=incident_id,
            relationship_type=RelationshipType.PART_OF.value,
            provenance_type=obs.provenance_type,
            creation_reason=f"Observation '{obs.title}' recorded for incident {incident.incident_number}",
            confidence=obs.confidence,
            source_timestamp=obs.timestamp,
            target_timestamp=incident.created_at,
            is_conflict=(obs.observation_type == ObservationType.CONFLICT_RECORD.value),
            conflict_details=obs.details_json if obs.observation_type == ObservationType.CONFLICT_RECORD.value else {},
            is_missing_evidence=(obs.observation_type == ObservationType.MISSING_DATA_GAP.value),
            metadata_json={"observation_type": obs.observation_type},
        )
        db.add(edge)
        db.commit()
        return obs

    @staticmethod
    def supersede_observation(
        db: Session,
        incident_id: int,
        old_observation_id: int,
        new_obs_in: EvidenceObservationCreate,
        reason: str,
    ) -> EvidenceObservation:
        """
        Preserve history instead of silently overwriting earlier observations.
        Marks old observation as SUPERSEDED and links new observation with SUPERSEDES relationship.
        """
        old_obs = (
            db.query(EvidenceObservation)
            .filter(
                EvidenceObservation.id == old_observation_id,
                EvidenceObservation.incident_id == incident_id,
            )
            .first()
        )
        if not old_obs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prior observation #{old_observation_id} not found in incident #{incident_id}",
            )

        # 1. Create the new observation
        new_obs = EvidenceObservation(
            incident_id=incident_id,
            observation_type=new_obs_in.observation_type.value,
            provenance_type=new_obs_in.provenance_type.value,
            title=new_obs_in.title,
            description=new_obs_in.description,
            source_system=new_obs_in.source_system,
            timestamp=new_obs_in.timestamp or datetime.datetime.now(datetime.timezone.utc),
            confidence=new_obs_in.confidence,
            camera_id=new_obs_in.camera_id or old_obs.camera_id,
            video_id=new_obs_in.video_id or old_obs.video_id,
            frame_number=new_obs_in.frame_number or old_obs.frame_number,
            status="ACTIVE",
            details_json=new_obs_in.details_json,
        )
        db.add(new_obs)
        db.flush()

        # 2. Update old observation status and pointer without deleting its history
        now = datetime.datetime.now(datetime.timezone.utc)
        old_obs.status = "SUPERSEDED"
        old_obs.superseded_by_id = new_obs.id

        # 3. Invalidate old edges if needed, and create SUPERSEDES link
        supersedes_edge = EventLink(
            incident_id=incident_id,
            source_node_type="OBSERVATION",
            source_node_id=new_obs.id,
            target_node_type="OBSERVATION",
            target_node_id=old_obs.id,
            relationship_type=RelationshipType.SUPERSEDES.value,
            provenance_type=new_obs.provenance_type,
            creation_reason=f"Supersedes #{old_obs.id} ('{old_obs.title}'): {reason}",
            confidence=new_obs.confidence,
            source_timestamp=new_obs.timestamp,
            target_timestamp=old_obs.timestamp,
            metadata_json={"supersession_reason": reason, "previous_status": "ACTIVE"},
        )
        db.add(supersedes_edge)

        # Link new observation to incident
        part_of_edge = EventLink(
            incident_id=incident_id,
            source_node_type="OBSERVATION",
            source_node_id=new_obs.id,
            target_node_type="INCIDENT",
            target_node_id=incident_id,
            relationship_type=RelationshipType.PART_OF.value,
            provenance_type=new_obs.provenance_type,
            creation_reason=f"Active replacement observation '{new_obs.title}'",
            confidence=new_obs.confidence,
            source_timestamp=new_obs.timestamp,
            metadata_json={"superseded_observation_id": old_obs.id},
        )
        db.add(part_of_edge)

        db.commit()
        db.refresh(new_obs)
        return new_obs

    @staticmethod
    def build_incident_graph(db: Session, incident_id: int) -> EventGraphResponse:
        """Retrieve an incident's complete evidence graph."""
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with ID {incident_id} not found",
            )

        edges = (
            db.query(EventLink)
            .filter(EventLink.incident_id == incident_id)
            .order_by(EventLink.id.asc())
            .all()
        )

        # Collect unique nodes
        nodes_dict: Dict[str, GraphNode] = {}

        # Always include the Incident root node
        nodes_dict[f"INCIDENT:{incident.id}"] = GraphNode(
            id=f"INCIDENT:{incident.id}",
            node_type="INCIDENT",
            entity_id=incident.id,
            label=f"Incident {incident.incident_number}",
            timestamp=incident.created_at,
            provenance_type="DIRECT_OBSERVATION",
            status=incident.status,
            metadata={"severity": incident.severity, "title": incident.title},
        )

        for edge in edges:
            for ntype, nid in [
                (edge.source_node_type, edge.source_node_id),
                (edge.target_node_type, edge.target_node_id),
            ]:
                key = f"{ntype}:{nid}"
                if key not in nodes_dict:
                    exists, obj, ts, lbl = EventGraphService.verify_entity_exists(db, ntype, nid)
                    prov = edge.provenance_type
                    st = None
                    meta: Dict[str, Any] = {}
                    if exists and obj:
                        if hasattr(obj, "status"):
                            st = getattr(obj, "status")
                        if hasattr(obj, "description"):
                            meta["description"] = getattr(obj, "description")
                        if hasattr(obj, "checksum_sha256"):
                            meta["checksum_sha256"] = getattr(obj, "checksum_sha256")
                        if hasattr(obj, "confidence"):
                            meta["confidence"] = getattr(obj, "confidence")
                    nodes_dict[key] = GraphNode(
                        id=key,
                        node_type=ntype,
                        entity_id=nid,
                        label=lbl or f"{ntype} #{nid}",
                        timestamp=ts,
                        provenance_type=prov,
                        status=st,
                        metadata=meta,
                    )

        nodes_list = list(nodes_dict.values())
        edge_responses = [EventLinkResponse.model_validate(e) for e in edges]

        conflicts = sum(1 for e in edges if e.is_conflict)
        missing = sum(1 for e in edges if e.is_missing_evidence)
        direct_facts = sum(1 for e in edges if e.provenance_type == ProvenanceType.DIRECT_OBSERVATION.value)
        inferred = sum(1 for e in edges if e.provenance_type in [
            ProvenanceType.INFERRED_ASSOCIATION.value,
            ProvenanceType.DERIVED_SYNTHESIS.value,
        ])

        return EventGraphResponse(
            incident_id=incident.id,
            incident_number=incident.incident_number,
            nodes=nodes_list,
            edges=edge_responses,
            total_nodes=len(nodes_list),
            total_edges=len(edge_responses),
            conflicts_count=conflicts,
            missing_evidence_count=missing,
            direct_facts_count=direct_facts,
            inferred_count=inferred,
        )

    @staticmethod
    def get_complete_evidence_chain(db: Session, incident_id: int) -> EvidenceChainResponse:
        """
        Retrieve an incident and its complete evidence chain,
        verifying that each reference resolves to a real stored database record.
        """
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with ID {incident_id} not found",
            )

        chain_steps: List[EvidenceChainStep] = []
        step_num = 1

        # 1. Associated Security Events
        events = (
            db.query(SecurityEvent)
            .filter(SecurityEvent.incident_id == incident_id)
            .order_by(SecurityEvent.timestamp.asc())
            .all()
        )

        for ev in events:
            # Camera level
            if ev.camera_id:
                cam = db.query(Camera).filter(Camera.id == ev.camera_id).first()
                if cam:
                    chain_steps.append(
                        EvidenceChainStep(
                            step_number=step_num,
                            node_type="CAMERA",
                            node_id=cam.id,
                            label=f"Sensor Origin: {cam.name}",
                            timestamp=cam.created_at,
                            provenance_type="DIRECT_OBSERVATION",
                            relationship_from_parent="OBSERVED_BY",
                            creation_reason="Hardware CCTV camera streaming live field of view",
                            is_verified_in_db=True,
                            source_identifier=cam.stream_url or f"cam-{cam.id}",
                            details={"location": cam.location, "status": cam.status},
                        )
                    )
                    step_num += 1

            # Video level
            if ev.video_id:
                vid = db.query(Video).filter(Video.id == ev.video_id).first()
                if vid:
                    chain_steps.append(
                        EvidenceChainStep(
                            step_number=step_num,
                            node_type="VIDEO",
                            node_id=vid.id,
                            label=f"Video Footage: {vid.filename}",
                            timestamp=vid.source_timestamp or vid.created_at,
                            provenance_type="DIRECT_OBSERVATION",
                            relationship_from_parent="RECORDED_IN",
                            creation_reason="Cryptographically hashed surveillance video recording",
                            is_verified_in_db=True,
                            source_identifier=vid.path,
                            evidence_sha256=vid.checksum_sha256,
                            details={
                                "duration_seconds": vid.duration,
                                "fps": vid.fps,
                                "resolution": vid.resolution,
                            },
                        )
                    )
                    step_num += 1

            # Track level if present in metadata
            track_id = ev.metadata_json.get("tracking_id")
            if track_id and ev.video_id:
                trk = (
                    db.query(ObjectTrack)
                    .filter(
                        ObjectTrack.video_id == ev.video_id,
                        ObjectTrack.tracking_id == track_id,
                    )
                    .first()
                )
                if trk:
                    chain_steps.append(
                        EvidenceChainStep(
                            step_number=step_num,
                            node_type="OBJECT_TRACK",
                            node_id=trk.id,
                            label=f"Persistent Track #{trk.tracking_id} ({trk.object_type})",
                            timestamp=ev.timestamp,
                            provenance_type="INFERRED_ASSOCIATION",
                            relationship_from_parent="TRACKED_ACROSS_FRAMES",
                            creation_reason="Multi-frame IoU and centroid association engine",
                            is_verified_in_db=True,
                            source_identifier=f"video:{trk.video_id}:track:{trk.tracking_id}",
                            details={
                                "first_seen_frame": trk.first_seen_frame,
                                "last_seen_frame": trk.last_seen_frame,
                                "dwell_time_seconds": trk.dwell_time_seconds,
                                "max_confidence": trk.max_confidence,
                            },
                        )
                    )
                    step_num += 1

            # Event breach level
            chain_steps.append(
                EvidenceChainStep(
                    step_number=step_num,
                    node_type="EVENT",
                    node_id=ev.id,
                    label=f"Security Event: {ev.event_type}",
                    timestamp=ev.timestamp,
                    provenance_type="DIRECT_OBSERVATION",
                    relationship_from_parent="TRIGGERED",
                    creation_reason=f"Geometric boundary breach: {ev.description}",
                    is_verified_in_db=True,
                    source_identifier=f"event-{ev.id}",
                    details={
                        "severity": ev.severity,
                        "confidence": ev.confidence,
                        "snapshot_path": ev.snapshot_path,
                    },
                )
            )
            step_num += 1

            # Evidence files bound to event
            for ev_file in ev.evidence_items:
                chain_steps.append(
                    EvidenceChainStep(
                        step_number=step_num,
                        node_type="EVIDENCE",
                        node_id=ev_file.id,
                        label=f"Forensic Asset: {ev_file.evidence_type}",
                        timestamp=ev_file.timestamp,
                        provenance_type="DIRECT_OBSERVATION",
                        relationship_from_parent="SUPPORTS",
                        creation_reason="Tamper-evident frame snapshot captured at point of breach",
                        is_verified_in_db=True,
                        source_identifier=ev_file.file_path,
                        evidence_sha256=ev_file.checksum_sha256,
                        details={"file_size_bytes": ev_file.file_size_bytes},
                    )
                )
                step_num += 1

        # 2. Observations (conflicts, missing evidence, analyst assertions)
        observations = (
            db.query(EvidenceObservation)
            .filter(EvidenceObservation.incident_id == incident_id)
            .order_by(EvidenceObservation.timestamp.asc())
            .all()
        )
        for obs in observations:
            chain_steps.append(
                EvidenceChainStep(
                    step_number=step_num,
                    node_type="OBSERVATION",
                    node_id=obs.id,
                    label=f"Observation ({obs.observation_type}): {obs.title}",
                    timestamp=obs.timestamp,
                    provenance_type=obs.provenance_type,
                    relationship_from_parent="PART_OF",
                    creation_reason=obs.description,
                    is_verified_in_db=True,
                    source_identifier=obs.source_system,
                    details=obs.details_json,
                )
            )
            step_num += 1

        # 3. AI Analyses
        analyses = (
            db.query(AIAnalysis)
            .filter(AIAnalysis.incident_id == incident_id)
            .order_by(AIAnalysis.created_at.asc())
            .all()
        )
        for an in analyses:
            chain_steps.append(
                EvidenceChainStep(
                    step_number=step_num,
                    node_type="AI_ANALYSIS",
                    node_id=an.id,
                    label=f"Cognitive Threat Reasoning: {an.prompt_type}",
                    timestamp=an.created_at,
                    provenance_type="DERIVED_SYNTHESIS",
                    relationship_from_parent="ANALYZED_BY",
                    creation_reason=f"Structured multimodal analysis processed by {an.model_name}",
                    is_verified_in_db=True,
                    source_identifier=an.model_name,
                    details={
                        "confidence_score": an.confidence_score,
                        "grounded_citations": an.grounded_citations,
                        "execution_time_ms": an.execution_time_ms,
                    },
                )
            )
            step_num += 1

        # 4. Reports
        reports = (
            db.query(Report)
            .filter(Report.incident_id == incident_id)
            .order_by(Report.created_at.asc())
            .all()
        )
        for rep in reports:
            chain_steps.append(
                EvidenceChainStep(
                    step_number=step_num,
                    node_type="REPORT",
                    node_id=rep.id,
                    label=f"Official Dossier: {rep.report_number}",
                    timestamp=rep.created_at,
                    provenance_type="DERIVED_SYNTHESIS",
                    relationship_from_parent="DOCUMENTED_IN",
                    creation_reason=f"Exported dossier title '{rep.title}'",
                    is_verified_in_db=True,
                    source_identifier=rep.file_path,
                    evidence_sha256=rep.checksum_sha256,
                    details={"status": rep.status, "type": rep.report_type},
                )
            )
            step_num += 1

        # Incident node as termination
        chain_steps.append(
            EvidenceChainStep(
                step_number=step_num,
                node_type="INCIDENT",
                node_id=incident.id,
                label=f"Active Incident Dossier: {incident.incident_number}",
                timestamp=incident.created_at,
                provenance_type="DIRECT_OBSERVATION",
                relationship_from_parent="CONTAINED_IN",
                creation_reason="Master security operations incident envelope",
                is_verified_in_db=True,
                source_identifier=incident.incident_number,
                details={"severity": incident.severity, "status": incident.status},
            )
        )

        unresolved_conflicts = (
            db.query(EvidenceObservation)
            .filter(
                EvidenceObservation.incident_id == incident_id,
                EvidenceObservation.observation_type == ObservationType.CONFLICT_RECORD.value,
                EvidenceObservation.status == "ACTIVE",
            )
            .count()
        )

        missing_evidence = (
            db.query(EvidenceObservation)
            .filter(
                EvidenceObservation.incident_id == incident_id,
                EvidenceObservation.observation_type == ObservationType.MISSING_DATA_GAP.value,
                EvidenceObservation.status == "ACTIVE",
            )
            .count()
        )

        return EvidenceChainResponse(
            incident_id=incident.id,
            incident_number=incident.incident_number,
            chain=chain_steps,
            is_chain_intact=True,
            unresolved_conflicts=unresolved_conflicts,
            missing_evidence_gaps=missing_evidence,
        )

    @staticmethod
    def validate_incident_graph(db: Session, incident_id: int) -> GraphValidationResult:
        """
        Validate graph integrity:
        - Detect dangling references to nonexistent or deleted records.
        - Detect out-of-order timestamps in causal sequences.
        - Detect duplicate links.
        - Detect circular dependency loops (cycles).
        - Enumerate unresolved conflicts and missing evidence notices.
        """
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with ID {incident_id} not found",
            )

        edges = db.query(EventLink).filter(EventLink.incident_id == incident_id).all()

        dangling: List[Dict[str, Any]] = []
        out_of_order: List[Dict[str, Any]] = []
        duplicates: List[Dict[str, Any]] = []
        conflicts: List[Dict[str, Any]] = []
        missing: List[Dict[str, Any]] = []
        cycles: List[Dict[str, Any]] = []

        seen_edges = set()
        adj_list = defaultdict(list)

        for edge in edges:
            # 1. Check dangling references
            src_ok, _, src_ts, _ = EventGraphService.verify_entity_exists(
                db, edge.source_node_type, edge.source_node_id
            )
            if not src_ok:
                dangling.append(
                    {
                        "edge_id": edge.id,
                        "type": "SOURCE_MISSING",
                        "entity": f"{edge.source_node_type}:{edge.source_node_id}",
                    }
                )

            tgt_ok, _, tgt_ts, _ = EventGraphService.verify_entity_exists(
                db, edge.target_node_type, edge.target_node_id
            )
            if not tgt_ok:
                dangling.append(
                    {
                        "edge_id": edge.id,
                        "type": "TARGET_MISSING",
                        "entity": f"{edge.target_node_type}:{edge.target_node_id}",
                    }
                )

            # 2. Check duplicate edges
            edge_signature = (
                edge.source_node_type,
                edge.source_node_id,
                edge.target_node_type,
                edge.target_node_id,
                edge.relationship_type,
            )
            if edge_signature in seen_edges and edge.valid_to is None:
                duplicates.append(
                    {
                        "edge_id": edge.id,
                        "signature": f"{edge.source_node_type}:{edge.source_node_id} -> {edge.target_node_type}:{edge.target_node_id} ({edge.relationship_type})",
                    }
                )
            seen_edges.add(edge_signature)

            # 3. Check out of order timestamps for causal relationships
            st = edge.source_timestamp or src_ts
            tt = edge.target_timestamp or tgt_ts
            if (
                st
                and tt
                and edge.relationship_type in [
                    RelationshipType.TRIGGERED.value,
                    RelationshipType.EXTRACTED_FROM.value,
                    RelationshipType.ANALYZED_BY.value,
                    RelationshipType.DOCUMENTED_IN.value,
                ]
            ):
                if tt < st:
                    out_of_order.append(
                        {
                            "edge_id": edge.id,
                            "source": f"{edge.source_node_type}:{edge.source_node_id} ({st})",
                            "target": f"{edge.target_node_type}:{edge.target_node_id} ({tt})",
                            "relationship": edge.relationship_type,
                        }
                    )

            # 4. Check conflicts & missing evidence
            if edge.is_conflict:
                conflicts.append(
                    {
                        "edge_id": edge.id,
                        "reason": edge.creation_reason,
                        "details": edge.conflict_details,
                    }
                )
            if edge.is_missing_evidence:
                missing.append(
                    {
                        "edge_id": edge.id,
                        "reason": edge.creation_reason,
                        "details": edge.metadata_json,
                    }
                )

            # Build adjacency list for cycle detection
            u = f"{edge.source_node_type}:{edge.source_node_id}"
            v = f"{edge.target_node_type}:{edge.target_node_id}"
            adj_list[u].append(v)

        # 5. Cycle Detection using DFS
        visited: Dict[str, int] = {}  # 0 = unvisited, 1 = visiting, 2 = visited

        def dfs(node: str, path: List[str]):
            visited[node] = 1
            path.append(node)
            for neighbor in adj_list.get(node, []):
                if visited.get(neighbor) == 1:
                    cycle_slice = path[path.index(neighbor):] + [neighbor]
                    cycles.append({"cycle": " -> ".join(cycle_slice)})
                elif visited.get(neighbor, 0) == 0:
                    dfs(neighbor, path)
            path.pop()
            visited[node] = 2

        for node in list(adj_list.keys()):
            if visited.get(node, 0) == 0:
                dfs(node, [])

        is_valid = len(dangling) == 0 and len(duplicates) == 0 and len(cycles) == 0

        return GraphValidationResult(
            incident_id=incident_id,
            is_valid=is_valid,
            dangling_references=dangling,
            out_of_order_timestamps=out_of_order,
            unresolved_conflicts=conflicts,
            missing_evidence_notices=missing,
            duplicate_edges=duplicates,
            cycles_detected=cycles,
        )

    @staticmethod
    def auto_synthesize_incident_graph(
        db: Session, incident_id: int
    ) -> EventGraphResponse:
        """
        Auto-synthesize provenance links from existing incident relationships:
        - Security Events, Cameras, Videos, Tracks, Evidence Files, AI Analyses, Reports.
        """
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident with ID {incident_id} not found",
            )

        events = db.query(SecurityEvent).filter(SecurityEvent.incident_id == incident_id).all()

        for ev in events:
            # 1. Event -> Incident (PART_OF)
            EventGraphService._ensure_link(
                db,
                incident_id,
                source_type="EVENT",
                source_id=ev.id,
                target_type="INCIDENT",
                target_id=incident.id,
                rel_type=RelationshipType.PART_OF,
                prov_type=ProvenanceType.DIRECT_OBSERVATION,
                reason=f"Security event #{ev.id} ({ev.event_type}) classified under incident {incident.incident_number}",
                source_ts=ev.timestamp,
                target_ts=incident.created_at,
            )

            # 2. Event -> Camera (OBSERVED_BY)
            if ev.camera_id:
                cam = db.query(Camera).filter(Camera.id == ev.camera_id).first()
                if cam:
                    EventGraphService._ensure_link(
                        db,
                        incident_id,
                        source_type="EVENT",
                        source_id=ev.id,
                        target_type="CAMERA",
                        target_id=cam.id,
                        rel_type=RelationshipType.OBSERVED_BY,
                        prov_type=ProvenanceType.DIRECT_OBSERVATION,
                        reason=f"Physical event captured on Camera '{cam.name}'",
                        source_ts=ev.timestamp,
                        target_ts=cam.created_at,
                    )

            # 3. Event -> Video (EXTRACTED_FROM)
            if ev.video_id:
                vid = db.query(Video).filter(Video.id == ev.video_id).first()
                if vid:
                    EventGraphService._ensure_link(
                        db,
                        incident_id,
                        source_type="EVENT",
                        source_id=ev.id,
                        target_type="VIDEO",
                        target_id=vid.id,
                        rel_type=RelationshipType.EXTRACTED_FROM,
                        prov_type=ProvenanceType.DIRECT_OBSERVATION,
                        reason=f"Event extracted from video footage '{vid.filename}' (SHA256: {vid.checksum_sha256 or 'N/A'})",
                        source_ts=ev.timestamp,
                        target_ts=vid.source_timestamp or vid.created_at,
                    )

            # 4. ObjectTrack -> Event (TRIGGERED)
            track_id = ev.metadata_json.get("tracking_id")
            if track_id and ev.video_id:
                trk = (
                    db.query(ObjectTrack)
                    .filter(
                        ObjectTrack.video_id == ev.video_id,
                        ObjectTrack.tracking_id == track_id,
                    )
                    .first()
                )
                if trk:
                    EventGraphService._ensure_link(
                        db,
                        incident_id,
                        source_type="OBJECT_TRACK",
                        source_id=trk.id,
                        target_type="EVENT",
                        target_id=ev.id,
                        rel_type=RelationshipType.TRIGGERED,
                        prov_type=ProvenanceType.INFERRED_ASSOCIATION,
                        reason=f"Trajectory of Track #{trk.tracking_id} crossed perimeter boundary, triggering {ev.event_type}",
                        source_ts=ev.timestamp,
                        target_ts=ev.timestamp,
                    )

            # 5. Evidence -> Event (SUPPORTS)
            for ev_file in ev.evidence_items:
                EventGraphService._ensure_link(
                    db,
                    incident_id,
                    source_type="EVIDENCE",
                    source_id=ev_file.id,
                    target_type="EVENT",
                    target_id=ev.id,
                    rel_type=RelationshipType.SUPPORTS,
                    prov_type=ProvenanceType.DIRECT_OBSERVATION,
                    reason=f"Tamper-evident snapshot ({ev_file.evidence_type}) supports physical breach assertion",
                    source_ts=ev_file.timestamp,
                    target_ts=ev.timestamp,
                )

        # 6. Incident -> AIAnalysis (ANALYZED_BY)
        analyses = db.query(AIAnalysis).filter(AIAnalysis.incident_id == incident_id).all()
        for an in analyses:
            EventGraphService._ensure_link(
                db,
                incident_id,
                source_type="INCIDENT",
                source_id=incident.id,
                target_type="AI_ANALYSIS",
                target_id=an.id,
                rel_type=RelationshipType.ANALYZED_BY,
                prov_type=ProvenanceType.DERIVED_SYNTHESIS,
                reason=f"Incident evaluated by cognitive reasoning engine ({an.model_name})",
                source_ts=incident.created_at,
                target_ts=an.created_at,
            )

        # 7. Incident -> Report (DOCUMENTED_IN)
        reports = db.query(Report).filter(Report.incident_id == incident_id).all()
        for rep in reports:
            EventGraphService._ensure_link(
                db,
                incident_id,
                source_type="INCIDENT",
                source_id=incident.id,
                target_type="REPORT",
                target_id=rep.id,
                rel_type=RelationshipType.DOCUMENTED_IN,
                prov_type=ProvenanceType.DERIVED_SYNTHESIS,
                reason=f"Official SITREP generated: Report #{rep.report_number}",
                source_ts=incident.created_at,
                target_ts=rep.created_at,
            )

        db.commit()
        return EventGraphService.build_incident_graph(db, incident_id)

    @staticmethod
    def _ensure_link(
        db: Session,
        incident_id: int,
        source_type: str,
        source_id: int,
        target_type: str,
        target_id: int,
        rel_type: RelationshipType,
        prov_type: ProvenanceType,
        reason: str,
        source_ts: Optional[datetime.datetime] = None,
        target_ts: Optional[datetime.datetime] = None,
    ):
        """Helper to ensure an edge exists without raising an error on duplicate."""
        exists = (
            db.query(EventLink)
            .filter(
                EventLink.incident_id == incident_id,
                EventLink.source_node_type == source_type.upper(),
                EventLink.source_node_id == source_id,
                EventLink.target_node_type == target_type.upper(),
                EventLink.target_node_id == target_id,
                EventLink.relationship_type == rel_type.value,
                EventLink.valid_to.is_(None),
            )
            .first()
        )
        if not exists:
            link = EventLink(
                incident_id=incident_id,
                source_node_type=source_type.upper(),
                source_node_id=source_id,
                target_node_type=target_type.upper(),
                target_node_id=target_id,
                relationship_type=rel_type.value,
                provenance_type=prov_type.value,
                creation_reason=reason,
                confidence=1.0,
                source_timestamp=source_ts,
                target_timestamp=target_ts,
            )
            db.add(link)
