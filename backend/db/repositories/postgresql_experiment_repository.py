from typing import Optional, List, Any

from sqlalchemy import select, delete, func
from sqlalchemy.orm import Session, joinedload, contains_eager, selectinload

from db.orm_models.batch import BatchORM
from db.orm_models.configuration import ConfigurationORM
from db.orm_models.experiment import ExperimentORM
from db.orm_models.layout import LayoutORM
from db.orm_models.order_list import OrderListORM
from db.repositories.base_experiment_repository import BaseExperimentRepository
from domain.enums import ExperimentStatus, SolverType, LayoutType, ExperimentSortField, SortDirection, BatchSortField
from domain.models.batch import BatchDomainModel
from domain.models.experiment import ExperimentDomainModel
from mappers.orm.experiment_mapper import map_experiment_domain_to_orm, map_experiment_orm_to_domain, \
    update_experiment_orm, map_batch_orm_to_domain, map_batch_domain_to_orm, update_batch_orm


class PostgreSQLExperimentRepository(BaseExperimentRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, experiment: ExperimentDomainModel) -> ExperimentDomainModel:
        experiment_orm = map_experiment_domain_to_orm(domain_model=experiment)
        self.session.add(experiment_orm)
        self.session.flush()
        self.session.refresh(experiment_orm)
        return map_experiment_orm_to_domain(orm_model=experiment_orm)

    def find_by_id(self, experiment_id: int) -> Optional[ExperimentDomainModel]:
        statement = (
            select(ExperimentORM)
            .options(
                joinedload(ExperimentORM.layout, innerjoin=True),
                joinedload(ExperimentORM.configuration, innerjoin=True)
            )
            .where(ExperimentORM.id == experiment_id)
        )
        experiment_orm = self.session.scalar(statement)
        if not experiment_orm:
            return None
        return map_experiment_orm_to_domain(orm_model=experiment_orm)

    def find_all(
            self,
            skip: int = 0,
            limit: int = 100,
            statuses: Optional[List[ExperimentStatus]] = None,
            layout_types: Optional[List[LayoutType]] = None,
            solver_types: Optional[List[SolverType]] = None,
            batch_id: Optional[int] = None,
            search: Optional[str] = None,
            sort_by: ExperimentSortField = ExperimentSortField.CREATED_AT,
            sort_dir: SortDirection = SortDirection.ASC
    ) -> List[ExperimentDomainModel]:
        statement = (
            select(ExperimentORM)
            .join(ExperimentORM.layout)
            .join(ExperimentORM.configuration)
            .join(ExperimentORM.order_list)
            .outerjoin(ExperimentORM.batch)
            .options(
                contains_eager(ExperimentORM.layout),
                contains_eager(ExperimentORM.configuration),
                contains_eager(ExperimentORM.order_list),
                contains_eager(ExperimentORM.batch)
            )
        )

        sort_column_map = {
            ExperimentSortField.NAME: ExperimentORM.name,
            ExperimentSortField.STATUS: ExperimentORM.status,
            ExperimentSortField.CREATED_AT: ExperimentORM.created_at,
            ExperimentSortField.UPDATED_AT: ExperimentORM.updated_at,
            ExperimentSortField.STARTED_AT: ExperimentORM.started_at,
            ExperimentSortField.FINISHED_AT: ExperimentORM.finished_at,
            ExperimentSortField.TILE_AMOUNT: LayoutORM.tile_amount,
            ExperimentSortField.INTERFACE_AMOUNT: LayoutORM.interface_amount,
            ExperimentSortField.DISPENSER_AMOUNT: LayoutORM.dispenser_amount,
            ExperimentSortField.LAYOUT_TYPE: LayoutORM.type,
            ExperimentSortField.LAYOUT_NAME: LayoutORM.name,
            ExperimentSortField.CONFIGURATION_NAME: ConfigurationORM.name,
            ExperimentSortField.SOLVER_TYPE: ConfigurationORM.solver_type,
            ExperimentSortField.MOVER_AMOUNT: ConfigurationORM.mover_amount,
            ExperimentSortField.TIME_LIMIT: ConfigurationORM.time_limit,
            ExperimentSortField.PROCESS_AMOUNT: ConfigurationORM.process_amount,
            ExperimentSortField.ORDER_LIST_NAME: OrderListORM.name,
            ExperimentSortField.ORDER_AMOUNT: OrderListORM.order_amount,
            ExperimentSortField.BATCH_SIZE: ConfigurationORM.batch_size,
            ExperimentSortField.WARMUP: ConfigurationORM.warmup,
            ExperimentSortField.INTERFACE_TIME: ConfigurationORM.interface_time,
            ExperimentSortField.DISPENSING_TIME: ConfigurationORM.dispensing_time,
            ExperimentSortField.BATCH_NAME: BatchORM.name
        }
        sort_column = sort_column_map.get(sort_by, ExperimentORM.created_at)

        if statuses:
            statement = statement.where(ExperimentORM.status.in_(statuses))
        if layout_types:
            statement = statement.where(LayoutORM.type.in_(layout_types))
        if solver_types:
            statement = statement.where(ConfigurationORM.solver_type.in_(solver_types))
        if search:
            statement = statement.where(ExperimentORM.name.ilike(f"%{search}%"))
        if batch_id is not None:
            statement = statement.where(ExperimentORM.batch_id == batch_id)

        if sort_dir == SortDirection.ASC:
            statement = statement.order_by(sort_column.asc().nulls_last())
        else:
            statement = statement.order_by(sort_column.desc().nulls_last())

        statement = statement.offset(skip).limit(limit)

        results = self.session.scalars(statement).all()
        return [map_experiment_orm_to_domain(orm_model=experiment_orm) for experiment_orm in results]

    def update(self, experiment: ExperimentDomainModel) -> Optional[ExperimentDomainModel]:
        statement = select(ExperimentORM).filter_by(id=experiment.id)
        experiment_orm = self.session.scalar(statement)
        if not experiment_orm:
            return None
        update_experiment_orm(domain_model=experiment, orm_model=experiment_orm)
        self.session.flush()
        self.session.refresh(experiment_orm)
        return map_experiment_orm_to_domain(orm_model=experiment_orm)

    def delete(self, experiment_id: int) -> bool:
        # Save batch ID of experiment if it exists.
        statement = select(ExperimentORM).where(ExperimentORM.id == experiment_id)
        experiment_orm = self.session.scalar(statement)
        if not experiment_orm:
            return False
        batch_id = experiment_orm.batch_id

        # Delete experiment.
        delete_stmt = delete(ExperimentORM).where(ExperimentORM.id == experiment_id)
        self.session.execute(delete_stmt)

        # Check how many experiments remained in the batch and delete it if it's empty.
        if batch_id is not None:
            count_stmt = select(func.count(ExperimentORM.id)).where(ExperimentORM.batch_id == batch_id)
            remaining_count = self.session.execute(count_stmt).scalar_one()
            if remaining_count == 0:
                delete_batch_stmt = delete(BatchORM).where(BatchORM.id == batch_id)
                self.session.execute(delete_batch_stmt)
        self.session.flush()
        return True

    def get_experiment_count(
            self,
            statuses: Optional[List[ExperimentStatus]] = None,
            layout_types: Optional[List[LayoutType]] = None,
            solver_types: Optional[List[SolverType]] = None,
            batch_id: Optional[int] = None,
            search: Optional[str] = None,
    ) -> int:
        statement = select(func.count(ExperimentORM.id))

        if statuses:
            statement = statement.where(ExperimentORM.status.in_(statuses))

        if layout_types:
            statement = statement.join(ExperimentORM.layout)
            statement = statement.where(LayoutORM.type.in_(layout_types))

        if solver_types:
            statement = statement.join(ExperimentORM.configuration)
            statement = statement.where(ConfigurationORM.solver_type.in_(solver_types))

        if search:
            statement = statement.where(ExperimentORM.name.ilike(f"%{search}%"))

        if batch_id is not None:
            statement = statement.where(ExperimentORM.batch_id == batch_id)

        return self.session.execute(statement).scalar_one()

    def create_batch(self, batch: BatchDomainModel) -> BatchDomainModel:
        batch_orm = map_batch_domain_to_orm(domain_model=batch)
        self.session.add(batch_orm)
        self.session.flush()
        self.session.refresh(batch_orm)
        return map_batch_orm_to_domain(orm_model=batch_orm)

    def update_batch(self, batch: BatchDomainModel) -> Optional[BatchDomainModel]:
        statement = select(BatchORM).where(BatchORM.id == batch.id)
        batch_orm = self.session.scalar(statement)
        if not batch_orm:
            return None
        update_batch_orm(domain_model=batch, orm_model=batch_orm)

        self.session.flush()
        self.session.refresh(batch_orm)
        return map_batch_orm_to_domain(orm_model=batch_orm)

    def delete_batch(self, batch_id: int) -> bool:
        delete_experiments_stmt = delete(ExperimentORM).where(ExperimentORM.batch_id == batch_id)
        self.session.execute(delete_experiments_stmt)
        delete_batch_stmt = delete(BatchORM).where(BatchORM.id == batch_id)
        result: Any = self.session.execute(delete_batch_stmt)
        self.session.flush()
        return result.rowcount > 0

    def find_batch_by_id(self, batch_id: int) -> Optional[BatchDomainModel]:
        statement = (
            select(BatchORM)
            .options(selectinload(BatchORM.experiments))
            .where(BatchORM.id == batch_id)
        )
        batch_orm = self.session.scalar(statement)
        if not batch_orm:
            return None
        return map_batch_orm_to_domain(orm_model=batch_orm)

    def find_all_batches(self,
                         skip: int = 0,
                         limit: int = 100,
                         search: Optional[str] = None,
                         sort_by: BatchSortField = BatchSortField.CREATED_AT,
                         sort_dir: SortDirection = SortDirection.ASC) -> List[
        BatchDomainModel]:
        statement = select(BatchORM).options(selectinload(BatchORM.experiments))
        sort_column_map = {
            BatchSortField.NAME: BatchORM.name,
            BatchSortField.CREATED_AT: BatchORM.created_at,
            BatchSortField.UPDATED_AT: BatchORM.updated_at,
            BatchSortField.TOTAL_EXPERIMENT_AMOUNT: BatchORM.total_experiment_amount,
            BatchSortField.QUEUED_EXPERIMENT_AMOUNT: BatchORM.queued_experiment_amount,
            BatchSortField.RUNNING_EXPERIMENT_AMOUNT: BatchORM.running_experiment_amount,
            BatchSortField.FINISHED_EXPERIMENT_AMOUNT: BatchORM.finished_experiment_amount,
            BatchSortField.FAILED_EXPERIMENT_AMOUNT: BatchORM.failed_experiment_amount
        }
        sort_column = sort_column_map.get(sort_by, BatchORM.created_at)
        if search:
            statement = statement.where(BatchORM.name.ilike(f"%{search}%"))
        if sort_dir == SortDirection.ASC:
            statement = statement.order_by(sort_column.asc().nulls_last())
        else:
            statement = statement.order_by(sort_column.desc().nulls_last())
        statement = statement.offset(skip).limit(limit)

        results = self.session.scalars(statement).all()
        return [map_batch_orm_to_domain(orm_model=batch_orm) for batch_orm in results]

    def get_batch_count(self, search: Optional[str] = None) -> int:
        statement = select(func.count(BatchORM.id))
        if search:
            statement = statement.where(BatchORM.name.ilike(f"%{search}%"))
        return self.session.execute(statement).scalar_one()
