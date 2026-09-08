from sqlalchemy import Column, Integer, String, DateTime, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from db.orm_models.base import Base
from domain.enums import IngredientListType


class IngredientListORM(Base):
    __tablename__ = "ingredient_lists"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    type = Column(SQLEnum(IngredientListType), nullable=False)
    ingredients = Column(JSONB, nullable=False)
    ingredient_amount = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    layouts = relationship("LayoutORM", back_populates="ingredient_list")
