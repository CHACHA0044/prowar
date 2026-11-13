"""
SQLAlchemy ORM Model for Simulator Replay Checkpoint.
Stores the replay cursor so a Render restart does not lose simulator progress.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SimulatorCheckpoint(Base):
    __tablename__ = "simulator_checkpoint"

    # Single-row table. The application only ever reads/writes id = 1.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state: Mapped[str] = mapped_column(String(16), default="IDLE", nullable=False)
    speed_multiplier: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    replay_offset: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_replay_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_transaction_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow_naive, onupdate=_utcnow_naive, nullable=False
    )
