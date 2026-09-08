from datetime import datetime
from typing import List

from api.dtos.common.layout_dto import LayoutDTO
from api.dtos.common.tile_dto import TileDTO
from api.dtos.requests.layout import LayoutSingleCreateRequestDTO
from domain.enums import TileType, LayoutType
from domain.models.common.tile import Tile
from domain.models.layout import LayoutDomainModel
from mappers.domain.layout_mapper import (
    map_layout_domain_to_single_get_response_dto,
    map_tile_dto_to_domain,
    map_layout_dto_to_domain,
    map_layout_single_create_request_dto_to_domain,
    map_layout_domain_to_batch_get_response_dto,
    map_domain_to_tile_dto,
    map_domain_to_layout_basic_dto,
    map_layout_domain_to_single_create_response_dto,
    map_layout_to_layout_summary_response_dto
)
from tests.factories.ingredient_list_factory import get_ingredient_list_domain_model
from tests.factories.layout_factory import get_layout_domain_model


def test_get_name_returns_layout_name_when_set(layout_domain_model: LayoutDomainModel) -> None:
    # Arrange
    layout_domain_model.created_at = datetime.now()
    layout_domain_model.updated_at = datetime.now()

    # Act
    dto = map_layout_domain_to_single_get_response_dto(layout_domain_model)

    # Assert
    assert dto.name == layout_domain_model.name


def test_map_tile_dto_to_domain(tile_dto: TileDTO) -> None:
    # Act
    domain_model = map_tile_dto_to_domain(tile_dto)

    # Assert
    assert domain_model.model_dump() == {
        "type": tile_dto.type,
        "dispensed_types": tile_dto.dispensed_types,
        "x": tile_dto.x,
        "y": tile_dto.y
    }


def test_map_layout_dto_to_domain(layout_dto: LayoutDTO) -> None:
    # Arrange
    ingredient_list_domain_model = get_ingredient_list_domain_model()

    # Act
    domain_model = map_layout_dto_to_domain(layout_dto, ingredient_list_domain_model)

    # Assert
    assert domain_model.model_dump(exclude={"ingredient_list"}) == {
        "id": None,
        "name": layout_dto.name,
        "type": layout_dto.type,
        "tiles": [tile.model_dump() for tile in layout_dto.tiles],
        "tile_amount": len(layout_dto.tiles),
        "interface_amount": sum(1 for tile in layout_dto.tiles if tile.type == TileType.INTERFACE),
        "dispenser_amount": sum(1 for tile in layout_dto.tiles if tile.type == TileType.DISPENSER),
        "filled": True if domain_model.type == LayoutType.SQUARE or domain_model.type == LayoutType.CUSTOM else False,
        "created_at": None,
        "updated_at": None
    }
    assert domain_model.ingredient_list == ingredient_list_domain_model


def test_map_layout_single_create_request_dto_to_domain(
        layout_single_create_request_dto: LayoutSingleCreateRequestDTO) -> None:
    # Arrange
    ingredient_list_domain_model = get_ingredient_list_domain_model()

    # Act
    domain_model = map_layout_single_create_request_dto_to_domain(layout_single_create_request_dto,
                                                                  ingredient_list_domain_model)

    # Assert
    assert domain_model.model_dump(exclude={"ingredient_list"}) == {
        "id": None,
        "name": layout_single_create_request_dto.name,
        "type": layout_single_create_request_dto.type,
        "tiles": [tile.model_dump() for tile in layout_single_create_request_dto.tiles],
        "tile_amount": len(layout_single_create_request_dto.tiles),
        "interface_amount": sum(
            1 for tile in layout_single_create_request_dto.tiles if tile.type == TileType.INTERFACE),
        "dispenser_amount": sum(
            1 for tile in layout_single_create_request_dto.tiles if tile.type == TileType.DISPENSER),
        "filled": not any(tile.type == TileType.BLOCKED for tile in layout_single_create_request_dto.tiles),
        "created_at": None,
        "updated_at": None
    }
    assert domain_model.ingredient_list == ingredient_list_domain_model


def test_map_layout_to_layout_summary_response_dto(layout_domain_model: LayoutDomainModel) -> None:
    # Arrange
    layout_domain_model.created_at = datetime.now()
    layout_domain_model.updated_at = datetime.now()

    # Act
    dto = map_layout_to_layout_summary_response_dto(layout_domain_model)

    # Assert
    assert dto.model_dump() == {
        "id": layout_domain_model.id,
        "name": layout_domain_model.name,
        "type": layout_domain_model.type,
        "tile_amount": layout_domain_model.tile_amount,
        "interface_amount": layout_domain_model.interface_amount,
        "dispenser_amount": layout_domain_model.dispenser_amount,
        "created_at": layout_domain_model.created_at,
        "updated_at": layout_domain_model.updated_at,
        "ingredient_list_type": layout_domain_model.ingredient_list.type
    }


