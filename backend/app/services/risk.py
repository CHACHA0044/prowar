"""
Risk Scoring Service Interface.
"""

from typing import Dict, Any


class RiskAssessmentService:
    """Risk ensemble weighting service contract."""

    @staticmethod
    def get_tier(score: float) -> str:
        if score < 30.0:
            return "LOW"
        if score < 60.0:
            return "MEDIUM"
        if score < 85.0:
            return "HIGH"
        return "CRITICAL"

