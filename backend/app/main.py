import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.db.database import engine, Base, SessionLocal
from app.db.init_db import init_db
from app.api.routes import (
    health, auth, users, cameras, videos, detections,
    events, alerts, incidents, evidence, analytics, ai
)

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.APP_ENV}]...")
    for dir_path in [
        settings.get_absolute_path(settings.UPLOAD_DIR),
        settings.get_absolute_path(settings.PROCESSED_DIR),
        settings.get_absolute_path(settings.EVIDENCE_DIR),
        settings.get_absolute_path(settings.SNAPSHOTS_DIR),
        settings.get_absolute_path("models"),
        settings.get_absolute_path("data"),
        settings.get_absolute_path("demo_videos"),
    ]:
        os.makedirs(dir_path, exist_ok=True)
    logger.info("Runtime storage directories initialized.")

    # Initialize tables and seed default users/cameras
    try:
        import app.models.user
        import app.models.camera
        import app.models.video
        import app.models.detection
        import app.models.event
        import app.models.alert
        import app.models.incident
        import app.models.evidence
        import app.models.audit

        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            init_db(db)
        finally:
            db.close()
        logger.info("Database schema and default authentication credentials initialized.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}", exc_info=True)

    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Based Intelligent Video Analytics Platform for Border Surveillance (SIH 2026)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers for Security & Sanitized Responses
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    logger.warning(f"Validation error on {request.url.path}: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Input validation error", "errors": errors},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal surveillance platform error occurred. Please contact SOC operations."},
    )

# Mount static media directories
evidence_dir = settings.get_absolute_path(settings.EVIDENCE_DIR)
snapshots_dir = settings.get_absolute_path(settings.SNAPSHOTS_DIR)
processed_dir = settings.get_absolute_path(settings.PROCESSED_DIR)
upload_dir = settings.get_absolute_path(settings.UPLOAD_DIR)
demo_dir = settings.get_absolute_path("demo_videos")

os.makedirs(evidence_dir, exist_ok=True)
os.makedirs(snapshots_dir, exist_ok=True)
os.makedirs(processed_dir, exist_ok=True)
os.makedirs(upload_dir, exist_ok=True)
os.makedirs(demo_dir, exist_ok=True)

app.mount("/static/evidence", StaticFiles(directory=str(evidence_dir)), name="evidence")
app.mount("/static/snapshots", StaticFiles(directory=str(snapshots_dir)), name="snapshots")
app.mount("/static/processed", StaticFiles(directory=str(processed_dir)), name="processed")
app.mount("/static/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")
app.mount("/static/demo", StaticFiles(directory=str(demo_dir)), name="demo")

# Register API Routers
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(cameras.router, prefix=settings.API_V1_PREFIX)
app.include_router(videos.router, prefix=settings.API_V1_PREFIX)
app.include_router(detections.router, prefix=settings.API_V1_PREFIX)
app.include_router(events.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts.router, prefix=settings.API_V1_PREFIX)
app.include_router(incidents.router, prefix=settings.API_V1_PREFIX)
app.include_router(evidence.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai.router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API. Visit /docs for OpenAPI documentation.",
        "version": settings.APP_VERSION,
        "status": "online",
    }
