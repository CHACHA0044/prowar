"""Tests for dataset status and summary endpoints — static CSV architecture."""

from fastapi.testclient import TestClient


def test_dataset_status_completed(client: TestClient):
    r = client.get("/api/v1/dataset/status")
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["import_status"] == "COMPLETED"
    assert body["imported_rows"] >= 129675
    assert body["total_rows"] >= 129675


def test_dataset_summary_endpoint(client: TestClient):
    r = client.get("/api/v1/dataset/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert "total_transactions" in data
    assert data["total_transactions"] >= 129675
    assert "channel_distribution" in data
    assert "amount_buckets" in data
    assert "ground_truth_evaluation" in data
