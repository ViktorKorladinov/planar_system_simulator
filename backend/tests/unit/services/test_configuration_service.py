from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError, field_validator

from api.dtos.requests.configuration import ConfigurationSingleUpdateRequestDTO, ConfigurationSingleCreateRequestDTO
from core.exceptions import EntityNotFoundError
from domain.enums import ConfigurationSortField, SortDirection, SolverType
from domain.models.configuration import ConfigurationDomainModel
from services.configuration_service import ConfigurationService


@pytest.fixture
def mock_uow() -> MagicMock:
    uow = MagicMock()
    uow.__enter__.return_value = uow
    uow.configuration_repo = MagicMock()
    return uow


@pytest.fixture
def configuration_service(mock_uow: object) -> Any:
    return ConfigurationService(uow=mock_uow)


@pytest.fixture
def sample_domain_model() -> MagicMock:
    model = MagicMock(spec=ConfigurationDomainModel)
    model.id = 1
    model.name = "Test Config"
    return model


@pytest.fixture
def sample_create_request_dto() -> ConfigurationSingleCreateRequestDTO:
    return ConfigurationSingleCreateRequestDTO(
        name="Test Config",
        solver_type=SolverType.HEXALY,
        interface_time=3,
        dispensing_time=1,
        mover_amount=3,
        time_limit=60,
        process_amount=3
    )


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


def test_set_default_name_when_name_is_none(configuration_service: object, mock_uow: object) -> None:
    # Arrange
    domain_model = MagicMock(spec=ConfigurationDomainModel)
    domain_model.id = 5
    domain_model.name = None

    # Act
    configuration_service._set_default_name(domain_model)

    # Assert
    assert domain_model.name == "Configuration (5)"
    mock_uow.configuration_repo.update.assert_called_once_with(domain_model)
    mock_uow.commit.assert_called_once()


def test_set_default_name_skips_when_name_exists(configuration_service: object, mock_uow: object) -> None:
    # Arrange
    domain_model = MagicMock(spec=ConfigurationDomainModel)
    domain_model.id = 5
    domain_model.name = "Existing Name"

    # Act
    configuration_service._set_default_name(domain_model)

    # Assert
    assert domain_model.name == "Existing Name"
    mock_uow.configuration_repo.update.assert_not_called()
    mock_uow.commit.assert_not_called()


@patch("services.configuration_service.map_configuration_domain_to_single_create_response_dto")
@patch("services.configuration_service.map_configuration_single_create_request_dto_to_domain")
def test_create_success(
        mock_map_to_domain: object,
        mock_map_to_dto: object,
        configuration_service: object,
        mock_uow: object,
        sample_create_request_dto: object,
        sample_domain_model: object
) -> None:
    # Arrange
    mock_map_to_domain.return_value = sample_domain_model
    mock_uow.configuration_repo.create.return_value = sample_domain_model

    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = configuration_service.create(request_dto=sample_create_request_dto, is_dry_run=False)

    # Assert
    mock_uow.configuration_repo.create.assert_called_once_with(sample_domain_model)
    mock_uow.commit.assert_called()
    mock_map_to_dto.assert_called_once_with(domain_model=sample_domain_model, is_dry_run=False, errors=[])
    assert result == mock_response_dto


@patch("services.configuration_service.map_configuration_domain_to_single_create_response_dto")
@patch("services.configuration_service.map_configuration_single_create_request_dto_to_domain")
def test_create_dry_run(
        mock_map_to_domain: object,
        mock_map_to_dto: object,
        configuration_service: object,
        mock_uow: object,
        sample_create_request_dto: object,
        sample_domain_model: object
) -> None:
    # Arrange
    mock_map_to_domain.return_value = sample_domain_model
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = configuration_service.create(request_dto=sample_create_request_dto, is_dry_run=True)

    # Assert
    mock_uow.configuration_repo.create.assert_not_called()
    mock_uow.commit.assert_not_called()
    mock_map_to_dto.assert_called_once_with(domain_model=sample_domain_model, is_dry_run=True, errors=[])
    assert result == mock_response_dto


