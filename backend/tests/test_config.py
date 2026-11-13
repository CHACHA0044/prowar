"""
Configuration and environment variable tests.
Removed: database_url, is_postgresql, effective_auto_create_schema, DB_POOL_*, AUTO_CREATE_SCHEMA
         (these settings no longer exist in Phase 2.6 static CSV architecture).
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


def test_dataset_path_config():
    """DATASET_PATH is an optional string setting (None by default)."""
    settings = Settings()
    # When not set, DATASET_PATH is None — the service will auto-discover the CSV
    assert settings.DATASET_PATH is None or isinstance(settings.DATASET_PATH, str)


def test_database_url_optional():
    """DATABASE_URL is optional and not required for the static CSV architecture."""
    settings = Settings()
    # Should not raise; DATABASE_URL is None when not provided
    assert settings.DATABASE_URL is None or isinstance(settings.DATABASE_URL, str)
