from unittest.mock import patch, MagicMock

import pytest
import requests

from api.dtos.requests.webhook import ExperimentStatusUpdateDTO
from clients.simulator.simulator_client import SimulatorClient
from domain.enums import ExperimentStatus


def test_init_sets_auth_header(simulator_client: object, api_key: object) -> None:
    # Assert
    assert "Authorization" in simulator_client.session.headers
    assert simulator_client.session.headers["Authorization"] == f"Bearer {api_key}"


@patch("clients.simulator.simulator_client.settings")
@patch("requests.Session.post")
def test_notify_experiment_status_change_success(mock_post: MagicMock, mock_settings: MagicMock,
                                                 simulator_client: SimulatorClient) -> None:
    # Arrange
    mock_settings.BACKEND_API_URL = "http://mock-backend"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    experiment_id = 10
    status = ExperimentStatus.FINISHED

    # Act
    result = simulator_client.notify_experiment_status_change(
        experiment_id=experiment_id,
        status=status
    )

    # Assert
    assert result is True

    expected_url = "http://mock-backend/webhooks/experiment-updated"
    expected_payload = ExperimentStatusUpdateDTO(
        experiment_id=experiment_id,
        status=status
    ).model_dump(mode='json')

    mock_post.assert_called_once_with(
        expected_url,
        json=expected_payload,
        timeout=5
    )


@patch("clients.simulator.simulator_client.settings")
@patch("requests.Session.post")
def test_notify_experiment_status_change_http_error(mock_post: object, mock_settings: object,
                                                    simulator_client: SimulatorClient) -> None:
    # Arrange
    mock_settings.BACKEND_API_URL = "http://mock-backend"
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
    mock_post.return_value = mock_response

    # Act & Assert
    with pytest.raises(requests.exceptions.RequestException) as exc_info:
        simulator_client.notify_experiment_status_change(1, ExperimentStatus.RUNNING)

    assert "404 Client Error" in str(exc_info.value)


@patch("clients.simulator.simulator_client.settings")
@patch("requests.Session.post")
def test_notify_experiment_status_change_timeout(mock_post: object, mock_settings: object,
                                                 simulator_client: SimulatorClient) -> None:
    # Arrange
    mock_settings.BACKEND_API_URL = "http://mock-backend"
    mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

    # Act & Assert
    with pytest.raises(requests.exceptions.RequestException) as exc_info:
        simulator_client.notify_experiment_status_change(2, ExperimentStatus.FAILED)

    assert "Connection timed out" in str(exc_info.value)
