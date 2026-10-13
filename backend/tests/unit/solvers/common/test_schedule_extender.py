import pandas as pd
import pytest
from unittest.mock import MagicMock

from solvers.common.utilities.path_optimizer import PathOptimizer
from solvers.common.utilities.schedule_extender import ScheduleExtender


def test_schedule_extender_enforces_tile_exclusivity():
    # Mock path optimizer where any shortest path length is 2 (travel time = 1)
    path_optimizer = MagicMock(spec=PathOptimizer)
    path_optimizer.find_shortest_path.return_value = [(0, 0), (1, 1)]

    # Two tasks on the SAME tile ('tile2x3') but DIFFERENT dispensers (0 and 1) on DIFFERENT movers
    schedule_data = {
        'Task': ['Job 1', 'Job 2'],
        'Medicine': ['MedA', 'MedB'],
        'Tile': ['tile2x3', 'tile2x3'],
        'Patient': [1, 2],
        'Length': [10, 10],
        'Start': [0, 10],
        'Mover': ['mover0', 'mover1'],
        'Finish': [10, 20],
        'Dispenser': [0, 1]
    }
    df = pd.DataFrame(schedule_data)

    extender = ScheduleExtender(df, path_optimizer)
    assert 'tile2x3' in extender.tile_groups
    assert len(extender.tile_groups['tile2x3']) == 2

    # Extend Task 1 by 5 ticks
    # Task 1 length becomes 15. Task 2 must now start at or after t = 15
    updated_schedule, changed = extender.optimize([5, 0])

    assert changed is True
    # Find Task 1 and Task 2 in updated schedule
    task1 = updated_schedule[updated_schedule['Task'] == 'Job 1'].iloc[0]
    task2 = updated_schedule[updated_schedule['Task'] == 'Job 2'].iloc[0]

    assert task1['Start'] == 0
    assert task1['Length'] == 15
    assert task1['Finish'] == 15

    # Tile exclusivity must ensure Task 2 starts only after Task 1 finishes on tile2x3
    assert task2['Start'] >= task1['Finish']
