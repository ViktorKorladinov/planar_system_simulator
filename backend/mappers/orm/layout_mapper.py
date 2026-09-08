from db.orm_models.layout import LayoutORM
from domain.models.common.tile import Tile
from domain.models.layout import LayoutDomainModel
from mappers.orm.ingredient_list_mapper import map_ingredient_list_orm_to_domain


def map_layout_orm_to_domain(orm_model: LayoutORM) -> LayoutDomainModel:
    """Maps the SQLAlchemy Layout ORM object to the pure Domain Model.

    Args:
        orm_model: The SQLAlchemy Layout ORM object.

    Returns:
        The pure Layout Domain Model.
    """
    raw_tiles = orm_model.tiles if orm_model.tiles is not None else []
    domain_tiles = [Tile.model_validate(tile_dict) for tile_dict in raw_tiles]
    domain_ingredient_list = map_ingredient_list_orm_to_domain(orm_model.ingredient_list)
    return LayoutDomainModel(
        id=orm_model.id,
        name=orm_model.name,
        type=orm_model.type,
        tiles=domain_tiles,
        tile_amount=orm_model.tile_amount,
        interface_amount=orm_model.interface_amount,
        dispenser_amount=orm_model.dispenser_amount,
        filled=orm_model.filled,
        ingredient_list=domain_ingredient_list,
        created_at=orm_model.created_at,
        updated_at=orm_model.updated_at
    )


def map_layout_domain_to_orm(domain_model: LayoutDomainModel) -> LayoutORM:
    """Maps a pure Layout Domain Model to a SQLAlchemy ORM object.

    Args:
        domain_model: The pure Layout Domain Model.

    Returns:
        The SQLAlchemy Layout ORM object.
    """
    orm_tiles = [tile.model_dump(mode='json') for tile in domain_model.tiles]
    return LayoutORM(
        id=domain_model.id,
        name=domain_model.name,
        type=domain_model.type,
        tiles=orm_tiles,
        tile_amount=domain_model.tile_amount,
        interface_amount=domain_model.interface_amount,
        dispenser_amount=domain_model.dispenser_amount,
        filled=domain_model.filled,
        ingredient_list_id=domain_model.ingredient_list.id,
    )


def update_layout_orm(domain_model: LayoutDomainModel, orm_model: LayoutORM) -> None:
    """Updates the ORM object with data from Domain Model.

    Args:
        domain_model: The pure Layout Domain Model which holds updated data.
        orm_model: The SQLAlchemy Layout ORM object which should be updated.
    """
    orm_model.name = domain_model.name
