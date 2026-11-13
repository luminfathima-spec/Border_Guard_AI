# SentinelAI — System Architecture & Engineering Specifications

## 1. Architectural Foundations

SentinelAI utilizes a decoupled, asynchronous micro-modular architecture designed for 24/7 mission-critical border surveillance:

```
┌─────────────────────────────────────────────────────────────┐
│                FastAPI Application Layer                    │
├─────────────┬──────────────┬───────────────┬────────────────┤
│ Auth & RBAC │ Video Ingest │ Computer Vis. │ Gemini GenAI   │
│ (JWT/Bcrypt)│ & FFmpeg     │ & Tracking    │ Intelligence   │
└──────┬──────┴──────┬───────┴───────┬───────┴────────┬───────┘
       │             │               │                │
       ▼             ▼               ▼                ▼
┌──────────────┬──────────────┬───────────────┬───────────────┐
│ PostgreSQL 17│ Local Media  │ Ultralytics   │ Google GenAI  │
│ Database     │ Storage Pool │ YOLOv8n / CV2 │ Python SDK    │
└──────────────┴──────────────┴───────────────┴───────────────┘
```

---

## 2. Core Subsystems

### 2.1 Video Ingestion & Decoding Pipeline
- **Validation**: Uploaded files pass extension whitelisting (`.mp4`, `.avi`, `.mov`, `.mkv`), MIME verification, and 500MB size caps.
- **Path Traversal Protection**: Filenames are renamed using UUID4 hashes server-side.
- **FFmpeg & OpenCV Probe**: Probes frame width, height, fps, total duration, and codec metadata.

### 2.2 Computer Vision & Spatial Analytics
1. **YOLOv8 Detection Engine**:
   - Class filtering restricted to surveillance categories: `person`, `car`, `truck`, `bus`, `motorcycle`, `bicycle`, `animal`.
   - Normalization of all bounding box coordinates to `[0.0, 1.0]` relative to frame dimensions.
2. **Surveillance Object Tracker**:
   - IoU (Intersection-over-Union) cost matrix matching.
   - Persistent tracking IDs across frames.
   - Dwell time calculation: $t_{\text{dwell}} = t_{\text{last}} - t_{\text{first}}$.
3. **Ray-Casting Polygonal Zone Analyzer**:
   - Determines whether target centroid $(c_x, c_y)$ falls within an arbitrary convex/concave polygon.
   - Edge transition detection triggering `RESTRICTED_ZONE_ENTRY`.
4. **Vector Line Crossing Tripwire**:
   - Evaluates vector intersection between previous centroid $(p_x, p_y)$ and current centroid $(c_x, c_y)$ against virtual line segment $(q_1, q_2)$.

### 2.3 Automated Forensic Evidence Subsystem
- When a `HIGH` or `CRITICAL` event is detected:
  1. Keyframe snapshot JPEG is written with $92\%$ quality.
  2. FFmpeg extracts a clipped MP4 stream around the timestamp ($t - 3\text{s}$ to $t + 3\text{s}$).
  3. SHA-256 hash is computed and stored with the `Evidence` record.

### 2.4 Google Gemini Intelligence Layer (Phase 5 Architecture)
- **Official Google GenAI SDK (`google-genai` v2.19.0)**:
  - Default operational model: `gemini-2.5-flash` (`settings.GEMINI_MODEL`), delivering sub-second multimodal inference and native JSON schema structured outputs.
  - Decoupled `BaseGeminiClient` architecture supporting `RealGeminiClient` with bounded exponential backoff on HTTP 429/503 and `MockGeminiClient` for deterministic unit testing.
- **Event-Triggered Multimodal Keyframe Selection**:
  - Automatically isolates snapshot frames and extracts breach keyframes ($\pm 1.5\text{s}$ context) rather than streaming continuous raw video feeds, compressing to $< 350\text{ KB}$ JPEG payloads.
- **Versioned Prompting & Privacy Sanitization**:
  - Immutable version tracking via `PROMPT_VERSION = "2026.04.1"`.
  - Privacy and OPSEC sanitization (`sanitize_telemetry`) stripping RTSP passwords, bearer tokens, database secrets, and operator PII before external transmission.
- **Structured Pydantic Response Schema (`IncidentAnalysisResponse`)**:
  - Enforces rigid output typing across `summary`, `observed_events`, `referenced_camera_ids`, `supporting_evidence_ids`, `timestamp_references`, `uncertainty_and_conflicts`, `suggested_human_actions`, `threat_level`, and `insufficient_evidence`.
