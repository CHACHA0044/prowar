"""Tests for the real transaction API endpoints — static CSV architecture."""

import pytest
from fastapi.testclient import TestClient


REAL_TXN_ID = "T000001"  # First ID in the synthetic dataset


def test_list_transactions_default(client: TestClient):
    r = client.get("/api/v1/transactions")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["total"] >= 129675
    assert isinstance(body["data"]["items"], list)
    assert len(body["data"]["items"]) > 0


def test_list_transactions_pagination(client: TestClient):
    r = client.get("/api/v1/transactions?limit=5&offset=0")
    assert r.status_code == 200
    assert len(r.json()["data"]["items"]) == 5


def test_filter_by_channel(client: TestClient):
    r = client.get("/api/v1/transactions?channel=UPI")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    assert len(items) >= 1
    assert all(t["channel"] == "UPI" for t in items)


def test_filter_by_amount_range(client: TestClient):
    r = client.get("/api/v1/transactions?min_amount=5000&max_amount=10000")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    for t in items:
        assert 5000 <= t["amount"] <= 10000


def test_get_transaction_by_id(client: TestClient):
    r = client.get(f"/api/v1/transactions/{REAL_TXN_ID}")
    assert r.status_code == 200
    assert r.json()["data"]["transaction_id"] == REAL_TXN_ID


def test_transaction_no_ground_truth_fields(client: TestClient):
    r = client.get(f"/api/v1/transactions/{REAL_TXN_ID}")
    body = r.json()["data"]
    forbidden = {
        "is_fraud",
        "is_aml_pattern",
        "pattern_type",
        "scenario_id",
        "is_edge_case",
        "edge_case_type",
    }
    assert not forbidden.intersection(body.keys()), (
        "Ground truth fields must NOT appear in operational API"
    )


def test_transaction_not_found(client: TestClient):
    r = client.get("/api/v1/transactions/NONEXISTENT_99999")
    assert r.status_code == 404
