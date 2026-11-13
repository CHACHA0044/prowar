"""Tests for dataset status and summary endpoints."""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.database.session import SessionLocal
from app.models.dataset_import import DatasetImport


@pytest.fixture(scope="module", autouse=True)
def seed_dataset_import():
    db = SessionLocal()
    existing = db.query(DatasetImport).first()
    if not existing:
        db.add(
            DatasetImport(
                dataset_id="test-ds-001",
                source_filename="transactions.csv",
                checksum_sha256="abc123sha",
                imported_at=datetime(2026, 11, 13, 10, 0, 0),
                total_rows=100,
                imported_rows=100,
                skipped_rows=0,
                status="COMPLETED",
                duration_seconds=10.5,
            )
        )
        db.commit()
    db.close()


def test_dataset_status_completed(client: TestClient):
    r = client.get("/api/v1/dataset/status")
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["import_status"] == "COMPLETED"
    assert body["imported_rows"] >= 100
    assert body["total_rows"] >= 100


def test_dataset_summary_endpoint(client: TestClient):
    r = client.get("/api/v1/dataset/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "total_transactions" in body["data"]
    assert "channel_distribution" in body["data"]
    assert "amount_buckets" in body["data"]
    assert "ground_truth_evaluation" in body["data"]
