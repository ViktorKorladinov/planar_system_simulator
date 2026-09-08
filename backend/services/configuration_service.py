import math
from typing import Optional, List

from pydantic import ValidationError

from api.dtos.requests.configuration import ConfigurationSingleCreateRequestDTO, ConfigurationSingleUpdateRequestDTO
from api.dtos.responses.configuration import ConfigurationSingleCreateResponseDTO, ConfigurationBatchGetResponseDTO, \
    ConfigurationSingleGetResponseDTO
from core.exceptions import EntityNotFoundError
from db.base_unit_of_work import BaseUnitOfWork
from domain.enums import SolverType, SortDirection, ConfigurationSortField
from domain.models.configuration import ConfigurationDomainModel
from mappers.domain.configuration_mapper import map_configuration_single_create_request_dto_to_domain, \
    map_configuration_domain_to_single_create_response_dto, \
    map_configuration_domain_to_batch_get_response_dto, map_configuration_domain_to_single_get_response_dto


class ConfigurationService:
    """Orchestrates business use cases for Configuration entities."""

    def __init__(self, uow: BaseUnitOfWork):
        self.uow = uow

    def _set_default_name(self, domain_model: ConfigurationDomainModel):
        """Sets default name for configuration if not provided.

        Args:
            domain_model: Domain model for which name should be set.
        """
        if domain_model.name is None and domain_model.id is not None:
            with self.uow:
                domain_model.name = f"Configuration ({domain_model.id})"
                self.uow.configuration_repo.update(domain_model)
                self.uow.commit()

    def create(
            self,
            request_dto: ConfigurationSingleCreateRequestDTO,
            is_dry_run: bool
    ) -> ConfigurationSingleCreateResponseDTO:
        """Processes a request to create a new configuration.

        Args:
            request_dto: The data transfer object containing the new configuration data.
            is_dry_run: Indicates whether the layout should be created or only validated.

        Returns:
            A response DTO representing the successfully created configuration.
        """
        errors = []
        with self.uow:
            try:
                domain_model = map_configuration_single_create_request_dto_to_domain(request_dto)
            except ValidationError as e:
                for error in e.errors():
                    clean_msg = error['msg'].replace("Value error, ", "")
                    errors.append(clean_msg)
                return map_configuration_domain_to_single_create_response_dto(
                    domain_model=None,
                    errors=errors,
                    is_dry_run=is_dry_run
                )
            if is_dry_run:
                return map_configuration_domain_to_single_create_response_dto(
                    domain_model=domain_model,
                    errors=errors,
                    is_dry_run=is_dry_run
                )
            domain_model = self.uow.configuration_repo.create(domain_model)
            self.uow.commit()
        self._set_default_name(domain_model)
        return map_configuration_domain_to_single_create_response_dto(
            domain_model=domain_model,
            is_dry_run=is_dry_run,
            errors=errors
        )

    def get_all(self,
                page: int = 1,
                size: int = 20,
                solver_types: Optional[List[SolverType]] = None,
                search: Optional[str] = None,
                sort_by: ConfigurationSortField = ConfigurationSortField.CREATED_AT,
                sort_dir: SortDirection = SortDirection.ASC
                ) -> ConfigurationBatchGetResponseDTO:
        """Retrieves a paginated batch of configurations.

        Args:
            page: Page number.
            size: Amount of configurations on one page.
            solver_types: An optional list of solver types to filter by.
            search: An optional search string to filter by name.
            sort_by: An optional sort field to sort by.
            sort_dir: An optional sort direction to sort by.

        Returns:
            A batch response DTO containing the list of configurations.
        """
        skip = (page - 1) * size
        limit = size
        total = 0
        with self.uow:
            domain_models = self.uow.configuration_repo.find_all(
                skip=skip,
                limit=limit,
                solver_types=solver_types,
                search=search,
                sort_by=sort_by,
                sort_dir=sort_dir
            )
            total = self.uow.configuration_repo.get_configuration_count(
                solver_types=solver_types,
                search=search)
        return map_configuration_domain_to_batch_get_response_dto(
            domain_models=domain_models,
            page=page,
            size=size,
            total=int(math.ceil(total / size)),
        )

    def get_by_id(self, configuration_id: int) -> Optional[ConfigurationSingleGetResponseDTO]:
        """Fetches a single configuration by its unique identifier.

        Args:
            configuration_id: The ID of the requested configuration.

        Returns:
            A response DTO if the configuration exists, otherwise None.

        Raises:
            EntityNotFoundError: If the configuration was not found.
        """
        with self.uow:
            domain_model = self.uow.configuration_repo.find_by_id(configuration_id)
        if domain_model is None:
            raise EntityNotFoundError(entity_name="Configuration", entity_id=configuration_id)
        return map_configuration_domain_to_single_get_response_dto(domain_model)

    def delete(self, configuration_id: int) -> bool:
        """Attempts to delete a configuration by its unique identifier.

        Args:
            configuration_id: The ID of the configuration to remove.

        Returns:
            True if the configuration was successfully deleted, False if it was not found.

        Raises:
            EntityNotFoundError: If the configuration was not found.
        """
        with self.uow:
            success = self.uow.configuration_repo.delete(configuration_id)
            if not success:
                raise EntityNotFoundError(entity_name="Configuration", entity_id=configuration_id)
            self.uow.commit()
        return success

    def update_by_id(self, configuration_id: int, request_dto: ConfigurationSingleUpdateRequestDTO) -> Optional[
        ConfigurationSingleGetResponseDTO]:
        """Updates a single configuration by its unique identifier.

        Args:
            configuration_id: ID of the configuration which should be updated.
            request_dto: Request DTO with updated configuration details.

        Returns:
            True if the configuration was successfully updated, False otherwise.

        Raises:
            EntityNotFoundError: If the configuration was not found.
        """
        with self.uow:
            configuration = self.uow.configuration_repo.find_by_id(configuration_id)
            if configuration is None:
                raise EntityNotFoundError(entity_name="Configuration", entity_id=configuration_id)
            configuration.name = request_dto.name
            success = self.uow.configuration_repo.update(configuration)
            if success is None:
                return None
            self.uow.commit()
            return map_configuration_domain_to_single_get_response_dto(configuration)
