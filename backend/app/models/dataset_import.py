"""
SQLAlchemy ORM Model for Dataset Import Metadata.
Tracks import runs, checksums, and record counts for idempotency.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base
from app.utils.timestamps import utc_now


class DatasetImport(Base):
    __tablename__ = "dataset_imports"

    dataset_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    imported_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    skipped_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    date_range_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    date_range_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED", nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

