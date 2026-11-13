"""
Dataset status and summary endpoints.
Provides aggregated statistics and import metadata.
"""

from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text
from app.database.session import get_db
from app.models.dataset_import import DatasetImport
from app.models.transaction import Transaction
from app.models.ground_truth import TransactionGroundTruth
from app.schemas.dataset import (
    DatasetStatusResponse,
    DatasetSummaryResponse,
    ChannelMetric,
    CategoryMetric,
    DailyVolumeMetric,
    AmountBucketMetric,
    GroundTruthEvaluationSummary,
)
from app.schemas.common import APIResponse

router = APIRouter(prefix="/dataset", tags=["Dataset"])


@router.get(
    "/status",
    response_model=APIResponse[DatasetStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Dataset Import Status",
    description="Check the latest dataset import status and metadata.",
)
def get_dataset_status(db: Session = Depends(get_db)) -> APIResponse[DatasetStatusResponse]:
    latest = db.execute(
        select(DatasetImport).order_by(DatasetImport.imported_at.desc()).limit(1)
    ).scalar_one_or_none()

    if not latest:
        return APIResponse(
            success=True,
            message="No dataset imported yet",
            data=DatasetStatusResponse(
                import_status="EMPTY",
                total_rows=0,
                imported_rows=0,
                skipped_rows=0,
            ),
        )

    return APIResponse(
        success=True,
        message="Dataset import status retrieved",
        data=DatasetStatusResponse(
            import_status=latest.status,
            dataset_id=latest.dataset_id,
            source_filename=latest.source_filename,
            checksum_sha256=latest.checksum_sha256,
            imported_at=latest.imported_at,
            total_rows=latest.total_rows,
            imported_rows=latest.imported_rows,
            skipped_rows=latest.skipped_rows,
            date_range_start=latest.date_range_start,
            date_range_end=latest.date_range_end,
            duration_seconds=latest.duration_seconds,
        ),
    )


@router.get(
    "/summary",
    response_model=APIResponse[DatasetSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Dataset Summary Statistics",
    description="Calculates comprehensive metrics across all ingested transactions and dataset labels.",
)
def get_dataset_summary(db: Session = Depends(get_db)) -> APIResponse[DatasetSummaryResponse]:
    # Core aggregates
    agg = db.execute(
        select(
            func.count(Transaction.transaction_id).label("total"),
            func.sum(Transaction.amount).label("volume"),
            func.avg(Transaction.amount).label("avg_amt"),
            func.min(Transaction.amount).label("min_amt"),
            func.max(Transaction.amount).label("max_amt"),
            func.min(Transaction.timestamp).label("date_start"),
            func.max(Transaction.timestamp).label("date_end"),
        )
    ).one()

    total = agg.total or 0

    if total == 0:
        return APIResponse(
            success=True,
            message="No transactions available in dataset",
            data=DatasetSummaryResponse(
                total_transactions=0,
                total_volume_inr=0.0,
                avg_transaction_inr=0.0,
                min_transaction_inr=0.0,
                max_transaction_inr=0.0,
                unique_senders=0,
                unique_receivers=0,
                unique_accounts_total=0,
                date_range={"start": None, "end": None},
                channel_distribution=[],
                category_distribution=[],
                daily_volume=[],
                amount_buckets=[],
                missing_metadata_counts={"device_id": 0, "location": 0, "sender_balance_before": 0},
                ground_truth_evaluation=GroundTruthEvaluationSummary(
                    total_evaluated_rows=0,
                    ground_truth_fraud_count=0,
                    ground_truth_fraud_rate=0.0,
                    ground_truth_aml_count=0,
                    ground_truth_aml_rate=0.0,
                    ground_truth_edge_cases_count=0,
                    pattern_breakdown={},
                ),
            ),
        )

    # Unique account counts
    unique_senders = db.execute(
        select(func.count(func.distinct(Transaction.sender_account_id)))
    ).scalar_one()
    unique_receivers = db.execute(
        select(func.count(func.distinct(Transaction.receiver_account_id)))
    ).scalar_one()
    all_accounts = db.execute(
        select(func.count()).select_from(
            select(Transaction.sender_account_id.label("acc"))
            .union(select(Transaction.receiver_account_id.label("acc")))
            .subquery()
        )
    ).scalar_one()

    # Channel distribution
    channel_rows = db.execute(
        select(
            Transaction.channel,
            func.count().label("cnt"),
            func.sum(Transaction.amount).label("vol"),
        )
        .group_by(Transaction.channel)
        .order_by(func.count().desc())
    ).all()
    channel_dist = [
        ChannelMetric(
            channel=r.channel,
            count=r.cnt,
            volume=float(r.vol or 0),
            percentage=round(r.cnt / total * 100, 2),
        )
        for r in channel_rows
    ]

    # Category distribution
    cat_rows = db.execute(
        select(
            Transaction.merchant_category,
            func.count().label("cnt"),
            func.sum(Transaction.amount).label("vol"),
        )
        .group_by(Transaction.merchant_category)
        .order_by(func.count().desc())
    ).all()
    cat_dist = [
        CategoryMetric(
            category=r.merchant_category,
            count=r.cnt,
            volume=float(r.vol or 0),
            percentage=round(r.cnt / total * 100, 2),
        )
        for r in cat_rows
    ]

    # Daily volume (SQLite strftime / portable date grouping)
    daily_rows = db.execute(
        text(
            "SELECT substr(timestamp, 1, 10) as day, "
            "COUNT(*) as cnt, SUM(amount) as vol "
            "FROM transactions "
            "GROUP BY day ORDER BY day"
        )
    ).all()
    daily_vol = [
        DailyVolumeMetric(date=str(r.day), count=r.cnt, volume=float(r.vol or 0))
        for r in daily_rows
    ]

    # Amount buckets
    buckets = [
        ("0-1K", 0, 1_000),
        ("1K-10K", 1_000, 10_000),
        ("10K-50K", 10_000, 50_000),
        ("50K-1L", 50_000, 100_000),
        ("1L-5L", 100_000, 500_000),
        ("5L+", 500_000, float("inf")),
    ]
    amount_buckets = []
    for label, lo, hi in buckets:
        q = select(func.count()).select_from(Transaction).where(Transaction.amount >= lo)
        if hi != float("inf"):
            q = q.where(Transaction.amount < hi)
        cnt = db.execute(q).scalar_one()
        amount_buckets.append(
            AmountBucketMetric(
                bucket=label,
                min_val=lo,
                max_val=hi if hi != float("inf") else -1,
                count=cnt,
                percentage=round(cnt / total * 100, 2),
            )
        )

    # Missing metadata
    missing = {
        "device_id": db.execute(
            select(func.count()).select_from(Transaction).where(Transaction.device_id.is_(None))
        ).scalar_one(),
        "location": db.execute(
            select(func.count()).select_from(Transaction).where(Transaction.location.is_(None))
        ).scalar_one(),
        "sender_balance_before": db.execute(
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.sender_balance_before.is_(None))
        ).scalar_one(),
    }

    # Ground truth evaluation summary
    gt_agg = db.execute(
        select(
            func.count().label("total"),
            func.sum(TransactionGroundTruth.is_fraud).label("fraud_cnt"),
            func.sum(TransactionGroundTruth.is_aml_pattern).label("aml_cnt"),
            func.sum(TransactionGroundTruth.is_edge_case).label("edge_cnt"),
        )
    ).one()
    gt_total = gt_agg.total or 1

    pattern_rows = db.execute(
        select(TransactionGroundTruth.pattern_type, func.count().label("cnt"))
        .group_by(TransactionGroundTruth.pattern_type)
        .order_by(func.count().desc())
    ).all()
    pattern_breakdown = {r.pattern_type: r.cnt for r in pattern_rows}

    gt_eval = GroundTruthEvaluationSummary(
        total_evaluated_rows=gt_agg.total or 0,
        ground_truth_fraud_count=int(gt_agg.fraud_cnt or 0),
        ground_truth_fraud_rate=round(int(gt_agg.fraud_cnt or 0) / gt_total * 100, 4),
        ground_truth_aml_count=int(gt_agg.aml_cnt or 0),
        ground_truth_aml_rate=round(int(gt_agg.aml_cnt or 0) / gt_total * 100, 4),
        ground_truth_edge_cases_count=int(gt_agg.edge_cnt or 0),
        pattern_breakdown=pattern_breakdown,
    )

    return APIResponse(
        success=True,
        message="Dataset summary retrieved successfully",
        data=DatasetSummaryResponse(
            total_transactions=total,
            total_volume_inr=float(agg.volume or 0),
            avg_transaction_inr=float(agg.avg_amt or 0),
            min_transaction_inr=float(agg.min_amt or 0),
            max_transaction_inr=float(agg.max_amt or 0),
            unique_senders=unique_senders,
            unique_receivers=unique_receivers,
            unique_accounts_total=all_accounts,
            date_range={
                "start": str(agg.date_start) if agg.date_start else None,
                "end": str(agg.date_end) if agg.date_end else None,
            },
            channel_distribution=channel_dist,
            category_distribution=cat_dist,
            daily_volume=daily_vol,
            amount_buckets=amount_buckets,
            missing_metadata_counts=missing,
            ground_truth_evaluation=gt_eval,
        ),
    )
