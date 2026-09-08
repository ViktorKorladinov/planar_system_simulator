from abc import abstractmethod, ABC
from typing import Optional, List

from domain.enums import SolverType, ConfigurationSortField, SortDirection
from domain.models.configuration import ConfigurationDomainModel


class BaseConfigurationRepository(ABC):
    @abstractmethod
    def create(self, configuration: ConfigurationDomainModel) -> ConfigurationDomainModel:
        """Persists a new configuration to the storage.

        Args:
            configuration: The model containing configuration details.

        Returns:
            The saved model, populated with its generated ID.
        """

    @abstractmethod
    def find_by_id(self, configuration_id: int) -> Optional[ConfigurationDomainModel]:
        """Retrieves a configuration by its unique identifier.

        Args:
            configuration_id: The ID of the configuration to find.

        Returns:
            The configuration model if found, otherwise None.
        """

    @abstractmethod
    def find_all(self,
                 skip: int = 0,
                 limit: int = 100,
                 solver_types: Optional[List[SolverType]] = None,
                 search: Optional[str] = None,
                 sort_by: ConfigurationSortField = ConfigurationSortField.CREATED_AT,
                 sort_dir: SortDirection = SortDirection.ASC) -> List[ConfigurationDomainModel]:
        """Retrieves a paginated list of configurations.

        Args:
            skip: The number of records to skip (for pagination).
            limit: The maximum number of records to return.
            solver_types: An optional list of solver types to filter by.
            search: An optional search string to filter by name.
            sort_by: An optional sort field to sort by.
            sort_dir: An optional sort direction to sort by.

        Returns:
            A list of configuration models domain matching the criteria.
        """

    @abstractmethod
    def update(self, configuration: ConfigurationDomainModel) -> Optional[ConfigurationDomainModel]:
        """Updates an existing configuration in the storage.

        Args:
            configuration: The model containing updated values.

        Returns:
            The updated model, or None if the configuration was not found.
        """

    @abstractmethod
    def delete(self, configuration_id: int) -> bool:
        """Removes a configuration from the storage.

        Args:
            configuration_id: The ID of the configuration to delete.

        Returns:
            True if the configuration was successfully deleted, False otherwise.
        """

    @abstractmethod
    def get_configuration_count(
            self,
            solver_types: Optional[List[SolverType]] = None,
            search: Optional[str] = None
    ) -> int:
        """Returns the amount of configurations in the database.

        Args:
            solver_types: An optional list of solver types to filter by.
            search: An optional search string to filter by name.

        Returns:
            The amount of configurations matching filters in the database.
        """
