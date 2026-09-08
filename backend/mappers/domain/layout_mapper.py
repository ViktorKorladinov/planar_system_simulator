from typing import List, Optional

from api.dtos.common.layout_dto import LayoutDTO, LayoutBasicDTO
from api.dtos.common.tile_dto import TileDTO
from api.dtos.requests.layout import LayoutSingleCreateRequestDTO
from api.dtos.responses.layout import LayoutBatchGetResponseDTO, LayoutSingleCreateResponseDTO, \
    LayoutSingleGetResponseDTO, LayoutSummaryResponseDTO
from domain.enums import TileType, LayoutType
from domain.models.common.tile import Tile
from domain.models.ingredient_list import IngredientListDomainModel
from domain.models.layout import LayoutDomainModel
from mappers.domain.ingredient_list_mapper import map_ingredient_list_domain_to_dto


def map_tile_dto_to_domain(dto: TileDTO) -> Tile:
    """Maps an TileDTO instance to a tile domain model.

    Args:
        dto: The Data Transfer Object containing tile details.

    Returns:
        A domain model instance of the tile.
    """
    return Tile(
        type=dto.type,
        dispensed_types=dto.dispensed_types,
        x=dto.x,
        y=dto.y
    )


def _get_tile_amount(tiles: List[Tile]) -> int:
    """Return total amount of tiles in the layout.

    Args:
        tiles: List of tile instances included in the layout.

    Returns:
        Amount of tiles in the layout.
    """
    return len(tiles)


def _get_interface_amount(tiles: List[Tile]) -> int:
    """Return total amount of tiles with interface type in the layout.

    Args:
        tiles: List of tile instances included in the layout.

    Returns:
        Amount of tiles with interface type in the layout.
    """
    return sum(1 for tile in tiles if tile.type == TileType.INTERFACE)


def _get_dispenser_amount(tiles: List[Tile]) -> int:
    """Return total amount of tiles with dispenser type in the layout.

    Args:
        tiles: List of tile instances included in the layout.

    Returns:
        Amount of tiles with dispenser type in the layout.
    """
    return sum(1 for tile in tiles if tile.type == TileType.DISPENSER)


def _is_filled(layout_type: LayoutType) -> bool:
    """Returns true if layout is filled (has no blocked tiles), false otherwise.

    Args:
        layout_type: Type of the layout.

    Returns:
        Returns true if layout is filled (has no blocked tiles), false otherwise.
    """
    return layout_type == LayoutType.SQUARE or layout_type == LayoutType.CUSTOM


def map_layout_dto_to_domain(dto: LayoutDTO,
                             ingredient_list_domain_model: IngredientListDomainModel) -> LayoutDomainModel:
    """Maps an LayoutDTO instance to a tile domain model.

    Args:
        dto: The Data Transfer Object containing layout details.
        ingredient_list_domain_model: Ingredient list which is assigned to the layout.

    Returns:
        A domain model instance of the layout.
    """
    tiles = [map_tile_dto_to_domain(tile) for tile in dto.tiles]
    return LayoutDomainModel(
        id=None,
        name=dto.name,
        type=dto.type,
        tiles=tiles,
        tile_amount=_get_tile_amount(tiles),
        interface_amount=_get_interface_amount(tiles),
        dispenser_amount=_get_dispenser_amount(tiles),
        filled=_is_filled(dto.type),
        ingredient_list=ingredient_list_domain_model
    )


def map_layout_single_create_request_dto_to_domain(dto: LayoutSingleCreateRequestDTO,
                                                   ingredient_list_domain_model: IngredientListDomainModel) -> LayoutDomainModel:
    """Maps an LayoutSingleCreateRequestDTO instance to a tile domain model.

    Args:
        dto: The Data Transfer Object containing layout details.
        ingredient_list_domain_model: The domain model of the ingredient list.

    Returns:
        A domain model instance of the layout.
    """
    tiles = [map_tile_dto_to_domain(tile) for tile in dto.tiles]
    return LayoutDomainModel(
        id=None,
        name=dto.name,
        type=dto.type,
        tiles=tiles,
        tile_amount=_get_tile_amount(tiles),
        interface_amount=_get_interface_amount(tiles),
        dispenser_amount=_get_dispenser_amount(tiles),
        filled=_is_filled(dto.type),
        ingredient_list=ingredient_list_domain_model
    )


