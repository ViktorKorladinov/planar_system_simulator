from db.orm_models.ingredient_list import IngredientListORM
from domain.models.ingredient_list import IngredientListDomainModel, Ingredient


def map_ingredient_list_domain_to_orm(domain_model: IngredientListDomainModel) -> IngredientListORM:
    """Maps a pure Ingredient List Domain Model to a SQLAlchemy ORM object.

    Args:
        domain_model: The pure Ingredient List Domain Model.

    Returns:
        The SQLAlchemy Ingredient List ORM object.
    """
    orm_ingredients = [ingredient.model_dump(mode='json') for ingredient in domain_model.ingredients]
    return IngredientListORM(
        id=domain_model.id,
        name=domain_model.name,
        type=domain_model.type,
        ingredients=orm_ingredients,
        ingredient_amount=domain_model.ingredient_amount
    )


def map_ingredient_list_orm_to_domain(orm_model: IngredientListORM) -> IngredientListDomainModel:
    """Maps the SQLAlchemy Ingredient List ORM object to the pure Domain Model.

    Args:
        orm_model: The SQLAlchemy Ingredient List ORM object.

    Returns:
        The pure Ingredient List Domain Model.
    """
    raw_ingredient = orm_model.ingredients if orm_model.ingredients is not None else []
    domain_ingredients = [Ingredient.model_validate(ingredient_dict) for ingredient_dict in raw_ingredient]
    return IngredientListDomainModel(
        id=orm_model.id,
        name=orm_model.name,
        type=orm_model.type,
        ingredients=domain_ingredients,
        ingredient_amount=orm_model.ingredient_amount,
        created_at=orm_model.created_at,
        updated_at=orm_model.updated_at
    )


def update_ingredient_list_orm(domain_model: IngredientListDomainModel, orm_model: IngredientListORM) -> None:
    """Updates the ORM object with data from Domain Model.

    Args:
        domain_model: The pure Ingredient List Domain Model which holds updated data.
        orm_model: The SQLAlchemy Ingredient List ORM object which should be updated.
    """
    orm_model.name = domain_model.name
