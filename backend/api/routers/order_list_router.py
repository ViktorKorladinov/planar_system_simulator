from typing import Optional, List

from fastapi import APIRouter, status, Depends, Query, Response

from api.dtos.requests.order_list import OrderListSingleCreateRequestDTO, OrderListSingleUpdateRequestDTO
from api.dtos.responses.order_list import OrderListSingleCreateResponseDTO, OrderListBatchGetResponseDTO, \
    OrderListSingleGetResponseDTO
from dependencies import get_order_list_service
from domain.enums import OrderListSortField, SortDirection, OrderListType
from services.order_list_service import OrderListService

router = APIRouter(
    prefix="/order_lists",
    tags=["Order Lists"]
)


@router.post(
    "/",
    response_model=OrderListSingleCreateResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a single order list."
)
async def create_order_list(
        order_list_data: OrderListSingleCreateRequestDTO,
        response: Response,
        dry_run: Optional[bool] = Query(False, description="Perform a dry run"),
        order_list_service: OrderListService = Depends(get_order_list_service)
):
    """Creates a single order list."""
    result = order_list_service.create(request_dto=order_list_data, is_dry_run=dry_run)
    if result.errors:
        response.status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif result.is_dry_run:
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_201_CREATED
    return result


@router.get(
    "/",
    response_model=OrderListBatchGetResponseDTO,
    summary="Get a paginated list of order lists."
)
async def get_order_lists(
        types: Optional[List[OrderListType]] = Query(None, description="Filter by one or more order list types"),
        page: int = Query(1, ge=1, description="Page number for the pagination."),
        size: int = Query(20, ge=1, le=100, description="Number of items to return per page."),
        search: Optional[str] = Query(None, description="Search by order list name"),
        sort_by: OrderListSortField = Query(OrderListSortField.CREATED_AT, description="Field to sort by"),
        sort_dir: SortDirection = Query(SortDirection.DESC, description="Sort direction (asc/desc)"),
        order_list_service: OrderListService = Depends(get_order_list_service)
):
    """Fetches all order lists, optionally filtered, searched, and sorted."""
    return order_list_service.get_all(
        page=page,
        size=size,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        types=types
    )


@router.get(
    "/{order_list_id}",
    response_model=OrderListSingleGetResponseDTO,
    summary="Get a single order list."
)
async def get_order_list(
        order_list_id: int,
        order_list_service: OrderListService = Depends(get_order_list_service)
):
    """Fetches details for a specific order list."""
    order_list = order_list_service.get_by_id(order_list_id)
    return order_list


@router.delete(
    "/{order_list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a single order list."
)
async def delete_order_list(
        order_list_id: int,
        order_list_service: OrderListService = Depends(get_order_list_service)
):
    """Deletes an order list from the database."""
    order_list_service.delete(order_list_id)
    return


@router.patch("/{order_list_id}",
              response_model=OrderListSingleGetResponseDTO,
              summary="Update a single order list."
              )
async def update_order_list(
        order_list_id: int,
        order_list_data: OrderListSingleUpdateRequestDTO,
        order_list_service: OrderListService = Depends(get_order_list_service)
):
    """Updates order list."""
    order_list = order_list_service.update_by_id(
        order_list_id=order_list_id,
        request_dto=order_list_data
    )
    return order_list
