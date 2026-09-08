from typing import Optional

from pydantic import BaseModel, Field

from api.dtos.common.ingredient_list_dto import IngredientListDTO


class IngredientListSingleCreateRequestDTO(IngredientListDTO):
    """
    Data Transfer Object representing a single ingredient list create request.
    """
    pass


class IngredientListSingleUpdateRequestDTO(BaseModel):
    """
    Data Transfer Object representing a single ingredient list update request.
    """
    name: Optional[str] = Field(
        default=None,
        description="New name of the ingredient list."
    )
