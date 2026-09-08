import logging
from typing import List, Optional

import hexaly.optimizer
from hexaly.optimizer import HxSolutionStatus

from domain.enums import ExperimentStatus, LayoutType, TileType
from domain.models.common.tile import Tile
from domain.models.experiment import ExperimentDomainModel
from solvers.common.base_experiment_solver import BaseExperimentSolver, ExperimentResult
from solvers.common.mapper import map_experiment_domain_to_simulation_data
from solvers.common.models import Task, Schedule
from solvers.common.utilities.simulation_creator import create_simulation
from solvers.hexaly.mapper import map_experiment_to_hexaly_experiment, map_schedule_domain_to_dataframe
from solvers.hexaly.models import HexalyExperimentModel

logger = logging.getLogger(__name__)


class HexalyExperimentSolver(BaseExperimentSolver):
    def _create_scheduled_task(self, task_id: int, order_id: int, data: HexalyExperimentModel, start: int, end: int,
                               tile_id: int,
                               mover_id: int) -> Task:
        """Creates scheduled task.

        Args:
            task_id: ID of the task.
            order_id: Time needed to dispense one unit.
            data: Experiment data.
            start: Start time of the task.
            end: End time of the task.
            tile_id: ID of the tile which is assigned to the task.
            mover_id: ID of the mover which is assigned to the task.

        Returns:
            Scheduled task.
        """
        return Task(task_id=task_id,
                    order_id=order_id,
                    duration=data.tasks[task_id].duration,
                    start=start,
                    end=end,
                    needed_dispensed_type=data.tasks[task_id].tile_type if data.tasks[
                                                                               task_id].tile_type != TileType.INTERFACE.value else None,
                    tile=Tile(type=data.tiles[tile_id].type,
                              dispensed_types=data.tiles[tile_id].dispensed_types,
                              x=data.tiles[tile_id].x,
                              y=data.tiles[tile_id].y),
                    mover_id=mover_id)

    def _construct_schedule(self, data: HexalyExperimentModel, opt_order_sequence_per_mover: List[List[int]],
                            opt_dispenser_task_sequence_per_order, opt_task_intervals,
                            opt_task_tile_assignment) -> Schedule:
        """Constructs schedule based on optimization results.

        Args:
            data: Experiment data.
            opt_order_sequence_per_mover: List for each mover containing list of order IDs assigned to the mover.
            opt_dispenser_task_sequence_per_order: List for each order containing ID of assigned tile for each task.
            opt_task_intervals: List of task intervals (["start", "end"]).
            opt_task_tile_assignment: List of tile IDs assigned to each task.

        Returns:
            Constructed schedule.
        """
        tasks: List[Task] = []
        for mover_id in range(len(opt_order_sequence_per_mover)):
            for order_id in opt_order_sequence_per_mover[mover_id]:
                # Add the first interface task
                task_id = data.orders[order_id].tasks[0].task_id
                tasks.append(self._create_scheduled_task(
                    task_id=task_id,
                    order_id=order_id,
                    data=data,
                    start=opt_task_intervals[task_id]['start'],
                    end=opt_task_intervals[task_id]['end'], tile_id=opt_task_tile_assignment[task_id],
                    mover_id=mover_id))
                # Add dispenser tasks
                first_dispenser_task_id = data.orders[order_id].tasks[1].task_id
                for r_task_id in opt_dispenser_task_sequence_per_order[order_id]:
                    task_id = first_dispenser_task_id + r_task_id
                    tasks.append(self._create_scheduled_task(
                        task_id=task_id,
                        order_id=order_id,
                        data=data,
                        start=opt_task_intervals[task_id]['start'],
                        end=opt_task_intervals[task_id]['end'], tile_id=opt_task_tile_assignment[task_id],
                        mover_id=mover_id))
                # Add the last interface task
                task_id = data.orders[order_id].tasks[-1].task_id
                tasks.append(self._create_scheduled_task(
                    task_id=task_id,
                    order_id=order_id,
                    data=data,
                    start=opt_task_intervals[task_id]['start'],
                    end=opt_task_intervals[task_id]['end'], tile_id=opt_task_tile_assignment[task_id],
                    mover_id=mover_id))
        return Schedule(tasks=tasks)

    def _create_schedule(self, data: HexalyExperimentModel) -> Optional[Schedule]:
        """Solves the given experiment.

        Args:
            data: Data about the experiment.

        Returns:
            Schedule if found, none otherwise.
        """
        with (hexaly.optimizer.HexalyOptimizer() as optimizer):
            model = optimizer.model

            # Number of orders
            nb_orders = len(data.orders)
            # Number of tasks including interface tasks
            nb_tasks = len(data.tasks)
            # Number of movers
            nb_movers = data.mover_amount
            # Total number of tiles with dispensers and interfaces
            nb_special_tiles = len(data.setup_times)
            # Total duration of all tasks including interface tasks
            total_duration_of_tasks = sum(task.duration for task in data.tasks)
            # The highest time needed to switch from machine m to machine n
            max_setup_time = max(max(row) for row in data.setup_times)
            # Upper bound for optimal solution which should be sufficient even for 1 mover
            max_possible_makespan = total_duration_of_tasks + (nb_tasks - 1) * max_setup_time

            # Matrix with times needed to switch from special tile m to special tile n between tasks
            setup_times_h = model.array(data.setup_times)
            # Durations of tasks ordered by task id
            task_durations_h = model.array(t.duration for t in data.tasks)
            # ID of the first task of each order
            order_first_task_ids_h = model.array([order.tasks[0].task_id for order in data.orders])
            # ID of the last task of each order
            order_last_task_ids_h = model.array(
                [order.tasks[len(order.tasks) - 1].task_id for order in data.orders])
            # Sequence of orders assigned to each mover in order in which they should be performed
            order_sequence_h = model.array([model.list(nb_orders) for _ in range(nb_movers)])
            # Sequence of tasks assigned to each special tile in order in which they should be performed
            tile_sequence_h = model.array([model.list(nb_tasks) for _ in range(nb_special_tiles)])
            # Array with special tile id assigned to each task.
            task_tile_h = model.array([model.find(tile_sequence_h, i) for i in range(nb_tasks)])
            # Intervals during which tasks should be performed.
            task_intervals_h = model.array(model.interval(0, max_possible_makespan) for _ in range(nb_tasks))
            # Sequence of tasks that require dispenser for each order sorted in order in which they should be performed
            task_sequence = []

            # CONSTRAINT: Each order has to be completed by 1 mover.
            model.constraint(model.partition(order_sequence_h))

            # CONSTRAINT: Each task has to be performed on 1 special tile.
            model.constraint(model.partition(tile_sequence_h))

            # CONSTRAINT: Tasks have to be completed on compatible special tile.
            for task in data.tasks:
                for tile_id in range(nb_special_tiles):
                    if data.available_tiles[task.task_id][tile_id] == 0:
                        model.constraint(model.not_(model.contains(tile_sequence_h[tile_id], task.task_id)))

            # CONSTRAINT: Length of interval for each task has to correspond to its duration.
            for i in range(nb_tasks):
                model.constraint(model.length(task_intervals_h[i]) == task_durations_h[i])

            for order in data.orders:
                # Amount of tasks in order that require dispenser
                dispenser_task_amount = len(order.tasks) - 2
                # The lowest id of dispenser task in order
                lowest_dispenser_task_id = order.tasks[1].task_id
                # Sequence of relative ids for tasks t1 ... tn-1 (all tasks except for interface tasks) in order in which they should be performed
                d_task_sequence_h = model.list(dispenser_task_amount)
                task_sequence.append(d_task_sequence_h)

                # CONSTRAINT: Every dispenser task has to be scheduled.
                model.constraint(model.count(d_task_sequence_h) == dispenser_task_amount)

                # CONSTRAINT: Order of dispenser tasks has to be determined.
                task_sequence_constraint = model.lambda_function(lambda i:
                                                                 model.end(task_intervals_h[lowest_dispenser_task_id +
                                                                                            d_task_sequence_h[i]]) +
                                                                 setup_times_h[model.find(tile_sequence_h,
                                                                                          lowest_dispenser_task_id +
                                                                                          d_task_sequence_h[i])]
                                                                 [model.find(tile_sequence_h, lowest_dispenser_task_id +
                                                                             d_task_sequence_h[i + 1])]
                                                                 <= model.start(task_intervals_h[
                                                                                    lowest_dispenser_task_id +
                                                                                    d_task_sequence_h[i + 1]]))
                model.constraint(model.and_(model.range(0, dispenser_task_amount - 1), task_sequence_constraint))

                # ID of load task performed on interface tile
                interface_load_task_id = order.tasks[0].task_id
                # ID of the first task from order which should be performed on dispenser tile
                first_dispenser_task_id = lowest_dispenser_task_id + d_task_sequence_h[0]

                # CONSTRAINT: Dispenser task from order which should be completed first has to start after mover is loaded.
                model.constraint(
                    model.end(task_intervals_h[interface_load_task_id]) +
                    setup_times_h[model.find(tile_sequence_h, interface_load_task_id)]
                    [model.find(tile_sequence_h, first_dispenser_task_id)]
                    <= model.start(task_intervals_h[first_dispenser_task_id]))

                # ID of unload task performed on interface tile
                interface_unload_task_id = order.tasks[len(order.tasks) - 1].task_id
                # ID of the last task from order which should be performed on dispenser tile
                last_dispenser_task_id = lowest_dispenser_task_id + d_task_sequence_h[dispenser_task_amount - 1]

                # CONSTRAINT: Unload task on interface can start when the last dispenser task is completed.
                model.constraint(
                    model.end(task_intervals_h[last_dispenser_task_id]) +
                    setup_times_h[model.find(tile_sequence_h, last_dispenser_task_id)]
                    [model.find(tile_sequence_h, interface_unload_task_id)]
                    <= model.start(task_intervals_h[interface_unload_task_id]))

            # CONSTRAINT: Tasks in orders completed by one mover can't overlap.
            for mover in range(nb_movers):
                m_orders_seq = order_sequence_h[mover]
                order_sequence_constraint = model.lambda_function(lambda i:
                                                                  model.end(model.at(task_intervals_h,
                                                                                     model.at(order_last_task_ids_h,
                                                                                              m_orders_seq[i]))) +
                                                                  setup_times_h[model.find(tile_sequence_h, model.at(
                                                                      order_last_task_ids_h, m_orders_seq[i]))]
                                                                  [model.find(tile_sequence_h,
                                                                              model.at(order_first_task_ids_h,
                                                                                       m_orders_seq[i + 1]))]
                                                                  <= model.start(model.at(task_intervals_h, model.at(
                                                                      order_first_task_ids_h, m_orders_seq[i + 1]))))
                model.constraint(model.and_(model.range(0, model.count(m_orders_seq) - 1), order_sequence_constraint))

            # CONSTRAINT: Tasks performed on one special tile can't overlap.
            for tile in range(nb_special_tiles):
                t_task_seq = tile_sequence_h[tile]
                tile_sequence_constraint = model.lambda_function(lambda i:
                                                                 model.end(model.at(task_intervals_h, t_task_seq[i]))
                                                                 <= model.start(
                                                                     model.at(task_intervals_h, t_task_seq[i + 1])))
                model.constraint(model.and_(model.range(0, model.count(t_task_seq) - 1), tile_sequence_constraint))

            # Makespan equals to the end of the task which ends as the last one.
            makespan = model.max(model.end(task_intervals_h[i]) for i in range(nb_tasks))
            model.minimize(makespan)
            model.close()

            optimizer.get_param().set_time_limit(data.time_limit)
            optimizer.get_param().set_nb_threads(data.nb_threads)
            optimizer.solve()

            opt_order_sequence_per_mover = []
            opt_dispenser_task_sequence_per_order = []
            opt_task_intervals = []

            if optimizer.solution.status == HxSolutionStatus.FEASIBLE or optimizer.solution.status == HxSolutionStatus.OPTIMAL:
                solution = optimizer.solution
                for mover in range(nb_movers):
                    hexaly_list = solution.get_value(order_sequence_h)[mover]
                    python_list = [order_id for order_id in hexaly_list]
                    opt_order_sequence_per_mover.append(python_list)
                for order in range(nb_orders):
                    hexaly_list = solution.get_value(task_sequence[order])
                    python_list = [task_id for task_id in hexaly_list]
                    opt_dispenser_task_sequence_per_order.append(python_list)
                opt_t_intervals = solution.get_value(task_intervals_h)
                for interval in opt_t_intervals:
                    start = interval.start()
                    end = interval.end()
                    opt_task_intervals.append({'start': start, 'end': end})
                hexaly_list = solution.get_value(task_tile_h)
                opt_task_tile_assignment = [tile_id for tile_id in hexaly_list]

                schedule = self._construct_schedule(data=data,
                                                    opt_order_sequence_per_mover=opt_order_sequence_per_mover,
                                                    opt_dispenser_task_sequence_per_order=opt_dispenser_task_sequence_per_order,
                                                    opt_task_intervals=opt_task_intervals,
                                                    opt_task_tile_assignment=opt_task_tile_assignment)

                return schedule

            return None

    def solve(self, experiment_data: ExperimentDomainModel) -> ExperimentResult:
        supported_topologies = [LayoutType.SQUARE, LayoutType.LINE, LayoutType.DOUBLE_LINE]
        if experiment_data.layout.type not in supported_topologies:
            return ExperimentResult(result=None, status=ExperimentStatus.FAILED)
        try:
            data = map_experiment_to_hexaly_experiment(experiment_data)
            initial_schedule = self._create_schedule(data)
            if initial_schedule is None:
                return ExperimentResult(result=None, status=ExperimentStatus.FAILED, gantt_files=None)
            simulation_data = map_experiment_domain_to_simulation_data(experiment_data)
            converted_schedule = map_schedule_domain_to_dataframe(
                schedule=initial_schedule,
                layout=experiment_data.layout
            )
            result = create_simulation(
                schedule=converted_schedule,
                data=simulation_data
            )
        except Exception as exc:
            logger.error(f"Exception thrown during Hexaly solver execution: {exc}", exc_info=True)
            return ExperimentResult(result=None, status=ExperimentStatus.FAILED, gantt_files=None)
        return result
