import pytest
from sqlalchemy.orm import Session

from core.exceptions import EntityInUseError
from db.orm_models.experiment import ExperimentORM
from db.orm_models.ingredient_list import IngredientListORM
from db.orm_models.layout import LayoutORM
from db.orm_models.order_list import OrderListORM
from db.repositories.postgresql_configuration_repository import PostgreSQLConfigurationRepository
from domain.enums import SolverType, ConfigurationSortField, SortDirection, LayoutType, OrderListType, \
    IngredientListType
from domain.models.configuration import ConfigurationDomainModel


def _create_base_config_model(name: str = "Test Config",
                              solver_type: SolverType = SolverType.HEXALY) -> ConfigurationDomainModel:
    return ConfigurationDomainModel(
        id=None,
        name=name,
        solver_type=solver_type,
        interface_time=15,
        dispensing_time=5,
        mover_amount=4,
        time_limit=300,
        batch_size=10 if solver_type == SolverType.CPLEX_MEDICINE else None,
        process_amount=100,
        warmup=True if solver_type == SolverType.CPLEX_MEDICINE else None,
        dispense_rate=1.5 if solver_type == SolverType.CPLEX_PERFUMES else None,
        viscosity_exponent=1.2 if solver_type == SolverType.CPLEX_PERFUMES else None,
        mover_speed=2.0 if solver_type == SolverType.CPLEX_PERFUMES else None,
        mixer_primary_time=10 if solver_type == SolverType.CPLEX_PERFUMES else None,
        mixer_final_time=15 if solver_type == SolverType.CPLEX_PERFUMES else None,
        capper_time=5 if solver_type == SolverType.CPLEX_PERFUMES else None,
    )


def test_create_and_find_configuration(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLConfigurationRepository(session=db_session)
    new_config = _create_base_config_model()

    # Act
    created_config = repo.create(new_config)
    fetched_config = repo.find_by_id(created_config.id)

    # Assert
    assert created_config.id is not None
    assert fetched_config is not None
    assert fetched_config.name == "Test Config"
    assert fetched_config.mover_amount == 4
    assert fetched_config.solver_type == SolverType.HEXALY
    assert fetched_config.created_at is not None


def test_find_by_id_returns_none_when_not_found(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLConfigurationRepository(session=db_session)

    # Act
    fetched_config = repo.find_by_id(999)

    # Assert
    assert fetched_config is None


def test_find_all_pagination(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLConfigurationRepository(session=db_session)
    for i in range(5):
        repo.create(_create_base_config_model(name=f"Config {i}"))

    # Act
    page_1 = repo.find_all(skip=0, limit=2)
    page_2 = repo.find_all(skip=2, limit=2)
    page_3 = repo.find_all(skip=4, limit=2)

    # Assert
    assert len(page_1) == 2
    assert len(page_2) == 2
    assert len(page_3) == 1


def test_find_all_filtering_by_solver_type(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLConfigurationRepository(session=db_session)
    repo.create(_create_base_config_model(solver_type=SolverType.HEXALY))
    repo.create(_create_base_config_model(solver_type=SolverType.CPLEX_MEDICINE))
    repo.create(_create_base_config_model(solver_type=SolverType.CPLEX_PERFUMES))

    # Act
    hexaly_configs = repo.find_all(solver_types=[SolverType.HEXALY])
    cplex_configs = repo.find_all(solver_types=[SolverType.CPLEX_MEDICINE, SolverType.CPLEX_PERFUMES])

    # Assert
    assert len(hexaly_configs) == 1
    assert hexaly_configs[0].solver_type == SolverType.HEXALY
    assert len(cplex_configs) == 2


def test_find_all_searching_by_name(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLConfigurationRepository(session=db_session)
    repo.create(_create_base_config_model(name="Alpha Config"))
    repo.create(_create_base_config_model(name="Beta Config"))
    repo.create(_create_base_config_model(name="Gamma Setting"))

    # Act
    search_results = repo.find_all(search="Config")

    # Assert
    assert len(search_results) == 2
    for config in search_results:
        assert "Config" in config.name


def test_find_all_sorting(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLConfigurationRepository(session=db_session)
    repo.create(_create_base_config_model(name="Zebra"))
    repo.create(_create_base_config_model(name="Apple"))
    repo.create(_create_base_config_model(name="Mango"))

    # Act
    asc_results = repo.find_all(sort_by=ConfigurationSortField.NAME, sort_dir=SortDirection.ASC)
    desc_results = repo.find_all(sort_by=ConfigurationSortField.NAME, sort_dir=SortDirection.DESC)

    # Assert
    assert asc_results[0].name == "Apple"
    assert asc_results[1].name == "Mango"
    assert asc_results[2].name == "Zebra"

    assert desc_results[0].name == "Zebra"
    assert desc_results[1].name == "Mango"
    assert desc_results[2].name == "Apple"


def test_update_success(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLConfigurationRepository(session=db_session)
    created_config = repo.create(_create_base_config_model(name="Old Name"))

    # Act
    created_config.name = "New Name"
    updated_config = repo.update(created_config)
    fetched_config = repo.find_by_id(created_config.id)

    # Assert
    assert updated_config is not None
    assert updated_config.name == "New Name"
    assert fetched_config is not None
    assert fetched_config.name == "New Name"
    assert updated_config.mover_amount == 4


def test_update_returns_none_when_not_found(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLConfigurationRepository(session=db_session)
    dummy_config = _create_base_config_model()
    dummy_config.id = 999

    # Act
    result = repo.update(dummy_config)

    # Assert
    assert result is None


def test_delete_success(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLConfigurationRepository(session=db_session)
    created_config = repo.create(_create_base_config_model())

    # Act
    delete_result = repo.delete(created_config.id)
    fetched_config = repo.find_by_id(created_config.id)

    # Assert
    assert delete_result is True
    assert fetched_config is None


def test_delete_returns_false_when_not_found(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLConfigurationRepository(session=db_session)

    # Act
    delete_result = repo.delete(999)

    # Assert
    assert delete_result is False


def test_delete_raises_entity_in_use_error_when_linked_to_experiment(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLConfigurationRepository(session=db_session)
    config = repo.create(_create_base_config_model())
    ingredient_list = IngredientListORM(name="Test Ing", type=IngredientListType.MEDICINE, ingredients=[],
                                        ingredient_amount=0)
    db_session.add(ingredient_list)
    db_session.flush()

    layout = LayoutORM(name="Test Layout", type=LayoutType.CUSTOM, tiles=[], tile_amount=0, interface_amount=0,
                       dispenser_amount=0, filled=True, ingredient_list_id=ingredient_list.id)
    db_session.add(layout)

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
        repo.delete(config.id)

    assert f"Cannot delete Configuration {config.id}" in str(exc_info.value)


def test_get_configuration_count(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLConfigurationRepository(session=db_session)
    repo.create(_create_base_config_model(name="Alpha", solver_type=SolverType.HEXALY))
    repo.create(_create_base_config_model(name="Alpha v2", solver_type=SolverType.CPLEX_MEDICINE))
    repo.create(_create_base_config_model(name="Beta", solver_type=SolverType.CPLEX_PERFUMES))

    # Act
    total_count = repo.get_configuration_count()
    alpha_count = repo.get_configuration_count(search="Alpha")
    hexaly_count = repo.get_configuration_count(solver_types=[SolverType.HEXALY])

    # Assert
    assert total_count == 3
    assert alpha_count == 2
    assert hexaly_count == 1
