from db.orm_models.batch import BatchORM
from db.orm_models.experiment import ExperimentORM
from domain.models.batch import BatchDomainModel
from domain.models.experiment import ExperimentDomainModel, Result
from mappers.orm.configuration_mapper import map_configuration_orm_to_domain
from mappers.orm.layout_mapper import map_layout_orm_to_domain
from mappers.orm.order_list_mapper import map_order_list_orm_to_domain


def map_experiment_orm_to_domain(orm_model: ExperimentORM) -> ExperimentDomainModel:
    """Maps the SQLAlchemy Experiment ORM object to the pure Domain Model.

    Args:
        orm_model: The SQLAlchemy Experiment ORM object.

    Returns:
        The pure Experiment Domain Model.
    """
    domain_result = None
    if orm_model.result is not None:
        domain_result = Result.model_validate(orm_model.result)
    domain_layout = map_layout_orm_to_domain(orm_model.layout)
    domain_configuration = map_configuration_orm_to_domain(orm_model.configuration)
    batch_name = orm_model.batch.name if orm_model.batch else None
    return ExperimentDomainModel(
        id=orm_model.id,
        name=orm_model.name,
        status=orm_model.status,
        layout=domain_layout,
        configuration=domain_configuration,
        order_list=map_order_list_orm_to_domain(orm_model.order_list),
        result=domain_result,
        created_at=orm_model.created_at,
        updated_at=orm_model.updated_at,
        finished_at=orm_model.finished_at,
        started_at=orm_model.started_at,
        task_id=orm_model.task_id,
        batch_id=orm_model.batch_id,
        batch_name=batch_name
    )


def map_experiment_domain_to_orm(domain_model: ExperimentDomainModel) -> ExperimentORM:
    """Maps a pure Experiment Domain Model to a SQLAlchemy ORM object.

    Args:
        domain_model: The pure Experiment Domain Model.

    Returns:
        The SQLAlchemy Experiment ORM object.
    """
    orm_result = domain_model.result.model_dump(mode='json') if domain_model.result is not None else None
    return ExperimentORM(
        id=domain_model.id,
        name=domain_model.name,
        status=domain_model.status,
        layout_id=domain_model.layout.id,
        configuration_id=domain_model.configuration.id,
        order_list_id=domain_model.order_list.id,
        result=orm_result,
        started_at=domain_model.started_at,
        finished_at=domain_model.finished_at,
        task_id=domain_model.task_id,
        batch_id=domain_model.batch_id
    )


def update_experiment_orm(domain_model: ExperimentDomainModel, orm_model: ExperimentORM) -> None:
    """Updates the ORM object with data from Domain Model.

    Args:
        domain_model: The pure Experiment Domain Model which holds updated data.
        orm_model: The SQLAlchemy Experiment ORM object which should be updated.
    """
    orm_result = domain_model.result.model_dump(mode='json') if domain_model.result is not None else None
    orm_model.name = domain_model.name
    orm_model.status = domain_model.status
    orm_model.layout_id = domain_model.layout.id
    orm_model.configuration_id = domain_model.configuration.id
    orm_model.order_list_id = domain_model.order_list.id
    orm_model.result = orm_result
    orm_model.task_id = domain_model.task_id
    orm_model.finished_at = domain_model.finished_at
    orm_model.started_at = domain_model.started_at
    orm_model.batch_id = domain_model.batch_id


def map_batch_orm_to_domain(orm_model: BatchORM) -> BatchDomainModel:
    """Maps the SQLAlchemy Batch ORM object to the pure Domain Model.

    Args:
        orm_model: The SQLAlchemy Batch ORM object.

    Returns:
        The pure Batch Domain Model.
    """
    return BatchDomainModel(
        id=orm_model.id,
        name=orm_model.name,
        total_experiment_amount=orm_model.total_experiment_amount,
        running_experiment_amount=orm_model.running_experiment_amount,
        queued_experiment_amount=orm_model.queued_experiment_amount,
        failed_experiment_amount=orm_model.failed_experiment_amount,
        finished_experiment_amount=orm_model.finished_experiment_amount,
        created_at=orm_model.created_at,
        updated_at=orm_model.updated_at,
        experiments=[map_experiment_orm_to_domain(experiment) for experiment in orm_model.experiments]
    )


def map_batch_domain_to_orm(domain_model: BatchDomainModel) -> BatchORM:
    """Maps a pure Batch Domain Model to a SQLAlchemy ORM object.

    Args:
        domain_model: The pure Batch Domain Model.

    Returns:
        The SQLAlchemy Batch ORM object.
    """
    return BatchORM(
        id=domain_model.id,
        name=domain_model.name,
        experiments=[map_experiment_domain_to_orm(experiment) for experiment in domain_model.experiments]
    )


def update_batch_orm(domain_model: BatchDomainModel, orm_model: BatchORM) -> None:
    """Updates name of the ORM object with data from Domain Model.

    Args:
        domain_model: The pure Batch Domain Model which holds updated data.
        orm_model: The SQLAlchemy Batch ORM object which should be updated.
    """
    orm_model.name = domain_model.name
