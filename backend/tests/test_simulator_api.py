"""Tests for the real-time transaction simulator — static CSV architecture."""

import pytest
from fastapi.testclient import TestClient


def test_simulator_status_endpoint(client: TestClient):
    r = client.get("/api/v1/simulator/status")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "state" in body["data"]
    assert "speed_multiplier" in body["data"]


def test_simulator_speed_update(client: TestClient):
    r = client.patch("/api/v1/simulator/speed", json={"speed": 30.0})
    assert r.status_code == 200
    assert r.json()["data"]["speed_multiplier"] == 30.0


def test_simulator_lifecycle(client: TestClient):
    # Reset
    r = client.post("/api/v1/simulator/reset")
    assert r.status_code == 200
    assert r.json()["data"]["state"] == "IDLE"

    # Pause on idle is safe
    r = client.post("/api/v1/simulator/pause")
    assert r.status_code == 200


def test_simulator_state_is_in_memory(client: TestClient):
    """
    Phase 2.6: Simulator state is fully in-memory (no DB checkpoint).
    Verify that reset brings state back to IDLE and speed is preserved correctly.
    """
    client.post("/api/v1/simulator/reset")
    r = client.patch("/api/v1/simulator/speed", json={"speed": 15.0})
    assert r.status_code == 200
    assert r.json()["data"]["speed_multiplier"] == 15.0

    status = client.get("/api/v1/simulator/status").json()["data"]
    assert status["speed_multiplier"] == 15.0
    assert status["state"] == "IDLE"
