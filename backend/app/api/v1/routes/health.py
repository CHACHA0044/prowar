"""
Health check endpoints.
Provides real-time system and database health status.
"""

from fastapi import APIRouter, HTTPException, status
from app.core.config import settings
from app.database.session import check_db_health
from app.schemas.health import SystemHealthResponse, DatabaseHealthResponse, ComponentHealth
from app.utils.timestamps import utc_now

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Cheap process liveness check. Does not touch the database.",
)
def get_liveness() -> dict:
    return {"status": "alive", "environment": settings.ENVIRONMENT}


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Returns 200 only when the API can reach its database. Used by Render.",
)
def get_readiness() -> dict:
    db_health = check_db_health()
    if not db_health.get("connected"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not reachable.",
        )
    return {
        "status": "ready",
        "database": db_health.get("dialect"),
        "environment": settings.ENVIRONMENT,
    }


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

