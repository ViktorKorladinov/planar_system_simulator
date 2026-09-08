from sqlalchemy import Column, Integer, String, Enum as SQLEnum, Boolean, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from db.orm_models.base import Base
from domain.enums import LayoutType


class LayoutORM(Base):
    __tablename__ = "layouts"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    type = Column(SQLEnum(LayoutType), nullable=False)
    tiles = Column(JSONB, nullable=True)
    tile_amount = Column(Integer, nullable=False)
    interface_amount = Column(Integer, nullable=False)
    dispenser_amount = Column(Integer, nullable=False)
    filled = Column(Boolean, nullable=False)
    ingredient_list_id = Column(Integer, ForeignKey("ingredient_lists.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    ingredient_list = relationship("IngredientListORM", back_populates="layouts")
