from typing import List

from api.dtos.common.order_list_dto import OrderListDTO, OrderDTO, OrderItemDTO
from api.dtos.requests.order_list import OrderListSingleCreateRequestDTO
from db.orm_models.order_list import OrderListORM
from domain.enums import OrderListType
from domain.models.order_list import OrderListDomainModel, Order, OrderItem


def _get_order_domain_models() -> List[Order]:
    """Returns list of Order domain models.
    Returns:
        List of Order domain models.
    """
    return [Order(t_max=100, items=[OrderItem(name="Aspirin", quantity=3), OrderItem(name="Lisinopril", quantity=1)]),
            Order(t_max=200, items=[OrderItem(name="Aspirin", quantity=3)]),
            Order(t_max=300, items=[OrderItem(name="Aspirin", quantity=2), OrderItem(name="Lisinopril", quantity=2)])]


def get_order_list_domain_model(
        id: int = 1,
        name: str = "Important Orders"
) -> OrderListDomainModel:
    """Returns order list domain model.

    Args:
        id: Order list id. Defaults to 1.
        name: Order list name. Defaults to "Important Orders".

    Returns:
        Order list domain model.
    """
    orders = _get_order_domain_models()
    return OrderListDomainModel(
        id=id,
        name=name,
        orders=orders,
        order_amount=len(orders),
        type=OrderListType.PERFUME
    )


def get_order_list_orm_model() -> OrderListORM:
    """Returns order list ORM model.

    Returns:
        Order list ORM model.
    """
    return OrderListORM(
        id=1,
        name="Important Orders",
        orders=[order.model_dump(mode='json') for order in get_order_list_domain_model().orders],
        order_amount=len(get_order_list_domain_model().orders),
        type=OrderListType.PERFUME
    )


def get_order_dtos() -> List[OrderDTO]:
    """Returns list of Order DTOs.

    Returns:
        List of Order DTOs.
    """
    return [OrderDTO(t_max=100,
                     items=[OrderItemDTO(name="Aspirin", quantity=3), OrderItemDTO(name="Lisinopril", quantity=1)]),
            OrderDTO(t_max=200, items=[OrderItemDTO(name="Aspirin", quantity=3)]),
            OrderDTO(t_max=300,
                     items=[OrderItemDTO(name="Aspirin", quantity=2), OrderItemDTO(name="Lisinopril", quantity=2)])]


def get_order_list_dto() -> OrderListDTO:
    """Returns order list DTO.
    Returns:
        Order list DTO.
    """
    return OrderListDTO(
        name="Important Orders",
        orders=get_order_dtos(),
        type=OrderListType.PERFUME
    )


def get_order_list_single_create_request_dto() -> OrderListSingleCreateRequestDTO:
    return OrderListSingleCreateRequestDTO(
        name="Important Orders",
        orders=get_order_dtos(),
        type=OrderListType.PERFUME
    )
