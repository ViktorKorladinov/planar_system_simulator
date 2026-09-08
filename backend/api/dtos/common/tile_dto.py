from typing import List, Optional

from pydantic import BaseModel, Field

from domain.enums import TileType


class TileDTO(BaseModel):
    """
    Data Transfer Object representing tile on the layout.
    """
    type: TileType = Field(
        ...,
        description="Type of the tile.",
        examples=[TileType.INTERFACE.value, TileType.BLOCKED.value, TileType.EMPTY.value, TileType.DISPENSER.value]
    )
    dispensed_types: Optional[List[str]] = Field(
        default=None,
        description="Types dispensed on this tile."
    )
    x: int = Field(
        ...,
        gt=-1,
        description="X coordinate of the tile.",
        examples=["0"]
    )
    y: int = Field(
        ...,
        gt=-1,
        description="Y coordinate of the tile.",
        examples=["1"]
    )
