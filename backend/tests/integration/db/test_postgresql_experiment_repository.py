from sqlalchemy.orm import Session

from db.orm_models.configuration import ConfigurationORM
from db.orm_models.ingredient_list import IngredientListORM
from db.orm_models.layout import LayoutORM
from db.orm_models.order_list import OrderListORM
from db.repositories.postgresql_experiment_repository import PostgreSQLExperimentRepository
from domain.enums import (
    ExperimentStatus, SolverType, LayoutType, OrderListType,
    IngredientListType, ExperimentSortField, SortDirection
)
from domain.models.batch import BatchDomainModel
from domain.models.experiment import ExperimentDomainModel
from mappers.orm.configuration_mapper import map_configuration_orm_to_domain
from mappers.orm.layout_mapper import map_layout_orm_to_domain
from mappers.orm.order_list_mapper import map_order_list_orm_to_domain


def _create_experiment_dependencies(db_session: Session):
    ing_list = IngredientListORM(name="Test Ing", type=IngredientListType.MEDICINE, ingredients=[], ingredient_amount=0)
    db_session.add(ing_list)
    db_session.flush()
    layout = LayoutORM(name="Test Layout", type=LayoutType.CUSTOM, tiles=[], tile_amount=0, interface_amount=0,
                       dispenser_amount=0, filled=True, ingredient_list_id=ing_list.id)
    config = ConfigurationORM(name="Test Config", solver_type=SolverType.CPLEX_MEDICINE, interface_time=1, dispensing_time=1,
                              mover_amount=1, time_limit=1, process_amount=1, batch_size=100, warmup=True)
    order_list = OrderListORM(name="Test Orders", type=OrderListType.MEDICINE, orders=[], order_amount=0)

    db_session.add_all([layout, config, order_list])
    db_session.flush()

    return (
        map_layout_orm_to_domain(layout),
        map_configuration_orm_to_domain(config),
        map_order_list_orm_to_domain(order_list)
    )


def _create_base_experiment_model(
        db_session: Session,
        name: str = "Test Experiment",
        status: ExperimentStatus = ExperimentStatus.QUEUED
) -> ExperimentDomainModel:
    layout, config, order_list = _create_experiment_dependencies(db_session)

    return ExperimentDomainModel(
        id=None,
        name=name,
        status=status,
        layout=layout,
        configuration=config,
        order_list=order_list
    )


