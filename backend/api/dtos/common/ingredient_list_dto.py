from typing import Optional, List

from pydantic import BaseModel, Field

from domain.enums import NoteType, IngredientListType


class IngredientDTO(BaseModel):
    """
    Data Transfer Object representing a single ingredient.
    """
    name: str = Field(
        ...,
        description="Name of the ingredient."
    )
    note_type: Optional[NoteType] = Field(
        ...,
        description="Note assigned to the ingredient."
    )
    viscosity: Optional[float] = Field(
        ...,
        description="Viscosity of the ingredient (cSt)."
    )
    volatility_rank: Optional[int] = Field(
        ...,
        description="Volatility rank of the ingredient."
    )


class IngredientListDTO(BaseModel):
    """
    Data Transfer Object representing a list of ingredients.
    """
    name: Optional[str] = Field(
        default=None,
        description="Name of the ingredient list."
    )
    type: IngredientListType = Field(
        ...,
        description="Type of the ingredient list."
    )
    ingredients: List[IngredientDTO] = Field(
        ...,
        description="Ingredients that are on the list."
    )
