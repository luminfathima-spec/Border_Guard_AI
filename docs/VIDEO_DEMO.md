# SentinelAI-X Real Video Analytics & Surveillance Pipeline Guide

**AI-Based Intelligent Video Analytics Platform for Border Surveillance using Existing CCTV Infrastructure (SIH 2026)**

---

## 1. Overview

SentinelAI-X includes an end-to-end computer vision and spatial analytics pipeline that processes **real physical surveillance video files** (.mp4, .webm, .mov, .mkv) with **Ultralytics YOLOv8 object detection**, **ByteTrack persistent multi-object tracking**, **geospatial polygon/line crossing verification**, and **H.264 video transcoding** with burned-in tactical telemetry HUD and bounding boxes.

---

## 2. Architecture & Processing Flow

```
[ CCTV / Drone Video Source (.mp4) ]
               │
               ▼
[ Video Ingestion & Format Validation ]
               │
               ▼
[ Frame-by-Frame Streaming & Extraction (OpenCV) ]
               │
               ▼
[ Ultralytics YOLOv8 Edge Object Detection ]
  (Detects: Person, Car, Truck, Bus, Motorcycle with confidence scores)
               │
               ▼
[ Persistent Multi-Object Tracking (ByteTrack / Kalman Filter) ]
  (Assigns unique track IDs across frames: PERSON #1, CAR #2)
               │
               ▼
[ Spatial Analytics Engine (Ray-Casting Polygon & Vector Intersection) ]
  (Evaluates 150m Exclusion Buffer Strip & Virtual Demarcation Tripwires)
               │
               ├────────────────────────────────────────┐
               ▼                                        ▼
[ Tactical Video Overlay Annotation ]        [ Structured Security Events & Incidents ]
  - High-contrast Bounding Boxes               - Real SecurityEvent in DB
  - Tracking ID & Class Badges                 - Critical Breach Alert in DB
  - Semi-transparent Zone Boundaries           - Active Incident Dossier in DB
  - Telemetry HUD Watermark                    - Cryptographic SHA-256 Snapshots
               │                                        │
               ▼                                        ▼
[ FFmpeg H.264 Browser Transcoding ]         [ Real-time Dashboard Synchronization ]
  (`-vcodec libx264 -pix_fmt yuv420p`)        - Active Incidents Queue (+1)
               │                                - Live Event Stream
               ▼                                - Surveillance Video Matrix Playback
[ HTML5 <video> Native Playback in UI ]
```

---

## 3. How to Start the Application

### A. Start the FastAPI Backend
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Database**: Connects to PostgreSQL if available, or automatically fails over to zero-latency local SQLite with auto-seeded default credentials.

### B. Start the React/Vite Frontend
```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```
- **Frontend Command Center**: [http://localhost:5173](http://localhost:5173)

---

## 4. Default Operator Credentials

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **General Commander (Admin)** | `admin@sentinel.ai` | `AdminPassword123!` | Full Operations & Sector Administration |
| **Senior AI Analyst** | `analyst@sentinel.ai` | `AnalystPassword123!` | Incident Dossiers & Gemini Threat Reasoning |
| **Field Operator** | `operator@sentinel.ai` | `OperatorPassword123!` | Live Monitoring & Incident Escalation |

*(One-click demo login buttons are available directly on the login screen).*

---

## 5. How to Ingest and Demonstrate Surveillance Footage

1. Log into the SentinelAI Command Center.
2. On the Top Page Header, click the purple **"Ingest Surveillance Video"** button.
3. In the modal dialog, select either:
   - **Demo Scenarios (Instant AI)**:
     - **Sector 07 Northern Buffer Zone Intrusion**: Demonstrates a target crossing the perimeter demarcation line into the 150m restricted exclusion buffer strip.
     - **Sector 04 Eastern Gate Patrol & Vehicle Transit**: Demonstrates routine patrol vehicle and guard movement.
   - **Upload Custom CCTV File**: Select any local `.mp4`, `.webm`, `.mov`, or `.mkv` video file from your computer.
4. Select the target sensor node (e.g. `CAM-NP-01`).
5. Click **"Ingest & Run AI Pipeline"**.
6. Watch the real-time multi-stage pipeline:
   - `1. Ingestion & Validation` → `2. YOLOv8 Detection` → `3. Spatial Buffer Analysis` → `4. H.264 Transcoding`
7. Click **"Deploy Processed Feed on Dashboard"**.
8. The Surveillance Video Matrix and Live Surveillance feeds immediately stream the real processed video with bounding boxes, tracking labels, and breach alerts!

---

## 6. How AI Detection, Tracking & Incidents Work

- **YOLOv8 Edge Inference**: Runs pretrained weights on surveillance frames with confidence threshold filtering.
- **Persistent Tracking**: Objects retain consistent track IDs across consecutive frames (`PERSON #1`, `CAR #2`).
- **Spatial Zone Rules**:
  - **Restricted Buffer Strip**: Ray-casting algorithm tests if the tracked target's centroid is inside the restricted polygon.
  - **Virtual Tripwires**: Evaluates 2D cross-product line segment intersection between the target's previous and current position vectors.
- **Incident Escalation**: High/Critical breaches automatically create an Incident record (e.g. `INC-20260830-0001`), an Alert record, and extract cryptographic evidence snapshots into the SOC Evidence Vault.
- **AI Threat Reasoning**: Incident dossiers are integrated with Google Gemini cognitive reasoning to summarize tactical threat level and generate recommended Quick Reaction Team (QRT) response steps.
