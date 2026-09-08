from typing import Optional, List

from fastapi import APIRouter, status, Response, Query, Depends

from api.dtos.requests.ingredient_list import IngredientListSingleCreateRequestDTO, IngredientListSingleUpdateRequestDTO
from api.dtos.responses.ingredient_list import IngredientListSingleCreateResponseDTO, IngredientListBatchGetResponseDTO, \
    IngredientListSingleGetResponseDTO
from dependencies import get_ingredient_list_service
from domain.enums import IngredientListSortField, SortDirection, IngredientListType
from services.ingredient_list_service import IngredientListService

router = APIRouter(
    prefix="/ingredient_lists",
    tags=["Ingredient Lists"]
)


@router.post(
    "/",
    response_model=IngredientListSingleCreateResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a single ingredient list."
)
async def create_ingredient_list(
        ingredient_list_data: IngredientListSingleCreateRequestDTO,
        response: Response,
        dry_run: Optional[bool] = Query(False, description="Perform a dry run"),
        ingredient_list_service: IngredientListService = Depends(get_ingredient_list_service)
):
    """Creates a single ingredient list."""
    result = ingredient_list_service.create(request_dto=ingredient_list_data, is_dry_run=dry_run)
    if result.errors:
        response.status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif result.is_dry_run:
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_201_CREATED
    return result


@router.get(
    "/",
    response_model=IngredientListBatchGetResponseDTO,
    summary="Get a paginated list of ingredient lists."
)
async def get_ingredient_lists(
        types: Optional[List[IngredientListType]] = Query(None,
                                                          description="Filter by one or more ingredient list types"),
        page: int = Query(1, ge=1, description="Page number for the pagination."),
        size: int = Query(20, ge=1, le=100, description="Number of items to return per page."),
        search: Optional[str] = Query(None, description="Search by ingredient list name"),
        sort_by: IngredientListSortField = Query(IngredientListSortField.CREATED_AT, description="Field to sort by"),
        sort_dir: SortDirection = Query(SortDirection.DESC, description="Sort direction (asc/desc)"),
        ingredient_list_service: IngredientListService = Depends(get_ingredient_list_service)
):
    """Fetches all ingredient lists, optionally filtered, searched, and sorted."""
    return ingredient_list_service.get_all(
        page=page,
        size=size,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        types=types
    )


@router.get(
    "/{ingredient_list_id}",
    response_model=IngredientListSingleGetResponseDTO,
    summary="Get a single ingredient list."
)
async def get_ingredient_list(
        ingredient_list_id: int,
        ingredient_list_service: IngredientListService = Depends(get_ingredient_list_service)
):
    """Fetches details for a specific ingredient list."""
    ingredient_list = ingredient_list_service.get_by_id(ingredient_list_id)
    return ingredient_list


@router.delete(
    "/{ingredient_list_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a single ingredient list."
)
async def delete_ingredient_list(
        ingredient_list_id: int,
        ingredient_list_service: IngredientListService = Depends(get_ingredient_list_service)
):
    """Deletes an ingredient list from the database."""
    ingredient_list_service.delete(ingredient_list_id)
    return


@router.patch("/{ingredient_list_id}",
              response_model=IngredientListSingleGetResponseDTO,
              summary="Update a single ingredient list."
              )
async def update_ingredient_list(
        ingredient_list_id: int,
        ingredient_list_data: IngredientListSingleUpdateRequestDTO,
        ingredient_list_service: IngredientListService = Depends(get_ingredient_list_service)
):
    """Updates ingredient list."""
    ingredient_list = ingredient_list_service.update_by_id(
        ingredient_list_id=ingredient_list_id,
        request_dto=ingredient_list_data
    )
    return ingredient_list
