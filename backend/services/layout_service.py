import math
from typing import Optional, List

from pydantic import ValidationError

from api.dtos.common.ingredient_list_dto import IngredientListDTO
from api.dtos.requests.layout import LayoutSingleCreateRequestDTO, LayoutSingleUpdateRequestDTO
from api.dtos.responses.layout import LayoutSingleCreateResponseDTO, LayoutBatchGetResponseDTO, \
    LayoutSingleGetResponseDTO
from core.exceptions import EntityNotFoundError
from db.base_unit_of_work import BaseUnitOfWork
from domain.enums import LayoutType, LayoutSortField, SortDirection, IngredientListType
from domain.models.ingredient_list import IngredientListDomainModel
from domain.models.layout import LayoutDomainModel
from mappers.domain.ingredient_list_mapper import map_ingredient_list_dto_to_domain
from mappers.domain.layout_mapper import map_layout_single_create_request_dto_to_domain, \
    map_layout_domain_to_single_create_response_dto, \
    map_layout_domain_to_batch_get_response_dto, map_layout_domain_to_single_get_response_dto


class LayoutService:
    """Orchestrates business use cases for Layout entities."""

    def __init__(self, uow: BaseUnitOfWork):
        self.uow = uow

    def _set_default_layout_name(self, domain_model: LayoutDomainModel):
        """Sets default name for layout if not provided.

        Args:
            domain_model: Domain model for which name should be set.
        """
        if domain_model.name is None and domain_model.id is not None:
            domain_model.name = f"Layout ({domain_model.id})"
            self.uow.layout_repo.update(domain_model)

    def _set_default_ingredient_list_name(self, domain_model: IngredientListDomainModel) -> None:
        """Sets default name for ingredient list if not provided.

        Args:
            domain_model: Domain model for which name should be set.
        """
        if domain_model.name is None and domain_model.id is not None:
            domain_model.name = f"Ingredient List ({domain_model.id})"
            self.uow.ingredient_list_repo.update(domain_model)

    def _resolve_ingredient_list(self, ingredient_list_id: Optional[int],
                                 ingredient_list: Optional[IngredientListDTO]) -> IngredientListDomainModel:
        """Returns ingredient list domain model chosen for the layout.

        Args:
            ingredient_list_id: Ingredient list ID.
            ingredient_list: Ingredient list.

        Returns:
            Ingredient list domain model for the layout.

        Raises:
            ValueError: If invalid layout ID is provided.
        """
        if ingredient_list_id is not None:
            ingredient_list_domain_model = self.uow.ingredient_list_repo.find_by_id(ingredient_list_id)
            if ingredient_list_domain_model is None:
                raise EntityNotFoundError(entity_name="Ingredient List", entity_id=ingredient_list_id)
            return ingredient_list_domain_model
        else:
            ingredient_list_domain_model = map_ingredient_list_dto_to_domain(ingredient_list)
            return self.uow.ingredient_list_repo.create(ingredient_list_domain_model)

    def create(
            self,
            request_dto: LayoutSingleCreateRequestDTO,
            is_dry_run: bool) -> LayoutSingleCreateResponseDTO:
        """Processes a request to create a new layout.

        Args:
            request_dto: The data transfer object containing the new layout data.
            is_dry_run: Indicates whether the layout should be created or only validated.

        Returns:
            A response DTO representing the successfully created layout.
        """
        errors = []
        with self.uow:
            try:
                domain_model = map_layout_single_create_request_dto_to_domain(
                    dto=request_dto,
                    ingredient_list_domain_model=self._resolve_ingredient_list(
                        ingredient_list_id=request_dto.ingredient_list_id,
                        ingredient_list=request_dto.ingredient_list
                    )
                )
            except ValidationError as e:
                for error in e.errors():
                    clean_msg = error['msg'].replace("Value error, ", "")
                    errors.append(clean_msg)
                return map_layout_domain_to_single_create_response_dto(
                    domain_model=None,
                    errors=errors,
                    is_dry_run=is_dry_run
                )
            if is_dry_run:
                return map_layout_domain_to_single_create_response_dto(
                    domain_model=domain_model,
                    errors=errors,
                    is_dry_run=is_dry_run
                )
            domain_model = self.uow.layout_repo.create(domain_model)
            self._set_default_layout_name(domain_model)
            self._set_default_ingredient_list_name(domain_model.ingredient_list)
            self.uow.commit()
        return map_layout_domain_to_single_create_response_dto(
            domain_model=domain_model,
            is_dry_run=is_dry_run,
            errors=errors
        )

    def get_all(self,
                page: int = 1,
                size: int = 20,
                layout_types: Optional[List[LayoutType]] = None,
                ingredient_list_types: Optional[List[IngredientListType]] = None,
                search: Optional[str] = None,
                sort_by: LayoutSortField = LayoutSortField.CREATED_AT,
                sort_dir: SortDirection = SortDirection.ASC) -> LayoutBatchGetResponseDTO:
        """Retrieves a paginated batch of layouts.

        Args:
            page: Page number.
            size: Amount of layouts on one page.
            layout_types: An optional list of layout types to filter by.
            ingredient_list_types: An optional list of ingredient list types to filter by.
            search: An optional search string to filter by name.
            sort_by: An optional sort field to sort by.
            sort_dir: An optional sort direction to sort by.

        Returns:
            A batch response DTO containing the list of layouts.
        """
        skip = (page - 1) * size
        limit = size
        total = 0
        with self.uow:
            domain_models = self.uow.layout_repo.find_all(
                skip=skip,
                limit=limit,
                layout_types=layout_types,
                ingredient_list_types=ingredient_list_types,
                search=search,
                sort_by=sort_by,
                sort_dir=sort_dir
            )
            total = self.uow.layout_repo.get_layout_count(
                layout_types=layout_types,
                search=search
            )
        return map_layout_domain_to_batch_get_response_dto(
            domain_models=domain_models,
            page=page,
            size=size,
            total=int(math.ceil(total / size))
        )

    def get_by_id(self, layout_id: int) -> Optional[LayoutSingleGetResponseDTO]:
        """Fetches a single layout by its unique identifier.

        Args:
            layout_id: The ID of the requested layout.

        Returns:
            A response DTO if the layout exists, otherwise None.

        Raises:
            EntityNotFoundError: If the layout was not found.
        """
        with self.uow:
            domain_model = self.uow.layout_repo.find_by_id(layout_id)
        if domain_model is None:
            raise EntityNotFoundError(entity_name="Layout", entity_id=layout_id)
        return map_layout_domain_to_single_get_response_dto(domain_model)

    def delete(self, layout_id: int) -> bool:
        """Attempts to delete a layout by its unique identifier.

        Args:
            layout_id: The ID of the layout to remove.

        Returns:
            True if the layout was successfully deleted, False if it was not found.

        Raises:
            EntityNotFoundError: If the layout was not found.
        """
        with self.uow:
            success = self.uow.layout_repo.delete(layout_id)
            if not success:
                raise EntityNotFoundError(entity_name="Layout", entity_id=layout_id)
            self.uow.commit()
        return success

    def update_by_id(self, layout_id: int, request_dto: LayoutSingleUpdateRequestDTO) -> Optional[
        LayoutSingleGetResponseDTO]:
        """Updates a single layout by its unique identifier.

        Args:
            layout_id: ID of the layout which should be updated.
            request_dto: Request DTO with updated layout details.

        Returns:
            True if the layout was successfully updated, False otherwise.

        Raises:
            EntityNotFoundError: If the layout was not found.
        """
        with self.uow:
            layout = self.uow.layout_repo.find_by_id(layout_id)
            if layout is None:
                raise EntityNotFoundError(entity_name="Layout", entity_id=layout_id)
            layout.name = request_dto.name
            success = self.uow.layout_repo.update(layout)
            if success is None:
                return None
            self.uow.commit()
            return map_layout_domain_to_single_get_response_dto(layout)
