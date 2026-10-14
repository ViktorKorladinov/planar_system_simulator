from unittest.mock import MagicMock

import pandas as pd

from domain.enums import MoverMode, ExperimentStatus
from solvers.common.models import SimulationData
from solvers.common.utilities.multimed_path_maker_car import generate_mover_paths
from solvers.common.utilities.path_optimizer import PathOptimizer
from solvers.common.utilities.simulation_creator import create_simulation


def test_initial_wait_is_not_counted_as_loading():
    mover_df = pd.DataFrame({
        'Patient': [0], 'Start': [3], 'Finish': [5], 'Length': [2], 'Position': [(1, 0)],
    })
    paths = generate_mover_paths([mover_df], MagicMock(spec=PathOptimizer), {'selected': {}})

    assert [step.mode for step in paths[0]] == [MoverMode.EXTENSION] * 3 + [MoverMode.LOADING] * 2


def test_create_simulation_reports_compressed_makespan_and_dispensing_ratio():
    # One mover on a 1x3 layout: interface (0,0), drug A (1,0). The CP schedule starts with an idle gap of 2 ticks
    # and leaves 1 extra tick before the outlet, which compression removes.
    schedule = pd.DataFrame({
        'Task': ['Job 1', 'Job 2', 'Job 3'],
        'Medicine': ['interface', 'A', 'interface'],
        'Tile': ['tile0x0', 'tile1x0', 'tile0x0'],
        'Patient': [0, 0, 0],
        'Length': [3, 4, 3],
        'Start': [2, 6, 11],
        'Finish': [5, 10, 14],
        'Mover': ['mover0', 'mover0', 'mover0'],
        'Dispenser': [0, 0, 0],
    })
    data = SimulationData(
        row_amount=1,
        column_amount=3,
        filled=True,
        unavailable_coordinates=[],
        coordinate_dict={'interface': [(0, 0)], 'A': [(1, 0)]},
        mover_amount=1,
    )

    result = create_simulation(schedule=schedule, data=data)

    assert result.status == ExperimentStatus.FINISHED
    assert result.result.cp_cmax == 14
    # Compressed: interface 0-3, travel 1, A 4-8, travel 1, interface 9-12
    assert result.result.scheduled_cmax == 12
    assert result.result.routed_cmax == 12
    assert result.result.routing_overhead_abs == 0
    # Only drug dispensing counts (4 ticks), interface operations do not; two transit steps
    assert result.result.total_dispensing_time == 4
    assert result.result.total_transit_time == 2
    assert result.result.dispensing_to_travel_ratio == 2.0
