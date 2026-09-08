import logging
import math
import os
from typing import Optional, List

from pydantic import ValidationError

from api.dtos.common.configuration_dto import ConfigurationDTO
from api.dtos.common.layout_dto import LayoutDTO
from api.dtos.common.order_list_dto import OrderListDTO
from api.dtos.requests.experiment import ExperimentSingleCreateRequestDTO, ExperimentBatchCreateRequestDTO, \
    ExperimentMatrixCreateRequestDTO, \
    ExperimentSingleUpdateRequestDTO, ExperimentBatchSingleUpdateRequestDTO
from api.dtos.responses.experiment import ExperimentSingleCreateResponseDTO, \
    ExperimentPaginatedGetResponseDTO, ExperimentSingleGetResponseDTO, QueueGetResponseDTO, \
    ExperimentBatchGetResponseDTO, ExperimentBatchPaginatedGetResponseDTO, ExperimentBatchCreateResponseDTO
from api.dtos.responses.simulation import SimulationBatchGetResponseDTO, SimulationGetResponseDTO
from clients.tasks.base_task_client import BaseTaskClient
from core.config import settings
from core.exceptions import EntityNotFoundError
from db.base_unit_of_work import BaseUnitOfWork
from domain.enums import ExperimentStatus, LayoutType, SolverType, ExperimentSortField, SortDirection, BatchSortField, \
    GraphType
from domain.models.batch import BatchDomainModel
from domain.models.configuration import ConfigurationDomainModel
from domain.models.experiment import ExperimentDomainModel
from domain.models.layout import LayoutDomainModel
from domain.models.order_list import OrderListDomainModel
from mappers.domain.configuration_mapper import map_configuration_dto_to_domain
from mappers.domain.experiment_mapper import map_experiment_domain_to_single_get_response_dto, \
    map_experiments_domain_to_paginated_get_response_dto, \
    map_experiments_domain_to_queue_get_response_dto, map_experiment_create_request_dto_to_domain, \
    map_experiment_domain_to_single_create_response_dto, map_batch_domain_to_batch_get_response_dto, \
    map_experiments_domain_to_simulation_batch_response_dto, map_experiment_domain_to_simulation_get_response_dto, \
    map_experiment_matrix_create_request_to_domain, map_batch_domain_to_batch_create_response_dto, \
    map_batches_domain_to_paginated_get_response_dto
from mappers.domain.ingredient_list_mapper import map_ingredient_list_dto_to_domain
from mappers.domain.layout_mapper import map_layout_dto_to_domain
from mappers.domain.order_list_mapper import map_order_list_dto_to_domain

logger = logging.getLogger(__name__)


