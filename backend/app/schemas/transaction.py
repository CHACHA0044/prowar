"""
Pydantic schemas for Transactions.
Matches Initial Data Contract and operational fields without label leakage.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class TransactionBase(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction reference", min_length=1, max_length=64)
    timestamp: datetime = Field(..., description="Transaction timestamp")
    sender_account_id: str = Field(..., description="Masked or unique identifier of sender", min_length=1, max_length=64)
    receiver_account_id: str = Field(..., description="Masked or unique identifier of receiver", min_length=1, max_length=64)
    amount: float = Field(..., description="Monetary transaction amount in INR", gt=0)
    currency: str = Field("INR", description="Three-letter ISO currency code")
    channel: str = Field(..., description="Channel: UPI, CARD, NEFT, IMPS, RTGS, WALLET, ATM, NACH")
    merchant_category: str = Field("transfer", description="Spending or transfer category")
    device_id: Optional[str] = Field(None, description="Originating device identifier")
    location: Optional[str] = Field(None, description="Location or Online")
    sender_balance_before: Optional[float] = Field(None, description="Sender balance prior to debit")
    transaction_status: str = Field("COMPLETED", description="Transaction status")


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)


class TransactionFilter(BaseModel):
    search: Optional[str] = Field(None, description="Text search on transaction_id, sender, receiver")
    sender_id: Optional[str] = None
    receiver_id: Optional[str] = None
    channel: Optional[str] = None
    merchant_category: Optional[str] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sort_by: Literal["timestamp", "amount", "transaction_id"] = "timestamp"
    sort_order: Literal["asc", "desc"] = "desc"
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
