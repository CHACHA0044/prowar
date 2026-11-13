"""
Simulator API — control endpoints and real-time SSE event stream.
"""

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from app.services.simulator import simulator_service
from app.schemas.simulator import SimulatorStatus, SpeedUpdateRequest
from app.schemas.common import APIResponse

router = APIRouter(prefix="/simulator", tags=["Simulator"])


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
async def simulator_stream():
    return StreamingResponse(
        simulator_service.event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
