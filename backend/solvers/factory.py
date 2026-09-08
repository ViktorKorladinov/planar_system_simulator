from domain.enums import SolverType
from solvers.common.base_experiment_solver import BaseExperimentSolver
from solvers.cplex_medicine.experiment_solver import CplexMedicineExperimentSolver
from solvers.cplex_perfume.experiment_solver import CplexPerfumeExperimentSolver
from solvers.hexaly.experiment_solver import HexalyExperimentSolver

SOLVER_REGISTRY = {
    SolverType.HEXALY: HexalyExperimentSolver,
    SolverType.CPLEX_MEDICINE: CplexMedicineExperimentSolver,
    SolverType.CPLEX_PERFUMES: CplexPerfumeExperimentSolver,
}


def get_solver(solver_type: SolverType) -> BaseExperimentSolver:
    """Factory method to instantiate the correct solver.

    Args:
        solver_type: Type of the solver which should be instantiated.

    Returns:
        Instantiated solver based on given type.
    """
    solver_class = SOLVER_REGISTRY.get(solver_type)
    if not solver_class:
        raise ValueError(f"Unsupported solver type: {solver_type}")
    return solver_class()
