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

### 2.4 Google Gemini Intelligence Layer
- Strict separation between **deterministic detection facts** and **generative cognitive reasoning**.
- Structured JSON telemetry is injected into Gemini prompts to prevent hallucination.
- Provides executive tactical summaries, probability analysis, and step-by-step operational recommendations.

---

## 3. Database Schema Entity Relationship

- **`User`**: Security personnel accounts with RBAC roles (`ADMIN`, `SECURITY_ANALYST`, `OPERATOR`, `VIEWER`).
- **`Camera`**: Surveillance sensor node with spatial zone and line definitions stored in JSONB.
- **`Video`**: Uploaded video files, codecs, frame rates, and processing states.
- **`Detection`**: Individual object bounding boxes, confidence scores, and frame references.
- **`SecurityEvent`**: Classified threat events (`RESTRICTED_ZONE_ENTRY`, `LINE_CROSSING`, `LOITERING`).
- **`Alert`**: Triageable alerts with acknowledgement workflows.
- **`Incident`**: Aggregated case files linking events, alerts, evidence, and Gemini AI summaries.
- **`Evidence`**: Media pointers and SHA-256 checksums.
- **`AuditLog`**: Tamper-proof log of user operations.
