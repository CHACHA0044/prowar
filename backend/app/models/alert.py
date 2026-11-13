"""
SQLAlchemy ORM Model for Security Alert.
"""

from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database.base import Base


class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    alert_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    transaction_id: Mapped[str] = mapped_column(String(64), index=True, nullable=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    alert_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # FRAUD, AML_STRUCTURING, AML_CYCLE, BEHAVIORAL_ANOMALY
    severity: Mapped[str] = mapped_column(String(16), index=True, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)  # 0.00 to 100.00
    explanation: Mapped[str] = mapped_column(Text, nullable=False)  # Human-readable & SHAP summary
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    status: Mapped[str] = mapped_column(String(24), default="OPEN", index=True)  # OPEN, UNDER_REVIEW, RESOLVED, DISMISSED

    # Analyst audit trail hooks (for Department 10 Responsible AI & human-in-the-loop):
    # - reviewed_by, reviewed_at, resolution_notes

    __table_args__ = (
        Index("ix_alert_account_created", "account_id", "created_at"),
        Index("ix_alert_severity_status", "severity", "status"),
    )

