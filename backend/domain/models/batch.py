from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from domain.models.experiment import ExperimentDomainModel


class BatchDomainModel(BaseModel):
    """
    Domain Entity representing batch of experiments.
    Handles its own state changes and validates its own data.
    """
    model_config = ConfigDict(validate_assignment=True)

    id: Optional[int] = None
    name: Optional[str] = Field(
        ...,
        min_length=1,
        description="The name of the batch.",
    )
    experiments: List["ExperimentDomainModel"] = Field(
        ...,
        description="A list of experiments belonging to this batch.",
    )
    total_experiment_amount: int = Field(
        default=0,
        description="Total amount of experiments.",
    )
    queued_experiment_amount: int = Field(
        default=0,
        description="Total amount of experiments.",
    )
    finished_experiment_amount: int = Field(
        default=0,
        description="Total amount of experiments.",
    )
    running_experiment_amount: int = Field(
        default=0,
        description="Total amount of experiments.",
    )
    failed_experiment_amount: int = Field(
        default=0,
        description="Total amount of experiments.",
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Date of the batch creation."
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Date of the batch update."
    )
