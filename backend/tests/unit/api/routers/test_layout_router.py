from datetime import datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from core.exceptions import EntityNotFoundError
from main import app

client = TestClient(app)


def _setup_mock_layout_response(mock_service_call: object, errors: object = None, is_dry_run: object = False) -> None:
    """Sets up a fully Pydantic-compliant mock response for single layout endpoints."""
    mock_result = MagicMock()
    mock_result.id = 1
    mock_result.name = "Standard Square Layout"
    mock_result.type = "square"
    mock_result.tile_amount = 2
    mock_result.interface_amount = 1
    mock_result.dispenser_amount = 1
    mock_result.ingredient_list_id = 1

    # Mocking tiles
    mock_tile_1 = MagicMock()
    mock_tile_1.type = "interface"
    mock_tile_1.x = 0
    mock_tile_1.y = 0
    mock_tile_1.dispensed_types = None

    mock_tile_2 = MagicMock()
    mock_tile_2.type = "dispenser"
    mock_tile_2.x = 1
    mock_tile_2.y = 0
    mock_tile_2.dispensed_types = ["Aspirin"]

    mock_result.tiles = [mock_tile_1, mock_tile_2]

    # Mocking Ingredient List
    mock_ing_list = MagicMock()
    mock_ing_list.name = "Medicine Base"
    mock_ing_list.type = "medicine"
    mock_ing_list.ingredients = []
    mock_result.ingredient_list = mock_ing_list

    mock_result.created_at = datetime.now()
    mock_result.updated_at = datetime.now()

    # Validation fields
    mock_result.errors = errors if errors is not None else []
    mock_result.is_dry_run = is_dry_run

    mock_service_call.return_value = mock_result


def _setup_mock_layout_batch_response(mock_service_call: object) -> None:
    """Sets up a fully Pydantic-compliant mock response for paginated layouts."""
    mock_result = MagicMock()
    mock_result.total = 1
    mock_result.page = 1
    mock_result.size = 20

    mock_summary = MagicMock()
    mock_summary.id = 1
    mock_summary.name = "Standard Square Layout"
    mock_summary.type = "square"
    mock_summary.ingredient_list_type = "medicine"
    mock_summary.tile_amount = 2
    mock_summary.interface_amount = 1
    mock_summary.dispenser_amount = 1
    mock_summary.created_at = datetime.now()
    mock_summary.updated_at = datetime.now()

    mock_result.layouts = [mock_summary]
    mock_service_call.return_value = mock_result


def test_create_layout_returns_201_on_success(
        mock_layout_service: MagicMock,
        valid_layout_payload: dict
) -> None:
    # Arrange
    _setup_mock_layout_response(mock_layout_service.create, errors=None, is_dry_run=False)

    # Act
    response = client.post("/api/v1/layouts/", json=valid_layout_payload)

    # Assert
    assert response.status_code == 201
    mock_layout_service.create.assert_called_once()
    assert response.json()["name"] == "Standard Square Layout"


def test_create_layout_returns_200_on_dry_run(
        mock_layout_service: MagicMock,
        valid_layout_payload: dict
) -> None:
    # Arrange
    _setup_mock_layout_response(mock_layout_service.create, errors=None, is_dry_run=True)

    # Act
    response = client.post("/api/v1/layouts/?dry_run=true", json=valid_layout_payload)

    # Assert
    assert response.status_code == 200
    mock_layout_service.create.assert_called_once()


def test_create_layout_returns_422_on_errors(
        mock_layout_service: MagicMock,
        valid_layout_payload: dict
) -> None:
    # Arrange
    _setup_mock_layout_response(mock_layout_service.create, errors=["Invalid layout boundaries."])

    # Act
    response = client.post("/api/v1/layouts/", json=valid_layout_payload)

    # Assert
    assert response.status_code == 422
    assert "Invalid layout boundaries." in response.json()["errors"]


def test_get_layouts_returns_200(mock_layout_service: MagicMock) -> None:
    # Arrange
    _setup_mock_layout_batch_response(mock_layout_service.get_all)

    # Act
    response = client.get("/api/v1/layouts/?page=1&size=20")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["layouts"]) == 1
    mock_layout_service.get_all.assert_called_once()


def test_get_layout_returns_200_when_found(mock_layout_service: MagicMock) -> None:
    # Arrange
    _setup_mock_layout_response(mock_layout_service.get_by_id)

    # Act
    response = client.get("/api/v1/layouts/1")

    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == "Standard Square Layout"
    mock_layout_service.get_by_id.assert_called_once_with(1)


def test_get_layout_returns_404_when_not_found(mock_layout_service: MagicMock) -> None:
    # Arrange
    mock_layout_service.get_by_id.side_effect = EntityNotFoundError(
        entity_name="Layout",
        entity_id=999
    )

    # Act
    response = client.get("/api/v1/layouts/999")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Layout with ID 999 not found."


def test_update_layout_returns_200(mock_layout_service: MagicMock) -> None:
    # Arrange
    _setup_mock_layout_response(mock_layout_service.update_by_id)
    payload = {"name": "Updated Layout Name"}

    # Act
    response = client.patch("/api/v1/layouts/1", json=payload)

    # Assert
    assert response.status_code == 200
    mock_layout_service.update_by_id.assert_called_once()


def test_update_layout_returns_404_when_not_found(mock_layout_service: MagicMock) -> None:
    # Arrange
    mock_layout_service.update_by_id.side_effect = EntityNotFoundError(
        entity_name="Layout",
        entity_id=999
    )
    payload = {"name": "Updated Layout Name"}

    # Act
    response = client.patch("/api/v1/layouts/999", json=payload)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Layout with ID 999 not found."


def test_delete_layout_returns_204_when_deleted(mock_layout_service: MagicMock) -> None:
    # Arrange
    mock_layout_service.delete.return_value = True

    # Act
    response = client.delete("/api/v1/layouts/1")

    # Assert
    assert response.status_code == 204
    mock_layout_service.delete.assert_called_once_with(1)


def test_delete_layout_returns_404_when_not_found(mock_layout_service: MagicMock) -> None:
    # Arrange
    mock_layout_service.delete.side_effect = EntityNotFoundError(
        entity_name="Layout",
        entity_id=1
    )

    # Act
    response = client.delete("/api/v1/layouts/1")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Layout with ID 1 not found."
