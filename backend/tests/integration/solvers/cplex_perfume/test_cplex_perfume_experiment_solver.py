import pytest

from domain.enums import (
    ExperimentStatus, LayoutType, TileType, SolverType,
    OrderListType, IngredientListType, NoteType
)
from domain.models.common.tile import Tile
from domain.models.configuration import ConfigurationDomainModel
from domain.models.experiment import ExperimentDomainModel
from domain.models.ingredient_list import Ingredient, IngredientListDomainModel
from domain.models.layout import LayoutDomainModel
from domain.models.order_list import Order, OrderItem, OrderListDomainModel
from solvers.cplex_perfume.experiment_solver import CplexPerfumeExperimentSolver
from tests.integration.solvers.utilities import verify_obtained_schedule


@pytest.fixture
def cplex_perfume_solver() -> CplexPerfumeExperimentSolver:
    return CplexPerfumeExperimentSolver()


@pytest.fixture
def base_configuration() -> ConfigurationDomainModel:
    return ConfigurationDomainModel(
        id=1,
        name="Standard Perfume Config",
        solver_type=SolverType.CPLEX_PERFUMES,
        interface_time=3,
        dispensing_time=1,
        mover_amount=3,
        time_limit=10,
        process_amount=4,
        dispense_rate=0.1,
        viscosity_exponent=0.55,
        mover_speed=1.0,
        mixer_primary_time=5,
        mixer_final_time=10,
        capper_time=4
    )


def test_solve_complex_perfume_experiment_multiple_dispensers(
        cplex_perfume_solver: CplexPerfumeExperimentSolver,
        base_configuration: ConfigurationDomainModel
) -> None:
    # Arrange:
    ingredients = [
        Ingredient(name="Rose", note_type=NoteType.HEART_NOTE, viscosity=1.2, volatility_rank=2),
        Ingredient(name="Jasmine", note_type=NoteType.HEART_NOTE, viscosity=1.1, volatility_rank=2),
        Ingredient(name="Musk", note_type=NoteType.BASE_NOTE, viscosity=2.5, volatility_rank=1),
        Ingredient(name="Vanilla", note_type=NoteType.BASE_NOTE, viscosity=2.0, volatility_rank=1)
    ]
    ing_list = IngredientListDomainModel(
        id=1, name="Complex Perfume Ingredients", type=IngredientListType.PERFUME,
        ingredients=ingredients, ingredient_amount=len(ingredients)
    )
    tiles = [
        Tile(type=TileType.INTERFACE, x=0, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["Rose", "Jasmine"], x=0, y=1),
        Tile(type=TileType.DISPENSER, dispensed_types=["Musk", "Vanilla"], x=1, y=0),
        Tile(type=TileType.MIXER, x=1, y=1),
        Tile(type=TileType.EMPTY, x=2, y=0),
        Tile(type=TileType.CAPPER, x=2, y=1)
    ]
    layout = LayoutDomainModel(
        id=1, name="Multi-Dispenser Layout", type=LayoutType.DOUBLE_LINE,
        tiles=tiles, tile_amount=len(tiles), interface_amount=1,
        dispenser_amount=2, filled=False, ingredient_list=ing_list
    )
    orders = [
        Order(items=[
            OrderItem(name="Rose", quantity=2.0),
            OrderItem(name="mixer", quantity=0),
            OrderItem(name="Musk", quantity=1.0),
            OrderItem(name="mixer", quantity=0),
            OrderItem(name="capper", quantity=0)],
            t_max=400
        ),
        Order(items=[
            OrderItem(name="Jasmine", quantity=3.0),
            OrderItem(name="mixer", quantity=0),
            OrderItem(name="Vanilla", quantity=2.0),
            OrderItem(name="mixer", quantity=0),
            OrderItem(name="capper", quantity=0)],
            t_max=400
        )
    ]
    order_list = OrderListDomainModel(
        id=1, name="Multi-Ingredient Orders", orders=orders,
        order_amount=len(orders), type=OrderListType.PERFUME
    )

    experiment = ExperimentDomainModel(
        id=100, name="Complex Dispenser Test", status=ExperimentStatus.RUNNING,
        layout=layout, configuration=base_configuration, order_list=order_list, task_id="test-complex"
    )

    # Act
    result = cplex_perfume_solver.solve(experiment)

    # Assert
    assert result.status == ExperimentStatus.FINISHED
    assert result.result is not None
    assert verify_obtained_schedule(data=experiment, schedule=result.schedule)


