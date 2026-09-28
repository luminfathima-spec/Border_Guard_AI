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
