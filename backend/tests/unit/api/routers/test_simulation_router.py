from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_get_simulations_returns_200(mock_experiment_service: MagicMock) -> None:
    # Arrange
    mock_experiment_service.get_simulations.return_value = {
        "total": 1,
        "page": 1,
        "size": 20,
        "items": []
    }

    # Act
    response = client.get("/api/v1/simulations/?page=1&size=20")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 1
    mock_experiment_service.get_simulations.assert_called_once_with(page=1, size=20)


def test_get_simulation_returns_200_when_found(mock_experiment_service: MagicMock) -> None:
    # Arrange
    mock_experiment_service.get_simulation_by_id.return_value = {
        "tile_type_dict": {"Aspirin": [[0, 0]]},
        "dispenser_dict": {"0_0": "Aspirin"},
        "order_color_dict": {"Order 1": "#FFFFFF"},
        "gantts": {"max_path": 10, "names": ["machines"], "api_plot_url": "url"},
        "mover_paths": {"m": 5, "n": 5, "filled": False, "paths": []}
    }

    # Act
    response = client.get("/api/v1/simulations/1")

    # Assert
    assert response.status_code == 200
    mock_experiment_service.get_simulation_by_id.assert_called_once_with(1)


def test_get_simulation_returns_404_when_not_found(mock_experiment_service: MagicMock) -> None:
    # Arrange
    mock_experiment_service.get_simulation_by_id.return_value = None

    # Act
    response = client.get("/api/v1/simulations/999")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Simulation not found"


@patch("api.routers.simulation_router.os.path.isfile")
def test_get_simulation_plot_returns_404_if_file_missing(mock_isfile: MagicMock) -> None:
    # Arrange
    mock_isfile.return_value = False

    # Act
    response = client.get("/api/v1/simulations/1/plots/missing_plot")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Plot file 'missing_plot' not found for simulation 1"


@patch("api.routers.simulation_router.settings")
def test_get_simulation_plot_returns_file(mock_settings: MagicMock, tmp_path) -> None:
    # Arrange
    sim_dir = tmp_path / "1"
    sim_dir.mkdir()
    fake_file = sim_dir / "machines.html"
    fake_file.write_text("<html>fake gantt</html>", encoding="utf-8")
    mock_settings.GRAPH_FOLDER_PATH = str(tmp_path)

    # Act
    response = client.get("/api/v1/simulations/1/plots/machines")

    # Assert
    assert response.status_code == 200
    assert response.text == "<html>fake gantt</html>"
    assert "text/html" in response.headers["content-type"]
