from collections import defaultdict
from typing import List, Tuple, Dict, Optional

from api.dtos.requests.experiment import ExperimentCreateRequestDTO
from api.dtos.responses.experiment import (ExperimentPaginatedGetResponseDTO, ExperimentSingleCreateResponseDTO, \
                                           ExperimentSingleGetResponseDTO, QueueGetResponseDTO,
                                           ExperimentSummaryResponseDTO, ExperimentBatchGetResponseDTO,
                                           ExperimentBatchCreateResponseDTO, ExperimentBatchPaginatedGetResponseDTO,
                                           BatchSummaryResponseDTO)
from api.dtos.responses.simulation import SimulationGetResponseDTO, SimulationBatchGetResponseDTO, TopologyInfoDTO, \
    SimulationSummaryDTO, MoverStepDTO, MoverPathsDTO, GanttDataDTO
from core.config import settings
from domain.enums import ExperimentStatus, TileType, GraphType, LayoutType
from domain.models.batch import BatchDomainModel
from domain.models.common.tile import Tile
from domain.models.configuration import ConfigurationDomainModel
from domain.models.experiment import ExperimentDomainModel, MoverStep
from domain.models.layout import LayoutDomainModel
from domain.models.order_list import OrderListDomainModel
from mappers.domain.configuration_mapper import map_domain_to_configuration_dto
from mappers.domain.ingredient_list_mapper import map_ingredient_list_domain_to_dto
from mappers.domain.layout_mapper import map_domain_to_layout_basic_dto
from mappers.domain.order_list_mapper import map_order_list_domain_to_dto


def map_experiment_create_request_dto_to_domain(
        dto: ExperimentCreateRequestDTO,
        configuration_domain_model: ConfigurationDomainModel,
        layout_domain_model: LayoutDomainModel,
        order_list_domain_model: OrderListDomainModel) -> ExperimentDomainModel:
    """Maps an ExperimentCreateRequestDTO instance to an Experiment domain model.

    Args:
        dto: The Data Transfer Object containing experiment details.
        configuration_domain_model: The configuration domain model already converted from DTO.
        layout_domain_model: The layout domain model already converted from DTO.
        order_list_domain_model: The order list domain model already converted from DTO.

    Returns:
        A domain model instance of the experiment.
    """
    return ExperimentDomainModel(
        id=None,
        name=dto.name,
        status=ExperimentStatus.QUEUED,
        configuration=configuration_domain_model,
        layout=layout_domain_model,
        order_list=order_list_domain_model,
    )


def map_experiment_matrix_create_request_to_domain(
        configuration_domain_model: ConfigurationDomainModel,
        layout_domain_model: LayoutDomainModel,
        order_list_domain_model: OrderListDomainModel) -> ExperimentDomainModel:
    """Maps an ExperimentCreateRequestDTO instance to an Experiment domain model.

    Args:
        configuration_domain_model: The configuration domain model already converted from DTO.
        layout_domain_model: The layout domain model already converted from DTO.
        order_list_domain_model: The order list domain model already converted from DTO.

    Returns:
        A domain model instance of the experiment.
    """
    return ExperimentDomainModel(
        id=None,
        name=None,
        status=ExperimentStatus.QUEUED,
        configuration=configuration_domain_model,
        layout=layout_domain_model,
        order_list=order_list_domain_model,
    )


def map_experiment_domain_to_summary_response_dto(domain_model: ExperimentDomainModel) -> ExperimentSummaryResponseDTO:
    """Converts experiment domain models into a Data Transfer Object.

        Args:
            domain_model: The source domain entity to be mapped.

        Returns:
            A DTO representation of the experiment summary response.
        """
    res = domain_model.result
    return ExperimentSummaryResponseDTO(
        id=domain_model.id,
        name=domain_model.name,
        status=domain_model.status,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at,
        started_at=domain_model.started_at,
        finished_at=domain_model.finished_at,
        tile_amount=domain_model.layout.tile_amount,
        interface_amount=domain_model.layout.interface_amount,
        dispenser_amount=domain_model.layout.dispenser_amount,
        layout_id=domain_model.layout.id,
        layout_type=domain_model.layout.type,
        layout_name=domain_model.layout.name,
        configuration_id=domain_model.configuration.id,
        configuration_name=domain_model.configuration.name,
        solver_type=domain_model.configuration.solver_type,
        mover_amount=domain_model.configuration.mover_amount,
        time_limit=domain_model.configuration.time_limit,
        batch_size=domain_model.configuration.batch_size,
        process_amount=domain_model.configuration.process_amount,
        order_list_id=domain_model.order_list.id,
        order_list_name=domain_model.order_list.name,
        order_amount=domain_model.order_list.order_amount,
        batch_id=domain_model.batch_id,
        batch_name=domain_model.batch_name,
        warmup=domain_model.configuration.warmup,
        interface_time=domain_model.configuration.interface_time,
        dispensing_time=domain_model.configuration.dispensing_time,
        scheduled_cmax=res.scheduled_cmax if res else None,
        routed_cmax=res.routed_cmax if res else None,
        routing_overhead_abs=res.routing_overhead_abs if res else None,
        routing_overhead_pct=res.routing_overhead_pct if res else None,
        routing_iterations=res.routing_iterations if res else None,
        total_time_s=res.total_time_s if res else None
    )


