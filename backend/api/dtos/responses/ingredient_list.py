from datetime import datetime
from typing import Optional, List

from pydantic import Field, BaseModel

from api.dtos.common.ingredient_list_dto import IngredientListDTO, IngredientDTO
from domain.enums import IngredientListType


class IngredientListResponseDTO(IngredientListDTO):
    id: int = Field(
        ...,
        description='ID of the ingredient list.'
    )
    ingredient_amount: int = Field(
        ...,
        description='Ingredient amount.'
    )
    created_at: datetime = Field(
        default=None,
        description="Date of the ingredient list creation."
    )
    updated_at: datetime = Field(
        default=None,
        description="Date of the ingredient list update."
    )


class IngredientListSingleCreateResponseDTO(BaseModel):
    """
    Data Transfer Object representing a single ingredient list create response.
    """
    id: Optional[int] = Field(
        default=None,
        description='ID of the ingredient list.'
    )
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Name of the ingredient list."
    )
    type: Optional[IngredientListType] = Field(
        default=None,
        description="Type of the ingredient list."
    )
    ingredients: Optional[List[IngredientDTO]] = Field(
        default=None,
        description="Ingredients that are on the list."
    )
    ingredient_amount: Optional[int] = Field(
        default=None,
        description='Ingredient amount.'
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Date of the ingredient list creation."
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Date of the ingredient list update."
    )
    is_dry_run: bool = Field(
        default=False,
        description="True if this was only a validation run."
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Validation errors in plain text caused by violation of domain constraints."
    )


class IngredientListSingleGetResponseDTO(IngredientListResponseDTO):
    """
    Data Transfer Object representing a single ingredient list get response.
    """
    pass


class IngredientListShortResponseDTO(BaseModel):
    """
    Data Transfer Object representing a short ingredient list response.
    """
    id: int = Field(
        ...,
        description='ID of the ingredient list.'
    )
    name: str = Field(
        default=None,
        min_length=1,
        description="Name of the ingredient list."
    )
    type: IngredientListType = Field(
        ...,
        description="Type of the ingredient list."
    )
    ingredient_amount: int = Field(
        ...,
        description='Ingredient amount.'
    )
    created_at: datetime = Field(
        default=None,
        description="Date of the ingredient list creation."
    )
    updated_at: datetime = Field(
        default=None,
        description="Date of the ingredient list update."
    )


class IngredientListBatchGetResponseDTO(BaseModel):
    """
    Data Transfer Object representing a batch ingredient list get response.
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
        description="Amount of ingredient lists on the page."
    )
    ingredient_lists: List[IngredientListShortResponseDTO] = Field(
        ...,
        description='Summary of ingredient lists.'
    )
