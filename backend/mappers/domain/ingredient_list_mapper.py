from typing import Optional, List

from api.dtos.common.ingredient_list_dto import IngredientDTO, IngredientListDTO
from api.dtos.requests.ingredient_list import IngredientListSingleCreateRequestDTO
from api.dtos.responses.ingredient_list import IngredientListSingleCreateResponseDTO, \
    IngredientListSingleGetResponseDTO, IngredientListShortResponseDTO, IngredientListBatchGetResponseDTO
from domain.models.ingredient_list import Ingredient, IngredientListDomainModel


def map_ingredient_dto_to_domain(dto: IngredientDTO) -> Ingredient:
    """
    Maps an IngredientDTO instance to an Ingredient domain model.

    Args:
        dto: The Data Transfer Object containing ingredient details.

    Returns:
        A domain model instance of the ingredient.
    """
    return Ingredient(
        name=dto.name,
        note_type=dto.note_type,
        viscosity=dto.viscosity,
        volatility_rank=dto.volatility_rank
    )


def map_ingredient_domain_to_dto(domain_model: Ingredient) -> IngredientDTO:
    """Converts an Ingredient domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the ingredient for API responses.
    """
    return IngredientDTO(
        name=domain_model.name,
        note_type=domain_model.note_type,
        viscosity=domain_model.viscosity,
        volatility_rank=domain_model.volatility_rank
    )


def map_ingredient_list_dto_to_domain(dto: IngredientListDTO) -> IngredientListDomainModel:
    """
    Maps an IngredientListDTO instance to an Ingredient List domain model.

    Args:
        dto: The Data Transfer Object containing ingredient list details.

    Returns:
        A domain model instance of the ingredient list.
    """
    return IngredientListDomainModel(
        name=dto.name,
        type=dto.type,
        ingredients=[map_ingredient_dto_to_domain(ingredient) for ingredient in dto.ingredients],
        ingredient_amount=len(dto.ingredients)
    )


def map_ingredient_list_domain_to_dto(domain_model: IngredientListDomainModel) -> IngredientListDTO:
    """Converts an Ingredient List domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the ingredient list for API responses.
    """
    return IngredientListDTO(
        name=domain_model.name,
        type=domain_model.type,
        ingredients=[map_ingredient_domain_to_dto(ingredient) for ingredient in domain_model.ingredients]
    )


def map_ingredient_list_domain_to_single_create_response_dto(
        domain_model: Optional[IngredientListDomainModel],
        errors: List[str],
        is_dry_run: bool
) -> IngredientListSingleCreateResponseDTO:
    """Converts an Ingredient List domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.
        errors: List of validation errors encountered.
        is_dry_run: True if this was only a validation run.

    Returns:
        A DTO representation of the ingredient list single create response.
    """
    if domain_model is None:
        return IngredientListSingleCreateResponseDTO(
            id=None,
            name=None,
            type=None,
            ingredients=[],
            ingredient_amount=None,
            created_at=None,
            updated_at=None,
            is_dry_run=is_dry_run,
            errors=errors
        )
    return IngredientListSingleCreateResponseDTO(
        id=domain_model.id,
        name=domain_model.name,
        type=domain_model.type,
        ingredients=[map_ingredient_domain_to_dto(ingredient) for ingredient in domain_model.ingredients],
        ingredient_amount=domain_model.ingredient_amount,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at,
        is_dry_run=is_dry_run,
        errors=errors
    )


def map_ingredient_list_domain_to_single_get_response_dto(
        domain_model: IngredientListDomainModel) -> IngredientListSingleGetResponseDTO:
    """Converts an Ingredient List domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the ingredient list single get response.
    """
    return IngredientListSingleGetResponseDTO(
        id=domain_model.id,
        name=domain_model.name,
        type=domain_model.type,
        ingredients=[map_ingredient_domain_to_dto(ingredient) for ingredient in domain_model.ingredients],
        ingredient_amount=domain_model.ingredient_amount,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at
    )


def map_ingredient_list_domain_to_short_response_dto(
        domain_model: IngredientListDomainModel) -> IngredientListShortResponseDTO:
    """Converts an Ingredient List domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the ingredient list short response.
    """
    return IngredientListShortResponseDTO(
        id=domain_model.id,
        name=domain_model.name,
        type=domain_model.type,
        ingredient_amount=domain_model.ingredient_amount,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at
    )


def map_ingredient_list_domain_to_batch_get_response_dto(
        total_pages: int,
        page: int,
        size: int,
        domain_models: List[IngredientListDomainModel]) -> IngredientListBatchGetResponseDTO:
    """Converts ingredient list domain models into a Data Transfer Object.

    Args:
        domain_models: The source domain entities to be mapped.
        total_pages: The total number of pages available.
        page: The current page.
        size: The size of the page.

    Returns:
        A DTO representation of the ingredient list batch get response.
    """
    return IngredientListBatchGetResponseDTO(
        total=total_pages,
        page=page,
        size=size,
        ingredient_lists=[map_ingredient_list_domain_to_short_response_dto(domain_model) for domain_model in
                          domain_models]
    )


def map_ingredient_list_single_create_request_dto_to_domain(
        dto: IngredientListSingleCreateRequestDTO) -> IngredientListDomainModel:
    """Maps an ingredient list single create request DTO instance to an Ingredient List domain model.

    Args:
        dto: The Data Transfer Object containing ingredient details.

    Returns:
        A domain model instance of the ingredient list.
    """
    return IngredientListDomainModel(
        name=dto.name,
        type=dto.type,
        ingredients=[map_ingredient_dto_to_domain(ingredient) for ingredient in dto.ingredients],
        ingredient_amount=len(dto.ingredients)
    )
