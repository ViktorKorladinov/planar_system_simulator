from abc import ABC, abstractmethod
from typing import Optional, List

from domain.enums import ExperimentStatus, LayoutType, SolverType, ExperimentSortField, SortDirection, BatchSortField
from domain.models.batch import BatchDomainModel
from domain.models.experiment import ExperimentDomainModel


class BaseExperimentRepository(ABC):
    """Interface for managing Experiment entity persistence."""

    @abstractmethod
    def create(self, experiment: ExperimentDomainModel) -> ExperimentDomainModel:
        """Persists a new experiment to the storage.

        Args:
            experiment: The model containing experiment details.

        Returns:
            The saved models model, populated with its generated ID.
        """

    @abstractmethod
    def find_by_id(self, experiment_id: int) -> Optional[ExperimentDomainModel]:
        """Retrieves an experiment by its unique identifier.

        Args:
            experiment_id: The ID of the experiment to find.

        Returns:
            The experiment model if found, otherwise None.
        """

    @abstractmethod
    def find_all(self,
                 skip: int = 0,
                 limit: int = 100,
                 statuses: Optional[List[ExperimentStatus]] = None,
                 layout_types: Optional[List[LayoutType]] = None,
                 solver_types: Optional[List[SolverType]] = None,
                 batch_id: Optional[int] = None,
                 search: Optional[str] = None,
                 sort_by: ExperimentSortField = ExperimentSortField.CREATED_AT,
                 sort_dir: SortDirection = SortDirection.ASC) -> List[
        ExperimentDomainModel]:
        """Retrieves a paginated list of experiments.

        Args:
            skip: The number of records to skip (for pagination).
            limit: The maximum number of records to return.
            statuses: An optional list of statuses to filter by.
            layout_types: An optional list of layout types to filter by.
            solver_types: An optional list of solver types to filter by.
            batch_id: The ID of the batch for which experiments should be found.
            search: An optional search string to filter by name.
            sort_by: An optional sort field to sort by.
            sort_dir: An optional sort direction to sort by.

        Returns:
            A list of experiment models matching the criteria.
        """

    @abstractmethod
    def update(self, experiment: ExperimentDomainModel) -> Optional[ExperimentDomainModel]:
        """Updates an existing experiment in the storage.

        Args:
            experiment: The model containing updated values.

        Returns:
            The updated models model, or None if the experiment was not found.
        """

    @abstractmethod
    def delete(self, experiment_id: int) -> bool:
        """Removes an experiment from the storage. It removes also experiment batch if it was the last experiment from the batch.

        Args:
            experiment_id: The ID of the experiment to delete.

        Returns:
            True if the experiment was successfully deleted, False otherwise.
        """

    @abstractmethod
    def get_experiment_count(
            self,
            statuses: Optional[List[ExperimentStatus]] = None,
            layout_types: Optional[List[LayoutType]] = None,
            solver_types: Optional[List[SolverType]] = None,
            batch_id: Optional[int] = None,
            search: Optional[str] = None
    ) -> int:
        """Returns the amount of experiments in the database.

        Args:
            statuses: An optional list of statuses to filter by.
            layout_types: An optional list of layout types to filter by.
            solver_types: An optional list of solver types to filter by.
            batch_id: The ID of the batch for which experiments should be found.
            search: An optional search string to filter by name.

        Returns:
            The amount of experiments matching filters in the database.
        """

    @abstractmethod
    def create_batch(self, batch: BatchDomainModel) -> BatchDomainModel:
        """Persists a new batch to the storage.

        Args:
            batch: The model containing batch details.

        Returns:
            The saved model, populated with its generated ID.
        """

    @abstractmethod
    def update_batch(self, batch: BatchDomainModel) -> Optional[BatchDomainModel]:
        """Updates name of an existing batch in the storage.

        Args:
            batch: The model containing updated name.

        Returns:
            The updated model, or None if the batch was not found.
        """

    @abstractmethod
    def delete_batch(self, batch_id: int) -> bool:
        """Removes a batch from the storage together with all experiments from that batch.

        Args:
            batch_id: The ID of the batch to delete.

        Returns:
            True if the batch was successfully deleted, false otherwise.
        """

    @abstractmethod
    def find_batch_by_id(self, batch_id: int) -> Optional[BatchDomainModel]:
        """Retrieves a batch by its unique identifier.

        Args:
            batch_id: The ID of the batch to find.

        Returns:
            The batch model if found, otherwise None.
        """

    @abstractmethod
    def find_all_batches(self,
                         skip: int = 0,
                         limit: int = 100,
                         search: Optional[str] = None,
                         sort_by: BatchSortField = BatchSortField.CREATED_AT,
                         sort_dir: SortDirection = SortDirection.ASC) -> List[
        BatchDomainModel]:
        """Retrieves a paginated list of batches.

        Args:
            skip: The number of records to skip (for pagination).
            limit: The maximum number of records to return.
            search: An optional search string to filter by name.
            sort_by: An optional sort field to sort by.
            sort_dir: An optional sort direction to sort by.

        Returns:
            A list of batch models matching the criteria.
        """

    @abstractmethod
    def get_batch_count(self, search: Optional[str] = None) -> int:
        """Returns the amount of batches in the database.

        Args:
            search: An optional search string to filter by name.

        Returns:
            The amount of batches matching filters in the database.
        """
