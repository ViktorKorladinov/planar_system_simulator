import pytest
from sqlalchemy.orm import Session

from core.exceptions import EntityInUseError
from db.orm_models.layout import LayoutORM
from db.repositories.postgresql_ingredient_list_repository import PostgreSQLIngredientListRepository
from domain.enums import IngredientListType, IngredientListSortField, SortDirection, LayoutType, NoteType
from domain.models.ingredient_list import Ingredient
from domain.models.ingredient_list import IngredientListDomainModel


def _create_base_ingredient_list_model(
        name: str = "Test Ingredient List",
        list_type: IngredientListType = IngredientListType.MEDICINE
) -> IngredientListDomainModel:
    ingredients = [
        Ingredient(
            name="Aspirin" if list_type == IngredientListType.MEDICINE else "Rose Oil",
            note_type=NoteType.HEART_NOTE if list_type == IngredientListType.PERFUME else None,
            viscosity=1.5 if list_type == IngredientListType.PERFUME else None,
            volatility_rank=3 if list_type == IngredientListType.PERFUME else None
        )
    ]
    return IngredientListDomainModel(
        id=None,
        name=name,
        type=list_type,
        ingredient_amount=len(ingredients),
        ingredients=ingredients
    )


def test_create_and_find_ingredient_list(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLIngredientListRepository(session=db_session)
    new_ing_list = _create_base_ingredient_list_model()

    # Act
    created_ing_list = repo.create(new_ing_list)
    fetched_ing_list = repo.find_by_id(created_ing_list.id)

    # Assert
    assert created_ing_list.id is not None
    assert fetched_ing_list is not None
    assert fetched_ing_list.name == "Test Ingredient List"
    assert fetched_ing_list.type == IngredientListType.MEDICINE
    assert fetched_ing_list.ingredient_amount == 1
    assert fetched_ing_list.created_at is not None
    assert len(fetched_ing_list.ingredients) == 1
    assert fetched_ing_list.ingredients[0].name == "Aspirin"


def test_find_by_id_returns_none_when_not_found(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLIngredientListRepository(session=db_session)

    # Act
    fetched_ing_list = repo.find_by_id(999)

    # Assert
    assert fetched_ing_list is None


def test_find_all_pagination(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLIngredientListRepository(session=db_session)
    for i in range(5):
        repo.create(_create_base_ingredient_list_model(name=f"List {i}"))

    # Act
    page_1 = repo.find_all(skip=0, limit=2)
    page_2 = repo.find_all(skip=2, limit=2)
    page_3 = repo.find_all(skip=4, limit=2)

    # Assert
    assert len(page_1) == 2
    assert len(page_2) == 2
    assert len(page_3) == 1


def test_find_all_filtering_by_type(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLIngredientListRepository(session=db_session)
    repo.create(_create_base_ingredient_list_model(name="Med 1", list_type=IngredientListType.MEDICINE))
    repo.create(_create_base_ingredient_list_model(name="Med 2", list_type=IngredientListType.MEDICINE))
    repo.create(_create_base_ingredient_list_model(name="Perfume 1", list_type=IngredientListType.PERFUME))

    # Act
    medicine_lists = repo.find_all(types=[IngredientListType.MEDICINE])
    perfume_lists = repo.find_all(types=[IngredientListType.PERFUME])

    # Assert
    assert len(medicine_lists) == 2
    assert medicine_lists[0].type == IngredientListType.MEDICINE
    assert len(perfume_lists) == 1
    assert perfume_lists[0].type == IngredientListType.PERFUME


def test_find_all_searching_by_name(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLIngredientListRepository(session=db_session)
    repo.create(_create_base_ingredient_list_model(name="Alpha Base"))
    repo.create(_create_base_ingredient_list_model(name="Beta Base"))
    repo.create(_create_base_ingredient_list_model(name="Gamma Mixture"))

    # Act
    search_results = repo.find_all(search="Base")

    # Assert
    assert len(search_results) == 2
    for ing_list in search_results:
        assert "Base" in ing_list.name


def test_find_all_sorting(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLIngredientListRepository(session=db_session)
    repo.create(_create_base_ingredient_list_model(name="Zebra Extract"))
    repo.create(_create_base_ingredient_list_model(name="Apple Extract"))
    repo.create(_create_base_ingredient_list_model(name="Mango Extract"))

    # Act
    asc_results = repo.find_all(sort_by=IngredientListSortField.NAME, sort_dir=SortDirection.ASC)
    desc_results = repo.find_all(sort_by=IngredientListSortField.NAME, sort_dir=SortDirection.DESC)

    # Assert
    assert asc_results[0].name == "Apple Extract"
    assert asc_results[1].name == "Mango Extract"
    assert asc_results[2].name == "Zebra Extract"

    assert desc_results[0].name == "Zebra Extract"
    assert desc_results[1].name == "Mango Extract"
    assert desc_results[2].name == "Apple Extract"


def test_update_success(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLIngredientListRepository(session=db_session)
    created_ing_list = repo.create(_create_base_ingredient_list_model(name="Old Name"))

    # Act
    created_ing_list.name = "New Name"
    updated_ing_list = repo.update(created_ing_list)
    fetched_ing_list = repo.find_by_id(created_ing_list.id)

    # Assert
    assert updated_ing_list is not None
    assert updated_ing_list.name == "New Name"
    assert fetched_ing_list is not None
    assert fetched_ing_list.name == "New Name"
    assert fetched_ing_list.updated_at is not None


def test_update_returns_none_when_not_found(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLIngredientListRepository(session=db_session)
    dummy_ing_list = _create_base_ingredient_list_model()
    dummy_ing_list.id = 999

    # Act
    result = repo.update(dummy_ing_list)

    # Assert
    assert result is None


def test_delete_success(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLIngredientListRepository(session=db_session)
    created_ing_list = repo.create(_create_base_ingredient_list_model())

    # Act
    delete_result = repo.delete(created_ing_list.id)
    fetched_ing_list = repo.find_by_id(created_ing_list.id)

    # Assert
    assert delete_result is True
    assert fetched_ing_list is None


def test_delete_returns_false_when_not_found(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLIngredientListRepository(session=db_session)

    # Act
    delete_result = repo.delete(999)

    # Assert
    assert delete_result is False


def test_delete_raises_entity_in_use_error_when_linked_to_layout(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLIngredientListRepository(session=db_session)
    ing_list = repo.create(_create_base_ingredient_list_model())
    layout = LayoutORM(
        name="Test Layout",
        type=LayoutType.CUSTOM,
        tiles=[],
        tile_amount=0,
        interface_amount=0,
        dispenser_amount=0,
        filled=True,
        ingredient_list_id=ing_list.id
    )
    db_session.add(layout)
    db_session.flush()

    # Act & Assert
    with pytest.raises(EntityInUseError) as exc_info:
        repo.delete(ing_list.id)

    assert f"Cannot delete Ingredient List {ing_list.id}" in str(exc_info.value)


def test_get_ingredient_list_count(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLIngredientListRepository(session=db_session)
    repo.create(_create_base_ingredient_list_model(name="Alpha List"))
    repo.create(_create_base_ingredient_list_model(name="Alpha Ext List"))
    repo.create(_create_base_ingredient_list_model(name="Beta List"))

    # Act
    total_count = repo.get_ingredient_list_count()
    alpha_count = repo.get_ingredient_list_count(search="Alpha")

    # Assert
    assert total_count == 3
    assert alpha_count == 2
