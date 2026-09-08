from unittest.mock import patch

import pandas as pd

from domain.enums import TileType
from domain.models.common.tile import Tile
from domain.models.experiment import ExperimentDomainModel
from domain.models.layout import LayoutDomainModel
from domain.models.order_list import OrderListDomainModel, OrderItem
from solvers.common.models import Schedule, Task
from solvers.hexaly.mapper import (
    get_duration, map_tasks, map_orders, get_task_list, get_setup_times,
    get_available_tiles, map_tiles, map_experiment_to_hexaly_experiment,
    map_schedule_domain_to_dataframe
)
from solvers.hexaly.models import HexalyOrder, HexalyTask, HexalyTile
from tests.factories.layout_factory import get_layout_domain_model


def test_get_duration_calculates_correct_time() -> None:
    # Arrange
    quantity = 10
    dispensing_time = 3

    # Act
    result = get_duration(quantity=quantity, dispensing_time=dispensing_time)

    # Assert
    assert result == 30


def test_get_duration_handles_zero_quantity() -> None:
    # Arrange
    quantity = 0
    dispensing_time = 5

    # Act
    result = get_duration(quantity=quantity, dispensing_time=dispensing_time)

    # Assert
    assert result == 0


def test_map_tasks_creates_interface_and_dispenser_tasks() -> None:
    # Arrange
    tasks = [
        OrderItem(name="Ethanol", quantity=5),
        OrderItem(name="Rose Oil", quantity=2)
    ]
    task_id = 10
    dispensing_time = 2
    interface_load_time = 3
    interface_unload_time = 4

    # Act
    result = map_tasks(
        tasks=tasks,
        task_id=task_id,
        dispensing_time=dispensing_time,
        interface_load_time=interface_load_time,
        interface_unload_time=interface_unload_time
    )

    # Assert
    assert len(result) == 4

    # Check Interface Load Task
    assert result[0].model_dump() == {
        "task_id": task_id,
        "tile_type": TileType.INTERFACE.value,
        "duration": interface_load_time
    }
    # Check Dispense Tasks
    assert result[1].model_dump() == {
        "task_id": task_id + 1,
        "tile_type": "Ethanol",
        "duration": 5 * dispensing_time,
    }
    assert result[2].model_dump() == {
        "task_id": task_id + 2,
        "tile_type": "Rose Oil",
        "duration": 2 * dispensing_time,
    }
    # Check Interface Unload Task
    assert result[3].model_dump() == {
        "task_id": task_id + 3,
        "tile_type": TileType.INTERFACE.value,
        "duration": interface_unload_time
    }


def test_map_orders_maintains_correct_task_ids_across_multiple_orders(
        order_list_domain_model: OrderListDomainModel) -> None:
    # Arrange
    orders = order_list_domain_model.orders
    dispensing_time = 2
    interface_load_time = 3
    interface_unload_time = 3

    # Act
    result = map_orders(
        orders=orders,
        dispensing_time=dispensing_time,
        interface_load_time=interface_load_time,
        interface_unload_time=interface_unload_time
    )

    # Assert
    assert len(result) == len(orders)

    # Order 0 has 2 items -> 4 tasks (load + 2 items + unload)
    assert len(result[0].tasks) == 4
    assert result[0].order_id == 0
    assert result[0].tasks[0].task_id == 0
    assert result[0].tasks[-1].task_id == 3

    # Order 1 has 1 item -> 3 tasks
    assert len(result[1].tasks) == 3
    assert result[1].order_id == 1
    assert result[1].tasks[0].task_id == 4
    assert result[1].tasks[-1].task_id == 6

    # Order 2 has 2 items -> 4 tasks
    assert len(result[2].tasks) == 4
    assert result[2].order_id == 2
    assert result[2].tasks[0].task_id == 7
    assert result[2].tasks[-1].task_id == 10


def test_get_task_list_flattens_nested_tasks() -> None:
    # Arrange
    task_1 = HexalyTask(task_id=1, tile_type="interface", duration=3)
    task_2 = HexalyTask(task_id=2, tile_type="Ethanol", duration=5)
    task_3 = HexalyTask(task_id=3, tile_type="interface", duration=3)
    task_4 = HexalyTask(task_id=4, tile_type="interface", duration=3)
    task_5 = HexalyTask(task_id=5, tile_type="Rose Oil", duration=4)
    task_6 = HexalyTask(task_id=6, tile_type="interface", duration=3)

    initial_tasks = [task_1, task_2, task_3, task_4, task_5, task_6]

    orders = [
        HexalyOrder(order_id=1, tasks=[task_1, task_2, task_3]),
        HexalyOrder(order_id=2, tasks=[task_4, task_5, task_6])
    ]

    # Act
    obtained_tasks = get_task_list(orders=orders)

    # Assert
    assert len(obtained_tasks) == len(initial_tasks)
    for i in range(len(obtained_tasks)):
        assert obtained_tasks[i].model_dump() == {
            "task_id": initial_tasks[i].task_id,
            "tile_type": initial_tasks[i].tile_type,
            "duration": initial_tasks[i].duration
        }


def test_get_setup_times_calculates_manhattan_distance() -> None:
    # Arrange
    tiles = [
        HexalyTile(id=0, type=TileType.INTERFACE, dispensed_types=None, x=0, y=0),
        HexalyTile(id=1, type=TileType.DISPENSER, dispensed_types=["Ethanol"], x=1, y=2),
        HexalyTile(id=2, type=TileType.MIXER, dispensed_types=None, x=2, y=2)
    ]

    # Act
    setup_times = get_setup_times(tiles=tiles)

    # Assert
    assert setup_times == [
        [0, 3, 4],  # Distance from (0,0) to (0,0), (1,2), (2,2)
        [3, 0, 1],  # Distance from (1,2) to (0,0), (1,2), (2,2)
        [4, 1, 0],  # Distance from (2,2) to (0,0), (1,2), (2,2)
    ]


