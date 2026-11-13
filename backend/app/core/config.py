"""
Centralized Application Configuration.
Manages environment variables, security settings, and static CSV paths.
Zero Database Dependencies.
"""

from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    PROJECT_NAME: str = "Financial Fraud Detection & AML Security Platform"
    APP_VERSION: str = "0.2.6"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server binding
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # Path to static transactions dataset (optional override, auto-discovered if unset)
    DATASET_PATH: Optional[str] = None

    # CORS configuration
    # Accepts comma-separated string or list of URLs.
    # Production origins are configured explicitly; localhost is only kept in
    # non-production environments (or when ALLOW_LOCALHOST_ORIGINS is enabled).
    ALLOWED_ORIGINS: Union[str, List[str]] = (
        "https://prowar-rho.vercel.app,http://localhost:3000,http://127.0.0.1:3000"
    )
    ALLOW_LOCALHOST_ORIGINS: bool = False
    CORS_ORIGIN_REGEX: Optional[str] = None

    # Optional shared token protecting simulator/admin mutation endpoints.
    # When unset, control endpoints remain public demo controls (documented limitation).
    # Set CONTROL_API_TOKEN on Render to require the X-Control-Token header.
    CONTROL_API_TOKEN: Optional[str] = None

    # Optional legacy database URL (ignored in static CSV architecture)
    DATABASE_URL: Optional[str] = None

    # Render free-tier keepalive self-ping configuration
    # Note: Automated pings do not guarantee prevention of Render's free-tier sleep or override its inactivity policies.
    SELF_PING_ENABLED: bool = True
    SELF_PING_INTERVAL_SECONDS: int = 180  # 3 minutes default
    SELF_PING_URL: Optional[str] = None
    RENDER_EXTERNAL_URL: Optional[str] = None  # Render auto-populates this on Web Services

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
