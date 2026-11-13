"""
FastAPI Application Entry Point.
AI-Powered Financial Fraud Detection & Anti-Money Laundering (AML) Platform.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from backend.app.database.base import Base
from backend.app.database.session import engine
from backend.app.api.v1.router import api_v1_router
# Import models to ensure metadata registration
import backend.app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info(
        f"Starting {settings.PROJECT_NAME} in '{settings.ENVIRONMENT}' mode."
    )
    # Ensure database schema is created for SQLite/local development
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified and initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")

    yield

    logger.info("Shutting down application resources.")


def create_application() -> FastAPI:
    """Factory function for FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "AI-Powered Financial Fraud Detection, Behavioral Anomaly Monitoring, "
            "and Anti-Money Laundering (AML) Security Platform."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure Cross-Origin Resource Sharing (CORS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
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
            "version": "0.1.0",
            "status": "online",
            "docs": "/docs",
            "health": f"{settings.API_V1_STR}/health",
        }

    return app


app = create_application()

