"""
Analytics router (Foundation Placeholder).
Prepared for Department 9: Analytical summaries, model metrics, and reporting.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/analytics", tags=["Analytics & Reports"])


class AnalyticsOverview(BaseModel):
    phase: str
    status: str
    available_metrics: list[str]


@router.get(
    "/overview",
    response_model=APIResponse[AnalyticsOverview],
    status_code=status.HTTP_200_OK,
    summary="Analytics Overview",
)
def get_analytics_overview() -> APIResponse[AnalyticsOverview]:
    return APIResponse(
        success=True,
        message="Analytics module registered. True statistical aggregations will activate in subsequent phases.",
        data=AnalyticsOverview(
            phase="Phase 1 Foundation",
            status="READY_FOR_METRICS_PIPELINE",
            available_metrics=[
                "Processed Transaction Volume",
                "Alert Distribution by Severity",
                "Precision-Recall / F1 Evaluation Curves",
                "Graph Density & AML Subgraph Clusters",
            ],
        ),
    )

