import logging

from domain.enums import ExperimentStatus
from domain.models.experiment import ExperimentDomainModel
from solvers.common.base_experiment_solver import BaseExperimentSolver, ExperimentResult
from solvers.common.mapper import map_experiment_domain_to_simulation_data
from solvers.common.utilities.simulation_creator import create_simulation
from solvers.cplex_perfume.mapper import map_experiment_domain_to_cplex_perfume_data, \
    map_schedule_dataframe_to_simulation_dataframe
from solvers.cplex_perfume.utilities.solver_engine import run

logger = logging.getLogger(__name__)


class CplexPerfumeExperimentSolver(BaseExperimentSolver):
    def solve(self, experiment_data: ExperimentDomainModel) -> ExperimentResult:
        try:
            data = map_experiment_domain_to_cplex_perfume_data(experiment_data)
            initial_schedule = run(data)
            simulation_data = map_experiment_domain_to_simulation_data(experiment_data)
            converted_schedule = map_schedule_dataframe_to_simulation_dataframe(
                schedule=initial_schedule,
                layout=experiment_data.layout
            )
            result = create_simulation(
                schedule=converted_schedule,
                data=simulation_data
            )
        except Exception as exc:
            logger.error(f"Exception thrown during Cplex Perfume solver execution: {exc}", exc_info=True)
            return ExperimentResult(result=None, status=ExperimentStatus.FAILED, gantt_files=None)
        return result
