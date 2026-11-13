"""
Health check endpoints.
Provides real-time system and dataset storage health status.
"""

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.schemas.health import ComponentHealth, DatabaseHealthResponse, SystemHealthResponse
from app.services.dataset_service import dataset_service
from app.utils.timestamps import utc_now

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Cheap process liveness check for container orchestrators.",
)
def get_liveness() -> dict:
    return {"status": "alive", "environment": settings.ENVIRONMENT}


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Returns 200 only when the static dataset has been loaded and indexed. Used by Render.",
)
def get_readiness() -> dict:
    if not dataset_service.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Static dataset is loading or unavailable.",
        )
    return {
        "status": "ready",
        "dataset": "loaded",
        "records": dataset_service.total_records,
        "environment": settings.ENVIRONMENT,
    }


@router.get(
    "",
    response_model=SystemHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health Check",
    description="Returns aggregate health status for the API service and its static data repository.",
)
def get_system_health() -> SystemHealthResponse:
    is_ready = dataset_service.is_ready
    ds_status = "healthy" if is_ready else "degraded"
    records_count = dataset_service.total_records if is_ready else 0

    components = {
        "api_gateway": ComponentHealth(
            status="healthy",
            message="FastAPI service is running and accepting requests.",
        ),
        "database": ComponentHealth(
            status=ds_status,
            message=f"Static CSV data repository active ({records_count:,} records).",
            details={"storage_type": "static_csv", "records": records_count},
        ),
        "ml_engine": ComponentHealth(
            status="healthy",
            message="ML subsystem interface initialized (Phase 1/2 foundation active).",
        ),
    }

    return SystemHealthResponse(
        status="healthy" if is_ready else "degraded",
        environment=settings.ENVIRONMENT,
        timestamp=utc_now(),
        version="0.2.6",
        components=components,
    )


@router.get(
    "/database",
    response_model=DatabaseHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Data Storage Health Check",
    description="Reports the operational status of the static CSV data repository.",
)
def get_database_health() -> DatabaseHealthResponse:
    is_ready = dataset_service.is_ready
    records = dataset_service.total_records if is_ready else 0
    return DatabaseHealthResponse(
        status="healthy" if is_ready else "degraded",
        connected=is_ready,
        dialect="static_csv",
        url_type="file",
        message=f"Static CSV repository active ({records:,} transactions loaded in-memory).",
        timestamp=utc_now(),
    )
