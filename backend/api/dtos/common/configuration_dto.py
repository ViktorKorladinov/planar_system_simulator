from typing import Optional

from pydantic import BaseModel, Field

from domain.enums import SolverType


class ConfigurationDTO(BaseModel):
    """
    Data Transfer Object representing configuration of a single experiment.
    """
    name: Optional[str] = Field(
        default=None,
        description="Name of the configuration."
    )
    solver_type: SolverType = Field(
        ...,
        description="Type of the solver which should be used for this experiment."
    )
    interface_time: int = Field(
        ...,
        gt=-1,
        description="Time required for operations on the interface tile.",
        examples=["3"]
    )
    dispensing_time: int = Field(
        ...,
        gt=-1,
        description="Time required to dispense 1 unit of product.",
        examples=["10"]
    )
    mover_amount: int = Field(
        ...,
        gt=0,
        description="Amount of movers available for this experiment.",
        examples=["3"]
    )
    time_limit: int = Field(
        ...,
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
