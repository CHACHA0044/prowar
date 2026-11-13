"""
SQLAlchemy ORM Model for Transaction.
"""

from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    sender_account_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    receiver_account_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # UPI, NEFT, RTGS, CARD, ATM
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)  # mobile_app, web, pos, atm, api
    location: Mapped[str] = mapped_column(String(64), nullable=False)  # city, state, or geo-coordinates
    transaction_status: Mapped[str] = mapped_column(String(32), default="COMPLETED", index=True)  # COMPLETED, PENDING, FAILED, BLOCKED

    # ML Feature Engineering Hooks (documented for subsequent phases):
    # - balance_before, balance_after
    # - device_id, ip_address, user_agent
    # - is_fraud (ground-truth label for synthetic evaluation)
    # - is_aml_pattern (ground-truth label)
    # - pattern_type (e.g. structuring, cycle, fan_in, pass_through)

    __table_args__ = (
        Index("ix_tx_sender_timestamp", "sender_account_id", "timestamp"),
        Index("ix_tx_receiver_timestamp", "receiver_account_id", "timestamp"),
    )

