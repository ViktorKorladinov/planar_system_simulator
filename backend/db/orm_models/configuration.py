from sqlalchemy import Column, Integer, String, Enum as SQLEnum, Boolean, DateTime, func, Float

from db.orm_models.base import Base
from domain.enums import SolverType


class ConfigurationORM(Base):
    __tablename__ = "configurations"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    solver_type = Column(SQLEnum(SolverType), nullable=False)
    interface_time = Column(Integer, nullable=False)
    dispensing_time = Column(Integer, nullable=False)
    mover_amount = Column(Integer, nullable=False)
    time_limit = Column(Integer, nullable=False)
    process_amount = Column(Integer, nullable=False)
    batch_size = Column(Integer, nullable=True)
    warmup = Column(Boolean, nullable=True)
    dispense_rate = Column(Float, nullable=True)
    viscosity_exponent = Column(Float, nullable=True)
    mover_speed = Column(Float, nullable=True)
    mixer_primary_time = Column(Integer, nullable=True)
    mixer_final_time = Column(Integer, nullable=True)
    capper_time = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
