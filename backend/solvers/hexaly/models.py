from typing import List, Optional

from pydantic import BaseModel, Field

from domain.enums import TileType


class HexalyTask(BaseModel):
    """
    Object representing task used by Hexaly model.
    """
    task_id: int = Field(
        ...,
        gt=-1,
        description="ID of the task."
    )
    tile_type: str = Field(
        ...,
        description="Type of the tile."
    )
    duration: int = Field(
        ...,
        gt=-1,
        description="Duration of the task."
    )


class HexalyOrder(BaseModel):
    """
    Object representing order used by Hexaly model.
    """
    order_id: int = Field(
        ...,
        gt=-1,
        description="ID of the order"
    )
    tasks: List[HexalyTask] = Field(
        ...,
        description="Tasks in the order sorted by ID in ascending order."
    )


class HexalyTile(BaseModel):
    """
    Object representing tile used by Hexaly model.
    """
    id: int = Field(
        ...,
        description="ID of the tile."
    )
    type: TileType = Field(
        ...,
        description="Type of the tile."
    )
    dispensed_types: Optional[List[str]] = Field(
        default=None,
        description="Types dispensed on this tile."
    )
    x: int = Field(
        ...,
        description="X coordinate of the tile."
    )
    y: int = Field(
        ...,
        description="Y coordinate of the tile."
    )


class HexalyExperimentModel(BaseModel):
    """
    Object representing experiment used by Hexaly model.
    """
    orders: List[HexalyOrder] = Field(
        ...,
        description="Orders from the experiment."
    )
    tasks: List[HexalyTask] = Field(
        ...,
        description="Tasks from the experiment sorted by ID in ascending order."
    )
    mover_amount: int = Field(
        ...,
        description="Amount of available movers."
    )
    interface_load_time: int = Field(
        ...,
        description="Time required to load capsules at the interface tile."
    )
    interface_unload_time: int = Field(
        ...,
        description="Time required to unload capsules at the interface tile."
    )
    tiles: List[HexalyTile] = Field(
        ...,
        description="Tiles from the layout."
    )
    setup_times: list[list[int]] = Field(
        ...,
        description="2D matrix of travel times between tiles: setup_times[tile_id_1][tile_id_2]."
    )
    available_tiles: list[list[int]] = Field(
        ...,
        description="2D matrix of compatibility: available_tiles[task_id][tile_id] (0 or 1)."
    )
    time_limit: int = Field(
        ...,
        gt=0,
        description="Time limit for this experiment in seconds."
    )
    nb_threads: int = Field(
        ...,
        description="Number of threads that should be used by solver."
    )
