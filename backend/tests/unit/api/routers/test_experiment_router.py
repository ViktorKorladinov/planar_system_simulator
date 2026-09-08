from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from api.dtos.requests.experiment import ExperimentCreateRequestDTO, ExperimentMatrixCreateRequestDTO
from api.dtos.responses.experiment import ExperimentSingleGetResponseDTO
from core.exceptions import EntityNotFoundError
from domain.enums import LayoutType, SolverType, OrderListType, IngredientListType, ExperimentStatus
from main import app

client = TestClient(app)


def _setup_mock_experiment_response(mock_service_call: object, errors: object = None,
                                    is_dry_run: object = False) -> None:
    """Sets up a fully Pydantic-compliant mock response for single experiment creation."""
    mock_result = MagicMock()
    mock_result.name = "Valid Name"
    mock_result.status = ExperimentStatus.QUEUED
    mock_result.batch_name = "Valid Batch"

    # Layout mock
    mock_result.layout = MagicMock()
    mock_result.layout.name = "Valid Layout"
    mock_result.layout.type = LayoutType.CUSTOM

    # Ingredient List mock
    mock_ing_list = MagicMock()
    mock_ing_list.name = "Valid Ing"
    mock_ing_list.type = IngredientListType.MEDICINE

    mock_result.layout.ingredient_list = mock_ing_list
    mock_result.ingredient_list = mock_ing_list

    # Configuration mock
    mock_result.configuration = MagicMock()
    mock_result.configuration.name = "Valid Config"
    mock_result.configuration.solver_type = SolverType.HEXALY

    # Order List mock
    mock_result.order_list = MagicMock()
    mock_result.order_list.name = "Valid Orders"
    mock_result.order_list.type = OrderListType.MEDICINE

    mock_result.errors = errors if errors is not None else []
    mock_result.is_dry_run = is_dry_run

    mock_service_call.return_value = mock_result


def _setup_mock_batch_response(mock_service_call: object, errors: object = None, is_dry_run: object = False,
                               created_amount: object = 1) -> None:
    """Sets up a Pydantic-compliant mock response for batch creation endpoints."""
    mock_result = MagicMock()
    mock_result.name = "Valid Batch Name"
    mock_result.errors = errors if errors is not None else []
    mock_result.is_dry_run = is_dry_run
    mock_result.created_amount = created_amount
    mock_service_call.return_value = mock_result


def _setup_mock_basic_batch(mock_service_call: object) -> None:
    """Sets up a Pydantic-compliant mock response for batch get/update endpoints."""
    mock_result = MagicMock()
    mock_result.name = "Valid Batch Name"
    mock_service_call.return_value = mock_result


def test_create_experiment_returns_201_on_success(
        mock_experiment_service: MagicMock,
        experiment_create_request_dto: ExperimentCreateRequestDTO
) -> None:
    # Arrange
    _setup_mock_experiment_response(mock_experiment_service.create_and_enqueue, errors=None, is_dry_run=False)

    # Act
    response = client.post("/api/v1/experiments/", json=experiment_create_request_dto.model_dump())

    # Assert
    assert response.status_code == 201
    mock_experiment_service.create_and_enqueue.assert_called_once()


def test_create_experiment_returns_200_on_dry_run(
        mock_experiment_service: MagicMock,
        experiment_create_request_dto: ExperimentCreateRequestDTO
) -> None:
    # Arrange
    _setup_mock_experiment_response(mock_experiment_service.create_and_enqueue, errors=None, is_dry_run=True)

    # Act
    response = client.post("/api/v1/experiments/?dry_run=true", json=experiment_create_request_dto.model_dump())

    # Assert
    assert response.status_code == 200


def test_create_experiment_returns_422_on_errors(
        mock_experiment_service: MagicMock,
        experiment_create_request_dto: ExperimentCreateRequestDTO
) -> None:
    # Arrange
    _setup_mock_experiment_response(mock_experiment_service.create_and_enqueue,
                                    errors=["Layout and configuration incompatible"])

    # Act
    response = client.post("/api/v1/experiments/", json=experiment_create_request_dto.model_dump())

    # Assert
    assert response.status_code == 422


def test_get_experiment_returns_200_when_found(
        mock_experiment_service: MagicMock,
        experiment_single_get_response_dto: ExperimentSingleGetResponseDTO
) -> None:
    # Arrange
    mock_experiment_service.get_by_id.return_value = experiment_single_get_response_dto

    # Act
    response = client.get("/api/v1/experiments/1")

    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == experiment_single_get_response_dto.name


def test_get_experiment_returns_404_when_not_found(mock_experiment_service: MagicMock) -> None:
    # Arrange
    mock_experiment_service.get_by_id.side_effect = EntityNotFoundError(
        entity_name="Experiment",
        entity_id=999
    )

    # Act
    response = client.get("/api/v1/experiments/999")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment with ID 999 not found."


def test_get_experiments_returns_200(mock_experiment_service: MagicMock) -> None:
    # Arrange
    mock_paginated_response = MagicMock()
    mock_experiment_service.get_all.return_value = mock_paginated_response

    # Act
    response = client.get("/api/v1/experiments/?page=1&size=10")

    # Assert
    assert response.status_code == 200
    mock_experiment_service.get_all.assert_called_once()


