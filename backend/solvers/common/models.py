from typing_extensions import Self
from typing import List, Dict, Tuple, Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator

from domain.models.common.tile import Tile


class SimulationData(BaseModel):
    """
    Object representing data required for simulations.
    """
    row_amount: int = Field(
        ...,
        ge=1,
        description="Number of rows in the layout."
    )
    column_amount: int = Field(
        ...,
        ge=1,
        description="Number of columns in the layout."
    )
    filled: bool = Field(
        ...,
        description="Whether the layout is filled or not."
    )
    unavailable_coordinates: List[List[int]] = Field(
        ...,
        description="Coordinates of unavailable tiles in the layout."
    )
    coordinate_dict: Dict[str, List[Tuple[int, int]]] = Field(
        ...,
        description="Dictionary with tile types or dispensed types as keys and lists of tuples with coordinates as values. "
    )
    mover_amount: int = Field(
        ...,
        description="Amount of movers available for the experiment."
    )

class Task(BaseModel):
    """
    Immutable value object representing a single scheduled task.
    """
    model_config = ConfigDict(frozen=True)

    task_id: int = Field(
        ...,
        description="ID of the task."
    )
    order_id: int = Field(
        ...,
        description="ID of order to which the task belongs."
    )
    duration: int = Field(
        ...,
        gt=0,
        description="Duration of the task."
    )
    start: int = Field(
        ...,
        gt=-1,
        description="Start time of the task."
    )
    end: int = Field(
        ...,
        gt=-1,
        description="End time of the task."
    )
    tile: Tile = Field(
        ...,
        description="Tile on which the task is performed."
    )
    needed_dispensed_type: Optional[str] = Field(
        default=None,
        description="Type of the dispensed type needed by this task."
    )
    mover_id: int = Field(
        ...,
        description="ID of the mover which performs the task."
    )
    ticks_added: Optional[int] = Field(
        default=0,
        gt=-1,
        description="Ticks added to the task compared to initial schedule."
    )

    # Ensure that task starts before it ends.
    @model_validator(mode='after')
    def validate_start_and_end_times(self) -> Self:
        if not self.start <= self.end:
            raise ValueError("Task can't end before it starts.")
        return self


class Schedule(BaseModel):
    """
    Immutable value object representing schedule for movers.
    """
    model_config = ConfigDict(frozen=True)

    tasks: List[Task] = Field(
        ...,
        description="Scheduled tasks."
    )
