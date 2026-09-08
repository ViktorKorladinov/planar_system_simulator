import math
from typing import Optional, List

from pydantic import ValidationError

from api.dtos.requests.order_list import OrderListSingleCreateRequestDTO, OrderListSingleUpdateRequestDTO
from api.dtos.responses.order_list import OrderListSingleCreateResponseDTO, OrderListBatchGetResponseDTO, \
    OrderListSingleGetResponseDTO
from core.exceptions import EntityNotFoundError
from db.base_unit_of_work import BaseUnitOfWork
from domain.enums import OrderListSortField, SortDirection, OrderListType
from domain.models.order_list import OrderListDomainModel
from mappers.domain.order_list_mapper import map_order_list_domain_to_batch_get_response_dto, \
    map_order_list_domain_to_single_get_response_dto, map_order_list_domain_to_single_create_response_dto, \
    map_order_list_single_create_request_dto_to_domain


class OrderListService:
    """Orchestrates business use cases for Order List entities."""

    def __init__(self, uow: BaseUnitOfWork):
        self.uow = uow

    def _set_default_name(self, domain_model: OrderListDomainModel):
        """Sets default name for order list if not provided.

        Args:
            domain_model: Domain model for which name should be set.
        """
        if domain_model.name is None and domain_model.id is not None:
            with self.uow:
                domain_model.name = f"Order List ({domain_model.id})"
                self.uow.order_list_repo.update(domain_model)
                self.uow.commit()

    def create(
            self,
            request_dto: OrderListSingleCreateRequestDTO,
            is_dry_run: bool
    ) -> OrderListSingleCreateResponseDTO:
        """Processes a request to create a new order list.

        Args:
            request_dto: The data transfer object containing the new order list data.
            is_dry_run: Indicates whether the order list should be created or only validated.

        Returns:
            A response DTO representing the successfully created order list.
        """
        errors = []
        with self.uow:
            try:
                domain_model = map_order_list_single_create_request_dto_to_domain(request_dto)
            except ValidationError as e:
                for error in e.errors():
                    clean_msg = error['msg'].replace("Value error, ", "")
                    errors.append(clean_msg)
                return map_order_list_domain_to_single_create_response_dto(
                    domain_model=None,
                    errors=errors,
                    is_dry_run=is_dry_run
                )
            if is_dry_run:
                return map_order_list_domain_to_single_create_response_dto(
                    domain_model=domain_model,
                    errors=errors,
                    is_dry_run=is_dry_run
                )
            domain_model = self.uow.order_list_repo.create(domain_model)
            self.uow.commit()
        self._set_default_name(domain_model)
        return map_order_list_domain_to_single_create_response_dto(
            domain_model=domain_model,
            is_dry_run=is_dry_run,
            errors=errors
        )

    def get_all(self,
                page: Optional[int] = 1,
                size: Optional[int] = 20,
                types: Optional[List[OrderListType]] = None,
                search: Optional[str] = None,
                sort_by: OrderListSortField = OrderListSortField.CREATED_AT,
                sort_dir: SortDirection = SortDirection.ASC
                ) -> OrderListBatchGetResponseDTO:
        """Retrieves a paginated batch of order lists.

        Args:
            page: The number of the page for which order lists should be retrieved.
            size: Max amount of order lists on one page.
            search: An optional search string to filter by name.
            sort_by: An optional sort field to sort by.
            sort_dir: An optional sort direction to sort by.
            types: An optional list of order list types to filter by.

        Returns:
            An order list batch response DTO containing the list of order lists on desired page.
        """
        skip = (page - 1) * size
        limit = size
        total = 0
        with self.uow:
            domain_models = self.uow.order_list_repo.find_all(
                skip=skip,
                limit=limit,
                search=search,
                sort_by=sort_by,
                sort_dir=sort_dir,
                types=types
            )
            total = self.uow.order_list_repo.get_order_list_count(
                search=search
            )
        return map_order_list_domain_to_batch_get_response_dto(
            domain_models=domain_models,
            total_pages=int(math.ceil(total / size)),
            page=page,
            size=size
        )

    def get_by_id(self, order_list_id: int) -> Optional[OrderListSingleGetResponseDTO]:
        """Fetches a single order list by its unique identifier.

        Args:
            order_list_id: The ID of the requested order list.

        Returns:
            A response DTO if the order list exists, otherwise None.
        """
        with self.uow:
            domain_model = self.uow.order_list_repo.find_by_id(order_list_id)
        if domain_model is None:
            raise EntityNotFoundError(entity_name="Order List", entity_id=order_list_id)
        return map_order_list_domain_to_single_get_response_dto(domain_model)

    def delete(self, order_list_id: int) -> bool:
        """Attempts to delete an order list by its unique identifier.

        Args:
            order_list_id: The ID of the order list to remove.

        Returns:
            True if the order list was successfully deleted, False if it was not found.
        """
        with self.uow:
            success = self.uow.order_list_repo.delete(order_list_id)
            if not success:
                raise EntityNotFoundError(entity_name="Order List", entity_id=order_list_id)
            self.uow.commit()
        return success

    def update_by_id(self, order_list_id: int, request_dto: OrderListSingleUpdateRequestDTO) -> Optional[
        OrderListSingleGetResponseDTO]:
        """Updates a single order list by its unique identifier.

        Args:
            order_list_id: ID of the order list which should be updated.
            request_dto: Request DTO with updated order list details.

        Returns:
            True if the order list was successfully updated, False otherwise.

        Raises:
            EntityNotFoundError: If the order list was not found.
        """
        with self.uow:
            order_list = self.uow.order_list_repo.find_by_id(order_list_id)
            if order_list is None:
                raise EntityNotFoundError(entity_name="Order List", entity_id=order_list_id)
            order_list.name = request_dto.name
            success = self.uow.order_list_repo.update(order_list)
            if success is None:
                return None
            self.uow.commit()
            return map_order_list_domain_to_single_get_response_dto(order_list)
