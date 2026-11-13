"""
Lightweight Self-Ping Service for Render Free-Tier Container Keep-Alive.

Sends periodic HTTP requests (default every 3 minutes) to the application's health
endpoint to help mitigate Render free-tier idle spin-down. Each ping also performs
a small randomized, harmless CPU calculation (generating random floats and computing
their sum) to ensure container activity is registered by the hypervisor.

IMPORTANT DISCLAIMER:
Automated self-pings do not guarantee prevention of Render's free-tier sleep or override
Render's platform-level inactivity or suspension policies. This service runs purely as
a best-effort background helper and does not interfere with the transaction simulator
or operational API throughput.
"""

import asyncio
import random
import time
from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import logger


class SelfPingService:
    """Manages periodic background self-ping requests with CPU activity."""

    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False
        self._lock = asyncio.Lock()
        self._ping_count: int = 0

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def ping_count(self) -> int:
        return self._ping_count

    def resolve_target_url(self) -> str:
        """Resolve the health URL to ping."""
        if settings.SELF_PING_URL:
            return settings.SELF_PING_URL.strip()

        # Render auto-populates RENDER_EXTERNAL_URL on deployed Web Services
        if settings.RENDER_EXTERNAL_URL:
            base = settings.RENDER_EXTERNAL_URL.strip().rstrip("/")
            return f"{base}{settings.API_V1_STR}/health/live"

        # Fallback to local loopback interface
        return f"http://127.0.0.1:{settings.BACKEND_PORT}{settings.API_V1_STR}/health/live"

    def perform_harmless_cpu_work(self) -> dict:
        """
        Perform a small, non-blocking randomized CPU calculation:
        generates N random numbers (between 500 and 1500) and computes their sum.
        """
        start_time = time.perf_counter()
        count = random.randint(500, 1500)
        numbers = [random.random() for _ in range(count)]
        calc_sum = sum(numbers)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "sample_count": count,
            "calculated_sum": round(calc_sum, 4),
            "cpu_time_ms": round(elapsed_ms, 3),
        }

    async def ping_once(self, client: httpx.AsyncClient) -> None:
        """Execute a single safe ping cycle with concurrency locking."""
        if self._lock.locked():
            logger.debug("Previous self-ping cycle still active; skipping to avoid overlap.")
            return

        async with self._lock:
            # 1. Perform lightweight CPU calculation
            work_stats = self.perform_harmless_cpu_work()

            target_url = self.resolve_target_url()
            start_req = time.perf_counter()

            try:
                response = await client.get(target_url, timeout=10.0)
                latency_ms = (time.perf_counter() - start_req) * 1000.0
                self._ping_count += 1

                logger.info(
                    "Self-ping #%d successful -> %s [status=%d, latency=%.1fms, cpu_work=%.3fms, sum=%.4f]",
                    self._ping_count,
                    target_url,
                    response.status_code,
                    latency_ms,
                    work_stats["cpu_time_ms"],
                    work_stats["calculated_sum"],
                )
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                logger.warning(
                    "Self-ping to %s failed gracefully (non-fatal): %s",
                    target_url,
                    exc,
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning(
                    "Unexpected error during self-ping cycle to %s: %s",
                    target_url,
                    exc,
                )

    async def _ping_loop(self) -> None:
        """Background loop executing pings at configured intervals."""
        interval = max(30, settings.SELF_PING_INTERVAL_SECONDS)
        logger.info(
            "Self-ping background task started (interval=%ds, target=%s). "
            "Note: Pings do not guarantee prevention of Render free-tier sleep.",
            interval,
            self.resolve_target_url(),
        )

        # Initial delay to give the server time to finish startup & bind port
        await asyncio.sleep(15)

        async with httpx.AsyncClient() as client:
            while self._running:
                try:
                    await self.ping_once(client)
                except asyncio.CancelledError:
                    break
                except Exception as exc:  # pylint: disable=broad-except
                    logger.error("Unhandled error in self-ping loop: %s", exc)

                try:
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    break

        logger.info("Self-ping background task terminated.")

    async def start(self) -> None:
        """Start the periodic self-ping task if enabled and not in testing."""
        if not settings.SELF_PING_ENABLED:
            logger.info("Self-ping service is disabled via SELF_PING_ENABLED=False.")
            return

        if settings.ENVIRONMENT.lower() in ("testing", "test"):
            logger.debug("Self-ping service skipped in testing environment.")
            return

        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._ping_loop(), name="self_ping_worker")

    async def stop(self) -> None:
        """Gracefully stop and cancel the background ping task."""
        if not self._running:
            return

        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("Self-ping service stopped.")


self_ping_service = SelfPingService()
