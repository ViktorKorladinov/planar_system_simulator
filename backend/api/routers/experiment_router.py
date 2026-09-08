from typing import Optional, List

from fastapi import APIRouter, status, Depends, Query, Response

from api.dtos.requests.experiment import ExperimentSingleCreateRequestDTO, ExperimentBatchCreateRequestDTO, \
    ExperimentMatrixCreateRequestDTO, ExperimentSingleUpdateRequestDTO, ExperimentBatchSingleUpdateRequestDTO
from api.dtos.responses.experiment import ExperimentSingleCreateResponseDTO, \
    ExperimentPaginatedGetResponseDTO, ExperimentSingleGetResponseDTO, ExperimentBatchGetResponseDTO, \
    ExperimentBatchPaginatedGetResponseDTO, ExperimentBatchCreateResponseDTO
from dependencies import get_experiment_service
from domain.enums import ExperimentSortField, SortDirection, ExperimentStatus, LayoutType, SolverType, BatchSortField
from services.experiment_service import ExperimentService

router = APIRouter(
    prefix="/experiments",
    tags=["Experiments"]
)


@router.post(
    "/batch/",
    response_model=ExperimentBatchCreateResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create batch with experiments and add them to the queue."
)
async def create_experiments_batch(
        experiment_data: ExperimentBatchCreateRequestDTO,
        response: Response,
        dry_run: Optional[bool] = Query(False, description="Perform a dry run"),
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Creates experiments from batch and adds them to the queue."""
    result = experiment_service.create_and_enqueue_batch(request_dto=experiment_data, is_dry_run=dry_run)
    if result.errors:
        response.status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif result.is_dry_run:
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_201_CREATED
    return result


@router.post(
    "/batch/matrix",
    response_model=ExperimentBatchCreateResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create batch with all combinations of experiments from provided layouts, configurations and order lists and add them to the queue."
)
async def create_experiments_matrix(
        experiment_data: ExperimentMatrixCreateRequestDTO,
        response: Response,
        dry_run: Optional[bool] = Query(False, description="Perform a dry run"),
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Creates all combinations of experiments from provided layouts, configurations and order lists and add them to the queue."""
    result = experiment_service.create_and_enqueue_matrix(request_dto=experiment_data, is_dry_run=dry_run)
    if result.errors and result.created_amount == 0:
        response.status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif result.is_dry_run:
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_201_CREATED
    return result


@router.get(
    "/batch/{batch_id}",
    response_model=ExperimentBatchGetResponseDTO,
    summary="Get a single batch."
)
async def get_batch(
        batch_id: int,
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Fetches details for a specific batch."""
    batch = experiment_service.get_batch_by_id(batch_id)
    return batch


@router.get(
    "/batch/",
    response_model=ExperimentBatchPaginatedGetResponseDTO,
    summary="Get a paginated list of batches."
)
async def get_batches(
        search: Optional[str] = Query(None, description="Search by batch name"),
        sort_by: BatchSortField = Query(BatchSortField.CREATED_AT, description="Field to sort by"),
        sort_dir: SortDirection = Query(SortDirection.DESC, description="Sort direction (asc/desc)"),
        page: int = Query(1, ge=1, le=20, description="Page number"),
        size: int = Query(100, description="Page size"),
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Fetches all batches, optionally filtered, searched, and sorted."""
    return experiment_service.get_all_batches(
        page=page,
        size=size,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir
    )


@router.patch("/batch/{batch_id}",
              response_model=ExperimentBatchGetResponseDTO,
              summary="Update a single batch."
              )
async def update_batch(
        batch_id: int,
        batch_data: ExperimentBatchSingleUpdateRequestDTO,
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Updates batch."""
    batch = experiment_service.update_batch_by_id(
        batch_id=batch_id,
        request_dto=batch_data
    )
    return batch


@router.delete(
    "/batch/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a single batch."
)
async def delete_batch(
        batch_id: int,
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Deletes a batch from the database."""
    experiment_service.delete_batch(batch_id)
    return


@router.post(
    "/",
    response_model=ExperimentSingleCreateResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a single experiment and add it to the queue."
)
async def create_experiment(
        experiment_data: ExperimentSingleCreateRequestDTO,
        response: Response,
        dry_run: Optional[bool] = Query(False, description="Perform a dry run"),
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Creates a single experiment and adds it to the queue."""
    result = experiment_service.create_and_enqueue(request_dto=experiment_data, is_dry_run=dry_run)
    if result.errors:
        response.status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif result.is_dry_run:
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_201_CREATED
    return result


@router.get(
    "/{experiment_id}",
    response_model=ExperimentSingleGetResponseDTO,
    summary="Get a single experiment."
)
async def get_experiment(
        experiment_id: int,
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Fetches details for a specific experiment."""
    experiment = experiment_service.get_by_id(experiment_id)
    return experiment


@router.get(
    "/",
    response_model=ExperimentPaginatedGetResponseDTO,
    summary="Get a paginated list of experiments."
)
async def get_experiments(
        statuses: Optional[List[ExperimentStatus]] = Query(None, description="Filter by one or more statuses"),
        layout_types: Optional[List[LayoutType]] = Query(None, description="Filter by one or more layout types"),
        solver_types: Optional[List[SolverType]] = Query(None, description="Filter by one or more solver types"),
        batch_id: Optional[int] = Query(None, description="Filter by batch ID"),
        search: Optional[str] = Query(None, description="Search by experiment name"),
        sort_by: ExperimentSortField = Query(ExperimentSortField.CREATED_AT, description="Field to sort by"),
        sort_dir: SortDirection = Query(SortDirection.DESC, description="Sort direction (asc/desc)"),
        page: int = Query(1, ge=1, le=20, description="Page number"),
        size: int = Query(100, description="Page size"),
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Fetches all experiments, optionally filtered, searched, and sorted."""
    return experiment_service.get_all(
        page=page,
        size=size,
        statuses=statuses,
        layout_types=layout_types,
        solver_types=solver_types,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        batch_id=batch_id
    )


@router.patch("/{experiment_id}",
              response_model=ExperimentSingleGetResponseDTO,
              summary="Update a single experiment."
              )
async def update_experiment(
        experiment_id: int,
        experiment_data: ExperimentSingleUpdateRequestDTO,
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Updates experiment."""
    experiment = experiment_service.update_by_id(
        experiment_id=experiment_id,
        request_dto=experiment_data
    )
    return experiment


@router.delete(
    "/{experiment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a single experiment."
)
async def delete_experiment(
        experiment_id: int,
        experiment_service: ExperimentService = Depends(get_experiment_service)
):
    """Deletes an experiment from the database."""
    experiment_service.delete(experiment_id)
    return
