"""
SQLAlchemy Session and Engine management.
Provides connection lifecycle, pooling, transaction handling and database
health inspection for both SQLite (local development) and PostgreSQL
(Supabase production).
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import logger


def _build_engine():
    """Create a dialect-aware SQLAlchemy engine with safe pooling defaults."""
    url = settings.database_url

    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        return create_engine(
            url,
            connect_args=connect_args,
            pool_pre_ping=True,
            echo=settings.DB_ECHO,
        )

    if url.startswith("postgresql"):
        connect_args = {
            "connect_timeout": settings.DB_CONNECT_TIMEOUT,
            "application_name": "sentinel-aml-backend",
        }
        # Supabase requires TLS. Do not override an explicit sslmode in the URL.
        if settings.DB_SSL_MODE and "sslmode=" not in url:
            connect_args["sslmode"] = settings.DB_SSL_MODE

        return create_engine(
            url,
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            echo=settings.DB_ECHO,
        )

    # Unknown dialect: keep SQLAlchemy defaults but still verify connections.
    return create_engine(url, pool_pre_ping=True, echo=settings.DB_ECHO)


engine = _build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.

    The session is rolled back if the request handler raises and is always
    closed afterwards, preventing leaked connections.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for background jobs and CLI tasks."""
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
    """
    Execute a simple query to verify database connectivity and dialect.

    Error details are only returned outside production to avoid leaking host
    names, usernames, or driver internals to API clients.
    """
    dialect_name = engine.dialect.name
    try:
        with engine.connect() as connection:
            scalar = connection.execute(text("SELECT 1")).scalar()
            is_alive = scalar == 1
            return {
                "status": "healthy" if is_alive else "unhealthy",
                "connected": is_alive,
                "dialect": dialect_name,
                "url_type": "sqlite" if dialect_name == "sqlite" else "postgresql",
                "message": "Database ping successful",
                "pool": _pool_summary(),
            }
    except Exception as e:  # noqa: BLE001 - health checks must never raise
        logger.error("Database health check failed: %s", e)
        safe_message = (
            "Database connection failed. Verify DATABASE_URL and network access."
            if settings.is_production
            else str(e)
        )
        return {
            "status": "unhealthy",
            "connected": False,
            "dialect": dialect_name,
            "url_type": "sqlite" if dialect_name == "sqlite" else "postgresql",
            "message": safe_message,
            "pool": _pool_summary(),
        }


def _pool_summary() -> dict:
    """Best-effort, non-sensitive pool diagnostics."""
    pool = engine.pool
    try:
        return {
            "class": type(pool).__name__,
            "checked_out": pool.checkedout(),
            "size": pool.size(),
            "overflow": pool.overflow(),
        }
    except Exception:  # noqa: BLE001 - NullPool/StaticPool lack some methods
        return {"class": type(pool).__name__}
