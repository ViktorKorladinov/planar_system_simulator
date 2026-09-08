from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from api.dtos.common.configuration_dto import ConfigurationDTO
from domain.enums import SolverType


class ConfigurationResponseDTO(ConfigurationDTO):
    id: int = Field(
        ...,
        description='ID of the configuration.'
    )
    created_at: datetime = Field(
        ...,
        description="Date of the experiment creation."
    )
    updated_at: datetime = Field(
        default=None,
        description="Date of the experiment completion."
    )


class ConfigurationSummaryDTO(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = Field(
        ...,
        min_length=1,
        description="The name of the configuration.",
    )
    solver_type: SolverType = Field(
        ...,
        description="Type of the solver which should be used for this experiment."
    )
    mover_amount: int = Field(
        ...,
        gt=0,
        description="Amount of movers available for this experiment."
    )
    time_limit: int = Field(
        ...,
        gt=0,
        description="Time limit for this experiment in seconds."
    )
    interface_time: Optional[int] = Field(
        default=None,
        gt=-1,
        description="Time required for operations on the interface tile.",
        examples=["3"]
    )
    dispensing_time: Optional[int] = Field(
        default=None,
        gt=-1,
        description="Time required to dispense 1 unit of product.",
        examples=["10"]
    )
    batch_size: Optional[int] = Field(
        default=None,
        gt=0,
        description="Amount of orders that should be processed in one batch (relevant for CPLEX solver).",
        examples=["100"]
    )
    process_amount: int = Field(
        ...,
        description="Amount of processes that can be used by solver."
    )
    warmup: Optional[bool] = Field(
        default=None,
        description="True if warmup should be used for experiment."
    )
    dispense_rate: Optional[float] = Field(
        default=None,
        description="Dispense rate (s / ml)."
    )
    viscosity_exponent: Optional[float] = Field(
        default=None,
        description="Viscosity scaling exponent."
    )
    mover_speed: Optional[float] = Field(
        default=None,
        description="Mover speed (s per tile)."
    )
    mixer_primary_time: Optional[int] = Field(
        default=None,
        description="Mixer primary agitation time in seconds (before solvents)."
    )
    mixer_final_time: Optional[int] = Field(
        default=None,
        description="Mixer final agitation time in seconds (after solvents)."
    )
    capper_time: Optional[int] = Field(
        default=None,
        description="Capper agitation time in seconds."
    )
    created_at: datetime = Field(
        default=None,
        description="Date of the experiment creation."
    )
    updated_at: datetime = Field(
        default=None,
        description="Date of the experiment completion."
    )


class ConfigurationBatchGetResponseDTO(BaseModel):
    """
    Data Transfer Object representing batch configuration response.
    """
    total: int = Field(
        ...,
        description="Total amount of pages."
    )
    page: int = Field(
        ...,
        description="Page number."
    )
    size: int = Field(
        ...,
        description="Amount of simulations on the page."
    )
    configurations: List[ConfigurationSummaryDTO] = Field(
        ...,
        description='List of layouts on the page.'
    )
    pass


class ConfigurationSingleCreateResponseDTO(ConfigurationResponseDTO):
    """
    Data Transfer Object representing a single configuration create response.
    """
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Name of the configuration."
    )
    solver_type: Optional[SolverType] = Field(
        default=None,
        description="Type of the solver which should be used for this experiment."
    )
    interface_time: Optional[int] = Field(
        default=None,
        gt=-1,
        description="Time required for operations on the interface tile.",
        examples=["3"]
    )
    dispensing_time: Optional[int] = Field(
        default=None,
        gt=-1,
        description="Time required to dispense 1 unit of product.",
        examples=["10"]
    )
    mover_amount: Optional[int] = Field(
        default=None,
        gt=0,
        description="Amount of movers available for this experiment.",
        examples=["3"]
    )
    time_limit: Optional[int] = Field(
        default=None,
        gt=0,
        description="Time limit for this experiment in seconds.",
        examples=["60"]
    )
    batch_size: Optional[int] = Field(
        default=None,
        gt=0,
        description="Amount of orders that should be processed in one batch (relevant for CPLEX solver).",
        examples=["100"]
    )
    process_amount: Optional[int] = Field(
        default=None,
        description="Amount of processes that can be used by solver."
    )
    warmup: Optional[bool] = Field(
        default=None,
        description="True if warmup should be used for experiment."
    )
    dispense_rate: Optional[float] = Field(
        default=None,
        description="Dispense rate (s / ml)."
    )
    viscosity_exponent: Optional[float] = Field(
        default=None,
        description="Viscosity scaling exponent."
    )
    mover_speed: Optional[float] = Field(
        default=None,
        description="Mover speed (s per tile)."
    )
    mixer_primary_time: Optional[int] = Field(
        default=None,
        description="Mixer primary agitation time in seconds (before solvents)."
    )
    mixer_final_time: Optional[int] = Field(
        default=None,
        description="Mixer final agitation time in seconds (after solvents)."
    )
    capper_time: Optional[int] = Field(
        default=None,
        description="Capper agitation time in seconds."
    )
    id: Optional[int] = Field(
        default=None,
        description='ID of the configuration.'
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment creation."
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment completion."
    )
    is_dry_run: bool = Field(
        default=False,
        description="True if this was only a validation run."
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Validation errors in plain text caused by violation of domain constraints."
    )


class ConfigurationSingleGetResponseDTO(ConfigurationResponseDTO):
    """
    Data Transfer Object representing a single configuration get response.
    """
    pass
