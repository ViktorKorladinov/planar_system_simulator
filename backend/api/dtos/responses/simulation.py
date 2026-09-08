from datetime import datetime
from typing import List, Optional, Dict

from pydantic import BaseModel, Field, field_serializer

from domain.enums import LayoutType, MoverMode


class TopologyInfoDTO(BaseModel):
    """
    Data Transfer Object representing topology information.
    """
    topology: LayoutType = Field(
        ...,
        description="Type of the topology."
    )
    n_tiles: int = Field(
        ...,
        description="Number of tiles in the topology."
    )
    n_interfaces: int = Field(
        ...,
        description="Number of interfaces in the topology."
    )
    n_dispensers: int = Field(
        ...,
        description="Number of dispensers in the topology."
    )

    @field_serializer('topology')
    def serialize_topology(self, topology: LayoutType, _info):
        return topology.value.lower()


class SimulationSummaryDTO(BaseModel):
    """
    Data Transfer Object representing summary about the simulation.
    """
    id: int = Field(
        ...,
        description="ID of the simulation."
    )
    name: str = Field(
        ...,
        description="Name of the simulation."
    )
    dispensing_time: int = Field(
        ...,
        description="Dispensing time of one unit."
    )
    mover_amount: int = Field(
        ...,
        description="Amount of movers."
    )
    order_amount: int = Field(
        ...,
        description="Amount of patients."
    )
    topology_info: TopologyInfoDTO = Field(
        ...,
        description="Information about the topology."
    )
    calculated_at: datetime = Field(
        ...,
        description="The time when the simulation was calculated."
    )


class SimulationBatchGetResponseDTO(BaseModel):
    """
    Data Transfer Object representing page with summary about simulations.
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
    items: List[SimulationSummaryDTO] = Field(
        ...,
        description="Simulations list."
    )


class MoverStepDTO(BaseModel):
    """
    Data Transfer Object representing one mover step in simulation.
    """
    x: int = Field(
        ...,
        description="X coordinate."
    )
    y: int = Field(
        ...,
        description="Y coordinate."
    )
    mode: MoverMode = Field(
        ...,
        description="Mover mode."
    )
    order: str = Field(
        ...,
        description="Patient name."
    )
    rest_offset_x: Optional[int] = Field(
        default=None,
        description="Rest offset x coordinate."
    )
    rest_offset_y: Optional[int] = Field(
        default=None,
        description="Rest offset y coordinate."
    )

    @field_serializer('mode')
    def serialize_topology(self, mode: MoverMode, _info):
        return mode.value.lower()


class MoverPathsDTO(BaseModel):
    """
    Data Transfer Object representing list of lists with paths for movers.
    """
    m: int = Field(
        ...,
        description="Grid dimension m."
    )
    n: int = Field(
        ...,
        description="Grid dimension n."
    )
    filled: bool = Field(
        default=False,
        description="Determines if the grid should be completely filled with tiles."
    )
    paths: List[List[MoverStepDTO]] = Field(
        ...,
        description="List of paths."
    )


class GanttDataDTO(BaseModel):
    """
    Data Transfer Object representing details about location of Gannt charts.
    """
    max_path: int = Field(
        ...,
        description="The length of the longest mover path."
    )
    names: List[str] = Field(
        ...,
        description="Names of the files with Gannt charts."
    )
    api_plot_url: str = Field(
        ...,
        description="The base URL for statis route."
    )


class SimulationGetResponseDTO(BaseModel):
    """
    Data Transfer Object representing detailed description of simulation.
    """
    tile_type_dict: Dict[str, List[List[int]]] = Field(
        ...,
        description="Dictionary with coordinates of dispensers for each medicine."
    )
    dispenser_dict: Dict[str, str] = Field(
        ...,
        description="Dictionary medicine names for dispenser coordinates in format x_y."
    )
    order_color_dict: Dict[str, str] = Field(
        ...,
        description="Dictionary with color for each patient."
    )
    gantts: GanttDataDTO = Field(
        ...,
        description="Data necessary to load Gannt charts."
    )
    mover_paths: MoverPathsDTO = Field(
        ...,
        description="Paths for all movers."
    )
