from typing import List, Dict, Union, Tuple, Set

import pandas as pd

from domain.enums import MoverMode
from domain.models.experiment import MoverStep
from solvers.common.utilities.convs import tile_str_to_tuple, mover_str_to_int

# Maximum number of movers that can transit the same tile simultaneously (round-robin around the tile).
MAX_TRANSITING_MOVERS_PER_TILE = 3


def compute_transit_congestion_penalties(schedule: pd.DataFrame, paths: List[List[MoverStep]]) -> Dict[int, int]:
    """
    Detects tiles transited by more than MAX_TRANSITING_MOVERS_PER_TILE movers at the same time step and
    assigns staggered delays to the most recently completed task of each excess mover.

    Args:
        schedule: Schedule to analyze.
        paths: List of paths to analyze.

    Returns:
        Dictionary with schedule index as key and penalty ticks as value.
    """
    num_movers = len(paths)
    max_path_len = max((len(path) for path in paths), default=0)

    # Precompute tasks by mover for fast lookup
    mover_task_indices: Dict[int, List[int]] = {}
    for seq_id, seq in schedule.iterrows():
        mover_task_indices.setdefault(mover_str_to_int(seq["Mover"]), []).append(seq_id)

    transit_penalties = {idx: 0 for idx in schedule.index}
    # Tile -> set of excess movers congested there in the previous time step
    active_congestions: Dict[Tuple[int, int], Set[int]] = {}

    for t in range(max_path_len):
        tile_occupancy: Dict[Tuple[int, int], List[int]] = {}
        for m in range(num_movers):
            if t < len(paths[m]) and paths[m][t].mode == MoverMode.TRANSIT:
                tile_occupancy.setdefault((paths[m][t].x, paths[m][t].y), []).append(m)

        new_active_congestions = {}
        for pos, movers in tile_occupancy.items():
            if len(movers) <= MAX_TRANSITING_MOVERS_PER_TILE:
                continue
            movers.sort()
            excess_movers = movers[MAX_TRANSITING_MOVERS_PER_TILE:]
            new_active_congestions[pos] = set(excess_movers)
            previously_congested_movers = active_congestions.get(pos, set())

            for i, mover_id in enumerate(excess_movers):
                # Only penalize once per continuous over-capacity event
                if mover_id in previously_congested_movers:
                    continue
                # Find the most recently completed task of this mover
                preceding_task_idx = None
                for idx in mover_task_indices.get(mover_id, []):
                    if schedule.loc[idx, "Finish"] <= t:
                        preceding_task_idx = idx
                if preceding_task_idx is not None:
                    transit_penalties[preceding_task_idx] += i + 1

        active_congestions = new_active_congestions

    return transit_penalties


def analyze_interruptions(
        schedule: pd.DataFrame,
        paths: List[List[MoverStep]],
        use_transit_congestion_fix: bool = True
) -> List[Dict[str, Union[int, float]]]:
    """
    Reconstructs loading sequences from movers' paths and calculate interruptions for each task,
    including both dispensing interruptions and transit congestion penalties.

    Args:
        schedule: Schedule to analyze.
        paths: List of paths to analyze.
        use_transit_congestion_fix: If true, penalizes movers exceeding the transit capacity of a tile.

    Returns:
        List with dictionaries containing interruption data.
    """
    num_movers = len(paths)

    if use_transit_congestion_fix:
        transit_penalties = compute_transit_congestion_penalties(schedule, paths)
    else:
        transit_penalties = {idx: 0 for idx in schedule.index}

    interruption_stats = []
    # Count interruptions for each loading sequence
    for seq_id, seq in schedule.iterrows():
        mover_id = mover_str_to_int(seq["Mover"])
        start = int(seq["Start"])
        end = int(seq["Finish"])
        seq_length = int(seq["Length"])
        interruptions = 0
        all_interruptions = 0

        for step_idx in range(start, end):
            interrupted = False
            for other_mover in range(num_movers):
                if other_mover == mover_id:
                    continue  # Skip the current mover
                if step_idx >= len(paths[other_mover]):
                    continue
                step = paths[other_mover][step_idx]
                if (step.x, step.y) == tile_str_to_tuple(seq['Tile']) and step.mode == MoverMode.TRANSIT:
                    if not interrupted:  # Count at most one interruption per time step
                        interruptions += 1
                        interrupted = True
                    all_interruptions += 1

        total_interruptions = interruptions + transit_penalties[seq_id]

        interruption_stats.append({
            "sequence_length": seq_length,
            "interruptions": total_interruptions,
            "task_interruptions": interruptions,
            "transit_interruptions": transit_penalties[seq_id],
            "all_interruptions": all_interruptions,
            "interruption_percentage": round(total_interruptions / seq_length * 100, 2) if seq_length > 0 else 0
        })

    return interruption_stats
