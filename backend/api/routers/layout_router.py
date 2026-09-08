from typing import Optional, List

from fastapi import APIRouter, status, Depends, Query, Response

from api.dtos.requests.layout import LayoutSingleCreateRequestDTO, LayoutSingleUpdateRequestDTO
from api.dtos.responses.layout import LayoutSingleCreateResponseDTO, LayoutBatchGetResponseDTO, \
    LayoutSingleGetResponseDTO
from dependencies import get_layout_service
from domain.enums import LayoutType, LayoutSortField, SortDirection, IngredientListType
from services.layout_service import LayoutService

router = APIRouter(
    prefix="/layouts",
    tags=["Layouts"]
)


@router.post(
    "/",
    response_model=LayoutSingleCreateResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a single layout."
)
async def create_layout(
        layout_data: LayoutSingleCreateRequestDTO,
        response: Response,
        dry_run: Optional[bool] = Query(False, description="Perform a dry run"),
        layout_service: LayoutService = Depends(get_layout_service)
):
    """Creates a single layout."""
    result = layout_service.create(request_dto=layout_data, is_dry_run=dry_run)
    if result.errors:
        response.status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif result.is_dry_run:
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_201_CREATED
    return result


@router.get(
    "/",
    response_model=LayoutBatchGetResponseDTO,
    summary="Get a paginated list of layouts."
)
async def get_layouts(
        layout_types: Optional[List[LayoutType]] = Query(None, description="Filter by one or more layout types"),
        ingredient_list_types: Optional[List[IngredientListType]] = Query(None,
                                                                          description="Filter by one or more ingredient list types"),
        search: Optional[str] = Query(None, description="Search by layout name"),
        sort_by: LayoutSortField = Query(LayoutSortField.CREATED_AT, description="Field to sort by"),
        sort_dir: SortDirection = Query(SortDirection.DESC, description="Sort direction (asc/desc)"),
        page: int = Query(1, ge=1, le=20, description="Page number"),
        size: int = Query(100, description="Page size"),
        layout_service: LayoutService = Depends(get_layout_service)
):
    """Fetches all layouts, optionally filtered, searched, and sorted."""
    return layout_service.get_all(
        page=page,
        size=size,
        layout_types=layout_types,
        ingredient_list_types=ingredient_list_types,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir
    )


@router.get(
    "/{layout_id}",
    response_model=LayoutSingleGetResponseDTO,
    summary="Get a single layout."
)
async def get_layout(
        layout_id: int,
        layout_service: LayoutService = Depends(get_layout_service)
):
    """Fetches details for a specific layout."""
    layout = layout_service.get_by_id(layout_id)
    return layout


@router.delete(
    "/{layout_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a single layout."
)
async def delete_layout(
        layout_id: int,
        layout_service: LayoutService = Depends(get_layout_service)
):
    """Deletes a layout from the database."""
    layout_service.delete(layout_id)
    return


@router.patch("/{layout_id}",
              response_model=LayoutSingleGetResponseDTO,
              summary="Update a single layout."
              )
async def update_layout(
        layout_id: int,
        layout_data: LayoutSingleUpdateRequestDTO,
        layout_service: LayoutService = Depends(get_layout_service)
):
    """Updates layout."""
    layout = layout_service.update_by_id(
        layout_id=layout_id,
        request_dto=layout_data
    )
    return layout
