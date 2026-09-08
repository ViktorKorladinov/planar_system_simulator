from typing import Optional, List, Any

from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import EntityInUseError
from db.orm_models.ingredient_list import IngredientListORM
from db.repositories.base_ingredient_list_repository import BaseIngredientListRepository
from domain.enums import IngredientListSortField, SortDirection, IngredientListType
from domain.models.ingredient_list import IngredientListDomainModel
from mappers.orm.ingredient_list_mapper import map_ingredient_list_domain_to_orm, map_ingredient_list_orm_to_domain, \
    update_ingredient_list_orm


class PostgreSQLIngredientListRepository(BaseIngredientListRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, ingredient_list: IngredientListDomainModel) -> IngredientListDomainModel:
        ingredient_list_orm = map_ingredient_list_domain_to_orm(domain_model=ingredient_list)
        self.session.add(ingredient_list_orm)
        self.session.flush()
        self.session.refresh(ingredient_list_orm)
        return map_ingredient_list_orm_to_domain(ingredient_list_orm)

    def find_by_id(self, ingredient_list_id: int) -> Optional[IngredientListDomainModel]:
        statement = (select(IngredientListORM).where(IngredientListORM.id == ingredient_list_id))
        ingredient_list_orm = self.session.scalar(statement)
        if not ingredient_list_orm:
            return None
        return map_ingredient_list_orm_to_domain(orm_model=ingredient_list_orm)

    def find_all(
            self,
            skip: int = 0,
            limit: int = 100,
            types: Optional[List[IngredientListType]] = None,
            search: Optional[str] = None,
            sort_by: IngredientListSortField = IngredientListSortField.CREATED_AT,
            sort_dir: SortDirection = SortDirection.ASC
    ) -> List[IngredientListDomainModel]:
        statement = (select(IngredientListORM))

        sort_column_map = {
            IngredientListSortField.NAME: IngredientListORM.name,
            IngredientListSortField.INGREDIENT_AMOUNT: IngredientListORM.ingredient_amount,
            IngredientListSortField.CREATED_AT: IngredientListORM.created_at,
            IngredientListSortField.UPDATED_AT: IngredientListORM.updated_at,
            IngredientListSortField.TYPE: IngredientListORM.type
        }
        sort_column = sort_column_map.get(sort_by, IngredientListORM.created_at)

        if types:
            statement = statement.where(IngredientListORM.type.in_(types))
        if search:
            statement = statement.where(IngredientListORM.name.ilike(f"%{search}%"))

        if sort_dir == SortDirection.ASC:
            statement = statement.order_by(sort_column.asc().nulls_last())
        else:
            statement = statement.order_by(sort_column.desc().nulls_last())

        statement = statement.offset(skip).limit(limit)

        results = self.session.scalars(statement).all()
        return [map_ingredient_list_orm_to_domain(orm_model=ingredient_list_orm) for ingredient_list_orm in results]

    def delete(self, ingredient_list_id: int) -> bool:
        statement = delete(IngredientListORM).where(IngredientListORM.id == ingredient_list_id)
        try:
            result: Any = self.session.execute(statement)
            self.session.flush()
            return result.rowcount > 0
        except IntegrityError:
            raise EntityInUseError(
                f"Cannot delete Ingredient List {ingredient_list_id} because it is currently used by a Layout."
            )

    def get_ingredient_list_count(
            self,
            search: Optional[str] = None,
    ) -> int:
        statement = select(func.count(IngredientListORM.id))

        if search:
            statement = statement.where(IngredientListORM.name.ilike(f"%{search}%"))

        return self.session.execute(statement).scalar_one()

    def update(self, ingredient_list: IngredientListDomainModel) -> Optional[IngredientListDomainModel]:
        statement = select(IngredientListORM).filter_by(id=ingredient_list.id)
        ingredient_list_orm = self.session.scalar(statement)
        if not ingredient_list_orm:
            return None
        update_ingredient_list_orm(domain_model=ingredient_list, orm_model=ingredient_list_orm)
        self.session.flush()
        self.session.refresh(ingredient_list_orm)
        return map_ingredient_list_orm_to_domain(orm_model=ingredient_list_orm)
