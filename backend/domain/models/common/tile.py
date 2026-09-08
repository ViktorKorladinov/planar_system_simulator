from typing_extensions import Self
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.enums import TileType


class Tile(BaseModel):
    """
    Immutable value object representing a single tile.
    """
    model_config = ConfigDict(frozen=True)

    type: TileType = Field(
        ...,
        description="Type of the tile."
    )
    dispensed_types: Optional[List[str]] = Field(
        default=None,
        description="Types dispensed on this tile."
    )
    x: int = Field(
        ...,
        gt=-1,
        description="X coordinate of the tile."
    )
    y: int = Field(
        ...,
        gt=-1,
        description="Y coordinate of the tile."
    )

    # Ensure that dispensed types are included only when tile type is dispenser.
    @model_validator(mode='after')
    def validate_dispensed_types(self) -> Self:
        if self.type == TileType.DISPENSER and self.dispensed_types is None:
            raise ValueError("Dispensed types have to be included when tile is a dispenser.")
        if self.type != TileType.DISPENSER and self.dispensed_types is not None:
            raise ValueError("Dispensed types can be included only when tile is a dispenser.")
        return self

    # Ensure that dispensed types don't collide with tile types. (Required for solvers.)
    @model_validator(mode='after')
    def validate_dispensed_type_names(self) -> Self:
        if self.dispensed_types is not None:
            for dispensed_type in self.dispensed_types:
                if dispensed_type == TileType.DISPENSER.value:
                    raise ValueError(f"Name {TileType.DISPENSER.value} for dispensed type is forbidden.")
                if dispensed_type == TileType.EMPTY.value:
                    raise ValueError(f"Name {TileType.EMPTY.value} for dispensed type is forbidden.")
                if dispensed_type == TileType.BLOCKED.value:
                    raise ValueError(f"Name {TileType.BLOCKED.value} for dispensed type is forbidden.")
                if dispensed_type == TileType.INTERFACE.value:
                    raise ValueError(f"Name {TileType.INTERFACE.value} for dispensed type is forbidden.")
        return self
