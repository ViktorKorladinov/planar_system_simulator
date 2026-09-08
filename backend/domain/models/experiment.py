from typing_extensions import Self
from datetime import datetime, timezone
from typing import Optional, List, Dict, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.enums import ExperimentStatus, MoverMode, SolverType, LayoutType, IngredientListType, TileType, \
    OrderListType
from domain.models.batch import BatchDomainModel
from domain.models.configuration import ConfigurationDomainModel
from domain.models.layout import LayoutDomainModel
from domain.models.order_list import OrderListDomainModel

if TYPE_CHECKING:
    from domain.models.batch import BatchDomainModel


class MoverStep(BaseModel):
    """
    Immutable value object representing a single step of one mover.
    """
    model_config = ConfigDict(frozen=True)

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
        description="Order name in format order_<order_id>."
    )
    rest_offset_x: Optional[int] = Field(
        default=None,
        description="Rest offset x coordinate."
    )
    rest_offset_y: Optional[int] = Field(
        default=None,
        description="Rest offset y coordinate."
    )


class Result(BaseModel):
    """
    Immutable value object representing result of the experiment.
    """
    mover_paths: Optional[List[List[MoverStep]]] = Field(
        default=None,
        description="List of paths for each mover."
    )
    max_path: Optional[int] = Field(
        default=None,
        description="The length of the longest mover path."
    )
    color_dict: Optional[Dict[str, str]] = Field(
        default=None,
        description="Dictionary with colors for orders and tiles."
    )


