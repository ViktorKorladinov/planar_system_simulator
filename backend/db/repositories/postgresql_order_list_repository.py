from typing import Optional, List, Any

from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import EntityInUseError
from db.orm_models.order_list import OrderListORM
from db.repositories.base_order_list_repository import BaseOrderListRepository
from domain.enums import OrderListSortField, SortDirection, OrderListType
from domain.models.order_list import OrderListDomainModel
from mappers.orm.order_list_mapper import map_order_list_domain_to_orm, map_order_list_orm_to_domain, \
    update_order_list_orm


class PostgreSQLOrderListRepository(BaseOrderListRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, order_list: OrderListDomainModel) -> OrderListDomainModel:
        order_list_orm = map_order_list_domain_to_orm(domain_model=order_list)
        self.session.add(order_list_orm)
        self.session.flush()
        self.session.refresh(order_list_orm)
        return map_order_list_orm_to_domain(order_list_orm)

    def find_by_id(self, order_list_id: int) -> Optional[OrderListDomainModel]:
        statement = (select(OrderListORM).where(OrderListORM.id == order_list_id))
        order_list_orm = self.session.scalar(statement)
        if not order_list_orm:
            return None
        return map_order_list_orm_to_domain(orm_model=order_list_orm)

    def find_all(
            self,
            skip: int = 0,
            limit: int = 100,
            types: Optional[List[OrderListType]] = None,
            search: Optional[str] = None,
            sort_by: OrderListSortField = OrderListSortField.CREATED_AT,
            sort_dir: SortDirection = SortDirection.ASC
    ) -> List[OrderListDomainModel]:
        statement = (select(OrderListORM))

        sort_column_map = {
            OrderListSortField.NAME: OrderListORM.name,
            OrderListSortField.ORDER_AMOUNT: OrderListORM.order_amount,
            OrderListSortField.CREATED_AT: OrderListORM.created_at,
            OrderListSortField.UPDATED_AT: OrderListORM.updated_at,
            OrderListSortField.TYPE: OrderListORM.type
        }
        sort_column = sort_column_map.get(sort_by, OrderListORM.created_at)

        if types:
            statement = statement.where(OrderListORM.type.in_(types))
        if search:
            statement = statement.where(OrderListORM.name.ilike(f"%{search}%"))

        if sort_dir == SortDirection.ASC:
            statement = statement.order_by(sort_column.asc().nulls_last())
        else:
            statement = statement.order_by(sort_column.desc().nulls_last())

        statement = statement.offset(skip).limit(limit)

        results = self.session.scalars(statement).all()
        return [map_order_list_orm_to_domain(orm_model=order_list_orm) for order_list_orm in results]

    def delete(self, order_list_id: int) -> bool:
        statement = delete(OrderListORM).where(OrderListORM.id == order_list_id)
        try:
            result: Any = self.session.execute(statement)
            self.session.flush()
            return result.rowcount > 0
        except IntegrityError:
            raise EntityInUseError(
                f"Cannot delete Order List {order_list_id} because it is currently used by an Experiment."
            )

    def get_order_list_count(
            self,
            search: Optional[str] = None,
    ) -> int:
        statement = select(func.count(OrderListORM.id))

        if search:
            statement = statement.where(OrderListORM.name.ilike(f"%{search}%"))

        return self.session.execute(statement).scalar_one()

    def update(self, order_list: OrderListDomainModel) -> Optional[OrderListDomainModel]:
        statement = select(OrderListORM).filter_by(id=order_list.id)
        order_list_orm = self.session.scalar(statement)
        if not order_list_orm:
            return None
        update_order_list_orm(domain_model=order_list, orm_model=order_list_orm)
        self.session.flush()
        self.session.refresh(order_list_orm)
        return map_order_list_orm_to_domain(orm_model=order_list_orm)
