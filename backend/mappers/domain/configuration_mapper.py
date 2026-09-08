from typing import List, Optional

from api.dtos.common.configuration_dto import ConfigurationDTO
from api.dtos.requests.configuration import ConfigurationSingleCreateRequestDTO
from api.dtos.responses.configuration import ConfigurationBatchGetResponseDTO, ConfigurationSingleCreateResponseDTO, \
    ConfigurationSingleGetResponseDTO, ConfigurationSummaryDTO
from domain.models.configuration import ConfigurationDomainModel


def map_configuration_dto_to_domain(dto: ConfigurationDTO) -> ConfigurationDomainModel:
    """Maps an ConfigurationDTO instance to a configuration domain model.

    Args:
        dto: The Data Transfer Object containing configuration details.

    Returns:
        A domain model instance of the configuration.
    """
    return ConfigurationDomainModel(
        id=None,
        name=dto.name,
        solver_type=dto.solver_type,
        interface_time=dto.interface_time,
        dispensing_time=dto.dispensing_time,
        mover_amount=dto.mover_amount,
        time_limit=dto.time_limit,
        batch_size=dto.batch_size,
        process_amount=dto.process_amount,
        warmup=dto.warmup,
        dispense_rate=dto.dispense_rate,
        viscosity_exponent=dto.viscosity_exponent,
        mover_speed=dto.mover_speed,
        mixer_primary_time=dto.mixer_primary_time,
        mixer_final_time=dto.mixer_final_time,
        capper_time=dto.capper_time
    )


def map_configuration_single_create_request_dto_to_domain(
        dto: ConfigurationSingleCreateRequestDTO) -> ConfigurationDomainModel:
    """Maps an ConfigurationSingleCreateRequestDTO instance to a configuration domain model.

    Args:
        dto: The Data Transfer Object containing configuration details.

    Returns:
        A domain model instance of the configuration.
    """
    return ConfigurationDomainModel(
        id=None,
        name=dto.name,
        solver_type=dto.solver_type,
        interface_time=dto.interface_time,
        dispensing_time=dto.dispensing_time,
        mover_amount=dto.mover_amount,
        time_limit=dto.time_limit,
        batch_size=dto.batch_size,
        process_amount=dto.process_amount,
        warmup=dto.warmup,
        dispense_rate=dto.dispense_rate,
        viscosity_exponent=dto.viscosity_exponent,
        mover_speed=dto.mover_speed,
        mixer_primary_time=dto.mixer_primary_time,
        mixer_final_time=dto.mixer_final_time,
        capper_time=dto.capper_time
    )


def map_configuration_domain_to_summary_dto(domain_model: ConfigurationDomainModel) -> ConfigurationSummaryDTO:
    """Converts configuration domain model into a Data Transfer Object.

        Args:
            domain_model: The source domain entity to be mapped.

        Returns:
            A DTO representation of the configuration summary.
        """
    return ConfigurationSummaryDTO(
        id=domain_model.id,
        name=domain_model.name,
        solver_type=domain_model.solver_type,
        mover_amount=domain_model.mover_amount,
        time_limit=domain_model.time_limit,
        process_amount=domain_model.process_amount,
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at,
        batch_size=domain_model.batch_size,
        warmup=domain_model.warmup,
        interface_time=domain_model.interface_time,
        dispensing_time=domain_model.dispensing_time,
        dispense_rate=domain_model.dispense_rate,
        viscosity_exponent=domain_model.viscosity_exponent,
        mover_speed=domain_model.mover_speed,
        mixer_primary_time=domain_model.mixer_primary_time,
        mixer_final_time=domain_model.mixer_final_time,
        capper_time=domain_model.capper_time
    )


def map_configuration_domain_to_batch_get_response_dto(
        domain_models: List[ConfigurationDomainModel],
        page: int,
        size: int,
        total: int
) -> ConfigurationBatchGetResponseDTO:
    """Converts configuration domain models into a Data Transfer Object.

    Args:
        domain_models: The source domain entities to be mapped.
        page: The current page number.
        size: The total number of configurations on one page.
        total: The total number of configurations.

    Returns:
        A DTO representation of the configuration batch get response.
    """
    return ConfigurationBatchGetResponseDTO(
        configurations=[map_configuration_domain_to_summary_dto(model) for model in domain_models],
        page=page,
        size=size,
        total=total
    )


def map_domain_to_configuration_dto(domain_model: ConfigurationDomainModel) -> ConfigurationDTO:
    """Converts a configuration domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the configuration.
    """
    return ConfigurationDTO(
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
        capper_time=domain_model.capper_time
    )


def map_configuration_domain_to_single_create_response_dto(
        domain_model: Optional[ConfigurationDomainModel],
        errors: List[str],
        is_dry_run: bool
) -> ConfigurationSingleCreateResponseDTO:
    """Converts a configuration domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.
        errors: List of validation errors encountered.
        is_dry_run: True if this was only a validation run.

    Returns:
        A DTO representation of the configuration single create response.
    """
    if domain_model is None:
        return ConfigurationSingleCreateResponseDTO(
            id=None,
            name=None,
            solver_type=None,
            interface_time=None,
            dispensing_time=None,
            mover_amount=None,
            time_limit=None,
            batch_size=None,
            process_amount=None,
            warmup=None,
            created_at=None,
            updated_at=None,
            errors=errors,
            is_dry_run=is_dry_run,
            dispense_rate=None,
            viscosity_exponent=None,
            mover_speed=None,
            mixer_primary_time=None,
            mixer_final_time=None,
            capper_time=None
        )
    return ConfigurationSingleCreateResponseDTO(
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
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at,
        errors=errors,
        is_dry_run=is_dry_run
    )


def map_configuration_domain_to_single_get_response_dto(
        domain_model: ConfigurationDomainModel) -> ConfigurationSingleGetResponseDTO:
    """Converts a configuration domain model into a Data Transfer Object.

    Args:
        domain_model: The source domain entity to be mapped.

    Returns:
        A DTO representation of the configuration single get response.
    """
    return ConfigurationSingleGetResponseDTO(
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
        created_at=domain_model.created_at,
        updated_at=domain_model.updated_at
    )
