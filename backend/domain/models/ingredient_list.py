from typing_extensions import Self
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, model_validator

from domain.enums import NoteType, IngredientListType, TileType


class Ingredient(BaseModel):
    name: str = Field(
        ...,
        description="Name of the ingredient."
    )
    note_type: Optional[NoteType] = Field(
        default=None,
        description="Note assigned to the ingredient."
    )
    viscosity: Optional[float] = Field(
        default=None,
        description="Viscosity of the ingredient (cSt)."
    )
    volatility_rank: Optional[int] = Field(
        default=None,
        description="Volatility rank of the ingredient."
    )

    # Ensure that item name doesn't collide with tile types.
    @model_validator(mode='after')
    def validate_item_name(self) -> Self:
        if self.name == TileType.DISPENSER.value:
            raise ValueError(f"Name {TileType.DISPENSER.value} for dispensed type is forbidden.")
        if self.name == TileType.EMPTY.value:
            raise ValueError(f"Name {TileType.EMPTY.value} for dispensed type is forbidden.")
        if self.name == TileType.BLOCKED.value:
            raise ValueError(f"Name {TileType.BLOCKED.value} for dispensed type is forbidden.")
        if self.name == TileType.INTERFACE.value:
            raise ValueError(f"Name {TileType.INTERFACE.value} for dispensed type is forbidden.")
        if self.name == TileType.MIXER.value:
            raise ValueError(f"Name {TileType.MIXER.value} for dispensed type is forbidden.")
        if self.name == TileType.CAPPER.value:
            raise ValueError(f"Name {TileType.CAPPER.value} for dispensed type is forbidden.")
        return self


class IngredientListDomainModel(BaseModel):
    """
    Domain model representing list of ingredients.
    """
    id: Optional[int] = None
    name: Optional[str] = Field(
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
        description="Amount of ingredients on the list."
    )
    ingredients: List[Ingredient] = Field(
        ...,
        description="Ingredients that are on the list."
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Date of the creation."
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Date of the update."
    )

    # Ensure that ingredients contain required fields for chosen ingredient list type.
    @model_validator(mode='after')
    def validate_ingredients(self) -> Self:
        if self.type == IngredientListType.PERFUME.value:
            for ingredient in self.ingredients:
                if ingredient.note_type is None:
                    raise ValueError(
                        f"Note type must be defined for each ingredient when ingredient list of type Perfume is chosen.")
                if ingredient.viscosity is None:
                    raise ValueError(
                        f"Viscosity must be defined for each ingredient when ingredient list of type Perfume is chosen.")
                if ingredient.volatility_rank is None:
                    raise ValueError(
                        f"Volatility rank must be defined for each ingredient when ingredient list of type Perfume is chosen.")
        return self

    # Ensure that all ingredients have unique names.
    @model_validator(mode='after')
    def validate_unique_ingredients(self) -> Self:
        unique_names = set()
        for ingredient in self.ingredients:
            if ingredient.name.lower() in unique_names:
                raise ValueError(
                    f"Name \"{ingredient.name}\" is used for more than 1 ingredient, but names should be unique.")
            unique_names.add(ingredient.name.lower())
        return self
