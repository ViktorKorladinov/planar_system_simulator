from typing_extensions import Self
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from api.dtos.common.ingredient_list_dto import IngredientListDTO
from api.dtos.common.tile_dto import TileDTO
from domain.enums import LayoutType


class LayoutBasicDTO(BaseModel):
    """
    Data Transfer Object representing basic info about layout for movers.
    """
    name: Optional[str] = Field(
        default=None,
        description="Name of the layout."
    )
    type: LayoutType = Field(
        ...,
        description="Type of the layout."
    )
    tiles: List[TileDTO] = Field(
        ...,
        description="List with tiles from the layout."
    )
    ingredient_list: Optional[IngredientListDTO] = Field(
        ...,
        description="Ingredients that should be used for this layout."
    )


class LayoutDTO(LayoutBasicDTO):
    """
    Data Transfer Object representing a layout for movers.
    """
    ingredient_list_id: Optional[int] = Field(
        ...,
        description="ID of the ingredient list which should be used for the layout."
    )

    # Ensure that ID or object is provided for ingredient list
    @model_validator(mode='after')
    def validate_dependencies(self) -> Self:
        has_ingredient_list_id = self.ingredient_list_id is not None
        has_ingredient_list = self.ingredient_list is not None
        if has_ingredient_list_id == has_ingredient_list:
            raise ValueError("Must provide exactly one of 'ingredient_list_id' OR 'ingredient_list' object.")
        return self
