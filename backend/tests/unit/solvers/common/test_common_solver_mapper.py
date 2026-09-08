from datetime import datetime

from domain.enums import LayoutType, TileType
from domain.models.common.tile import Tile
from domain.models.experiment import ExperimentDomainModel
from domain.models.layout import LayoutDomainModel
from solvers.common.mapper import (
    get_unavailable_coordinates,
    get_coordinate_dictionary,
    map_experiment_domain_to_simulation_data
)
from solvers.common.models import SimulationData
from tests.factories.ingredient_list_factory import get_ingredient_list_domain_model


def test_get_unavailable_coordinates(layout_domain_model: LayoutDomainModel) -> None:
    # Arrange
    tiles = [
        Tile(type=TileType.INTERFACE, x=0, y=0),
        Tile(type=TileType.BLOCKED, x=0, y=1),
        Tile(type=TileType.EMPTY, x=1, y=0),
        Tile(type=TileType.EMPTY, x=1, y=1),
        Tile(type=TileType.DISPENSER, dispensed_types=["Lisinopril", "Aspirin"], x=2, y=0),
        Tile(type=TileType.BLOCKED, x=2, y=1),
        Tile(type=TileType.CAPPER, x=3, y=0),
        Tile(type=TileType.MIXER, x=3, y=1),
    ]
    layout = LayoutDomainModel(
        id=1,
        name="Layout",
        type=LayoutType.CUSTOM,
        tiles=tiles,
        tile_amount=len(tiles),
        interface_amount=sum(1 for tile in tiles if tile.type == TileType.INTERFACE),
        dispenser_amount=sum(1 for tile in tiles if tile.type == TileType.DISPENSER),
        filled=False,
        ingredient_list=get_ingredient_list_domain_model(),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # Act
    result = get_unavailable_coordinates(layout=layout)

    # Assert
    assert result == [[0, 1], [2, 1]]


def test_get_coordinate_dictionary(layout_domain_model: LayoutDomainModel) -> None:
    # Arrange
    layout_domain_model.tiles = [
        Tile(type=TileType.INTERFACE, x=0, y=0),
        Tile(type=TileType.BLOCKED, x=1, y=0),
        Tile(type=TileType.EMPTY, x=2, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["Aspirin", "Lisinopril"], x=0, y=1),
        Tile(type=TileType.CAPPER, x=1, y=1),
        Tile(type=TileType.MIXER, x=2, y=1),
        Tile(type=TileType.INTERFACE, x=3, y=1)
    ]

    # Act
    result = get_coordinate_dictionary(layout=layout_domain_model)

    # Assert
    print(result)
    assert result == {
        "interface": [(0, 0), (3, 1)],
        "Aspirin": [(0, 1)],
        "Lisinopril": [(0, 1)],
        "capper": [(1, 1)],
        "mixer": [(2, 1)]
    }


def test_map_experiment_domain_to_simulation_data_custom_layout(experiment_domain_model: ExperimentDomainModel) -> None:
    # Arrange
    experiment_domain_model.layout.tiles = [
        Tile(type=TileType.INTERFACE, x=0, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["Aspirin", "Lisinopril"], x=1, y=0),
        Tile(type=TileType.EMPTY, x=0, y=1),
        Tile(type=TileType.BLOCKED, x=1, y=1),
        Tile(type=TileType.MIXER, x=0, y=1),
        Tile(type=TileType.CAPPER, x=1, y=1)
    ]
    experiment_domain_model.configuration.mover_amount = 5

    # Act
    result = map_experiment_domain_to_simulation_data(domain_model=experiment_domain_model)

    # Assert
    assert isinstance(result, SimulationData)
    print(result)
    assert result.model_dump(mode='json') == {
        "row_amount": 2,
        "column_amount": 2,
        "filled": True,
        "unavailable_coordinates": [[1, 1]],
        "coordinate_dict": {
            "interface": [[0, 0]],
            "Aspirin": [[1, 0]],
            "Lisinopril": [[1, 0]],
            'mixer': [[0, 1]],
            'capper': [[1, 1]]
        },
        "mover_amount": 5
    }


def test_map_experiment_domain_to_simulation_data(experiment_domain_model: ExperimentDomainModel) -> None:
    # Arrange
    experiment_domain_model.layout.tiles = [
        Tile(type=TileType.INTERFACE, x=0, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["Aspirin"], x=0, y=1),
        Tile(type=TileType.MIXER, x=1, y=0),
        Tile(type=TileType.CAPPER, x=1, y=1)
    ]
    experiment_domain_model.configuration.mover_amount = 3

    # Act
    result = map_experiment_domain_to_simulation_data(domain_model=experiment_domain_model)

    # Assert
    print(result)
    assert result.row_amount == 2
    assert result.column_amount == 2
    assert result.filled is True
    assert result.mover_amount == 3
