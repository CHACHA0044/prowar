"""
Anomaly Detection router (Foundation Placeholder).
Prepared for Department 4: Unsupervised anomaly detection & account baselines.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from app.schemas.common import APIResponse

router = APIRouter(prefix="/anomaly", tags=["Anomaly Monitoring"])


class AnomalyEngineInfo(BaseModel):
    engine_name: str
    status: str
    detectors: list[str]
    phase: str


@router.get(
    "/status",
    response_model=APIResponse[AnomalyEngineInfo],
    status_code=status.HTTP_200_OK,
    summary="Anomaly Monitoring Status",
)
def get_anomaly_status() -> APIResponse[AnomalyEngineInfo]:
    return APIResponse(
        success=True,
        message="Unsupervised anomaly detection module registered.",
        data=AnomalyEngineInfo(
            engine_name="BehavioralAnomalyDetector",
            status="READY_FOR_CALIBRATION",
            detectors=["IsolationForest", "ZScoreRollingVelocity"],
            phase="Phase 1 Foundation",
        ),
    )

