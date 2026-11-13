"""
Pydantic schemas for Transactions.
Matches Initial Data Contract and provides validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TransactionType(str, Enum):
    UPI = "UPI"
    NEFT = "NEFT"
    RTGS = "RTGS"
    CARD = "CARD"
    ATM = "ATM"
    TRANSFER = "TRANSFER"


class TransactionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class TransactionBase(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction reference", min_length=4, max_length=64)
    sender_account_id: str = Field(..., description="Masked or unique identifier of sender", min_length=4, max_length=64)
    receiver_account_id: str = Field(..., description="Masked or unique identifier of receiver", min_length=4, max_length=64)
    amount: float = Field(..., description="Monetary transaction amount", gt=0)
    currency: str = Field("INR", description="Three-letter ISO currency code", min_length=3, max_length=3)
    transaction_type: TransactionType = Field(..., description="Payment channel or protocol")
    timestamp: datetime = Field(..., description="UTC timestamp of the transaction")
    channel: str = Field(..., description="Access channel (mobile_app, web, pos, atm, api)")
    location: str = Field(..., description="Transaction location (city, state, or geo-hash)")
    transaction_status: TransactionStatus = Field(default=TransactionStatus.COMPLETED)

    # Future ML Engineering fields (optional in contract):
    # balance_before: Optional[float] = None
    # balance_after: Optional[float] = None
    # device_id: Optional[str] = None
    # ip_address: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)


class TransactionFilter(BaseModel):
    account_id: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    status: Optional[TransactionStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)