def test_get_available_tiles_identifies_compatible_and_incompatible_tiles() -> None:
    # Arrange
    tiles = [
        HexalyTile(id=0, type=TileType.INTERFACE, dispensed_types=None, x=0, y=0),
        HexalyTile(id=1, type=TileType.DISPENSER, dispensed_types=["Ethanol", "Rose Oil"], x=1, y=1),
        HexalyTile(id=2, type=TileType.DISPENSER, dispensed_types=["Water"], x=2, y=1),
        HexalyTile(id=3, type=TileType.MIXER, dispensed_types=None, x=2, y=2)
    ]
    tasks = [
        HexalyTask(task_id=0, tile_type="interface", duration=3),
        HexalyTask(task_id=1, tile_type="Ethanol", duration=5),
        HexalyTask(task_id=2, tile_type="Water", duration=15),
        HexalyTask(task_id=3, tile_type="mixer", duration=10)
    ]

    # Act
    available_tiles = get_available_tiles(tiles=tiles, tasks=tasks)

    # Assert
    assert available_tiles == [
        [1, 0, 0, 0],  # interface matches only tile 0
        [0, 1, 0, 0],  # Ethanol matches only tile 1
        [0, 0, 1, 0],  # Water matches only tile 2
        [0, 0, 0, 1],  # mixer matches only tile 3
    ]


def test_map_tiles_preserves_coordinates_and_assigns_sequential_ids(layout_domain_model: LayoutDomainModel) -> None:
    # Act
    mapped_tiles = map_tiles(tiles=layout_domain_model.tiles)

    # Assert
    assert len(mapped_tiles) == len(layout_domain_model.tiles)
    for i in range(len(mapped_tiles)):
        assert mapped_tiles[i].model_dump() == {
            "id": i,
            "type": layout_domain_model.tiles[i].type,
            "dispensed_types": layout_domain_model.tiles[i].dispensed_types,
            "x": layout_domain_model.tiles[i].x,
            "y": layout_domain_model.tiles[i].y,
        }


def test_map_experiment_to_hexaly_experiment_aggregates_all_data(
        experiment_domain_model: ExperimentDomainModel) -> None:
    # Act
    experiment = map_experiment_to_hexaly_experiment(experiment_data=experiment_domain_model)

    # Assert
    assert experiment.model_dump(exclude={"orders", "tasks", "tiles", "available_tiles", "setup_times"}) == {
        "mover_amount": experiment_domain_model.configuration.mover_amount,
        "interface_load_time": experiment_domain_model.configuration.interface_time,
        "interface_unload_time": experiment_domain_model.configuration.interface_time,
        "time_limit": experiment_domain_model.configuration.time_limit,
        "nb_threads": experiment_domain_model.configuration.process_amount
    }

    assert len(experiment.orders) == len(experiment_domain_model.order_list.orders)
    assert len(experiment.tiles) == len(experiment_domain_model.layout.tiles)
    assert len(experiment.setup_times) == len(experiment.tiles)
    assert len(experiment.available_tiles) == len(experiment.tasks)


@patch("solvers.hexaly.mapper.get_coordinate_dictionary")
def test_map_schedule_domain_to_dataframe_creates_valid_dataframe(mock_get_coord_dict) -> None:
    # Arrange
    layout = get_layout_domain_model()

    task1 = Task(task_id=0, order_id=0, duration=5, start=0, end=5, mover_id=0,
                 tile=Tile(type=TileType.INTERFACE, x=0, y=0), needed_dispensed_type=None, ticks_added=0)
    task2 = Task(task_id=1, order_id=0, duration=10, start=5, end=15, mover_id=0,
                 tile=Tile(type=TileType.DISPENSER, dispensed_types=["Ethanol", "Rose Oil"], x=1, y=1),
                 needed_dispensed_type="Ethanol", ticks_added=0)
    task3 = Task(task_id=2, order_id=0, duration=5, start=15, end=20, mover_id=0,
                 tile=Tile(type=TileType.MIXER, x=2, y=2), needed_dispensed_type="mixer", ticks_added=0)
    schedule = Schedule(tasks=[task1, task2, task3])

    mock_get_coord_dict.return_value = {
        "interface": [(0, 0)],
        "Ethanol": [(1, 1)],
        "mixer": [(2, 2)]
    }

    # Act
    df = map_schedule_domain_to_dataframe(schedule=schedule, layout=layout)

    # Assert
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3

    # Verify Interface Task
    assert df.iloc[0]["Task"] == "Job 1"
    assert df.iloc[0]["Medicine"] == "interface"
    assert df.iloc[0]["Tile"] == "tile0x0"
    assert df.iloc[0]["Dispenser"] == 0  # 0th index in the mock dictionary array

    # Verify Dispenser Task
    assert df.iloc[1]["Task"] == "Job 1"
    assert df.iloc[1]["Medicine"] == "Ethanol"
    assert df.iloc[1]["Tile"] == "tile1x1"
    assert df.iloc[1]["Dispenser"] == 0  # 0th index in the mock dictionary array

    # Verify Mixer Task
    assert df.iloc[2]["Task"] == "Job 1"
    assert df.iloc[2]["Medicine"] == "mixer"
    assert df.iloc[2]["Tile"] == "tile2x2"
    assert df.iloc[2]["Dispenser"] == 0  # 0th index in the mock dictionary array
