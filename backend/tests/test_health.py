"""
Health endpoints tests.
"""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "/api/v1/health" in data["health"]


def test_system_health_endpoint(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("healthy", "degraded")
    assert "components" in data
    assert "api_gateway" in data["components"]
    assert "database" in data["components"]
    assert data["components"]["api_gateway"]["status"] == "healthy"


def test_database_health_endpoint(client: TestClient):
    response = client.get("/api/v1/health/database")
    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is True
    assert data["status"] == "healthy"
    assert "dialect" in data

