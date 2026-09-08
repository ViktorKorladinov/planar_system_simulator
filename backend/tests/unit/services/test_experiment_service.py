from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError, field_validator

from core.exceptions import EntityNotFoundError
from domain.enums import ExperimentStatus
from domain.models.batch import BatchDomainModel
from domain.models.experiment import ExperimentDomainModel
from services.experiment_service import ExperimentService


@pytest.fixture
def mock_uow() -> MagicMock:
    uow = MagicMock()
    uow.__enter__.return_value = uow
    uow.experiment_repo = MagicMock()
    uow.configuration_repo = MagicMock()
    uow.layout_repo = MagicMock()
    uow.order_list_repo = MagicMock()
    uow.ingredient_list_repo = MagicMock()
    return uow


@pytest.fixture
def mock_task_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def experiment_service(mock_uow: object, mock_task_client: object) -> ExperimentService:
    return ExperimentService(uow=mock_uow, task_client=mock_task_client)


@pytest.fixture
def sample_experiment_model() -> MagicMock:
    model = MagicMock(spec=ExperimentDomainModel)
    model.id = 1
    model.name = "Test Experiment"
    model.status = ExperimentStatus.FINISHED
    model.task_id = "task-123"
    model.configuration = MagicMock()
    model.configuration.time_limit = 60
    model.layout = MagicMock()
    model.order_list = MagicMock()
    return model


@pytest.fixture
def sample_batch_model(sample_experiment_model: object) -> MagicMock:
    model = MagicMock(spec=BatchDomainModel)
    model.id = 5
    model.name = "Test Batch"
    model.experiments = [sample_experiment_model]
    return model


def generate_pydantic_validation_error() -> Any:
    """Helper to generate a real Pydantic ValidationError for testing."""

    class DummyModel(BaseModel):
        field: int

        @field_validator('field', mode='before')
        @classmethod
        def force_error(cls, v: object) -> Any:
            raise ValueError("Custom validation error message")

    try:
        DummyModel(field=1)
    except ValidationError as e:
        return e


def test_resolve_configuration_by_id(experiment_service: object, mock_uow: object) -> None:
    # Arrange
    mock_config = MagicMock()
    mock_uow.configuration_repo.find_by_id.return_value = mock_config

    result = experiment_service._resolve_configuration(configuration_id=1, configuration=None)

    mock_uow.configuration_repo.find_by_id.assert_called_once_with(1)
    assert result == mock_config


