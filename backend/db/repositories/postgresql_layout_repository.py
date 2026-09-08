from typing import Optional, List, Any

from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import EntityInUseError
from db.orm_models.ingredient_list import IngredientListORM
from db.orm_models.layout import LayoutORM
from db.repositories.base_layout_repository import BaseLayoutRepository
from domain.enums import LayoutType, LayoutSortField, SortDirection, IngredientListType
from domain.models.layout import LayoutDomainModel
from mappers.orm.layout_mapper import map_layout_domain_to_orm, map_layout_orm_to_domain, update_layout_orm


class PostgreSQLLayoutRepository(BaseLayoutRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, layout: LayoutDomainModel) -> LayoutDomainModel:
        layout_orm = map_layout_domain_to_orm(domain_model=layout)
        self.session.add(layout_orm)
        self.session.flush()
        self.session.refresh(layout_orm)
        return map_layout_orm_to_domain(orm_model=layout_orm)

    def find_by_id(self, layout_id: int) -> Optional[LayoutDomainModel]:
        statement = (select(LayoutORM).where(LayoutORM.id == layout_id))
        statement = statement.outerjoin(LayoutORM.ingredient_list)
        layout_orm = self.session.scalar(statement)
        if not layout_orm:
            return None
        return map_layout_orm_to_domain(orm_model=layout_orm)

    def find_all(
            self,
            skip: int = 0,
            limit: int = 100,
            layout_types: Optional[List[LayoutType]] = None,
            ingredient_list_types: Optional[List[IngredientListType]] = None,
            search: Optional[str] = None,
            sort_by: LayoutSortField = LayoutSortField.CREATED_AT,
            sort_dir: SortDirection = SortDirection.ASC
    ) -> List[LayoutDomainModel]:
        statement = (select(LayoutORM))

        if ingredient_list_types or sort_by == LayoutSortField.INGREDIENT_LIST_TYPE:
            statement = statement.outerjoin(LayoutORM.ingredient_list)

        sort_column_map = {
            LayoutSortField.NAME: LayoutORM.name,
            LayoutSortField.TYPE: LayoutORM.type,
            LayoutSortField.TILE_AMOUNT: LayoutORM.tile_amount,
            LayoutSortField.INTERFACE_AMOUNT: LayoutORM.interface_amount,
            LayoutSortField.DISPENSER_AMOUNT: LayoutORM.dispenser_amount,
            LayoutSortField.CREATED_AT: LayoutORM.created_at,
            LayoutSortField.UPDATED_AT: LayoutORM.updated_at,
            LayoutSortField.INGREDIENT_LIST_TYPE: IngredientListORM.type
        }
        sort_column = sort_column_map.get(sort_by, LayoutORM.created_at)

        if ingredient_list_types:
            statement = statement.where(IngredientListORM.type.in_(ingredient_list_types))
        if layout_types:
            statement = statement.where(LayoutORM.type.in_(layout_types))
        if search:
            statement = statement.where(LayoutORM.name.ilike(f"%{search}%"))

        if sort_dir == SortDirection.ASC:
            statement = statement.order_by(sort_column.asc().nulls_last())
        else:
            statement = statement.order_by(sort_column.desc().nulls_last())

        statement = statement.offset(skip).limit(limit)

        results = self.session.scalars(statement).all()
        return [map_layout_orm_to_domain(orm_model=layout_orm) for layout_orm in results]

    def update(self, layout: LayoutDomainModel) -> Optional[LayoutDomainModel]:
        statement = select(LayoutORM).filter_by(id=layout.id)
        layout_orm = self.session.scalar(statement)
        if not layout_orm:
            return None
        update_layout_orm(domain_model=layout, orm_model=layout_orm)
        self.session.flush()
        self.session.refresh(layout_orm)
        return map_layout_orm_to_domain(orm_model=layout_orm)

    def delete(self, layout_id: int) -> bool:
        statement = delete(LayoutORM).where(LayoutORM.id == layout_id)
        try:
            result: Any = self.session.execute(statement)
            self.session.flush()
            return result.rowcount > 0
        except IntegrityError:
            raise EntityInUseError(
                f"Cannot delete Layout {layout_id} because it is currently used by an Experiment."
            )

    def get_layout_count(
            self,
            layout_types: Optional[List[LayoutType]] = None,
            search: Optional[str] = None,
    ) -> int:
        statement = select(func.count(LayoutORM.id))

        if layout_types:
            statement = statement.where(LayoutORM.type.in_(layout_types))

        if search:
            statement = statement.where(LayoutORM.name.ilike(f"%{search}%"))

        return self.session.execute(statement).scalar_one()