- **Deterministic Cross-Examiner Evidence Safeguard**:
  - Post-generation programmatic verification of all cited camera, event, and evidence IDs against immutable PostgreSQL tables.
  - Quarantines ungrounded hallucinations, flags status as `FLAGGED`, appends evidentiary warning banners, and records Grounding Score $S_{\text{ground}} \in [0.0, 1.0]$.
- **Provenance Graph Registration**:
  - Automatically registers an `ANALYZED_BY` edge (`provenance_type="DERIVED_SYNTHESIS"`) connecting `AI_ANALYSIS` records to the incident in the Event Graph.


### 2.5 Provenance-Aware Event Graph & Chain of Custody Subsystem
- **Labeled Property Graph in PostgreSQL**:
  - Implements typed explicit relationships via `event_links` and non-destructive historical tracking via `evidence_observations`.
  - Distinguishes raw physical sensor facts (`DIRECT_OBSERVATION`) from algorithmic or heuristic conclusions (`INFERRED_ASSOCIATION`) and AI reasoning (`DERIVED_SYNTHESIS`).
  - Native representation for contradictory sensor observations (`CONFLICT_RECORD`) and telemetry loss intervals (`MISSING_DATA_GAP`).
  - Prohibits dangling references by verifying source and target record physical existence prior to link creation.
  - History preservation via `SUPERSEDES` relationships, preventing destructive in-place overwriting of evidentiary records.

### 2.6 Adaptive Evidence Verification Controller (Phase 6 Architecture)
- **Independent Evidentiary Sufficiency Evaluator**:
  - Calculates composite evidentiary sufficiency $S_{ev} \in [0.0, 1.0]$ across 7 physical and contextual telemetry dimensions:
    $$S_{ev} = w_{det} S_{det} + w_{trk} S_{trk} + w_{geom} S_{geom} + w_{cam} S_{cam} + w_{ev} S_{evid} - w_{conf} C_{conf}$$
  - Evaluates boundary geometric distance margins, object-track continuity, sensor availability, and contradictory observation penalties.
- **Hierarchical Adaptive Controller Loop**:
  - **Local Dense Frame Burst**: When $S_{ev} < \theta_{min}$, controller extracts a dense local frame burst ($\pm 1.5\text{s}$ at native frame rate) from the raw source video, re-verifying trajectory without invoking cloud APIs.
  - **Selective Cloud AI Invocation**: Invokes Google Gemini multimodal reasoning *only* when cross-camera observational conflicts exist or visual ambiguity persists after local resampling.
  - **Resource Budget Termination**: Halts processing when max frames, API quota, or latency budgets are reached.
  - **Principled `UNRESOLVED` State**: Cases with irrecoverable camera gaps or unverified thresholds are formally designated `UNRESOLVED` rather than forced into arbitrary binary classifications.
  - **Immutable Decision Ledger**: Every step, sensory input, rationale, and cost is logged in `verification_ledgers` and mapped to `INCIDENT` / `EVENT`.
### 2.7 Evidence-Grounded Incident Report Generation Subsystem (Phase 7 Architecture)
- **Programmatic Cross-Examiner Verification (Untrusted LLM Output Model)**:
  - Treats all Generative AI (Google Gemini) textual outputs as untrusted input candidate drafts.
  - Programmatically verifies each cited entity (`EVENT`, `OBJECT_TRACK`, `CAMERA`, `VIDEO`, `OBSERVATION`, `EVIDENCE`) against actual physical database tables using foreign key constraints and primary keys.
  - Verifies source timestamp alignment within a strict configurable tolerance ($|\Delta t| \le 2.0\text{s}$), catching temporal distortions and hallucinated timelines.
- **4-Tier Epistemic Taxonomy**:
  - Statements are strictly partitioned and visually badged into four epistemic categories:
    1. `OBSERVATION`: Direct physical sensor or CCTV footage observation.
    2. `CV_DETECTION`: Algorithmic computer vision detection or tracker trajectory result.
    3. `MODEL_INTERPRETATION`: Machine learning inference, cognitive extrapolation, or reasoning hypothesis.
    4. `HUMAN_ANNOTATION`: Field analyst or command review correction.
- **Indirect Prompt Injection (IPI) Defense**:
  - `ReportInputSanitizer` neutralizes adversarial delimiter payloads, prompt breakouts, and jailbreak commands embedded in CCTV stream metadata, camera names, and analyst notes.
  - Wraps untrusted metadata strings in explicit XML tag enclosures (`<untrusted_metadata>`) prior to model prompt formulation.
- **Provenance-Grounded Graph Registration**:
  - Generates bidirectional `DOCUMENTED_IN` links between the `Report` node and `Incident` in the Phase 4 Event Graph with `provenance_type="DERIVED_SYNTHESIS"`.
