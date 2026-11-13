"""
SQLAlchemy ORM Model for Transaction Ground Truth.
Strictly separated from operational transactions to prevent label leakage.
"""

from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class TransactionGroundTruth(Base):
    __tablename__ = "transaction_ground_truth"

    transaction_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("transactions.transaction_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    is_fraud: Mapped[int] = mapped_column(Integer, default=0, index=True, nullable=False)
    is_aml_pattern: Mapped[int] = mapped_column(Integer, default=0, index=True, nullable=False)
    pattern_type: Mapped[str] = mapped_column(String(64), default="normal", index=True, nullable=False)
    scenario_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    is_edge_case: Mapped[int] = mapped_column(Integer, default=0, index=True, nullable=False)
    edge_case_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="ground_truth",
    )

    __table_args__ = (
        Index("ix_gt_fraud_aml", "is_fraud", "is_aml_pattern"),
        Index("ix_gt_pattern_scenario", "pattern_type", "scenario_id"),
    )

