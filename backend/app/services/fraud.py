"""
Fraud Detection Service Interface.
"""

from typing import Dict, Any


class FraudDetectionService:
    """Supervised fraud classification service contract."""

    @staticmethod
    def get_model_metadata() -> Dict[str, Any]:
        return {
            "model_type": "Supervised Classifier",
            "framework": "LightGBM / Scikit-Learn",
            "status": "uninitialized",
        }

