"""Tests for the real-time transaction simulator."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.simulator import simulator_service


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_simulator_status_endpoint(client):
    r = client.get("/api/v1/simulator/status")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "state" in body["data"]
    assert "speed_multiplier" in body["data"]


def test_simulator_speed_update(client):
    r = client.patch("/api/v1/simulator/speed", json={"speed": 30.0})
    assert r.status_code == 200
    assert r.json()["data"]["speed_multiplier"] == 30.0


def test_simulator_lifecycle(client):
    # Reset
    r = client.post("/api/v1/simulator/reset")
    assert r.status_code == 200
    assert r.json()["data"]["state"] == "IDLE"

    # Pause on idle is safe
    r = client.post("/api/v1/simulator/pause")
    assert r.status_code == 200


def test_simulator_checkpoint_persists(client):
    from app.database.session import SessionLocal
    from app.models.simulator_checkpoint import SimulatorCheckpoint

    client.post("/api/v1/simulator/reset")
    r = client.patch("/api/v1/simulator/speed", json={"speed": 30.0})
    assert r.status_code == 200

    db = SessionLocal()
    try:
        checkpoint = db.get(SimulatorCheckpoint, 1)
        assert checkpoint is not None
        assert checkpoint.speed_multiplier == 30.0
        assert checkpoint.state in ("IDLE", "PAUSED", "RUNNING", "COMPLETED")
    finally:
        db.close()
