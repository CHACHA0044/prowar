"""
FastAPI Application Entry Point.
AI-Powered Financial Fraud Detection & Anti-Money Laundering (AML) Platform.
Static CSV Data Architecture — Zero Database Dependencies.
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
from app.services.dataset_service import dataset_service
from app.services.simulator import simulator_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info("Starting %s v%s in '%s' mode.", settings.PROJECT_NAME, settings.APP_VERSION, settings.ENVIRONMENT)

    # Load static dataset into memory once at startup
    try:
        dataset_service.load_dataset(settings.DATASET_PATH)
        logger.info(
            "Static CSV dataset successfully loaded and indexed (%d records).",
            dataset_service.total_records,
        )
    except Exception as e:
        logger.error("Failed to load static CSV dataset: %s", e, exc_info=True)

    # Initialize simulator
    await simulator_service.initialize()

    yield

    logger.info("Shutting down application resources.")
    await simulator_service.shutdown()


def create_application() -> FastAPI:
    """Factory function for FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "AI-Powered Financial Fraud Detection, Behavioral Anomaly Monitoring, "
            "and Anti-Money Laundering (AML) Security Platform (Static CSV Architecture)."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Explicit CORS policy. Wildcards are rejected in production.
    cors_kwargs = {
        "allow_origins": settings.cors_origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept", "Authorization", "X-Control-Token"],
        "expose_headers": ["Content-Type", "Content-Length"],
        "max_age": 600,
    }
    if settings.CORS_ORIGIN_REGEX:
        cors_kwargs["allow_origin_regex"] = settings.CORS_ORIGIN_REGEX

    app.add_middleware(CORSMiddleware, **cors_kwargs)
    logger.info("Configured CORS allowed origins: %s", settings.cors_origins)

    # Centralized exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Mount API v1 router
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    @app.get(
        "/",
        status_code=status.HTTP_200_OK,
        summary="Service Root",
        description="Public informational root endpoint.",
    )
    def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.APP_VERSION,
            "architecture": "static_csv",
            "environment": settings.ENVIRONMENT,
            "docs_url": "/docs",
            "health_url": f"{settings.API_V1_STR}/health",
            "ready_url": f"{settings.API_V1_STR}/health/ready",
        }

    return app


app = create_application()
