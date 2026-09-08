import pytest
from sqlalchemy.orm import Session

from core.exceptions import EntityInUseError
from db.orm_models.configuration import ConfigurationORM
from db.orm_models.experiment import ExperimentORM
from db.orm_models.ingredient_list import IngredientListORM
from db.orm_models.layout import LayoutORM
from db.repositories.postgresql_order_list_repository import PostgreSQLOrderListRepository
from domain.enums import OrderListType, LayoutType, SolverType, IngredientListType
from domain.models.order_list import OrderListDomainModel, Order, OrderItem


def _create_base_order_list_model(
        name: str = "Test Order List",
        list_type: OrderListType = OrderListType.MEDICINE
) -> OrderListDomainModel:
    orders_perfume = [Order(items=[OrderItem(name="Aspirin", quantity=10.00)], t_max=3600)]
    orders_medicine = [Order(items=[OrderItem(name="Aspirin", quantity=10)])]

    return OrderListDomainModel(
        id=None,
        name=name,
        type=list_type,
        order_amount=1,
        orders=orders_perfume if list_type == OrderListType.PERFUME else orders_medicine
    )


def test_create_and_find_order_list(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLOrderListRepository(session=db_session)
    new_order_list = _create_base_order_list_model()

    # Act
    created_list = repo.create(new_order_list)
    fetched_list = repo.find_by_id(created_list.id)

    # Assert
    assert created_list.id is not None
    assert fetched_list is not None
    assert fetched_list.name == "Test Order List"
    assert fetched_list.type == OrderListType.MEDICINE
    assert len(fetched_list.orders) == 1
    assert fetched_list.orders[0].items[0].name == "Aspirin"


def test_find_by_id_returns_none_when_not_found(db_session: Session) -> None:
    repo = PostgreSQLOrderListRepository(session=db_session)
    assert repo.find_by_id(9999) is None


def test_find_all_pagination(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLOrderListRepository(session=db_session)
    for i in range(5):
        repo.create(_create_base_order_list_model(name=f"List {i}"))

    # Act
    page_1 = repo.find_all(skip=0, limit=2)
    page_2 = repo.find_all(skip=2, limit=2)

    # Assert
    assert len(page_1) == 2
    assert len(page_2) == 2


def test_find_all_filtering_and_searching(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLOrderListRepository(session=db_session)
    repo.create(_create_base_order_list_model(name="Med Alpha", list_type=OrderListType.MEDICINE))
    repo.create(_create_base_order_list_model(name="Perfume Beta", list_type=OrderListType.PERFUME))

    # Act
    search_results = repo.find_all(search="Alpha")
    type_results = repo.find_all(types=[OrderListType.PERFUME])

    # Assert
    assert len(search_results) == 1
    assert "Alpha" in search_results[0].name
    assert len(type_results) == 1
    assert type_results[0].type == OrderListType.PERFUME


def test_update_order_list_name(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLOrderListRepository(session=db_session)
    created_list = repo.create(_create_base_order_list_model(name="Old Name"))

    # Act
    created_list.name = "New Name"
    updated_list = repo.update(created_list)

    # Assert
    assert updated_list.name == "New Name"
    assert repo.find_by_id(created_list.id).name == "New Name"


def test_delete_success(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLOrderListRepository(session=db_session)
    created_list = repo.create(_create_base_order_list_model())

    # Act
    result = repo.delete(created_list.id)

    # Assert
    assert result is True
    assert repo.find_by_id(created_list.id) is None


def test_delete_raises_entity_in_use_error(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLOrderListRepository(session=db_session)
    order_list = repo.create(_create_base_order_list_model())
    ing_list = IngredientListORM(name="Ing", type=IngredientListType.MEDICINE, ingredients=[], ingredient_amount=0)
    db_session.add(ing_list)
    db_session.flush()

    layout = LayoutORM(name="L", type=LayoutType.CUSTOM, tiles=[], tile_amount=0, interface_amount=0,
                       dispenser_amount=0, filled=True, ingredient_list_id=ing_list.id)
    config = ConfigurationORM(name="C", solver_type=SolverType.HEXALY, interface_time=1, dispensing_time=1,
                              mover_amount=1, time_limit=1, process_amount=1)
    db_session.add_all([layout, config])
    db_session.flush()

    exp = ExperimentORM(name="E", status="queued", layout_id=layout.id, configuration_id=config.id,
                        order_list_id=order_list.id)
    db_session.add(exp)
    db_session.flush()

    # Act & Assert
    with pytest.raises(EntityInUseError):
        repo.delete(order_list.id)


def test_get_order_list_count(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLOrderListRepository(session=db_session)
    repo.create(_create_base_order_list_model(name="Target 1"))
    repo.create(_create_base_order_list_model(name="Target 2"))
    repo.create(_create_base_order_list_model(name="Other"))

    # Act
    count = repo.get_order_list_count(search="Target")

    # Assert
    assert count == 2
