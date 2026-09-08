from domain.enums import ExperimentStatus
from mappers.orm.experiment_mapper import (
    map_experiment_domain_to_orm,
    update_experiment_orm,
    map_experiment_orm_to_domain,
    map_batch_orm_to_domain,
    map_batch_domain_to_orm,
    update_batch_orm
)
from tests.factories.experiment_factory import (
    get_experiment_orm_model,
    get_experiment_domain_model,
    get_batch_orm_model,
    get_batch_domain_model
)


def test_map_experiment_orm_to_domain() -> None:
    # Arrange
    experiment_orm_model = get_experiment_orm_model()

    # Act
    domain_model = map_experiment_orm_to_domain(experiment_orm_model)

    # Assert
    assert domain_model.id == experiment_orm_model.id
    assert domain_model.name == experiment_orm_model.name
    assert domain_model.status == experiment_orm_model.status
    assert domain_model.layout.id == experiment_orm_model.layout_id
    assert domain_model.configuration.id == experiment_orm_model.configuration_id
    assert domain_model.order_list.id == experiment_orm_model.order_list_id
    assert domain_model.task_id == experiment_orm_model.task_id


def test_map_experiment_domain_to_orm() -> None:
    # Arrange
    experiment_domain_model = get_experiment_domain_model()

    # Act
    orm_model = map_experiment_domain_to_orm(experiment_domain_model)

    # Assert
    assert orm_model.id == experiment_domain_model.id
    assert orm_model.name == experiment_domain_model.name
    assert orm_model.status == experiment_domain_model.status
    assert orm_model.layout_id == experiment_domain_model.layout.id
    assert orm_model.configuration_id == experiment_domain_model.configuration.id
    assert orm_model.order_list_id == experiment_domain_model.order_list.id
    assert orm_model.task_id == experiment_domain_model.task_id
    assert orm_model.batch_id == experiment_domain_model.batch_id


def test_update_experiment_orm() -> None:
    # Arrange
    experiment_domain_model = get_experiment_domain_model()
    orm_model = get_experiment_orm_model()

    experiment_domain_model.name = "Updated Experiment Name"
    experiment_domain_model.status = ExperimentStatus.FAILED
    experiment_domain_model.task_id = "new-celery-task"

    # Act
    update_experiment_orm(domain_model=experiment_domain_model, orm_model=orm_model)

    # Assert
    assert orm_model.name == "Updated Experiment Name"
    assert orm_model.status == ExperimentStatus.FAILED
    assert orm_model.task_id == "new-celery-task"


def test_map_batch_orm_to_domain() -> None:
    # Arrange
    batch_orm_model = get_batch_orm_model()

    # Act
    domain_model = map_batch_orm_to_domain(batch_orm_model)

    # Assert
    assert domain_model.id == batch_orm_model.id
    assert domain_model.name == batch_orm_model.name
    assert domain_model.total_experiment_amount == batch_orm_model.total_experiment_amount
    assert len(domain_model.experiments) == len(batch_orm_model.experiments)


def test_map_batch_domain_to_orm() -> None:
    # Arrange
    batch_domain_model = get_batch_domain_model()

    # Act
    orm_model = map_batch_domain_to_orm(batch_domain_model)

    # Assert
    assert orm_model.id == batch_domain_model.id
    assert orm_model.name == batch_domain_model.name
    assert len(orm_model.experiments) == len(batch_domain_model.experiments)


def test_update_batch_orm() -> None:
    # Arrange
    batch_domain_model = get_batch_domain_model()
    orm_model = get_batch_orm_model()

    batch_domain_model.name = "Updated Batch Name"

    # Act
    update_batch_orm(domain_model=batch_domain_model, orm_model=orm_model)

    # Assert
    assert orm_model.name == "Updated Batch Name"