def map_batch_domain_to_batch_create_response_dto(
        domain_model: Optional[BatchDomainModel],
        created_count: int,
        skipped_count: int,
        estimated_time: int,
        errors: List[str],
        is_dry_run: bool
) -> ExperimentBatchCreateResponseDTO:
    """Converts batch domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.
        created_count: Amount of created experiments.
        skipped_count: Amount of skipped experiments.
        estimated_time: Estimated time to process the whole batch in seconds.
        errors: List of validation errors encountered.
        is_dry_run: True if this was only a validation run.

    Returns:
        A DTO representation of the experiment batch create response.
    """
    if domain_model is None or is_dry_run:
        return ExperimentBatchCreateResponseDTO(
            experiments=None,
            created_amount=created_count,
            skipped_amount=skipped_count,
            name=None,
            total_experiment_amount=None,
            queued_experiment_amount=None,
            finished_experiment_amount=None,
            running_experiment_amount=None,
            failed_experiment_amount=None,
            estimated_time=estimated_time,
            created_at=None,
            updated_at=None,
            id=None,
            errors=errors,
            is_dry_run=is_dry_run
        )
    return ExperimentBatchCreateResponseDTO(
        experiments=[map_experiment_domain_to_summary_response_dto(model) for model in domain_model.experiments],
        created_amount=created_count,
        skipped_amount=skipped_count,
        name=domain_model.name,
        total_experiment_amount=domain_model.total_experiment_amount,
        queued_experiment_amount=domain_model.queued_experiment_amount,
        finished_experiment_amount=domain_model.finished_experiment_amount,
        running_experiment_amount=domain_model.running_experiment_amount,
        failed_experiment_amount=domain_model.failed_experiment_amount,
        estimated_time=estimated_time,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at,
        id=domain_model.id,
        errors=errors,
        is_dry_run=is_dry_run
    )


def map_batch_domain_to_summary_response_dto(domain_model: BatchDomainModel) -> BatchSummaryResponseDTO:
    """Converts batch domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the batch create response.
    """
    return BatchSummaryResponseDTO(
        id=domain_model.id,
        name=domain_model.name,
        total_experiment_amount=domain_model.total_experiment_amount,
        queued_experiment_amount=domain_model.queued_experiment_amount,
        finished_experiment_amount=domain_model.finished_experiment_amount,
        running_experiment_amount=domain_model.running_experiment_amount,
        failed_experiment_amount=domain_model.failed_experiment_amount,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at
    )


def map_batches_domain_to_paginated_get_response_dto(
        domain_models: List[BatchDomainModel],
        page: int,
        size: int,
        total: int
) -> ExperimentBatchPaginatedGetResponseDTO:
    """Converts batch domain models into a Data Transfer Object.

    Args:
        domain_models: The source domain entities to be mapped.
        page: Page number for paging.
        size: Size for paging.
        total: Total number of pages.

    Returns:
        A DTO representation of the batch get response.
    """
    return ExperimentBatchPaginatedGetResponseDTO(
        batches=[map_batch_domain_to_summary_response_dto(model) for model in domain_models],
        page=page,
        size=size,
        total=total
    )


