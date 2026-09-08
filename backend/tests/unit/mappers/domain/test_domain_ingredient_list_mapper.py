from datetime import datetime
from typing import List

from mappers.domain.ingredient_list_mapper import (
    map_ingredient_dto_to_domain,
    map_ingredient_domain_to_dto,
    map_ingredient_list_dto_to_domain,
    map_ingredient_list_domain_to_dto,
    map_ingredient_list_domain_to_single_create_response_dto,
    map_ingredient_list_domain_to_single_get_response_dto,
    map_ingredient_list_domain_to_short_response_dto,
    map_ingredient_list_domain_to_batch_get_response_dto,
    map_ingredient_list_single_create_request_dto_to_domain
)
from tests.factories.ingredient_list_factory import (
    get_ingredient_dto,
    get_ingredient_domain_model,
    get_ingredient_list_dto,
    get_ingredient_list_domain_model,
    get_ingredient_list_single_create_request_dto
)


def test_map_ingredient_dto_to_domain() -> None:
    # Arrange
    dto = get_ingredient_dto()

    # Act
    domain_model = map_ingredient_dto_to_domain(dto)

    # Assert
    assert domain_model.model_dump() == {
        "name": dto.name,
        "note_type": dto.note_type,
        "viscosity": dto.viscosity,
        "volatility_rank": dto.volatility_rank
    }


def test_map_ingredient_domain_to_dto() -> None:
    # Arrange
    domain_model = get_ingredient_domain_model()

    # Act
    dto = map_ingredient_domain_to_dto(domain_model)

    # Assert
    assert dto.model_dump() == {
        "name": domain_model.name,
        "note_type": domain_model.note_type,
        "viscosity": domain_model.viscosity,
        "volatility_rank": domain_model.volatility_rank
    }


def test_map_ingredient_list_dto_to_domain() -> None:
    # Arrange
    dto = get_ingredient_list_dto()

    # Act
    domain_model = map_ingredient_list_dto_to_domain(dto)

    # Assert
    assert domain_model.model_dump() == {
        "id": None,
        "name": dto.name,
        "type": dto.type,
        "ingredients": [ingredient.model_dump() for ingredient in dto.ingredients],
        "ingredient_amount": len(dto.ingredients),
        "created_at": None,
        "updated_at": None
    }


def test_map_ingredient_list_domain_to_dto() -> None:
    # Arrange
    domain_model = get_ingredient_list_domain_model()

    # Act
    dto = map_ingredient_list_domain_to_dto(domain_model)

    # Assert
    assert dto.model_dump() == {
        "name": domain_model.name,
        "type": domain_model.type,
        "ingredients": [ingredient.model_dump() for ingredient in domain_model.ingredients]
    }


def test_map_ingredient_list_domain_to_single_create_response_dto() -> None:
    # Arrange
    domain_model = get_ingredient_list_domain_model()
    domain_model.created_at = datetime.now()
    domain_model.updated_at = datetime.now()
    errors: List[str] = []
    is_dry_run = False

    # Act
    dto = map_ingredient_list_domain_to_single_create_response_dto(
        domain_model=domain_model,
        errors=errors,
        is_dry_run=is_dry_run
    )

    # Assert
    assert dto.model_dump() == {
        "id": domain_model.id,
        "name": domain_model.name,
        "type": domain_model.type,
        "ingredients": [ingredient.model_dump() for ingredient in domain_model.ingredients],
        "ingredient_amount": domain_model.ingredient_amount,
        "created_at": domain_model.created_at,
        "updated_at": domain_model.updated_at,
        "is_dry_run": is_dry_run,
        "errors": errors
    }


def test_map_ingredient_list_domain_to_single_create_response_dto_when_domain_model_is_none() -> None:
    # Arrange
    errors: List[str] = ["Constraint violation: Invalid ingredient type"]
    is_dry_run = True

    # Act
    dto = map_ingredient_list_domain_to_single_create_response_dto(
        domain_model=None,
        errors=errors,
        is_dry_run=is_dry_run
    )

    # Assert
    assert dto.model_dump() == {
        "id": None,
        "name": None,
        "type": None,
        "ingredients": [],
        "ingredient_amount": None,
        "created_at": None,
        "updated_at": None,
        "is_dry_run": is_dry_run,
        "errors": errors
    }


def test_map_ingredient_list_domain_to_single_get_response_dto() -> None:
    # Arrange
    domain_model = get_ingredient_list_domain_model()
    domain_model.created_at = datetime.now()
    domain_model.updated_at = datetime.now()

    # Act
    dto = map_ingredient_list_domain_to_single_get_response_dto(domain_model)

    # Assert
    assert dto.model_dump() == {
        "id": domain_model.id,
        "name": domain_model.name,
        "type": domain_model.type,
        "ingredients": [ingredient.model_dump() for ingredient in domain_model.ingredients],
        "ingredient_amount": domain_model.ingredient_amount,
        "created_at": domain_model.created_at,
        "updated_at": domain_model.updated_at
    }


def test_map_ingredient_list_domain_to_short_response_dto() -> None:
    # Arrange
    domain_model = get_ingredient_list_domain_model()
    domain_model.created_at = datetime.now()
    domain_model.updated_at = datetime.now()

    # Act
    dto = map_ingredient_list_domain_to_short_response_dto(domain_model)

    # Assert
    assert dto.model_dump() == {
        "id": domain_model.id,
        "name": domain_model.name,
        "type": domain_model.type,
        "ingredient_amount": domain_model.ingredient_amount,
        "created_at": domain_model.created_at,
        "updated_at": domain_model.updated_at
    }


def test_map_ingredient_list_domain_to_batch_get_response_dto() -> None:
    # Arrange
    domain_model_a = get_ingredient_list_domain_model(id=1, name="List A")
    domain_model_a.created_at = datetime.now()
    domain_model_a.updated_at = datetime.now()

    domain_model_b = get_ingredient_list_domain_model(id=2, name="List B")
    domain_model_b.created_at = datetime.now()
    domain_model_b.updated_at = datetime.now()

    total_pages = 5
    page = 1
    size = 10

    # Act
    dto = map_ingredient_list_domain_to_batch_get_response_dto(
        total_pages=total_pages,
        page=page,
        size=size,
        domain_models=[domain_model_a, domain_model_b]
    )

    # Assert
    assert dto.model_dump(mode='json') == {
        "total": total_pages,
        "page": page,
        "size": size,
        "ingredient_lists": [
            domain_model_a.model_dump(mode='json', exclude={"ingredients"}),
            domain_model_b.model_dump(mode='json', exclude={"ingredients"})
        ]
    }


def test_map_ingredient_list_single_create_request_dto_to_domain() -> None:
    # Arrange
    dto = get_ingredient_list_single_create_request_dto()

    # Act
    domain_model = map_ingredient_list_single_create_request_dto_to_domain(dto)

    # Assert
    assert domain_model.model_dump() == {
        "id": None,
        "name": dto.name,
        "type": dto.type,
        "ingredients": [ingredient.model_dump() for ingredient in dto.ingredients],
        "ingredient_amount": len(dto.ingredients),
        "created_at": None,
        "updated_at": None
    }
