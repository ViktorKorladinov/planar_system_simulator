from datetime import datetime
from typing import Optional, List

from pydantic import Field, BaseModel

from api.dtos.common.configuration_dto import ConfigurationDTO
from api.dtos.common.ingredient_list_dto import IngredientListDTO
from api.dtos.common.layout_dto import LayoutBasicDTO
from api.dtos.common.order_list_dto import OrderListDTO
from domain.enums import ExperimentStatus, LayoutType, SolverType


class ExperimentFullResponseDTO(BaseModel):
    """
    Data Transfer Object representing full experiment create response.
    """
    id: int = Field(
        ...,
        description="ID of the experiment."
    )
    name: str = Field(
        ...,
        description="Name of the experiment."
    )
    layout_id: int = Field(
        ...,
        description="ID of the layout which should be used for the experiment."
    )
    layout: LayoutBasicDTO = Field(
        ...,
        description="Layout which should be used for the experiment."
    )
    configuration_id: int = Field(
        ...,
        description="ID of the configuration which should be used for the experiment."
    )
    configuration: ConfigurationDTO = Field(
        ...,
        description="Configuration which should be used for the experiment."
    )
    ingredient_list_id: int = Field(
        ...,
        description="ID of the ingredient list."
    )
    ingredient_list: IngredientListDTO = Field(
        ...,
        description="Ingredients that should be used for this layout."
    )
    order_list_id: int = Field(
        ...,
        description="ID of the order list."
    )
    order_list: OrderListDTO = Field(
        ...,
        description="Orders that should be completed in this experiment."
    )
    batch_id: Optional[int] = Field(
        ...,
        description="ID of the batch to which this experiment belongs."
    )
    batch_name: Optional[str] = Field(
        ...,
        description="Name of the batch to which this experiment belongs."
    )
    status: ExperimentStatus = Field(
        ...,
        description="Status of the experiment."
    )
    created_at: datetime = Field(
        ...,
        description="Date of the experiment creation."
    )
    updated_at: datetime = Field(
        default=None,
        description="Date of the experiment completion."
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment start."
    )
    finished_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment finish."
    )


class ExperimentSummaryResponseDTO(BaseModel):
    """
    Data Transfer Object representing experiment summary.
    """
    id: int = Field(
        ...,
        description="ID of the experiment."
    )
    name: str = Field(
        ...,
        description="Name of the experiment."
    )
    status: ExperimentStatus = Field(
        ...,
        description="Status of the experiment."
    )
    created_at: datetime = Field(
        ...,
        description="Date of the experiment creation."
    )
    updated_at: datetime = Field(
        default=None,
        description="Date of the experiment completion."
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment start."
    )
    finished_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment finish."
    )
    batch_id: Optional[int] = Field(
        ...,
        description="ID of the batch to which this experiment belongs."
    )
    batch_name: Optional[str] = Field(
        ...,
        description="Name of the batch to which this experiment belongs."
    )
    tile_amount: int = Field(
        ...,
        description="Amount of tiles on the layout."
    )
    interface_amount: int = Field(
        ...,
        description="Amount of interfaces on the layout."
    )
    dispenser_amount: int = Field(
        ...,
        description="Amount of dispensers on the layout."
    )
    layout_id: int = Field(
        ...,
        description="ID of the layout used for the experiment."
    )
    layout_type: LayoutType = Field(
        ...,
        description="Type of the layout."
    )
    layout_name: str = Field(
        ...,
        description="Name of the layout."
    )
    configuration_id: int = Field(
        ...,
        description="ID of the configuration used for the experiment."
    )
    configuration_name: str = Field(
        ...,
        description="Name of the configuration."
    )
    solver_type: SolverType = Field(
        ...,
        description="Type of the solver used for the experiment."
    )
    mover_amount: int = Field(
        ...,
        description="Amount of movers used for the experiment."
    )
    time_limit: int = Field(
        ...,
        description="Time limit for the experiment."
    )
    interface_time: int = Field(
        default=None,
        gt=-1,
        description="Time required for operations on the interface tile.",
        examples=["3"]
    )
    dispensing_time: int = Field(
        default=None,
        gt=-1,
        description="Time required to dispense 1 unit of product.",
        examples=["10"]
    )
    batch_size: Optional[int] = Field(
        ...,
        description="Batch size used for the experiment."
    )
    warmup: Optional[bool] = Field(
        default=None,
        description="True if warmup should be used for experiment."
    )
    process_amount: int = Field(
        ...,
        description="Amount of processes used for the experiment."
    )
    order_list_id: int = Field(
        ...,
        description="ID of the order list used for the experiment."
    )
    order_list_name: str = Field(
        ...,
        description="Name of the order list."
    )
    order_amount: int = Field(
        ...,
        description="Amount of orders used for the experiment."
    )
    scheduled_cmax: Optional[int] = Field(
        default=None,
        description="Pre-routing scheduled makespan."
    )
    routed_cmax: Optional[int] = Field(
        default=None,
        description="Post-routing final makespan."
    )
    routing_overhead_abs: Optional[int] = Field(
        default=None,
        description="Absolute routing overhead: routed_cmax - scheduled_cmax."
    )
    routing_overhead_pct: Optional[float] = Field(
        default=None,
        description="Percentage routing overhead."
    )
    routing_iterations: Optional[int] = Field(
        default=None,
        description="Routing iterations executed."
    )
    total_time_s: Optional[float] = Field(
        default=None,
        description="Total elapsed solve time in seconds."
    )


