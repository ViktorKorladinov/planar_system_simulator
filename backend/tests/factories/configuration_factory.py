from typing import Optional

from api.dtos.common.configuration_dto import ConfigurationDTO
from api.dtos.requests.configuration import ConfigurationSingleCreateRequestDTO
from db.orm_models.configuration import ConfigurationORM
from domain.enums import SolverType
from domain.models.configuration import ConfigurationDomainModel


def get_configuration_domain_model(
        id: int = 3,
        name: str = "Test Config",
        solver_type: SolverType = SolverType.CPLEX_PERFUMES,
        interface_time: int = 3,
        dispensing_time: int = 1,
        mover_amount: int = 4,
        time_limit: int = 60,
        process_amount: int = 3,
        warmup: bool = None,
        batch_size: int = None,
        dispense_rate: Optional[float] = 4.5,
        viscosity_exponent: Optional[float] = 3.2,
        mover_speed: Optional[float] = 1,
        mixer_primary_time: Optional[int] = 5,
        mixer_final_time: Optional[int] = 3,
        capper_time: Optional[int] = 6

) -> ConfigurationDomainModel:
    """Factory method to return a configuration domain model.

    Args:
        id: Configuration ID. Defaults to 3.
        name: Configuration name. Defaults to "Test Config".
        solver_type: Solver type. Defaults to SolverType.CPLEX.
        interface_time: Interface time. Defaults to 3.
        dispensing_time: Dispensing time. Defaults to 1.
        mover_amount: Mover amount. Defaults to 4.
        time_limit: Time limit. Defaults to 60.
        process_amount: Process amount. Defaults to 3.
        warmup: Warmup. Defaults to None.
        batch_size: Batch size. Defaults to None.
        dispense_rate: Dispense rate (s / ml).
        viscosity_exponent: Viscosity scaling exponent.
        mover_speed: Mover speed (s per tile).
        mixer_primary_time: Mixer primary agitation time in seconds (before solvents).
        mixer_final_time: Mixer final agitation time in seconds (after solvents).
        capper_time: Capper agitation time in seconds.

    Returns:
        Configuration domain model.
    """
    return ConfigurationDomainModel(
        id=id,
        name=name,
        solver_type=solver_type,
        interface_time=interface_time,
        dispensing_time=dispensing_time,
        mover_amount=mover_amount,
        time_limit=time_limit,
        process_amount=process_amount,
        warmup=warmup,
        batch_size=batch_size,
        dispense_rate=dispense_rate,
        viscosity_exponent=viscosity_exponent,
        mover_speed=mover_speed,
        mixer_primary_time=mixer_primary_time,
        mixer_final_time=mixer_final_time,
        capper_time=capper_time
    )


def get_configuration_orm_model(
        id: int = 3,
        name: str = "Test Config",
        solver_type: SolverType = SolverType.CPLEX_PERFUMES,
        interface_time: int = 3,
        dispensing_time: int = 1,
        mover_amount: int = 4,
        time_limit: int = 60,
        process_amount: int = 3,
        warmup: bool = None,
        batch_size: int = None,
        dispense_rate: Optional[float] = 4.5,
        viscosity_exponent: Optional[float] = 3.2,
        mover_speed: Optional[float] = 1,
        mixer_primary_time: Optional[int] = 5,
        mixer_final_time: Optional[int] = 3,
        capper_time: Optional[int] = 6
) -> ConfigurationORM:
    """Factory method to return a configuration ORM model.

        Args:
            id: Configuration ID. Defaults to 3.
            name: Configuration name. Defaults to "Test Config".
            solver_type: Solver type. Defaults to SolverType.CPLEX.
            interface_time: Interface time. Defaults to 3.
            dispensing_time: Dispensing time. Defaults to 1.
            mover_amount: Mover amount. Defaults to 4.
            time_limit: Time limit. Defaults to 60.
            process_amount: Process amount. Defaults to 3.
            warmup: Warmup. Defaults to None.
            batch_size: Batch size. Defaults to None.
            dispense_rate: Dispense rate (s / ml).
            viscosity_exponent: Viscosity scaling exponent.
            mover_speed: Mover speed (s per tile).
            mixer_primary_time: Mixer primary agitation time in seconds (before solvents).
            mixer_final_time: Mixer final agitation time in seconds (after solvents).
            capper_time: Capper agitation time in seconds.

        Returns:
            Configuration ORM model.
        """
    return ConfigurationORM(
        id=id,
        name=name,
        solver_type=solver_type,
        interface_time=interface_time,
        dispensing_time=dispensing_time,
        mover_amount=mover_amount,
        time_limit=time_limit,
        process_amount=process_amount,
        warmup=warmup,
        batch_size=batch_size,
        dispense_rate=dispense_rate,
        viscosity_exponent=viscosity_exponent,
        mover_speed=mover_speed,
        mixer_primary_time=mixer_primary_time,
        mixer_final_time=mixer_final_time,
        capper_time=capper_time
    )


def get_configuration_dto() -> ConfigurationDTO:
    """Returns configuration DTO.

    Returns:
        Configuration DTO.
    """
    return ConfigurationDTO(
        name="Test Config",
        solver_type=SolverType.CPLEX_PERFUMES,
        interface_time=3,
        dispensing_time=1,
        mover_amount=3,
        time_limit=60,
        batch_size=None,
        process_amount=3,
        warmup=None,
        dispense_rate=0.1,
        viscosity_exponent=0.5,
        mover_speed=1,
        mixer_primary_time=2,
        mixer_final_time=6,
        capper_time=3
    )


def get_configuration_single_create_request_dto() -> ConfigurationSingleCreateRequestDTO:
    """Returns configuration single create request DTO.

    Returns:
        Configuration single create request DTO.
    """
    return ConfigurationSingleCreateRequestDTO(
        name="Test Config",
        solver_type=SolverType.CPLEX_PERFUMES,
        interface_time=3,
        dispensing_time=1,
        mover_amount=3,
        time_limit=60,
        batch_size=None,
        process_amount=3,
        warmup=None,
        dispense_rate=0.1,
        viscosity_exponent=0.5,
        mover_speed=1,
        mixer_primary_time=2,
        mixer_final_time=6,
        capper_time=3
    )
