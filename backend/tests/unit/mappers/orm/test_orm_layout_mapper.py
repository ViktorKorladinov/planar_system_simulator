from db.orm_models.layout import LayoutORM
from domain.models.layout import LayoutDomainModel
from mappers.orm.layout_mapper import (
    map_layout_domain_to_orm,
    map_layout_orm_to_domain,
    update_layout_orm
)


def test_map_layout_orm_to_domain(layout_orm_model: LayoutORM) -> None:
    # Act
    domain_model = map_layout_orm_to_domain(layout_orm_model)

    # Assert
    assert domain_model.model_dump(exclude={"ingredient_list", "tiles"}) == {
        "id": layout_orm_model.id,
        "name": layout_orm_model.name,
        "type": layout_orm_model.type.value if hasattr(layout_orm_model.type, 'value') else layout_orm_model.type,
        "tile_amount": layout_orm_model.tile_amount,
        "interface_amount": layout_orm_model.interface_amount,
        "dispenser_amount": layout_orm_model.dispenser_amount,
        "filled": layout_orm_model.filled,
        "created_at": layout_orm_model.created_at,
        "updated_at": layout_orm_model.updated_at
    }
    assert domain_model.ingredient_list.id == layout_orm_model.ingredient_list_id


def test_map_layout_domain_to_orm(layout_domain_model: LayoutDomainModel) -> None:
    # Act
    orm_model = map_layout_domain_to_orm(layout_domain_model)

    # Assert
    assert orm_model.id == layout_domain_model.id
    assert orm_model.name == layout_domain_model.name
    assert orm_model.type == layout_domain_model.type
    assert orm_model.tiles == [tile.model_dump(mode="json") for tile in layout_domain_model.tiles]
    assert orm_model.tile_amount == layout_domain_model.tile_amount
    assert orm_model.interface_amount == layout_domain_model.interface_amount
    assert orm_model.dispenser_amount == layout_domain_model.dispenser_amount
    assert orm_model.filled == layout_domain_model.filled
    assert orm_model.ingredient_list_id == layout_domain_model.ingredient_list.id


def test_update_layout_orm(layout_domain_model: LayoutDomainModel, layout_orm_model: LayoutORM) -> None:
    # Arrange
    layout_domain_model.name = "Super New Layout Name"

    # Act
    update_layout_orm(domain_model=layout_domain_model, orm_model=layout_orm_model)

    # Assert
    assert layout_orm_model.name == "Super New Layout Name"