class ExperimentPaginatedGetResponseDTO(BaseModel):
    """
    Data Transfer Object representing paginated experiment get response.
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
    experiments: List[ExperimentSummaryResponseDTO] = Field(
        ...,
        description="List of essential information about experiments."
    )


class ExperimentSingleCreateResponseDTO(ExperimentFullResponseDTO):
    """
    Data Transfer Object representing a single experiment create response.
    """
    id: Optional[int] = Field(
        ...,
        description="ID of the experiment."
    )
    name: Optional[str] = Field(
        ...,
        description="Name of the experiment."
    )
    layout_id: Optional[int] = Field(
        ...,
        description="ID of the layout."
    )
    layout: Optional[LayoutBasicDTO] = Field(
        ...,
        description="Layout which should be used for the experiment."
    )
    configuration_id: Optional[int] = Field(
        ...,
        description="ID of the configuration."
    )
    configuration: Optional[ConfigurationDTO] = Field(
        ...,
        description="Configuration which should be used for the experiment."
    )
    ingredient_list_id: Optional[int] = Field(
        ...,
        description="ID of the ingredient list."
    )
    ingredient_list: Optional[IngredientListDTO] = Field(
        ...,
        description="Ingredients that should be used for this layout."
    )
    order_list_id: Optional[int] = Field(
        ...,
        description="ID of the order list."
    )
    order_list: Optional[OrderListDTO] = Field(
        ...,
        description="Orders that should be completed in this experiment."
    )
    batch_id: Optional[int] = Field(
        ...,
        description="ID of the batch to which this experiment belongs."
    )
    batch_name: Optional[str] = Field(
        ...,
        description="Name of the batch to which this experiment belongs."
    )
    status: Optional[ExperimentStatus] = Field(
        ...,
        description="Status of the experiment."
    )
    created_at: Optional[datetime] = Field(
        ...,
        description="Date of the experiment creation."
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment completion."
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment start."
    )
    finished_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment finish."
    )
    is_dry_run: bool = Field(
        default=False,
        description="True if this was only a validation run."
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Validation errors in plain text caused by violation of domain constraints."
    )


class ExperimentSingleGetResponseDTO(ExperimentFullResponseDTO):
    """
    Data Transfer Object representing a single experiment get response.
    """
    pass


class QueueGetResponseDTO(BaseModel):
    """
    Data Transfer Object representing a list with details about experiments in the queue.
    """
    experiments: List[ExperimentSummaryResponseDTO] = Field(
        ...,
        description="Experiments that are in the queue."
    )


class ExperimentBatchCreateResponseDTO(BaseModel):
    """
    Data Transfer Object representing a batch experiment get response.
    """
    id: Optional[int] = Field(
        ...,
        description="ID of the batch to which this experiment belongs."
    )
    name: Optional[str] = Field(
        ...,
        description="New name of the batch."
    )
    created_amount: Optional[int] = Field(
        ...,
        description="Amount of created experiments."
    )
    skipped_amount: Optional[int] = Field(
        ...,
        description="Amount of skipped experiments due to domain constraints."
    )
    experiments: Optional[List[ExperimentSummaryResponseDTO]] = Field(
        ...,
        description="List of essential information about created experiments."
    )
    total_experiment_amount: Optional[int] = Field(
        default=0,
        description="Total amount of experiments.",
    )
    queued_experiment_amount: Optional[int] = Field(
        default=0,
        description="Total amount of experiments.",
    )
    finished_experiment_amount: Optional[int] = Field(
        default=0,
        description="Total amount of experiments.",
    )
    running_experiment_amount: Optional[int] = Field(
        default=0,
        description="Total amount of experiments.",
    )
    failed_experiment_amount: Optional[int] = Field(
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
    estimated_time: Optional[int] = Field(
        default=None,
        description="Estimated time in seconds."
    )
    is_dry_run: Optional[bool] = Field(
        default=False,
        description="True if this was only a validation run."
    )
    errors: Optional[List[str]] = Field(
        default_factory=list,
        description="Validation errors in plain text caused by violation of domain constraints."
    )


class ExperimentBatchGetResponseDTO(BaseModel):
    """
    Data Transfer Object representing a batch experiment get response.
    """
    id: int = Field(
        ...,
        description="ID of the batch to which this experiment belongs."
    )
    name: str = Field(
        ...,
        description="New name of the batch."
    )
    experiments: List[ExperimentSummaryResponseDTO] = Field(
        ...,
        description="List of essential information about created experiments."
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
    created_at: datetime = Field(
        default=None,
        description="Date of the batch creation."
    )
    updated_at: datetime = Field(
        default=None,
        description="Date of the batch update."
    )


class BatchSummaryResponseDTO(BaseModel):
    """
    Data Transfer Object representing batch summary.
    """
    id: int = Field(
        ...,
        description="ID of the batch to which this experiment belongs."
    )
    name: str = Field(
        ...,
        description="New name of the batch."
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
    created_at: datetime = Field(
        default=None,
        description="Date of the batch creation."
    )
    updated_at: datetime = Field(
        default=None,
        description="Date of the batch update."
    )


class ExperimentBatchPaginatedGetResponseDTO(BaseModel):
    """
    Data Transfer Object paginated batch get response.
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
    batches: List[BatchSummaryResponseDTO] = Field(
        ...,
        description="List of essential information about experiments."
    )
