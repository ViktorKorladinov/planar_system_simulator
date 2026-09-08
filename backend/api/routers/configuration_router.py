from typing import Optional, List

from fastapi import APIRouter, status, Depends, Query, Response

from api.dtos.requests.configuration import ConfigurationSingleCreateRequestDTO, ConfigurationSingleUpdateRequestDTO
from api.dtos.responses.configuration import ConfigurationSingleCreateResponseDTO, ConfigurationBatchGetResponseDTO, \
    ConfigurationSingleGetResponseDTO
from dependencies import get_configuration_service
from domain.enums import SolverType, ConfigurationSortField, SortDirection
from services.configuration_service import ConfigurationService

router = APIRouter(
    prefix="/configurations",
    tags=["Configurations"]
)


@router.post(
    "/",
    response_model=ConfigurationSingleCreateResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a single configuration."
)
async def create_configuration(
        configuration_data: ConfigurationSingleCreateRequestDTO,
        response: Response,
        dry_run: Optional[bool] = Query(False, description="Perform a dry run"),
        configuration_service: ConfigurationService = Depends(get_configuration_service)
):
    """Creates a single configuration."""
    result = configuration_service.create(request_dto=configuration_data, is_dry_run=dry_run)
    if result.errors:
        response.status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif result.is_dry_run:
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_201_CREATED
    return result


@router.get(
    "/",
    response_model=ConfigurationBatchGetResponseDTO,
    summary="Get a paginated list of configurations."
)
async def get_configurations(
        solver_types: Optional[List[SolverType]] = Query(None, description="Filter by one or more solver types"),
        search: Optional[str] = Query(None, description="Search by configuration name"),
        sort_by: ConfigurationSortField = Query(ConfigurationSortField.CREATED_AT, description="Field to sort by"),
        sort_dir: SortDirection = Query(SortDirection.DESC, description="Sort direction (asc/desc)"),
        page: int = Query(1, ge=1, le=20, description="Page number"),
        size: int = Query(100, description="Page size"),
        configuration_service: ConfigurationService = Depends(get_configuration_service)
):
    """Fetches all configurations, optionally filtered, searched, and sorted."""
    return configuration_service.get_all(
        page=page,
        size=size,
        solver_types=solver_types,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir
    )


@router.get(
    "/{configuration_id}",
    response_model=ConfigurationSingleGetResponseDTO,
    summary="Get a single configuration."
)
async def get_configuration(
        configuration_id: int,
        configuration_service: ConfigurationService = Depends(get_configuration_service)
):
    """Fetches details for a specific configuration."""
    configuration = configuration_service.get_by_id(configuration_id)
    return configuration


@router.delete(
    "/{configuration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a single configuration."
)
async def delete_configuration(
        configuration_id: int,
        configuration_service: ConfigurationService = Depends(get_configuration_service)
):
    """Deletes a configuration from the database."""
    configuration_service.delete(configuration_id)
    return


@router.patch("/{configuration_id}",
              response_model=ConfigurationSingleGetResponseDTO,
              summary="Update a single configuration."
              )
async def update_configuration(
        configuration_id: int,
        configuration_data: ConfigurationSingleUpdateRequestDTO,
        configuration_service: ConfigurationService = Depends(get_configuration_service)
):
    """Updates configuration."""
    configuration = configuration_service.update_by_id(
        configuration_id=configuration_id,
        request_dto=configuration_data
    )
    return configuration
