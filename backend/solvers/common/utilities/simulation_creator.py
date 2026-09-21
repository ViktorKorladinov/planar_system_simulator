import time
from typing import Optional, Dict, Any, List
import pandas as pd

from domain.enums import GraphType, ExperimentStatus, MoverMode
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
        data: SimulationData,
        solver_metadata: Optional[Dict[str, Any]] = None,
        start_total_time: Optional[float] = None
) -> ExperimentResult:
    """Generates all data required for simulations. It starts from initial schedule and adds routing.

        Args:
            schedule: Dataframe with schedule.
            data: Simulation data.
            solver_metadata: Optional dictionary with CP solver metrics.
            start_total_time: Optional start timestamp (perf_counter) of solver execution.

        Returns:
            Experiment result with required data for simulations.
    """
    routing_start = time.perf_counter()

    # Pre-routing scheduled makespan
    scheduled_cmax = 0
    if len(schedule) > 0 and 'Finish' in schedule.columns:
        scheduled_cmax = int(schedule['Finish'].max())

    # Extend schedule to allow for path creation
    path_optimizer = PathOptimizer(data.row_amount, data.column_amount, data.filled, data.unavailable_coordinates)
    extender = ScheduleExtender(schedule, path_optimizer)
    schedule_temp = schedule.copy()

    # Run extender without interruptions, to make sure the schedule is optimally compressed
    interruptions = [0 for _ in range(len(schedule_temp))]
    schedule_temp, _ = extender.optimize(interruptions, compress=True)

    # Create path and account for interruptions
    schedule_has_changed = True
    iteration_count = 0
    iterations_interruption_history: List[int] = []
    initial_interruptions = None

    while schedule_has_changed:
        iteration_count += 1
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
        current_interruptions_sum = sum(interruptions)
        iterations_interruption_history.append(current_interruptions_sum)

        if initial_interruptions is None:
            initial_interruptions = current_interruptions_sum

        schedule_temp, schedule_has_changed = extender.optimize(interruptions)

    finished_schedule = schedule_temp
    final_interruptions = iterations_interruption_history[-1] if iterations_interruption_history else 0

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

    routing_elapsed = time.perf_counter() - routing_start
    total_elapsed = (time.perf_counter() - start_total_time) if start_total_time is not None else routing_elapsed

    routed_cmax = max(len(path) for path in mover_paths) if mover_paths else 0
    routing_overhead_abs = routed_cmax - scheduled_cmax
    routing_overhead_pct = round(((routed_cmax - scheduled_cmax) / scheduled_cmax * 100.0), 2) if scheduled_cmax > 0 else 0.0

    # Operational metrics calculated from mover_paths
    total_transit = 0
    total_loading = 0
    total_wait = 0
    mover_busy_times: Dict[str, int] = {}

    for mover_idx, path in enumerate(mover_paths):
        mover_key = f"mover_{mover_idx}"
        mover_transit = 0
        mover_loading = 0
        mover_wait = 0
        for step in path:
            if step.mode == MoverMode.TRANSIT:
                mover_transit += 1
            elif step.mode == MoverMode.LOADING:
                mover_loading += 1
            elif step.mode == MoverMode.WAIT_REST:
                mover_wait += 1
        total_transit += mover_transit
        total_loading += mover_loading
        total_wait += mover_wait
        mover_busy_times[mover_key] = mover_transit + mover_loading

    dispensing_to_travel = round(total_loading / total_transit, 4) if total_transit > 0 else 0.0

    # Build Result
    result_kwargs: Dict[str, Any] = {
        "mover_paths": mover_paths,
        "max_path": routed_cmax,
        "color_dict": color_dict,
        "scheduled_cmax": scheduled_cmax,
        "routed_cmax": routed_cmax,
        "routing_overhead_abs": routing_overhead_abs,
        "routing_overhead_pct": routing_overhead_pct,
        "routing_iterations": iteration_count,
        "routing_time_s": round(routing_elapsed, 4),
        "total_time_s": round(total_elapsed, 4),
        "initial_interruptions": initial_interruptions,
        "final_interruptions": final_interruptions,
        "iterations_interruption_history": iterations_interruption_history,
        "total_transit_time": total_transit,
        "total_dispensing_time": total_loading,
        "total_wait_time": total_wait,
        "dispensing_to_travel_ratio": dispensing_to_travel,
        "mover_busy_time_per_mover": mover_busy_times,
        "task_count": len(finished_schedule),
    }

    if solver_metadata:
        for k, v in solver_metadata.items():
            if k in Result.model_fields:
                result_kwargs[k] = v

    return ExperimentResult(
        result=Result(**result_kwargs),
        status=ExperimentStatus.FINISHED,
        gantt_files=graphs,
        schedule=map_finished_schedule_to_schedule(finished_schedule)
    )