def map_batch_domain_to_batch_get_response_dto(
        domain_model: BatchDomainModel) -> ExperimentBatchGetResponseDTO:
    """Converts batch domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the experiment batch get response.
    """
    return ExperimentBatchGetResponseDTO(
        experiments=[map_experiment_domain_to_summary_response_dto(model) for model in domain_model.experiments],
        name=domain_model.name,
        total_experiment_amount=domain_model.total_experiment_amount,
        queued_experiment_amount=domain_model.queued_experiment_amount,
        finished_experiment_amount=domain_model.finished_experiment_amount,
        running_experiment_amount=domain_model.running_experiment_amount,
        failed_experiment_amount=domain_model.failed_experiment_amount,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at,
        id=domain_model.id
    )


def map_experiments_domain_to_paginated_get_response_dto(
        domain_models: List[ExperimentDomainModel],
        page: int,
        size: int,
        total: int) -> ExperimentPaginatedGetResponseDTO:
    """Converts experiment domain models into a Data Transfer Object.

    Args:
        domain_models: The source domain entities to be mapped.
        page: Page number for paging.
        size: Size for paging.
        total: Total number of pages.

    Returns:
        A DTO representation of the experiment batch get response.
    """
    return ExperimentPaginatedGetResponseDTO(
        experiments=[map_experiment_domain_to_summary_response_dto(model) for model in domain_models],
        page=page,
        size=size,
        total=total
    )


def map_experiment_domain_to_single_create_response_dto(
        domain_model: Optional[ExperimentDomainModel],
        errors: List[str],
        is_dry_run: bool
) -> ExperimentSingleCreateResponseDTO:
    """Converts an experiment domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.
        errors: List of validation errors encountered.
        is_dry_run: True if this was only a validation run.

    Returns:
        A DTO representation of the experiment single create response.
    """
    if domain_model is None:
        return ExperimentSingleCreateResponseDTO(
            id=None,
            name=None,
            layout_id=None,
            layout=None,
            configuration_id=None,
            configuration=None,
            order_list=None,
            status=None,
            created_at=None,
            updated_at=None,
            started_at=None,
            finished_at=None,
            batch_id=None,
            batch_name=None,
            errors=errors,
            is_dry_run=is_dry_run,
            order_list_id=None,
            ingredient_list_id=None,
            ingredient_list=None
        )
    return ExperimentSingleCreateResponseDTO(
        id=domain_model.id,
        name=domain_model.name,
        layout_id=domain_model.layout.id,
        layout=map_domain_to_layout_basic_dto(domain_model.layout),
        configuration_id=domain_model.configuration.id,
        configuration=map_domain_to_configuration_dto(domain_model.configuration),
        order_list=map_order_list_domain_to_dto(domain_model.order_list),
        status=domain_model.status,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at,
        started_at=domain_model.started_at,
        finished_at=domain_model.finished_at,
        batch_id=domain_model.batch_id,
        batch_name=domain_model.batch_name,
        errors=errors,
        is_dry_run=is_dry_run,
        order_list_id=domain_model.order_list.id,
        ingredient_list_id=domain_model.layout.ingredient_list.id,
        ingredient_list=map_ingredient_list_domain_to_dto(domain_model.layout.ingredient_list)
    )


def map_experiment_domain_to_single_get_response_dto(
        domain_model: ExperimentDomainModel) -> ExperimentSingleGetResponseDTO:
    """Converts an experiment domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the experiment single get response.
    """
    return ExperimentSingleGetResponseDTO(
        id=domain_model.id,
        name=domain_model.name,
        layout_id=domain_model.layout.id,
        layout=map_domain_to_layout_basic_dto(domain_model.layout),
        configuration_id=domain_model.configuration.id,
        configuration=map_domain_to_configuration_dto(domain_model.configuration),
        order_list=map_order_list_domain_to_dto(domain_model.order_list),
        status=domain_model.status,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at,
        started_at=domain_model.started_at,
        finished_at=domain_model.finished_at,
        batch_id=domain_model.batch_id,
        batch_name=domain_model.batch_name,
        ingredient_list=map_ingredient_list_domain_to_dto(domain_model.layout.ingredient_list),
        ingredient_list_id=domain_model.layout.ingredient_list.id,
        order_list_id=domain_model.order_list.id
    )


def map_experiments_domain_to_queue_get_response_dto(domain_models: List[ExperimentDomainModel]) -> QueueGetResponseDTO:
    """Converts experiment domain models into a Data Transfer Object.

    Args:
        domain_models: The source domain entities to be mapped.

    Returns:
        A DTO representation of the queue get response.
    """
    return QueueGetResponseDTO(
        experiments=[map_experiment_domain_to_summary_response_dto(model) for model in domain_models]
    )


