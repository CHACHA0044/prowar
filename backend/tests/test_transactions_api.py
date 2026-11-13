"""Tests for the real transaction API endpoints."""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.database.session import SessionLocal
from app.models.transaction import Transaction


@pytest.fixture(scope="module", autouse=True)
def seed_transactions():
    db = SessionLocal()
    # Check if already seeded
    existing = db.query(Transaction).filter(Transaction.transaction_id == "TXN_0000").first()
    if not existing:
        txns = [
            Transaction(
                transaction_id=f"TXN_{i:04d}",
                timestamp=datetime(2026, 10, (i % 28) + 1, 10, 0, 0),
                sender_account_id=f"ACC_S{i:03d}",
                receiver_account_id=f"ACC_R{i:03d}",
                amount=float(1000 * (i + 1)),
                currency="INR",
                channel="UPI" if i % 2 == 0 else "NEFT",
                merchant_category="transfer",
                transaction_status="COMPLETED",
            )
            for i in range(20)
        ]
        db.add_all(txns)
        db.commit()
    db.close()


def test_list_transactions_default(client: TestClient):
    r = client.get("/api/v1/transactions")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["total"] >= 20
    assert len(body["data"]["items"]) >= 20


def test_list_transactions_pagination(client: TestClient):
    r = client.get("/api/v1/transactions?limit=5&offset=0")
    assert r.status_code == 200
    assert len(r.json()["data"]["items"]) == 5


def test_filter_by_channel(client: TestClient):
    r = client.get("/api/v1/transactions?channel=UPI")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    assert len(items) >= 10
    assert all(t["channel"] == "UPI" for t in items)


def test_filter_by_amount_range(client: TestClient):
    r = client.get("/api/v1/transactions?min_amount=5000&max_amount=10000")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    for t in items:
        assert 5000 <= t["amount"] <= 10000


def test_get_transaction_by_id(client: TestClient):
    r = client.get("/api/v1/transactions/TXN_0000")
    assert r.status_code == 200
    assert r.json()["data"]["transaction_id"] == "TXN_0000"


def test_transaction_no_ground_truth_fields(client: TestClient):
    r = client.get("/api/v1/transactions/TXN_0000")
    body = r.json()["data"]
    forbidden = {
        "is_fraud",
        "is_aml_pattern",
        "pattern_type",
        "scenario_id",
        "is_edge_case",
        "edge_case_type",
    }
    assert not forbidden.intersection(body.keys()), "Ground truth fields must NOT appear in operational API"


def test_transaction_not_found(client: TestClient):
    r = client.get("/api/v1/transactions/NONEXISTENT_99999")
    assert r.status_code == 404