@patch("services.configuration_service.map_configuration_domain_to_single_create_response_dto")
@patch("services.configuration_service.map_configuration_single_create_request_dto_to_domain")
def test_create_validation_error(
        mock_map_to_domain: object,
        mock_map_to_dto: object,
        configuration_service: object,
        mock_uow: object,
        sample_create_request_dto: object
) -> None:
    # Arrange
    mock_map_to_domain.side_effect = generate_pydantic_validation_error()
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = configuration_service.create(request_dto=sample_create_request_dto, is_dry_run=False)

    # Assert
    mock_uow.configuration_repo.create.assert_not_called()
    mock_map_to_dto.assert_called_once()

    # Verify the error was cleaned ("Value error, " removed) and passed to DTO mapper
    passed_kwargs = mock_map_to_dto.call_args.kwargs
    assert passed_kwargs["domain_model"] is None
    assert "Custom validation error message" in passed_kwargs["errors"][0]
    assert result == mock_response_dto


@patch("services.configuration_service.map_configuration_domain_to_batch_get_response_dto")
def test_get_all_success(mock_map_to_dto: object, configuration_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.configuration_repo.find_all.return_value = ["model1", "model2"]
    mock_uow.configuration_repo.get_configuration_count.return_value = 25
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = configuration_service.get_all(page=2, size=10, search="Test")

    # Assert
    mock_uow.configuration_repo.find_all.assert_called_once_with(
        skip=10, limit=10, solver_types=None, search="Test",
        sort_by=ConfigurationSortField.CREATED_AT, sort_dir=SortDirection.ASC
    )
    mock_uow.configuration_repo.get_configuration_count.assert_called_once_with(
        solver_types=None, search="Test"
    )

    mock_map_to_dto.assert_called_once_with(
        domain_models=["model1", "model2"], page=2, size=10, total=3
    )
    assert result == mock_response_dto


@patch("services.configuration_service.map_configuration_domain_to_single_get_response_dto")
def test_get_by_id_success(mock_map_to_dto: object, configuration_service: object, mock_uow: object,
                           sample_domain_model: object) -> None:
    # Arrange
    mock_uow.configuration_repo.find_by_id.return_value = sample_domain_model
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = configuration_service.get_by_id(1)

    # Assert
    mock_uow.configuration_repo.find_by_id.assert_called_once_with(1)
    mock_map_to_dto.assert_called_once_with(sample_domain_model)
    assert result == mock_response_dto


def test_get_by_id_not_found(configuration_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.configuration_repo.find_by_id.return_value = None

    # Act & Assert
    with pytest.raises(EntityNotFoundError) as exc_info:
        configuration_service.get_by_id(999)

    assert exc_info.value.entity_name == "Configuration"
    assert exc_info.value.entity_id == 999


def test_delete_success(configuration_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.configuration_repo.delete.return_value = True

    # Act
    result = configuration_service.delete(1)

    # Assert
    mock_uow.configuration_repo.delete.assert_called_once_with(1)
    mock_uow.commit.assert_called_once()
    assert result is True


def test_delete_not_found(configuration_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.configuration_repo.delete.return_value = False

    # Act & Assert
    with pytest.raises(EntityNotFoundError) as exc_info:
        configuration_service.delete(999)

    assert exc_info.value.entity_name == "Configuration"
    assert exc_info.value.entity_id == 999
    mock_uow.commit.assert_not_called()


@patch("services.configuration_service.map_configuration_domain_to_single_get_response_dto")
def test_update_by_id_success(mock_map_to_dto: object, configuration_service: object, mock_uow: object,
                              sample_domain_model: object) -> None:
    # Arrange
    mock_uow.configuration_repo.find_by_id.return_value = sample_domain_model
    mock_uow.configuration_repo.update.return_value = True

    request_dto = ConfigurationSingleUpdateRequestDTO(name="Updated Name")
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = configuration_service.update_by_id(1, request_dto)

    # Assert
    assert sample_domain_model.name == "Updated Name"
    mock_uow.configuration_repo.update.assert_called_once_with(sample_domain_model)
    mock_uow.commit.assert_called_once()
    assert result == mock_response_dto


def test_update_by_id_not_found(configuration_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.configuration_repo.find_by_id.return_value = None
    request_dto = ConfigurationSingleUpdateRequestDTO(name="Updated Name")

    # Act & Assert
    with pytest.raises(EntityNotFoundError) as exc_info:
        configuration_service.update_by_id(999, request_dto)

    assert exc_info.value.entity_name == "Configuration"
    assert exc_info.value.entity_id == 999
    mock_uow.configuration_repo.update.assert_not_called()
