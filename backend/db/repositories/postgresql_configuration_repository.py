from typing import Optional, List, Any

from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import EntityInUseError
from db.orm_models.configuration import ConfigurationORM
from db.repositories.base_configuration_repository import BaseConfigurationRepository
from domain.enums import SolverType, ConfigurationSortField, SortDirection
from domain.models.configuration import ConfigurationDomainModel
from mappers.orm.configuration_mapper import map_configuration_domain_to_orm, map_configuration_orm_to_domain, \
    update_configuration_orm


class PostgreSQLConfigurationRepository(BaseConfigurationRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, configuration: ConfigurationDomainModel) -> ConfigurationDomainModel:
        configuration_orm = map_configuration_domain_to_orm(domain_model=configuration)
        self.session.add(configuration_orm)
        self.session.flush()
        self.session.refresh(configuration_orm)
        return map_configuration_orm_to_domain(configuration_orm)

    def find_by_id(self, configuration_id: int) -> Optional[ConfigurationDomainModel]:
        statement = (select(ConfigurationORM).where(ConfigurationORM.id == configuration_id))
        configuration_orm = self.session.scalar(statement)
        if not configuration_orm:
            return None
        return map_configuration_orm_to_domain(orm_model=configuration_orm)

    def find_all(
            self,
            skip: int = 0,
            limit: int = 100,
            solver_types: Optional[List[SolverType]] = None,
            search: Optional[str] = None,
            sort_by: ConfigurationSortField = ConfigurationSortField.CREATED_AT,
            sort_dir: SortDirection = SortDirection.ASC
    ) -> List[ConfigurationDomainModel]:
        statement = (select(ConfigurationORM))

        sort_column_map = {
            ConfigurationSortField.NAME: ConfigurationORM.name,
            ConfigurationSortField.SOLVER_TYPE: ConfigurationORM.solver_type,
            ConfigurationSortField.MOVER_AMOUNT: ConfigurationORM.mover_amount,
            ConfigurationSortField.TIME_LIMIT: ConfigurationORM.time_limit,
            ConfigurationSortField.PROCESS_AMOUNT: ConfigurationORM.process_amount,
            ConfigurationSortField.CREATED_AT: ConfigurationORM.created_at,
            ConfigurationSortField.UPDATED_AT: ConfigurationORM.updated_at,
            ConfigurationSortField.BATCH_SIZE: ConfigurationORM.batch_size,
            ConfigurationSortField.WARMUP: ConfigurationORM.warmup,
            ConfigurationSortField.INTERFACE_TIME: ConfigurationORM.interface_time,
            ConfigurationSortField.DISPENSING_TIME: ConfigurationORM.dispensing_time,
            ConfigurationSortField.DISPENSE_RATE: ConfigurationORM.dispense_rate,
            ConfigurationSortField.VISCOSITY_EXPONENT: ConfigurationORM.viscosity_exponent,
            ConfigurationSortField.MOVER_SPEED: ConfigurationORM.mover_speed,
            ConfigurationSortField.MIXER_PRIMARY_TIME: ConfigurationORM.mixer_primary_time,
            ConfigurationSortField.MIXER_FINAL_TIME: ConfigurationORM.mixer_final_time,
            ConfigurationSortField.CAPPER_TIME: ConfigurationORM.capper_time
        }
        sort_column = sort_column_map.get(sort_by, ConfigurationORM.created_at)

        if solver_types:
            statement = statement.where(ConfigurationORM.solver_type.in_(solver_types))
        if search:
            statement = statement.where(ConfigurationORM.name.ilike(f"%{search}%"))

        if sort_dir == SortDirection.ASC:
            statement = statement.order_by(sort_column.asc().nulls_last())
        else:
            statement = statement.order_by(sort_column.desc().nulls_last())

        statement = statement.offset(skip).limit(limit)

        results = self.session.scalars(statement).all()
        return [map_configuration_orm_to_domain(orm_model=configuration_orm) for configuration_orm in results]

    def update(self, configuration: ConfigurationDomainModel) -> Optional[ConfigurationDomainModel]:
        statement = select(ConfigurationORM).filter_by(id=configuration.id)
        configuration_orm = self.session.scalar(statement)
        if not configuration_orm:
            return None
        update_configuration_orm(domain_model=configuration, orm_model=configuration_orm)
        self.session.flush()
        self.session.refresh(configuration_orm)
        return map_configuration_orm_to_domain(orm_model=configuration_orm)

    def delete(self, configuration_id: int) -> bool:
        statement = delete(ConfigurationORM).where(ConfigurationORM.id == configuration_id)
        try:
            result: Any = self.session.execute(statement)
            self.session.flush()
            return result.rowcount > 0
        except IntegrityError:
            raise EntityInUseError(
                f"Cannot delete Configuration {configuration_id} because it is currently used by an Experiment."
            )

    def get_configuration_count(
            self,
            solver_types: Optional[List[SolverType]] = None,
            search: Optional[str] = None,
    ) -> int:
        statement = select(func.count(ConfigurationORM.id))

        if solver_types:
            statement = statement.where(ConfigurationORM.solver_type.in_(solver_types))

        if search:
            statement = statement.where(ConfigurationORM.name.ilike(f"%{search}%"))

        return self.session.execute(statement).scalar_one()
