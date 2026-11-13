"""
Fraud Detection router (Foundation Placeholder).
Prepared for Department 3: Supervised ML classification (LightGBM/XGBoost).
"""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/fraud", tags=["Fraud Detection"])


class FraudInspectionRequest(BaseModel):
    transaction_id: str = Field(..., description="ID of transaction to inspect")


class FraudModelInfoResponse(BaseModel):
    engine_name: str
    status: str
    supported_models: list[str]
    phase: str


@router.get(
    "/status",
    response_model=APIResponse[FraudModelInfoResponse],
    status_code=status.HTTP_200_OK,
    summary="Fraud Detection Engine Status",
)
def get_fraud_engine_status() -> APIResponse[FraudModelInfoResponse]:
    return APIResponse(
        success=True,
        message="Supervised fraud classification module registered.",
        data=FraudModelInfoResponse(
            engine_name="SupervisedFraudDetector",
            status="READY_FOR_MODEL_TRAINING",
            supported_models=["LightGBM", "LogisticRegressionBaseline"],
            phase="Phase 1 Foundation",
        ),
    )


@router.post(
    "/evaluate",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Evaluate Fraud Risk",
    description="Endpoint interface for scoring a transaction against the trained fraud model.",
)
def evaluate_fraud(payload: FraudInspectionRequest) -> APIResponse[dict]:
    return APIResponse(
        success=True,
        message="Fraud evaluation interface ready. Model weights will be integrated in subsequent phase.",
        data={
            "transaction_id": payload.transaction_id,
            "status": "NOT_EVALUATED_PHASE_1",
            "model_version": "none",
        },
    )

