from typing import List

import pandas as pd

from domain.enums import TileType
from domain.models.common.tile import Tile
from domain.models.experiment import ExperimentDomainModel
from domain.models.layout import LayoutDomainModel
from domain.models.order_list import Order, OrderItem
from solvers.common.mapper import get_coordinate_dictionary
from solvers.common.models import Schedule
from solvers.hexaly.models import HexalyExperimentModel, HexalyTask, HexalyOrder, HexalyTile


def get_duration(quantity: int, dispensing_time: int):
    """Returns task duration based on quantity and dispensing time.

    Args:
        quantity: Amount of units that should be dispensed.
        dispensing_time: Time needed to dispense one unit.

    Returns:
        Duration of the task
    """
    return quantity * dispensing_time


def map_tasks(tasks: List[OrderItem], task_id: int, dispensing_time: int, interface_load_time: int,
              interface_unload_time: int) -> List[HexalyTask]:
    """Maps tasks from domain model to hexaly model. Adds interface related tasks

    Args:
        tasks: Tasks that should be mapped.
        task_id: The lowest ID that should be used for mapped task.
        dispensing_time: Time needed to dispense one unit.
        interface_load_time: Timer required to load empty capsules on mover at the interface tile.
        interface_unload_time: Timer required to unload filled capsules from mover at the interface tile.

    Returns:
        Hexaly tasks obtained from domain models.
    """
    hexaly_tasks: List[HexalyTask] = [HexalyTask(
        task_id=task_id,
        tile_type=TileType.INTERFACE.value,
        duration=interface_load_time)]
    task_id += 1
    for task in tasks:
        hexaly_tasks.append(
            HexalyTask(
                task_id=task_id,
                tile_type=task.name,
                duration=get_duration(quantity=int(task.quantity), dispensing_time=dispensing_time)))
        task_id += 1
    hexaly_tasks.append(
        HexalyTask(
            task_id=task_id,
            tile_type=TileType.INTERFACE.value,
            duration=interface_unload_time))
    return hexaly_tasks


def map_orders(orders: List[Order], dispensing_time: int, interface_load_time: int, interface_unload_time: int) -> List[
    HexalyOrder]:
    """Maps orders from domain model to hexaly model.

    Args:
        orders: Orders that should be mapped.
        dispensing_time: Time needed to dispense one unit.
        interface_load_time: Timer required to load empty capsules on mover at the interface tile.
        interface_unload_time: Timer required to unload filled capsules from mover at the interface tile.

    Returns:
        Hexaly orders obtained from domain models.
    """
    task_id = 0
    order_id = 0
    hexaly_orders: List[HexalyOrder] = []
    for order in orders:
        hexaly_tasks = map_tasks(
            tasks=order.items,
            task_id=task_id,
            dispensing_time=dispensing_time,
            interface_load_time=interface_load_time,
            interface_unload_time=interface_unload_time)
        hexaly_orders.append(HexalyOrder(order_id=order_id, tasks=hexaly_tasks))
        task_id += len(hexaly_tasks)
        order_id += 1
    return hexaly_orders


def get_task_list(orders: List[HexalyOrder]) -> List[HexalyTask]:
    """Returns list with all tasks.

    Args:
        orders: Orders containing all tasks.

    Returns:
        List with tasks from all orders.
    """
    return [task for order in orders for task in order.tasks]


def get_setup_times(tiles: List[HexalyTile]) -> list[list[int]]:
    """Returns 2D matrix of travel times between tiles: setup_times[tile_id_1][tile_id_2].

    Args:
        tiles: Tiles from the layout.

    Returns:
        2D matrix of travel times between tiles: setup_times[tile_id_1][tile_id_2].
    """
    return [[abs(t1.x - t2.x) + abs(t1.y - t2.y) for t1 in tiles] for t2 in tiles]


def get_available_tiles(tasks: List[HexalyTask], tiles: List[HexalyTile]) -> list[list[int]]:
    """Returns 2D matrix of compatibility: available_tiles[task_id][tile_id] (0 or 1).

    Args:
        tasks: Tasks for which compatible tiles should be found.
        tiles: Tiles from the layout.

    Returns:
        2D matrix of compatibility: available_tiles[task_id][tile_id] (0 or 1).
    """
    incompatible = 0
    compatible = 1
    available_tiles = []
    for task in tasks:
        available_tiles.append([])
        for tile in tiles:
            if task.tile_type == tile.type.value or (
                    tile.dispensed_types is not None and task.tile_type in tile.dispensed_types):
                available_tiles[task.task_id].append(compatible)
            else:
                available_tiles[task.task_id].append(incompatible)
    return available_tiles


def map_tiles(tiles: List[Tile]):
    """Maps tiles from domain model to hexaly model.

    Args:
        tiles: Tiles that should be mapped.

    Returns:
        Hexaly tiles obtained from domain models.
    """
    hexaly_tiles: List[HexalyTile] = []
    tile_id = 0
    for tile in tiles:
        hexaly_tiles.append(HexalyTile(
            id=tile_id,
            type=tile.type,
            dispensed_types=tile.dispensed_types,
            x=tile.x,
            y=tile.y
        ))
        tile_id += 1
    return hexaly_tiles


def map_experiment_to_hexaly_experiment(experiment_data: ExperimentDomainModel) -> HexalyExperimentModel:
    """Maps experiment from domain model to hexaly model.

        Args:
            experiment_data: Domain model for experiment.

        Returns:
            Hexaly experiment model obtained from domain model.
        """
    orders = map_orders(
        orders=experiment_data.order_list.orders,
        dispensing_time=experiment_data.configuration.dispensing_time,
        interface_load_time=experiment_data.configuration.interface_time,
        interface_unload_time=experiment_data.configuration.interface_time)
    tiles = map_tiles(tiles=experiment_data.layout.tiles)
    tasks = get_task_list(orders=orders)
    return HexalyExperimentModel(
        orders=orders,
        tasks=tasks,
        mover_amount=experiment_data.configuration.mover_amount,
        interface_load_time=experiment_data.configuration.interface_time,
        interface_unload_time=experiment_data.configuration.interface_time,
        tiles=tiles,
        setup_times=get_setup_times(tiles=tiles),
        available_tiles=get_available_tiles(tasks, tiles=tiles),
        time_limit=experiment_data.configuration.time_limit,
        nb_threads=experiment_data.configuration.process_amount
    )


def map_schedule_domain_to_dataframe(
        schedule: Schedule,
        layout: LayoutDomainModel
) -> pd.DataFrame:
    """Maps schedule to Dataframe required as starting point for simulation creation.

    Args:
        schedule: Initial schedule generated by solver.
        layout: Experiment layout.

    Returns:
        Dataframe required as starting point for simulation creation.
    """
    coord_dict = get_coordinate_dictionary(layout)
    data = []
    for task in schedule.tasks:
        if task.tile.type == TileType.INTERFACE:
            medicine = 'interface'
        else:
            medicine = task.needed_dispensed_type

        coords = (task.tile.x, task.tile.y)
        dispenser_id = coord_dict[medicine].index(coords)
        data.append({
            "Task": f"Job {task.order_id + 1}",
            "Medicine": medicine,
            "Tile": f"tile{task.tile.x}x{task.tile.y}",
            "Patient": task.order_id,
            "Length": task.duration,
            "Start": task.start,
            "Mover": f"mover{task.mover_id}",
            "Finish": task.end,
            "Dispenser": dispenser_id
        })
    return pd.DataFrame(data)
