from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError, field_validator

from api.dtos.requests.order_list import (
    OrderListSingleCreateRequestDTO,
    OrderListSingleUpdateRequestDTO
)
from core.exceptions import EntityNotFoundError
from domain.enums import OrderListSortField, SortDirection, OrderListType
from domain.models.order_list import OrderListDomainModel
from services.order_list_service import OrderListService


@pytest.fixture
def mock_uow() -> MagicMock:
    uow = MagicMock()
    uow.__enter__.return_value = uow
    uow.order_list_repo = MagicMock()
    return uow


@pytest.fixture
def order_list_service(mock_uow: object) -> Any:
    return OrderListService(uow=mock_uow)


@pytest.fixture
def sample_domain_model() -> MagicMock:
    model = MagicMock(spec=OrderListDomainModel)
    model.id = 1
    model.name = "Test Order List"
    return model


@pytest.fixture
def sample_configuration_create_request_dto() -> OrderListSingleCreateRequestDTO:
    return OrderListSingleCreateRequestDTO(
        name="Test Order List",
        type=OrderListType.MEDICINE,
        orders=[]
    )


@pytest.fixture
def sample_create_request_dto() -> Any:
    return OrderListSingleCreateRequestDTO(
        name="Test Ingredient List",
        type=OrderListType.MEDICINE,
        orders=[]
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


def test_set_default_name_when_name_is_none(order_list_service: object, mock_uow: object) -> None:
    # Arrange
    domain_model = MagicMock(spec=OrderListDomainModel)
    domain_model.id = 5
    domain_model.name = None

    # Act
    order_list_service._set_default_name(domain_model)

    # Assert
    assert domain_model.name == "Order List (5)"
    mock_uow.order_list_repo.update.assert_called_once_with(domain_model)
    mock_uow.commit.assert_called_once()


def test_set_default_name_skips_when_name_exists(order_list_service: object, mock_uow: object) -> None:
    # Arrange
    domain_model = MagicMock(spec=OrderListDomainModel)
    domain_model.id = 5
    domain_model.name = "Existing Name"

    # Act
    order_list_service._set_default_name(domain_model)

    # Assert
    assert domain_model.name == "Existing Name"
    mock_uow.order_list_repo.update.assert_not_called()
    mock_uow.commit.assert_not_called()


@patch("services.order_list_service.map_order_list_domain_to_single_create_response_dto")
@patch("services.order_list_service.map_order_list_single_create_request_dto_to_domain")
def test_create_success(
        mock_map_to_domain: object,
        mock_map_to_dto: object,
        order_list_service: object,
        mock_uow: object,
        sample_create_request_dto: object,
        sample_domain_model: object
) -> None:
    # Arrange
    mock_map_to_domain.return_value = sample_domain_model
    mock_uow.order_list_repo.create.return_value = sample_domain_model

    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = order_list_service.create(request_dto=sample_create_request_dto, is_dry_run=False)

    # Assert
    mock_uow.order_list_repo.create.assert_called_once_with(sample_domain_model)
    mock_uow.commit.assert_called()
    mock_map_to_dto.assert_called_once_with(domain_model=sample_domain_model, is_dry_run=False, errors=[])
    assert result == mock_response_dto


@patch("services.order_list_service.map_order_list_domain_to_single_create_response_dto")
@patch("services.order_list_service.map_order_list_single_create_request_dto_to_domain")
def test_create_dry_run(
        mock_map_to_domain: object,
        mock_map_to_dto: object,
        order_list_service: object,
        mock_uow: object,
        sample_create_request_dto: object,
        sample_domain_model: object
) -> None:
    # Arrange
    mock_map_to_domain.return_value = sample_domain_model
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = order_list_service.create(request_dto=sample_create_request_dto, is_dry_run=True)

    # Assert
    mock_uow.order_list_repo.create.assert_not_called()
    mock_uow.commit.assert_not_called()
    mock_map_to_dto.assert_called_once_with(domain_model=sample_domain_model, is_dry_run=True, errors=[])
    assert result == mock_response_dto


@patch("services.order_list_service.map_order_list_domain_to_single_create_response_dto")
@patch("services.order_list_service.map_order_list_single_create_request_dto_to_domain")
def test_create_validation_error(
        mock_map_to_domain: object,
        mock_map_to_dto: object,
        order_list_service: object,
        mock_uow: object,
        sample_create_request_dto: object
) -> None:
    # Arrange
    mock_map_to_domain.side_effect = generate_pydantic_validation_error()
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = order_list_service.create(request_dto=sample_create_request_dto, is_dry_run=False)

    # Assert
    mock_uow.order_list_repo.create.assert_not_called()
    mock_map_to_dto.assert_called_once()
    passed_kwargs = mock_map_to_dto.call_args.kwargs
    assert passed_kwargs["domain_model"] is None
    assert "Custom validation error message" in passed_kwargs["errors"][0]
    assert result == mock_response_dto


@patch("services.order_list_service.map_order_list_domain_to_batch_get_response_dto")
def test_get_all_success(mock_map_to_dto: object, order_list_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.order_list_repo.find_all.return_value = ["model1", "model2"]
    mock_uow.order_list_repo.get_order_list_count.return_value = 25
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = order_list_service.get_all(
        page=2,
        size=10,
        search="Test",
        types=[OrderListType.MEDICINE]
    )

    # Assert
    mock_uow.order_list_repo.find_all.assert_called_once_with(
        skip=10, limit=10, search="Test", types=[OrderListType.MEDICINE],
        sort_by=OrderListSortField.CREATED_AT, sort_dir=SortDirection.ASC
    )
    mock_uow.order_list_repo.get_order_list_count.assert_called_once_with(
        search="Test"
    )

    mock_map_to_dto.assert_called_once_with(
        domain_models=["model1", "model2"], page=2, size=10, total_pages=3
    )
    assert result == mock_response_dto


@patch("services.order_list_service.map_order_list_domain_to_single_get_response_dto")
def test_get_by_id_success(mock_map_to_dto: object, order_list_service: object, mock_uow: object,
                           sample_domain_model: object) -> None:
    # Arrange
    mock_uow.order_list_repo.find_by_id.return_value = sample_domain_model
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = order_list_service.get_by_id(1)

    # Assert
    mock_uow.order_list_repo.find_by_id.assert_called_once_with(1)
    mock_map_to_dto.assert_called_once_with(sample_domain_model)
    assert result == mock_response_dto


def test_get_by_id_not_found(order_list_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.order_list_repo.find_by_id.return_value = None

    # Act & Assert
    with pytest.raises(EntityNotFoundError) as exc_info:
        order_list_service.get_by_id(999)

    assert exc_info.value.entity_name == "Order List"
    assert exc_info.value.entity_id == 999


def test_delete_success(order_list_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.order_list_repo.delete.return_value = True

    # Act
    result = order_list_service.delete(1)

    # Assert
    mock_uow.order_list_repo.delete.assert_called_once_with(1)
    mock_uow.commit.assert_called_once()
    assert result is True


def test_delete_not_found(order_list_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.order_list_repo.delete.return_value = False

    # Act & Assert
    with pytest.raises(EntityNotFoundError) as exc_info:
        order_list_service.delete(999)

    assert exc_info.value.entity_name == "Order List"
    assert exc_info.value.entity_id == 999
    mock_uow.commit.assert_not_called()


@patch("services.order_list_service.map_order_list_domain_to_single_get_response_dto")
def test_update_by_id_success(mock_map_to_dto: object, order_list_service: object, mock_uow: object,
                              sample_domain_model: object) -> None:
    # Arrange
    mock_uow.order_list_repo.find_by_id.return_value = sample_domain_model
    mock_uow.order_list_repo.update.return_value = True

    request_dto = OrderListSingleUpdateRequestDTO(name="Updated Name")
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = order_list_service.update_by_id(1, request_dto)

    # Assert
    assert sample_domain_model.name == "Updated Name"
    mock_uow.order_list_repo.update.assert_called_once_with(sample_domain_model)
    mock_uow.commit.assert_called_once()
    assert result == mock_response_dto


def test_update_by_id_not_found(order_list_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.order_list_repo.find_by_id.return_value = None
    request_dto = OrderListSingleUpdateRequestDTO(name="Updated Name")

    # Act & Assert
    with pytest.raises(EntityNotFoundError) as exc_info:
        order_list_service.update_by_id(999, request_dto)

    assert exc_info.value.entity_name == "Order List"
    assert exc_info.value.entity_id == 999
    mock_uow.order_list_repo.update.assert_not_called()