- **Human Corrections & Chain of Custody Approval Workflow**:
  - Real-time statement editing with preserved immutable audit history (`REPORT_GENERATED`, `HUMAN_CORRECTION`, `REVIEW_APPROVE`, `REVIEW_REQUEST_REVISIONS`, `REVIEW_REJECT`).
  - Command approval workflow transitioning dossiers across `DRAFT`, `PENDING_REVIEW`, `APPROVED`, and `REJECTED`.
- **Forensic PDF Export Engine with Cryptographic Digest**:
  - ReportLab-powered document generation with legal-grade formatting, color-coded statement tags, conflict callout boxes, and physical evidence inventory registers.
  - Computes and records authoritative SHA-256 cryptographic digests on all generated dossiers.

### 2.8 Edge Operation and Store-and-Forward Subsystem (Phase 8 Architecture)
- **Crash-Safe SQLite WAL Local Buffer (`data/edge_buffer.db`)**:
  - Standalone SQLite engine operating in Write-Ahead Logging mode (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`).
  - Spools events, detections, and evidence references locally during network blackouts, satellite interruptions, or server outages.
  - Retains buffer queue across cold power cuts and process crash-restarts.
- **Zero Temporal Skew Pipeline**:
  - Strictly decouples edge occurrence time ($t_{\text{detected}}$) from central arrival time ($t_{\text{synced}}$).
  - Assigns `SecurityEvent.timestamp = detected_at` and `SecurityEvent.synced_at = now()`, preventing synchronization delays from distorting chronological incident timelines.
- **Idempotent Ingestion Protocol**:
  - Deterministic client UUIDs (`client_event_id`, `client_evidence_id`) enforced via unique PostgreSQL database indexes.
  - Idempotently acknowledges and skips duplicate batches during network packet retransmissions, guaranteeing zero duplicate alerts.
- **Priority-Aware 500 MB Quota Retention Controller**:
  - `EdgeStorageManager` enforces a configurable $500\text{ MB}$ local storage ceiling.
  - Prunes expired synced media ($> 7\text{ days}$) and performs FIFO pruning on `LOW` and `MEDIUM` priority snapshots under disk pressure ($> 90\%$).
  - Strictly preserves `HIGH` and `CRITICAL` perimeter breach snapshots and permanent metadata.
- **Honest Offline AI Status Protocol (Zero Fabrication Mandate)**:
  - When network is unreachable, Generative AI cognitive analyses are assigned `PENDING_NETWORK` status.
  - When running in disconnected edge mode without cloud keys, analyses are assigned `UNAVAILABLE` status.
  - Strictly prevents hallucinated threat summaries or fabricated cognitive conclusions during communication outages.
- **Atomic Per-Record Transaction Engine**:
  - Commits database transactions per event, ensuring partial synchronization during fleeting reconnection windows without rolling back successfully ingested records.
  - Implements bounded exponential backoff ($1.0\text{s} \to 30.0\text{s}$) and transitions poison-pill records to `QUARANTINED` status after 5 consecutive failures.

### 2.9 Surveillance Copilot & Modern Frontend Architecture (Phase 9)
- **Authorized Tool Execution Engine**:
  - Directs Gemini natural language questions to strictly typed, Pydantic-validated Python functions.
  - Strictly prohibits raw SQL execution, shell script evaluation, or dynamic code compilation.
  - Implements five operational query archetypes: camera telemetry summaries, unresolved evidence gaps, spatio-temporal zone bounds, report evidence audits, and provenance graph syntheses.
- **Two-Step Consequential Action Confirmation Protocol**:
  - Consequential actions (such as `escalate_incident` to Tactical QRT) return status `CONFIRMATION_REQUIRED` and a single-use token.
  - UI modal requires operator affirmation before dispatching `confirmed_action` to mutate database state and record an immutable audit entry.
  - Enforces Role-Based Access Control (rejects `VIEWER` role).
- **Responsive 9-Page Bright Palette Frontend**:
  - Professional white surfaces (`#FFFFFF`), light violet accents (`#7C5CFC`), subtle purple badges (`#F0EDFD`), and readable typography (`#211D2B`).
  - Nine core command modules: Overview & Health, Cameras & Sources, Video Monitoring, Detections & Tracks, Incident Graph, Gemini Reports, Surveillance Copilot, Offline Sync Status, and Audit & Settings.
  - Real HTML5 `<video>` range-seeking playback, interactive SVG zone polygon editing, and zero decorative stub buttons.

### 2.10 Evaluation, Reproducible Benchmarking & Invention Architecture (Phase 10)
- **Deterministic 100-Scenario Benchmark Harness (`app/evaluation/reproducible_benchmark.py`)**:
  - Configured with fixed random seed (`RANDOM_SEED = 20260930`) and strict chronological partitioning to guarantee zero test-data leakage.
  - Six operational evaluation categories: Daylight Nominal (15), Low-Light & Infrared (20), Severe Occlusion (20), Degraded Video (15), Network Partition (15), and Contradictory Observations (15).
  - Evaluates primary comparative baselines: `Baseline-1_RawDetector` (unfiltered single-frame detections), `Baseline-2_TrackerNoController` (motion tracking without graph or adaptive verification), and `Proposed_SentinelAI_Full`.
- **Four-Variant Component Ablation Engine**:
  - `Ablation_NoEventGraph`: Measures multi-sensor tracking and contradiction handling degradation when explicit provenance graph edges are disabled.
  - `Ablation_NoAdaptiveController`: Measures recall penalties under static confidence thresholds ($0.75$) without dynamic frame resampling.
  - `Ablation_NoCrossExaminer`: Quantifies generative hallucination rates when programmatic citation validation against relational database entities is removed.
  - `Ablation_NoEdgeBuffer`: Measures event loss and temporal skew when SQLite WAL spooling is disabled during network blackouts.
- **Machine-Readable Empirical Reporting Engine**:
  - Automatic export of comprehensive test findings to `backend/evaluation_results/benchmark_report.json`, `benchmark_summary.csv`, and `benchmark_raw_scenarios.csv`.
  - Real-time measurement of detection precision, recall, F1, false alarm rate (FAR), latency distributions (mean, P95, P99), API token consumption, citation validity rate, and event loss.
- **Honest Failure Mode Ledger**:
  - Explicitly registers real architectural boundary constraints: `FAIL-LOWLIGHT-TINY` (sub-30px targets in low-lux/IR), `FAIL-OCCLUSION-IDSWITCH` (Kalman covariance expansion beyond 45 frames), `FAIL-CONTROLLER-LATENCY` (high-resolution secondary inference tail latency), and `FAIL-UNCONSTRAINED-HALLUCINATION` (autoregressive LLM citation fabrication).
- **Formal Patent & Legal Invention Documentation**:
  - **Technical Invention Disclosure (TID-SENTINEL-2026-01)**: Structural blueprints, reduction to practice, alternative edge/cloud embodiments, and statutory Alice/Mayo / technical effect declarations.
  - **Patent Claim-Mapping Worksheet (CMW-SENTINEL-2026-01)**: Element-by-element mapping connecting Independent System Claim 1 ([1.0]–[1.5]) and Method Claim 11 ([11.0]–[11.6]) plus Dependent Claims 2–10 & 12–20 to specification sections, code files/line ranges, test metrics, and prior art technical differentiations (US20180247137A1, US10929705B2, US20210350172A1, US11551042B2, US20230196783A1, EP3745308A1).

---

## 3. Database Schema Entity Relationship

- **`User`**: Security personnel accounts with RBAC roles (`ADMIN`, `SECURITY_ANALYST`, `OPERATOR`, `VIEWER`).
- **`Camera`**: Surveillance sensor node with spatial zone and line definitions stored in JSONB.
- **`Video`**: Uploaded video files, codecs, frame rates, and processing states.
- **`Detection`**: Individual object bounding boxes, confidence scores, and frame references.
- **`ObjectTrack`**: Persistent multi-frame trajectories, dwell times, and velocity profiles.
- **`SecurityEvent`**: Classified threat events (`RESTRICTED_ZONE_ENTRY`, `LINE_CROSSING`, `LOITERING`).
- **`Alert`**: Triageable alerts with acknowledgement workflows.
- **`Incident`**: Aggregated case files linking events, alerts, evidence, and Gemini AI summaries.
- **`Evidence`**: Media pointers and SHA-256 checksums.
- **`AIAnalysis`**: Multimodal Gemini reasoning runs with grounded citations.
- **`Report`**: Generated PDF incident dossiers with SHA-256 hashes.
- **`AuditLog`**: Tamper-proof log of user operations.
- **`EventLink`**: Explicit typed graph edges linking incident entities (`OBSERVED_BY`, `DETECTED_IN`, `TRIGGERED`, `SUPPORTS`, `CONFLICTS_WITH`, `SUPERSEDES`, `FLAGS_MISSING`).
- **`EvidenceObservation`**: Field analyst assertions, contradictory sensor records, and missing telemetry intervals.
- **`VerificationLedgerRecord`**: Complete step-by-step decision audit logs, sufficiency scores, actions, and cost tracking.


