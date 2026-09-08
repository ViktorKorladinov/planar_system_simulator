from datetime import datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from api.dtos.requests.configuration import ConfigurationSingleCreateRequestDTO
from core.exceptions import EntityNotFoundError
from main import app

client = TestClient(app)


def _setup_mock_config_response(mock_service_call: object, errors: object = None, is_dry_run: object = False) -> None:
    """Sets up a fully Pydantic-compliant mock response for single configuration endpoints."""
    mock_result = MagicMock()
    mock_result.id = 1
    mock_result.name = "Test Configuration"
    mock_result.solver_type = "hexaly"
    mock_result.interface_time = 3
    mock_result.dispensing_time = 1
    mock_result.mover_amount = 3
    mock_result.time_limit = 60
    mock_result.process_amount = 3

    # Nullable fields to satisfy schema
    mock_result.batch_size = None
    mock_result.warmup = None
    mock_result.dispense_rate = None
    mock_result.viscosity_exponent = None
    mock_result.mover_speed = None
    mock_result.mixer_primary_time = None
    mock_result.mixer_final_time = None
    mock_result.capper_time = None

    mock_result.created_at = datetime.now()
    mock_result.updated_at = datetime.now()

    # Validation fields
    mock_result.errors = errors if errors is not None else []
    mock_result.is_dry_run = is_dry_run

    mock_service_call.return_value = mock_result


def _setup_mock_config_batch_response(mock_service_call: object) -> None:
    """Sets up a fully Pydantic-compliant mock response for paginated configurations."""
    mock_result = MagicMock()
    mock_result.total = 1
    mock_result.page = 1
    mock_result.size = 100

    mock_config = MagicMock()
    mock_config.id = 1
    mock_config.name = "Test Configuration"
    mock_config.solver_type = "hexaly"
    mock_config.interface_time = 3
    mock_config.dispensing_time = 1
    mock_config.mover_amount = 3
    mock_config.time_limit = 60
    mock_config.process_amount = 3
    mock_config.batch_size = None
    mock_config.warmup = None
    mock_config.dispense_rate = None
    mock_config.viscosity_exponent = None
    mock_config.mover_speed = None
    mock_config.mixer_primary_time = None
    mock_config.mixer_final_time = None
    mock_config.capper_time = None
    mock_config.created_at = datetime.now()
    mock_config.updated_at = datetime.now()

    mock_result.configurations = [mock_config]
    mock_service_call.return_value = mock_result


def test_create_configuration_returns_201_on_success(
        mock_configuration_service: MagicMock,
        configuration_single_create_request_dto: ConfigurationSingleCreateRequestDTO
) -> None:
    # Arrange
    _setup_mock_config_response(mock_configuration_service.create, errors=None, is_dry_run=False)

    # Act
    response = client.post("/api/v1/configurations/", json=configuration_single_create_request_dto.model_dump())

    # Assert
    assert response.status_code == 201
    mock_configuration_service.create.assert_called_once()
    assert response.json()["name"] == "Test Configuration"


def test_create_configuration_returns_200_on_dry_run(
        mock_configuration_service: MagicMock,
        configuration_single_create_request_dto: ConfigurationSingleCreateRequestDTO
) -> None:
    # Arrange
    _setup_mock_config_response(mock_configuration_service.create, errors=None, is_dry_run=True)

    # Act
    response = client.post("/api/v1/configurations/?dry_run=true",
                           json=configuration_single_create_request_dto.model_dump())

    # Assert
    assert response.status_code == 200
    mock_configuration_service.create.assert_called_once()


def test_create_configuration_returns_422_on_errors(
        mock_configuration_service: MagicMock,
        configuration_single_create_request_dto: ConfigurationSingleCreateRequestDTO
) -> None:
    # Arrange
    _setup_mock_config_response(mock_configuration_service.create, errors=["Invalid solver parameters"])

    # Act
    response = client.post("/api/v1/configurations/", json=configuration_single_create_request_dto.model_dump())

    # Assert
    assert response.status_code == 422
    assert "Invalid solver parameters" in response.json()["errors"]


def test_get_configurations_returns_200(mock_configuration_service: MagicMock) -> None:
    # Arrange
    _setup_mock_config_batch_response(mock_configuration_service.get_all)

    # Act
    response = client.get("/api/v1/configurations/?page=1&size=10")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["configurations"]) == 1
    mock_configuration_service.get_all.assert_called_once()


def test_get_configuration_returns_200_when_found(mock_configuration_service: MagicMock) -> None:
    # Arrange
    _setup_mock_config_response(mock_configuration_service.get_by_id)

    # Act
    response = client.get("/api/v1/configurations/1")

    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == "Test Configuration"
    mock_configuration_service.get_by_id.assert_called_once_with(1)


def test_get_configuration_returns_404_when_not_found(mock_configuration_service: MagicMock) -> None:
    # Arrange
    mock_configuration_service.get_by_id.side_effect = EntityNotFoundError(
        entity_name="Configuration",
        entity_id=999
    )

    # Act
    response = client.get("/api/v1/configurations/999")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Configuration with ID 999 not found."


def test_update_configuration_returns_200(mock_configuration_service: MagicMock) -> None:
    # Arrange
    _setup_mock_config_response(mock_configuration_service.update_by_id)
    payload = {"name": "Updated Configuration"}

    # Act
    response = client.patch("/api/v1/configurations/1", json=payload)

    # Assert
    assert response.status_code == 200
    mock_configuration_service.update_by_id.assert_called_once()


def test_update_configuration_returns_404_when_not_found(mock_configuration_service: MagicMock) -> None:
    # Arrange
    mock_configuration_service.update_by_id.side_effect = EntityNotFoundError(
        entity_name="Configuration",
        entity_id=999
    )
    payload = {"name": "Updated Configuration"}

    # Act
    response = client.patch("/api/v1/configurations/999", json=payload)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Configuration with ID 999 not found."


def test_delete_configuration_returns_204_when_deleted(mock_configuration_service: MagicMock) -> None:
    # Arrange
    mock_configuration_service.delete.return_value = True

    # Act
    response = client.delete("/api/v1/configurations/1")

    # Assert
    assert response.status_code == 204
    mock_configuration_service.delete.assert_called_once_with(1)


def test_delete_configuration_returns_404_when_not_found(mock_configuration_service: MagicMock) -> None:
    # Arrange
    mock_configuration_service.delete.side_effect = EntityNotFoundError(
        entity_name="Configuration",
        entity_id=1
    )

    # Act
    response = client.delete("/api/v1/configurations/1")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Configuration with ID 1 not found."
