from sqlalchemy import Column, Integer, String, Enum as SQLEnum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from db.orm_models.base import Base
from domain.enums import ExperimentStatus


class ExperimentORM(Base):
    __tablename__ = "experiments"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    status = Column(SQLEnum(ExperimentStatus), nullable=False, default=ExperimentStatus.QUEUED)
    layout_id = Column(Integer, ForeignKey("layouts.id"), nullable=False)
    configuration_id = Column(Integer, ForeignKey("configurations.id"), nullable=False)
    order_list_id = Column(Integer, ForeignKey("order_lists.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=True)
    result = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    task_id = Column(String, nullable=True)

    layout = relationship("LayoutORM")
    configuration = relationship("ConfigurationORM")
    order_list = relationship("OrderListORM")
    batch = relationship("BatchORM", back_populates="experiments")
