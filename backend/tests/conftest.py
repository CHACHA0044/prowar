"""
Pytest test fixtures and configuration.
Static CSV Architecture — No database setup required.
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure the backend package root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "False"
os.environ.setdefault(
    "DATASET_PATH", str(PROJECT_ROOT / "data" / "transactions.csv")
)

from app.main import app  # noqa: E402
from app.services.dataset_service import dataset_service  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def load_dataset_once():
    """Load the static CSV once for the entire test session."""
    if not dataset_service.is_ready:
        csv_path = os.environ.get("DATASET_PATH")
        dataset_service.load_dataset(csv_path)
    yield


@pytest.fixture
def client(load_dataset_once):
    """FastAPI TestClient fixture (dataset already warm)."""
    with TestClient(app) as test_client:
        yield test_client
