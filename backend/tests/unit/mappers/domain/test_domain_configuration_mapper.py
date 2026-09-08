from datetime import datetime
from typing import List

from api.dtos.common.configuration_dto import ConfigurationDTO
from api.dtos.requests.configuration import ConfigurationSingleCreateRequestDTO
from domain.models.configuration import ConfigurationDomainModel
from mappers.domain.configuration_mapper import (
    map_configuration_dto_to_domain,
    map_configuration_single_create_request_dto_to_domain,
    map_configuration_domain_to_batch_get_response_dto,
    map_domain_to_configuration_dto,
    map_configuration_domain_to_single_create_response_dto,
    map_configuration_domain_to_single_get_response_dto
)
from tests.factories.configuration_factory import get_configuration_domain_model


def test_get_name_returns_configuration_name_when_set(configuration_domain_model: ConfigurationDomainModel) -> None:
    # Arrange
    configuration_domain_model.created_at = datetime.now()
    configuration_domain_model.updated_at = datetime.now()

    # Act
    dto = map_configuration_domain_to_single_get_response_dto(configuration_domain_model)

    # Assert
    assert dto.name == configuration_domain_model.name


def test_map_configuration_dto_to_domain(configuration_dto: ConfigurationDTO) -> None:
    # Act
    domain_model = map_configuration_dto_to_domain(configuration_dto)

    # Assert
    assert domain_model.model_dump() == {
        "id": None,
        "name": configuration_dto.name,
        "solver_type": configuration_dto.solver_type,
        "interface_time": configuration_dto.interface_time,
        "dispensing_time": configuration_dto.dispensing_time,
        "mover_amount": configuration_dto.mover_amount,
        "time_limit": configuration_dto.time_limit,
        "batch_size": configuration_dto.batch_size,
        "process_amount": configuration_dto.process_amount,
        "warmup": configuration_dto.warmup,
        "dispense_rate": configuration_dto.dispense_rate,
        "viscosity_exponent": configuration_dto.viscosity_exponent,
        "mover_speed": configuration_dto.mover_speed,
        "mixer_primary_time": configuration_dto.mixer_primary_time,
        "mixer_final_time": configuration_dto.mixer_final_time,
        "capper_time": configuration_dto.capper_time,
        "created_at": None,
        "updated_at": None
    }


def test_map_configuration_single_create_request_dto_to_domain(
        configuration_single_create_request_dto: ConfigurationSingleCreateRequestDTO) -> None:
    # Act
    domain_model = map_configuration_single_create_request_dto_to_domain(configuration_single_create_request_dto)

    # Assert
    assert domain_model.model_dump() == {
        "id": None,
        "name": configuration_single_create_request_dto.name,
        "solver_type": configuration_single_create_request_dto.solver_type,
        "interface_time": configuration_single_create_request_dto.interface_time,
        "dispensing_time": configuration_single_create_request_dto.dispensing_time,
        "mover_amount": configuration_single_create_request_dto.mover_amount,
        "time_limit": configuration_single_create_request_dto.time_limit,
        "batch_size": configuration_single_create_request_dto.batch_size,
        "process_amount": configuration_single_create_request_dto.process_amount,
        "warmup": configuration_single_create_request_dto.warmup,
        "dispense_rate": configuration_single_create_request_dto.dispense_rate,
        "viscosity_exponent": configuration_single_create_request_dto.viscosity_exponent,
        "mover_speed": configuration_single_create_request_dto.mover_speed,
        "mixer_primary_time": configuration_single_create_request_dto.mixer_primary_time,
        "mixer_final_time": configuration_single_create_request_dto.mixer_final_time,
        "capper_time": configuration_single_create_request_dto.capper_time,
        "created_at": None,
        "updated_at": None
    }


def test_map_configuration_domain_to_batch_get_response_dto() -> None:
    # Arrange
    domain_model_a = get_configuration_domain_model(id=1)
    domain_model_a.created_at = datetime.now()
    domain_model_a.updated_at = datetime.now()
    domain_model_b = get_configuration_domain_model(id=2)
    domain_model_b.created_at = datetime.now()
    domain_model_b.updated_at = datetime.now()
    page = 1
    size = 3
    total = 5

    # Act
    dto = map_configuration_domain_to_batch_get_response_dto(
        domain_models=[domain_model_a, domain_model_b],
        page=page,
        size=size,
        total=total
    )

    # Assert
    assert dto.total == total
    assert dto.page == page
    assert dto.size == size
    assert [configuration.id for configuration in dto.configurations] == [1, 2]


