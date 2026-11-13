# SentinelAI — REST API Reference

Base API Path: `/api/v1`

---

## 1. Authentication (`/api/v1/auth`)

### `POST /auth/login`
Authenticates an operator and issues a JWT token.
- **Request Body**:
  ```json
  {
    "email": "admin@sentinel.ai",
    "password": "AdminPassword123!"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in_minutes": 1440,
    "user": {
      "id": 1,
      "name": "Commander R. Sharma",
      "email": "admin@sentinel.ai",
      "role": "ADMIN"
    }
  }
  ```

### `GET /auth/me`
Retrieves authenticated user profile. Requires `Authorization: Bearer <token>`.

---

## 2. Cameras & Surveillance Nodes (`/api/v1/cameras`)

### `GET /cameras`
Lists all surveillance camera nodes. Supports `?status=ONLINE&zone=Sector4`.

### `POST /cameras`
Registers a new camera feed (Admin/Analyst only).

### `PATCH /cameras/{id}`
Updates camera coordinates, restricted polygon zones, or virtual lines.
- **Request Body**:
  ```json
  {
    "restricted_zones": [
      {
        "id": "zone-1",
        "name": "Buffer Strip",
        "polygon": [{"x": 0.1, "y": 0.2}, {"x": 0.9, "y": 0.2}, {"x": 0.9, "y": 0.8}, {"x": 0.1, "y": 0.8}],
        "alert_severity": "HIGH"
      }
    ]
  }
  ```

---

## 3. Video Analytics Pipeline (`/api/v1/videos`)

### `POST /videos/upload`
Uploads a surveillance video (`multipart/form-data`).
- Form field: `file` (binary)
- Form field: `camera_id` (optional integer)

### `POST /videos/{id}/process`
Runs the YOLOv8 detection, tracking, zone analysis, and alert generation pipeline.

---

## 4. Security Events & Alerts (`/api/v1/events` & `/api/v1/alerts`)

### `GET /events`
Lists detected security events with filters `?event_type=...&severity=...&camera_id=...`.

### `GET /alerts`
Lists operational alerts.

### `PATCH /alerts/{id}`
Updates alert status (`ACKNOWLEDGED`, `INVESTIGATING`, `RESOLVED`, `DISMISSED`).

---

## 5. Google Gemini AI Intelligence (`/api/v1/ai`)

### `POST /ai/incidents/{id}/summarize`
Generates tactical AI threat assessment and suggested containment actions.

### `POST /ai/assistant/chat`
Interactive natural language copilot answering surveillance queries based on live database state.

### `POST /ai/incidents/{id}/report`
Generates a formal Markdown and PDF investigation dossier.

---

## 6. Event Graph & Provenance Chain (`/api/v1/incidents`)

### `GET /incidents/{id}/graph`
Retrieves the full evidence graph for an incident including nodes, typed edges, epistemic classifications (`DIRECT_OBSERVATION`, `INFERRED_ASSOCIATION`), conflict counts, and missing evidence gaps.

### `POST /incidents/{id}/graph/links`
Creates an explicit typed relationship between two entities (`OBSERVED_BY`, `DETECTED_IN`, `TRIGGERED`, `SUPPORTS`, `CONFLICTS_WITH`, `SUPERSEDES`, `FLAGS_MISSING`).
- Validates that source and target records physically exist, preventing dangling references.
- Checks for duplicate edges.
- Enforces mandatory `creation_reason`.

### `GET /incidents/{id}/evidence-chain`
Retrieves the complete, multi-tier chain of custody from physical camera sensor through video recordings, frame detections, object tracks, boundary crossing events, snapshot evidence, Gemini cognitive reasoning, and final reports.
- Verifies that every step resolves to a real stored database record.
- Returns cryptographic SHA-256 digests for legal custody verification.

### `POST /incidents/{id}/observations`
Records field analyst assertions, contradictory sensor observations, or missing data intervals.

### `POST /incidents/{id}/observations/{obs_id}/supersede`
Preserves history instead of silently overwriting earlier observations. Marks the older observation as `SUPERSEDED` and creates a `SUPERSEDES` graph edge.

### `POST /incidents/{id}/graph/validate`
Validates graph integrity, identifying dangling references, out-of-order timestamps, duplicate edges, and circular dependency loops.

### `POST /incidents/{id}/graph/auto-synthesize`
Automatically synthesizes provenance links from all entities linked to the incident in the database.

---

## 7. Google Gemini Generative AI Intelligence (`/api/v1/ai`)

