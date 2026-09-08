from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional, Type

from db.repositories.base_configuration_repository import BaseConfigurationRepository
from db.repositories.base_experiment_repository import BaseExperimentRepository
from db.repositories.base_ingredient_list_repository import BaseIngredientListRepository
from db.repositories.base_layout_repository import BaseLayoutRepository
from db.repositories.base_order_list_repository import BaseOrderListRepository


class BaseUnitOfWork(ABC):
    experiment_repo: 'BaseExperimentRepository'
    configuration_repo: 'BaseConfigurationRepository'
    layout_repo: 'BaseLayoutRepository'
    order_list_repo: 'BaseOrderListRepository'
    ingredient_list_repo: 'BaseIngredientListRepository'

    def __enter__(self) -> 'BaseUnitOfWork':
        return self

    def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType]
    ) -> None:
        if exc_type:
            self.rollback()

    @abstractmethod
    def commit(self) -> None:
        """Commits the transaction."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rolls back the transaction."""
        pass
