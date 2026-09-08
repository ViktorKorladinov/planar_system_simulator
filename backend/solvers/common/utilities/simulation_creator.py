import pandas as pd

from domain.enums import GraphType, ExperimentStatus
from domain.models.experiment import Result
from solvers.common.base_experiment_solver import ExperimentResult
from solvers.common.models import SimulationData
from solvers.common.utilities import multimed_path_maker_car as path_maker
from solvers.common.utilities.interruptions_counter import analyze_interruptions
from solvers.common.utilities.path_optimizer import PathOptimizer
from solvers.common.utilities.schedule_extender import ScheduleExtender
from solvers.common.utilities.schedule_visualiser import ScheduleVisualizer
from solvers.cplex_medicine.mapper import map_finished_schedule_to_schedule


def create_simulation(
        schedule: pd.DataFrame,
        data: SimulationData
) -> ExperimentResult:
    """Generates all data required for simulations. It starts from initial schedule and adds routing.

        Args:
            schedule: Dataframe with schedule.
            data: Simulation data.

        Returns:
            Experiment result with required data for simulations.
        """
    # Extend schedule to allow for path creation
    path_optimizer = PathOptimizer(data.row_amount, data.column_amount, data.filled, data.unavailable_coordinates)
    extender = ScheduleExtender(schedule, path_optimizer)
    schedule_temp = schedule.copy()

    # Run extender without interruptions, to make sure the schedule is optimally compressed
    interruptions = [0 for _ in range(len(schedule_temp))]
    schedule_temp, _ = extender.optimize(interruptions, compress=True)

    # Create path and account for interruptions
    schedule_has_changed = True
    while schedule_has_changed:
        paths = path_maker.run_from_merged(
            df=schedule_temp,
            row_amount=data.row_amount,
            column_amount=data.column_amount,
            filled=data.filled,
            unavailable_coordinates=data.unavailable_coordinates,
            coordinate_dict=data.coordinate_dict,
            mover_amount=data.mover_amount
        )
        interruption_objects = analyze_interruptions(schedule_temp, paths)
        interruptions = [intrp['interruptions'] for intrp in interruption_objects]
        schedule_temp, schedule_has_changed = extender.optimize(interruptions)
    finished_schedule = schedule_temp

    # Create graphs for finished schedule
    schedule_visualizer = ScheduleVisualizer(
        coordinate_dict=data.coordinate_dict,
        mover_amount=data.mover_amount
    )
    color_options = [
        (finished_schedule, GraphType.DISPENSED_TYPE, True, True),
        (finished_schedule, GraphType.ORDER, True, False),
        (finished_schedule, GraphType.TILE, True, False)
    ]
    graphs, color_dict = schedule_visualizer.create_graphs(color_options)
    mover_paths = path_maker.run_from_merged(
        df=schedule_temp,
        row_amount=data.row_amount,
        column_amount=data.column_amount,
        filled=data.filled,
        unavailable_coordinates=data.unavailable_coordinates,
        coordinate_dict=data.coordinate_dict,
        mover_amount=data.mover_amount
    )
    return ExperimentResult(
        result=Result(
            mover_paths=mover_paths,
            max_path=max(len(path) for path in mover_paths),
            color_dict=color_dict
        ),
        status=ExperimentStatus.FINISHED,
        gantt_files=graphs,
        schedule=map_finished_schedule_to_schedule(finished_schedule)
    )