### `POST /ai/incidents/{incident_id}/analyze`
Executes complete Phase 5 multimodal Gemini reasoning on an incident:
- Selects event-triggered keyframes ($\pm 1.5\text{s}$ context frames compressed to JPEG).
- Formulates versioned prompt (`PROMPT_VERSION = "2026.04.1"`) with sanitized facts.
- Enforces rigid Pydantic JSON schema (`IncidentAnalysisResponse`).
- Executes deterministic **CrossExaminer** verification against PostgreSQL tables to detect and quarantine hallucinated camera, event, or evidence citations.
- Persists record in `ai_analyses` table and registers an `ANALYZED_BY` edge in the Event Graph.

### `GET /ai/incidents/{incident_id}/analyses`
Retrieves chronological audit trail of all Gemini analyses run for the specified incident, including prompt versions, token counts, execution latencies, and grounding verification scores.

### `POST /ai/incidents/{incident_id}/summarize`
Generates tactical threat summary and operational recommendations based on structured telemetry (backward-compatible endpoint).

### `POST /ai/assistant/chat`
Interactive natural-language query assistant for security analysts backed by live surveillance telemetry, camera operational statuses, and active alerts.

### `POST /ai/incidents/{incident_id}/report`
Generates a formal, printable investigation report with event timelines, threat assessment, forensic register, and evidence chain.

---

## 8. Adaptive Evidence Verification Controller (`/api/v1/verification`)

### `POST /verification/evaluate-event`
Evaluates an event using the multi-modal Evidentiary Sufficiency Evaluator and executes adaptive verification steps:
- **Request Body (`EvaluateEventRequest`)**:
  ```json
  {
    "event_id": 101,
    "incident_id": 12,
    "config": {
      "min_sufficiency_threshold": 0.70,
      "unresolved_threshold": 0.40,
      "max_local_resample_frames": 10,
      "max_gemini_calls": 1,
      "max_latency_budget_ms": 3000.0,
      "allow_gemini_reasoning": true
    }
  }
  ```
- **Response**: `200 OK` (`VerificationEvaluationResult`)
  ```json
  {
    "event_id": 101,
    "incident_id": 12,
    "verdict": "VERIFIED_BREACH",
    "final_sufficiency_score": 0.88,
    "is_unresolved": false,
    "is_conflict_detected": false,
    "frames_examined": 15,
    "gemini_calls_made": 0,
    "estimated_cost_usd": 0.0,
    "execution_time_ms": 142.5,
    "summary_explanation": "Event verified with high multi-modal sufficiency.",
    "ledger": [
      {
        "timestamp": "2026-09-28T16:00:00Z",
        "action": "EVALUATE_INITIAL_SUFFICIENCY",
        "input_state": { "initial_sufficiency": 0.75 },
        "rationale": "Sufficient initial evidence; proceeding directly to verification.",
        "sufficiency_score": 0.75
      }
    ]
  }
  ```
- **Behavioral Guarantees**:
  - Assigns `UNRESOLVED` if data gaps or camera corruption exhaust the budget without meeting threshold.
  - Automatically invokes local dense frame burst before incurring cloud LLM API calls.
  - Strictly enforces the Safety Mandate: sanitizes any classification to prevent categorizing human subjects as hostile or malicious.

### `GET /verification/ledgers/{event_id}`
Retrieves the immutable audit ledger for all verification actions and decisions performed on a security event.
- **Path Parameter**: `event_id` (integer)
- **Response**: `200 OK` (`List[VerificationLedgerResponse]`)

### `POST /verification/benchmark`
Runs an automated, reproducible comparative evaluation of **Mode A (Baseline Fixed Sampling)** vs. **Mode B (Adaptive Controller)** and component ablations.
- **Request Body (`BenchmarkRunRequest`)**:
  ```json
  {
    "num_episodes": 40,
    "split": "test",
    "run_ablations": true
  }
  ```
- **Response**: `200 OK` (`BenchmarkComparisonResponse`)
  Returns precision, recall, false positive rate, missed event rate, latency, frames examined, Gemini API calls, cost, and unresolved rates across both modes and all 3 ablation conditions.

---

## 9. Evidence-Grounded Reports & PDF Dossiers (`/api/v1/reports`)

### `POST /reports/incidents/{incident_id}/generate`
Generates a structured, evidence-grounded incident dossier with programmatic citation validation against database entities and indirect prompt injection defense.
- **Path Parameter**: `incident_id` (integer)
- **Request Body (`ReportGenerateRequest`)**:
  ```json
  {
    "custom_instructions": "Focus on Sector 4 perimeter breach timeline",
    "force_mock": false,
    "model_name": "gemini-2.5-flash"
  }
  ```
- **Response**: `200 OK` (`ReportResponse`)
  Returns chronological factual statements with 4-tier epistemic classification (`OBSERVATION`, `CV_DETECTION`, `MODEL_INTERPRETATION`, `HUMAN_ANNOTATION`), citation validation status (`VERIFIED`, `FLAGGED_UNSUPPORTED`, `FLAGGED_TIMESTAMP_MISMATCH`, `FLAGGED_NONEXISTENT`), conflicting observations, missing data gaps, containment recommendations, and SHA-256 cryptographic PDF digest.

