from sqlalchemy import Column, Integer, DateTime, String, func, select, and_
from sqlalchemy.orm import relationship, column_property

from db.orm_models.base import Base
from db.orm_models.experiment import ExperimentORM
from domain.enums import ExperimentStatus


class BatchORM(Base):
    __tablename__ = "batches"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    experiments = relationship("ExperimentORM", back_populates="batch")
    total_experiment_amount = column_property(
        select(func.count(ExperimentORM.id))
        .where(ExperimentORM.batch_id == id)
        .correlate_except(ExperimentORM)
        .scalar_subquery()
    )
    queued_experiment_amount = column_property(
        select(func.count(ExperimentORM.id))
        .where(and_(ExperimentORM.batch_id == id, ExperimentORM.status == ExperimentStatus.QUEUED))
        .correlate_except(ExperimentORM)
        .scalar_subquery()
    )
    running_experiment_amount = column_property(
        select(func.count(ExperimentORM.id))
        .where(and_(ExperimentORM.batch_id == id, ExperimentORM.status == ExperimentStatus.RUNNING))
        .correlate_except(ExperimentORM)
        .scalar_subquery()
    )
    finished_experiment_amount = column_property(
        select(func.count(ExperimentORM.id))
        .where(and_(ExperimentORM.batch_id == id, ExperimentORM.status == ExperimentStatus.FINISHED))
        .correlate_except(ExperimentORM)
        .scalar_subquery()
    )
    failed_experiment_amount = column_property(
        select(func.count(ExperimentORM.id))
        .where(and_(ExperimentORM.batch_id == id, ExperimentORM.status == ExperimentStatus.FAILED))
        .correlate_except(ExperimentORM)
        .scalar_subquery()
    )
