"""
Configuration and environment variable tests.
"""

from app.core.config import Settings


def test_default_config():
    settings = Settings()
    assert settings.API_V1_STR == "/api/v1"
    assert settings.BACKEND_PORT == 8000
    assert len(settings.cors_origins) > 0


def test_cors_origins_parsing():
    settings = Settings(ALLOWED_ORIGINS="http://test.com, https://secure.test.com")
    origins = settings.cors_origins
    assert "http://test.com" in origins
    assert "https://secure.test.com" in origins
    assert len(origins) == 2


def test_production_cors_filters_localhost():
    settings = Settings(
        ENVIRONMENT="production",
        ALLOWED_ORIGINS="https://prowar-rho.vercel.app,http://localhost:3000",
    )
    assert settings.cors_origins == ["https://prowar-rho.vercel.app"]


def test_production_rejects_wildcard_origins():
    settings = Settings(ENVIRONMENT="production", ALLOWED_ORIGINS="*")
    try:
        settings.cors_origins
    except ValueError as exc:
        assert "Wildcard" in str(exc)
    else:
        raise AssertionError("Production wildcard CORS origin should be rejected")


def test_database_url_normalization():
    settings = Settings(DATABASE_URL="postgresql://user:pass@example.com:5432/postgres")
    assert settings.database_url.startswith("postgresql+psycopg2://")
    assert settings.is_postgresql is True

    legacy = Settings(DATABASE_URL="postgres://user:pass@example.com:5432/postgres")
    assert legacy.database_url.startswith("postgresql+psycopg2://")


def test_production_does_not_auto_create_schema():
    settings = Settings(ENVIRONMENT="production", AUTO_CREATE_SCHEMA=None)
    assert settings.effective_auto_create_schema is False

    dev = Settings(ENVIRONMENT="development", AUTO_CREATE_SCHEMA=None)
    assert dev.effective_auto_create_schema is True

