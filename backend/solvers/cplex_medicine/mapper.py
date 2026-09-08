import re
from typing import List, Dict

import pandas as pd

from domain.enums import TileType
from domain.models.common.tile import Tile
from domain.models.experiment import ExperimentDomainModel, Result
from domain.models.layout import LayoutDomainModel
from domain.models.order_list import Order
from solvers.common.models import Task, Schedule
from solvers.cplex_medicine.models import CplexExperimentModel, CplexOrder, CplexLayout, CplexResult


def map_placement_to_packer_result(placement: List[List[str]]) -> Dict[str, List[str]]:
    """Turns placement into dictionary with numbers as keys and medicine as values.

    Args:
        placement: Placement of tiles in the layout.

    Returns:
        Dictionary with numbers as keys and medicine as values.
    """
    packer_result = {}
    pack_id = 0
    ignored_cells = ['empty', 'blocked', 'interface']

    for row in placement:
        for cell in row:
            if cell not in ignored_cells:
                drugs_in_pack = cell.split(",")
                packer_result[str(pack_id)] = drugs_in_pack
                pack_id += 1

    return packer_result


def map_order_domain_to_cplex(domain_model: Order, order_id: int) -> CplexOrder:
    """Maps order domain models to cplex_medicine model.

    Args:
        domain_model: Order domain model.
        order_id: ID of the current order.

    Returns:
        Cplex order model.
    """
    drug_names = []
    dosages = []
    for item in domain_model.items:
        drug_names.append(item.name)
        dosages.append(int(item.quantity))
    return CplexOrder(
        order_id=order_id,
        drug_names=drug_names,
        dosages=dosages
    )


def map_orders_domain_to_cplex(domain_models: List[Order]) -> List[CplexOrder]:
    """Maps orders domain models to cplex_medicine model.

    Args:
        domain_models: Order domain models.

    Returns:
        Cplex order models.
    """
    result = []
    for order_id in range(len(domain_models)):
        result.append(map_order_domain_to_cplex(domain_models[order_id], order_id))
    return result


def map_tiles_to_placement(tiles: List[Tile]) -> List[List[str]]:
    """Maps tile domain models to placement.

    Args:
        tiles: Tile domain models.

    Returns:
        Placement of tiles.
    """
    max_x = max(tile.x for tile in tiles)
    max_y = max(tile.y for tile in tiles)
    placement = []

    for y in range(max_y + 1):
        placement.append([])
        for x in range(max_x + 1):
            placement[-1].append('empty')

    for tile in tiles:
        if tile.type == TileType.INTERFACE:
            placement[tile.y][tile.x] = 'interface'
        elif tile.type == TileType.BLOCKED:
            placement[tile.y][tile.x] = 'blocked'
        elif tile.type == TileType.EMPTY:
            placement[tile.y][tile.x] = 'empty'
        elif tile.dispensed_types is not None and len(tile.dispensed_types) > 1:
            dispensed_types = ",".join(sorted(tile.dispensed_types))
            placement[tile.y][tile.x] = dispensed_types
        elif tile.dispensed_types is not None and len(tile.dispensed_types) == 1:
            placement[tile.y][tile.x] = tile.dispensed_types[0]
        else:
            placement[tile.y][tile.x] = 'empty'

    return placement


def map_layout_domain_to_cplex(domain_model: LayoutDomainModel) -> CplexLayout:
    """Maps layout domain models to cplex_medicine model.

    Args:
        domain_model: Layout domain model.

    Returns:
        Cplex layout model.
    """
    interface_amount = sum(1 for tile in domain_model.tiles if tile.type == TileType.INTERFACE)
    placement = map_tiles_to_placement(domain_model.tiles)
    return CplexLayout(
        type=domain_model.type,
        row_amount=max(tile.y for tile in domain_model.tiles) + 1,
        column_amount=max(tile.x for tile in domain_model.tiles) + 1,
        placement=placement,
        tile_amount=domain_model.dispenser_amount,
        interface_amount=interface_amount,
        packer_result=map_placement_to_packer_result(placement)
    )


def map_experiment_to_cplex_experiment(domain_model: ExperimentDomainModel) -> CplexExperimentModel:
    """Maps experiment domain model to cplex_medicine model.

    Args:
        domain_model: Experiment domain model.

    Returns:
        Cplex experiment model.
    """
    return CplexExperimentModel(
        orders=map_orders_domain_to_cplex(domain_model.order_list.orders),
        mover_amount=domain_model.configuration.mover_amount,
        time_limit=domain_model.configuration.time_limit,
        dispensing_time=domain_model.configuration.dispensing_time,
        batch_size=domain_model.configuration.batch_size,
        process_amount=domain_model.configuration.process_amount,
        warmup=domain_model.configuration.warmup,
        interface_time=domain_model.configuration.interface_time,
        layout=map_layout_domain_to_cplex(domain_model.layout)
    )


def map_cplex_tile_to_domain(cplex_type: str, x: int, y: int) -> Tile:
    """Maps cplex_medicine tile to domain model.

    Args:
        cplex_type: The type of the cplex_medicine tile.
        x: The x coordinate of the cplex_medicine tile.
        y: The y coordinate of the cplex_medicine tile.

    Returns:
        Tile domain model.
    """
    if cplex_type == 'interface':
        return Tile(
            type=TileType.INTERFACE,
            x=x,
            y=y
        )
    return Tile(
        type=TileType.DISPENSER,
        dispensed_types=[cplex_type],
        x=x,
        y=y
    )


def map_schedule_row_to_task(schedule_row: pd.DataFrame, task_id: int) -> Task:
    """Maps schedule row from dataframe to task.

    Args:
        schedule_row: Row with task data from dataframe.
        task_id: Task id.

    Returns:
        Task domain model.
    """

    mover = schedule_row["Mover"]
    id_match = re.search(r"(\d+)", mover)
    mover_id = -1

    if id_match:
        mover_id = id_match.group()
    return Task(
        task_id=task_id,
        order_id=schedule_row['Patient'],
        duration=schedule_row['Length'],
        start=schedule_row['Start'],
        end=schedule_row['Finish'],
        tile=map_cplex_tile_to_domain(schedule_row['Medicine'], schedule_row['Position'][0],
                                      schedule_row['Position'][1]),
        mover_id=mover_id,
        ticks_added=schedule_row['TicksAdded']
    )


def map_finished_schedule_to_schedule(finished_schedule: pd.DataFrame) -> Schedule:
    """Maps finished schedule from dataframe to domain model.

    Args:
        finished_schedule: Finished schedule in dataframe.

    Returns:
        Schedule domain model.
    """

    tasks = []
    for task_id in range(len(finished_schedule)):
        row = finished_schedule.iloc[task_id]
        tasks.append(map_schedule_row_to_task(row, task_id))
    return Schedule(tasks=tasks)


def map_cplex_result_to_result(cplex_result: CplexResult) -> Result:
    """Maps cplex_medicine result to domain model.

    Args:
        cplex_result: Cplex result from cplex_medicine.

    Returns:
        Result domain model.
    """
    return Result(
        mover_paths=cplex_result.mover_paths,
        max_path=cplex_result.max_path,
        color_dict=cplex_result.color_dict,
        schedule=map_finished_schedule_to_schedule(cplex_result.finished_schedule)
    )
