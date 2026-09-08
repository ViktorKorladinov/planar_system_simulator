from abc import ABC, abstractmethod
from typing import Optional, List

from domain.enums import LayoutType, LayoutSortField, SortDirection, IngredientListType
from domain.models.layout import LayoutDomainModel


class BaseLayoutRepository(ABC):
    @abstractmethod
    def create(self, layout: LayoutDomainModel) -> LayoutDomainModel:
        """Persists a new layout to the storage.

        Args:
            layout: The model containing layout details.

        Returns:
            The saved layout model, populated with its generated ID.
        """

    @abstractmethod
    def find_by_id(self, layout_id: int) -> Optional[LayoutDomainModel]:
        """Retrieves a layout by its unique identifier.

        Args:
            layout_id: The ID of the layout to find.

        Returns:
            The layout model if found, otherwise None.
        """

    @abstractmethod
    def find_all(
            self,
            skip: int = 0,
            limit: int = 100,
            layout_types: Optional[List[LayoutType]] = None,
            ingredient_list_types: Optional[List[IngredientListType]] = None,
            search: Optional[str] = None,
            sort_by: LayoutSortField = LayoutSortField.CREATED_AT,
            sort_dir: SortDirection = SortDirection.ASC) -> List[LayoutDomainModel]:
        """Retrieves a paginated list of layouts.

        Args:
            skip: The number of records to skip (for pagination).
            limit: The maximum number of records to return.
            layout_types: An optional list of layout types to filter by.
            ingredient_list_types: An optional list of ingredient list types to filter by.
            search: An optional search string to filter by name.
            sort_by: An optional sort field to sort by.
            sort_dir: An optional sort direction to sort by.

        Returns:
            A list of layout domain models matching the criteria.
        """

    @abstractmethod
    def delete(self, layout_id: int) -> bool:
        """Removes a layout from the storage.

        Args:
            layout_id: The ID of the layout to delete.

        Returns:
            True if the layout was successfully deleted, False otherwise.
        """

    @abstractmethod
    def get_layout_count(
            self,
            layout_types: Optional[List[LayoutType]] = None,
            search: Optional[str] = None
    ) -> int:
        """Returns the amount of layouts in the database.

        Args:
            layout_types: An optional list of layout types to filter by.
            search: An optional search string to filter by name.

        Returns:
            The amount of layouts matching filters in the database.
        """

    @abstractmethod
    def update(self, layout: LayoutDomainModel) -> Optional[LayoutDomainModel]:
        """Updates an existing layout in the storage.

        Args:
            layout: The model containing updated values.

        Returns:
            The updated model, or None if the layout was not found.
        """
