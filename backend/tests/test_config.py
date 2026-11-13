"""
Configuration and environment variable tests.
"""

from backend.app.core.config import Settings


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

