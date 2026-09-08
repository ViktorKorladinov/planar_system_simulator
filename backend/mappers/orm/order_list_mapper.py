from db.orm_models.order_list import OrderListORM
from domain.models.order_list import OrderListDomainModel, Order


def map_order_list_domain_to_orm(domain_model: OrderListDomainModel) -> OrderListORM:
    """Maps a pure Order List Domain Model to a SQLAlchemy ORM object.

    Args:
        domain_model: The pure Order List Domain Model.

    Returns:
        The SQLAlchemy Order List ORM object.
    """
    orm_orders = [order.model_dump(mode='json') for order in domain_model.orders]
    return OrderListORM(
        id=domain_model.id,
        name=domain_model.name,
        type=domain_model.type,
        orders=orm_orders,
        order_amount=domain_model.order_amount
    )


def map_order_list_orm_to_domain(orm_model: OrderListORM) -> OrderListDomainModel:
    """Maps the SQLAlchemy Order List ORM object to the pure Domain Model.

    Args:
        orm_model: The SQLAlchemy Order List ORM object.

    Returns:
        The pure Order List Domain Model.
    """
    raw_order = orm_model.orders if orm_model.orders is not None else []
    domain_orders = [Order.model_validate(order_dict) for order_dict in raw_order]
    return OrderListDomainModel(
        id=orm_model.id,
        name=orm_model.name,
        type=orm_model.type,
        orders=domain_orders,
        order_amount=orm_model.order_amount,
        created_at=orm_model.created_at,
        updated_at=orm_model.updated_at
    )


def update_order_list_orm(domain_model: OrderListDomainModel, orm_model: OrderListORM) -> None:
    """Updates the ORM object with data from Domain Model.

    Args:
        domain_model: The pure Order List Domain Model which holds updated data.
        orm_model: The SQLAlchemy Order List ORM object which should be updated.
    """
    orm_model.name = domain_model.name
