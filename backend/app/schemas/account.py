"""
Pydantic schemas for Accounts.
Matches Initial Data Contract and provides validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.utils.timestamps import utc_now


class AccountType(str, Enum):
    SAVINGS = "savings"
    CURRENT = "current"
    WALLET = "wallet"
    MERCHANT = "merchant"
    CORPORATE = "corporate"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    FLAGGED = "flagged"
    CLOSED = "closed"


class AccountBase(BaseModel):
    account_id: str = Field(..., description="Unique account identifier", min_length=4, max_length=64)
    account_type: AccountType = Field(default=AccountType.SAVINGS)
    account_status: AccountStatus = Field(default=AccountStatus.ACTIVE)
    created_at: datetime = Field(default_factory=utc_now)


class AccountCreate(AccountBase):
    pass


class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)