def map_layout_to_layout_summary_response_dto(domain_model: LayoutDomainModel) -> LayoutSummaryResponseDTO:
    """Converts layout domain model into a Data Transfer Object.

        Args:
            domain_model: The source domain entity to be mapped.

        Returns:
            A DTO representation of the layout summary.
        """
    return LayoutSummaryResponseDTO(
        id=domain_model.id,
        name=domain_model.name,
        type=domain_model.type,
        tile_amount=domain_model.tile_amount,
        interface_amount=domain_model.interface_amount,
        dispenser_amount=domain_model.dispenser_amount,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at,
        ingredient_list_type=domain_model.ingredient_list.type
    )


def map_layout_domain_to_batch_get_response_dto(
        domain_models: List[LayoutDomainModel],
        page: int,
        size: int,
        total: int
) -> LayoutBatchGetResponseDTO:
    """Converts layout domain models into a Data Transfer Object.

    Args:
        domain_models: The source domain entities to be mapped.
        page: The page number.
        size: The page size.
        total: The total amount of pages.

    Returns:
        A DTO representation of the layout batch get response.
    """
    return LayoutBatchGetResponseDTO(
        layouts=[map_layout_to_layout_summary_response_dto(layout) for layout in domain_models],
        page=page,
        size=size,
        total=total
    )


def map_domain_to_tile_dto(domain_model: Tile) -> TileDTO:
    """Converts tile domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the tile.
    """
    return TileDTO(
        type=domain_model.type,
        dispensed_types=domain_model.dispensed_types,
        x=domain_model.x,
        y=domain_model.y
    )


def map_domain_to_layout_basic_dto(domain_model: LayoutDomainModel) -> LayoutBasicDTO:
    """Converts layout domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the layout.
    """
    return LayoutBasicDTO(
        name=domain_model.name,
        type=domain_model.type,
        tiles=[map_domain_to_tile_dto(tile) for tile in domain_model.tiles],
        ingredient_list=map_ingredient_list_domain_to_dto(domain_model.ingredient_list)
    )


def map_layout_domain_to_single_create_response_dto(
        domain_model: Optional[LayoutDomainModel],
        errors: List[str],
        is_dry_run: bool
) -> LayoutSingleCreateResponseDTO:
    """Converts layout domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.
        errors: List of validation errors encountered.
        is_dry_run: True if this was only a validation run.

    Returns:
        A DTO representation of the layout single create response.
    """
    if domain_model is None:
        return LayoutSingleCreateResponseDTO(
            name=None,
            id=None,
            type=None,
            tiles=None,
            dispenser_amount=None,
            tile_amount=None,
            interface_amount=None,
            is_dry_run=is_dry_run,
            errors=errors,
            ingredient_list=None,
            ingredient_list_id=None
        )
    return LayoutSingleCreateResponseDTO(
        name=domain_model.name,
        id=domain_model.id,
        type=domain_model.type,
        tiles=[map_domain_to_tile_dto(tile) for tile in domain_model.tiles],
        dispenser_amount=domain_model.dispenser_amount,
        tile_amount=domain_model.tile_amount,
        interface_amount=domain_model.interface_amount,
        is_dry_run=is_dry_run,
        errors=errors,
        ingredient_list=map_ingredient_list_domain_to_dto(domain_model.ingredient_list),
        ingredient_list_id=domain_model.ingredient_list.id,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at
    )


def map_layout_domain_to_single_get_response_dto(domain_model: LayoutDomainModel) -> LayoutSingleGetResponseDTO:
    """Converts layout domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the layout single get response.
    """
    return LayoutSingleGetResponseDTO(
        name=domain_model.name,
        id=domain_model.id,
        type=domain_model.type,
        tiles=[map_domain_to_tile_dto(tile) for tile in domain_model.tiles],
        dispenser_amount=domain_model.dispenser_amount,
        tile_amount=domain_model.tile_amount,
        interface_amount=domain_model.interface_amount,
        ingredient_list=map_ingredient_list_domain_to_dto(domain_model.ingredient_list),
        ingredient_list_id=domain_model.ingredient_list.id,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at
    )