def map_experiment_domain_to_topology_info_dto(domain_model: ExperimentDomainModel) -> TopologyInfoDTO:
    """Converts an experiment domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the topology info for API responses.
    """
    return TopologyInfoDTO(
        topology=domain_model.layout.type,
        n_tiles=domain_model.layout.tile_amount,
        n_interfaces=domain_model.layout.interface_amount,
        n_dispensers=domain_model.layout.dispenser_amount
    )


def map_experiment_domain_to_simulation_summary_dto(domain_model: ExperimentDomainModel) -> SimulationSummaryDTO:
    """Converts an experiment domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the simulation summary for API responses.
    """
    return SimulationSummaryDTO(
        id=domain_model.id,
        name=f"{domain_model.name} Simulation",
        dispensing_time=domain_model.configuration.dispensing_time,
        mover_amount=domain_model.configuration.mover_amount,
        order_amount=len(domain_model.order_list.orders),
        topology_info=map_experiment_domain_to_topology_info_dto(domain_model),
        calculated_at=domain_model.updated_at
    )


def map_experiments_domain_to_simulation_batch_response_dto(domain_models: List[ExperimentDomainModel],
                                                            total_pages: int, page: int,
                                                            size: int) -> SimulationBatchGetResponseDTO:
    """Converts experiment domain models into a Data Transfer Object.

    Args:
        domain_models: The source domain entities to be mapped.
        total_pages: The total number of pages available.
        page: The current page.
        size: The size of the page.

    Returns:
        A DTO representation of the simulation batch get response.
    """
    return SimulationBatchGetResponseDTO(
        total=total_pages,
        page=page,
        size=size,
        items=[map_experiment_domain_to_simulation_summary_dto(model) for model in domain_models]
    )


def map_mover_step_domain_to_dto(domain_model: MoverStep) -> MoverStepDTO:
    """Converts a mover step domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the mover step for API responses.
    """
    return MoverStepDTO(
        x=domain_model.x,
        y=domain_model.y,
        mode=domain_model.mode,
        order=domain_model.order,
        rest_offset_x=domain_model.rest_offset_x,
        rest_offset_y=domain_model.rest_offset_y
    )


def get_layout_dimensions(tiles: List[Tile]) -> Tuple[int, int]:
    """Returns the dimensions (m, n) of the layout where:
        m = highest x coordinate + 1
        n = highest y coordinate + 1

    Args:
        tiles: A list of tiles included in the layout.

    Returns:
        The dimensions of the layout (m, n).
    """
    m = max((tile.y for tile in tiles), default=-1) + 1
    n = max((tile.x for tile in tiles), default=-1) + 1
    return m, n


def map_experiment_domain_to_mover_paths_dto(domain_model: ExperimentDomainModel) -> MoverPathsDTO:
    """Converts an experiment domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the mover paths for API responses.
    """
    m, n = get_layout_dimensions(domain_model.layout.tiles)
    paths = []
    if domain_model.result is not None and domain_model.result.mover_paths is not None:
        paths = [[map_mover_step_domain_to_dto(step) for step in path] for path in domain_model.result.mover_paths]

    non_empty_paths = []
    for path in paths:
        if len(path) > 0:
            non_empty_paths.append(path)

    is_filled = domain_model.layout.type in [LayoutType.SQUARE, LayoutType.CUSTOM]
    return MoverPathsDTO(
        m=m,
        n=n,
        filled=is_filled,
        paths=non_empty_paths
    )


def map_experiment_domain_to_gannt_data_dto(domain_model: ExperimentDomainModel) -> GanttDataDTO:
    """Converts an experiment domain model into a Data Transfer Object.

        Args:
            domain_model: The source domain entity to be mapped.

        Returns:
            A DTO representation of the gannt data for API responses.
    """
    max_path = 0
    if domain_model.result is not None and domain_model.result.max_path is not None:
        max_path = domain_model.result.max_path
    return GanttDataDTO(
        max_path=max_path,
        names=[f"{GraphType.DISPENSED_TYPE.value}_graph", f"{GraphType.ORDER.value}_graph",
               f"{GraphType.TILE.value}_graph"],
        api_plot_url=f"{settings.BACKEND_URL}/api/v1/simulations/{domain_model.id}/plots"
    )


