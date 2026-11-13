"""Tests for the chunked, transactional dataset ingestion engine."""

import csv
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

import app.services.ingestion as ingestion_module
from app.database.base import Base
from app.models.dataset_import import DatasetImport
from app.models.ground_truth import TransactionGroundTruth
from app.models.transaction import Transaction
from app.services.ingestion import IngestionService

COLUMNS = [
    "txn_id",
    "timestamp",
    "sender_id",
    "receiver_id",
    "amount",
    "channel",
    "merchant_category",
    "device_id",
    "location",
    "sender_balance_before",
    "is_fraud",
    "is_aml_pattern",
    "pattern_type",
    "scenario_id",
    "is_edge_case",
    "edge_case_type",
]


def _write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _row(txn_id: str, timestamp: str = "2026-10-01T00:03:23", is_fraud: int = 0) -> dict:
    return {
        "txn_id": txn_id,
        "timestamp": timestamp,
        "sender_id": "ACC_SEND",
        "receiver_id": "ACC_RECV",
        "amount": "1234.56",
        "channel": "UPI",
        "merchant_category": "transfer",
        "device_id": "D1",
        "location": "Kolkata",
        "sender_balance_before": "50000.00",
        "is_fraud": str(is_fraud),
        "is_aml_pattern": "0",
        "pattern_type": "normal",
        "scenario_id": "",
        "is_edge_case": "0",
        "edge_case_type": "",
    }


@pytest.fixture()
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Point the ingestion service at an isolated SQLite database."""
    db_path = tmp_path / "ingestion.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    monkeypatch.setattr(ingestion_module, "SessionLocal", TestingSession)

    yield TestingSession

    engine.dispose()


def test_import_preserves_ids_and_ground_truth(isolated_db, tmp_path: Path):
    csv_path = tmp_path / "dataset.csv"
    _write_csv(csv_path, [_row("T000001"), _row("T000002", is_fraud=1)])

    summary = IngestionService.import_csv(csv_path, dataset_id="test-ds", chunk_size=1)
    assert summary["status"] == "COMPLETED"
    assert summary["imported_rows"] == 2
    assert summary["verification"]["orphan_ground_truth_rows"] == 0

    db = isolated_db()
    try:
        assert db.scalar(select(func.count()).select_from(Transaction)) == 2
        assert db.scalar(select(func.count()).select_from(TransactionGroundTruth)) == 2
        tx = db.get(Transaction, "T000001")
        gt = db.get(TransactionGroundTruth, "T000001")
        assert tx is not None and gt is not None
        assert float(tx.amount) == 1234.56
        assert db.get(TransactionGroundTruth, "T000002").is_fraud == 1
        assert db.scalar(select(func.count()).select_from(DatasetImport)) == 1
    finally:
        db.close()


def test_duplicate_rows_are_safely_skipped(isolated_db, tmp_path: Path):
    csv_path = tmp_path / "duplicates.csv"
    _write_csv(csv_path, [_row("T000001"), _row("T000001"), _row("T000002")])

    summary = IngestionService.import_csv(csv_path, dataset_id="test-ds", chunk_size=10)
    assert summary["imported_rows"] == 2
    assert summary["skipped_rows"] == 1

    # Re-importing the same checksum is idempotent.
    second = IngestionService.import_csv(csv_path, dataset_id="test-ds")
    assert second["status"] == "SKIPPED_ALREADY_IMPORTED"

    db = isolated_db()
    try:
        assert db.scalar(select(func.count()).select_from(Transaction)) == 2
        assert db.scalar(select(func.count()).select_from(TransactionGroundTruth)) == 2
    finally:
        db.close()


def test_failed_import_rolls_back_all_chunks(isolated_db, tmp_path: Path):
    csv_path = tmp_path / "broken.csv"
    _write_csv(
        csv_path,
        [
            _row("T000001"),
            _row("T000002"),
            _row("T000003", timestamp="not-a-timestamp"),
        ],
    )

    with pytest.raises(Exception):
        IngestionService.import_csv(csv_path, dataset_id="test-ds", chunk_size=2)

    db = isolated_db()
    try:
        assert db.scalar(select(func.count()).select_from(Transaction)) == 0
        assert db.scalar(select(func.count()).select_from(TransactionGroundTruth)) == 0
        assert db.scalar(select(func.count()).select_from(DatasetImport)) == 0
    finally:
        db.close()
