import platform
from docplex.cp.config import context

from core.config import settings
from solvers.cplex_perfume.models import CplexPerfumeData
from solvers.cplex_perfume.utilities.model_builder import SchedulingModelBuilder
from solvers.cplex_perfume.utilities.utils import solution_to_dataframe


def run(data: CplexPerfumeData):
    if platform.processor() != 'arm':
        context.solver.local.execfile = settings.CPLEX_PATH
    else:
        context.solver.local.execfile = settings.ARM64_PATH

    builder = SchedulingModelBuilder(
        recipes=data.recipes_raw,
        ingredients=data.ingredients,
        tiles_flat=data.tiles_flat,
        machines=data.machines,
        n_movers=data.mover_amount,
        tmax_values=data.tmax_values,
        data=data
    )
    full_model = builder.build()
    solution = full_model["model"].solve(TimeLimit=data.time_limit, LogVerbosity='Terse', Workers=data.process_amount)
    return solution_to_dataframe(solution, full_model)
