from sqlalchemy import Column, Integer, String, DateTime, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB

from db.orm_models.base import Base
from domain.enums import OrderListType


class OrderListORM(Base):
    __tablename__ = "order_lists"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    type = Column(SQLEnum(OrderListType), nullable=False)
    orders = Column(JSONB, nullable=False)
    order_amount = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