def test_map_layout_domain_to_batch_get_response_dto() -> None:
    # Arrange
    domain_model_a = get_layout_domain_model(id=1)
    domain_model_a.created_at = datetime.now()
    domain_model_a.updated_at = datetime.now()

    domain_model_b = get_layout_domain_model(id=2)
    domain_model_b.created_at = datetime.now()
    domain_model_b.updated_at = datetime.now()

    page = 2
    size = 3
    total = 10

    # Act
    dto = map_layout_domain_to_batch_get_response_dto(
        domain_models=[domain_model_a, domain_model_b],
        page=page,
        size=size,
        total=total
    )

    # Assert
    assert [layout.id for layout in dto.layouts] == [domain_model_a.id, domain_model_b.id]
    assert dto.page == page
    assert dto.size == size
    assert dto.total == total


def test_map_domain_to_tile_dto(tile_domain_model: Tile) -> None:
    # Act
    dto = map_domain_to_tile_dto(tile_domain_model)

    # Assert
    assert dto.model_dump() == {
        "type": tile_domain_model.type,
        "dispensed_types": tile_domain_model.dispensed_types,
        "x": tile_domain_model.x,
        "y": tile_domain_model.y
    }


def test_map_domain_to_layout_basic_dto(layout_domain_model: LayoutDomainModel) -> None:
    # Act
    dto = map_domain_to_layout_basic_dto(layout_domain_model)

    # Assert
    assert dto.model_dump() == {
        "name": layout_domain_model.name,
        "type": layout_domain_model.type,
        "tiles": [tile.model_dump() for tile in layout_domain_model.tiles],
        "ingredient_list": dto.ingredient_list.model_dump() if dto.ingredient_list else None
    }


def test_map_layout_domain_to_single_create_response_dto(layout_domain_model: LayoutDomainModel) -> None:
    # Arrange
    errors: List[str] = []
    is_dry_run = False

    # Act
    dto = map_layout_domain_to_single_create_response_dto(
        domain_model=layout_domain_model,
        errors=errors,
        is_dry_run=is_dry_run
    )

    # Assert
    assert dto.model_dump() == {
        "id": layout_domain_model.id,
        "name": layout_domain_model.name,
        "type": layout_domain_model.type,
        "tiles": [tile.model_dump() for tile in layout_domain_model.tiles],
        "dispenser_amount": layout_domain_model.dispenser_amount,
        "interface_amount": layout_domain_model.interface_amount,
        "tile_amount": layout_domain_model.tile_amount,
        "ingredient_list_id": layout_domain_model.ingredient_list.id,
        "ingredient_list": dto.ingredient_list.model_dump() if dto.ingredient_list else None,
        "created_at": layout_domain_model.created_at,
        "updated_at": layout_domain_model.updated_at,
        "is_dry_run": is_dry_run,
        "errors": errors
    }


def test_map_layout_domain_to_single_create_response_dto_when_domain_model_is_none() -> None:
    # Arrange
    errors: List[str] = ["Ingredient List not found"]
    is_dry_run = True

    # Act
    dto = map_layout_domain_to_single_create_response_dto(
        domain_model=None,
        errors=errors,
        is_dry_run=is_dry_run
    )

    # Assert
    assert dto.model_dump() == {
        "id": None,
        "name": None,
        "type": None,
        "tiles": None,
        "dispenser_amount": None,
        "interface_amount": None,
        "tile_amount": None,
        "ingredient_list_id": None,
        "ingredient_list": None,
        "created_at": None,
        "updated_at": None,
        "is_dry_run": is_dry_run,
        "errors": errors
    }


def test_map_layout_domain_to_single_get_response_dto(layout_domain_model: LayoutDomainModel) -> None:
    # Act
    dto = map_layout_domain_to_single_get_response_dto(layout_domain_model)

    # Assert
    assert dto.model_dump() == {
        "id": layout_domain_model.id,
        "name": layout_domain_model.name,
        "type": layout_domain_model.type,
        "tiles": [tile.model_dump() for tile in layout_domain_model.tiles],
        "dispenser_amount": layout_domain_model.dispenser_amount,
        "interface_amount": layout_domain_model.interface_amount,
        "tile_amount": layout_domain_model.tile_amount,
        "ingredient_list_id": layout_domain_model.ingredient_list.id,
        "ingredient_list": dto.ingredient_list.model_dump() if dto.ingredient_list else None,
        "created_at": layout_domain_model.created_at,
        "updated_at": layout_domain_model.updated_at
    }
