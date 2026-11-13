"""
SQLAlchemy ORM Model for Transaction.
Operational transaction records isolated from ground-truth labels.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Numeric, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    sender_account_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    receiver_account_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    channel: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    merchant_category: Mapped[str] = mapped_column(String(64), index=True, nullable=False, default="transfer")
    device_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sender_balance_before: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    transaction_status: Mapped[str] = mapped_column(String(32), default="COMPLETED", index=True)

    # Optional relationship to ground truth for evaluation
    ground_truth: Mapped[Optional["TransactionGroundTruth"]] = relationship(
        "TransactionGroundTruth",
        back_populates="transaction",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_tx_sender_timestamp", "sender_account_id", "timestamp"),
        Index("ix_tx_receiver_timestamp", "receiver_account_id", "timestamp"),
        Index("ix_tx_channel_category", "channel", "merchant_category"),
        # Deterministic chronological replay ordering used by the simulator.
        Index("ix_tx_replay_order", "timestamp", "transaction_id"),
    )
