import pytest
from sqlalchemy.orm import Session

from core.exceptions import EntityInUseError
from db.orm_models.configuration import ConfigurationORM
from db.orm_models.experiment import ExperimentORM
from db.orm_models.ingredient_list import IngredientListORM
from db.orm_models.order_list import OrderListORM
from db.repositories.postgresql_layout_repository import PostgreSQLLayoutRepository
from domain.enums import (
    LayoutType, LayoutSortField, SortDirection, IngredientListType,
    SolverType, OrderListType, TileType, NoteType
)
from domain.models.common.tile import Tile
from domain.models.layout import LayoutDomainModel
from mappers.orm.ingredient_list_mapper import map_ingredient_list_orm_to_domain


def _create_base_layout_model(
        db_session: Session,
        name: str = "Test Layout",
        layout_type: LayoutType = LayoutType.SQUARE,
        ingredient_list_type: IngredientListType = IngredientListType.MEDICINE
) -> LayoutDomainModel:
    ingredients_data = [
        {
            "name": "Aspirin" if ingredient_list_type == IngredientListType.MEDICINE else "Rose Oil",
            "note_type": NoteType.HEART_NOTE.value if ingredient_list_type == IngredientListType.PERFUME else None,
            "viscosity": 1.5 if ingredient_list_type == IngredientListType.PERFUME else None,
            "volatility_rank": 3 if ingredient_list_type == IngredientListType.PERFUME else None
        }
    ]

    ing_list = IngredientListORM(
        name=f"Ing List for {name}",
        type=ingredient_list_type,
        ingredients=ingredients_data,
        ingredient_amount=0
    )
    db_session.add(ing_list)
    db_session.flush()
    ing_list_domain = map_ingredient_list_orm_to_domain(ing_list)

    medicine_tiles = [
        Tile(type=TileType.INTERFACE, x=0, y=0),
        Tile(type=TileType.DISPENSER,
             dispensed_types=["Aspirin" if ingredient_list_type == IngredientListType.MEDICINE else "Rose Oil"], x=1,
             y=0)
    ]
    perfume_tiles = [
        Tile(type=TileType.INTERFACE, x=0, y=0),
        Tile(type=TileType.DISPENSER,
             dispensed_types=["Aspirin" if ingredient_list_type == IngredientListType.MEDICINE else "Rose Oil"], x=0,
             y=1),
        Tile(type=TileType.MIXER, x=1, y=0),
        Tile(type=TileType.CAPPER, x=1, y=1)
    ]

    return LayoutDomainModel(
        id=None,
        name=name,
        type=layout_type,
        tiles=medicine_tiles if ingredient_list_type == IngredientListType.MEDICINE else perfume_tiles,
        tile_amount=len(medicine_tiles),
        interface_amount=1,
        dispenser_amount=1,
        filled=False,
        ingredient_list=ing_list_domain
    )


