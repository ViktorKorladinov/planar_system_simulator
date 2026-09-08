import math
from typing import Optional, List

from pydantic import ValidationError

from api.dtos.requests.ingredient_list import IngredientListSingleCreateRequestDTO, IngredientListSingleUpdateRequestDTO
from api.dtos.responses.ingredient_list import IngredientListSingleCreateResponseDTO, IngredientListBatchGetResponseDTO, \
    IngredientListSingleGetResponseDTO
from core.exceptions import EntityNotFoundError
from db.base_unit_of_work import BaseUnitOfWork
from domain.enums import IngredientListSortField, SortDirection, IngredientListType
from domain.models.ingredient_list import IngredientListDomainModel
from mappers.domain.ingredient_list_mapper import map_ingredient_list_single_create_request_dto_to_domain, \
    map_ingredient_list_domain_to_single_create_response_dto, map_ingredient_list_domain_to_batch_get_response_dto, \
    map_ingredient_list_domain_to_single_get_response_dto


class IngredientListService:
    """Orchestrates business use cases for Ingredient List entities."""

    def __init__(self, uow: BaseUnitOfWork):
        self.uow = uow

    def _set_default_name(self, domain_model: IngredientListDomainModel):
        """Sets default name for ingredient list if not provided.

        Args:
            domain_model: Domain model for which name should be set.
        """
        if domain_model.name is None and domain_model.id is not None:
            with self.uow:
                domain_model.name = f"Ingredient List ({domain_model.id})"
                self.uow.ingredient_list_repo.update(domain_model)
                self.uow.commit()

    def create(
            self,
            request_dto: IngredientListSingleCreateRequestDTO,
            is_dry_run: bool
    ) -> IngredientListSingleCreateResponseDTO:
        """Processes a request to create a new ingredient list.

        Args:
            request_dto: The data transfer object containing the new ingredient list data.
            is_dry_run: Indicates whether the ingredient list should be created or only validated.

        Returns:
            A response DTO representing the successfully created ingredient list.
        """
        errors = []
        with self.uow:
            try:
                domain_model = map_ingredient_list_single_create_request_dto_to_domain(request_dto)
            except ValidationError as e:
                for error in e.errors():
                    clean_msg = error['msg'].replace("Value error, ", "")
                    errors.append(clean_msg)
                return map_ingredient_list_domain_to_single_create_response_dto(
                    domain_model=None,
                    errors=errors,
                    is_dry_run=is_dry_run
                )
            if is_dry_run:
                return map_ingredient_list_domain_to_single_create_response_dto(
                    domain_model=domain_model,
                    errors=errors,
                    is_dry_run=is_dry_run
                )
            domain_model = self.uow.ingredient_list_repo.create(domain_model)
            self.uow.commit()
        self._set_default_name(domain_model)
        return map_ingredient_list_domain_to_single_create_response_dto(
            domain_model=domain_model,
            is_dry_run=is_dry_run,
            errors=errors
        )

    def get_all(self,
                page: Optional[int] = 1,
                size: Optional[int] = 20,
                types: Optional[List[IngredientListType]] = None,
                search: Optional[str] = None,
                sort_by: IngredientListSortField = IngredientListSortField.CREATED_AT,
                sort_dir: SortDirection = SortDirection.ASC
                ) -> IngredientListBatchGetResponseDTO:
        """Retrieves a paginated batch of ingredient lists.

        Args:
            page: The number of the page for which ingredient lists should be retrieved.
            size: Max amount of ingredient lists on one page.
            search: An optional search string to filter by name.
            sort_by: An optional sort field to sort by.
            sort_dir: An optional sort direction to sort by.
            types: An optional list of ingredient list types to filter by.

        Returns:
            An ingredient list batch response DTO containing the list of ingredient lists on desired page.
        """
        skip = (page - 1) * size
        limit = size
        total = 0
        with self.uow:
            domain_models = self.uow.ingredient_list_repo.find_all(
                skip=skip,
                limit=limit,
                search=search,
                sort_by=sort_by,
                sort_dir=sort_dir,
                types=types
            )
            total = self.uow.ingredient_list_repo.get_ingredient_list_count(
                search=search
            )
        return map_ingredient_list_domain_to_batch_get_response_dto(
            domain_models=domain_models,
            total_pages=int(math.ceil(total / size)),
            page=page,
            size=size
        )

    def get_by_id(self, ingredient_list_id: int) -> Optional[IngredientListSingleGetResponseDTO]:
        """Fetches a single ingredient list by its unique identifier.

        Args:
            ingredient_list_id: The ID of the requested ingredient list.

        Returns:
            A response DTO if the ingredient list exists, otherwise None.
        """
        with self.uow:
            domain_model = self.uow.ingredient_list_repo.find_by_id(ingredient_list_id)
        if domain_model is None:
            raise EntityNotFoundError(entity_name="Ingredient List", entity_id=ingredient_list_id)
        return map_ingredient_list_domain_to_single_get_response_dto(domain_model)

    def delete(self, ingredient_list_id: int) -> bool:
        """Attempts to delete an ingredient list by its unique identifier.

        Args:
            ingredient_list_id: The ID of the ingredient list to remove.

        Returns:
            True if the ingredient list was successfully deleted, False if it was not found.
        """
        with self.uow:
            success = self.uow.ingredient_list_repo.delete(ingredient_list_id)
            if not success:
                raise EntityNotFoundError(entity_name="Ingredient List", entity_id=ingredient_list_id)
            self.uow.commit()
        return success

    def update_by_id(self, ingredient_list_id: int, request_dto: IngredientListSingleUpdateRequestDTO) -> Optional[
        IngredientListSingleGetResponseDTO]:
        """Updates a single ingredient list by its unique identifier.

        Args:
            ingredient_list_id: ID of the ingredient list which should be updated.
            request_dto: Request DTO with updated ingredient list details.

        Returns:
            True if the ingredient list was successfully updated, False otherwise.

        Raises:
            EntityNotFoundError: If the ingredient list was not found.
        """
        with self.uow:
            ingredient_list = self.uow.ingredient_list_repo.find_by_id(ingredient_list_id)
            if ingredient_list is None:
                raise EntityNotFoundError(entity_name="Ingredient List", entity_id=ingredient_list_id)
            ingredient_list.name = request_dto.name
            success = self.uow.ingredient_list_repo.update(ingredient_list)
            if success is None:
                return None
            self.uow.commit()
            return map_ingredient_list_domain_to_single_get_response_dto(ingredient_list)
