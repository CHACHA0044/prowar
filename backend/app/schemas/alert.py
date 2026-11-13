"""
Pydantic schemas for Security Alerts.
Matches Initial Data Contract and provides validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.utils.timestamps import utc_now


class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class AlertBase(BaseModel):
    alert_id: str = Field(..., description="Unique alert identifier", min_length=4, max_length=64)
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID if applicable")
    account_id: str = Field(..., description="Account identifier subject to alert", min_length=4, max_length=64)
    alert_type: str = Field(..., description="Type of detected security threat")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Ensemble risk score between 0 and 100")
    explanation: str = Field(..., description="Human-readable and feature attribution explanation")
    created_at: datetime = Field(default_factory=utc_now)
    status: AlertStatus = Field(default=AlertStatus.OPEN)


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    model_config = ConfigDict(from_attributes=True)


class AlertUpdateStatus(BaseModel):
    status: AlertStatus
    reviewer_notes: Optional[str] = None
