"""
SQLAlchemy ORM Model for Account.
"""

from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.base import Base


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    account_type: Mapped[str] = mapped_column(String(32), default="savings", index=True)
    # e.g., active, suspended, flagged, closed
    account_status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Future ML baseline fields placeholder
    # e.g., avg_monthly_turnover, risk_tier, country_code, customer_id

