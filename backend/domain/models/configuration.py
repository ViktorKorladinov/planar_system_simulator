from typing_extensions import Self
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator

from domain.enums import SolverType


class ConfigurationDomainModel(BaseModel):
    """
    Domain Entity for experiment configuration.
    Validates its own data.
    """
    model_config = ConfigDict(validate_assignment=True)

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
    interface_time: int = Field(
        ...,
        gt=-1,
        description="Time required for operations on the interface tile."
    )
    dispensing_time: int = Field(
        ...,
        gt=-1,
        description="Time required to dispense 1 unit of product."
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
    batch_size: Optional[int] = Field(
        default=None,
        gt=0,
        description="Amount of orders that should be processed in one batch (relevant for CPLEX solver)."
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
    created_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment creation."
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment completion."
    )

    # Ensure that batch size and warmup is provided when CPLEX medicine solver is selected.
    @model_validator(mode='after')
    def validate_batch_size_and_warmup_compatibility(self) -> Self:
        cplex_solver_is_selected = self.solver_type == SolverType.CPLEX_MEDICINE
        batch_size_is_provided = self.batch_size is not None
        warmup_is_provided = self.warmup is not None
        if cplex_solver_is_selected and not batch_size_is_provided:
            raise ValueError("Batch size must be provided when Cplex Medicine solver is selected.")
        if cplex_solver_is_selected and not warmup_is_provided:
            raise ValueError("Warmup must be provided when Cplex Medicine solver is selected.")
        if not cplex_solver_is_selected and batch_size_is_provided:
            raise ValueError("Selected solver doesn't support batch size.")
        if not cplex_solver_is_selected and warmup_is_provided:
            raise ValueError("Selected solver doesn't support warmup.")
        return self

    # Ensure that fields required by Cplex perfume solver are filled only when this solver is selected.
    @model_validator(mode='after')
    def validate_cplex_perfume_fields(self) -> Self:
        cplex_perfume_solver_is_selected = self.solver_type == SolverType.CPLEX_PERFUMES
        if cplex_perfume_solver_is_selected and self.dispense_rate is None:
            raise ValueError("Dispense rate must be provided when Cplex Perfume solver is selected.")
        if cplex_perfume_solver_is_selected and self.viscosity_exponent is None:
            raise ValueError("Viscosity exponent must be provided when Cplex Perfume solver is selected.")
        if cplex_perfume_solver_is_selected and self.mover_speed is None:
            raise ValueError("Mover speed must be provided when Cplex Perfume solver is selected.")
        if cplex_perfume_solver_is_selected and self.mixer_primary_time is None:
            raise ValueError("Mixer primary time must be provided when Cplex Perfume solver is selected.")
        if cplex_perfume_solver_is_selected and self.mixer_final_time is None:
            raise ValueError("Mixer final time must be provided when Cplex Perfume solver is selected.")
        if cplex_perfume_solver_is_selected and self.capper_time is None:
            raise ValueError("Capper time must be provided when Cplex Perfume solver is selected.")
        if not cplex_perfume_solver_is_selected and self.dispense_rate is not None:
            raise ValueError("Selected solver doesn't support dispense rate.")
        if not cplex_perfume_solver_is_selected and self.viscosity_exponent is not None:
            raise ValueError("Selected solver doesn't support viscosity exponent.")
        if not cplex_perfume_solver_is_selected and self.mover_speed is not None:
            raise ValueError("Selected solver doesn't support mover speed.")
        if not cplex_perfume_solver_is_selected and self.mixer_primary_time is not None:
            raise ValueError("Selected solver doesn't support mixer primary time.")
        if not cplex_perfume_solver_is_selected and self.mixer_final_time is not None:
            raise ValueError("Selected solver doesn't support mixer final time.")
        if not cplex_perfume_solver_is_selected and self.capper_time is not None:
            raise ValueError("Selected solver doesn't support capper time.")
        return self
