from typing import List, Dict, NamedTuple, Optional

import pandas as pd
from pydantic import BaseModel, Field, ConfigDict

from domain.enums import LayoutType, GraphType
from domain.models.experiment import MoverStep


class CplexOrder(BaseModel):
    """
    Object representing order used by Cplex solver.
    """
    order_id: int = Field(
        ...,
        gt=-1,
        description="ID of the order"
    )
    drug_names: List[str] = Field(
        ...,
        description="List with all drug names included in the order."
    )
    dosages: List[int] = Field(
        ...,
        description="List with dosages for each drug included in the order."
    )


class CplexLayout(BaseModel):
    type: LayoutType = Field(
        ...,
        description="Type of the layout."
    )
    row_amount: int = Field(
        ...,
        description="Amount of rows in layout."
    )
    column_amount: int = Field(
        ...,
        description="Amount of columns in layout."
    )
    placement: List[List[str]] = Field(
        ...,
        description="Placement of tiles included in the layout."
    )
    tile_amount: int = Field(
        ...,
        description="Amount of tiles included in the layout (without interfaces)."
    )
    interface_amount: int = Field(
        ...,
        description="Amount of interfaces included in the layout."
    )
    packer_result: Dict[str, List[str]] = Field(
        ...,
        description="Placement in different format required by solver."
    )


class CplexExperimentModel(BaseModel):
    """
    Object representing experiment model used by Cplex solver.
    """
    orders: List[CplexOrder] = Field(
        ...,
        description="List of orders used by Cplex solver."
    )
    mover_amount: int = Field(
        ...,
        description="Amount of movers."
    )
    time_limit: int = Field(
        ...,
        description="Time limit in seconds."
    )
    dispensing_time: int = Field(
        ...,
        description="Dispensing time in seconds."
    )
    batch_size: int = Field(
        ...,
        description="Size of the batch."
    )
    process_amount: int = Field(
        ...,
        description="Amount of processes that can be used by Cplex solver."
    )
    warmup: bool = Field(
        ...,
        description="True if warmup should be used for experiment."
    )
    interface_time: int = Field(
        ...,
        description="Time required by operations at the interface in seconds."
    )
    layout: CplexLayout = Field(
        ...,
        description="Layout for the experiment."
    )


class BasicGapStats(BaseModel):
    """
    Object representing gap stats for created schedule.
    """
    total_gaps: int = Field(
        ...,
        description="Total number of gaps."
    )
    total_gap_duration: int = Field(
        ...,
        description="Total duration of gaps."
    )
    average_gap: float = Field(
        ...,
        description="Average gap."
    )
    min_gap: int = Field(
        ...,
        description="Minimum gap."
    )
    max_gap: int = Field(
        ...,
        description="Maximum gap."
    )


class MoverGapStats(BasicGapStats):
    """
    Object representing mover gap stats for created schedule.
    """
    id: str = Field(
        ...,
        description="ID of the mover."
    )


class OverallGapStats(BasicGapStats):
    """
    Object representing overall gap stats for created schedule.
    """
    number_of_movers: int = Field(
        ...,
        description="Number of movers."
    )


class GapStats(BaseModel):
    """
    Object representing complete gap stats for created schedule.
    """
    movers: List[MoverGapStats] = Field(
        ...,
        description="List of gap stats for movers."
    )
    overall: OverallGapStats = Field(
        ...,
        description="Overall gap stats."
    )


class CplexResult(BaseModel):
    """
    Object representing experiment result obtained from Cplex solver.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    initial_schedule: pd.DataFrame = Field(
        ...,
        description="Initial schedule."
    )
    finished_schedule: pd.DataFrame = Field(
        ...,
        description="Finished schedule."
    )
    warmup_cmax_per_batch: List[Optional[float]] = Field(
        ...,
        description="Warmup cmax per batch."
    )
    pre_routing_cmax: int = Field(
        ...,
        description="Pre-routing cmax."
    )
    post_routing_cmax: int = Field(
        ...,
        description="Post-routing cmax."
    )
    routing_time: float = Field(
        ...,
        description="Routing time."
    )
    merging_time: float = Field(
        ...,
        description="Merging time."
    )
    gap_stats: Optional[GapStats] = Field(
        ...,
        description="Gap stats."
    )
    mover_paths: List[List[MoverStep]] = Field(
        ...,
        description="List of paths for each mover."
    )
    max_path: int = Field(
        ...,
        description="The length of the longest mover path."
    )
    color_dict: Dict[str, str] = Field(
        ...,
        description="Dictionary with colors for orders and tiles."
    )
    gantt_files: dict[GraphType, str] = Field(
        ...,
        description="Dictionary with gantt file name and its content."
    )


class BatchResult(NamedTuple):
    tasks: pd.DataFrame
    wrappers: pd.DataFrame
    metadata: dict
    warmup_cmax: Optional[float]
    metrics: Optional[dict] = None
