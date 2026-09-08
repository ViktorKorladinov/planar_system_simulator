import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.dtos.requests.webhook import ExperimentStatusUpdateDTO
from core.config import settings
from domain.enums import ExperimentStatus

webhook_router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"]
)

notifications_router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

bearer_scheme = HTTPBearer()
connected_clients = set()


def verify_webhook_api_key(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Validates the API key sent by the Celery SimulatorClient."""
    if credentials.credentials != settings.SIMULATOR_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key"
        )
    return credentials.credentials


async def broadcast_new_experiment_status(message: str) -> None:
    """Notify all clients about changed experiment status."""
    for client_queue in connected_clients:
        await client_queue.put(message)


@notifications_router.get(
    "/stream",
    summary="SSE endpoint for frontend notifications"
)
async def sse_notifications(request: Request):
    """Streams events to the connected frontends."""
    client_queue = asyncio.Queue()
    connected_clients.add(client_queue)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            while True:
                try:
                    message = await asyncio.wait_for(client_queue.get(), timeout=15.0)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"

                if await request.is_disconnected():
                    break
        finally:
            connected_clients.remove(client_queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@webhook_router.post(
    "/experiment-updated",
    summary="Internal webhook from Celery",
    dependencies=[Depends(verify_webhook_api_key)]
)
async def handle_experiment_status_update(payload: ExperimentStatusUpdateDTO):
    """
    Receives notification from the Celery worker that an experiment changed its status.

    Args:
        payload: Experiment status update webhook payload.
    Returns:
        Message with content based on experiment status.
    """
    if payload.status == ExperimentStatus.RUNNING:
        await broadcast_new_experiment_status('experiment_running')
    elif payload.status == ExperimentStatus.FINISHED:
        await broadcast_new_experiment_status('experiment_finished')
    elif payload.status == ExperimentStatus.FAILED:
        await broadcast_new_experiment_status('experiment_failed')
    return {"message": "Frontend notified successfully"}
