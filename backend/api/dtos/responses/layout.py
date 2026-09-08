from datetime import datetime
from typing import List, Optional

from pydantic import Field, BaseModel

from api.dtos.common.ingredient_list_dto import IngredientListDTO
from api.dtos.common.tile_dto import TileDTO
from domain.enums import LayoutType, IngredientListType


class LayoutSummaryResponseDTO(BaseModel):
    """
    Data Transfer Object representing a layout summary get response.
    """
    id: int = Field(
        ...,
        description="ID of the layout."
    )
    name: str = Field(
        ...,
        min_length=1,
        description="The name of the layout.",
    )
    type: LayoutType = Field(
        ...,
        description="Type of the layout.",
    )
    ingredient_list_type: IngredientListType = Field(
        ...,
        description="Type of the ingredient list."
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
    created_at: datetime = Field(
        default=None,
        description="Date of the experiment creation."
    )
    updated_at: datetime = Field(
        default=None,
        description="Date of the experiment completion."
    )


class LayoutBatchGetResponseDTO(BaseModel):
    """
    Data Transfer Object representing a batch layout get response.
    """
    total: int = Field(
        ...,
        description="Total amount of pages."
    )
    page: int = Field(
        ...,
        description="Page number."
    )
    size: int = Field(
        ...,
        description="Amount of simulations on the page."
    )
    layouts: List[LayoutSummaryResponseDTO] = Field(
        ...,
        description="List of layouts on the page."
    )


class LayoutSingleCreateResponseDTO(BaseModel):
    """
    Data Transfer Object representing a single layout create response.
    """
    id: Optional[int] = Field(
        default=None,
        description="ID of the layout."
    )
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Name of the layout."
    )
    type: Optional[LayoutType] = Field(
        default=None,
        description="Type of the layout."
    )
    tiles: Optional[List[TileDTO]] = Field(
        default=None,
        description="List with tiles from the layout."
    )
    tile_amount: Optional[int] = Field(
        default=None,
        description="Amount of tiles in the layout."
    )
    interface_amount: Optional[int] = Field(
        default=None,
        description="Amount of interfaces in the layout."
    )
    dispenser_amount: Optional[int] = Field(
        default=None,
        description="Amount of dispensers in the layout."
    )
    ingredient_list_id: Optional[int] = Field(
        ...,
        description="ID of the ingredient list which should be used for the layout."
    )
    ingredient_list: Optional[IngredientListDTO] = Field(
        ...,
        description="Ingredients that should be used for this layout."
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment creation."
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment completion."
    )
    is_dry_run: bool = Field(
        default=False,
        description="True if this was only a validation run."
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Validation errors in plain text caused by violation of domain constraints."
    )


class LayoutSingleGetResponseDTO(BaseModel):
    """
    Data Transfer Object representing a single layout get response.
    """
    id: int = Field(
        ...,
        description="ID of the layout."
    )
    name: str = Field(
        ...,
        min_length=1,
        description="The name of the layout.",
    )
    type: LayoutType = Field(
        ...,
        description="Type of the layout.",
    )
    tiles: List[TileDTO] = Field(
        ...,
        description="List with tiles from the layout."
    )
    ingredient_list_id: int = Field(
        ...,
        description="ID of the ingredient list."
    )
    ingredient_list: Optional[IngredientListDTO] = Field(
        ...,
        description="Ingredients that should be used for this layout."
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
    created_at: datetime = Field(
        default=None,
        description="Date of the experiment creation."
    )
    updated_at: datetime = Field(
        default=None,
        description="Date of the experiment completion."
    )
