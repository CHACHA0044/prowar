"""
Dataset Ingestion Service.
Handles chunked bulk insertion of synthetic transaction records and ground truth.
Enforces strict separation of operational transaction data and evaluation labels.
"""

import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.database.session import SessionLocal, engine
from app.models.transaction import Transaction
from app.models.ground_truth import TransactionGroundTruth
from app.models.dataset_import import DatasetImport
from app.utils.timestamps import utc_now


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
    ) -> Dict[str, Any]:
        """
        Stream and ingest transactions CSV into relational database.
        Returns execution summary.
        """
        path = Path(csv_path)
        if not path.is_file():
            raise FileNotFoundError(f"Dataset CSV not found at: {path.resolve()}")

        start_time = time.time()
        checksum = calculate_sha256(path)
        logger.info(f"Starting CSV ingestion from {path.name} (SHA-256: {checksum[:12]}...)")

        session: Session = SessionLocal()
        try:
            # Check for existing import with identical checksum
            existing_import = session.scalar(
                select(DatasetImport).where(DatasetImport.checksum_sha256 == checksum)
            )

            current_tx_count = session.scalar(select(func.count()).select_from(Transaction))

            if existing_import and current_tx_count > 0 and not force:
                logger.info(
                    f"Dataset with checksum {checksum[:12]} already imported ({current_tx_count} rows). Skipping duplicate."
                )
                return {
                    "status": "SKIPPED_ALREADY_IMPORTED",
                    "dataset_id": existing_import.dataset_id,
                    "checksum": checksum,
                    "total_rows": existing_import.total_rows,
                    "imported_rows": 0,
                    "skipped_rows": existing_import.total_rows,
                    "duration_seconds": 0.0,
                    "message": "Dataset checksum already registered in database.",
                }

            # If force re-importing, clean existing tables
            if force:
                logger.warning("Force flag active: clearing existing transaction and ground truth data.")
                session.query(TransactionGroundTruth).delete()
                session.query(Transaction).delete()
                session.query(DatasetImport).delete()
                session.commit()

            total_processed = 0
            imported_count = 0
            min_ts: Optional[datetime] = None
            max_ts: Optional[datetime] = None

            # Process CSV in memory-friendly chunks using pandas iterator
            for chunk_df in pd.read_csv(path, chunksize=cls.CHUNK_SIZE):
                chunk_len = len(chunk_df)
                total_processed += chunk_len

                # Parse timestamps
                chunk_df["parsed_timestamp"] = pd.to_datetime(chunk_df["timestamp"], format="%Y-%m-%dT%H:%M:%S")

                chunk_min = chunk_df["parsed_timestamp"].min()
                chunk_max = chunk_df["parsed_timestamp"].max()
                min_ts = chunk_min if min_ts is None or chunk_min < min_ts else min_ts
                max_ts = chunk_max if max_ts is None or chunk_max > max_ts else max_ts

                # 1. Prepare operational Transaction records (strictly without labels)
                tx_records = []
                for _, row in chunk_df.iterrows():
                    tx_records.append({
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
                        "sender_balance_before": float(row["sender_balance_before"]) if pd.notna(row["sender_balance_before"]) else None,
                        "transaction_status": "COMPLETED",
                    })

                # 2. Prepare isolated Ground Truth records
                gt_records = []
                for _, row in chunk_df.iterrows():
                    gt_records.append({
                        "transaction_id": str(row["txn_id"]),
                        "is_fraud": int(row["is_fraud"]),
                        "is_aml_pattern": int(row["is_aml_pattern"]),
                        "pattern_type": str(row["pattern_type"]),
                        "scenario_id": str(row["scenario_id"]) if pd.notna(row["scenario_id"]) else None,
                        "is_edge_case": int(row["is_edge_case"]),
                        "edge_case_type": str(row["edge_case_type"]) if pd.notna(row["edge_case_type"]) else None,
                    })

                # Bulk insert via SQLAlchemy bulk insert mappings
                session.bulk_insert_mappings(Transaction, tx_records)
                session.bulk_insert_mappings(TransactionGroundTruth, gt_records)
                session.commit()

                imported_count += chunk_len
                logger.info(f"Imported {imported_count}/{total_processed} rows...")

            duration = round(time.time() - start_time, 2)

            # Record DatasetImport metadata
            dataset_record = DatasetImport(
                dataset_id=dataset_id,
                source_filename=path.name,
                checksum_sha256=checksum,
                imported_at=utc_now(),
                total_rows=total_processed,
                imported_rows=imported_count,
                skipped_rows=0,
                date_range_start=min_ts,
                date_range_end=max_ts,
                status="COMPLETED",
                duration_seconds=duration,
            )
            session.add(dataset_record)
            session.commit()

            logger.info(f"Dataset import complete: {imported_count} rows in {duration}s.")

            return {
                "status": "COMPLETED",
                "dataset_id": dataset_id,
                "source_filename": path.name,
                "checksum": checksum,
                "total_rows": total_processed,
                "imported_rows": imported_count,
                "skipped_rows": 0,
                "date_range": {
                    "start": min_ts.isoformat() if min_ts else None,
                    "end": max_ts.isoformat() if max_ts else None,
                },
                "duration_seconds": duration,
            }

        except Exception as e:
            session.rollback()
            logger.exception(f"Fatal error during dataset ingestion: {e}")
            raise
        finally:
            session.close()