def test_create_and_find_experiment(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLExperimentRepository(session=db_session)
    new_experiment = _create_base_experiment_model(db_session)

    # Act
    created_exp = repo.create(new_experiment)
    fetched_exp = repo.find_by_id(created_exp.id)

    # Assert
    assert created_exp.id is not None
    assert fetched_exp is not None
    assert fetched_exp.name == "Test Experiment"
    assert fetched_exp.status == ExperimentStatus.QUEUED
    assert fetched_exp.layout.id == new_experiment.layout.id
    assert fetched_exp.configuration.id == new_experiment.configuration.id


def test_find_by_id_returns_none_when_not_found(db_session: Session) -> None:
    repo = PostgreSQLExperimentRepository(session=db_session)
    fetched_exp = repo.find_by_id(9999)
    assert fetched_exp is None


def test_find_all_experiments_with_filters(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLExperimentRepository(session=db_session)

    exp1 = _create_base_experiment_model(db_session, name="Alpha Exp", status=ExperimentStatus.FINISHED)
    exp2 = _create_base_experiment_model(db_session, name="Beta Exp", status=ExperimentStatus.RUNNING)
    exp3 = _create_base_experiment_model(db_session, name="Gamma Setup", status=ExperimentStatus.QUEUED)

    repo.create(exp1)
    repo.create(exp2)
    repo.create(exp3)

    # Act
    search_results = repo.find_all(search="Exp")
    status_results = repo.find_all(statuses=[ExperimentStatus.RUNNING, ExperimentStatus.FINISHED])
    sort_results = repo.find_all(sort_by=ExperimentSortField.NAME, sort_dir=SortDirection.DESC)

    # Assert
    assert len(search_results) == 2
    assert len(status_results) == 2
    assert sort_results[0].name == "Gamma Setup"
    assert sort_results[1].name == "Beta Exp"
    assert sort_results[2].name == "Alpha Exp"


def test_update_experiment_success(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLExperimentRepository(session=db_session)
    created_exp = repo.create(_create_base_experiment_model(db_session, name="Old Name"))

    # Act
    created_exp.name = "New Name"
    created_exp.status = ExperimentStatus.FAILED
    updated_exp = repo.update(created_exp)
    fetched_exp = repo.find_by_id(created_exp.id)

    # Assert
    assert updated_exp is not None
    assert updated_exp.name == "New Name"
    assert updated_exp.status == ExperimentStatus.FAILED
    assert fetched_exp.name == "New Name"


def test_delete_experiment_success(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLExperimentRepository(session=db_session)
    created_exp = repo.create(_create_base_experiment_model(db_session))

    # Act
    delete_result = repo.delete(created_exp.id)
    fetched_exp = repo.find_by_id(created_exp.id)

    # Assert
    assert delete_result is True
    assert fetched_exp is None


def test_get_experiment_count(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLExperimentRepository(session=db_session)
    repo.create(_create_base_experiment_model(db_session, name="Item 1", status=ExperimentStatus.FINISHED))
    repo.create(_create_base_experiment_model(db_session, name="Item 2", status=ExperimentStatus.QUEUED))

    # Act
    total_count = repo.get_experiment_count()
    finished_count = repo.get_experiment_count(statuses=[ExperimentStatus.FINISHED])

    # Assert
    assert total_count == 2
    assert finished_count == 1


def test_create_and_find_batch(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLExperimentRepository(session=db_session)
    exp1 = _create_base_experiment_model(db_session, name="Batch Exp 1")
    exp2 = _create_base_experiment_model(db_session, name="Batch Exp 2")

    batch = BatchDomainModel(id=None, name="Test Batch", experiments=[exp1, exp2])

    # Act
    created_batch = repo.create_batch(batch)
    fetched_batch = repo.find_batch_by_id(created_batch.id)

    # Assert
    assert created_batch.id is not None
    assert fetched_batch is not None
    assert fetched_batch.name == "Test Batch"
    assert len(fetched_batch.experiments) == 2


def test_update_batch(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLExperimentRepository(session=db_session)
    batch = BatchDomainModel(id=None, name="Old Batch Name", experiments=[_create_base_experiment_model(db_session)])
    created_batch = repo.create_batch(batch)

    # Act
    created_batch.name = "New Batch Name"
    updated_batch = repo.update_batch(created_batch)
    fetched_batch = repo.find_batch_by_id(created_batch.id)

    # Assert
    assert updated_batch.name == "New Batch Name"
    assert fetched_batch.name == "New Batch Name"


def test_delete_batch_cascades_to_experiments(db_session: Session) -> None:
    # Arrange
    repo = PostgreSQLExperimentRepository(session=db_session)
    exp1 = _create_base_experiment_model(db_session)
    batch = BatchDomainModel(id=None, name="To Delete", experiments=[exp1])
    created_batch = repo.create_batch(batch)
    exp_id = created_batch.experiments[0].id

    # Act
    delete_result = repo.delete_batch(created_batch.id)
    fetched_batch = repo.find_batch_by_id(created_batch.id)
    fetched_exp = repo.find_by_id(exp_id)

    # Assert
    assert delete_result is True
    assert fetched_batch is None
    assert fetched_exp is None


def test_delete_last_experiment_deletes_batch(db_session: Session) -> None:
    """Tests the custom delete behavior where deleting the last experiment in a batch cleans up the batch."""
    # Arrange
    repo = PostgreSQLExperimentRepository(session=db_session)
    exp1 = _create_base_experiment_model(db_session)
    exp2 = _create_base_experiment_model(db_session)
    batch = BatchDomainModel(id=None, name="Auto Cleanup Batch", experiments=[exp1, exp2])
    created_batch = repo.create_batch(batch)

    exp1_id = created_batch.experiments[0].id
    exp2_id = created_batch.experiments[1].id
    batch_id = created_batch.id

    # Act & Assert
    repo.delete(exp1_id)
    fetched_batch_step_1 = repo.find_batch_by_id(batch_id)
    assert fetched_batch_step_1 is not None
    repo.delete(exp2_id)
    fetched_batch_step_2 = repo.find_batch_by_id(batch_id)
    assert fetched_batch_step_2 is None
