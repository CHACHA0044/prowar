"""Tests for the lightweight self-ping service."""

import pytest
import httpx
from app.core.config import settings
from app.services.self_ping import SelfPingService


def test_harmless_cpu_work():
    service = SelfPingService()
    result = service.perform_harmless_cpu_work()
    assert "sample_count" in result
    assert 500 <= result["sample_count"] <= 1500
    assert "calculated_sum" in result
    assert isinstance(result["calculated_sum"], float)
    assert "cpu_time_ms" in result
    assert result["cpu_time_ms"] >= 0.0


def test_resolve_target_url(monkeypatch):
    service = SelfPingService()

    # Default fallback
    monkeypatch.setattr(settings, "SELF_PING_URL", None)
    monkeypatch.setattr(settings, "RENDER_EXTERNAL_URL", None)
    default_url = service.resolve_target_url()
    assert "/api/v1/health/live" in default_url
    assert "127.0.0.1" in default_url

    # Render external URL
    monkeypatch.setattr(settings, "RENDER_EXTERNAL_URL", "https://sentinel-backend.onrender.com")
    render_url = service.resolve_target_url()
    assert render_url == "https://sentinel-backend.onrender.com/api/v1/health/live"

    # Explicit override takes priority
    monkeypatch.setattr(settings, "SELF_PING_URL", "https://custom.ping/health")
    custom_url = service.resolve_target_url()
    assert custom_url == "https://custom.ping/health"


@pytest.mark.asyncio
async def test_ping_once_graceful_failure():
    service = SelfPingService()

    # Ping with an invalid host should be caught and handled gracefully without exception
    async with httpx.AsyncClient() as client:
        # Should not raise exception
        await service.ping_once(client)


@pytest.mark.asyncio
async def test_self_ping_skipped_in_testing():
    service = SelfPingService()
    # When ENVIRONMENT is testing, start() does not launch a task
    await service.start()
    assert service.is_running is False
    assert service._task is None
    await service.stop()
