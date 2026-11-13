"""
Dataset Ingestion Service.
Handles chunked bulk insertion of synthetic transaction records and ground truth.
Enforces strict separation of operational transaction data and evaluation labels.

The import runs inside a single database transaction: either every chunk and the
import metadata record commit together, or the whole import rolls back. This is
safe for both SQLite local development and Supabase PostgreSQL.
"""

import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.database.session import SessionLocal
from app.models.dataset_import import DatasetImport
from app.models.ground_truth import TransactionGroundTruth
from app.models.transaction import Transaction
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
    """Compute SHA-256 hash of a file efficiently in 64KB blocks."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


class IngestionService:
    """Manages high-throughput, idempotent dataset ingestion into SQLite/Postgres."""

    CHUNK_SIZE = 5000

    @classmethod
    def import_csv(
        cls,
        csv_path: str | Path,
        dataset_id: str = "synthetic-promptwars-2026",
        force: bool = False,
        chunk_size: int = CHUNK_SIZE,
        strict: bool = True,
    ) -> Dict[str, Any]:
        """
        Stream and ingest transactions CSV into the relational database.

        Args:
            csv_path: Path to the synthetic dataset CSV.
            dataset_id: Stable identifier stored in dataset_imports.
            force: Clear existing data before importing.
            chunk_size: Number of CSV rows processed per batch.
            strict: Fail verification when any transaction lacks ground truth.

        Returns:
            Execution summary including count and integrity verification.
        """
        path = Path(csv_path)
        if not path.is_file():
            raise FileNotFoundError(f"Dataset CSV not found at: {path.resolve()}")
        if chunk_size < 1:
            raise ValueError("chunk_size must be >= 1")

        start_time = time.time()
        checksum = calculate_sha256(path)
        logger.info("Starting CSV ingestion from %s (SHA-256: %s...)", path.name, checksum[:12])

        session: Session = SessionLocal()
        try:
            existing_import = session.scalar(
                select(DatasetImport).where(DatasetImport.checksum_sha256 == checksum)
            )
            current_tx_count = session.scalar(select(func.count()).select_from(Transaction))

            if existing_import and current_tx_count > 0 and not force:
                logger.info(
                    "Dataset with checksum %s already imported (%s rows). Skipping duplicate.",
                    checksum[:12],
                    current_tx_count,
                )
                return {
                    "status": "SKIPPED_ALREADY_IMPORTED",
                    "dataset_id": existing_import.dataset_id,
                    "checksum": checksum,
                    "total_rows": existing_import.total_rows,
                    "imported_rows": 0,
                    "skipped_rows": existing_import.total_rows,
                    "duration_seconds": 0.0,
                    "verification": cls.verify_database(session=session),
                    "message": "Dataset checksum already registered in database.",
                }

            if force:
                logger.warning("Force flag active: clearing existing transaction and ground truth data.")
                # Child table first for databases that enforce foreign keys.
                session.execute(delete(TransactionGroundTruth))
                session.execute(delete(Transaction))
                session.execute(delete(DatasetImport))
                session.flush()

            total_processed = 0
            imported_count = 0
            skipped_count = 0
            repaired_ground_truth = 0
            min_ts: Optional[datetime] = None
            max_ts: Optional[datetime] = None

            for chunk_df in pd.read_csv(path, chunksize=chunk_size, dtype=CSV_DTYPES):
                chunk_rows = len(chunk_df)
                total_processed += chunk_rows

                unique_df = chunk_df.drop_duplicates(subset=["txn_id"], keep="first")
                skipped_count += chunk_rows - len(unique_df)

                unique_df = unique_df.copy()
                unique_df["parsed_timestamp"] = pd.to_datetime(
                    unique_df["timestamp"], format="%Y-%m-%dT%H:%M:%S", errors="raise"
                )

                chunk_min = unique_df["parsed_timestamp"].min()
                chunk_max = unique_df["parsed_timestamp"].max()
                min_ts = chunk_min if min_ts is None or chunk_min < min_ts else min_ts
                max_ts = chunk_max if max_ts is None or chunk_max > max_ts else max_ts

                chunk_ids = unique_df["txn_id"].astype(str).tolist()
                existing_ids = set(
                    session.scalars(
                        select(Transaction.transaction_id).where(
                            Transaction.transaction_id.in_(chunk_ids)
                        )
                    ).all()
                )
                existing_gt_ids = set(
                    session.scalars(
                        select(TransactionGroundTruth.transaction_id).where(
                            TransactionGroundTruth.transaction_id.in_(existing_ids)
                        )
                    ).all()
                ) if existing_ids else set()

                new_df = unique_df[~unique_df["txn_id"].astype(str).isin(existing_ids)]
                duplicate_df = unique_df[unique_df["txn_id"].astype(str).isin(existing_ids)]
                skipped_count += len(duplicate_df)

                tx_records = [
                    {
                        "transaction_id": str(row["txn_id"]),
                        "timestamp": row["parsed_timestamp"].to_pydatetime(),
                        "sender_account_id": str(row["sender_id"]),
                        "receiver_account_id": str(row["receiver_id"]),
                        "amount": float(row["amount"]),
                        "currency": "INR",
                        "channel": str(row["channel"]),
                        "merchant_category": str(row["merchant_category"]),
                        "device_id": str(row["device_id"]) if pd.notna(row["device_id"]) else None,
                        "location": str(row["location"]) if pd.notna(row["location"]) else None,
                        "sender_balance_before": (
                            float(row["sender_balance_before"])
                            if pd.notna(row["sender_balance_before"])
                            else None
                        ),
                        "transaction_status": "COMPLETED",
                    }
                    for _, row in new_df.iterrows()
                ]

                # Ground truth is inserted only for new rows plus duplicate rows
                # that were previously imported without a label record.
                gt_source_df = pd.concat(
                    [
                        new_df,
                        duplicate_df[
                            ~duplicate_df["txn_id"].astype(str).isin(existing_gt_ids)
                        ],
                    ]
                )
                repaired_ground_truth += max(
                    0, len(gt_source_df) - len(new_df)
                )

                gt_records = [
                    {
                        "transaction_id": str(row["txn_id"]),
                        "is_fraud": int(row["is_fraud"]),
                        "is_aml_pattern": int(row["is_aml_pattern"]),
                        "pattern_type": str(row["pattern_type"]),
                        "scenario_id": str(row["scenario_id"]) if pd.notna(row["scenario_id"]) else None,
                        "is_edge_case": int(row["is_edge_case"]),
                        "edge_case_type": (
                            str(row["edge_case_type"]) if pd.notna(row["edge_case_type"]) else None
                        ),
                    }
                    for _, row in gt_source_df.iterrows()
                ]

                if tx_records:
                    session.bulk_insert_mappings(Transaction, tx_records)
                if gt_records:
                    session.bulk_insert_mappings(TransactionGroundTruth, gt_records)

                # Flush (not commit) so constraint errors surface immediately,
                # while keeping the whole import transactional.
                session.flush()
                imported_count += len(tx_records)

                logger.info(
                    "Imported batch: %s new rows, %s duplicates skipped (total processed %s).",
                    len(tx_records),
                    len(duplicate_df),
                    total_processed,
                )

            duration = round(time.time() - start_time, 2)

            if min_ts is None or max_ts is None:
                raise ValueError("Dataset CSV contained no data rows.")

            verification = cls._verify_import(
                session=session,
                total_processed=total_processed,
                imported_count=imported_count,
                skipped_count=skipped_count,
                strict=strict,
            )

            dataset_record = DatasetImport(
                dataset_id=dataset_id,
                source_filename=path.name,
                checksum_sha256=checksum,
                imported_at=utc_now(),
                total_rows=total_processed,
                imported_rows=imported_count,
                skipped_rows=skipped_count,
                date_range_start=min_ts,
                date_range_end=max_ts,
                status="COMPLETED",
                duration_seconds=duration,
            )
            session.add(dataset_record)

            # Commit metadata, transactions, and labels atomically.
            session.commit()
            logger.info("Dataset import complete: %s rows in %ss.", imported_count, duration)

            return {
                "status": "COMPLETED",
                "dataset_id": dataset_id,
                "source_filename": path.name,
                "checksum": checksum,
                "total_rows": total_processed,
                "imported_rows": imported_count,
                "skipped_rows": skipped_count,
                "repaired_ground_truth_rows": repaired_ground_truth,
                "date_range": {
                    "start": min_ts.isoformat() if min_ts else None,
                    "end": max_ts.isoformat() if max_ts else None,
                },
                "duration_seconds": duration,
                "verification": verification,
            }

        except Exception as e:
            session.rollback()
            logger.exception("Dataset ingestion failed and was rolled back: %s", e)
            raise
        finally:
            session.close()

    @classmethod
    def _verify_import(
        cls,
        session: Session,
        total_processed: int,
        imported_count: int,
        skipped_count: int,
        strict: bool,
    ) -> Dict[str, Any]:
        """Validate counts and ground-truth foreign-key integrity pre-commit."""
        if imported_count + skipped_count != total_processed:
            raise RuntimeError(
                "Ingestion accounting mismatch: "
                f"imported={imported_count}, skipped={skipped_count}, total={total_processed}"
            )

        verification = cls.verify_database(session=session, strict=strict)
        if verification["orphan_ground_truth_rows"] != 0:
            raise RuntimeError(
                "Ground-truth integrity check failed: "
                f"{verification['orphan_ground_truth_rows']} orphan label rows."
            )
        if strict and verification["transactions_without_ground_truth"] != 0:
            raise RuntimeError(
                "Ground-truth integrity check failed: "
                f"{verification['transactions_without_ground_truth']} transactions have no label record."
            )
        return verification

    @classmethod
    def verify_database(
        cls,
        session: Optional[Session] = None,
        strict: bool = False,
    ) -> Dict[str, Any]:
        """
        Inspect database-level dataset integrity.

        Returns row counts, orphan label counts, transactions without labels,
        and the latest registered import metadata.
        """
        owns_session = session is None
        db = session or SessionLocal()
        try:
            transaction_count = db.scalar(select(func.count()).select_from(Transaction)) or 0
            ground_truth_count = (
                db.scalar(select(func.count()).select_from(TransactionGroundTruth)) or 0
            )
            orphan_gt = (
                db.scalar(
                    select(func.count())
                    .select_from(TransactionGroundTruth)
                    .outerjoin(
                        Transaction,
                        TransactionGroundTruth.transaction_id == Transaction.transaction_id,
                    )
                    .where(Transaction.transaction_id.is_(None))
                )
                or 0
            )
            missing_gt = (
                db.scalar(
                    select(func.count())
                    .select_from(Transaction)
                    .outerjoin(
                        TransactionGroundTruth,
                        Transaction.transaction_id == TransactionGroundTruth.transaction_id,
                    )
                    .where(TransactionGroundTruth.transaction_id.is_(None))
                )
                or 0
            )
            latest_import = db.scalar(
                select(DatasetImport).order_by(DatasetImport.imported_at.desc()).limit(1)
            )

            result = {
                "transactions": transaction_count,
                "ground_truth_rows": ground_truth_count,
                "orphan_ground_truth_rows": orphan_gt,
                "transactions_without_ground_truth": missing_gt,
                "counts_match": transaction_count == ground_truth_count,
                "strict_ok": orphan_gt == 0 and (missing_gt == 0 if strict else True),
                "latest_import": {
                    "dataset_id": latest_import.dataset_id if latest_import else None,
                    "checksum_sha256": latest_import.checksum_sha256 if latest_import else None,
                    "status": latest_import.status if latest_import else "EMPTY",
                    "total_rows": latest_import.total_rows if latest_import else 0,
                    "imported_rows": latest_import.imported_rows if latest_import else 0,
                },
            }
            return result
        finally:
            if owns_session:
                db.close()
