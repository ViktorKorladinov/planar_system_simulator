import platform

import pandas as pd
from docplex.cp.config import context

from core.config import settings
from solvers.cplex_medicine.models import CplexExperimentModel
from solvers.cplex_medicine.utilities.batch_handler import ScheduleCreator


class LargeScheduleCreator:
    def run(self, data: CplexExperimentModel) -> pd.DataFrame:
        # Set CPLEX solver path
        if platform.processor() != 'arm':
            context.solver.local.execfile = settings.CPLEX_PATH
        else:
            context.solver.local.execfile = settings.ARM64_PATH

        # Gradually optimize schedule in batches
        creator = ScheduleCreator(data)
        schedules_arr = creator.run_multiple_batches(batch_size=data.batch_size)
        schedule = creator.merge_schedules([res_arr[0] for res_arr in schedules_arr])
        return schedule
