from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from core.config import settings
from main import app

client = TestClient(app)


def test_handle_experiment_status_update_fails_without_auth() -> None:
    # Act
    payload = {"experiment_id": 1, "status": "running"}
    response = client.post("/api/v1/webhooks/experiment-updated", json=payload)

    # Assert
    assert response.status_code == 401


def test_handle_experiment_status_update_fails_with_invalid_auth() -> None:
    # Act
    payload = {"experiment_id": 1, "status": "running"}
    headers = {"Authorization": "Bearer WRONG_KEY"}
    response = client.post("/api/v1/webhooks/experiment-updated", json=payload, headers=headers)

    # Assert
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid or missing API Key"


@patch("api.routers.notification_router.broadcast_new_experiment_status")
def test_handle_experiment_status_update_success(mock_broadcast: MagicMock) -> None:
    # Arrange
    original_key = settings.SIMULATOR_API_KEY
    settings.SIMULATOR_API_KEY = "test_valid_key"

    payload = {"experiment_id": 1, "status": "finished"}
    headers = {"Authorization": "Bearer test_valid_key"}

    try:
        # Act
        response = client.post("/api/v1/webhooks/experiment-updated", json=payload, headers=headers)

        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": "Frontend notified successfully"}
        mock_broadcast.assert_called_once_with('experiment_finished')
    finally:
        # Cleanup
        settings.SIMULATOR_API_KEY = original_key


def test_broadcast_new_experiment_status() -> None:
    """Verifies that the broadcast function puts the message in all connected client queues."""
    from api.routers.notification_router import broadcast_new_experiment_status, connected_clients
    import asyncio

    async def run_test() -> None:
        # Arrange
        mock_queue_1 = asyncio.Queue()
        mock_queue_2 = asyncio.Queue()
        connected_clients.add(mock_queue_1)
        connected_clients.add(mock_queue_2)

        try:
            # Act
            await broadcast_new_experiment_status("test_message")

            # Assert
            assert await mock_queue_1.get() == "test_message"
            assert await mock_queue_2.get() == "test_message"
        finally:
            # Cleanup global state
            connected_clients.clear()

    asyncio.run(run_test())
