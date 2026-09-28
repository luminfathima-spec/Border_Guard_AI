import os
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the sentinel-ai root (two levels up from backend/app/core)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "SentinelAI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "sentinel_ai_super_secret_jwt_key_sih_2026_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql://sentinel:sentinel@localhost:5432/sentinelai"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # AI & Computer Vision
    YOLO_MODEL_PATH: str = "models/yolov8n.pt"
    CONFIDENCE_THRESHOLD: float = 0.45
    IOU_THRESHOLD: float = 0.45
    PROCESS_EVERY_N_FRAMES: int = 2
    LOITERING_THRESHOLD_SECONDS: int = 15

    # Google Gemini Intelligence Layer
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Storage & Paths (Resolved relative to BASE_DIR if not absolute)
    DATA_DIR: str = "data"
    UPLOAD_DIR: str = "data/uploads"
    PROCESSED_DIR: str = "data/processed"
    EVIDENCE_DIR: str = "data/evidence"
    SNAPSHOTS_DIR: str = "data/snapshots"
    MAX_UPLOAD_SIZE_MB: int = 500

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def get_absolute_path(self, relative_or_absolute: str) -> Path:
        p = Path(relative_or_absolute)
        if p.is_absolute():
            return p
        return BASE_DIR / relative_or_absolute


settings = Settings()
