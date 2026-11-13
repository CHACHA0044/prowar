"""
Simulated Real-Time Transaction Engine.
Replays historical transactions directly from the in-memory static CSV dataset.
Pure in-memory async replay with zero external database dependencies.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import AsyncIterator, Optional, Set

from app.core.logging import logger
from app.schemas.simulator import SimulatorEvent, SimulatorStatus
from app.schemas.transaction import TransactionResponse
from app.services.dataset_service import dataset_service

VALID_SPEEDS = {0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 100.0}
SUBSCRIBER_QUEUE_SIZE = 150
HEARTBEAT_INTERVAL_SECONDS = 15.0


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SimulatorService:
    """
    Process-wide asynchronous transaction replay simulator.
    Streams synthetic transactions via Server-Sent Events (SSE).
    """

    def __init__(self):
        self._state: str = "IDLE"
        self._speed: float = 10.0
        self._processed: int = 0
        self._total: int = 0
        self._offset: int = 0
        self._started_at: Optional[datetime] = None
        self._current_replay_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
        self._task: Optional[asyncio.Task] = None
        self._subscribers: Set[asyncio.Queue[SimulatorEvent]] = set()

    @property
    def state(self) -> str:
        return self._state

    async def initialize(self) -> None:
        """Called during application startup."""
        self._total = dataset_service.total_records
        logger.info("Simulator service initialized with %d total transactions.", self._total)

    async def shutdown(self) -> None:
        """Cancel running replay loop during application shutdown."""
        await self.pause()
        self._subscribers.clear()

    def get_status(self) -> SimulatorStatus:
        total = self._total or dataset_service.total_records
        remaining = max(0, total - self._processed)
        pct = round(self._processed / total * 100, 2) if total > 0 else 0.0
        return SimulatorStatus(
            state=self._state,
            speed_multiplier=self._speed,
            current_replay_time=self._current_replay_time,
            processed_count=self._processed,
            remaining_count=remaining,
            total_count=total,
            progress_percentage=pct,
            started_at=self._started_at,
            mode="STATIC_CSV_REPLAY",
        )

    async def start(self) -> SimulatorStatus:
        """Start or resume real-time transaction replay."""
        async with self._lock:
            if self._state == "RUNNING":
                return self.get_status()

            if self._state in ("IDLE", "COMPLETED"):
                self._processed = 0
                self._offset = 0
                self._current_replay_time = None
                self._started_at = _utcnow()

            self._total = dataset_service.total_records
            self._state = "RUNNING"
            self._task = asyncio.create_task(self._replay_loop(), name="simulator-replay-loop")
            logger.info("Simulator replay started at speed %.1fx (offset=%d).", self._speed, self._offset)

        await self._broadcast(
            SimulatorEvent(
                event_type="STATE_CHANGE",
                timestamp=_utcnow(),
                status=self.get_status(),
                message="Simulator replay started.",
            )
        )
        return self.get_status()

    async def pause(self) -> SimulatorStatus:
        """Pause the current replay."""
        async with self._lock:
            if self._state == "RUNNING":
                self._state = "PAUSED"
                if self._task and not self._task.done():
                    self._task.cancel()
                    self._task = None
                logger.info("Simulator replay paused at offset %d.", self._offset)

        await self._broadcast(
            SimulatorEvent(
                event_type="STATE_CHANGE",
                timestamp=_utcnow(),
                status=self.get_status(),
                message="Simulator replay paused.",
            )
        )
        return self.get_status()

    async def reset(self) -> SimulatorStatus:
        """Reset replay position to beginning."""
        async with self._lock:
            self._state = "IDLE"
            self._processed = 0
            self._offset = 0
            self._current_replay_time = None
            self._started_at = None
            if self._task and not self._task.done():
                self._task.cancel()
                self._task = None
            logger.info("Simulator replay reset to start.")

        await self._broadcast(
            SimulatorEvent(
                event_type="STATE_CHANGE",
                timestamp=_utcnow(),
                status=self.get_status(),
                message="Simulator replay reset to start.",
            )
        )
        return self.get_status()

    async def set_speed(self, speed: float) -> SimulatorStatus:
        """Adjust replay speed multiplier dynamically."""
        if speed not in VALID_SPEEDS and not (0.5 <= speed <= 100.0):
            raise ValueError(f"Invalid speed {speed}. Expected value between 0.5 and 100.0.")
        self._speed = speed
        logger.info("Simulator replay speed set to %.1fx", speed)

        await self._broadcast(
            SimulatorEvent(
                event_type="STATE_CHANGE",
                timestamp=_utcnow(),
                status=self.get_status(),
                message=f"Replay speed adjusted to {speed}x.",
            )
        )
        return self.get_status()

    async def _broadcast(self, event: SimulatorEvent) -> None:
        """Deliver an event to all connected subscriber queues (non-blocking)."""
        dead: Set[asyncio.Queue[SimulatorEvent]] = set()
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    q.get_nowait()
                    q.put_nowait(event)
                except Exception:
                    dead.add(q)
            except Exception:
                dead.add(q)
        self._subscribers.difference_update(dead)

    async def event_stream(self) -> AsyncIterator[str]:
        """SSE generator yielding 'data: <json>\\n\\n' with periodic heartbeats."""
        q: asyncio.Queue[SimulatorEvent] = asyncio.Queue(maxsize=SUBSCRIBER_QUEUE_SIZE)
        self._subscribers.add(q)

        # Initial connection event
        yield f"data: {SimulatorEvent(event_type='STATE_CHANGE', timestamp=_utcnow(), status=self.get_status(), message='Connected to Sentinel.AML Replay Stream.').model_dump_json()}\\n\\n"

        try:
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=HEARTBEAT_INTERVAL_SECONDS)
                    yield f"data: {event.model_dump_json()}\\n\\n"
                except asyncio.TimeoutError:
                    # Periodic keepalive heartbeat for proxies/Vercel/Render
                    hb = SimulatorEvent(
                        event_type="HEARTBEAT",
                        timestamp=_utcnow(),
                        status=self.get_status(),
                    )
                    yield f"data: {hb.model_dump_json()}\\n\\n"
        finally:
            self._subscribers.discard(q)

    async def _replay_loop(self) -> None:
        """Asynchronous playback loop consuming chronological transactions."""
        try:
            records = dataset_service.get_chronological_transactions()
            self._total = len(records)

            while self._state == "RUNNING" and self._offset < len(records):
                tx = records[self._offset]
                self._current_replay_time = tx.timestamp
                self._processed += 1
                self._offset += 1

                event = SimulatorEvent(
                    event_type="TRANSACTION",
                    timestamp=_utcnow(),
                    data=tx,
                    status=self.get_status(),
                )
                await self._broadcast(event)

                # Sleep duration adjusted for speed multiplier
                sleep_sec = max(0.005, 0.1 / self._speed)
                await asyncio.sleep(sleep_sec)

            if self._offset >= len(records):
                self._state = "COMPLETED"
                await self._broadcast(
                    SimulatorEvent(
                        event_type="COMPLETE",
                        timestamp=_utcnow(),
                        status=self.get_status(),
                        message="Replay reached end of dataset.",
                    )
                )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Simulator replay error: %s", e, exc_info=True)
            self._state = "IDLE"


simulator_service = SimulatorService()