def test_map_domain_to_configuration_dto(configuration_domain_model: ConfigurationDomainModel) -> None:
    # Act
    dto = map_domain_to_configuration_dto(configuration_domain_model)

    # Assert
    assert dto.model_dump() == {
        "name": configuration_domain_model.name,
        "solver_type": configuration_domain_model.solver_type,
        "interface_time": configuration_domain_model.interface_time,
        "dispensing_time": configuration_domain_model.dispensing_time,
        "mover_amount": configuration_domain_model.mover_amount,
        "time_limit": configuration_domain_model.time_limit,
        "batch_size": configuration_domain_model.batch_size,
        "process_amount": configuration_domain_model.process_amount,
        "warmup": configuration_domain_model.warmup,
        "dispense_rate": configuration_domain_model.dispense_rate,
        "viscosity_exponent": configuration_domain_model.viscosity_exponent,
        "mover_speed": configuration_domain_model.mover_speed,
        "mixer_primary_time": configuration_domain_model.mixer_primary_time,
        "mixer_final_time": configuration_domain_model.mixer_final_time,
        "capper_time": configuration_domain_model.capper_time,
    }


def test_map_configuration_domain_to_single_create_response_dto(
        configuration_domain_model: ConfigurationDomainModel) -> None:
    # Arrange
    configuration_domain_model.created_at = datetime.now()
    configuration_domain_model.updated_at = datetime.now()
    errors: List[str] = []
    is_dry_run = False

    # Act
    dto = map_configuration_domain_to_single_create_response_dto(
        domain_model=configuration_domain_model,
        errors=errors,
        is_dry_run=is_dry_run
    )

    # Assert
    assert dto.model_dump() == {
        "id": configuration_domain_model.id,
        "name": configuration_domain_model.name,
        "solver_type": configuration_domain_model.solver_type,
        "interface_time": configuration_domain_model.interface_time,
        "dispensing_time": configuration_domain_model.dispensing_time,
        "mover_amount": configuration_domain_model.mover_amount,
        "time_limit": configuration_domain_model.time_limit,
        "batch_size": configuration_domain_model.batch_size,
        "process_amount": configuration_domain_model.process_amount,
        "warmup": configuration_domain_model.warmup,
        "dispense_rate": configuration_domain_model.dispense_rate,
        "viscosity_exponent": configuration_domain_model.viscosity_exponent,
        "mover_speed": configuration_domain_model.mover_speed,
        "mixer_primary_time": configuration_domain_model.mixer_primary_time,
        "mixer_final_time": configuration_domain_model.mixer_final_time,
        "capper_time": configuration_domain_model.capper_time,
        "created_at": configuration_domain_model.created_at,
        "updated_at": configuration_domain_model.updated_at,
        "errors": errors,
        "is_dry_run": is_dry_run
    }


def test_map_configuration_domain_to_single_create_response_dto_when_domain_model_is_none() -> None:
    # Arrange
    errors: List[str] = ["Validation error"]
    is_dry_run = True

    # Act
    dto = map_configuration_domain_to_single_create_response_dto(
        domain_model=None,
        errors=errors,
        is_dry_run=is_dry_run
    )

    # Assert
    assert dto.model_dump() == {
        "id": None,
        "name": None,
        "solver_type": None,
        "interface_time": None,
        "dispensing_time": None,
        "mover_amount": None,
        "time_limit": None,
        "batch_size": None,
        "process_amount": None,
        "warmup": None,
        "dispense_rate": None,
        "viscosity_exponent": None,
        "mover_speed": None,
        "mixer_primary_time": None,
        "mixer_final_time": None,
        "capper_time": None,
        "created_at": None,
        "updated_at": None,
        "errors": errors,
        "is_dry_run": is_dry_run
    }


def test_map_configuration_domain_to_single_get_response_dto(
        configuration_domain_model: ConfigurationDomainModel) -> None:
    # Arrange
    configuration_domain_model.created_at = datetime.now()
    configuration_domain_model.updated_at = datetime.now()

    # Act
    dto = map_configuration_domain_to_single_get_response_dto(configuration_domain_model)

    # Assert
    assert dto.model_dump() == {
        "id": configuration_domain_model.id,
        "name": configuration_domain_model.name,
        "solver_type": configuration_domain_model.solver_type,
        "interface_time": configuration_domain_model.interface_time,
        "dispensing_time": configuration_domain_model.dispensing_time,
        "mover_amount": configuration_domain_model.mover_amount,
        "time_limit": configuration_domain_model.time_limit,
        "batch_size": configuration_domain_model.batch_size,
        "process_amount": configuration_domain_model.process_amount,
        "warmup": configuration_domain_model.warmup,
        "dispense_rate": configuration_domain_model.dispense_rate,
        "viscosity_exponent": configuration_domain_model.viscosity_exponent,
        "mover_speed": configuration_domain_model.mover_speed,
        "mixer_primary_time": configuration_domain_model.mixer_primary_time,
        "mixer_final_time": configuration_domain_model.mixer_final_time,
        "capper_time": configuration_domain_model.capper_time,
        "created_at": configuration_domain_model.created_at,
        "updated_at": configuration_domain_model.updated_at
    }
