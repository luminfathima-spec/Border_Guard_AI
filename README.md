<<<<<<< HEAD
# Border_Guard_AI
=======
# SentinelAI — AI-Based Intelligent Video Analytics Platform for Border Surveillance

**Smart India Hackathon (SIH) 2026 Platform Submission**

SentinelAI is an enterprise-grade, high-reliability video analytics and security intelligence platform designed for national border perimeters and high-security installations. Utilizing existing CCTV infrastructure, SentinelAI detects real-time spatial intrusions, virtual line crossings, loitering anomalies, automatically generates forensic snapshot/clip evidence, and leverages **Google Gemini** as an investigative cognitive reasoning layer.

---

## Key Features

1. **Deterministic Computer Vision Pipeline**:
   - High-throughput **YOLOv8** object detection (pedestrians, vehicles, animal classifications).
   - Multi-object tracking (**ByteTrack / IoU centroid matching**) maintaining persistent tracking IDs, dwell times, and velocity trajectories.
   - **Polygonal Zone Intrusion Engine**: Ray-casting algorithm evaluating arbitrary multi-vertex exclusion perimeters.
   - **Virtual Tripwire Line Engine**: Vector intersection algorithm detecting directional demarcation crossings.
   - **Loitering Detection Engine**: Dwell time accumulator identifying suspicious lingering targets.

2. **Automated Forensic Evidence Automation**:
   - Integrated **FFmpeg** service extracting keyframe snapshot JPEGs and 6-10s evidence MP4 clips around breach timestamps.
   - **SHA-256 Cryptographic Checksums** guaranteeing evidentiary integrity for legal chain of custody.

3. **Google Gemini Intelligence & Reasoning Layer**:
   - **Tactical Incident Summarization**: Synthesizes structured event telemetry into executive threat dossiers and operational recommendations.
   - **Interactive Analyst Copilot**: Natural-language Q&A assistant answering operator questions based on live database state.
   - **Audit-Ready Report Generator**: Generates formatted, printable investigation reports.

4. **Security Operations Center (SOC) Console**:
   - Sleek, high-density dark mode React 18 + TypeScript + Tailwind CSS dashboard.
   - Live multi-stream monitoring grid with target bounding overlays.
   - Interactive visual designer for drawing polygonal zones and tripwire lines directly onto camera coordinates.
   - Alert triage center with status transitions (NEW → ACKNOWLEDGED → INVESTIGATING → RESOLVED).
   - Forensic Evidence Vault with inline video player and checksum inspection.
   - Full Role-Based Access Control (RBAC): Admin, Security Analyst, Operator, Viewer.

---

## System Architecture

```
[Existing CCTV Feeds / Video Uploads]
                │
                ▼
      [FFmpeg Ingestion Engine]
                │
                ▼
   [OpenCV Frame Extraction & Sampling]
                │
                ▼
      [YOLOv8 Detection Engine]
                │
                ▼
     [ByteTrack Object Association]
                │
                ▼
    [Spatial Analytics: Zones & Lines]
                │
                ▼
     [Security Event Dispatcher]
        ├───> [PostgreSQL 17 Database]
        ├───> [FFmpeg Snapshot & Clip Generation]
        ├───> [Priority Alert Matrix]
        └───> [Incident Aggregator]
                     │
                     ▼ (Structured Telemetry Facts)
          [Google Gemini Reasoning Layer]
                     │
                     ▼
  [React 18 + TypeScript SOC Command Console]
```

---

## Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 16+ (or Docker)
- FFmpeg installed and in PATH

### 1. Database Setup
Ensure PostgreSQL is running on port 5432 with database `sentinelai`:
```bash
python scripts/init_db.py
python scripts/seed_db.py
```

### 2. Backend Startup
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at `http://localhost:8000/docs`.

### 3. Frontend Startup
```bash
cd frontend
npm install
npm run dev
```
Access the SOC Console at `http://localhost:5173`.

### 4. Docker Deployment
```bash
docker-compose up --build -d
```

---

## Demo Accounts

| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@sentinel.ai` | `AdminPassword123!` |
| **Security Analyst** | `analyst@sentinel.ai` | `AnalystPassword123!` |
| **Operator** | `operator@sentinel.ai` | `OperatorPassword123!` |

---

## SIH 2026 Jury Demonstration Walkthrough

1. **Login & Dashboard Overview**:
   - Sign in as `admin@sentinel.ai`.
   - Inspect the SOC dashboard KPIs (Active Cameras, Alerts, Incident Dossiers, Sensor Uptime).
2. **Camera & Zone Configuration**:
   - Navigate to **Cameras & Zones**.
   - Select a camera (e.g. `CAM-NP-01`) and click **Configure Zones & Tripwires**.
   - Use the visual canvas to draw a 4-point exclusion zone or 2-point tripwire.
3. **Ingesting Surveillance Footage**:
   - Navigate to **Live Monitoring** or **Dashboard** and click **Upload / Ingest Video Feed**.
   - Select `data/uploads/sample_border_surveillance.mp4` and associate it with `CAM-NP-01`.
   - Click **Ingest & Process Analytics**.
   - Observe real-time YOLO detection, track ID assignment, restricted zone entry detection, and automated evidence extraction.
4. **Alert Triage & Forensic Evidence**:
   - Navigate to **Alert Center** and acknowledge new intrusion alerts.
   - Navigate to **Evidence Vault** to play generated short video clips and verify SHA-256 hashes.
5. **Google Gemini Intelligence & AI Copilot**:
   - Navigate to **Incidents & Cases** and click **Regenerate AI Summary**.
   - Observe Gemini reasoning on structured telemetry facts.
   - Click **Generate Report** to view and print the investigation dossier.
   - Navigate to **AI Analyst Copilot** and ask questions: *"Summarize today's highest priority border breaches."*
>>>>>>> eda35e1 (feat: complete SentinelAI-X real video surveillance & edge AI analytics platform)
