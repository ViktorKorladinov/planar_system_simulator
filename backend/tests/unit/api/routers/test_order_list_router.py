from datetime import datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from core.exceptions import EntityNotFoundError
from main import app

client = TestClient(app)


def _setup_mock_order_list_response(mock_service_call: object, errors: object = None,
                                    is_dry_run: object = False) -> None:
    """Sets up a fully Pydantic-compliant mock response for single order list endpoints."""
    mock_result = MagicMock()
    mock_result.id = 1
    mock_result.name = "Standard Medicine Orders"
    mock_result.type = "medicine"
    mock_result.order_amount = 1

    # Mocking order items
    mock_item_1 = MagicMock()
    mock_item_1.name = "Aspirin"
    mock_item_1.quantity = 10.0

    mock_item_2 = MagicMock()
    mock_item_2.name = "Ibuprofen"
    mock_item_2.quantity = 5.0

    # Mocking the order
    mock_order = MagicMock()
    mock_order.items = [mock_item_1, mock_item_2]
    mock_order.t_max = None

    mock_result.orders = [mock_order]

    mock_result.created_at = datetime.now()
    mock_result.updated_at = datetime.now()

    # Validation fields
    mock_result.errors = errors if errors is not None else []
    mock_result.is_dry_run = is_dry_run

    mock_service_call.return_value = mock_result


def _setup_mock_order_list_batch_response(mock_service_call: object) -> None:
    """Sets up a fully Pydantic-compliant mock response for paginated order lists."""
    mock_result = MagicMock()
    mock_result.total = 1
    mock_result.page = 1
    mock_result.size = 20

    mock_short_list = MagicMock()
    mock_short_list.id = 1
    mock_short_list.name = "Standard Medicine Orders"
    mock_short_list.type = "medicine"
    mock_short_list.order_amount = 1
    mock_short_list.created_at = datetime.now()
    mock_short_list.updated_at = datetime.now()

    mock_result.order_lists = [mock_short_list]
    mock_service_call.return_value = mock_result


def test_create_order_list_returns_201_on_success(
        mock_order_list_service: MagicMock,
        valid_order_list_payload: dict
) -> None:
    # Arrange
    _setup_mock_order_list_response(mock_order_list_service.create, errors=None, is_dry_run=False)

    # Act
    response = client.post("/api/v1/order_lists/", json=valid_order_list_payload)

    # Assert
    assert response.status_code == 201
    mock_order_list_service.create.assert_called_once()
    assert response.json()["name"] == "Standard Medicine Orders"


def test_create_order_list_returns_200_on_dry_run(
        mock_order_list_service: MagicMock,
        valid_order_list_payload: dict
) -> None:
    # Arrange
    _setup_mock_order_list_response(mock_order_list_service.create, errors=None, is_dry_run=True)

    # Act
    response = client.post("/api/v1/order_lists/?dry_run=true", json=valid_order_list_payload)

    # Assert
    assert response.status_code == 200
    mock_order_list_service.create.assert_called_once()


def test_create_order_list_returns_422_on_errors(
        mock_order_list_service: MagicMock,
        valid_order_list_payload: dict
) -> None:
    # Arrange
    _setup_mock_order_list_response(mock_order_list_service.create, errors=["Invalid quantities for Medicine type."])

    # Act
    response = client.post("/api/v1/order_lists/", json=valid_order_list_payload)

    # Assert
    assert response.status_code == 422
    assert "Invalid quantities for Medicine type." in response.json()["errors"]


def test_get_order_lists_returns_200(mock_order_list_service: MagicMock) -> None:
    # Arrange
    _setup_mock_order_list_batch_response(mock_order_list_service.get_all)

    # Act
    response = client.get("/api/v1/order_lists/?page=1&size=20")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["order_lists"]) == 1
    mock_order_list_service.get_all.assert_called_once()


def test_get_order_list_returns_200_when_found(mock_order_list_service: MagicMock) -> None:
    # Arrange
    _setup_mock_order_list_response(mock_order_list_service.get_by_id)

    # Act
    response = client.get("/api/v1/order_lists/1")

    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == "Standard Medicine Orders"
    mock_order_list_service.get_by_id.assert_called_once_with(1)


def test_get_order_list_returns_404_when_not_found(mock_order_list_service: MagicMock) -> None:
    # Arrange
    mock_order_list_service.get_by_id.side_effect = EntityNotFoundError(
        entity_name="Order List",
        entity_id=999
    )

    # Act
    response = client.get("/api/v1/order_lists/999")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Order List with ID 999 not found."


def test_update_order_list_returns_200(mock_order_list_service: MagicMock) -> None:
    # Arrange
    _setup_mock_order_list_response(mock_order_list_service.update_by_id)
    payload = {"name": "Updated Medicine Orders"}

    # Act
    response = client.patch("/api/v1/order_lists/1", json=payload)

    # Assert
    assert response.status_code == 200
    mock_order_list_service.update_by_id.assert_called_once()


def test_update_order_list_returns_404_when_not_found(mock_order_list_service: MagicMock) -> None:
    # Arrange
    mock_order_list_service.update_by_id.side_effect = EntityNotFoundError(
        entity_name="Order List",
        entity_id=999
    )
    payload = {"name": "Updated Medicine Orders"}

    # Act
    response = client.patch("/api/v1/order_lists/999", json=payload)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Order List with ID 999 not found."


def test_delete_order_list_returns_204_when_deleted(mock_order_list_service: MagicMock) -> None:
    # Arrange
    mock_order_list_service.delete.return_value = True

    # Act
    response = client.delete("/api/v1/order_lists/1")

    # Assert
    assert response.status_code == 204
    mock_order_list_service.delete.assert_called_once_with(1)


def test_delete_order_list_returns_404_when_not_found(mock_order_list_service: MagicMock) -> None:
    # Arrange
    mock_order_list_service.delete.side_effect = EntityNotFoundError(
        entity_name="Order List",
        entity_id=1
    )

    # Act
    response = client.delete("/api/v1/order_lists/1")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Order List with ID 1 not found."
