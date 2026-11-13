"""
Risk Assessment router (Foundation Placeholder).
Prepared for Department 6: Weighted ensemble scoring and rule overrides.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from app.schemas.common import APIResponse

router = APIRouter(prefix="/risk", tags=["Risk Assessment"])


class RiskEngineInfo(BaseModel):
    engine_name: str
    status: str
    scoring_formula: str
    risk_tiers: dict[str, str]
    phase: str


@router.get(
    "/status",
    response_model=APIResponse[RiskEngineInfo],
    status_code=status.HTTP_200_OK,
    summary="Risk Engine Status",
)
def get_risk_status() -> APIResponse[RiskEngineInfo]:
    return APIResponse(
        success=True,
        message="Risk assessment engine registered.",
        data=RiskEngineInfo(
            engine_name="EnsembleRiskScorer",
            status="READY_FOR_WEIGHTS",
            scoring_formula="0.45*fraud_prob + 0.25*anomaly_score + 0.30*aml_signal (+ rule overrides)",
            risk_tiers={
                "LOW": "0-29",
                "MEDIUM": "30-59",
                "HIGH": "60-84",
                "CRITICAL": "85-100",
            },
            phase="Phase 1 Foundation",
        ),
    )

