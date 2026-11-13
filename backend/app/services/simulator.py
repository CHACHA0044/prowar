"""
Simulated Real-Time Transaction Engine.
Replays historical transactions from the database in timestamp order.

Production notes:
- The replay engine is a single process-wide singleton; all SSE clients share it.
- Each subscriber has a bounded queue, so a slow client cannot grow memory or
  block the replay loop.
- Replay progress is checkpointed to the database so Render restarts resume from
  the last committed batch instead of restarting from zero.
- Run exactly one Uvicorn worker per service instance. Multi-instance reliable
  replay requires an external queue/worker (documented in docs/DEPLOYMENT.md).
"""

import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import AsyncIterator, Optional

from sqlalchemy import func, select

from app.database.session import SessionLocal
from app.models.simulator_checkpoint import SimulatorCheckpoint
from app.models.transaction import Transaction
from app.schemas.simulator import SimulatorEvent, SimulatorStatus
from app.schemas.transaction import TransactionResponse

logger = logging.getLogger(__name__)

VALID_SPEEDS = {0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 100.0}
CHECKPOINT_ID = 1
SUBSCRIBER_QUEUE_SIZE = 150
HEARTBEAT_INTERVAL_SECONDS = 15.0
BATCH_SIZE = 50


def _utcnow_naive() -> datetime:
    """UTC now as a naive datetime for SQLAlchemy DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SimulatorService:
    def __init__(self):
        self._state: str = "IDLE"
        self._speed: float = 10.0
        self._processed: int = 0
        self._total: int = 0
        self._offset: int = 0
        self._started_at: Optional[datetime] = None
        self._current_replay_time: Optional[datetime] = None
        self._last_transaction_id: Optional[str] = None
        self._lock = asyncio.Lock()
        self._task: Optional[asyncio.Task] = None
        self._subscribers: set[asyncio.Queue[SimulatorEvent]] = set()
        self._persist_lock = threading.Lock()
        self._initialized = False

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    @property
    def state(self) -> str:
        return self._state

    def get_status(self) -> SimulatorStatus:
        remaining = max(0, self._total - self._processed)
        pct = round(self._processed / self._total * 100, 2) if self._total > 0 else 0.0
        return SimulatorStatus(
            state=self._state,
            speed_multiplier=self._speed,
            current_replay_time=self._current_replay_time,
            processed_count=self._processed,
            remaining_count=remaining,
            total_count=self._total,
            progress_percentage=pct,
            started_at=self._started_at,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def initialize(self) -> None:
        """Restore the replay checkpoint (idempotent; safe to call repeatedly)."""
        if self._initialized:
            return
        self._initialized = True
        loop = asyncio.get_running_loop()
        checkpoint = await loop.run_in_executor(None, self._load_checkpoint)
        if not checkpoint:
            return

        self._speed = checkpoint.speed_multiplier or 10.0
        self._offset = max(0, checkpoint.replay_offset or 0)
        self._processed = max(0, checkpoint.processed_count or 0)
        self._total = max(0, checkpoint.total_count or 0)
        self._current_replay_time = checkpoint.current_replay_time
        self._last_transaction_id = checkpoint.last_transaction_id

        if checkpoint.state == "RUNNING":
            # Never auto-resume a background task after a restart; the operator
            # explicitly resumes from the persisted cursor.
            self._state = "PAUSED"
            logger.info("Simulator checkpoint restored; replay is PAUSED at offset %s", self._offset)
        elif checkpoint.state == "COMPLETED":
            self._state = "COMPLETED"
        else:
            self._state = "PAUSED" if self._offset > 0 else "IDLE"

    async def shutdown(self) -> None:
        """Persist progress and cancel the replay task during app shutdown."""
        async with self._lock:
            if self._task and not self._task.done():
                self._task.cancel()
                self._task = None
            await self._persist_checkpoint_async()
            self._subscribers.clear()

    async def start(self) -> SimulatorStatus:
        async with self._lock:
            if self._state == "RUNNING":
                return self.get_status()
            if self._state in ("IDLE", "COMPLETED"):
                self._processed = 0
                self._offset = 0
                self._current_replay_time = None
                self._last_transaction_id = None
            self._state = "RUNNING"
            self._started_at = _utcnow_naive()
            if self._task is None or self._task.done():
                self._task = asyncio.create_task(self._replay_loop())
            await self._persist_checkpoint_async()
            self._publish_state_change()
        return self.get_status()

    async def pause(self) -> SimulatorStatus:
        async with self._lock:
            if self._state == "RUNNING":
                self._state = "PAUSED"
                if self._task and not self._task.done():
                    self._task.cancel()
                    self._task = None
                await self._persist_checkpoint_async()
                self._publish_state_change()
        return self.get_status()

    async def reset(self) -> SimulatorStatus:
        async with self._lock:
            self._state = "IDLE"
            self._processed = 0
            self._offset = 0
            self._current_replay_time = None
            self._last_transaction_id = None
            self._started_at = None
            if self._task and not self._task.done():
                self._task.cancel()
                self._task = None
            await self._persist_checkpoint_async()
            self._publish_state_change()
        return self.get_status()

    async def set_speed(self, speed: float) -> SimulatorStatus:
        if not (0.5 <= speed <= 100.0):
            raise ValueError("Speed must be between 0.5 and 100.0")
        async with self._lock:
            self._speed = speed
            await self._persist_checkpoint_async()
        return self.get_status()

    # ------------------------------------------------------------------
    # SSE subscribers
    # ------------------------------------------------------------------
    def _register_subscriber(self) -> asyncio.Queue[SimulatorEvent]:
        queue: asyncio.Queue[SimulatorEvent] = asyncio.Queue(maxsize=SUBSCRIBER_QUEUE_SIZE)
        self._subscribers.add(queue)
        return queue

    def _unregister_subscriber(self, queue: asyncio.Queue[SimulatorEvent]) -> None:
        self._subscribers.discard(queue)

    def _publish(self, event: SimulatorEvent) -> None:
        """Fan out an event to every connected SSE client without blocking."""
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Drop the oldest event for slow consumers; never stall replay.
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except Exception:  # noqa: BLE001 - subscriber may have disconnected
                    self._subscribers.discard(queue)

    def _publish_state_change(self) -> None:
        self._publish(
            SimulatorEvent(
                event_type="STATE_CHANGE",
                timestamp=_utcnow_naive(),
                status=self.get_status(),
                message=f"Simulator state changed to {self._state}",
            )
        )

    async def event_stream(self, request=None) -> AsyncIterator[str]:
        """
        SSE generator: yields ``data: <json>`` frames plus periodic heartbeats.

        Each connection receives its own bounded queue, so multiple browser tabs
        observe the same replay instead of consuming each other's events.
        """
        queue = self._register_subscriber()
        try:
            # Browser EventSource honours this reconnection delay.
            yield "retry: 3000\n\n"
            yield f"data: {SimulatorEvent(event_type='STATE_CHANGE', timestamp=_utcnow_naive(), status=self.get_status()).model_dump_json()}\n\n"

            while True:
                if request is not None and await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(
                        queue.get(), timeout=HEARTBEAT_INTERVAL_SECONDS
                    )
                    yield f"data: {event.model_dump_json()}\n\n"
                except asyncio.TimeoutError:
                    if request is not None and await request.is_disconnected():
                        break
                    heartbeat = SimulatorEvent(
                        event_type="HEARTBEAT",
                        timestamp=_utcnow_naive(),
                        status=self.get_status(),
                    )
                    yield f"data: {heartbeat.model_dump_json()}\n\n"
        except asyncio.CancelledError:
            raise
        finally:
            self._unregister_subscriber(queue)

    # ------------------------------------------------------------------
    # Replay loop
    # ------------------------------------------------------------------
    def _fetch_total(self) -> int:
        db = SessionLocal()
        try:
            return db.execute(select(func.count(Transaction.transaction_id))).scalar_one()
        finally:
            db.close()

    def _fetch_batch(self, offset: int, limit: int):
        db = SessionLocal()
        try:
            rows = (
                db.execute(
                    select(Transaction)
                    .order_by(Transaction.timestamp.asc(), Transaction.transaction_id.asc())
                    .limit(limit)
                    .offset(offset)
                )
                .scalars()
                .all()
            )
            return [TransactionResponse.model_validate(row) for row in rows]
        finally:
            db.close()

    async def _replay_loop(self) -> None:
        """Background coroutine: batches database reads and broadcasts transactions."""
        loop = asyncio.get_running_loop()
        try:
            total = await loop.run_in_executor(None, self._fetch_total)
            if total != self._total:
                self._total = total
            if self._offset > total:
                self._offset = 0
                self._processed = 0
                self._current_replay_time = None
                self._last_transaction_id = None

            while self._state == "RUNNING":
                items = await loop.run_in_executor(
                    None, self._fetch_batch, self._offset, BATCH_SIZE
                )
                if not items:
                    self._state = "COMPLETED"
                    self._publish(
                        SimulatorEvent(
                            event_type="COMPLETE",
                            timestamp=_utcnow_naive(),
                            status=self.get_status(),
                            message="Transaction replay completed",
                        )
                    )
                    await self._persist_checkpoint_async()
                    break

                for tx in items:
                    if self._state != "RUNNING":
                        return
                    self._current_replay_time = tx.timestamp
                    self._last_transaction_id = tx.transaction_id
                    self._processed += 1
                    self._offset += 1

                    self._publish(
                        SimulatorEvent(
                            event_type="TRANSACTION",
                            timestamp=_utcnow_naive(),
                            data=tx,
                            status=self.get_status(),
                        )
                    )

                    sleep_time = max(0.005, 0.1 / self._speed)
                    await asyncio.sleep(sleep_time)

                # Persist at batch boundaries. At most one batch can be replayed
                # again after a hard process restart.
                await self._persist_checkpoint_async()

        except asyncio.CancelledError:
            await self._persist_checkpoint_async()
            raise
        except Exception as e:  # noqa: BLE001 - background task must not crash app
            logger.error("Simulator replay error: %s", e, exc_info=True)
            self._state = "IDLE"
            await self._persist_checkpoint_async()
            self._publish_state_change()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _load_checkpoint(self) -> Optional[SimulatorCheckpoint]:
        db = SessionLocal()
        try:
            return db.get(SimulatorCheckpoint, CHECKPOINT_ID)
        except Exception as e:  # noqa: BLE001 - table may not exist before migration
            logger.warning("Could not load simulator checkpoint: %s", e)
            return None
        finally:
            db.close()

    def _persist_checkpoint(self) -> None:
        with self._persist_lock:
            db = SessionLocal()
            try:
                checkpoint = db.get(SimulatorCheckpoint, CHECKPOINT_ID)
                if checkpoint is None:
                    checkpoint = SimulatorCheckpoint(id=CHECKPOINT_ID)
                    db.add(checkpoint)
                checkpoint.state = self._state
                checkpoint.speed_multiplier = self._speed
                checkpoint.replay_offset = self._offset
                checkpoint.processed_count = self._processed
                checkpoint.total_count = self._total
                checkpoint.current_replay_time = self._current_replay_time
                checkpoint.last_transaction_id = self._last_transaction_id
                checkpoint.updated_at = _utcnow_naive()
                db.commit()
            except Exception as e:  # noqa: BLE001 - progress persistence is best-effort
                db.rollback()
                logger.warning("Could not persist simulator checkpoint: %s", e)
            finally:
                db.close()

    async def _persist_checkpoint_async(self) -> None:
        """Run the blocking checkpoint write outside the event loop."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._persist_checkpoint)


simulator_service = SimulatorService()
