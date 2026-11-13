import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI

from app.core.config import (
    Settings,
    DEFAULT_DEV_SECRET,
    SecurityConfigurationError,
    settings,
)
from app.core.security import verify_password, get_password_hash
from app.db.database import Base
from app.db.init_db import init_db
from app.models.user import User, UserRole
from app.main import lifespan


# ---------------------------------------------------------------------------
# Task 7.1: Production Startup Rejection Tests
# ---------------------------------------------------------------------------

def test_production_rejects_empty_secret():
    """Fail-fast: Production startup must reject an empty or whitespace SECRET_KEY."""
    prod_settings = Settings(APP_ENV="production", SECRET_KEY="")
    with pytest.raises(SecurityConfigurationError, match="SECRET_KEY is empty"):
        prod_settings.validate_production_secrets()

    prod_settings_whitespace = Settings(APP_ENV="production", SECRET_KEY="   \t\n  ")
    with pytest.raises(SecurityConfigurationError, match="SECRET_KEY is empty"):
        prod_settings_whitespace.validate_production_secrets()


def test_production_rejects_default_dev_secret():
    """Fail-fast: Production startup must reject the known development secret."""
    prod_settings = Settings(
        APP_ENV="production",
        SECRET_KEY=DEFAULT_DEV_SECRET,
    )
    with pytest.raises(SecurityConfigurationError, match="matches a known development or placeholder"):
        prod_settings.validate_production_secrets()


@pytest.mark.parametrize("insecure_key", [
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
])
def test_production_rejects_known_weak_keys(insecure_key):
    """Fail-fast: Production startup must reject common placeholder keys."""
    prod_settings = Settings(APP_ENV="production", SECRET_KEY=insecure_key)
    with pytest.raises(SecurityConfigurationError):
        prod_settings.validate_production_secrets()


def test_production_rejects_placeholder_substrings():
    """Fail-fast: Production startup must reject keys containing placeholder keywords."""
    prod_settings = Settings(
        APP_ENV="production",
        SECRET_KEY="corp_security_key_with_changeme_inside_that_is_long_enough",
    )
    with pytest.raises(SecurityConfigurationError, match="placeholder pattern"):
        prod_settings.validate_production_secrets()


def test_production_rejects_short_secret():
    """Fail-fast: Production startup must reject secrets under 32 characters (HMAC-SHA256)."""
    short_secret = "short_20_chars_only"
    assert len(short_secret) < 32
    prod_settings = Settings(APP_ENV="production", SECRET_KEY=short_secret)
    with pytest.raises(SecurityConfigurationError, match="is below the minimum requirement of 32 characters"):
        prod_settings.validate_production_secrets()


def test_production_accepts_strong_secret():
    """Production startup must succeed when configured with a strong 32+ byte secret."""
    strong_secret = "f8a9e2b1c4d703561a9e8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e"
    assert len(strong_secret) == 64
    prod_settings = Settings(APP_ENV="production", SECRET_KEY=strong_secret)
    # Must not raise any exception
    prod_settings.validate_production_secrets()


def test_staging_enforces_production_security():
    """Staging environments must enforce the same fail-fast secret validation as production."""
    staging_settings = Settings(APP_ENV="staging", SECRET_KEY=DEFAULT_DEV_SECRET)
    with pytest.raises(SecurityConfigurationError):
        staging_settings.validate_production_secrets()


# ---------------------------------------------------------------------------
# Task 7.2: Development Mode Ergonomics Tests
# ---------------------------------------------------------------------------

def test_development_mode_allows_dev_secret_with_warning():
    """Development mode allows default secret to keep local setup frictionless, with notice."""
    dev_settings = Settings(
        APP_ENV="development",
        SECRET_KEY=DEFAULT_DEV_SECRET,
    )
    with pytest.warns(UserWarning, match="SECURITY NOTICE"):
        dev_settings.validate_production_secrets()


def test_development_mode_empty_secret_fallback():
    """Development mode gracefully falls back to default dev secret if set to empty."""
    dev_settings = Settings(
        APP_ENV="development",
        SECRET_KEY="",
    )
    with pytest.warns(UserWarning, match="Falling back to default development secret"):
        dev_settings.validate_production_secrets()
    assert dev_settings.SECRET_KEY == DEFAULT_DEV_SECRET


# ---------------------------------------------------------------------------
# Task 7.3: Secret Masking & Sanitization Tests (Never print secrets)
# ---------------------------------------------------------------------------

