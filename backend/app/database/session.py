"""
SQLAlchemy Session and Engine management.
Provides connection lifecycle and database health inspection.
"""

from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

# SQLite specific config
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session and safely closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> dict:
    """Execute a simple query to verify database connectivity and dialect."""
    dialect_name = engine.dialect.name
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            scalar = result.scalar()
            is_alive = scalar == 1
            return {
                "status": "healthy" if is_alive else "unhealthy",
                "connected": is_alive,
                "dialect": dialect_name,
                "url_type": "sqlite" if dialect_name == "sqlite" else "postgresql/other",
                "message": "Database ping successful",
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "dialect": dialect_name,
            "url_type": "sqlite" if dialect_name == "sqlite" else "postgresql/other",
            "message": str(e),
        }

