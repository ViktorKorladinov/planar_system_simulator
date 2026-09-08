from datetime import datetime
from typing import List

from api.dtos.common.layout_dto import LayoutDTO
from api.dtos.common.tile_dto import TileDTO
from api.dtos.requests.layout import LayoutSingleCreateRequestDTO
from db.orm_models.layout import LayoutORM
from domain.enums import LayoutType, TileType
from domain.models.common.tile import Tile
from domain.models.layout import LayoutDomainModel
from tests.factories.ingredient_list_factory import get_ingredient_list_domain_model, get_ingredient_list_orm_model, \
    get_ingredient_list_dto


def get_layout_domain_model(
        id: int = 2,
        name: str = "Small Layout",
        type: LayoutType = LayoutType.CUSTOM,
        tiles: List[Tile] = None

) -> LayoutDomainModel:
    """Factory method to return a layout domain model.

    Args:
        id: Layout ID. Defaults to 2.
        name: Layout name. Defaults to "Small Layout".
        type: Layout type. Defaults to LayoutType.DOUBLE_LINE.
        tiles: List of tiles.

    Returns:
        Layout domain model.
    """
    if tiles is None:
        tiles = [
            Tile(type=TileType.INTERFACE, x=0, y=0),
            Tile(type=TileType.BLOCKED, x=0, y=1),
            Tile(type=TileType.CAPPER, x=1, y=0),
            Tile(type=TileType.MIXER, x=1, y=1),
            Tile(type=TileType.INTERFACE, x=2, y=0),
            Tile(type=TileType.DISPENSER, dispensed_types=["Aspirin", "Lisinopril"], x=2, y=1)
        ]

    return LayoutDomainModel(
        id=id,
        name=name,
        type=type,
        tiles=tiles,
        tile_amount=len(tiles),
        interface_amount=sum(1 for tile in tiles if tile.type == TileType.INTERFACE),
        dispenser_amount=sum(1 for tile in tiles if tile.type == TileType.DISPENSER),
        filled=not any(tile.type == TileType.BLOCKED for tile in tiles),
        ingredient_list=get_ingredient_list_domain_model(),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def get_layout_orm_model(
        id: int = 2,
        name: str = "Small Layout",
        type: LayoutType = LayoutType.CUSTOM,
        tiles: List[Tile] = None) -> LayoutORM:
    """Factory method to return a layout orm model.

        Args:
            id: Layout ID. Defaults to 2.
            name: Layout name. Defaults to "Small Layout".
            type: Layout type. Defaults to LayoutType.DOUBLE_LINE.
            tiles: List of tiles.

        Returns:
            Layout orm model.
        """
    if tiles is None:
        tiles = [
            {"type": TileType.INTERFACE.value, "x": 0, "y": 0, "dispensed_types": None},
            {"type": TileType.BLOCKED.value, "x": 0, "y": 1, "dispensed_types": None},
            {"type": TileType.CAPPER.value, "x": 1, "y": 0, "dispensed_types": None},
            {"type": TileType.DISPENSER.value, "x": 1, "y": 1, "dispensed_types": ["Aspirin", "Lisinopril"]},
            {"type": TileType.MIXER.value, "x": 2, "y": 0, "dispensed_types": None},
            {"type": TileType.INTERFACE.value, "x": 2, "y": 1, "dispensed_types": None},
        ]
    ingredient_list_orm = get_ingredient_list_orm_model()

    return LayoutORM(
        id=id,
        name=name,
        type=type,
        tiles=tiles,
        tile_amount=len(tiles),
        interface_amount=sum(1 for tile in tiles if tile['type'] == TileType.INTERFACE.value),
        dispenser_amount=sum(1 for tile in tiles if tile['type'] == TileType.DISPENSER.value),
        filled=not any(tile['type'] == TileType.BLOCKED.value for tile in tiles),
        ingredient_list_id=ingredient_list_orm.id,
        ingredient_list=ingredient_list_orm,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def get_tile_dto() -> TileDTO:
    """Returns tile DTO.

    Returns:
        Tile DTO.
    """
    return TileDTO(
        type=TileType.DISPENSER,
        dispensed_types=["Aspirin", "Lisinopril"],
        x=10,
        y=20
    )


def get_layout_dto() -> LayoutDTO:
    """Returns layout DTO.

    Returns:
        Layout DTO.
    """
    return LayoutDTO(
        name="Default Layout",
        type=LayoutType.CUSTOM,
        tiles=[
            TileDTO(type=TileType.DISPENSER, dispensed_types=["Aspirin", "Lisinopril"], x=0, y=0),
            TileDTO(type=TileType.INTERFACE, x=0, y=1),
            TileDTO(type=TileType.CAPPER, x=1, y=0),
            TileDTO(type=TileType.BLOCKED, x=1, y=1),
            TileDTO(type=TileType.MIXER, x=2, y=0),
            TileDTO(type=TileType.INTERFACE, x=2, y=1)
        ],
        ingredient_list_id=None,
        ingredient_list=get_ingredient_list_dto(),
    )


def get_layout_single_create_request_dto() -> LayoutSingleCreateRequestDTO:
    """Returns layout single create request DTO.

    Returns:
        Layout single create request DTO.
    """
    return LayoutSingleCreateRequestDTO(
        name="Default Layout",
        type=LayoutType.CUSTOM,
        tiles=[
            TileDTO(type=TileType.DISPENSER, dispensed_types=["Aspirin", "Lisinopril"], x=0, y=0),
            TileDTO(type=TileType.INTERFACE, x=0, y=1),
            TileDTO(type=TileType.CAPPER, x=1, y=0),
            TileDTO(type=TileType.DISPENSER, dispensed_types=["Aspirin"], x=1, y=1),
            TileDTO(type=TileType.MIXER, x=2, y=0),
            TileDTO(type=TileType.INTERFACE, x=2, y=1)
        ],
        ingredient_list_id=None,
        ingredient_list=get_ingredient_list_dto()
    )


def get_tile_domain_model(
        type: TileType = TileType.DISPENSER,
        dispensed_types: List[str] = None,
        x: int = 0,
        y: int = 1
) -> Tile:
    """Returns tile domain model.

    Args:
        type: Tile type. Defaults to "DISPENSER".
        dispensed_types: List of dispensed types.
        x: Tile x-axis. Defaults to 0.
        y: Tile y-axis. Defaults to 1.

    Returns:
        Tile domain model.
    """
    if type == TileType.DISPENSER and dispensed_types is None:
        dispensed_types = ["Aspirin", "Lisinopril"]
    return Tile(
        type=type,
        dispensed_types=dispensed_types,
        x=x,
        y=y
    )
