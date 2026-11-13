"""
Transactions API — real DB-backed implementation.
Operational fields only; ground-truth labels never exposed.
"""

from typing import Optional, Literal
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, asc, desc, or_, and_
from app.database.session import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionResponse, TransactionCreate
from app.schemas.common import APIResponse, PaginatedResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])

SORT_COLUMNS = {
    "timestamp": Transaction.timestamp,
    "amount": Transaction.amount,
    "transaction_id": Transaction.transaction_id,
}


@router.get(
    "",
    response_model=APIResponse[PaginatedResponse[TransactionResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Transactions",
    description="Query ingested transactions with optional filtering, sorting and server-side pagination.",
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
    db: Session = Depends(get_db),
) -> APIResponse[PaginatedResponse[TransactionResponse]]:
    stmt = select(Transaction)
    count_stmt = select(func.count()).select_from(Transaction)

    conditions = []
    if search:
        like = f"%{search}%"
        conditions.append(
            or_(
                Transaction.transaction_id.ilike(like),
                Transaction.sender_account_id.ilike(like),
                Transaction.receiver_account_id.ilike(like),
            )
        )
    if sender_id:
        conditions.append(Transaction.sender_account_id == sender_id)
    if receiver_id:
        conditions.append(Transaction.receiver_account_id == receiver_id)
    if channel:
        conditions.append(Transaction.channel == channel)
    if merchant_category:
        conditions.append(Transaction.merchant_category == merchant_category)
    if min_amount is not None:
        conditions.append(Transaction.amount >= min_amount)
    if max_amount is not None:
        conditions.append(Transaction.amount <= max_amount)
    if start_date:
        conditions.append(Transaction.timestamp >= start_date)
    if end_date:
        conditions.append(Transaction.timestamp <= end_date)

    if conditions:
        stmt = stmt.where(and_(*conditions))
        count_stmt = count_stmt.where(and_(*conditions))

    sort_col = SORT_COLUMNS.get(sort_by, Transaction.timestamp)
    stmt = stmt.order_by(desc(sort_col) if sort_order == "desc" else asc(sort_col))
    stmt = stmt.limit(limit).offset(offset)

    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(stmt).scalars().all()

    items = [TransactionResponse.model_validate(r) for r in rows]
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
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
) -> APIResponse[TransactionResponse]:
    tx = db.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{transaction_id}' not found",
        )
    return APIResponse(
        success=True,
        message="Transaction retrieved successfully",
        data=TransactionResponse.model_validate(tx),
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
    tx = Transaction(
        transaction_id=payload.transaction_id,
        timestamp=payload.timestamp,
        sender_account_id=payload.sender_account_id,
        receiver_account_id=payload.receiver_account_id,
        amount=payload.amount,
        currency=payload.currency,
        channel=payload.channel,
        merchant_category=payload.merchant_category,
        device_id=payload.device_id,
        location=payload.location,
        sender_balance_before=payload.sender_balance_before,
        transaction_status=payload.transaction_status,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return APIResponse(
        success=True,
        message="Transaction ingested successfully",
        data=TransactionResponse.model_validate(tx),
    )
