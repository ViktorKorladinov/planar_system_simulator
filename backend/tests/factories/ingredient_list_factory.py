from typing import List, Optional

from api.dtos.common.ingredient_list_dto import IngredientDTO, IngredientListDTO
from api.dtos.requests.ingredient_list import IngredientListSingleCreateRequestDTO
from db.orm_models.ingredient_list import IngredientListORM
from domain.enums import IngredientListType, NoteType
from domain.models.ingredient_list import Ingredient, IngredientListDomainModel


def get_ingredient_domain_model(
        name: str = "Ethanol",
        note_type: Optional[NoteType] = NoteType.PRIMARY_SOLVENT,
        viscosity: Optional[float] = 1.2,
        volatility_rank: Optional[int] = 5
) -> Ingredient:
    """Returns Ingredient domain model.

    Args:
        name: Name of the ingredient.
        note_type: Note assigned to the ingredient.
        viscosity: Viscosity of the ingredient (cSt).
        volatility_rank: Volatility rank of the ingredient.
    Returns:
        Ingredient domain model.
    """
    return Ingredient(
        name=name,
        note_type=note_type,
        viscosity=viscosity,
        volatility_rank=volatility_rank
    )


def get_ingredient_dto(
        name: str = "Ethanol",
        note_type: NoteType = NoteType.PRIMARY_SOLVENT,
        viscosity: float = 1.2,
        volatility_rank: int = 5
) -> IngredientDTO:
    """Returns Ingredient DTO.

    Args:
        name: Name of the ingredient.
        note_type: Note assigned to the ingredient.
        viscosity: Viscosity of the ingredient (cSt).
        volatility_rank: Volatility rank of the ingredient.
    Returns:
        Ingredient DTO.
    """
    return IngredientDTO(
        name=name,
        note_type=note_type,
        viscosity=viscosity,
        volatility_rank=volatility_rank
    )


def get_ingredient_list_domain_model(
        id: int = 1,
        name: str = "Standard Perfume Base",
        type: IngredientListType = IngredientListType.PERFUME,
        ingredients: Optional[List[Ingredient]] = None
) -> IngredientListDomainModel:
    """Returns Ingredient List domain model.

    Args:
        id: ID of the ingredient list
        name: Name of the ingredient.
        type: Type of the ingredient list.
        ingredients: List of ingredients.
    Returns:
        Ingredient List domain model.
    """
    if ingredients is None:
        ingredients = [
            get_ingredient_domain_model(),
            get_ingredient_domain_model(name="Aspirin", note_type=NoteType.HEART_NOTE, viscosity=5.5,
                                        volatility_rank=3),
            get_ingredient_domain_model(name="Lisinopril", note_type=NoteType.BASE_NOTE, viscosity=4.5,
                                        volatility_rank=2)
        ]
    return IngredientListDomainModel(
        id=id,
        name=name,
        type=type,
        ingredients=ingredients,
        ingredient_amount=len(ingredients)
    )


def get_ingredient_list_orm_model(
        id: int = 1,
        name: str = "Standard Perfume Base",
        type: IngredientListType = IngredientListType.PERFUME,
        ingredients: Optional[List[dict]] = None
) -> IngredientListORM:
    """Returns Ingredient List ORM model.

    Args:
        id: ID of the ingredient list
        name: Name of the ingredient.
        type: Type of the ingredient list.
        ingredients: List of ingredients.
    Returns:
        Ingredient List ORM model.
    """
    if ingredients is None:
        ingredients = [
            get_ingredient_domain_model().model_dump(mode='json'),
            get_ingredient_domain_model(name="Aspirin", note_type=NoteType.HEART_NOTE, viscosity=5.5,
                                        volatility_rank=3).model_dump(mode='json'),
            get_ingredient_domain_model(name="Lisinopril", note_type=NoteType.BASE_NOTE, viscosity=4.5,
                                        volatility_rank=2)
        ]
    return IngredientListORM(
        id=id,
        name=name,
        type=type,
        ingredients=ingredients,
        ingredient_amount=len(ingredients)
    )


def get_ingredient_list_dto() -> IngredientListDTO:
    """Returns Ingredient List DTO.
    Returns:
        Ingredient List DTO.
    """
    ingredients = [
        get_ingredient_dto(),
        get_ingredient_dto(name="Aspirin", note_type=NoteType.HEART_NOTE, viscosity=5.5, volatility_rank=3),
        get_ingredient_dto(name="Lisinopril", note_type=NoteType.BASE_NOTE, viscosity=4.5, volatility_rank=2)
    ]
    return IngredientListDTO(
        name="Standard Perfume Base",
        type=IngredientListType.PERFUME,
        ingredients=ingredients
    )


def get_ingredient_list_single_create_request_dto() -> IngredientListSingleCreateRequestDTO:
    """Returns Ingredient List Single Create Request DTO.
    Returns:
        Ingredient List Single Create Request DTO.
    """
    ingredients = [
        get_ingredient_dto(),
        get_ingredient_dto(name="Aspirin", note_type=NoteType.HEART_NOTE, viscosity=5.5, volatility_rank=3),
        get_ingredient_dto(name="Lisinopril", note_type=NoteType.BASE_NOTE, viscosity=4.5, volatility_rank=2)
    ]
    return IngredientListSingleCreateRequestDTO(
        name="Standard Perfume Base",
        type=IngredientListType.PERFUME,
        ingredients=ingredients
    )