### `GET /reports/{id}`
Retrieves a specific incident investigation dossier by report ID.
- **Path Parameter**: `id` (integer)
- **Response**: `200 OK` (`ReportResponse`)

### `GET /reports/incidents/{incident_id}`
Lists all historical reports and dossiers generated for a specific incident.
- **Path Parameter**: `incident_id` (integer)
- **Response**: `200 OK` (`List[ReportResponse]`)

### `PATCH /reports/{id}/statements/{statement_id}`
Applies an analyst human correction to a specific factual statement. Transitions statement type to `HUMAN_ANNOTATION`, preserves previous text, re-renders the PDF dossier with updated signature lines, and records an immutable audit entry.
- **Path Parameters**: `id` (report ID), `statement_id` (statement ID)
- **Request Body (`ReportCorrectionRequest`)**:
  ```json
  {
    "corrected_text": "Target identified as authorized border maintenance crew with work permit #402.",
    "analyst_comment": "Verified against duty roster and biometric checkpoint sign-in log."
  }
  ```
- **Response**: `200 OK` (`ReportResponse`)

### `POST /reports/{id}/review`
Executes an operational review action on an incident dossier (`APPROVE`, `REQUEST_REVISIONS`, `REJECT`).
- **Path Parameter**: `id` (integer)
- **Request Body (`ReportReviewRequest`)**:
  ```json
  {
    "action": "APPROVE",
    "reviewer_comments": "Reviewed CCTV keyframes and validated maintenance roster. Incident cleared."
  }
  ```
- **Response**: `200 OK` (`ReportResponse`)

### `GET /reports/{id}/export-pdf`
Streams the evidentiary-grade PDF dossier with cryptographic SHA-256 integrity digest, color-coded statement tags, and chain-of-custody signature blocks.
- **Path Parameter**: `id` (integer)
- **Response**: `200 OK` (`application/pdf`)

### `GET /reports/{id}/audit-history`
Retrieves the complete immutable audit trail of generation, human corrections, and review decisions for the dossier.
- **Path Parameter**: `id` (integer)
- **Response**: `200 OK` (`List[AuditHistoryEntry]`)

---

## 10. Edge Operation and Store-and-Forward APIs

### `GET /edge/status`
Retrieves real-time edge node telemetry, network connectivity state, local SQLite buffer queue metrics, and disk quota consumption.
- **Response**: `200 OK` (`EdgeStatusResponse`)
  ```json
  {
    "edge_node_id": "EDGE-SECTOR4-NODE-01",
    "network_state": "ONLINE",
    "last_state_change": "2026-09-30T19:45:00Z",
    "offline_reason": null,
    "buffer_stats": {
      "total_buffered_events": 42,
      "pending_sync_count": 0,
      "synced_count": 42,
      "quarantined_count": 0,
      "pending_evidence_count": 0,
      "oldest_pending_timestamp": null,
      "db_file_size_bytes": 49152
    },
    "disk_metrics": {
      "total_bytes": 1000204886016,
      "free_bytes": 542388224000,
      "used_bytes": 457816662016,
      "used_percent": 45.77,
      "buffer_size_bytes": 14897152,
      "buffer_size_mb": 14.21,
      "max_quota_mb": 500.0,
      "quota_utilization_percent": 2.84,
      "is_warning": false,
      "is_quota_breached": false
    }
  }
  ```

### `POST /edge/network-state`
Simulates or sets edge network operational states (`ONLINE`, `OFFLINE`, `DEGRADED`) for resilience drills, blackout tests, and electronic countermeasure evaluations.
- **Request Body (`NetworkStateUpdateRequest`)**:
  ```json
  {
    "state": "OFFLINE",
    "reason": "Operator-initiated edge blackout resilience drill"
  }
  ```
- **Response**: `200 OK` (`EdgeStatusResponse`)

### `POST /edge/sync`
Triggers store-and-forward reconciliation of pending buffered edge events and associated evidence to the central PostgreSQL database. Enforces zero temporal skew and idempotent deduplication.
- **Request Body (`SyncTriggerRequest`)**:
  ```json
  {
    "batch_size": 100,
    "force_sync": false
  }
  ```
- **Response**: `200 OK` (`SyncResponse`)
  ```json
  {
    "session_id": "SYNC-1775043820-4a8b2c",
    "status": "SUCCESS",
    "events_synced": 15,
    "evidence_synced": 15,
    "duplicates_prevented": 0,
    "conflicts_resolved": 0,
    "bytes_transferred": 2048576,
    "duration_ms": 184,
    "errors_count": 0,
    "remaining_pending": 0,
    "message": null
  }
  ```

