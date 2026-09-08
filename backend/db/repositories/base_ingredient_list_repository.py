from abc import abstractmethod, ABC
from typing import Optional, List

from domain.enums import IngredientListSortField, SortDirection, IngredientListType
from domain.models.ingredient_list import IngredientListDomainModel


class BaseIngredientListRepository(ABC):
    @abstractmethod
    def create(self, ingredient_list: IngredientListDomainModel) -> IngredientListDomainModel:
        """Persists a new ingredient list to the storage.

        Args:
            ingredient_list: The model containing ingredient list details.

        Returns:
            The saved ingredient list model, populated with its generated ID.
        """

    @abstractmethod
    def find_by_id(self, ingredient_list_id: int) -> Optional[IngredientListDomainModel]:
        """Retrieves an ingredient list by its unique identifier.

        Args:
            ingredient_list_id: The ID of the ingredient list to find.

        Returns:
            The ingredient list model if found, otherwise None.
        """

    @abstractmethod
    def find_all(
            self,
            skip: int = 0,
            limit: int = 100,
            types: Optional[List[IngredientListType]] = None,
            search: Optional[str] = None,
            sort_by: IngredientListSortField = IngredientListSortField.CREATED_AT,
            sort_dir: SortDirection = SortDirection.ASC
    ) -> List[IngredientListDomainModel]:
        """Retrieves a paginated list of ingredient lists.

        Args:
            skip: The number of records to skip (for pagination).
            limit: The maximum number of records to return.
            types: An optional list of ingredient list types to filter by.
            search: An optional search string to filter by name.
            sort_by: An optional sort field to sort by.
            sort_dir: An optional sort direction to sort by.

        Returns:
            A list of ingredient list domain models matching the criteria.
        """

    @abstractmethod
    def delete(self, ingredient_list_id: int) -> bool:
        """Removes an ingredient list from the storage.

        Args:
            ingredient_list_id: The ID of the ingredient list to delete.

        Returns:
            True if the ingredient list was successfully deleted, False otherwise.
        """

    @abstractmethod
    def get_ingredient_list_count(
            self,
            search: Optional[str] = None
    ) -> int:
        """Returns the amount of ingredient lists in the database.

        Args:
            search: An optional search string to filter by name.

        Returns:
            The amount of ingredient lists matching filters in the database.
        """

    @abstractmethod
    def update(self, ingredient_list: IngredientListDomainModel) -> Optional[IngredientListDomainModel]:
        """Updates an existing ingredient list in the storage.

        Args:
            ingredient_list: The model containing updated values.

        Returns:
            The updated model, or None if the ingredient list was not found.
        """
