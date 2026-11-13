"""
Dataset status and summary endpoints.
Provides aggregated statistics and import metadata from the static CSV dataset.
"""

from fastapi import APIRouter, status

from app.schemas.common import APIResponse
from app.schemas.dataset import (
    DatasetStatusResponse,
    DatasetSummaryResponse,
)
from app.services.dataset_service import dataset_service

router = APIRouter(prefix="/dataset", tags=["Dataset"])


@router.get(
    "/status",
    response_model=APIResponse[DatasetStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Dataset Import Status",
    description="Check the static dataset status, SHA-256 checksum, and record counts.",
)
def get_dataset_status() -> APIResponse[DatasetStatusResponse]:
    status_data = dataset_service.get_status()
    return APIResponse(
        success=True,
        message="Dataset status retrieved",
        data=status_data,
    )


@router.get(
    "/summary",
    response_model=APIResponse[DatasetSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Dataset Summary Statistics",
    description="Calculates comprehensive metrics across all ingested transactions and ground-truth evaluation metadata.",
)
def get_dataset_summary() -> APIResponse[DatasetSummaryResponse]:
    summary_data = dataset_service.get_summary()
    return APIResponse(
        success=True,
        message="Dataset summary retrieved successfully",
        data=summary_data,
    )
