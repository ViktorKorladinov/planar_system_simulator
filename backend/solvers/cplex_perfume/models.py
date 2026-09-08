from typing import List, Dict

from pydantic import BaseModel, Field

from domain.models.ingredient_list import Ingredient


class Tile(BaseModel):
    """
    Object representing tile on the layout.
    """
    idx: int = Field(
        ...,
        description="Index of the tile."
    )
    row: int = Field(
        ...,
        description="Row of the tile."
    )
    col: int = Field(
        ...,
        description="Column of the tile."
    )
    label: str = Field(
        ...,
        description="Label of the tile."
    )


class Operation(BaseModel):
    """
    Object representing operation for Cplex medicine solver.
    """
    step: int = Field(
        ...,
        description="Step of the operation."
    )
    phase: int = Field(
        ...,
        description="Phase of the operation."
    )
    label: str = Field(
        ...,
        description="Label of the operation (ingredient name, MIXER, CAPPER, or INTERFACE)."
    )
    volume_ml: float = Field(
        ...,
        description="Volume of the liquid."
    )
    candidates: list[Tile] = Field(
        ...,
        description="Tiles that can perform this operation."
    )


class CplexPerfumeData(BaseModel):
    """
    Object representing data required by the Cplex perfume solver.
    """
    ingredients: Dict[str, Ingredient] = Field(
        ...,
        description="Dictionary of dictionaries with details about ingredients."
    )
    tiles_flat: List[Tile] = Field(
        ...,
        description="List of tiles from the layout."
    )
    machines: Dict[str, List[Tile]] = Field(
        ...,
        description="Dictionary with labels as keys and lists of tiles as values."
    )
    recipes_raw: List[List[Operation]] = Field(
        ...,
        description="List of lists of operations required to complete all recipes."
    )
    tmax_values: List[int] = Field(
        ...,
        description="List of T max values for each recipe."
    )
    time_limit: int = Field(
        ...,
        description="Time limit for computation in seconds."
    )
    process_amount: int = Field(
        ...,
        description="Amount of processes that can be used by Cplex solver."
    )
    dispense_rate: float = Field(
        ...,
        description="Dispense rate (s / ml)."
    )
    viscosity_exponent: float = Field(
        ...,
        description="Viscosity scaling exponent."
    )
    mover_speed: float = Field(
        ...,
        description="Mover speed (s per tile)."
    )
    mixer_primary_t: int = Field(
        ...,
        description="Mixer primary agitation time in seconds (before solvents)."
    )
    mixer_final_t: int = Field(
        ...,
        description="Mixer final agitation time in seconds (after solvents)."
    )
    capper_t: int = Field(
        ...,
        description="Capper agitation time in seconds."
    )
    interface_t: int = Field(
        ...,
        description="Interface entry/exit time in seconds."
    )
    mover_amount: int = Field(
        ...,
        description="Amount of available movers."
    )