def extract_medicine_dict(tiles: List[Tile]) -> Dict[str, List[List[int]]]:
    """Extracts a dictionary mapping medicine names to lists of [x, y] coordinates.

    Args:
        tiles: A list of tiles included in the layout.

    Returns:
        A dictionary mapping medicine names to lists of [x, y] coordinates.
    """
    medicine_dict = defaultdict(list)
    for tile in tiles:
        if tile.type == TileType.DISPENSER:
            for medicine_type in tile.dispensed_types:
                medicine_dict[medicine_type].append([tile.x, tile.y])
        elif tile.type == TileType.INTERFACE:
            medicine_dict['interface'].append([tile.x, tile.y])
        elif tile.type == TileType.MIXER:
            medicine_dict['mixer'].append([tile.x, tile.y])
        elif tile.type == TileType.CAPPER:
            medicine_dict['capper'].append([tile.x, tile.y])
        elif tile.type == TileType.BLOCKED:
            medicine_dict['blocked'].append([tile.x, tile.y])
    return dict(medicine_dict)


def extract_dispensers_dict(tiles: List[Tile]) -> Dict[str, str]:
    """Extracts a dictionary mapping "x_y" coordinate strings to medicine names.

    Args:
        tiles: A list of tiles included in the layout.

    Returns:
        A dictionary mapping "x_y" coordinate strings to medicine names.
    """
    dispensers_dict = {}
    for tile in tiles:
        key = f"{tile.x}x{tile.y}"
        if tile.type == TileType.DISPENSER and tile.dispensed_types:
            dispensers_dict[key] = ",".join(tile.dispensed_types)
        elif tile.type == TileType.INTERFACE:
            dispensers_dict[key] = 'interface'
        elif tile.type == TileType.MIXER:
            dispensers_dict[key] = 'mixer'
        elif tile.type == TileType.CAPPER:
            dispensers_dict[key] = 'capper'
        elif tile.type == TileType.BLOCKED:
            dispensers_dict[key] = 'blocked'
        elif tile.type == TileType.EMPTY:
            dispensers_dict[key] = 'empty'
    return dispensers_dict


def map_experiment_domain_to_simulation_get_response_dto(
        domain_model: ExperimentDomainModel) -> SimulationGetResponseDTO:
    """Converts an experiment domain model into a Data Transfer Object.

        Args:
            domain_model: The source domain entity to be mapped.

        Returns:
            A DTO representation of the simulation get response.
    """
    res = domain_model.result
    metrics_dict = None
    if res is not None:
        metrics_dict = {
            "scheduled_cmax": res.scheduled_cmax,
            "routed_cmax": res.routed_cmax,
            "routing_overhead_abs": res.routing_overhead_abs,
            "routing_overhead_pct": res.routing_overhead_pct,
            "routing_iterations": res.routing_iterations,
            "routing_time_s": res.routing_time_s,
            "scheduling_time_s": res.scheduling_time_s,
            "total_time_s": res.total_time_s,
            "initial_interruptions": res.initial_interruptions,
            "final_interruptions": res.final_interruptions,
            "iterations_interruption_history": res.iterations_interruption_history,
            "cp_solve_status": res.cp_solve_status,
            "best_bound_internal": res.best_bound_internal,
            "internal_gap_pct": res.internal_gap_pct,
            "solver_branches": res.solver_branches,
            "solver_fails": res.solver_fails,
            "solver_choice_points": res.solver_choice_points,
            "warm_start_cmax": res.warm_start_cmax,
            "total_transit_time": res.total_transit_time,
            "total_dispensing_time": res.total_dispensing_time,
            "total_wait_time": res.total_wait_time,
            "dispensing_to_travel_ratio": res.dispensing_to_travel_ratio,
            "mover_busy_time_per_mover": res.mover_busy_time_per_mover,
            "task_count": res.task_count,
            "batch_count": res.batch_count,
        }

    return SimulationGetResponseDTO(
        tile_type_dict=extract_medicine_dict(domain_model.layout.tiles),
        dispenser_dict=extract_dispensers_dict(domain_model.layout.tiles),
        gantts=map_experiment_domain_to_gannt_data_dto(domain_model),
        order_color_dict=domain_model.result.color_dict if domain_model.result else {},
        mover_paths=map_experiment_domain_to_mover_paths_dto(domain_model),
        metrics=metrics_dict
    )
