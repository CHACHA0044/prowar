"""
Pydantic schemas for Dataset status, summary, and ingestion reporting.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DatasetStatusResponse(BaseModel):
    import_status: str = Field(..., description="PENDING, COMPLETED, FAILED, EMPTY")
    dataset_id: Optional[str] = None
    source_filename: Optional[str] = None
    checksum_sha256: Optional[str] = None
    imported_at: Optional[datetime] = None
    total_rows: int = 0
    imported_rows: int = 0
    skipped_rows: int = 0
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class ChannelMetric(BaseModel):
    channel: str
    count: int
    volume: float
    percentage: float


class CategoryMetric(BaseModel):
    category: str
    count: int
    volume: float
    percentage: float


class DailyVolumeMetric(BaseModel):
    date: str
    count: int
    volume: float


class AmountBucketMetric(BaseModel):
    bucket: str
    min_val: float
    max_val: float
    count: int
    percentage: float


class GroundTruthEvaluationSummary(BaseModel):
    """
    STRICTLY SEPARATED evaluation metadata for dataset quality transparency.
    NOT exposed as model detection results.
    """
    total_evaluated_rows: int
    ground_truth_fraud_count: int
    ground_truth_fraud_rate: float
    ground_truth_aml_count: int
    ground_truth_aml_rate: float
    ground_truth_edge_cases_count: int
    pattern_breakdown: Dict[str, int]


class DatasetSummaryResponse(BaseModel):
    total_transactions: int
    total_volume_inr: float
    avg_transaction_inr: float
    min_transaction_inr: float
    max_transaction_inr: float
    unique_senders: int
    unique_receivers: int
    unique_accounts_total: int
    date_range: Dict[str, Optional[str]]
    channel_distribution: List[ChannelMetric]
    category_distribution: List[CategoryMetric]
    daily_volume: List[DailyVolumeMetric]
    amount_buckets: List[AmountBucketMetric]
    missing_metadata_counts: Dict[str, int]
    ground_truth_evaluation: GroundTruthEvaluationSummary