def test_create_and_find_layout(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLLayoutRepository(session=db_session)
    new_layout = _create_base_layout_model(db_session)

    # Act
    created_layout = repo.create(new_layout)
    fetched_layout = repo.find_by_id(created_layout.id)

    # Assert
    assert created_layout.id is not None
    assert fetched_layout is not None
    assert fetched_layout.name == "Test Layout"
    assert fetched_layout.type == LayoutType.SQUARE
    assert fetched_layout.tile_amount == 2
    assert fetched_layout.ingredient_list.id == new_layout.ingredient_list.id


def test_find_by_id_returns_none_when_not_found(db_session: Session) -> None:
    repo = PostgreSQLLayoutRepository(session=db_session)
    fetched_layout = repo.find_by_id(9999)
    assert fetched_layout is None


def test_find_all_pagination(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLLayoutRepository(session=db_session)
    for i in range(5):
        repo.create(_create_base_layout_model(db_session, name=f"Layout {i}"))

    # Act
    page_1 = repo.find_all(skip=0, limit=2)
    page_2 = repo.find_all(skip=2, limit=2)
    page_3 = repo.find_all(skip=4, limit=2)

    # Assert
    assert len(page_1) == 2
    assert len(page_2) == 2
    assert len(page_3) == 1


def test_find_all_filtering_by_layout_type(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLLayoutRepository(session=db_session)
    repo.create(_create_base_layout_model(db_session, layout_type=LayoutType.SQUARE))
    repo.create(_create_base_layout_model(db_session, layout_type=LayoutType.LINE))
    repo.create(_create_base_layout_model(db_session, layout_type=LayoutType.RING))

    # Act
    square_layouts = repo.find_all(layout_types=[LayoutType.SQUARE])
    non_square_layouts = repo.find_all(layout_types=[LayoutType.LINE, LayoutType.RING])

    # Assert
    assert len(square_layouts) == 1
    assert square_layouts[0].type == LayoutType.SQUARE
    assert len(non_square_layouts) == 2


def test_find_all_filtering_by_ingredient_list_type(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLLayoutRepository(session=db_session)
    repo.create(_create_base_layout_model(db_session, ingredient_list_type=IngredientListType.MEDICINE))
    repo.create(_create_base_layout_model(db_session, ingredient_list_type=IngredientListType.PERFUME))

    # Act
    perfume_layouts = repo.find_all(ingredient_list_types=[IngredientListType.PERFUME])

    # Assert
    assert len(perfume_layouts) == 1
    assert perfume_layouts[0].ingredient_list.type == IngredientListType.PERFUME


def test_find_all_searching_by_name(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLLayoutRepository(session=db_session)
    repo.create(_create_base_layout_model(db_session, name="Alpha Grid"))
    repo.create(_create_base_layout_model(db_session, name="Beta Grid"))
    repo.create(_create_base_layout_model(db_session, name="Gamma Line"))

    # Act
    search_results = repo.find_all(search="Grid")

    # Assert
    assert len(search_results) == 2
    for layout in search_results:
        assert "Grid" in layout.name


def test_find_all_sorting(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLLayoutRepository(session=db_session)
    repo.create(_create_base_layout_model(db_session, name="Zebra Layout"))
    repo.create(_create_base_layout_model(db_session, name="Apple Layout"))
    repo.create(_create_base_layout_model(db_session, name="Mango Layout"))

    # Act
    asc_results = repo.find_all(sort_by=LayoutSortField.NAME, sort_dir=SortDirection.ASC)
    desc_results = repo.find_all(sort_by=LayoutSortField.NAME, sort_dir=SortDirection.DESC)

    # Assert
    assert asc_results[0].name == "Apple Layout"
    assert asc_results[1].name == "Mango Layout"
    assert asc_results[2].name == "Zebra Layout"

    assert desc_results[0].name == "Zebra Layout"
    assert desc_results[1].name == "Mango Layout"
    assert desc_results[2].name == "Apple Layout"


def test_update_success(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLLayoutRepository(session=db_session)
    created_layout = repo.create(_create_base_layout_model(db_session, name="Old Name"))

    # Act
    created_layout.name = "New Name"
    updated_layout = repo.update(created_layout)
    fetched_layout = repo.find_by_id(created_layout.id)

    # Assert
    assert updated_layout is not None
    assert updated_layout.name == "New Name"
    assert fetched_layout is not None
    assert fetched_layout.name == "New Name"


def test_update_returns_none_when_not_found(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLLayoutRepository(session=db_session)
    dummy_layout = _create_base_layout_model(db_session)
    dummy_layout.id = 999  # Non-existent ID

    # Act
    result = repo.update(dummy_layout)

    # Assert
    assert result is None


def test_delete_success(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLLayoutRepository(session=db_session)
    created_layout = repo.create(_create_base_layout_model(db_session))

    # Act
    delete_result = repo.delete(created_layout.id)
    fetched_layout = repo.find_by_id(created_layout.id)

    # Assert
    assert delete_result is True
    assert fetched_layout is None


def test_delete_returns_false_when_not_found(db_session: Session) -> None:
    repo = PostgreSQLLayoutRepository(session=db_session)
    delete_result = repo.delete(9999)
    assert delete_result is False


def test_delete_raises_entity_in_use_error_when_linked_to_experiment(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLLayoutRepository(session=db_session)
    layout = repo.create(_create_base_layout_model(db_session))
    config = ConfigurationORM(name="Test Config", solver_type=SolverType.HEXALY, interface_time=1, dispensing_time=1,
                              mover_amount=1, time_limit=1, process_amount=1)
    db_session.add(config)
    order_list = OrderListORM(name="Test Orders", type=OrderListType.MEDICINE, orders=[], order_amount=0)
    db_session.add(order_list)
    db_session.flush()
    experiment = ExperimentORM(
        name="Test Experiment",
        status="queued",
        layout_id=layout.id,
        configuration_id=config.id,
        order_list_id=order_list.id
    )
    db_session.add(experiment)
    db_session.flush()

    # Act & Assert
    with pytest.raises(EntityInUseError) as exc_info:
        repo.delete(layout.id)

    assert f"Cannot delete Layout {layout.id}" in str(exc_info.value)


def test_get_layout_count(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLLayoutRepository(session=db_session)
    repo.create(_create_base_layout_model(db_session, name="Alpha Square", layout_type=LayoutType.SQUARE))
    repo.create(_create_base_layout_model(db_session, name="Alpha Line", layout_type=LayoutType.LINE))
    repo.create(_create_base_layout_model(db_session, name="Beta Custom", layout_type=LayoutType.CUSTOM))

    # Act
    total_count = repo.get_layout_count()
    alpha_count = repo.get_layout_count(search="Alpha")
    custom_count = repo.get_layout_count(layout_types=[LayoutType.CUSTOM])

    # Assert
    assert total_count == 3
    assert alpha_count == 2
    assert custom_count == 1
