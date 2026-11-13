"""
Pydantic schemas for the Simulated Real-Time Transaction Engine.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from app.schemas.transaction import TransactionResponse


class SimulatorStatus(BaseModel):
    state: Literal["IDLE", "RUNNING", "PAUSED", "COMPLETED"]
    speed_multiplier: float = 1.0
    current_replay_time: Optional[datetime] = None
    processed_count: int = 0
    remaining_count: int = 0
    total_count: int = 0
    progress_percentage: float = 0.0
    batch_size: int = 1
    started_at: Optional[datetime] = None
    mode: str = "HISTORICAL_REPLAY"


class SpeedUpdateRequest(BaseModel):
    speed: float = Field(..., ge=0.5, le=100.0, description="Replay speed multiplier (e.g. 1.0, 5.0, 10.0, 30.0, 60.0)")


class SimulatorEvent(BaseModel):
    event_type: Literal["TRANSACTION", "HEARTBEAT", "STATE_CHANGE", "COMPLETE"]
    timestamp: datetime
    data: Optional[TransactionResponse] = None
    status: Optional[SimulatorStatus] = None
    message: Optional[str] = None