### `GET /edge/buffer/events`
Inspects pending detection events currently spooled in the local edge SQLite WAL buffer.
- **Query Parameter**: `limit` (integer, default: 50)
- **Response**: `200 OK` (`List[BufferedEventItem]`)

### `POST /edge/buffer/purge`
Executes local edge storage retention policy and priority-aware pruning. Deletes expired low-priority snapshots while protecting `HIGH` and `CRITICAL` breach media.
- **Response**: `200 OK` (`PurgeResponse`)
  ```json
  {
    "files_deleted": 8,
    "bytes_freed": 12582912,
    "bytes_freed_mb": 12.0,
    "remaining_buffer_mb": 18.4,
    "status": "QUOTA_COMPLIANT"
  }
  ```

### `POST /edge/benchmark`
Executes an automated empirical recovery benchmark: simulates network blackout, generates $N$ synthetic events, reboots buffer connection, restores connectivity, reconciles records, and verifies zero event loss and duplicate prevention.
- **Request Body (`EdgeBenchmarkRequest`)**:
  ```json
  {
    "num_events": 20,
    "simulate_restart": true
  }
  ```
- **Response**: `200 OK` (`EdgeBenchmarkResponse`)
  ```json
  {
    "test_name": "Edge Store-and-Forward Recovery & Zero Loss Benchmark",
    "total_events_generated": 20,
    "events_recovered": 20,
    "event_loss_pct": 0.0,
    "duplicate_events_prevented": 1,
    "duplicate_detection_accuracy_pct": 100.0,
    "recovery_time_ms": 214,
    "mean_sync_delay_ms": 10240.0,
    "timestamp_preservation_accuracy_pct": 100.0,
    "evidence_hash_match_pct": 100.0,
    "buffer_db_size_bytes": 49152,
    "status": "PASSED"
  }
  ```

---

## 9. Surveillance Copilot & Operational Audit API (Phase 9)

### 9.1 POST `/api/v1/ai/copilot/chat`
Conversational operational interface powered by Gemini 2.5 Flash and authorized tool dispatching. Supports two-step confirmation for consequential actions.

- **Security**: Bearer JWT token required. Consequential actions require `SECURITY_ANALYST` or `ADMIN` role.
- **Request Body**:
  ```json
  {
    "message": "Find events associated with Sector 4 in the last 24 hours",
    "conversation_history": [
      {"role": "user", "content": "Hello"},
      {"role": "assistant", "content": "How can I assist?"}
    ],
    "camera_id": 1,
    "incident_id": 1,
    "confirmed_action": null
  }
  ```
- **Response**: `200 OK` (`CopilotChatResponse`)
  ```json
  {
    "response": "### Spatio-Temporal Query: Sector 4 (Last 24 Hours)...",
    "tool_calls": [
      {
        "tool_name": "find_events_by_zone_and_time",
        "arguments": {"zone": "Sector 4", "hours_ago": 24},
        "result": {"zone": "Sector 4", "total_events": 3},
        "status": "SUCCESS",
        "execution_time_ms": 14
      }
    ],
    "pending_confirmation": null,
    "suggested_queries": [
      "Summarize recorded events from camera 1",
      "Show incidents with unresolved evidence"
    ],
    "model_used": "gemini-2.5-flash"
  }
  ```

### 9.2 GET `/api/v1/audit/logs`
Retrieves immutable cryptographic system audit log records tracking operator actions, report changes, security reviews, and configuration updates.

- **Query Parameters**:
  - `action` (optional string): Filter by action name substring (e.g. `LOGIN`, `REPORT`, `ESCALATE`).
  - `resource_type` (optional string): Filter by target resource (e.g. `REPORT`, `INCIDENT`, `SYSTEM`).
  - `limit` (default: 100, max: 500)
  - `offset` (default: 0)
- **Response**: `200 OK` (`List[AuditLogResponse]`)

### 9.3 GET `/api/v1/audit/settings`
Retrieves system environment specifications, current model settings, edge parameters, and retention constraints.

- **Response**: `200 OK` (`SystemSettingsResponse`)
  ```json
  {
    "app_name": "SentinelAI",
    "app_version": "2.0.0",
    "app_env": "production",
    "edge_mode": false,
    "edge_node_id": "EDGE-BORDER-01",
    "edge_buffer_max_disk_mb": 500,
    "edge_buffer_retention_days": 7,
    "gemini_model": "gemini-2.5-flash",
    "max_upload_size_mb": 500,
    "max_video_duration_seconds": 1800,
    "total_audit_logs_count": 142
  }
  ```

### 9.4 POST `/api/v1/audit/settings`
Updates operational parameters (e.g., edge buffer retention threshold or sync batch size) and records an immutable audit log entry.

- **Request Body**:
  ```json
  {
    "edge_buffer_retention_days": 14,
    "edge_sync_batch_size": 100
  }
  ```
- **Response**: `200 OK` (`SystemSettingsResponse`)
