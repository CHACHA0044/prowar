"""
API v1 Router aggregation.
Registers all sub-routers under /api/v1 prefix.
"""

from fastapi import APIRouter
from backend.app.api.v1.routes import (
    health,
    transactions,
    fraud,
    anomaly,
    aml,
    risk,
    alerts,
    analytics,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router)
api_v1_router.include_router(transactions.router)
api_v1_router.include_router(fraud.router)
api_v1_router.include_router(anomaly.router)
api_v1_router.include_router(aml.router)
api_v1_router.include_router(risk.router)
api_v1_router.include_router(alerts.router)
api_v1_router.include_router(analytics.router)