class ExperimentService:
    def __init__(self, uow: BaseUnitOfWork, task_client: BaseTaskClient):
        self.uow = uow
        self.task_client = task_client
        self.buffer = 15

    def _set_default_experiment_name(self, domain_models: List[ExperimentDomainModel],
                                     batch_name: Optional[str] = None) -> None:
        """Sets default name for experiment if not provided.

        Args:
            domain_models: Domain models for which name should be set.
            batch_name: Batch name used as prefix.
        """
        index = 1
        with self.uow:
            for domain_model in domain_models:
                if domain_model.name is None and domain_model.id is not None:
                    if batch_name is None:
                        domain_model.name = f"Experiment ({domain_model.id})"
                    else:
                        domain_model.name = f"{batch_name} - Experiment ({index})"
                    self.uow.experiment_repo.update(domain_model)
                    index += 1
            self.uow.commit()

    def _set_default_configuration_name(self, domain_models: List[ConfigurationDomainModel],
                                        batch_name: Optional[str] = None) -> None:
        """Sets default name for configuration if not provided.

        Args:
            domain_models: Domain models for which name should be set.
            batch_name: Batch name used as prefix.
        """
        index = 1
        with self.uow:
            for domain_model in domain_models:
                if domain_model.name is None and domain_model.id is not None:
                    if batch_name is None:
                        domain_model.name = f"Configuration ({domain_model.id})"
                    else:
                        domain_model.name = f"{batch_name} - Configuration ({index})"
                    self.uow.configuration_repo.update(domain_model)
                    index += 1
            self.uow.commit()

    def _set_default_layout_name(self, domain_models: List[LayoutDomainModel],
                                 batch_name: Optional[str] = None) -> None:
        """Sets default name for layout if not provided.

        Args:
            domain_models: Domain models for which name should be set.
            batch_name: Batch name used as prefix.
        """
        index = 1
        with self.uow:
            for domain_model in domain_models:
                if domain_model.name is None and domain_model.id is not None:
                    if batch_name is None:
                        domain_model.name = f"Layout ({domain_model.id})"
                    else:
                        domain_model.name = f"{batch_name} - Layout ({index})"
                    self.uow.layout_repo.update(domain_model)
                    index += 1
            self.uow.commit()

    def _set_default_order_list_name(self, domain_models: List[OrderListDomainModel],
                                     batch_name: Optional[str] = None) -> None:
        """Sets default name for order list if not provided.

        Args:
            domain_models: Domain models for which name should be set.
            batch_name: Batch name used as prefix.
        """
        index = 1
        with self.uow:
            for domain_model in domain_models:
                if domain_model.name is None and domain_model.id is not None:
                    if batch_name is None:
                        domain_model.name = f"Order List ({domain_model.id})"
                    else:
                        domain_model.name = f"{batch_name} - Order List ({index})"
                    self.uow.order_list_repo.update(domain_model)
                    index += 1
            self.uow.commit()

    def _set_default_batch_name(self, domain_model: BatchDomainModel):
        """Sets default name for batch if not provided.

        Args:
            domain_model: Domain model for which name should be set.
        """
        if domain_model.name is None and domain_model.id is not None:
            with self.uow:
                domain_model.name = f"Batch ({domain_model.id})"
                self.uow.experiment_repo.update_batch(domain_model)
                self.uow.commit()

    def _resolve_configuration(self, configuration_id: Optional[int],
                               configuration: Optional[ConfigurationDTO]) -> ConfigurationDomainModel:
        """Returns configuration domain model chosen for the experiment.

        Args:
            configuration_id: Configuration ID.
            configuration: Configuration.

        Returns:
            Configuration domain model for the experiment.

        Raises:
            ValueError: If the request_dto contains invalid configuration ID.
        """
        if configuration_id is not None:
            configuration_domain_model = self.uow.configuration_repo.find_by_id(configuration_id)
            if configuration_domain_model is None:
                raise EntityNotFoundError(entity_name="Configuration", entity_id=configuration_id)
            return configuration_domain_model
        else:
            configuration_domain_model = map_configuration_dto_to_domain(configuration)
            return self.uow.configuration_repo.create(configuration_domain_model)

    def _resolve_layout(self, layout_id: Optional[int], layout: Optional[LayoutDTO]) -> LayoutDomainModel:
        """Returns layout domain model chosen for the experiment.

        Args:
            layout_id: Layout ID.
            layout: Layout.

        Returns:
            Layout domain model for the experiment.

        Raises:
            ValueError: If the request_dto contains invalid layout ID.
        """
        if layout_id is not None:
            layout_domain_model = self.uow.layout_repo.find_by_id(layout_id)
            if layout_domain_model is None:
                raise EntityNotFoundError(entity_name="Layout", entity_id=layout_id)
            return layout_domain_model
        else:
            if layout.ingredient_list_id is not None:
                ingredient_list_domain_model = self.uow.ingredient_list_repo.find_by_id(layout.ingredient_list_id)
                if ingredient_list_domain_model is None:
                    raise EntityNotFoundError(entity_name="Ingredient List", entity_id=layout.ingredient_list_id)
                layout_domain_model = map_layout_dto_to_domain(
                    dto=layout,
                    ingredient_list_domain_model=ingredient_list_domain_model
                )
                return self.uow.layout_repo.create(layout_domain_model)
            else:
                ingredient_list_domain_model = self.uow.ingredient_list_repo.create(
                    map_ingredient_list_dto_to_domain(layout.ingredient_list))
                ingredient_list_domain_model.name = f"Ingredient List ({ingredient_list_domain_model.id})"
                self.uow.ingredient_list_repo.update(ingredient_list_domain_model)
                layout_domain_model = map_layout_dto_to_domain(
                    dto=layout,
                    ingredient_list_domain_model=ingredient_list_domain_model
                )
                return self.uow.layout_repo.create(layout_domain_model)

    def _resolve_order_list(self, order_list_id: Optional[int],
                            order_list: Optional[OrderListDTO]) -> OrderListDomainModel:
        """Returns order list domain model chosen for the experiment.

        Args:
            order_list_id: Order list ID.
            order_list: Order List.

        Returns:
            Order list domain model for the experiment.

        Raises:
            ValueError: If the request_dto contains invalid order list ID.
        """
        if order_list_id is not None:
            order_list_domain_model = self.uow.order_list_repo.find_by_id(order_list_id)
            if order_list_domain_model is None:
                raise EntityNotFoundError(entity_name="Order List", entity_id=order_list_id)
            return order_list_domain_model
        else:
            order_list_domain_model = map_order_list_dto_to_domain(order_list)
            return self.uow.order_list_repo.create(order_list_domain_model)

    def create_and_enqueue(
            self,
            request_dto: ExperimentSingleCreateRequestDTO,
            is_dry_run: bool
    ) -> ExperimentSingleCreateResponseDTO:
        """Creates an experiment and adds it to the queue.

        Args:
            request_dto: DTO with experiment data.
            is_dry_run: Indicates whether the order list should be created or only validated.

        Returns:
            Create response DTO for the experiment.
        """
        errors = []
        with self.uow:
            try:
                experiment_domain_model = map_experiment_create_request_dto_to_domain(
                    dto=request_dto,
                    layout_domain_model=self._resolve_layout(
                        layout_id=request_dto.layout_id,
                        layout=request_dto.layout
                    ),
                    configuration_domain_model=self._resolve_configuration(
                        configuration_id=request_dto.configuration_id,
                        configuration=request_dto.configuration
                    ),
                    order_list_domain_model=self._resolve_order_list(
                        order_list_id=request_dto.order_list_id,
                        order_list=request_dto.order_list
                    )
                )
            except ValidationError as e:
                for error in e.errors():
                    clean_msg = error['msg'].replace("Value error, ", "")
                    errors.append(clean_msg)
                    return map_experiment_domain_to_single_create_response_dto(
                        domain_model=None,
                        errors=errors,
                        is_dry_run=is_dry_run
                    )
            if is_dry_run:
                return map_experiment_domain_to_single_create_response_dto(
                    domain_model=experiment_domain_model,
                    errors=errors,
                    is_dry_run=is_dry_run
                )
            experiment_domain_model = self.uow.experiment_repo.create(experiment_domain_model)
            self.uow.commit()

        task_id = self.task_client.enqueue_experiment(experiment_domain_model.id)
        with self.uow:
            experiment_domain_model.task_id = task_id
            self.uow.experiment_repo.update(experiment_domain_model)
            self.uow.commit()
        self._set_default_experiment_name([experiment_domain_model])
        self._set_default_layout_name([experiment_domain_model.layout])
        self._set_default_configuration_name([experiment_domain_model.configuration])
        self._set_default_order_list_name([experiment_domain_model.order_list])
        return map_experiment_domain_to_single_create_response_dto(
            domain_model=experiment_domain_model,
            errors=errors,
            is_dry_run=is_dry_run
        )

    def get_all(self,
                page: int = 1,
                size: int = 20,
                statuses: Optional[List[ExperimentStatus]] = None,
                layout_types: Optional[List[LayoutType]] = None,
                solver_types: Optional[List[SolverType]] = None,
                batch_id: Optional[int] = None,
                search: Optional[str] = None,
                sort_by: ExperimentSortField = ExperimentSortField.CREATED_AT,
                sort_dir: SortDirection = SortDirection.ASC) -> ExperimentPaginatedGetResponseDTO:
        """Retrieves a paginated batch of experiments.

        Args:
            page: Page number.
            size: Amount of experiments on one page.
            statuses: An optional list of statuses to filter by.
            layout_types: An optional list of layout types to filter by.
            solver_types: An optional list of solver types to filter by.
            batch_id: The ID of the batch for which experiments should be found.
            search: An optional search string to filter by name.
            sort_by: An optional sort field to sort by.
            sort_dir: An optional sort direction to sort by.

        Returns:
            A batch response DTO containing the list of experiments.
        """
        skip = (page - 1) * size
        limit = size
        total = 0
        with self.uow:
            domain_models = self.uow.experiment_repo.find_all(
                skip=skip,
                limit=limit,
                statuses=statuses,
                layout_types=layout_types,
                solver_types=solver_types,
                search=search,
                sort_by=sort_by,
                sort_dir=sort_dir,
                batch_id=batch_id
            )
            total = self.uow.experiment_repo.get_experiment_count(
                statuses=statuses,
                layout_types=layout_types,
                solver_types=solver_types,
                search=search,
                batch_id=batch_id
            )
        return map_experiments_domain_to_paginated_get_response_dto(
            domain_models=domain_models,
            page=page,
            size=size,
            total=int(math.ceil(total / size))
        )

    def get_by_id(self, experiment_id: int) -> Optional[ExperimentSingleGetResponseDTO]:
        """Fetches a single experiment by its unique identifier.

        Args:
            experiment_id: The ID of the requested experiment.

        Returns:
            A response DTO if the experiment exists, otherwise None.

        Raises:
            EntityNotFoundError: If the experiment was not found.
        """
        with self.uow:
            domain_model = self.uow.experiment_repo.find_by_id(experiment_id)
        if domain_model is None:
            raise EntityNotFoundError(entity_name="Experiment", entity_id=experiment_id)
        return map_experiment_domain_to_single_get_response_dto(domain_model)

    def delete_gantt_charts(self, experiment_id: int) -> bool:
        """Specifically deletes the expected graph files and the folder if empty.

        Args:
            experiment_id: The ID of the experiment.

        Returns:
            True if the specific files were handled, False otherwise.
        """
        graph_types = [GraphType.DISPENSED_TYPE, GraphType.ORDER, GraphType.TILE]
        experiment_folder = os.path.join(settings.GRAPH_FOLDER_PATH, str(experiment_id))

        if not os.path.exists(experiment_folder):
            return True

        try:
            for graph_type in graph_types:
                prefix = graph_type.value if hasattr(graph_type, 'value') else graph_type
                filename = f"{prefix.lower()}_graph.html"
                file_path = os.path.join(experiment_folder, filename)

                if os.path.exists(file_path):
                    os.remove(file_path)
            if not os.listdir(experiment_folder):
                os.rmdir(experiment_folder)
            else:
                logger.warning(f"Folder deletion failed. Folder {experiment_folder} is not empty.")

            return True
        except OSError as e:
            logger.error(f"Error during deletion of files with graphs for experiment {experiment_id}: {e}")
            return False

    def delete(self, experiment_id: int) -> bool:
        """Attempts to delete an experiment by its unique identifier and cancel its execution.

        Args:
            experiment_id: The ID of the experiment to remove.

        Returns:
            True if the experiment was successfully deleted, False if it was not found.

        Raises:
            EntityNotFoundException: If the experiment was not found.
        """
        task_id_to_delete = None
        with self.uow:
            experiment = self.uow.experiment_repo.find_by_id(experiment_id)
            if experiment is None:
                raise EntityNotFoundError(entity_name="Experiment", entity_id=experiment_id)
            task_id_to_delete = experiment.task_id
            success = self.uow.experiment_repo.delete(experiment_id)
            if success:
                self.uow.commit()
        if task_id_to_delete is not None:
            self.task_client.cancel_experiment(task_id_to_delete)
            self.delete_gantt_charts(experiment_id)
        return success

    def get_queue_state(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> QueueGetResponseDTO:
        """Retrieves a paginated batch of experiments from the queue.

        Args:
            skip: The number of records to skip for pagination.
            limit: The maximum number of records to return.
            status: The status to filter on.

        Returns:
            A queue response DTO containing the list of experiments.
        """
        statuses = [ExperimentStatus.QUEUED, ExperimentStatus.RUNNING]
        if status in [ExperimentStatus.QUEUED, ExperimentStatus.RUNNING]:
            statuses = [status]
        with self.uow:
            domain_models = self.uow.experiment_repo.find_all(skip=skip, limit=limit, statuses=statuses)
        return map_experiments_domain_to_queue_get_response_dto(domain_models)

    def get_simulations(self, page: Optional[int] = 0, size: Optional[int] = 20) -> SimulationBatchGetResponseDTO:
        """Retrieves a paginated batch of experiments.

        Args:
            page: The number of the page for which simulations should be retrieved.
            size: Max amount of simulations on one page.

        Returns:
            A simulation batch response DTO containing the list of simulations on desired page.
        """
        skip = (page - 1) * size
        limit = size
        statuses = [ExperimentStatus.FINISHED]
        with self.uow:
            domain_models = self.uow.experiment_repo.find_all(
                skip=skip,
                limit=limit,
                statuses=statuses,
                sort_by=ExperimentSortField.CREATED_AT,
                sort_dir=SortDirection.DESC
            )
            experiment_count = self.uow.experiment_repo.get_experiment_count(statuses=statuses)
        total_pages = int(math.ceil(experiment_count / size))
        return map_experiments_domain_to_simulation_batch_response_dto(domain_models=domain_models,
                                                                       total_pages=total_pages, page=page, size=size)

    def get_simulation_by_id(self, simulation_id: int) -> Optional[SimulationGetResponseDTO]:
        """Fetches a single simulation by its unique identifier.

        Args:
            simulation_id: ID of the simulation which matches ID of experiment to which the simulation belongs.

        Returns:
            A simulation response DTO with simulation details if it exists, otherwise None.

        Raises:
            EntityNotFoundError: If the simulation was not found.
        """
        with self.uow:
            domain_model = self.uow.experiment_repo.find_by_id(simulation_id)
        if domain_model is None or domain_model.status != ExperimentStatus.FINISHED:
            raise EntityNotFoundError(entity_name="Simulation", entity_id=simulation_id)
        return map_experiment_domain_to_simulation_get_response_dto(domain_model)

    def update_by_id(self, experiment_id: int, request_dto: ExperimentSingleUpdateRequestDTO) -> Optional[
        ExperimentSingleGetResponseDTO]:
        """Updates a single experiment by its unique identifier.

        Args:
            experiment_id: ID of the experiment which should be updated.
            request_dto: Request DTO with updated experiment details.

        Returns:
            True if the experiment was successfully updated, False otherwise.

        Raises:
            EntityNotFoundError: If the experiment was not found.
        """
        with self.uow:
            experiment = self.uow.experiment_repo.find_by_id(experiment_id)
            if experiment is None:
                raise EntityNotFoundError(entity_name="Experiment", entity_id=experiment_id)
            experiment.name = request_dto.name
            success = self.uow.experiment_repo.update(experiment)
            if success is None:
                return None
            self.uow.commit()
            return map_experiment_domain_to_single_get_response_dto(experiment)

    def create_and_enqueue_batch(
            self,
            request_dto: ExperimentBatchCreateRequestDTO,
            is_dry_run: bool
    ) -> ExperimentBatchCreateResponseDTO:
        """Creates batch of experiments and adds them to the queue. Nothing is created if any experiment data is invalid.

        Args:
            request_dto: DTO with experiment data.
            is_dry_run: Indicates whether the order list should be created or only validated.

        Returns:
            Create response DTO for the experiments.
        """
        in_memory_experiments = []
        errors = []
        estimated_time = 0
        with self.uow:
            try:
                for experiment_dto in request_dto.experiments:
                    layout_model = self._resolve_layout(
                        layout_id=experiment_dto.layout_id,
                        layout=experiment_dto.layout
                    )
                    config_model = self._resolve_configuration(
                        configuration_id=experiment_dto.configuration_id,
                        configuration=experiment_dto.configuration
                    )
                    order_list_model = self._resolve_order_list(
                        order_list_id=experiment_dto.order_list_id,
                        order_list=experiment_dto.order_list
                    )
                    experiment_model = map_experiment_create_request_dto_to_domain(
                        dto=experiment_dto,
                        layout_domain_model=layout_model,
                        configuration_domain_model=config_model,
                        order_list_domain_model=order_list_model
                    )
                    in_memory_experiments.append(experiment_model)
                    estimated_time += experiment_model.configuration.time_limit + self.buffer
                batch_model = BatchDomainModel(
                    name=request_dto.name,
                    experiments=in_memory_experiments
                )
            except ValidationError as e:
                for error in e.errors():
                    clean_msg = error['msg'].replace("Value error, ", "")
                    errors.append(clean_msg)
                return map_batch_domain_to_batch_create_response_dto(
                    domain_model=None,
                    created_count=0,
                    skipped_count=len(request_dto.experiments),
                    errors=errors,
                    is_dry_run=is_dry_run,
                    estimated_time=0,
                )
            if is_dry_run:
                return map_batch_domain_to_batch_create_response_dto(
                    domain_model=batch_model,
                    created_count=len(batch_model.experiments),
                    skipped_count=0,
                    errors=errors,
                    is_dry_run=is_dry_run,
                    estimated_time=estimated_time
                )
            batch_model = self.uow.experiment_repo.create_batch(batch_model)
            self.uow.commit()
        self._set_default_batch_name(batch_model)
        task_ids = {}
        for experiment in batch_model.experiments:
            task_id = self.task_client.enqueue_experiment(experiment.id)
            task_ids[experiment.id] = task_id
        with self.uow:
            for experiment in batch_model.experiments:
                experiment.task_id = task_ids[experiment.id]
                self.uow.experiment_repo.update(experiment)
            self.uow.commit()
        self._set_default_experiment_name(
            domain_models=[experiment for experiment in batch_model.experiments],
            batch_name=batch_model.name
        )
        self._set_default_layout_name(
            domain_models=[experiment.layout for experiment in batch_model.experiments],
            batch_name=batch_model.name
        )
        self._set_default_configuration_name(
            domain_models=[experiment.configuration for experiment in batch_model.experiments],
            batch_name=batch_model.name
        )
        self._set_default_order_list_name(
            domain_models=[experiment.order_list for experiment in batch_model.experiments],
            batch_name=batch_model.name
        )
        return map_batch_domain_to_batch_create_response_dto(
            domain_model=batch_model,
            created_count=len(batch_model.experiments),
            skipped_count=0,
            errors=errors,
            is_dry_run=is_dry_run,
            estimated_time=estimated_time
        )

    def create_and_enqueue_matrix(
            self,
            request_dto: ExperimentMatrixCreateRequestDTO,
            is_dry_run: bool
    ) -> ExperimentBatchCreateResponseDTO:
        """Creates multiple experiments as all combinations of provided order lists, configurations and layouts.
        Nothing is created if any experiment data is invalid.

        Args:
            request_dto: DTO with experiment data.
            is_dry_run: Indicates whether the order list should be created or only validated.

        Returns:
            Batch create response DTO for the experiments.
        """
        errors = []
        layout_models = []
        configuration_models = []
        order_list_models = []
        in_memory_experiments = []
        index = 0
        skipped_count = 0
        created_count = 0
        estimated_time = 0
        with (self.uow):
            try:
                if request_dto.layout_ids is not None:
                    layout_models.extend(
                        self._resolve_layout(layout_id=layout_id, layout=None) for layout_id in request_dto.layout_ids)
                if request_dto.layouts is not None:
                    layout_models.extend(
                        self._resolve_layout(layout_id=None, layout=layout) for layout in request_dto.layouts)
                if request_dto.configuration_ids is not None:
                    configuration_models.extend(
                        self._resolve_configuration(configuration_id=configuration_id, configuration=None) for
                        configuration_id in request_dto.configuration_ids)
                if request_dto.configurations is not None:
                    configuration_models.extend(
                        self._resolve_configuration(configuration_id=None, configuration=configuration) for
                        configuration in request_dto.configurations)
                if request_dto.order_list_ids is not None:
                    order_list_models.extend(
                        self._resolve_order_list(order_list_id=order_list_id, order_list=None) for order_list_id in
                        request_dto.order_list_ids)
                if request_dto.order_lists is not None:
                    order_list_models.extend(
                        self._resolve_order_list(order_list_id=None, order_list=order_list) for order_list in
                        request_dto.order_lists)
                for layout_domain_model in layout_models:
                    for configuration_domain_model in configuration_models:
                        for order_list_domain_model in order_list_models:
                            try:
                                experiment_model = map_experiment_matrix_create_request_to_domain(
                                    layout_domain_model=layout_domain_model,
                                    configuration_domain_model=configuration_domain_model,
                                    order_list_domain_model=order_list_domain_model)
                                in_memory_experiments.append(experiment_model)
                                index += 1
                                created_count += 1
                                estimated_time += experiment_model.configuration.time_limit + self.buffer
                            except ValidationError as e:
                                skipped_count += 1
                                for error in e.errors():
                                    clean_msg = error['msg'].replace("Value error, ", "")
                                    errors.append(clean_msg)
                batch_model = BatchDomainModel(
                    name=request_dto.name,
                    experiments=in_memory_experiments
                )
            except ValidationError as e:
                for error in e.errors():
                    clean_msg = error['msg'].replace("Value error, ", "")
                    errors.append(clean_msg)
                total_expected = len(layout_models) * len(configuration_models) * len(order_list_models)
                total_expected = total_expected if total_expected > 0 else 1
                return map_batch_domain_to_batch_create_response_dto(
                    domain_model=None,
                    created_count=0,
                    skipped_count=total_expected,
                    errors=errors,
                    is_dry_run=is_dry_run,
                    estimated_time=0
                )
            if is_dry_run:
                return map_batch_domain_to_batch_create_response_dto(
                    domain_model=batch_model,
                    created_count=created_count,
                    skipped_count=skipped_count,
                    errors=errors,
                    is_dry_run=is_dry_run,
                    estimated_time=sum(
                        (experiment.configuration.time_limit + self.buffer) for experiment in batch_model.experiments),
                )
            elif len(batch_model.experiments) == 0:
                return map_batch_domain_to_batch_create_response_dto(
                    domain_model=batch_model,
                    created_count=created_count,
                    skipped_count=skipped_count,
                    errors=errors,
                    is_dry_run=is_dry_run,
                    estimated_time=0
                )
            batch_model = self.uow.experiment_repo.create_batch(batch_model)
            self.uow.commit()
        self._set_default_batch_name(batch_model)
        task_ids = {}
        for experiment in batch_model.experiments:
            task_id = self.task_client.enqueue_experiment(experiment.id)
            task_ids[experiment.id] = task_id
        with self.uow:
            for experiment in batch_model.experiments:
                experiment.task_id = task_ids[experiment.id]
                self.uow.experiment_repo.update(experiment)
            self.uow.commit()
        self._set_default_experiment_name(
            domain_models=[experiment for experiment in batch_model.experiments],
            batch_name=batch_model.name
        )
        self._set_default_layout_name(
            domain_models=[experiment.layout for experiment in batch_model.experiments],
            batch_name=batch_model.name
        )
        self._set_default_configuration_name(
            domain_models=[experiment.configuration for experiment in batch_model.experiments],
            batch_name=batch_model.name
        )
        self._set_default_order_list_name(
            domain_models=[experiment.order_list for experiment in batch_model.experiments],
            batch_name=batch_model.name
        )
        return map_batch_domain_to_batch_create_response_dto(
            domain_model=batch_model,
            created_count=created_count,
            skipped_count=skipped_count,
            errors=errors,
            is_dry_run=is_dry_run,
            estimated_time=sum(
                (experiment.configuration.time_limit + self.buffer) for experiment in batch_model.experiments),
        )

    def get_batch_by_id(self, batch_id: int) -> Optional[ExperimentBatchGetResponseDTO]:
        """Fetches a single batch by its unique identifier.

        Args:
            batch_id: The ID of the requested batch.

        Returns:
            A response DTO if the batch exists, otherwise None.

        Raises:
            EntityNotFoundError: If the batch was not found.
        """
        with self.uow:
            domain_model = self.uow.experiment_repo.find_batch_by_id(batch_id)
        if domain_model is None:
            raise EntityNotFoundError(entity_name="Batch", entity_id=batch_id)
        return map_batch_domain_to_batch_get_response_dto(domain_model)

    def get_all_batches(self,
                        page: int = 1,
                        size: int = 20,
                        search: Optional[str] = None,
                        sort_by: BatchSortField = BatchSortField.CREATED_AT,
                        sort_dir: SortDirection = SortDirection.ASC) -> ExperimentBatchPaginatedGetResponseDTO:
        """Retrieves a paginated batch list.

        Args:
            page: Page number.
            size: Amount of experiments on one page.
            search: An optional search string to filter by name.
            sort_by: An optional sort field to sort by.
            sort_dir: An optional sort direction to sort by.

        Returns:
            A paginated list with batches.
        """
        skip = (page - 1) * size
        limit = size
        total = 0
        with self.uow:
            domain_models = self.uow.experiment_repo.find_all_batches(
                skip=skip,
                limit=limit,
                search=search,
                sort_by=sort_by,
                sort_dir=sort_dir
            )
            total = self.uow.experiment_repo.get_batch_count(
                search=search
            )
        return map_batches_domain_to_paginated_get_response_dto(
            domain_models=domain_models,
            page=page,
            size=size,
            total=int(math.ceil(total / size))
        )

    def update_batch_by_id(self, batch_id: int, request_dto: ExperimentBatchSingleUpdateRequestDTO) -> Optional[
        ExperimentBatchGetResponseDTO]:
        """Updates a single batch by its unique identifier.

        Args:
            batch_id: ID of the batch which should be updated.
            request_dto: Request DTO with updated batch details.

        Returns:
            True if the batch was successfully updated, False otherwise.

        Raises:
            EntityNotFoundError: If the batch was not found.
        """
        with self.uow:
            batch = self.uow.experiment_repo.find_batch_by_id(batch_id)
            if batch is None:
                raise EntityNotFoundError(entity_name="Batch", entity_id=batch_id)
            batch.name = request_dto.name
            success = self.uow.experiment_repo.update_batch(batch)
            if success is None:
                return None
            self.uow.commit()
            return map_batch_domain_to_batch_get_response_dto(batch)

    def delete_batch(self, batch_id: int) -> bool:
        """Attempts to delete a batch by its unique identifier together with all experiments belonging to the batch and cancels their execution.

        Args:
            batch_id: The ID of the batch to remove.

        Returns:
            True if the batch was successfully deleted, False if it was not found.

        Raises:
            EntityNotFoundException: If the batch was not found.
        """
        task_ids_to_cancel = []
        with self.uow:
            batch = self.uow.experiment_repo.find_batch_by_id(batch_id)
            if batch is None:
                raise EntityNotFoundError(entity_name="Batch", entity_id=batch_id)
            for experiment in batch.experiments:
                if experiment.task_id is not None:
                    task_ids_to_cancel.append(experiment.task_id)

            success = self.uow.experiment_repo.delete_batch(batch_id)
            if success:
                self.uow.commit()
            else:
                return False
        for task_id in task_ids_to_cancel:
            self.task_client.cancel_experiment(task_id)
        return True
