from db.orm_models.configuration import ConfigurationORM
from domain.models.configuration import ConfigurationDomainModel


def map_configuration_orm_to_domain(orm_model: ConfigurationORM) -> ConfigurationDomainModel:
    """Maps the SQLAlchemy Configuration ORM object to the pure Domain Model.

    Args:
        orm_model: The SQLAlchemy Configuration ORM object.

    Returns:
        The pure Configuration Domain Model.
    """
    return ConfigurationDomainModel(
        id=orm_model.id,
        name=orm_model.name,
        solver_type=orm_model.solver_type,
        interface_time=orm_model.interface_time,
        dispensing_time=orm_model.dispensing_time,
        mover_amount=orm_model.mover_amount,
        time_limit=orm_model.time_limit,
        batch_size=orm_model.batch_size,
        process_amount=orm_model.process_amount,
        warmup=orm_model.warmup,
        dispense_rate=orm_model.dispense_rate,
        viscosity_exponent=orm_model.viscosity_exponent,
        mover_speed=orm_model.mover_speed,
        mixer_primary_time=orm_model.mixer_primary_time,
        mixer_final_time=orm_model.mixer_final_time,
        capper_time=orm_model.capper_time,
        created_at=orm_model.created_at,
        updated_at=orm_model.updated_at
    )


def map_configuration_domain_to_orm(domain_model: ConfigurationDomainModel) -> ConfigurationORM:
    """Maps a pure Configuration Domain Model to a SQLAlchemy ORM object.

    Args:
        domain_model: The pure Configuration Domain Model.

    Returns:
        The SQLAlchemy Configuration ORM object.
    """
    return ConfigurationORM(
        id=domain_model.id,
        name=domain_model.name,
        solver_type=domain_model.solver_type,
        interface_time=domain_model.interface_time,
        dispensing_time=domain_model.dispensing_time,
        mover_amount=domain_model.mover_amount,
        time_limit=domain_model.time_limit,
        batch_size=domain_model.batch_size,
        process_amount=domain_model.process_amount,
        warmup=domain_model.warmup,
        dispense_rate=domain_model.dispense_rate,
        viscosity_exponent=domain_model.viscosity_exponent,
        mover_speed=domain_model.mover_speed,
        mixer_primary_time=domain_model.mixer_primary_time,
        mixer_final_time=domain_model.mixer_final_time,
        capper_time=domain_model.capper_time,
    )


def update_configuration_orm(domain_model: ConfigurationDomainModel, orm_model: ConfigurationORM) -> None:
    """Updates the ORM object with data from Domain Model.

    Args:
        domain_model: The pure Configuration Domain Model which holds updated data.
        orm_model: The SQLAlchemy Configuration ORM object which should be updated.
    """
    orm_model.name = domain_model.name
    orm_model.process_amount = domain_model.process_amount
