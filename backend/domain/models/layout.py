from typing_extensions import Self
from collections import deque
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Set

from pydantic import BaseModel, Field, ConfigDict, model_validator

from domain.enums import LayoutType, TileType, IngredientListType
from domain.models.common.tile import Tile
from domain.models.ingredient_list import IngredientListDomainModel


class LayoutDomainModel(BaseModel):
    """
    Domain Entity for a layout.
    Handles its own state changes and validates its own data.
    """
    model_config = ConfigDict(validate_assignment=True)

    id: Optional[int] = None
    name: Optional[str] = Field(
        ...,
        min_length=1,
        description="The name of the layout.",
    )
    type: LayoutType = Field(
        ...,
        description="Type of the layout.",
    )
    tiles: List[Tile] = Field(
        ...,
        description="Tiles included in this layout.",
    )
    tile_amount: int = Field(
        ...,
        description="Amount of tiles in the layout."
    )
    interface_amount: int = Field(
        ...,
        description="Amount of interfaces in the layout."
    )
    dispenser_amount: int = Field(
        ...,
        description="Amount of dispensers in the layout."
    )
    filled: bool = Field(
        ...,
        description="Determines if the layout is completely filled with tiles."
    )
    ingredient_list: IngredientListDomainModel = Field(
        ...,
        description="List with ingredients dispensed on this layout."
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment creation."
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment completion."
    )

    def get_reachable_tiles(self) -> List[Tile]:
        """Returns list with tiles that are reachable from any interface including interface itself.

        Returns:
            Returns list with tiles that are reachable from any interface including interface itself.
        """
        tile_map: Dict[Tuple[int, int], Tile] = {(t.x, t.y): t for t in self.tiles}
        start_tiles = [t for t in self.tiles if t.type == TileType.INTERFACE]
        if not start_tiles: return []

        queue = deque(start_tiles)
        visited_coords: Set[Tuple[int, int]] = {(t.x, t.y) for t in start_tiles}
        reachable_tiles: List[Tile] = list(start_tiles)

        while queue:
            current = queue.popleft()
            neighbors = [
                (current.x + 1, current.y),
                (current.x - 1, current.y),
                (current.x, current.y + 1),
                (current.x, current.y - 1),
            ]
            for nx, ny in neighbors:
                coords = (nx, ny)
                if coords in tile_map and coords not in visited_coords:
                    neighbor_tile = tile_map[coords]
                    if neighbor_tile.type != TileType.BLOCKED:
                        visited_coords.add(coords)
                        queue.append(neighbor_tile)
                        reachable_tiles.append(neighbor_tile)
        return reachable_tiles

    # Ensure that blocked tiles are used only for ring layout type.
    @model_validator(mode='after')
    def validate_blocked_tiles(self) -> Self:
        blocked_tile_amount = sum(1 for tile in self.tiles if tile.type == TileType.BLOCKED)
        if self.type != LayoutType.RING and self.type != LayoutType.CUSTOM and blocked_tile_amount > 0:
            raise ValueError("Blocked tiles are supported only for Ring and Custom layouts.")
        return self

    # Ensure that all dispensed types are included on ingredient list.
    @model_validator(mode='after')
    def validate_ingredients(self) -> Self:
        if self.ingredient_list is not None:
            available_ingredients = set(ingredient.name for ingredient in self.ingredient_list.ingredients)
            for tile in self.tiles:
                if tile.type == TileType.DISPENSER:
                    for ingredient in tile.dispensed_types:
                        if ingredient not in available_ingredients:
                            raise ValueError(
                                f"Dispensed ingredient {ingredient} isn't included on the ingredient list.")
        return self

    # Ensure that mixer and capper tiles are not used when ingredient list has medicine type.
    @model_validator(mode='after')
    def validate_mixer_and_capper_tiles(self) -> Self:
        if self.ingredient_list.type == IngredientListType.MEDICINE:
            for tile in self.tiles:
                if tile.type == TileType.CAPPER:
                    raise ValueError(f"Capper tiles aren't allowed when ingredient list has Medicine type.")
                if tile.type == TileType.MIXER:
                    raise ValueError(f"Mixer tiles aren't allowed when ingredient list has Medicine type.")
        return self

    # Ensure that at least one mixer and capper tile is present when perfume ingredient list is selected.
    @model_validator(mode='after')
    def validate_mixer_and_capper_presence(self) -> Self:
        if self.ingredient_list.type == IngredientListType.PERFUME:
            reachable_tiles = self.get_reachable_tiles()
            capper_tile_is_present = True if any(tile.type == TileType.CAPPER for tile in reachable_tiles) else False
            mixer_tile_is_present = True if any(tile.type == TileType.MIXER for tile in reachable_tiles) else False
            if not capper_tile_is_present:
                raise ValueError(
                    f"Capper tile has to be included in the layout and reachable from an interface when selected ingredient list has Perfume type.")
            if not mixer_tile_is_present:
                raise ValueError(
                    f"Mixer tile has to be included in the layout and reachable from an interface when ingredient list has Perfume type.")
        return self