def test_update_experiment_returns_200(
        mock_experiment_service: MagicMock,
        experiment_single_get_response_dto: ExperimentSingleGetResponseDTO
) -> None:
    # Arrange
    mock_experiment_service.update_by_id.return_value = experiment_single_get_response_dto
    payload = {"name": "Updated Experiment Name"}

    # Act
    response = client.patch("/api/v1/experiments/1", json=payload)

    # Assert
    assert response.status_code == 200
    mock_experiment_service.update_by_id.assert_called_once()


def test_delete_experiment_returns_204_when_deleted(mock_experiment_service: MagicMock) -> None:
    # Arrange
    mock_experiment_service.delete.return_value = True

    # Act
    response = client.delete("/api/v1/experiments/1")

    # Assert
    assert response.status_code == 204


def test_delete_experiment_returns_404_when_not_deleted(mock_experiment_service: MagicMock) -> None:
    # Arrange
    mock_experiment_service.delete.side_effect = EntityNotFoundError(
        entity_name="Experiment",
        entity_id=1
    )

    # Act
    response = client.delete("/api/v1/experiments/1")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Experiment with ID 1 not found."


def test_create_experiments_batch_returns_201_on_success(mock_experiment_service: MagicMock) -> None:
    # Arrange
    _setup_mock_batch_response(mock_experiment_service.create_and_enqueue_batch, errors=None, is_dry_run=False)
    payload = {
        "name": "New Batch",
        "experiments": [{"name": "Exp 1", "layout_id": 1, "configuration_id": 1, "order_list_id": 1}]
    }

    # Act
    response = client.post("/api/v1/experiments/batch/", json=payload)

    # Assert
    assert response.status_code == 201


def test_create_experiments_matrix_returns_201_on_success(
        mock_experiment_service: MagicMock,
        experiment_matrix_create_request_dto: ExperimentMatrixCreateRequestDTO
) -> None:
    # Arrange
    _setup_mock_batch_response(mock_experiment_service.create_and_enqueue_matrix, errors=None, is_dry_run=False)

    # Act
    response = client.post("/api/v1/experiments/batch/matrix", json=experiment_matrix_create_request_dto.model_dump())

    # Assert
    assert response.status_code == 201


def test_create_experiments_matrix_returns_422_on_errors_with_zero_created(
        mock_experiment_service: MagicMock,
        experiment_matrix_create_request_dto: ExperimentMatrixCreateRequestDTO
) -> None:
    # Arrange
    _setup_mock_batch_response(mock_experiment_service.create_and_enqueue_matrix, errors=["Some matrix error"],
                               created_amount=0)

    # Act
    response = client.post("/api/v1/experiments/batch/matrix", json=experiment_matrix_create_request_dto.model_dump())

    # Assert
    assert response.status_code == 422


def test_get_batch_returns_200_when_found(mock_experiment_service: MagicMock) -> None:
    # Arrange
    _setup_mock_basic_batch(mock_experiment_service.get_batch_by_id)

    # Act
    response = client.get("/api/v1/experiments/batch/5")

    # Assert
    assert response.status_code == 200
    mock_experiment_service.get_batch_by_id.assert_called_once_with(5)


def test_get_batch_returns_404_when_not_found(mock_experiment_service: MagicMock) -> None:
    # Arrange
    mock_experiment_service.get_batch_by_id.side_effect = EntityNotFoundError(
        entity_name="Batch",
        entity_id=999
    )

    # Act
    response = client.get("/api/v1/experiments/batch/999")

    # Assert
    assert response.status_code == 404


def test_get_batches_returns_200(mock_experiment_service: MagicMock) -> None:
    # Arrange
    mock_paginated_response = MagicMock()
    mock_experiment_service.get_all_batches.return_value = mock_paginated_response

    # Act
    response = client.get("/api/v1/experiments/batch/")

    # Assert
    assert response.status_code == 200
    mock_experiment_service.get_all_batches.assert_called_once()


def test_update_batch_returns_200(mock_experiment_service: MagicMock) -> None:
    # Arrange
    _setup_mock_basic_batch(mock_experiment_service.update_batch_by_id)
    payload = {"name": "Updated Batch Name"}

    # Act
    response = client.patch("/api/v1/experiments/batch/5", json=payload)

    # Assert
    assert response.status_code == 200
    mock_experiment_service.update_batch_by_id.assert_called_once()


def test_delete_batch_returns_204_when_deleted(mock_experiment_service: MagicMock) -> None:
    # Arrange
    mock_experiment_service.delete_batch.return_value = True

    # Act
    response = client.delete("/api/v1/experiments/batch/5")

    # Assert
    assert response.status_code == 204


def test_delete_batch_returns_404_when_not_deleted(mock_experiment_service: MagicMock) -> None:
    # Arrange
    mock_experiment_service.delete_batch.side_effect = EntityNotFoundError(
        entity_name="Batch",
        entity_id=999
    )

    # Act
    response = client.delete("/api/v1/experiments/batch/999")

    # Assert
    assert response.status_code == 404