@pytest.mark.parametrize("mover_count", [1, 3])
def test_perfume_solver_robustness(
        cplex_perfume_solver: CplexPerfumeExperimentSolver,
        base_configuration: ConfigurationDomainModel,
        mover_count: int
) -> None:
    base_configuration.mover_amount = mover_count

    ing_list = IngredientListDomainModel(
        id=2, name="Min List", type=IngredientListType.PERFUME,
        ingredients=[
            Ingredient(name="Rose", note_type=NoteType.HEART_NOTE, viscosity=1.2, volatility_rank=2),
            Ingredient(name="Jasmine", note_type=NoteType.HEART_NOTE, viscosity=1.1, volatility_rank=2),
            Ingredient(name="Musk", note_type=NoteType.BASE_NOTE, viscosity=2.5, volatility_rank=1),
            Ingredient(name="Vanilla", note_type=NoteType.BASE_NOTE, viscosity=2.0, volatility_rank=1)
        ],
        ingredient_amount=1
    )

    tiles = [
        Tile(type=TileType.INTERFACE, x=0, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["Rose", "Jasmine"], x=0, y=1),
        Tile(type=TileType.DISPENSER, dispensed_types=["Musk", "Vanilla"], x=1, y=0),
        Tile(type=TileType.MIXER, x=1, y=1),
        Tile(type=TileType.EMPTY, x=2, y=0),
        Tile(type=TileType.CAPPER, x=2, y=1)
    ]
    layout = LayoutDomainModel(
        id=2, name="Min Perfume Layout", type=LayoutType.DOUBLE_LINE, tiles=tiles,
        tile_amount=len(tiles), interface_amount=1, dispenser_amount=1, filled=False,
        ingredient_list=ing_list
    )
    orders = [
        Order(items=[
            OrderItem(name="Rose", quantity=2.0),
            OrderItem(name="mixer", quantity=0),
            OrderItem(name="Musk", quantity=1.0),
            OrderItem(name="mixer", quantity=0),
            OrderItem(name="capper", quantity=0)],
            t_max=400
        ),
        Order(items=[
            OrderItem(name="Jasmine", quantity=3.0),
            OrderItem(name="mixer", quantity=0),
            OrderItem(name="Vanilla", quantity=2.0),
            OrderItem(name="mixer", quantity=0),
            OrderItem(name="capper", quantity=0)],
            t_max=400
        )
    ]

    order_list = OrderListDomainModel(
        id=2, name="Min Perfume Orders",
        orders=orders,
        order_amount=1, type=OrderListType.PERFUME
    )

    experiment = ExperimentDomainModel(
        id=101, name="Robustness Test", status=ExperimentStatus.RUNNING,
        layout=layout, configuration=base_configuration, order_list=order_list, task_id="rob-id"
    )

    result = cplex_perfume_solver.solve(experiment)
    assert result.status == ExperimentStatus.FINISHED
    assert verify_obtained_schedule(data=experiment, schedule=result.schedule)


def test_perfume_solver_handles_impossible_time_limit(
        cplex_perfume_solver: CplexPerfumeExperimentSolver,
        base_configuration: ConfigurationDomainModel
) -> None:
    base_configuration.time_limit = 1
    base_configuration.mover_amount = 5

    ingredients = [
        Ingredient(name="Rose", note_type=NoteType.HEART_NOTE, viscosity=1.2, volatility_rank=2),
        Ingredient(name="Jasmine", note_type=NoteType.HEART_NOTE, viscosity=1.1, volatility_rank=2),
        Ingredient(name="Musk", note_type=NoteType.BASE_NOTE, viscosity=2.5, volatility_rank=1),
        Ingredient(name="Vanilla", note_type=NoteType.BASE_NOTE, viscosity=2.0, volatility_rank=1)
    ]
    ing_list = IngredientListDomainModel(
        id=3, name="Impossible Limit List", type=IngredientListType.PERFUME,
        ingredients=ingredients, ingredient_amount=len(ingredients)
    )

    tiles = [
        Tile(type=TileType.INTERFACE, x=0, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["Rose", "Musk"], x=0, y=1),
        Tile(type=TileType.MIXER, x=1, y=0),
        Tile(type=TileType.CAPPER, x=1, y=1)
    ]
    layout = LayoutDomainModel(
        id=3, name="Timeout Layout", type=LayoutType.DOUBLE_LINE, tiles=tiles,
        tile_amount=len(tiles), interface_amount=1, dispenser_amount=1, filled=False,
        ingredient_list=ing_list
    )

    orders = []
    for i in range(300):
        orders.append(
            Order(items=[
                OrderItem(name="Rose", quantity=2.0),
                OrderItem(name="mixer", quantity=0),
                OrderItem(name="Musk", quantity=1.0),
                OrderItem(name="mixer", quantity=0),
                OrderItem(name="capper", quantity=0)],
                t_max=400
            )
        )

    order_list = OrderListDomainModel(
        id=3, name="Massive Orders", orders=orders,
        order_amount=len(orders), type=OrderListType.PERFUME
    )

    experiment = ExperimentDomainModel(
        id=102, name="Timeout Test", status=ExperimentStatus.RUNNING,
        layout=layout, configuration=base_configuration, order_list=order_list, task_id="timeout-id"
    )

    # Act
    result = cplex_perfume_solver.solve(experiment)

    # Assert
    assert result.status == ExperimentStatus.FAILED
