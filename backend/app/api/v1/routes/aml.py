"""
AML (Anti-Money Laundering) router (Foundation Placeholder).
Prepared for Department 5: NetworkX graph analysis & laundering pattern detectors.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from app.schemas.common import APIResponse

router = APIRouter(prefix="/aml", tags=["AML Analysis"])


class AMLEngineInfo(BaseModel):
    engine_name: str
    status: str
    pattern_detectors: list[str]
    phase: str


@router.get(
    "/status",
    response_model=APIResponse[AMLEngineInfo],
    status_code=status.HTTP_200_OK,
    summary="AML Engine Status",
)
def get_aml_status() -> APIResponse[AMLEngineInfo]:
    return APIResponse(
        success=True,
        message="AML graph and typology engine registered.",
        data=AMLEngineInfo(
            engine_name="NetworkXAMLGraphEngine",
            status="READY_FOR_TYPOLOGIES",
            pattern_detectors=[
                "Structuring (Smurfing)",
                "Circular Flow Cycles (A->B->C->A)",
                "Fan-In / Fan-Out Hubs",
                "Rapid Pass-Through",
            ],
            phase="Phase 1 Foundation",
        ),
    )

