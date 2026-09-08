from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError, field_validator

from api.dtos.requests.layout import (
    LayoutSingleCreateRequestDTO,
    LayoutSingleUpdateRequestDTO
)
from core.exceptions import EntityNotFoundError
from domain.enums import LayoutType, LayoutSortField, SortDirection
from domain.models.ingredient_list import IngredientListDomainModel
from domain.models.layout import LayoutDomainModel
from services.layout_service import LayoutService


@pytest.fixture
def mock_uow() -> MagicMock:
    uow = MagicMock()
    uow.__enter__.return_value = uow
    uow.layout_repo = MagicMock()
    uow.ingredient_list_repo = MagicMock()
    return uow


@pytest.fixture
def layout_service(mock_uow: object) -> LayoutService:
    return LayoutService(uow=mock_uow)


@pytest.fixture
def sample_ingredient_list_domain_model() -> MagicMock:
    model = MagicMock(spec=IngredientListDomainModel)
    model.id = 10
    model.name = "Test Ingredient List"
    return model


@pytest.fixture
def sample_layout_domain_model(sample_ingredient_list_domain_model: object) -> MagicMock:
    model = MagicMock(spec=LayoutDomainModel)
    model.id = 1
    model.name = "Test Layout"
    model.ingredient_list = sample_ingredient_list_domain_model
    return model


