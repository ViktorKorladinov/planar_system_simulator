from pydantic import BaseModel, Field

from domain.enums import ExperimentStatus


class ExperimentStatusUpdateDTO(BaseModel):
    """
    Data Transfer Object for internal Celery webhooks.
    """
    experiment_id: int = Field(
        ...,
        description="ID of the finished experiment."
    )
    status: ExperimentStatus = Field(
        ...,
        description="Status of the experiment."
    )
