from typing import List, Dict, Tuple

import pandas as pd

from domain.enums import MoverMode
from domain.models.experiment import MoverStep
from solvers.common.utilities.convs import mover_str_to_int
from solvers.common.utilities.path_optimizer import PathOptimizer
from solvers.common.utilities.resting_site_optimizer import RestingSiteOptimizer
from solvers.common.utilities.routing_sites import RoutingSites


def split_df_by_movers(df: pd.DataFrame, coordinate_dict: dict, mover_amount: int) -> List[pd.DataFrame]:
    """
    Splits dataframe according to the movers.

    Args:
        df: Dataframe to be split.
        coordinate_dict: Dictionary with coordinates.
        mover_amount: Amount of utilized movers.

    Returns:
        List of dataframes with movers.
    """
    df['Position'] = df.apply(lambda row: coordinate_dict[row['Medicine']][row['Dispenser']], axis=1)
    grp_mover = df.groupby('Mover')
    df_arr = [pd.DataFrame() for _ in range(mover_amount)]
    for mover, group in grp_mover:
        idx = mover_str_to_int(mover)
        if idx < mover_amount:
            df_arr[idx] = group
    return df_arr


def convert_to_mover_steps(coords: List[tuple], order_id: str, mode: MoverMode) -> List[MoverStep]:
    """
    Converts a list of coordinates to a list of MoverStep objects.

    Args:
        coords: List of coordinates in format (x, y, direction).
        order_id: ID of the order.
        mode: Mover mode.

    Returns:
        List of MoverStep objects.
    """
    result = []
    if not coords or not coords[0]:
        return []
    for coord in coords:
        if isinstance(coord, tuple) and len(coord) == 3:
            x, y, direction = coord
            direction_map = {
                'n': (0, -1),
                's': (0, 1),
                'e': (1, 0),
                'w': (-1, 0)
            }
            result.append(MoverStep(
                x=int(x),
                y=int(y),
                mode=MoverMode.WAIT_REST,
                order=order_id,
                rest_offset_x=direction_map[direction][0],
                rest_offset_y=direction_map[direction][1]
            ))
        else:  # Regular position
            result.append(MoverStep(
                x=int(coord[0]),
                y=int(coord[1]),
                mode=mode,
                order=order_id
            ))
    return result


def generate_mover_paths(df_arr: List[pd.DataFrame], path_optimizer: PathOptimizer, resting_sites_sched: dict) -> List[
    List[MoverStep]]:
    """
    Generates mover paths.

    Args:
        df_arr: List with dataframes for movers.
        path_optimizer: PathOptimizer.
        resting_sites_sched: Schedule with resting sites.

    Returns:
        List of mover paths.
    """
    mover_paths = []

    for mover_id, mover_df in enumerate(df_arr):
        mover_path = []


        mover_df = mover_df.sort_values(by=['Start'])
        prev = None

        for task_i, task in mover_df.iterrows():
            order_name = f"Patient {task['Patient']}"
            target_pos = tuple(task['Position'])

            # Skip first task
            if prev is None:
                # Respect initial wait before introduction to the grid
                mover_path.extend(convert_to_mover_steps(
                    [target_pos for _ in range(int(task['Start']))],
                    order_name,
                    MoverMode.LOADING
                ))

                # Prep mover for his first patient
                mover_path.extend(convert_to_mover_steps(
                    [target_pos for _ in range(int(task['Length']))],
                    order_name,
                    MoverMode.LOADING
                ))

                prev = task
                continue

            prev_pos = tuple(prev['Position'])

            # Find path from previous dispenser to this one
            sub_path = path_optimizer.find_shortest_path(prev_pos, target_pos)[1:]

            # Calculate transit & waiting time
            overall_time = task['Start'] - prev['Finish']

            # Calculate waiting time
            free_time = overall_time - len(sub_path)

            if free_time > 0:
                w_task = resting_sites_sched['selected'][task_i]
                # Travel to one before diverging point
                sub_path = path_optimizer.find_balanced_path(prev_pos, tuple(w_task['best_div_point']))[1:-1]
                # Travel to one before the resting place
                sub_path += w_task['to_rest']
                # Wait
                for i in range(w_task['duration']):
                    sub_path.append(w_task['site'])
                # Travel back to the diverging point
                sub_path += w_task['to_div']
                # Travel to next task
                a = path_optimizer.find_balanced_path(tuple(w_task['best_div_point']), target_pos)[1:]
                sub_path += a
            else:
                # Add just transit path
                sub_path = path_optimizer.find_balanced_path(prev_pos, target_pos)[1:]

            # Add path (and waiting detours, if any) from previous to next task
            mover_path.extend(convert_to_mover_steps(sub_path, order_name, MoverMode.TRANSIT))

            # Add loading time at dispenser
            mover_path.extend(convert_to_mover_steps(
                [task['Position'] for _ in range(int(task['Length']))],
                order_name,
                MoverMode.LOADING
            ))

            prev = task

        mover_paths.append(mover_path)
    return mover_paths


def equalize_arrays(paths: List[List[MoverStep]]) -> List[List[MoverStep]]:
    """
    Equalizes lengths of all paths.

    Args:
        paths: Paths to equalize.

    Returns:
         Equalized paths.
    """
    if not paths:
        return paths

    max_length = max(len(path) for path in paths)
    # Add elements to the end of each array to make them equal in length
    for path in paths:
        to_fill = max_length - len(path)
        if to_fill == 0:
            continue
        last_step = path[-1]
        equalizing_array = [(last_step.x, last_step.y) for _ in range(to_fill)]
        path.extend(convert_to_mover_steps(equalizing_array, 'None', MoverMode.EXTENSION))
    return paths


def run_from_merged(
        df: pd.DataFrame,
        row_amount: int,
        column_amount: int,
        filled: bool,
        unavailable_coordinates: List[List[int]],
        coordinate_dict: Dict[str, List[Tuple[int, int]]],
        mover_amount: int
) -> List[List[MoverStep]]:
    """
    Takes the schedule creator and the merged dataframe,
    and returns a normalized list of paths represented by MoverSteps.

    Args:
        df: Dataframe with schedule.
        row_amount: Number of rows in the layout.
        column_amount: Number of columns in the layout.
        filled: Whether layout is filled or not.
        unavailable_coordinates: Lists of lists with unavailable coordinates.
        coordinate_dict: Dictionary with tile type (or dispensed type) as key and list of tuples with coordinates as value.
        mover_amount: Amount of utilized movers.

    Returns:
        Normalized list of paths.
    """
    df_arr = split_df_by_movers(df, coordinate_dict, mover_amount)
    path_optimizer = PathOptimizer(
        rows=row_amount,
        cols=column_amount,
        filled=filled,
        unavailable_coords=unavailable_coordinates
    )
    routing_sites = RoutingSites(
        interfaces=coordinate_dict['interface'],
        rows=row_amount,
        cols=column_amount,
        filled=filled,
        unavailable_coords=unavailable_coordinates
    )
    resting_site_optimizer = RestingSiteOptimizer(df_arr, path_optimizer, routing_sites)
    resting_sites_sched = resting_site_optimizer.run()
    mover_paths = generate_mover_paths(df_arr, path_optimizer, resting_sites_sched)
    readable_paths = equalize_arrays(mover_paths)
    return readable_paths
