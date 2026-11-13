"""Alembic environment for Sentinel.AML.

The database URL comes from ``DATABASE_URL`` through application settings, so
no credentials live in this repository. The same engine configuration used by
the API (SSL mode, timeouts, pooling) is reused for migrations.
"""

from logging.config import fileConfig

from alembic import context

from app.core.config import settings
from app.database.base import Base
from app.database.session import engine

# Register every model on Base.metadata.
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
is_sqlite = engine.dialect.name == "sqlite"


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (emits SQL)."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=is_sqlite,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the configured database."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=is_sqlite,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
