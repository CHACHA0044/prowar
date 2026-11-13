"""
Transactions router (Foundation Placeholder).
Provides endpoints for transaction ingestion, filtering, and detail retrieval.
"""

from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionFilter,
)
from backend.app.schemas.common import APIResponse, PaginatedResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get(
    "",
    response_model=APIResponse[PaginatedResponse[TransactionResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Transactions",
    description="Query ingested transactions with optional filtering and pagination.",
)
def list_transactions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> APIResponse[PaginatedResponse[TransactionResponse]]:
    # In Phase 1 foundation: returns empty list with valid pagination schema
    return APIResponse(
        success=True,
        message="Transactions endpoint ready. Ingestion pipeline will populate records in Phase 2.",
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
    response_model=APIResponse[TransactionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Transaction",
    description="Validates and registers a new transaction into the processing pipeline.",
)
def ingest_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
) -> APIResponse[TransactionResponse]:
    # Placeholder validation echo in Phase 1
    return APIResponse(
        success=True,
        message="Transaction validated successfully according to data contract.",
        data=TransactionResponse(**payload.model_dump()),
    )

