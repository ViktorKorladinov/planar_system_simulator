from typing import Callable

from sqlalchemy.orm import Session

from db.base_unit_of_work import BaseUnitOfWork
from db.repositories.postgresql_configuration_repository import PostgreSQLConfigurationRepository
from db.repositories.postgresql_experiment_repository import PostgreSQLExperimentRepository
from db.repositories.postgresql_ingredient_list_repository import PostgreSQLIngredientListRepository
from db.repositories.postgresql_layout_repository import PostgreSQLLayoutRepository
from db.repositories.postgresql_order_list_repository import PostgreSQLOrderListRepository


class PostgreSQLUnitOfWork(BaseUnitOfWork):
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def __enter__(self) -> 'BaseUnitOfWork':
        self.session = self.session_factory()
        self.experiment_repo = PostgreSQLExperimentRepository(self.session)
        self.configuration_repo = PostgreSQLConfigurationRepository(self.session)
        self.layout_repo = PostgreSQLLayoutRepository(self.session)
        self.order_list_repo = PostgreSQLOrderListRepository(self.session)
        self.ingredient_list_repo = PostgreSQLIngredientListRepository(self.session)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
