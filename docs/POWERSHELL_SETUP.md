# SentinelAI — Windows PowerShell Local Development Setup Guide

**Document Version:** 1.0.0  
**Target Environment:** Windows 10 / Windows 11 / Windows Server (PowerShell 5.1 / PowerShell 7+)  
**Backend Stack:** Python 3.11+, FastAPI, SQLAlchemy, Alembic, PostgreSQL 17, Docker Compose, FFmpeg  

---

## 1. System Prerequisites

Ensure the following tools are installed on your Windows workstation:

1. **Python 3.11+**:
   Verify in PowerShell:
   ```powershell
   python --version
   ```
2. **Git for Windows**:
   ```powershell
   git --version
   ```
3. **FFmpeg for Windows**:
   Required for keyframe extraction and clipped evidence video generation:
   ```powershell
   ffmpeg -version
   ```
   *If missing, install via winget:*
   ```powershell
   winget install Gyan.FFmpeg
   ```
4. **Docker Desktop (Optional for PostgreSQL)**:
   ```powershell
   docker --version
   ```

---

## 2. PowerShell Execution Policy Configuration

Windows restricts script execution by default. To allow virtual environment activation scripts (`Activate.ps1`) to run in your current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

*(Note: `-Scope Process` only applies the policy to your current terminal window, ensuring system security is unaffected).*

---

## 3. Clone Repository & Create Python Virtual Environment

Navigate to your workspace directory and set up an isolated Python environment:

```powershell
# Navigate into project directory
cd C:\Users\lumin\.gemini\antigravity\scratch\sentinel-ai

# Create virtual environment (.venv)
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Verify the active Python path is inside .venv
Get-Command python | Select-Object Source
```

Upgrade `pip` and install all required dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

---

## 4. Environment Variables Configuration

Copy the documented environment template to create your active `.env` file:

```powershell
Copy-Item .env.example .env
```

### Generating a Secure JWT Secret in PowerShell
For production or staging security, generate a cryptographically strong 48-character secret using PowerShell:

```powershell
$Secret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 48 | ForEach-Object {[char]$_})
Write-Host "Generated Secret Key: $Secret"
```

Edit `.env` using Notepad or your editor of choice:
```powershell
notepad .env
```
Key parameters to inspect:
* `SECRET_KEY`: Set to your generated secret key.
* `DATABASE_URL`: 
  * Docker PostgreSQL: `postgresql://sentinel:sentinel_dev_password@localhost:5432/sentinelai`
  * Local Windows PostgreSQL: `postgresql://sentinel:your_password@localhost:5432/sentinelai`
  * SQLite Fallback: If PostgreSQL is unreachable, SentinelAI automatically falls back to `data/sentinelai.db`.
* `GEMINI_API_KEY`: Enter your Google Gemini API key (optional for local CV; required for AI tactical summaries).

---

## 5. Starting the Database

You can run PostgreSQL using Docker Compose, a local Windows service, or rely on the automatic SQLite local fallback:

### Option A: Docker Compose PostgreSQL (Recommended)
```powershell
# Start only the PostgreSQL 17 container in the background
docker compose up -d postgres

# Verify container health
docker ps --filter "name=sentinel-postgres"
```

### Option B: Local Windows PostgreSQL Service
If you installed PostgreSQL directly on Windows:
```powershell
# Start PostgreSQL service (adjust version number if needed)
Start-Service postgresql-x64-17

# Verify port 5432 is listening
Test-NetConnection -ComputerName localhost -Port 5432
```

### Option C: Zero-Config Local Dev Fallback (SQLite)
If no PostgreSQL server is running, the SentinelAI database engine automatically detects the timeout and falls back to a high-performance local SQLite database (`data/sentinelai.db`) with full WAL logging.

---

## 6. Running Alembic Database Migrations

SentinelAI uses Alembic to manage database schema revisions reproducibly across both PostgreSQL and SQLite:

```powershell
cd backend

# Apply all migrations to the latest revision
python -m alembic upgrade head

# Check current revision status (should report head)
python -m alembic current
```

---

## 7. Starting the FastAPI Backend Server

Run the development server with live reload:

```powershell
# From the backend/ directory with .venv activated:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Verifying Service Health & Readiness in PowerShell
Open a new PowerShell window and execute:

```powershell
# 1. Test Liveness probe
Invoke-RestMethod http://localhost:8000/api/v1/health | Format-List

# 2. Test Readiness probe (checks DB, storage, and models)
Invoke-RestMethod http://localhost:8000/api/v1/health/ready | ConvertTo-Json -Depth 4
```

### Accessing Interactive OpenAPI Documentation
Open your browser to:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 8. Running Automated Unit Tests

Execute the automated test suite with detailed output:

```powershell
cd backend

# Run complete test suite
pytest -v

# Run only readiness tests
pytest tests/test_readiness.py -v

# Run model and repository relationship tests
pytest tests/test_models.py -v

# Run error schema tests
pytest tests/test_errors.py -v
```

---

## 9. Running Full Stack via Docker Compose

To run the entire platform (PostgreSQL, Backend, Frontend, and Nginx reverse proxy) in Docker:

```powershell
# Build and start all services
docker compose up --build -d

# Follow backend logs
docker compose logs -f backend

# Stop all services
docker compose down
```

---

## 10. Common PowerShell Troubleshooting

| Issue | Root Cause | PowerShell Resolution |
| :--- | :--- | :--- |
| `File ... Activate.ps1 cannot be loaded because running scripts is disabled` | PowerShell execution policy restriction | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `Port 8000 is already in use` | A previous uvicorn process is still running | `Get-Process python \| Stop-Process -Force` |
| `PostgreSQL connection failed ... Falling back to SQLite` | PostgreSQL service or Docker container is stopped | Run `docker compose up -d postgres` or start Windows PostgreSQL service. System continues safely on SQLite. |
| `ffmpeg: The term 'ffmpeg' is not recognized` | FFmpeg is not installed or not in system PATH | `winget install Gyan.FFmpeg`, then restart PowerShell. |
