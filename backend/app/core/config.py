import os
import re
from pathlib import Path
from typing import List, Union, Dict, Any, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import warnings

# Base directory for the sentinel-ai root (two levels up from backend/app/core)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

DEFAULT_DEV_SECRET = "sentinel_ai_super_secret_jwt_key_sih_2026_change_in_production"

KNOWN_INSECURE_SECRETS = {
    DEFAULT_DEV_SECRET.lower(),
    "changeme",
    "secret",
    "secretkey",
    "supersecret",
    "jwtsecret",
    "your_secret_key",
    "placeholder",
    "default",
    "admin",
    "password",
    "test",
    "testing",
    "12345678",
    "1234567890",
}

PLACEHOLDER_SUBSTRINGS = (
    "change_in_production",
    "changeme",
    "placeholder",
    "your_secret",
    "default_secret",
    "super_secret_jwt_key",
)

MINIMUM_SECRET_KEY_LENGTH = 32


class SecurityConfigurationError(ValueError):
    """Raised when security configuration is invalid or unsafe for the target environment."""
    pass


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
    SECRET_KEY: str = DEFAULT_DEV_SECRET
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    INITIAL_ADMIN_EMAIL: Optional[str] = None
    INITIAL_ADMIN_PASSWORD: Optional[str] = None
    ALLOW_DEFAULT_CREDENTIALS_IN_PRODUCTION: bool = False

    # Logging
    LOG_FORMAT: str = "text"  # "text" or "json"
    LOG_LEVEL: str = "INFO"

    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql://sentinel:sentinel@localhost:5432/sentinelai"
    DATABASE_CONNECT_TIMEOUT: int = 1
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
    MAX_VIDEO_DURATION_SECONDS: int = 3600  # Maximum video duration allowed (1 hour)
    RTSP_CONNECT_TIMEOUT_SECONDS: int = 5
    RTSP_RECONNECT_RETRIES: int = 3
    RTSP_RECONNECT_BACKOFF_SECONDS: float = 2.0

    # Phase 8 Edge Store-and-Forward
    EDGE_MODE: bool = False
    EDGE_NODE_ID: str = "EDGE-SECTOR4-NODE-01"
    EDGE_BUFFER_DB_PATH: str = "data/edge_buffer.db"
    EDGE_BUFFER_MAX_DISK_MB: int = 500
    EDGE_BUFFER_RETENTION_DAYS: int = 7
    EDGE_SYNC_BATCH_SIZE: int = 50
    EDGE_MAX_RETRIES: int = 5
    EDGE_BACKOFF_BASE_SECONDS: float = 1.0
    EDGE_BACKOFF_MAX_SECONDS: float = 60.0

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

    def validate_production_secrets(self) -> None:
        """
        Validates security configuration for the current environment.
        In production/staging, enforces fail-fast rejection of missing, placeholder,
        known development, or cryptographically insufficient secrets.
        Never prints secret values in error messages or logs.
        """
        is_production = self.APP_ENV.lower() in ("production", "prod", "staging")

        # 1. Production / Staging Fail-Fast Validation
        if is_production:
            if not self.SECRET_KEY or not self.SECRET_KEY.strip():
                raise SecurityConfigurationError(
                    "Production startup aborted: SECRET_KEY is empty. "
                    "You must provide a cryptographically secure 32+ character secret "
                    "via the SECRET_KEY environment variable or .env file."
                )

            secret_stripped = self.SECRET_KEY.strip()
            secret_lower = secret_stripped.lower()

            if secret_lower in KNOWN_INSECURE_SECRETS:
                raise SecurityConfigurationError(
                    "Production startup aborted: SECRET_KEY matches a known development or placeholder secret. "
                    "Generate a cryptographically secure 32+ byte secret (e.g. openssl rand -hex 32) "
                    "and set it in the SECRET_KEY environment variable."
                )

            for pattern in PLACEHOLDER_SUBSTRINGS:
                if pattern in secret_lower:
                    raise SecurityConfigurationError(
                        f"Production startup aborted: SECRET_KEY contains placeholder pattern '{pattern}'. "
                        "Generate a unique, cryptographically random secret for production deployment."
                    )

            if len(secret_stripped) < MINIMUM_SECRET_KEY_LENGTH:
                raise SecurityConfigurationError(
                    f"Production startup aborted: SECRET_KEY length ({len(secret_stripped)} chars) "
                    f"is below the minimum requirement of {MINIMUM_SECRET_KEY_LENGTH} characters "
                    "required for secure HMAC-SHA256 signing."
                )

        # 2. Development Notice / Non-production Handling
        else:
            if not self.SECRET_KEY or not self.SECRET_KEY.strip():
                warnings.warn(
                    "SECRET_KEY is empty in development. Falling back to default development secret. "
                    "Ensure a secure secret is configured before staging or production deployment.",
                    UserWarning,
                    stacklevel=2,
                )
                self.SECRET_KEY = DEFAULT_DEV_SECRET
            elif self.SECRET_KEY == DEFAULT_DEV_SECRET:
                warnings.warn(
                    "SECURITY NOTICE: Running in development with default dev SECRET_KEY. "
                    "This secret must NOT be used in production.",
                    UserWarning,
                    stacklevel=2,
                )

    def get_sanitized_config(self) -> Dict[str, Any]:
        """Returns application configuration with sensitive secrets masked."""
        config_dict = self.model_dump()
        sensitive_keys = {"SECRET_KEY", "GEMINI_API_KEY", "INITIAL_ADMIN_PASSWORD"}
        for k in sensitive_keys:
            if k in config_dict and config_dict[k]:
                val = str(config_dict[k])
                config_dict[k] = val[:4] + "****" if len(val) > 4 else "****"
            elif k in config_dict:
                config_dict[k] = "[NOT SET]"

        # Mask database password in URL if present
        if "DATABASE_URL" in config_dict and config_dict["DATABASE_URL"]:
            config_dict["DATABASE_URL"] = re.sub(
                r":([^:@]+)@", ":****@", config_dict["DATABASE_URL"]
            )
        return config_dict

    def get_absolute_path(self, relative_or_absolute: str) -> Path:
        p = Path(relative_or_absolute)
        if p.is_absolute():
            return p
        return BASE_DIR / relative_or_absolute

    @staticmethod
    def mask_rtsp_url(url: Optional[str]) -> Optional[str]:
        """
        Masks password credentials in RTSP or HTTP URLs.
        e.g. rtsp://admin:SecretPass123@192.168.1.50:554/live -> rtsp://admin:****@192.168.1.50:554/live
        """
        if not url:
            return url
        return re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", url)


settings = Settings()
settings.validate_production_secrets()
