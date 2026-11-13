"""
Anomaly Detection Service Interface.
"""

from typing import Dict, Any


class AnomalyDetectionService:
    """Unsupervised behavioral anomaly detection service contract."""

    @staticmethod
    def get_service_status() -> Dict[str, Any]:
        return {
            "algorithm": "IsolationForest & Rolling Z-Scores",
            "status": "uninitialized",
        }