@pytest.fixture
def sample_create_request_dto() -> LayoutSingleCreateRequestDTO:
    return LayoutSingleCreateRequestDTO(
        name="Test Layout",
        type=LayoutType.SQUARE,
        tiles=[],
        ingredient_list_id=10,
        ingredient_list=None
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


def test_set_default_layout_name_when_none(layout_service: object, mock_uow: object,
                                           sample_layout_domain_model: object) -> None:
    # Arrange
    sample_layout_domain_model.name = None

    # Act
    layout_service._set_default_layout_name(sample_layout_domain_model)

    # Assert
    assert sample_layout_domain_model.name == "Layout (1)"
    mock_uow.layout_repo.update.assert_called_once_with(sample_layout_domain_model)


def test_set_default_layout_name_skips_when_exists(layout_service: object, mock_uow: object,
                                                   sample_layout_domain_model: object) -> None:
    # Act
    layout_service._set_default_layout_name(sample_layout_domain_model)

    # Assert
    assert sample_layout_domain_model.name == "Test Layout"
    mock_uow.layout_repo.update.assert_not_called()


def test_set_default_ingredient_list_name_when_none(layout_service: object, mock_uow: object,
                                                    sample_ingredient_list_domain_model: object) -> None:
    # Arrange
    sample_ingredient_list_domain_model.name = None

    # Act
    layout_service._set_default_ingredient_list_name(sample_ingredient_list_domain_model)

    # Assert
    assert sample_ingredient_list_domain_model.name == "Ingredient List (10)"
    mock_uow.ingredient_list_repo.update.assert_called_once_with(sample_ingredient_list_domain_model)


def test_resolve_ingredient_list_by_id_success(layout_service: object, mock_uow: object,
                                               sample_ingredient_list_domain_model: object) -> None:
    # Arrange
    mock_uow.ingredient_list_repo.find_by_id.return_value = sample_ingredient_list_domain_model

    # Act
    result = layout_service._resolve_ingredient_list(ingredient_list_id=10, ingredient_list=None)

    # Assert
    mock_uow.ingredient_list_repo.find_by_id.assert_called_once_with(10)
    assert result == sample_ingredient_list_domain_model


def test_resolve_ingredient_list_by_id_not_found(layout_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.ingredient_list_repo.find_by_id.return_value = None

    # Act & Assert
    with pytest.raises(EntityNotFoundError) as exc_info:
        layout_service._resolve_ingredient_list(ingredient_list_id=999, ingredient_list=None)

    assert exc_info.value.entity_name == "Ingredient List"
    assert exc_info.value.entity_id == 999


@patch("services.layout_service.map_ingredient_list_dto_to_domain")
def test_resolve_ingredient_list_by_dto_creation(mock_map_dto: object, layout_service: object, mock_uow: object,
                                                 sample_ingredient_list_domain_model: object) -> None:
    # Arrange
    mock_dto = MagicMock()
    mock_map_dto.return_value = sample_ingredient_list_domain_model
    mock_uow.ingredient_list_repo.create.return_value = sample_ingredient_list_domain_model

    # Act
    result = layout_service._resolve_ingredient_list(ingredient_list_id=None, ingredient_list=mock_dto)

    # Assert
    mock_map_dto.assert_called_once_with(mock_dto)
    mock_uow.ingredient_list_repo.create.assert_called_once_with(sample_ingredient_list_domain_model)
    assert result == sample_ingredient_list_domain_model


@patch.object(LayoutService, "_resolve_ingredient_list")
@patch("services.layout_service.map_layout_domain_to_single_create_response_dto")
@patch("services.layout_service.map_layout_single_create_request_dto_to_domain")
def test_create_success(
        mock_map_to_domain: object,
        mock_map_to_dto: object,
        mock_resolve_ing_list: object,
        layout_service: object,
        mock_uow: object,
        sample_create_request_dto: object,
        sample_layout_domain_model: object,
        sample_ingredient_list_domain_model: object
) -> None:
    # Arrange
    mock_resolve_ing_list.return_value = sample_ingredient_list_domain_model
    mock_map_to_domain.return_value = sample_layout_domain_model
    mock_uow.layout_repo.create.return_value = sample_layout_domain_model

    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = layout_service.create(request_dto=sample_create_request_dto, is_dry_run=False)

    # Assert
    mock_resolve_ing_list.assert_called_once_with(
        ingredient_list_id=sample_create_request_dto.ingredient_list_id,
        ingredient_list=sample_create_request_dto.ingredient_list
    )
    mock_uow.layout_repo.create.assert_called_once_with(sample_layout_domain_model)
    mock_uow.commit.assert_called()
    mock_map_to_dto.assert_called_once_with(domain_model=sample_layout_domain_model, is_dry_run=False, errors=[])
    assert result == mock_response_dto


@patch.object(LayoutService, "_resolve_ingredient_list")
@patch("services.layout_service.map_layout_domain_to_single_create_response_dto")
@patch("services.layout_service.map_layout_single_create_request_dto_to_domain")
def test_create_dry_run(
        mock_map_to_domain: object,
        mock_map_to_dto: object,
        mock_resolve_ing_list: object,
        layout_service: object,
        mock_uow: object,
        sample_create_request_dto: object,
        sample_layout_domain_model: object
) -> None:
    # Arrange
    mock_map_to_domain.return_value = sample_layout_domain_model
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = layout_service.create(request_dto=sample_create_request_dto, is_dry_run=True)

    # Assert
    mock_uow.layout_repo.create.assert_not_called()
    mock_uow.commit.assert_not_called()
    mock_map_to_dto.assert_called_once_with(domain_model=sample_layout_domain_model, is_dry_run=True, errors=[])
    assert result == mock_response_dto


@patch.object(LayoutService, "_resolve_ingredient_list")
@patch("services.layout_service.map_layout_domain_to_single_create_response_dto")
@patch("services.layout_service.map_layout_single_create_request_dto_to_domain")
def test_create_validation_error(
        mock_map_to_domain: object,
        mock_map_to_dto: object,
        mock_resolve_ing_list: object,
        layout_service: object,
        mock_uow: object,
        sample_create_request_dto: object
) -> None:
    # Arrange
    mock_map_to_domain.side_effect = generate_pydantic_validation_error()
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = layout_service.create(request_dto=sample_create_request_dto, is_dry_run=False)

    # Assert
    mock_uow.layout_repo.create.assert_not_called()
    mock_map_to_dto.assert_called_once()
    passed_kwargs = mock_map_to_dto.call_args.kwargs
    assert passed_kwargs["domain_model"] is None
    assert "Custom validation error message" in passed_kwargs["errors"][0]
    assert result == mock_response_dto


@patch("services.layout_service.map_layout_domain_to_batch_get_response_dto")
def test_get_all_success(mock_map_to_dto: object, layout_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.layout_repo.find_all.return_value = ["model1", "model2"]
    mock_uow.layout_repo.get_layout_count.return_value = 25
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = layout_service.get_all(
        page=2,
        size=10,
        search="Test",
        layout_types=[LayoutType.SQUARE]
    )

    # Assert
    mock_uow.layout_repo.find_all.assert_called_once_with(
        skip=10, limit=10, search="Test", layout_types=[LayoutType.SQUARE], ingredient_list_types=None,
        sort_by=LayoutSortField.CREATED_AT, sort_dir=SortDirection.ASC
    )
    mock_uow.layout_repo.get_layout_count.assert_called_once_with(
        layout_types=[LayoutType.SQUARE], search="Test"
    )

    mock_map_to_dto.assert_called_once_with(
        domain_models=["model1", "model2"], page=2, size=10, total=3
    )
    assert result == mock_response_dto


@patch("services.layout_service.map_layout_domain_to_single_get_response_dto")
def test_get_by_id_success(mock_map_to_dto: object, layout_service: object, mock_uow: object,
                           sample_layout_domain_model: object) -> None:
    # Arrange
    mock_uow.layout_repo.find_by_id.return_value = sample_layout_domain_model
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = layout_service.get_by_id(1)

    # Assert
    mock_uow.layout_repo.find_by_id.assert_called_once_with(1)
    mock_map_to_dto.assert_called_once_with(sample_layout_domain_model)
    assert result == mock_response_dto


def test_get_by_id_not_found(layout_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.layout_repo.find_by_id.return_value = None

    # Act & Assert
    with pytest.raises(EntityNotFoundError) as exc_info:
        layout_service.get_by_id(999)

    assert exc_info.value.entity_name == "Layout"
    assert exc_info.value.entity_id == 999


def test_delete_success(layout_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.layout_repo.delete.return_value = True

    # Act
    result = layout_service.delete(1)

    # Assert
    mock_uow.layout_repo.delete.assert_called_once_with(1)
    mock_uow.commit.assert_called_once()
    assert result is True


def test_delete_not_found(layout_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.layout_repo.delete.return_value = False

    # Act & Assert
    with pytest.raises(EntityNotFoundError) as exc_info:
        layout_service.delete(999)

    assert exc_info.value.entity_name == "Layout"
    assert exc_info.value.entity_id == 999
    mock_uow.commit.assert_not_called()


@patch("services.layout_service.map_layout_domain_to_single_get_response_dto")
def test_update_by_id_success(mock_map_to_dto: object, layout_service: object, mock_uow: object,
                              sample_layout_domain_model: object) -> None:
    # Arrange
    mock_uow.layout_repo.find_by_id.return_value = sample_layout_domain_model
    mock_uow.layout_repo.update.return_value = True

    request_dto = LayoutSingleUpdateRequestDTO(name="Updated Name")
    mock_response_dto = MagicMock()
    mock_map_to_dto.return_value = mock_response_dto

    # Act
    result = layout_service.update_by_id(1, request_dto)

    # Assert
    assert sample_layout_domain_model.name == "Updated Name"
    mock_uow.layout_repo.update.assert_called_once_with(sample_layout_domain_model)
    mock_uow.commit.assert_called_once()
    assert result == mock_response_dto


def test_update_by_id_not_found(layout_service: object, mock_uow: object) -> None:
    # Arrange
    mock_uow.layout_repo.find_by_id.return_value = None
    request_dto = LayoutSingleUpdateRequestDTO(name="Updated Name")

    # Act & Assert
    with pytest.raises(EntityNotFoundError) as exc_info:
        layout_service.update_by_id(999, request_dto)

    assert exc_info.value.entity_name == "Layout"
    assert exc_info.value.entity_id == 999
    mock_uow.layout_repo.update.assert_not_called()
