from typing import List, Optional

from api.dtos.common.order_list_dto import OrderItemDTO, OrderDTO, OrderListDTO
from api.dtos.requests.order_list import OrderListSingleCreateRequestDTO
from api.dtos.responses.order_list import OrderListSingleCreateResponseDTO, OrderListSingleGetResponseDTO, \
    OrderListBatchGetResponseDTO, OrderListShortResponseDTO
from domain.models.order_list import OrderItem, Order, OrderListDomainModel


def map_order_item_dto_to_domain(dto: OrderItemDTO) -> OrderItem:
    """
    Maps an OrderItemDTO instance to an OrderItem domain model.

    Args:
        dto: The Data Transfer Object containing order item details.

    Returns:
        A domain model instance of the order item.
    """
    return OrderItem(
        name=dto.name,
        quantity=dto.quantity
    )


def map_order_item_domain_to_dto(domain_model: OrderItem) -> OrderItemDTO:
    """Converts an OrderItem domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the order item for API responses.
    """
    return OrderItemDTO(
        name=domain_model.name,
        quantity=domain_model.quantity
    )


def map_order_dto_to_domain(dto: OrderDTO) -> Order:
    """
    Maps an OrderDTO instance to an Order domain model.

    Args:
        dto: The Data Transfer Object containing order details.

    Returns:
        A domain model instance of the order.
    """
    return Order(
        t_max=dto.t_max,
        items=[map_order_item_dto_to_domain(item) for item in dto.items]
    )


def map_order_domain_to_dto(domain_model: Order) -> OrderDTO:
    """Converts an Order domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the order for API responses.
    """
    return OrderDTO(
        t_max=domain_model.t_max,
        items=[map_order_item_domain_to_dto(item) for item in domain_model.items]
    )


def map_order_list_dto_to_domain(dto: OrderListDTO) -> OrderListDomainModel:
    """
    Maps an OrderListDTO instance to an Order List domain model.

    Args:
        dto: The Data Transfer Object containing order details.

    Returns:
        A domain model instance of the order list.
    """
    return OrderListDomainModel(
        name=dto.name,
        type=dto.type,
        orders=[map_order_dto_to_domain(order) for order in dto.orders],
        order_amount=len(dto.orders)
    )


def map_order_list_domain_to_dto(domain_model: OrderListDomainModel) -> OrderListDTO:
    """Converts an Order List domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the order list for API responses.
    """
    return OrderListDTO(
        name=domain_model.name,
        type=domain_model.type,
        orders=[map_order_domain_to_dto(order) for order in domain_model.orders]
    )


def map_order_list_domain_to_single_create_response_dto(
        domain_model: Optional[OrderListDomainModel],
        errors: List[str],
        is_dry_run: bool
) -> OrderListSingleCreateResponseDTO:
    """Converts an Order List domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.
        errors: List of validation errors encountered.
        is_dry_run: True if this was only a validation run.

    Returns:
        A DTO representation of the order list single create response.
    """
    if domain_model is None:
        return OrderListSingleCreateResponseDTO(
            id=None,
            name=None,
            type=None,
            orders=[],
            order_amount=None,
            created_at=None,
            updated_at=None,
            is_dry_run=is_dry_run,
            errors=errors
        )
    return OrderListSingleCreateResponseDTO(
        id=domain_model.id,
        name=domain_model.name,
        type=domain_model.type,
        orders=[map_order_domain_to_dto(order) for order in domain_model.orders],
        order_amount=domain_model.order_amount,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at,
        is_dry_run=is_dry_run,
        errors=errors
    )


def map_order_list_domain_to_single_get_response_dto(
        domain_model: OrderListDomainModel) -> OrderListSingleGetResponseDTO:
    """Converts an Order List domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the order list single get response.
    """
    return OrderListSingleGetResponseDTO(
        id=domain_model.id,
        name=domain_model.name,
        type=domain_model.type,
        orders=[map_order_domain_to_dto(order) for order in domain_model.orders],
        order_amount=domain_model.order_amount,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at
    )


def map_order_list_domain_to_short_response_dto(domain_model: OrderListDomainModel) -> OrderListShortResponseDTO:
    """Converts an Order List domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the order list short response.
    """
    return OrderListShortResponseDTO(
        id=domain_model.id,
        name=domain_model.name,
        type=domain_model.type,
        order_amount=domain_model.order_amount,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at
    )


def map_order_list_domain_to_batch_get_response_dto(
        total_pages: int,
        page: int,
        size: int,
        domain_models: List[OrderListDomainModel]) -> OrderListBatchGetResponseDTO:
    """Converts order list domain models into a Data Transfer Object.

    Args:
        domain_models: The source domain entities to be mapped.
        total_pages: The total number of pages available.
        page: The current page.
        size: The size of the page.

    Returns:
        A DTO representation of the order list batch get response.
    """
    return OrderListBatchGetResponseDTO(
        total=total_pages,
        page=page,
        size=size,
        order_lists=[map_order_list_domain_to_short_response_dto(domain_model) for domain_model in domain_models]
    )


def map_order_list_single_create_request_dto_to_domain(dto: OrderListSingleCreateRequestDTO) -> OrderListDomainModel:
    """Maps an order list single create request DTO instance to an Order List domain model.

    Args:
        dto: The Data Transfer Object containing order details.

    Returns:
        A domain model instance of the order list.
    """
    return OrderListDomainModel(
        name=dto.name,
        type=dto.type,
        orders=[map_order_dto_to_domain(order) for order in dto.orders],
        order_amount=len(dto.orders)
    )
