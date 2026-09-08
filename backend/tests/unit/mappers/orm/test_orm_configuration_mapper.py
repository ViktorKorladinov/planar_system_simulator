from db.orm_models.configuration import ConfigurationORM
from domain.models.configuration import ConfigurationDomainModel
from mappers.orm.configuration_mapper import (
    map_configuration_domain_to_orm,
    map_configuration_orm_to_domain,
    update_configuration_orm
)


def test_map_configuration_orm_to_domain(configuration_orm_model: ConfigurationORM) -> None:
    # Act
    domain_model = map_configuration_orm_to_domain(configuration_orm_model)

    # Assert
    assert domain_model.model_dump() == {
        "id": configuration_orm_model.id,
        "name": configuration_orm_model.name,
        "solver_type": configuration_orm_model.solver_type.value if hasattr(configuration_orm_model.solver_type,
                                                                            'value') else configuration_orm_model.solver_type,
        "interface_time": configuration_orm_model.interface_time,
        "dispensing_time": configuration_orm_model.dispensing_time,
        "mover_amount": configuration_orm_model.mover_amount,
        "time_limit": configuration_orm_model.time_limit,
        "batch_size": configuration_orm_model.batch_size,
        "process_amount": configuration_orm_model.process_amount,
        "warmup": configuration_orm_model.warmup,
        "dispense_rate": configuration_orm_model.dispense_rate,
        "viscosity_exponent": configuration_orm_model.viscosity_exponent,
        "mover_speed": configuration_orm_model.mover_speed,
        "mixer_primary_time": configuration_orm_model.mixer_primary_time,
        "mixer_final_time": configuration_orm_model.mixer_final_time,
        "capper_time": configuration_orm_model.capper_time,
        "created_at": configuration_orm_model.created_at,
        "updated_at": configuration_orm_model.updated_at
    }


def test_map_configuration_domain_to_orm(configuration_domain_model: ConfigurationDomainModel) -> None:
    # Act
    orm_model = map_configuration_domain_to_orm(configuration_domain_model)

    # Assert
    assert orm_model.id == configuration_domain_model.id
    assert orm_model.name == configuration_domain_model.name
    assert orm_model.solver_type == configuration_domain_model.solver_type
    assert orm_model.interface_time == configuration_domain_model.interface_time
    assert orm_model.dispensing_time == configuration_domain_model.dispensing_time
    assert orm_model.mover_amount == configuration_domain_model.mover_amount
    assert orm_model.time_limit == configuration_domain_model.time_limit
    assert orm_model.process_amount == configuration_domain_model.process_amount
    assert orm_model.warmup == configuration_domain_model.warmup
    assert orm_model.batch_size == configuration_domain_model.batch_size
    assert orm_model.dispense_rate == configuration_domain_model.dispense_rate
    assert orm_model.viscosity_exponent == configuration_domain_model.viscosity_exponent
    assert orm_model.mover_speed == configuration_domain_model.mover_speed
    assert orm_model.mixer_primary_time == configuration_domain_model.mixer_primary_time
    assert orm_model.mixer_final_time == configuration_domain_model.mixer_final_time
    assert orm_model.capper_time == configuration_domain_model.capper_time


def test_update_configuration_orm(configuration_domain_model: ConfigurationDomainModel,
                                  configuration_orm_model: ConfigurationORM) -> None:
    # Arrange
    configuration_domain_model.name = "Updated Config Name"
    configuration_domain_model.process_amount = 5

    # Act
    update_configuration_orm(domain_model=configuration_domain_model, orm_model=configuration_orm_model)

    # Assert
    assert configuration_orm_model.name == "Updated Config Name"
    assert configuration_orm_model.process_amount == 5
