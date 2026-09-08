from datetime import datetime
from typing import List

from api.dtos.common.order_list_dto import OrderItemDTO, OrderDTO, OrderListDTO
from api.dtos.requests.order_list import OrderListSingleCreateRequestDTO
from domain.models.order_list import OrderListDomainModel, OrderItem, Order
from mappers.domain.order_list_mapper import (
    map_order_list_domain_to_single_get_response_dto,
    map_order_item_dto_to_domain,
    map_order_item_domain_to_dto,
    map_order_dto_to_domain,
    map_order_domain_to_dto,
    map_order_list_dto_to_domain,
    map_order_list_domain_to_dto,
    map_order_list_domain_to_single_create_response_dto,
    map_order_list_domain_to_short_response_dto,
    map_order_list_domain_to_batch_get_response_dto,
    map_order_list_single_create_request_dto_to_domain
)
from tests.factories.order_list_factory import get_order_list_domain_model


def test_get_name_returns_order_list_name_when_set(order_list_domain_model: OrderListDomainModel) -> None:
    # Arrange
    order_list_domain_model.created_at = datetime.now()
    order_list_domain_model.updated_at = datetime.now()

    # Act
    dto = map_order_list_domain_to_single_get_response_dto(order_list_domain_model)

    # Assert
    assert dto.name == order_list_domain_model.name


def test_map_order_item_dto_to_domain(order_item_dto: OrderItemDTO) -> None:
    # Act
    domain_model = map_order_item_dto_to_domain(order_item_dto)

    # Assert
    assert domain_model.model_dump() == {
        "name": order_item_dto.name,
        "quantity": order_item_dto.quantity
    }


def test_map_order_item_domain_to_dto(order_item_domain_model: OrderItem) -> None:
    # Act
    dto = map_order_item_domain_to_dto(order_item_domain_model)

    # Assert
    assert dto.model_dump() == {
        "name": order_item_domain_model.name,
        "quantity": order_item_domain_model.quantity
    }


def test_map_order_dto_to_domain(order_dto: OrderDTO) -> None:
    # Act
    domain_model = map_order_dto_to_domain(order_dto)

    # Assert
    assert domain_model.model_dump() == {
        "items": [item.model_dump(mode='json') for item in order_dto.items],
        "t_max": order_dto.t_max
    }


def test_map_order_domain_to_dto(order_domain_model: Order) -> None:
    # Act
    dto = map_order_domain_to_dto(order_domain_model)

    # Assert
    assert dto.model_dump() == {
        "items": [item.model_dump(mode='json') for item in order_domain_model.items],
        "t_max": order_domain_model.t_max
    }


def test_map_order_list_dto_to_domain(order_list_dto: OrderListDTO) -> None:
    # Act
    domain_model = map_order_list_dto_to_domain(order_list_dto)

    # Assert
    assert domain_model.model_dump() == {
        "id": None,
        "name": order_list_dto.name,
        "type": order_list_dto.type,
        "orders": [order.model_dump() for order in order_list_dto.orders],
        "created_at": None,
        "updated_at": None,
        "order_amount": len(order_list_dto.orders)
    }


def test_map_order_list_domain_to_dto(order_list_domain_model: OrderListDomainModel) -> None:
    # Act
    dto = map_order_list_domain_to_dto(order_list_domain_model)

    # Assert
    assert dto.model_dump() == {
        "name": order_list_domain_model.name,
        "type": order_list_domain_model.type,
        "orders": [order.model_dump() for order in order_list_domain_model.orders]
    }


def test_map_order_list_domain_to_single_create_response_dto(order_list_domain_model: OrderListDomainModel) -> None:
    # Arrange
    order_list_domain_model.created_at = datetime.now()
    order_list_domain_model.updated_at = datetime.now()
    errors: List[str] = ["Constraint violated"]
    is_dry_run = True

    # Act
    dto = map_order_list_domain_to_single_create_response_dto(
        domain_model=order_list_domain_model,
        errors=errors,
        is_dry_run=is_dry_run
    )

    # Assert
    assert dto.model_dump() == {
        "id": order_list_domain_model.id,
        "name": order_list_domain_model.name,
        "type": order_list_domain_model.type,
        "orders": [order.model_dump() for order in order_list_domain_model.orders],
        "order_amount": order_list_domain_model.order_amount,
        "created_at": order_list_domain_model.created_at,
        "updated_at": order_list_domain_model.updated_at,
        "is_dry_run": is_dry_run,
        "errors": errors
    }


