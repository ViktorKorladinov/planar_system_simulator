from abc import ABC, abstractmethod
from typing import Optional, NamedTuple

from domain.enums import ExperimentStatus, GraphType
from domain.models.experiment import ExperimentDomainModel, Result
from solvers.common.models import Schedule


class ExperimentResult(NamedTuple):
    result: Optional[Result]
    status: ExperimentStatus
    schedule: Optional[Schedule] = None
    gantt_files: Optional[dict[GraphType, str]] = None


class BaseExperimentSolver(ABC):
    @abstractmethod
    def solve(self, experiment_data: ExperimentDomainModel) -> ExperimentResult:
        """Solves the given experiment.

        Args:
            experiment_data: Data about the experiment.

        Returns:
            Schedule if solution was found, None otherwise.
        """
