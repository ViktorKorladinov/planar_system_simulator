from typing import List, Dict, Union

import pandas as pd

from domain.enums import MoverMode
from domain.models.experiment import MoverStep
from solvers.common.utilities.convs import tile_str_to_tuple, mover_str_to_int


def analyze_interruptions(schedule: pd.DataFrame, paths: List[List[MoverStep]]) -> List[Dict[str, Union[int, float]]]:
    """
    Reconstructs loading sequences from movers' paths and calculate interruptions for each task.

    Args:
        schedule: Schedule to analyze.
        paths: List of paths to analyze.

    Returns:
        List with dictionaries containing interruption data.
    """
    num_movers = len(paths)
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

        interruption_stats.append({
            "sequence_length": seq_length,
            "interruptions": interruptions,
            "all_interruptions": all_interruptions,
            "interruption_percentage": round(interruptions / seq_length * 100, 2)
        })

    return interruption_stats
