from abc import abstractmethod, ABC
from typing import Optional, List

from domain.enums import OrderListSortField, SortDirection, OrderListType
from domain.models.order_list import OrderListDomainModel


class BaseOrderListRepository(ABC):
    @abstractmethod
    def create(self, order_list: OrderListDomainModel) -> OrderListDomainModel:
        """Persists a new order list to the storage.

        Args:
            order_list: The model containing order list details.

        Returns:
            The saved order list model, populated with its generated ID.
        """

    @abstractmethod
    def find_by_id(self, order_list_id: int) -> Optional[OrderListDomainModel]:
        """Retrieves an order list by its unique identifier.

        Args:
            order_list_id: The ID of the order list to find.

        Returns:
            The order list model if found, otherwise None.
        """

    @abstractmethod
    def find_all(
            self,
            skip: int = 0,
            limit: int = 100,
            types: Optional[List[OrderListType]] = None,
            search: Optional[str] = None,
            sort_by: OrderListSortField = OrderListSortField.CREATED_AT,
            sort_dir: SortDirection = SortDirection.ASC
    ) -> List[OrderListDomainModel]:
        """Retrieves a paginated list of order lists.

        Args:
            skip: The number of records to skip (for pagination).
            limit: The maximum number of records to return.
            types: An optional list of order list types to filter by.
            search: An optional search string to filter by name.
            sort_by: An optional sort field to sort by.
            sort_dir: An optional sort direction to sort by.

        Returns:
            A list of order list domain models matching the criteria.
        """

    @abstractmethod
    def delete(self, order_list_id: int) -> bool:
        """Removes an order list from the storage.

        Args:
            order_list_id: The ID of the order list to delete.

        Returns:
            True if the order list was successfully deleted, False otherwise.
        """

    @abstractmethod
    def get_order_list_count(
            self,
            search: Optional[str] = None
    ) -> int:
        """Returns the amount of order lists in the database.

        Args:
            search: An optional search string to filter by name.

        Returns:
            The amount of order lists matching filters in the database.
        """

    @abstractmethod
    def update(self, order_list: OrderListDomainModel) -> Optional[OrderListDomainModel]:
        """Updates an existing order list in the storage.

        Args:
            order_list: The model containing updated values.

        Returns:
            The updated model, or None if the order list was not found.
        """
