"""
AML Graph Analysis Service Interface.
"""

from typing import Dict, Any


class AMLAnalysisService:
    """Graph typology detection service contract."""

    @staticmethod
    def get_supported_typologies() -> list[str]:
        return [
            "structuring",
            "circular_flow",
            "fan_in_fan_out",
            "rapid_pass_through",
        ]

