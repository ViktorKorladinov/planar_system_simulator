import platform

import pandas as pd
from docplex.cp.config import context

from core.config import settings
from solvers.cplex_medicine.models import CplexExperimentModel
from solvers.cplex_medicine.utilities.batch_handler import ScheduleCreator


class LargeScheduleCreator:
    def run(self, data: CplexExperimentModel) -> tuple[pd.DataFrame, dict]:
        # Set CPLEX solver path
        if platform.processor() != 'arm':
            context.solver.local.execfile = settings.CPLEX_PATH
        else:
            context.solver.local.execfile = settings.ARM64_PATH

        # Gradually optimize schedule in batches
        creator = ScheduleCreator(data)
        schedules_arr = creator.run_multiple_batches(batch_size=data.batch_size)
        schedule = creator.merge_schedules([res_arr.tasks for res_arr in schedules_arr])

        # Aggregate CP solver metrics across batches
        total_solve_time = 0.0
        total_branches = 0
        total_fails = 0
        total_choice_points = 0
        total_bound = 0.0
        solve_statuses = []
        gaps = []
        warm_cmaxes = []

        for batch_res in schedules_arr:
            if batch_res.warmup_cmax is not None:
                warm_cmaxes.append(batch_res.warmup_cmax)
            m = batch_res.metrics
            if m:
                if m.get("solve_time") is not None:
                    total_solve_time += m["solve_time"]
                if m.get("branches") is not None:
                    total_branches += m["branches"]
                if m.get("fails") is not None:
                    total_fails += m["fails"]
                if m.get("choice_points") is not None:
                    total_choice_points += m["choice_points"]
                if m.get("objective_bound") is not None:
                    total_bound += m["objective_bound"]
                if m.get("gap") is not None:
                    gaps.append(m["gap"])
                if m.get("solve_status"):
                    solve_statuses.append(m["solve_status"])

        aggregated_metrics = {
            "scheduling_time_s": round(total_solve_time, 4),
            "solver_branches": total_branches if total_branches > 0 else None,
            "solver_fails": total_fails if total_fails > 0 else None,
            "solver_choice_points": total_choice_points if total_choice_points > 0 else None,
            "best_bound_internal": round(total_bound, 4) if total_bound > 0 else None,
            "internal_gap_pct": round(sum(gaps) / len(gaps), 4) if gaps else None,
            "cp_solve_status": ", ".join(set(solve_statuses)) if solve_statuses else None,
            "warm_start_cmax": max(warm_cmaxes) if warm_cmaxes else None,
            "batch_count": len(schedules_arr),
        }

        return schedule, aggregated_metrics
