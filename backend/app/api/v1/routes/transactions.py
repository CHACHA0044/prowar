"""
Transactions API — Static CSV Data Architecture.
Operational transaction records served directly from the loaded dataset.
Ground-truth evaluation labels are strictly excluded.
"""

from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.dataset_service import dataset_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get(
    "",
    response_model=APIResponse[PaginatedResponse[TransactionResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Transactions",
    description="Query ingested transactions with optional filtering, sorting, and pagination.",
)
def list_transactions(
    # Pagination
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    # Filters
    search: Optional[str] = Query(None, description="Text search on transaction_id, sender, receiver"),
    sender_id: Optional[str] = Query(None, description="Exact sender account ID"),
    receiver_id: Optional[str] = Query(None, description="Exact receiver account ID"),
    channel: Optional[str] = Query(None, description="Transaction channel filter"),
    merchant_category: Optional[str] = Query(None, description="Merchant category filter"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum transaction amount in INR"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum transaction amount in INR"),
    start_date: Optional[datetime] = Query(None, description="Filter transactions on or after this timestamp"),
    end_date: Optional[datetime] = Query(None, description="Filter transactions on or before this timestamp"),
    # Sorting
    sort_by: Literal["timestamp", "amount", "transaction_id"] = Query("timestamp"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
) -> APIResponse[PaginatedResponse[TransactionResponse]]:
    items, total = dataset_service.list_transactions(
        limit=limit,
        offset=offset,
        search=search,
        sender_id=sender_id,
        receiver_id=receiver_id,
        channel=channel,
        merchant_category=merchant_category,
        min_amount=min_amount,
        max_amount=max_amount,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    total_pages = (total + limit - 1) // limit if total > 0 else 0

    return APIResponse(
        success=True,
        message=f"Retrieved {len(items)} transactions",
        data=PaginatedResponse(
            items=items,
            total=total,
            page=offset // limit + 1,
            page_size=limit,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/{transaction_id}",
    response_model=APIResponse[TransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Transaction Detail",
    description="Retrieve an operational transaction record by its unique ID.",
)
def get_transaction(transaction_id: str) -> APIResponse[TransactionResponse]:
    tx = dataset_service.get_transaction(transaction_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{transaction_id}' not found",
        )
    return APIResponse(
        success=True,
        message="Transaction retrieved successfully",
        data=tx,
    )


@router.post(
    "",
    response_model=APIResponse[TransactionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Transaction",
    description="Validates and registers a new transaction into the processing pipeline.",
)
def ingest_transaction(payload: TransactionCreate) -> APIResponse[TransactionResponse]:
    tx = dataset_service.add_transaction(payload)
    return APIResponse(
        success=True,
        message="Transaction ingested successfully",
        data=tx,
    )
