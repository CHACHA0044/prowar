"""
Centralized Application Configuration.
Manages environment variables, security settings, and database connectivity.
"""

from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """
    Normalize legacy/shorthand PostgreSQL URLs to the explicit psycopg2 dialect.

    Supabase and Render hand out URLs beginning with ``postgres://`` or
    ``postgresql://``. SQLAlchemy needs a driver name, so we map both to
    ``postgresql+psycopg2://``. Other URLs (including SQLite) pass through.
    """
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://") :]
    return url


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    PROJECT_NAME: str = "Financial Fraud Detection & AML Security Platform"
    APP_VERSION: str = "0.2.5"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server binding
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000

    # CORS configuration
    # Accepts comma-separated string or list of URLs.
    # Production origins are configured explicitly; localhost is only kept in
    # non-production environments (or when ALLOW_LOCALHOST_ORIGINS is enabled).
    ALLOWED_ORIGINS: Union[str, List[str]] = (
        "https://prowar-rho.vercel.app,http://localhost:3000,http://127.0.0.1:3000"
    )
    ALLOW_LOCALHOST_ORIGINS: bool = False
    # Optional scoped regex for Vercel preview deployments. Leave unset to
    # allow only the exact origins listed above.
    CORS_ORIGIN_REGEX: Optional[str] = None

    # Database configuration (SQLite by default, PostgreSQL for production)
    DATABASE_URL: str = "sqlite:///./financial_fraud_aml.db"

    # Connection pool tuning (ignored for SQLite)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_TIMEOUT: int = 30
    DB_CONNECT_TIMEOUT: int = 10
    DB_SSL_MODE: Optional[str] = "require"
    DB_ECHO: bool = False

    # Schema management.
    # None => auto-create tables only outside production. Migrations should be
    # applied with Alembic in production.
    AUTO_CREATE_SCHEMA: Optional[bool] = None

    # Optional shared token protecting simulator/admin mutation endpoints.
    # When unset, control endpoints remain public demo controls (documented
    # limitation). Set CONTROL_API_TOKEN on Render to require the X-Control-Token
    # header for all simulator control mutations.
    CONTROL_API_TOKEN: Optional[str] = None

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _normalize_origins_input(cls, value):
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                import json

                return json.loads(stripped)
        return value

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}

    @property
    def database_url(self) -> str:
        """Normalized SQLAlchemy database URL."""
        return normalize_database_url(self.DATABASE_URL)

    @property
    def is_postgresql(self) -> bool:
        return self.database_url.startswith("postgresql")

    @property
    def effective_auto_create_schema(self) -> bool:
        if self.AUTO_CREATE_SCHEMA is not None:
            return self.AUTO_CREATE_SCHEMA
        return not self.is_production

    @property
    def cors_origins(self) -> List[str]:
        """Parsed, validated list of allowed CORS origins."""
        if isinstance(self.ALLOWED_ORIGINS, list):
            raw_origins = self.ALLOWED_ORIGINS
        else:
            raw_origins = self.ALLOWED_ORIGINS.split(",")

        origins: List[str] = []
        for origin in raw_origins:
            cleaned = origin.strip().rstrip("/")
            if not cleaned:
                continue
            if cleaned == "*":
                if self.is_production:
                    raise ValueError(
                        "Wildcard CORS origins are not allowed in production. "
                        "Configure ALLOWED_ORIGINS explicitly."
                    )
                origins.append(cleaned)
                continue
            origins.append(cleaned)

        if self.is_production and not self.ALLOW_LOCALHOST_ORIGINS:
            origins = [
                origin
                for origin in origins
                if "localhost" not in origin and "127.0.0.1" not in origin
            ]

        # Preserve order while removing duplicates.
        return list(dict.fromkeys(origins))

    @property
    def control_token_required(self) -> bool:
        return bool(self.CONTROL_API_TOKEN)

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