def test_map_order_list_domain_to_single_create_response_dto_when_domain_model_is_none() -> None:
    # Arrange
    errors: List[str] = ["Validation failed"]
    is_dry_run = True

    # Act
    dto = map_order_list_domain_to_single_create_response_dto(
        domain_model=None,
        errors=errors,
        is_dry_run=is_dry_run
    )

    # Assert
    assert dto.model_dump() == {
        "id": None,
        "name": None,
        "type": None,
        "orders": [],
        "order_amount": None,
        "created_at": None,
        "updated_at": None,
        "is_dry_run": is_dry_run,
        "errors": errors
    }


def test_map_order_list_domain_to_single_get_response_dto(order_list_domain_model: OrderListDomainModel) -> None:
    # Arrange
    order_list_domain_model.created_at = datetime.now()
    order_list_domain_model.updated_at = datetime.now()

    # Act
    dto = map_order_list_domain_to_single_get_response_dto(order_list_domain_model)

    # Assert
    assert dto.model_dump() == {
        "id": order_list_domain_model.id,
        "name": order_list_domain_model.name,
        "type": order_list_domain_model.type,
        "orders": [order.model_dump() for order in order_list_domain_model.orders],
        "created_at": order_list_domain_model.created_at,
        "updated_at": order_list_domain_model.updated_at,
        "order_amount": order_list_domain_model.order_amount
    }


def test_map_order_list_domain_to_short_response_dto(order_list_domain_model: OrderListDomainModel) -> None:
    # Arrange
    order_list_domain_model.created_at = datetime.now()
    order_list_domain_model.updated_at = datetime.now()

    # Act
    dto = map_order_list_domain_to_short_response_dto(order_list_domain_model)

    # Assert
    assert dto.model_dump() == {
        "id": order_list_domain_model.id,
        "name": order_list_domain_model.name,
        "type": order_list_domain_model.type,
        "order_amount": order_list_domain_model.order_amount,
        "created_at": order_list_domain_model.created_at,
        "updated_at": order_list_domain_model.updated_at
    }


def test_map_order_list_domain_to_batch_get_response_dto() -> None:
    # Arrange
    domain_model_a = get_order_list_domain_model(id=1, name="A")
    domain_model_a.created_at = datetime.now()
    domain_model_a.updated_at = datetime.now()

    domain_model_b = get_order_list_domain_model(id=2, name="B")
    domain_model_b.created_at = datetime.now()
    domain_model_b.updated_at = datetime.now()

    total_pages = 10
    size = 20
    page = 5

    # Act
    dto = map_order_list_domain_to_batch_get_response_dto(
        total_pages=total_pages,
        size=size,
        page=page,
        domain_models=[domain_model_a, domain_model_b]
    )

    # Assert
    assert dto.model_dump(mode='json') == {
        "total": total_pages,
        "page": page,
        "size": size,
        "order_lists": [
            domain_model_a.model_dump(mode='json', exclude={"orders"}),
            domain_model_b.model_dump(mode='json', exclude={"orders"})
        ]
    }


def test_map_order_list_single_create_request_dto_to_domain(
        order_list_single_create_request_dto: OrderListSingleCreateRequestDTO) -> None:
    # Act
    domain_model = map_order_list_single_create_request_dto_to_domain(order_list_single_create_request_dto)

    # Assert
    assert domain_model.model_dump() == {
        "id": None,
        "name": order_list_single_create_request_dto.name,
        "type": order_list_single_create_request_dto.type,
        "orders": [order.model_dump() for order in order_list_single_create_request_dto.orders],
        "created_at": None,
        "updated_at": None,
        "order_amount": len(order_list_single_create_request_dto.orders),
    }