def test_sanitized_config_never_leaks_secrets():
    """get_sanitized_config must mask SECRET_KEY, GEMINI_API_KEY, and INITIAL_ADMIN_PASSWORD."""
    custom_secret = "super_secure_production_secret_key_random_hex_value_12345678"
    custom_gemini = "AIzaSyFakeKeyForTestingMaskingFunctionality123"
    custom_admin_pass = "MySecretAdminPass2026!"

    custom_settings = Settings(
        APP_ENV="development",
        SECRET_KEY=custom_secret,
        GEMINI_API_KEY=custom_gemini,
        INITIAL_ADMIN_PASSWORD=custom_admin_pass,
        DATABASE_URL="postgresql://user:db_secret_pass@localhost:5432/testdb",
    )
    sanitized = custom_settings.get_sanitized_config()

    # Raw secrets must NOT be present anywhere in the sanitized dict values
    assert custom_secret not in sanitized.values()
    assert custom_gemini not in sanitized.values()
    assert custom_admin_pass not in sanitized.values()
    assert "db_secret_pass" not in sanitized["DATABASE_URL"]

    # Masked representations must be present
    assert "****" in sanitized["SECRET_KEY"]
    assert "****" in sanitized["GEMINI_API_KEY"]
    assert "****" in sanitized["INITIAL_ADMIN_PASSWORD"]
    assert ":****@" in sanitized["DATABASE_URL"]


# ---------------------------------------------------------------------------
# Task 7.4: Default Credentials in Production Tests
# ---------------------------------------------------------------------------

def test_init_db_in_production_blocks_default_credentials(monkeypatch):
    """In production, init_db must NOT seed default demo accounts with known passwords."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()

    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "ALLOW_DEFAULT_CREDENTIALS_IN_PRODUCTION", False)
    monkeypatch.setattr(settings, "INITIAL_ADMIN_EMAIL", None)
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PASSWORD", None)

    try:
        init_db(db)
        # Default accounts must NOT exist in production
        admin_user = db.query(User).filter(User.email == "admin@sentinel.ai").first()
        assert admin_user is None
        operator_user = db.query(User).filter(User.email == "operator@sentinel.ai").first()
        assert operator_user is None
    finally:
        db.close()


def test_init_db_in_production_bootstraps_configured_admin(monkeypatch):
    """In production, if INITIAL_ADMIN_EMAIL & PASSWORD are set, bootstrap the initial admin."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()

    prod_email = "commander@defense.gov.in"
    prod_pass = "V3ryStr0ng!PerimeterSec2026#"

    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "ALLOW_DEFAULT_CREDENTIALS_IN_PRODUCTION", False)
    monkeypatch.setattr(settings, "INITIAL_ADMIN_EMAIL", prod_email)
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PASSWORD", prod_pass)

    try:
        init_db(db)
        admin_user = db.query(User).filter(User.email == prod_email).first()
        assert admin_user is not None
        assert admin_user.role == UserRole.ADMIN.value
        assert verify_password(prod_pass, admin_user.password_hash)
    finally:
        db.close()


def test_init_db_does_not_overwrite_existing_passwords(monkeypatch):
    """init_db must preserve modified user passwords and never reset them on restart."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()

    monkeypatch.setattr(settings, "APP_ENV", "development")

    try:
        # Initial seeding
        init_db(db)
        admin = db.query(User).filter(User.email == "admin@sentinel.ai").first()
        assert admin is not None
        assert verify_password("AdminPassword123!", admin.password_hash)

        # Admin changes their password
        new_password = "MyCustomNewPassword2026!"
        admin.password_hash = get_password_hash(new_password)
        db.commit()

        # Restart simulation: init_db runs again
        init_db(db)
        db.refresh(admin)

        # Password must remain the customized one, NOT reverted to AdminPassword123!
        assert verify_password(new_password, admin.password_hash)
        assert not verify_password("AdminPassword123!", admin.password_hash)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task 7.5: FastAPI Lifespan Fail-Fast Startup Rejection Test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fastapi_lifespan_fails_fast_in_production(monkeypatch):
    """FastAPI application lifespan must fail fast and abort startup in production with unsafe key."""
    test_app = FastAPI(lifespan=lifespan)

    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "SECRET_KEY", DEFAULT_DEV_SECRET)

    with pytest.raises(SecurityConfigurationError, match="Production startup aborted"):
        async with test_app.router.lifespan_context(test_app):
            pass  # pragma: no cover
