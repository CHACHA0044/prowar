"""
Simulator API — control endpoints and real-time SSE event stream.

Control mutations may be protected with a shared ``CONTROL_API_TOKEN``.
When configured on Render, send the token in the ``X-Control-Token`` header.
When unset, the endpoints remain public demo controls (documented limitation).
"""

import secrets
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.schemas.common import APIResponse
from app.schemas.simulator import SimulatorStatus, SpeedUpdateRequest
from app.services.simulator import simulator_service

router = APIRouter(prefix="/simulator", tags=["Simulator"])


async def require_control_token(
    x_control_token: Optional[str] = Header(default=None, alias="X-Control-Token"),
) -> None:
    """Optional shared-token guard for simulator mutations."""
    if not settings.CONTROL_API_TOKEN:
        return
    if not x_control_token or not secrets.compare_digest(
        x_control_token, settings.CONTROL_API_TOKEN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-Control-Token header.",
        )


@router.get(
    "/status",
    response_model=APIResponse[SimulatorStatus],
    status_code=status.HTTP_200_OK,
    summary="Get Simulator Status",
    description="Returns current replay state, speed multiplier, count and progress.",
)
async def get_simulator_status() -> APIResponse[SimulatorStatus]:
    return APIResponse(
        success=True,
        message="Simulator status retrieved",
        data=simulator_service.get_status(),
    )


@router.post(
    "/start",
    response_model=APIResponse[SimulatorStatus],
    status_code=status.HTTP_200_OK,
    summary="Start Simulator",
    description="Starts or resumes real-time historical transaction replay.",
    dependencies=[Depends(require_control_token)],
)
async def start_simulator() -> APIResponse[SimulatorStatus]:
    st = await simulator_service.start()
    return APIResponse(
        success=True,
        message="Simulator replay started",
        data=st,
    )


@router.post(
    "/pause",
    response_model=APIResponse[SimulatorStatus],
    status_code=status.HTTP_200_OK,
    summary="Pause Simulator",
    description="Pauses the active transaction replay.",
    dependencies=[Depends(require_control_token)],
)
async def pause_simulator() -> APIResponse[SimulatorStatus]:
    st = await simulator_service.pause()
    return APIResponse(
        success=True,
        message="Simulator replay paused",
        data=st,
    )


@router.post(
    "/reset",
    response_model=APIResponse[SimulatorStatus],
    status_code=status.HTTP_200_OK,
    summary="Reset Simulator",
    description="Resets the transaction replay back to the beginning.",
    dependencies=[Depends(require_control_token)],
)
async def reset_simulator() -> APIResponse[SimulatorStatus]:
    st = await simulator_service.reset()
    return APIResponse(
        success=True,
        message="Simulator replay reset to beginning",
        data=st,
    )


@router.patch(
    "/speed",
    response_model=APIResponse[SimulatorStatus],
    status_code=status.HTTP_200_OK,
    summary="Update Speed Multiplier",
    description="Adjust replay speed multiplier dynamically (0.5x to 100x).",
    dependencies=[Depends(require_control_token)],
)
async def update_speed(payload: SpeedUpdateRequest) -> APIResponse[SimulatorStatus]:
    st = await simulator_service.set_speed(payload.speed)
    return APIResponse(
        success=True,
        message=f"Simulator replay speed updated to {payload.speed}x",
        data=st,
    )


@router.get(
    "/stream",
    summary="Simulator SSE Stream",
    description="Server-Sent Events endpoint streaming transactions and periodic heartbeats.",
)
async def simulator_stream(request: Request):
    return StreamingResponse(
        simulator_service.event_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