class ExperimentDomainModel(BaseModel):
    """
    Domain Entity for an experiment.
    Handles its own state changes and validates its own data.
    """
    model_config = ConfigDict(validate_assignment=True)

    id: Optional[int] = None
    name: Optional[str] = Field(
        default=None,
        description="The name of the experiment.",
    )
    status: ExperimentStatus = Field(
        ...,
        description="The status of the experiment."
    )
    layout: LayoutDomainModel = Field(
        ...,
        description="The layout which should be used for the experiment."
    )
    configuration: ConfigurationDomainModel = Field(
        ...,
        description="The configuration which should be used for the experiment."
    )
    order_list: OrderListDomainModel = Field(
        ...,
        description="Orders that should be completed in this experiment."
    )
    result: Optional[Result] = Field(
        default=None,
        description="Result of the experiment."
    )
    batch_id: Optional[int] = Field(
        default=None,
        description="ID of the batch to which experiment belongs."
    )
    batch_name: Optional[str] = Field(
        default=None,
        description="Name of the batch to which experiment belongs."
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment creation."
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment update."
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment start."
    )
    finished_at: Optional[datetime] = Field(
        default=None,
        description="Date of the experiment finish."
    )
    task_id: Optional[str] = Field(
        default=None,
        description="ID of the task which is processing the experiment."
    )

    def mark_as_running(self) -> None:
        """Marks this experiment as running."""
        self.status = ExperimentStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def mark_as_finished(self) -> None:
        """Marks this experiment as finished."""
        self.status = ExperimentStatus.FINISHED
        self.finished_at = datetime.now(timezone.utc)

    def mark_as_failed(self) -> None:
        """Marks this experiment as failed."""
        self.status = ExperimentStatus.FAILED
        self.finished_at = datetime.now(timezone.utc)

    def save_extended_result(self, result: Result) -> None:
        """Saves result and changes state.

        Args:
            result: Result of the experiment.
        """
        if result is not None:
            self.result = result

    # Ensure that layout is compatible with chosen solver
    @model_validator(mode='after')
    def validate_layout_and_solver_compatibility(self) -> Self:
        solver_type = self.configuration.solver_type
        layout_type = self.layout.type
        perfume_solvers = [SolverType.CPLEX_PERFUMES]
        ingredient_list_type = self.layout.ingredient_list.type

        if solver_type == SolverType.HEXALY and layout_type == LayoutType.RING:
            raise ValueError(f"Hexaly solver doesn't support layout of type Ring.")
        if solver_type == SolverType.HEXALY and layout_type == LayoutType.CUSTOM:
            raise ValueError(f"Hexaly solver doesn't support layout of type Custom.")
        if solver_type in perfume_solvers and ingredient_list_type != IngredientListType.PERFUME:
            raise ValueError(f"Perfume solvers require layout with ingredient list of type Perfume.")

        return self

    # Ensure that layout contains dispensers with ingredients for all orders.
    @model_validator(mode='after')
    def validate_layout_and_orders_compatibility(self) -> Self:
        reachable_tiles = self.layout.get_reachable_tiles()
        dispensed_ingredients = set()
        for tile in reachable_tiles:
            if tile.type == TileType.DISPENSER:
                for ingredient in tile.dispensed_types:
                    dispensed_ingredients.add(ingredient)
        for order in self.order_list.orders:
            for item in order.items:
                if item.name != TileType.MIXER.value and item.name != TileType.CAPPER.value and item.name not in dispensed_ingredients:
                    raise ValueError(f"Item {item.name} isn't dispensed by any dispenser reachable from interface.")
        return self

    # Ensure that mixer and capper tiles are used only when Cplex perfume solver is selected.
    @model_validator(mode='after')
    def validate_mixer_and_capper_tiles_and_solver_compatibility(self) -> Self:
        if self.configuration.solver_type != SolverType.CPLEX_PERFUMES:
            for tile in self.layout.tiles:
                if tile.type == TileType.CAPPER:
                    raise ValueError(f"Capper tiles aren't supported by selected solver.")
                if tile.type == TileType.MIXER:
                    raise ValueError(f"Mixer tiles aren't supported by selected solver.")
        return self

    # Ensure that order list is compatible with chosen layout.
    @model_validator(mode='after')
    def validate_layout_and_order_list_compatibility(self) -> Self:
        if self.layout.ingredient_list.type == IngredientListType.PERFUME and self.order_list.type != IngredientListType.PERFUME:
            raise ValueError(f"Ingredient list of type perfume requires order list of type Perfume.")
        return self

    # Ensure that ingredient list has correct type based on chosen solver.
    @model_validator(mode='after')
    def validate_solver_and_ingredient_list_compatibility(self) -> Self:
        if self.configuration.solver_type == SolverType.CPLEX_PERFUMES:
            if self.layout.ingredient_list.type != IngredientListType.PERFUME:
                raise ValueError(f"Cplex Perfume solver requires ingredient list of type Perfume.")
        elif self.configuration.solver_type == SolverType.CPLEX_MEDICINE:
            if self.layout.ingredient_list.type != IngredientListType.MEDICINE:
                raise ValueError(f"Cplex Medicine solver requires ingredient list of type Medicine.")
        elif self.configuration.solver_type == SolverType.HEXALY:
            if self.layout.ingredient_list.type != IngredientListType.MEDICINE:
                raise ValueError(f"Hexaly solver requires ingredient list of type Medicine.")
        return self

    # Ensure that order list has correct type based on chosen solver.
    @model_validator(mode='after')
    def validate_solver_and_order_list_compatibility(self) -> Self:
        if self.configuration.solver_type == SolverType.CPLEX_PERFUMES:
            if self.order_list.type != OrderListType.PERFUME:
                raise ValueError(f"Cplex Perfume solver requires order list of type Perfume.")
        elif self.configuration.solver_type == SolverType.CPLEX_MEDICINE:
            if self.order_list.type != OrderListType.MEDICINE:
                raise ValueError(f"Cplex Medicine solver requires order list of type Medicine.")
        elif self.configuration.solver_type == SolverType.HEXALY:
            if self.order_list.type != OrderListType.MEDICINE:
                raise ValueError(f"Hexaly solver requires order list of type Medicine.")
        return self


ExperimentDomainModel.model_rebuild()
BatchDomainModel.model_rebuild()
