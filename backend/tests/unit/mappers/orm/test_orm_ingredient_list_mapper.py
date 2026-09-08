from mappers.orm.ingredient_list_mapper import (
    map_ingredient_list_domain_to_orm,
    map_ingredient_list_orm_to_domain,
    update_ingredient_list_orm
)
from tests.factories.ingredient_list_factory import (
    get_ingredient_list_domain_model,
    get_ingredient_list_orm_model
)


def test_map_ingredient_list_domain_to_orm() -> None:
    # Arrange
    domain_model = get_ingredient_list_domain_model()

    # Act
    orm_model = map_ingredient_list_domain_to_orm(domain_model)

    # Assert
    assert orm_model.id == domain_model.id
    assert orm_model.name == domain_model.name
    assert orm_model.type == domain_model.type
    assert orm_model.ingredients == [ingredient.model_dump(mode='json') for ingredient in domain_model.ingredients]
    assert orm_model.ingredient_amount == domain_model.ingredient_amount


def test_map_ingredient_list_orm_to_domain() -> None:
    # Arrange
    orm_model = get_ingredient_list_orm_model()

    # Act
    domain_model = map_ingredient_list_orm_to_domain(orm_model)

    # Assert
    assert domain_model.model_dump(mode='json', exclude={"ingredients"}) == {
        "id": orm_model.id,
        "name": orm_model.name,
        "type": orm_model.type.value if hasattr(orm_model.type, 'value') else orm_model.type,
        "ingredient_amount": orm_model.ingredient_amount,
        "created_at": orm_model.created_at.isoformat() if orm_model.created_at else None,
        "updated_at": orm_model.updated_at.isoformat() if orm_model.updated_at else None
    }


def test_update_ingredient_list_orm() -> None:
    # Arrange
    domain_model = get_ingredient_list_domain_model()
    domain_model.name = "Updated Perfume Ingredients"

    orm_model = get_ingredient_list_orm_model()

    # Act
    update_ingredient_list_orm(domain_model=domain_model, orm_model=orm_model)

    # Assert
    assert orm_model.name == "Updated Perfume Ingredients"
