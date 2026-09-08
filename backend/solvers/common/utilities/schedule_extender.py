from typing import Tuple, List

import gurobipy as gp
import pandas as pd

from solvers.common.utilities.convs import tile_str_to_tuple
from solvers.common.utilities.path_optimizer import PathOptimizer


class ScheduleExtender:
    """
    A class that extends task processing times
    while respecting mover and dispenser constraints.
    """

    def __init__(self, schedule: pd.DataFrame, path_optimizer: PathOptimizer):
        """
        Initialize the SchedulerOptimizer with a schedule and path optimizer.
        """
        self.schedule = schedule.copy()
        self.path_optimizer = path_optimizer

        # Ensure schedule is sorted by start time
        self.schedule.sort_values('Start', inplace=True)
        self.schedule.reset_index(drop=True, inplace=True)

        if 'TicksAdded' not in self.schedule.columns:
            self.schedule['TicksAdded'] = 0

        # Group tasks by mover and dispenser
        self.mover_groups = {}
        self.disp_groups = {}
        self._group_tasks()

    def _group_tasks(self) -> None:
        """Groups tasks by mover and dispenser for constraint generation."""
        # Get indices of tasks grouped by mover
        grp_mover = self.schedule.groupby('Mover')
        self.mover_groups = {
            mover: group.index.to_numpy() for mover, group in grp_mover
        }
        # Get indices of tasks grouped by dispenser
        grp_disp = self.schedule.groupby(['Tile', 'Dispenser'])
        self.disp_groups = {
            f"{tile}x{dispenser}": group.index.to_numpy()
            for (tile, dispenser), group in grp_disp
        }

    def _travel_time(self, index1: int, index2: int) -> int:
        """
        Calculates travel time between two tasks.

        Args:
            index1: Index of the first task
            index2: Index of the second task
        """
        task1 = self.schedule.iloc[index1]
        task2 = self.schedule.iloc[index2]
        tile1 = tile_str_to_tuple(task1['Tile'])
        tile2 = tile_str_to_tuple(task2['Tile'])
        return len(self.path_optimizer.find_shortest_path(tile1, tile2)) - 1

    def optimize(self, additional_times: List[int], compress=False) -> Tuple[pd.DataFrame, bool]:
        """
        Optimizes the schedule by minimizing the makespan while respecting constraints.

        Args:
            additional_times: List of additional processing times for each task. Must have the same length as the schedule.
            compress: If true, runs the model without accounting for interruptions, to attempt compression.
        Returns:
            Tuple of the updated schedule with extended processing times and a boolean indicating if schedule has changed.
        """
        self._group_tasks()
        tasks_len = len(self.schedule)

        if len(additional_times) != tasks_len:
            raise ValueError(
                f"Length of additional_times ({len(additional_times)}) "
                f"must match schedule length ({tasks_len})"
            )

        # Calculate additional times' sizes by subtracting already executed extensions
        already_added = self.schedule['TicksAdded'].to_numpy()
        new_additions = [max(0, req - done) for req, done in zip(additional_times, already_added)]

        if sum(new_additions) == 0 and not compress:
            # Nothing to add, return early
            return self.schedule, False

        # Create Gurobi model
        model = gp.Model("ScheduleExtender")
        model.params.LogToConsole = 0
        model.params.OutputFlag = 0

        # s[i] = start time of task i
        s = model.addVars(tasks_len, name="start_times")

        # p[i] = processing time of task i
        p = [self.schedule.iloc[i].Length for i in range(tasks_len)]

        # Add additional time to processing times
        if not compress:
            p = [p[i] + new_additions[i] for i in range(tasks_len)]

        # Add mover constraints
        for mover_id, mover_array in self.mover_groups.items():
            # Add constraints: each task starts only after previous one finishes + travel time
            for i in range(len(mover_array) - 1):
                curr = mover_array[i]
                next_task = mover_array[i + 1]

                setup_time = self._travel_time(curr, next_task)
                model.addConstr(s[next_task] >= s[curr] + p[curr] + setup_time,
                                name=f"mover_{mover_id}_task_{curr}_to_{next_task}")

        # Add dispenser constraints
        for disp_id, disp_array in self.disp_groups.items():
            # Add constraints: each dispenser has one task running at a time
            for i in range(len(disp_array) - 1):
                curr = disp_array[i]
                next_task = disp_array[i + 1]

                model.addConstr(s[next_task] >= s[curr] + p[curr], name=f"dispenser_lock")

        # Objective: minimize makespan
        z = model.addVar(lb=0, name="makespan")
        for i in range(tasks_len):
            model.addConstr(z >= s[i] + p[i], name=f"makespan_constraint_{i}")

        model.setObjective(z, gp.GRB.MINIMIZE)

        # Optimize the model
        model.optimize()

        if model.status != gp.GRB.OPTIMAL:
            raise RuntimeError(f"Optimization failed with status {model.status}")

        # Update schedule with new start times and processing times
        updated_schedule = self.schedule.copy()

        # Update additional times
        if not compress:
            for i in range(tasks_len):
                updated_schedule.loc[i, 'TicksAdded'] += int(round(new_additions[i]))

        # Update start times
        for i in range(tasks_len):
            updated_schedule.loc[i, 'Start'] = int(round(s[i].X))

        # Update processing times if additional times were provided
        for i in range(tasks_len):
            updated_schedule.loc[i, 'Length'] = int(round(p[i]))

        # Calculate end times (Start + Length)
        updated_schedule['Finish'] = updated_schedule['Start'] + updated_schedule['Length']

        # Sort by new start time
        updated_schedule.sort_values('Start', inplace=True)
        updated_schedule.reset_index(drop=True, inplace=True)

        self.schedule = updated_schedule
        return updated_schedule, True
