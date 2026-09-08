from db.orm_models.order_list import OrderListORM
from domain.models.order_list import OrderListDomainModel
from mappers.orm.order_list_mapper import (
    map_order_list_domain_to_orm,
    map_order_list_orm_to_domain,
    update_order_list_orm
)


def test_map_order_list_domain_to_orm(order_list_domain_model: OrderListDomainModel) -> None:
    # Act
    orm_model = map_order_list_domain_to_orm(order_list_domain_model)

    # Assert
    assert orm_model.id == order_list_domain_model.id
    assert orm_model.name == order_list_domain_model.name
    assert orm_model.type == order_list_domain_model.type
    assert orm_model.orders == [order.model_dump(mode='json') for order in order_list_domain_model.orders]
    assert orm_model.order_amount == order_list_domain_model.order_amount


def test_map_order_list_orm_to_domain(order_list_orm_model: OrderListORM) -> None:
    # Act
    domain_model = map_order_list_orm_to_domain(order_list_orm_model)

    # Assert
    assert domain_model.model_dump(mode='json') == {
        "id": order_list_orm_model.id,
        "name": order_list_orm_model.name,
        "type": order_list_orm_model.type.value if hasattr(order_list_orm_model.type,
                                                           'value') else order_list_orm_model.type,
        "orders": order_list_orm_model.orders,
        "created_at": order_list_orm_model.created_at.isoformat() if order_list_orm_model.created_at else None,
        "updated_at": order_list_orm_model.updated_at.isoformat() if order_list_orm_model.updated_at else None,
        "order_amount": len(order_list_orm_model.orders)
    }


def test_update_order_list_orm(order_list_domain_model: OrderListDomainModel,
                               order_list_orm_model: OrderListORM) -> None:
    # Arrange
    order_list_domain_model.name = "New Updated List Name"

    # Act
    update_order_list_orm(domain_model=order_list_domain_model, orm_model=order_list_orm_model)

    # Assert
    assert order_list_orm_model.name == "New Updated List Name"
