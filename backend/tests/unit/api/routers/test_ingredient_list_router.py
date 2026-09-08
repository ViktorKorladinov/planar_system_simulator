from datetime import datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from core.exceptions import EntityNotFoundError
from main import app

client = TestClient(app)


def _setup_mock_ingredient_list_response(mock_service_call: object, errors: object = None,
                                         is_dry_run: object = False) -> None:
    """Sets up a fully Pydantic-compliant mock response for single ingredient list endpoints."""
    mock_result = MagicMock()
    mock_result.id = 1
    mock_result.name = "Classic Perfume Base"
    mock_result.type = "perfume"
    mock_result.ingredient_amount = 2

    # Mocking ingredients
    mock_ingredient_1 = MagicMock()
    mock_ingredient_1.name = "Ethanol"
    mock_ingredient_1.note_type = "primary_solvent"
    mock_ingredient_1.viscosity = 1.2
    mock_ingredient_1.volatility_rank = 5

    mock_ingredient_2 = MagicMock()
    mock_ingredient_2.name = "Rose Oil"
    mock_ingredient_2.note_type = "heart_note"
    mock_ingredient_2.viscosity = 4.5
    mock_ingredient_2.volatility_rank = 3

    mock_result.ingredients = [mock_ingredient_1, mock_ingredient_2]

    mock_result.created_at = datetime.now()
    mock_result.updated_at = datetime.now()

    # Validation fields
    mock_result.errors = errors if errors is not None else []
    mock_result.is_dry_run = is_dry_run

    mock_service_call.return_value = mock_result


def _setup_mock_ingredient_list_batch_response(mock_service_call: object) -> None:
    """Sets up a fully Pydantic-compliant mock response for paginated ingredient lists."""
    mock_result = MagicMock()
    mock_result.total = 1
    mock_result.page = 1
    mock_result.size = 20

    mock_short_list = MagicMock()
    mock_short_list.id = 1
    mock_short_list.name = "Classic Perfume Base"
    mock_short_list.type = "perfume"
    mock_short_list.ingredient_amount = 2
    mock_short_list.created_at = datetime.now()
    mock_short_list.updated_at = datetime.now()

    mock_result.ingredient_lists = [mock_short_list]
    mock_service_call.return_value = mock_result


def test_create_ingredient_list_returns_201_on_success(
        mock_ingredient_list_service: MagicMock,
        valid_ingredient_list_payload: dict
) -> None:
    # Arrange
    _setup_mock_ingredient_list_response(mock_ingredient_list_service.create, errors=None, is_dry_run=False)

    # Act
    response = client.post("/api/v1/ingredient_lists/", json=valid_ingredient_list_payload)

    # Assert
    assert response.status_code == 201
    mock_ingredient_list_service.create.assert_called_once()
    assert response.json()["name"] == "Classic Perfume Base"


def test_create_ingredient_list_returns_200_on_dry_run(
        mock_ingredient_list_service: MagicMock,
        valid_ingredient_list_payload: dict
) -> None:
    # Arrange
    _setup_mock_ingredient_list_response(mock_ingredient_list_service.create, errors=None, is_dry_run=True)

    # Act
    response = client.post("/api/v1/ingredient_lists/?dry_run=true", json=valid_ingredient_list_payload)

    # Assert
    assert response.status_code == 200
    mock_ingredient_list_service.create.assert_called_once()


def test_create_ingredient_list_returns_422_on_errors(
        mock_ingredient_list_service: MagicMock,
        valid_ingredient_list_payload: dict
) -> None:
    # Arrange
    _setup_mock_ingredient_list_response(mock_ingredient_list_service.create,
                                         errors=["Duplicate ingredient names found."])

    # Act
    response = client.post("/api/v1/ingredient_lists/", json=valid_ingredient_list_payload)

    # Assert
    assert response.status_code == 422
    assert "Duplicate ingredient names found." in response.json()["errors"]


def test_get_ingredient_lists_returns_200(mock_ingredient_list_service: MagicMock) -> None:
    # Arrange
    _setup_mock_ingredient_list_batch_response(mock_ingredient_list_service.get_all)

    # Act
    response = client.get("/api/v1/ingredient_lists/?page=1&size=20")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["ingredient_lists"]) == 1
    mock_ingredient_list_service.get_all.assert_called_once()


def test_get_ingredient_list_returns_200_when_found(mock_ingredient_list_service: MagicMock) -> None:
    # Arrange
    _setup_mock_ingredient_list_response(mock_ingredient_list_service.get_by_id)

    # Act
    response = client.get("/api/v1/ingredient_lists/1")

    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == "Classic Perfume Base"
    mock_ingredient_list_service.get_by_id.assert_called_once_with(1)


def test_get_ingredient_list_returns_404_when_not_found(mock_ingredient_list_service: MagicMock) -> None:
    # Arrange
    mock_ingredient_list_service.get_by_id.side_effect = EntityNotFoundError(
        entity_name="Ingredient List",
        entity_id=999
    )

    # Act
    response = client.get("/api/v1/ingredient_lists/999")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Ingredient List with ID 999 not found."


def test_update_ingredient_list_returns_200(mock_ingredient_list_service: MagicMock) -> None:
    # Arrange
    _setup_mock_ingredient_list_response(mock_ingredient_list_service.update_by_id)
    payload = {"name": "Updated Perfume Base"}

    # Act
    response = client.patch("/api/v1/ingredient_lists/1", json=payload)

    # Assert
    assert response.status_code == 200
    mock_ingredient_list_service.update_by_id.assert_called_once()


def test_update_ingredient_list_returns_404_when_not_found(mock_ingredient_list_service: MagicMock) -> None:
    # Arrange
    mock_ingredient_list_service.update_by_id.side_effect = EntityNotFoundError(
        entity_name="Ingredient List",
        entity_id=999
    )
    payload = {"name": "Updated Perfume Base"}

    # Act
    response = client.patch("/api/v1/ingredient_lists/999", json=payload)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Ingredient List with ID 999 not found."


def test_delete_ingredient_list_returns_204_when_deleted(mock_ingredient_list_service: MagicMock) -> None:
    # Arrange
    mock_ingredient_list_service.delete.return_value = True

    # Act
    response = client.delete("/api/v1/ingredient_lists/1")

    # Assert
    assert response.status_code == 204
    mock_ingredient_list_service.delete.assert_called_once_with(1)


def test_delete_ingredient_list_returns_404_when_not_found(mock_ingredient_list_service: MagicMock) -> None:
    # Arrange
    mock_ingredient_list_service.delete.side_effect = EntityNotFoundError(
        entity_name="Ingredient List",
        entity_id=1
    )

    # Act
    response = client.delete("/api/v1/ingredient_lists/1")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Ingredient List with ID 1 not found."
