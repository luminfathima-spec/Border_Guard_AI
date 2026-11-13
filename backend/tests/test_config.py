import pytest
from app.core.config import settings, Settings, SecurityConfigurationError


def test_settings_sanitization():
    sanitized = settings.get_sanitized_config()
    assert "SECRET_KEY" in sanitized
    assert sanitized["SECRET_KEY"] != settings.SECRET_KEY
    assert "****" in sanitized["SECRET_KEY"]
    if settings.GEMINI_API_KEY:
        assert "****" in sanitized["GEMINI_API_KEY"]
    assert "sentinelai" in sanitized["DATABASE_URL"]
    assert "****" in sanitized["DATABASE_URL"] or "sqlite" in sanitized["DATABASE_URL"]


def test_settings_absolute_path_resolution():
    upload_path = settings.get_absolute_path(settings.UPLOAD_DIR)
    assert upload_path.is_absolute()
    assert str(upload_path).endswith("uploads")


def test_production_secret_fail_fast_rejection():
    prod_settings = Settings(
        APP_ENV="production",
        SECRET_KEY="sentinel_ai_super_secret_jwt_key_sih_2026_change_in_production",
    )
    with pytest.raises(SecurityConfigurationError, match="Production startup aborted"):
        prod_settings.validate_production_secrets()


def test_development_secret_notice_warning():
    dev_settings = Settings(
        APP_ENV="development",
        SECRET_KEY="sentinel_ai_super_secret_jwt_key_sih_2026_change_in_production",
    )
    with pytest.warns(UserWarning, match="SECURITY NOTICE"):
        dev_settings.validate_production_secrets()
