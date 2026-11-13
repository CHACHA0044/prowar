"""
SQLAlchemy Session and Engine management.
In the static CSV architecture, the primary data source is data/transactions.csv.
This module maintains optional, non-blocking local SQLite compatibility for legacy models.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import logger
from app.services.dataset_service import dataset_service


def _build_engine():
    """Create a lightweight local SQLite engine if DATABASE_URL is set, else in-memory."""
    url = settings.DATABASE_URL or "sqlite:///:memory:"
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)


engine = _build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency for endpoints requesting an optional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for background tasks needing an optional DB session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_health() -> dict:
    """Check dataset and optional database health."""
    is_ready = dataset_service.is_ready
    records = dataset_service.total_records if is_ready else 0
    return {
        "status": "healthy" if is_ready else "degraded",
        "connected": is_ready,
        "dialect": "static_csv",
        "url_type": "file",
        "message": f"Static CSV active ({records:,} transactions loaded).",
    }
