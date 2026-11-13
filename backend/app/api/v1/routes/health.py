"""
Health check endpoints.
Provides real-time system and database health status.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import check_db_health, get_db
from app.schemas.health import SystemHealthResponse, DatabaseHealthResponse, ComponentHealth
from app.utils.timestamps import utc_now

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


@router.get(
    "",
    response_model=SystemHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health Check",
    description="Returns aggregate health status for the API service and its core subsystems.",
)
def get_system_health() -> SystemHealthResponse:
    db_health = check_db_health()
    db_status = "healthy" if db_health.get("connected") else "unhealthy"

    components = {
        "api_gateway": ComponentHealth(
            status="healthy",
            message="FastAPI service is running and accepting requests.",
        ),
        "database": ComponentHealth(
            status=db_status,
            message=db_health.get("message", "Database connection verified."),
            details={"dialect": db_health.get("dialect")},
        ),
        "ml_engine": ComponentHealth(
            status="healthy",
            message="ML subsystem interface initialized (Phase 1 foundation ready).",
        ),
    }

    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return SystemHealthResponse(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        timestamp=utc_now(),
        version="0.1.0",
        components=components,
    )


@router.get(
    "/database",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Database Health Check",
    description="Tests direct connectivity to the configured database engine.",
)
def get_database_health() -> DatabaseHealthResponse:
    health = check_db_health()
    return DatabaseHealthResponse(
        status=health["status"],
        connected=health["connected"],
        dialect=health["dialect"],
        url_type=health["url_type"],
        message=health["message"],
        timestamp=utc_now(),
    )

