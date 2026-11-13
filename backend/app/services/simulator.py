"""
Simulated Real-Time Transaction Engine.
Replays historical transactions from DB in timestamp order.
Non-blocking — uses asyncio with threadpool for database queries.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, AsyncIterator
from sqlalchemy import select, func
from app.database.session import SessionLocal
from app.models.transaction import Transaction
from app.schemas.simulator import SimulatorStatus, SimulatorEvent
from app.schemas.transaction import TransactionResponse

logger = logging.getLogger(__name__)

VALID_SPEEDS = {0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 100.0}


class SimulatorService:
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
        self._queue: asyncio.Queue[SimulatorEvent] = asyncio.Queue(maxsize=100)

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

    async def start(self) -> SimulatorStatus:
        async with self._lock:
            if self._state == "RUNNING":
                return self.get_status()
            if self._state in ("IDLE", "COMPLETED"):
                self._processed = 0
                self._offset = 0
                self._current_replay_time = None
            self._state = "RUNNING"
            self._started_at = datetime.utcnow()
            if self._task is None or self._task.done():
                self._task = asyncio.create_task(self._replay_loop())
        return self.get_status()

    async def pause(self) -> SimulatorStatus:
        async with self._lock:
            if self._state == "RUNNING":
                self._state = "PAUSED"
                if self._task and not self._task.done():
                    self._task.cancel()
                    self._task = None
        return self.get_status()

    async def reset(self) -> SimulatorStatus:
        async with self._lock:
            self._state = "IDLE"
            self._processed = 0
            self._offset = 0
            self._current_replay_time = None
            self._started_at = None
            if self._task and not self._task.done():
                self._task.cancel()
                self._task = None
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except Exception:
                    break
        return self.get_status()

    async def set_speed(self, speed: float) -> SimulatorStatus:
        self._speed = speed
        return self.get_status()

    async def event_stream(self) -> AsyncIterator[str]:
        """SSE generator: yields 'data: <json>\\n\\n' strings."""
        while True:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=5.0)
                yield f"data: {event.model_dump_json()}\n\n"
            except asyncio.TimeoutError:
                hb = SimulatorEvent(
                    event_type="HEARTBEAT",
                    timestamp=datetime.utcnow(),
                    status=self.get_status(),
                )
                yield f"data: {hb.model_dump_json()}\n\n"

    def _fetch_total(self) -> int:
        db = SessionLocal()
        try:
            return db.execute(select(func.count(Transaction.transaction_id))).scalar_one()
        finally:
            db.close()

    def _fetch_batch(self, offset: int, limit: int):
        db = SessionLocal()
        try:
            rows = db.execute(
                select(Transaction)
                .order_by(Transaction.timestamp.asc(), Transaction.transaction_id.asc())
                .limit(limit)
                .offset(offset)
            ).scalars().all()
            return [TransactionResponse.model_validate(r) for r in rows]
        finally:
            db.close()

    async def _replay_loop(self):
        """Background coroutine: batches database reads and streams transactions."""
        batch_size = 50
        loop = asyncio.get_running_loop()
        try:
            self._total = await loop.run_in_executor(None, self._fetch_total)

            while self._state == "RUNNING":
                items = await loop.run_in_executor(
                    None, self._fetch_batch, self._offset, batch_size
                )
                if not items:
                    self._state = "COMPLETED"
                    await self._queue.put(
                        SimulatorEvent(
                            event_type="COMPLETE",
                            timestamp=datetime.utcnow(),
                            status=self.get_status(),
                            message="Transaction replay completed",
                        )
                    )
                    break

                for tx in items:
                    if self._state != "RUNNING":
                        return
                    self._current_replay_time = tx.timestamp
                    self._processed += 1
                    self._offset += 1

                    event = SimulatorEvent(
                        event_type="TRANSACTION",
                        timestamp=datetime.utcnow(),
                        data=tx,
                        status=self.get_status(),
                    )
                    try:
                        self._queue.put_nowait(event)
                    except asyncio.QueueFull:
                        pass

                    sleep_time = max(0.005, 0.1 / self._speed)
                    await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Simulator replay error: {e}", exc_info=True)
            self._state = "IDLE"


simulator_service = SimulatorService()
