import logging

from domain.enums import ExperimentStatus
from domain.models.experiment import ExperimentDomainModel
from solvers.common.base_experiment_solver import BaseExperimentSolver, ExperimentResult
from solvers.common.mapper import map_experiment_domain_to_simulation_data
from solvers.common.utilities.simulation_creator import create_simulation
from solvers.cplex_medicine.mapper import map_experiment_to_cplex_experiment
from solvers.cplex_medicine.utilities.large_schedules_handler import LargeScheduleCreator

logger = logging.getLogger(__name__)


class CplexMedicineExperimentSolver(BaseExperimentSolver):
    def solve(self, experiment_data: ExperimentDomainModel) -> ExperimentResult:
        try:
            cplex_data = map_experiment_to_cplex_experiment(experiment_data)
            large_schedules_creator = LargeScheduleCreator()
            initial_schedule = large_schedules_creator.run(cplex_data)
            simulation_data = map_experiment_domain_to_simulation_data(experiment_data)
            result = create_simulation(
                schedule=initial_schedule,
                data=simulation_data
            )
        except Exception as exc:
            logger.error(f"Exception thrown during Cplex Medicine solver execution: {exc}", exc_info=True)
            return ExperimentResult(result=None, status=ExperimentStatus.FAILED, gantt_files=None)
        return result
