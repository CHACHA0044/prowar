"""
FastAPI Application Entry Point.
AI-Powered Financial Fraud Detection & Anti-Money Laundering (AML) Platform.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import logger
from app.database.base import Base
from app.database.session import check_db_health, engine
from app.services.simulator import simulator_service

# Import models to ensure metadata registration.
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info("Starting %s v%s in '%s' mode.", settings.PROJECT_NAME, settings.APP_VERSION, settings.ENVIRONMENT)

    db_health = check_db_health()
    if db_health["connected"]:
        logger.info(
            "Database connection verified (dialect=%s, pool=%s).",
            db_health["dialect"],
            db_health.get("pool", {}).get("class"),
        )
    else:
        logger.error("Database is not reachable at startup: %s", db_health["message"])

    if settings.effective_auto_create_schema:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database schema verified and initialized (auto-create enabled).")
        except Exception as e:  # noqa: BLE001 - startup must report, not crash silently
            logger.error("Failed to initialize database tables: %s", e)
    else:
        logger.info(
            "AUTO_CREATE_SCHEMA disabled for '%s'. Apply migrations with 'alembic upgrade head'.",
            settings.ENVIRONMENT,
        )

    await simulator_service.initialize()

    yield

    logger.info("Shutting down application resources.")
    await simulator_service.shutdown()
    engine.dispose()


def create_application() -> FastAPI:
    """Factory function for FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "AI-Powered Financial Fraud Detection, Behavioral Anomaly Monitoring, "
            "and Anti-Money Laundering (AML) Security Platform."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Explicit CORS policy. Wildcards are rejected by settings in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.CORS_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Authorization",
            "Cache-Control",
            "Content-Type",
            "Last-Event-ID",
            "Origin",
            "X-Control-Token",
            "X-Requested-With",
        ],
        expose_headers=["Content-Type"],
        max_age=600,
    )

    # Centralized exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Register API Routers
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    # Root redirect / baseline endpoint
    @app.get("/", tags=["Root"], status_code=status.HTTP_200_OK)
    def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.APP_VERSION,
            "status": "online",
            "environment": settings.ENVIRONMENT,
            "docs": "/docs",
            "health": f"{settings.API_V1_STR}/health",
        }

    return app


app = create_application()
