"""
Security Alerts router (Foundation Placeholder).
Provides listing, filtering, and status updates for security incidents.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.alert import AlertResponse, AlertCreate, AlertUpdateStatus
from backend.app.schemas.common import APIResponse, PaginatedResponse

router = APIRouter(prefix="/alerts", tags=["Security Alerts"])


@router.get(
    "",
    response_model=APIResponse[PaginatedResponse[AlertResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Security Alerts",
    description="Retrieve security alerts with optional severity and status filtering.",
)
def list_alerts(
    severity: Optional[str] = Query(None, description="LOW, MEDIUM, HIGH, CRITICAL"),
    status_filter: Optional[str] = Query(None, alias="status", description="OPEN, UNDER_REVIEW, RESOLVED, DISMISSED"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> APIResponse[PaginatedResponse[AlertResponse]]:
    return APIResponse(
        success=True,
        message="Alerts endpoint active. Alert triggers will be dispatched by scoring pipeline in Phase 2.",
        data=PaginatedResponse(
            items=[],
            total=0,
            page=offset // limit + 1,
            page_size=limit,
            total_pages=0,
        ),
    )


@router.post(
    "",
    response_model=APIResponse[AlertResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Alert",
    description="Interface for alert generation by detection engines.",
)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
) -> APIResponse[AlertResponse]:
    return APIResponse(
        success=True,
        message="Alert schema validated successfully.",
        data=AlertResponse(**payload.model_dump()),
    )

