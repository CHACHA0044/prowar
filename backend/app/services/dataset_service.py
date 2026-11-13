"""
Static CSV Dataset Service.
Loads, validates, and indexes transactions from data/transactions.csv in-memory.
Provides high-performance filtering, sorting, pagination, and aggregate analytics
without requiring an external database.
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.core.logging import logger
from app.schemas.dataset import (
    AmountBucketMetric,
    CategoryMetric,
    ChannelMetric,
    DailyVolumeMetric,
    DatasetStatusResponse,
    DatasetSummaryResponse,
    GroundTruthEvaluationSummary,
)
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.utils.timestamps import utc_now

CSV_DTYPES = {
    "txn_id": str,
    "sender_id": str,
    "receiver_id": str,
    "channel": str,
    "merchant_category": str,
    "device_id": str,
    "location": str,
    "pattern_type": str,
    "scenario_id": str,
    "edge_case_type": str,
}


def calculate_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file in 64KB blocks."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def find_dataset_csv_path(custom_path: Optional[str] = None) -> Path:
    """Locate the dataset CSV across development and Render deployment environments."""
    if custom_path:
        p = Path(custom_path).expanduser().resolve()
        if p.is_file():
            return p

    candidates = [
        Path("data/transactions.csv"),
        Path("../data/transactions.csv"),
        Path(__file__).resolve().parents[3] / "data" / "transactions.csv",
        Path.cwd() / "data" / "transactions.csv",
        Path.cwd() / ".." / "data" / "transactions.csv",
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    raise FileNotFoundError(
        f"transactions.csv could not be found. Checked candidate locations: "
        f"{[str(c.resolve()) for c in candidates]}"
    )


class StaticCSVDatasetService:
    """
    In-memory static dataset repository.
    Read-only, thread-safe, and zero database dependencies.
    """

    def __init__(self):
        self._is_ready: bool = False
        self._source_path: Optional[Path] = None
        self._checksum: str = ""
        self._df: Optional[pd.DataFrame] = None
        self._records_by_id: Dict[str, TransactionResponse] = {}
        self._chronological_records: List[TransactionResponse] = []
        self._status_response: Optional[DatasetStatusResponse] = None
        self._summary_response: Optional[DatasetSummaryResponse] = None
        self._dynamic_records: List[TransactionResponse] = []

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    @property
    def total_records(self) -> int:
        return len(self._records_by_id)

    def load_dataset(self, custom_path: Optional[str] = None) -> None:
        """Load and index transactions.csv into memory once at application boot."""
        csv_path = find_dataset_csv_path(custom_path)
        logger.info("Loading static dataset from %s", csv_path)
        start_time = datetime.now()

        self._source_path = csv_path
        self._checksum = calculate_sha256(csv_path)

        df = pd.read_csv(csv_path, dtype=CSV_DTYPES)
        load_duration = (datetime.now() - start_time).total_seconds()
        logger.info("Loaded %d rows in %.2fs. Pre-computing analytics and indexes...", len(df), load_duration)

        # Parse timestamps into datetime objects
        df["parsed_timestamp"] = pd.to_datetime(df["timestamp"])
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
        df["currency"] = "INR"
        df["transaction_status"] = "COMPLETED"

        # Missing values normalization
        df["device_id"] = df["device_id"].replace({np.nan: None})
        df["location"] = df["location"].replace({np.nan: None})
        df["sender_balance_before"] = pd.to_numeric(df["sender_balance_before"], errors="coerce").replace({np.nan: None})

        # Ground truth columns normalization
        df["is_fraud"] = df["is_fraud"].fillna(0).astype(int)
        df["is_aml_pattern"] = df["is_aml_pattern"].fillna(0).astype(int)
        df["pattern_type"] = df["pattern_type"].fillna("normal").astype(str)
        df["scenario_id"] = df["scenario_id"].replace({np.nan: None})
        df["is_edge_case"] = df["is_edge_case"].fillna(0).astype(int)
        df["edge_case_type"] = df["edge_case_type"].replace({np.nan: None})

        # Cache DataFrame for filtering operations
        self._df = df

        # Build chronological records for simulation and O(1) dictionary for ID lookup
        sorted_df = df.sort_values(by=["parsed_timestamp", "txn_id"], ascending=[True, True])
        chronological: List[TransactionResponse] = []
        by_id: Dict[str, TransactionResponse] = {}

        for _, row in sorted_df.iterrows():
            tx = TransactionResponse(
                transaction_id=str(row["txn_id"]),
                timestamp=row["parsed_timestamp"].to_pydatetime(),
                sender_account_id=str(row["sender_id"]),
                receiver_account_id=str(row["receiver_id"]),
                amount=float(row["amount"]),
                currency="INR",
                channel=str(row["channel"]),
                merchant_category=str(row["merchant_category"]),
                device_id=row["device_id"],
                location=row["location"],
                sender_balance_before=float(row["sender_balance_before"]) if row["sender_balance_before"] is not None else None,
                transaction_status="COMPLETED",
            )
            chronological.append(tx)
            by_id[tx.transaction_id] = tx

        self._chronological_records = chronological
        self._records_by_id = by_id

        # Compute pre-aggregated summary statistics
        self._precompute_status_and_summary(df, load_duration)
        self._is_ready = True
        logger.info("Static dataset service ready. Indexed %d operational records.", len(by_id))

    def _precompute_status_and_summary(self, df: pd.DataFrame, load_duration: float) -> None:
        total = len(df)
        min_ts = df["parsed_timestamp"].min().to_pydatetime()
        max_ts = df["parsed_timestamp"].max().to_pydatetime()

        self._status_response = DatasetStatusResponse(
            import_status="COMPLETED",
            dataset_id="synthetic-promptwars-2026",
            source_filename="transactions.csv",
            checksum_sha256=self._checksum,
            imported_at=utc_now(),
            total_rows=total,
            imported_rows=total,
            skipped_rows=0,
            date_range_start=min_ts,
            date_range_end=max_ts,
            duration_seconds=round(load_duration, 3),
        )

        # Unique counterparties
        senders_set = set(df["sender_id"].unique())
        receivers_set = set(df["receiver_id"].unique())
        unique_senders = len(senders_set)
        unique_receivers = len(receivers_set)
        all_accounts = len(senders_set.union(receivers_set))

        # Channel distribution
        channel_counts = df.groupby("channel").agg(
            count=("txn_id", "count"),
            volume=("amount", "sum"),
        ).reset_index()
        channel_dist = [
            ChannelMetric(
                channel=str(r["channel"]),
                count=int(r["count"]),
                volume=float(r["volume"]),
                percentage=round(int(r["count"]) / total * 100, 2),
            )
            for _, r in channel_counts.sort_values(by="count", ascending=False).iterrows()
        ]

        # Category distribution
        cat_counts = df.groupby("merchant_category").agg(
            count=("txn_id", "count"),
            volume=("amount", "sum"),
        ).reset_index()
        cat_dist = [
            CategoryMetric(
                category=str(r["merchant_category"]),
                count=int(r["count"]),
                volume=float(r["volume"]),
                percentage=round(int(r["count"]) / total * 100, 2),
            )
            for _, r in cat_counts.sort_values(by="count", ascending=False).iterrows()
        ]

        # Daily volume (45 days)
        df_daily = df.groupby(df["parsed_timestamp"].dt.strftime("%Y-%m-%d")).agg(
            count=("txn_id", "count"),
            volume=("amount", "sum"),
        ).reset_index()
        daily_vol = [
            DailyVolumeMetric(
                date=str(r["parsed_timestamp"]),
                count=int(r["count"]),
                volume=float(r["volume"]),
            )
            for _, r in df_daily.sort_values(by="parsed_timestamp", ascending=True).iterrows()
        ]

        # Amount buckets
        bucket_defs = [
            ("0-1K", 0.0, 1_000.0),
            ("1K-10K", 1_000.0, 10_000.0),
            ("10K-50K", 10_000.0, 50_000.0),
            ("50K-1L", 50_000.0, 100_000.0),
            ("1L-5L", 100_000.0, 500_000.0),
            ("5L+", 500_000.0, float("inf")),
        ]
        amount_buckets = []
        for label, lo, hi in bucket_defs:
            if hi != float("inf"):
                cnt = int(((df["amount"] >= lo) & (df["amount"] < hi)).sum())
            else:
                cnt = int((df["amount"] >= lo).sum())
            amount_buckets.append(
                AmountBucketMetric(
                    bucket=label,
                    min_val=lo,
                    max_val=hi if hi != float("inf") else -1.0,
                    count=cnt,
                    percentage=round(cnt / total * 100, 2) if total else 0.0,
                )
            )

        # Missing metadata counts
        missing_metadata = {
            "device_id": int(df["device_id"].isna().sum()),
            "location": int(df["location"].isna().sum()),
            "sender_balance_before": int(df["sender_balance_before"].isna().sum()),
        }

        # Ground truth evaluation summary (Strictly segregated)
        gt_fraud_count = int(df["is_fraud"].sum())
        gt_aml_count = int(df["is_aml_pattern"].sum())
        gt_edge_count = int(df["is_edge_case"].sum())
        patterns_dict = df["pattern_type"].value_counts().to_dict()

        gt_eval = GroundTruthEvaluationSummary(
            total_evaluated_rows=total,
            ground_truth_fraud_count=gt_fraud_count,
            ground_truth_fraud_rate=round(gt_fraud_count / total * 100, 4) if total else 0.0,
            ground_truth_aml_count=gt_aml_count,
            ground_truth_aml_rate=round(gt_aml_count / total * 100, 4) if total else 0.0,
            ground_truth_edge_cases_count=gt_edge_count,
            pattern_breakdown={str(k): int(v) for k, v in patterns_dict.items()},
        )

        self._summary_response = DatasetSummaryResponse(
            total_transactions=total,
            total_volume_inr=float(df["amount"].sum()),
            avg_transaction_inr=float(df["amount"].mean()),
            min_transaction_inr=float(df["amount"].min()),
            max_transaction_inr=float(df["amount"].max()),
            unique_senders=unique_senders,
            unique_receivers=unique_receivers,
            unique_accounts_total=all_accounts,
            date_range={"start": str(min_ts), "end": str(max_ts)},
            channel_distribution=channel_dist,
            category_distribution=cat_dist,
            daily_volume=daily_vol,
            amount_buckets=amount_buckets,
            missing_metadata_counts=missing_metadata,
            ground_truth_evaluation=gt_eval,
        )

    def get_status(self) -> DatasetStatusResponse:
        if not self._status_response:
            return DatasetStatusResponse(import_status="EMPTY")
        return self._status_response

    def get_summary(self) -> DatasetSummaryResponse:
        if not self._summary_response:
            raise RuntimeError("Dataset has not been loaded yet.")
        return self._summary_response

    def get_transaction(self, transaction_id: str) -> Optional[TransactionResponse]:
        """O(1) lookup of operational transaction record."""
        return self._records_by_id.get(transaction_id)

    def get_chronological_transactions(self) -> List[TransactionResponse]:
        """Chronologically sorted records for replay simulation."""
        return self._chronological_records

    def add_transaction(self, payload: TransactionCreate) -> TransactionResponse:
        """Register a new operational transaction in-memory without mutating source CSV."""
        tx = TransactionResponse(**payload.model_dump())
        self._records_by_id[tx.transaction_id] = tx
        self._dynamic_records.append(tx)
        self._chronological_records.append(tx)
        return tx

    def list_transactions(
        self,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        sender_id: Optional[str] = None,
        receiver_id: Optional[str] = None,
        channel: Optional[str] = None,
        merchant_category: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
    ) -> Tuple[List[TransactionResponse], int]:
        """Filter, sort, and paginate transactions with high performance."""
        if self._df is None:
            return [], 0

        df = self._df
        mask = pd.Series(True, index=df.index)

        if search:
            s_lower = search.lower()
            mask &= (
                df["txn_id"].str.lower().str.contains(s_lower, na=False)
                | df["sender_id"].str.lower().str.contains(s_lower, na=False)
                | df["receiver_id"].str.lower().str.contains(s_lower, na=False)
            )

        if sender_id:
            mask &= df["sender_id"] == sender_id
        if receiver_id:
            mask &= df["receiver_id"] == receiver_id
        if channel:
            mask &= df["channel"].str.upper() == channel.upper()
        if merchant_category:
            mask &= df["merchant_category"].str.lower() == merchant_category.lower()
        if min_amount is not None:
            mask &= df["amount"] >= min_amount
        if max_amount is not None:
            mask &= df["amount"] <= max_amount
        if start_date:
            mask &= df["parsed_timestamp"] >= pd.to_datetime(start_date)
        if end_date:
            mask &= df["parsed_timestamp"] <= pd.to_datetime(end_date)

        filtered_df = df[mask]
        total_count = len(filtered_df)

        # Sorting column mapping
        sort_col_map = {
            "timestamp": "parsed_timestamp",
            "amount": "amount",
            "transaction_id": "txn_id",
        }
        target_col = sort_col_map.get(sort_by, "parsed_timestamp")
        ascending = sort_order.lower() == "asc"

        paged_df = filtered_df.sort_values(by=target_col, ascending=ascending).iloc[offset : offset + limit]

        items = [
            self._records_by_id[row["txn_id"]]
            for _, row in paged_df.iterrows()
            if row["txn_id"] in self._records_by_id
        ]

        return items, total_count


dataset_service = StaticCSVDatasetService()