def test_resolve_configuration_by_id_not_found(experiment_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.configuration_repo.find_by_id.return_value = None

    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        experiment_service._resolve_configuration(configuration_id=999, configuration=None)


@patch("services.experiment_service.map_configuration_dto_to_domain")
def test_resolve_configuration_by_dto(mock_map: object, experiment_service: object, mock_uow: object) -> None:
    # Arrange
    mock_dto = MagicMock()
    mock_domain = MagicMock()
    mock_map.return_value = mock_domain
    mock_uow.configuration_repo.create.return_value = mock_domain

    # Act
    result = experiment_service._resolve_configuration(configuration_id=None, configuration=mock_dto)

    # Assert
    mock_uow.configuration_repo.create.assert_called_once_with(mock_domain)
    assert result == mock_domain


@patch.object(ExperimentService, "_resolve_layout")
@patch.object(ExperimentService, "_resolve_configuration")
@patch.object(ExperimentService, "_resolve_order_list")
@patch.object(ExperimentService, "_set_default_experiment_name")
@patch.object(ExperimentService, "_set_default_layout_name")
@patch.object(ExperimentService, "_set_default_configuration_name")
@patch.object(ExperimentService, "_set_default_order_list_name")
@patch("services.experiment_service.map_experiment_domain_to_single_create_response_dto")
@patch("services.experiment_service.map_experiment_create_request_dto_to_domain")
def test_create_and_enqueue_success(
        mock_map_to_domain: object, mock_map_to_dto: object,
        mock_set_order_name: object, mock_set_conf_name: object, mock_set_layout_name: object,
        mock_set_exp_name: object,
        mock_resolve_order: object, mock_resolve_conf: object, mock_resolve_layout: object,
        experiment_service: object, mock_uow: object, mock_task_client: object, sample_experiment_model: object
) -> None:
    # Arrange
    request_dto = MagicMock()
    request_dto.layout_id = 1
    request_dto.layout = None
    request_dto.configuration_id = 1
    request_dto.configuration = None
    request_dto.order_list_id = 1
    request_dto.order_list = None

    mock_map_to_domain.return_value = sample_experiment_model
    mock_uow.experiment_repo.create.return_value = sample_experiment_model
    mock_task_client.enqueue_experiment.return_value = "celery-task-456"

    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = experiment_service.create_and_enqueue(request_dto=request_dto, is_dry_run=False)

    # Assert
    mock_uow.experiment_repo.create.assert_called_once_with(sample_experiment_model)
    mock_task_client.enqueue_experiment.assert_called_once_with(sample_experiment_model.id)
    assert sample_experiment_model.task_id == "celery-task-456"
    assert mock_uow.commit.call_count >= 2

    mock_set_exp_name.assert_called_once()
    mock_map_to_dto.assert_called_once_with(domain_model=sample_experiment_model, errors=[], is_dry_run=False)
    assert result == mock_response_dto


@patch.object(ExperimentService, "_resolve_layout")
@patch.object(ExperimentService, "_resolve_configuration")
@patch.object(ExperimentService, "_resolve_order_list")
@patch("services.experiment_service.map_experiment_domain_to_single_create_response_dto")
@patch("services.experiment_service.map_experiment_create_request_dto_to_domain")
def test_create_and_enqueue_validation_error(
        mock_map_to_domain: object, mock_map_to_dto: object,
        mock_resolve_order: object, mock_resolve_conf: object, mock_resolve_layout: object,
        experiment_service: object, mock_uow: object, mock_task_client: object
) -> None:
    # Arrange
    request_dto = MagicMock()
    request_dto.layout_id = 1
    request_dto.layout = None
    request_dto.configuration_id = 1
    request_dto.configuration = None
    request_dto.order_list_id = 1
    request_dto.order_list = None

    mock_map_to_domain.side_effect = generate_pydantic_validation_error()

    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = experiment_service.create_and_enqueue(request_dto=request_dto, is_dry_run=False)

    # Assert
    mock_uow.experiment_repo.create.assert_not_called()
    mock_task_client.enqueue_experiment.assert_not_called()

    passed_kwargs = mock_map_to_dto.call_args.kwargs
    assert passed_kwargs["domain_model"] is None
    assert "Custom validation error message" in passed_kwargs["errors"][0]
    assert result == mock_response_dto


@patch("services.experiment_service.map_experiments_domain_to_paginated_get_response_dto")
def test_get_all_success(mock_map_to_dto: object, experiment_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.experiment_repo.find_all.return_value = ["exp1", "exp2"]
    mock_uow.experiment_repo.get_experiment_count.return_value = 25
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = experiment_service.get_all(page=2, size=10, search="Test")

    # Assert
    mock_uow.experiment_repo.find_all.assert_called_once()
    mock_map_to_dto.assert_called_once_with(domain_models=["exp1", "exp2"], page=2, size=10, total=3)
    assert result == mock_response_dto


def test_delete_success(experiment_service: object, mock_uow: object, mock_task_client: object,
                        sample_experiment_model: object) -> None:
    # Arrange
    mock_uow.experiment_repo.find_by_id.return_value = sample_experiment_model
    mock_uow.experiment_repo.delete.return_value = True

    # Act
    result = experiment_service.delete(1)

    # Assert
    mock_uow.experiment_repo.delete.assert_called_once_with(1)
    mock_task_client.cancel_experiment.assert_called_once_with("task-123")
    mock_uow.commit.assert_called_once()
    assert result is True


def test_delete_not_found(experiment_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.experiment_repo.find_by_id.return_value = None

    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        experiment_service.delete(999)


@patch("services.experiment_service.map_experiment_domain_to_simulation_get_response_dto")
def test_get_simulation_by_id_success(mock_map: object, experiment_service: object, mock_uow: object,
                                      sample_experiment_model: object) -> None:
    # Arrange
    sample_experiment_model.status = ExperimentStatus.FINISHED
    mock_uow.experiment_repo.find_by_id.return_value = sample_experiment_model
    mock_map.return_value = MagicMock()

    # Act
    result = experiment_service.get_simulation_by_id(1)

    # Assert
    assert result == mock_map.return_value


def test_get_simulation_by_id_rejects_unfinished(experiment_service: object, mock_uow: object,
                                                 sample_experiment_model: object) -> None:
    # Arrange
    sample_experiment_model.status = ExperimentStatus.RUNNING
    mock_uow.experiment_repo.find_by_id.return_value = sample_experiment_model

    # Act & Assert
    with pytest.raises(EntityNotFoundError):
        experiment_service.get_simulation_by_id(1)


def test_delete_batch_cancels_all_tasks(experiment_service: object, mock_uow: object, mock_task_client: object,
                                        sample_batch_model: object) -> None:
    # Arrange
    mock_uow.experiment_repo.find_batch_by_id.return_value = sample_batch_model
    mock_uow.experiment_repo.delete_batch.return_value = True

    # Act
    result = experiment_service.delete_batch(5)

    # Assert
    mock_uow.experiment_repo.delete_batch.assert_called_once_with(5)
    mock_uow.commit.assert_called_once()
    mock_task_client.cancel_experiment.assert_called_once_with("task-123")
    assert result is True
