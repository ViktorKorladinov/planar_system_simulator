import pytest

from domain.enums import ExperimentStatus, LayoutType, TileType, SolverType, OrderListType, IngredientListType
from domain.models.common.tile import Tile
from domain.models.configuration import ConfigurationDomainModel
from domain.models.experiment import ExperimentDomainModel
from domain.models.ingredient_list import Ingredient, IngredientListDomainModel
from domain.models.layout import LayoutDomainModel
from domain.models.order_list import Order, OrderItem, OrderListDomainModel
from solvers.cplex_medicine.experiment_solver import CplexMedicineExperimentSolver
from tests.integration.solvers.utilities import verify_obtained_schedule


@pytest.fixture
def cplex_medicine_solver() -> CplexMedicineExperimentSolver:
    return CplexMedicineExperimentSolver()


@pytest.fixture
def base_configuration() -> ConfigurationDomainModel:
    return ConfigurationDomainModel(
        id=1,
        name="Standard Integration Config",
        solver_type=SolverType.CPLEX_MEDICINE,
        interface_time=3,
        dispensing_time=1,
        mover_amount=3,
        time_limit=10,
        process_amount=4,
        batch_size=100,
        warmup=True
    )


def test_solve_small_medicine_experiment_with_cplex_medicine_solver(cplex_medicine_solver: CplexMedicineExperimentSolver,
                                         base_configuration: ConfigurationDomainModel) -> None:
    # Arrange
    ingredient_names = ["AMLODIPINE", "SIMVASTATIN", "PARALEN"]
    ingredients = [Ingredient(name=name) for name in ingredient_names]
    ing_list = IngredientListDomainModel(
        id=1,
        name="Medicine Ingredients",
        type=IngredientListType.MEDICINE,
        ingredients=ingredients,
        ingredient_amount=len(ingredients)
    )
    tiles = [
        Tile(type=TileType.INTERFACE, x=0, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["AMLODIPINE"], x=1, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["SIMVASTATIN"], x=2, y=0),
        Tile(type=TileType.EMPTY, x=0, y=1),
        Tile(type=TileType.DISPENSER, dispensed_types=["PARALEN"], x=1, y=1),
    ]
    layout = LayoutDomainModel(
        id=1, name="Integration Layout", type=LayoutType.DOUBLE_LINE,
        tiles=tiles, tile_amount=len(tiles), interface_amount=1,
        dispenser_amount=3, filled=False, ingredient_list=ing_list
    )
    orders = [
        Order(items=[OrderItem(name="AMLODIPINE", quantity=2.0), OrderItem(name="SIMVASTATIN", quantity=5.0)]),
        Order(items=[OrderItem(name="PARALEN", quantity=10.0)])
    ]
    order_list = OrderListDomainModel(
        id=1, name="Test Orders", orders=orders,
        order_amount=len(orders), type=OrderListType.MEDICINE
    )
    experiment = ExperimentDomainModel(
        id=100, name="Small Test", status=ExperimentStatus.RUNNING,
        layout=layout, configuration=base_configuration, order_list=order_list, task_id="test-id"
    )

    # Act
    result = cplex_medicine_solver.solve(experiment)

    # Assert
    assert result.status == ExperimentStatus.FINISHED
    assert result.result is not None
    assert verify_obtained_schedule(data=experiment, schedule=result.schedule)


@pytest.mark.parametrize("mover_count", [1, 3])
def test_solver_robustness_with_varying_movers_with_cplex_medicine_solver(cplex_medicine_solver: CplexMedicineExperimentSolver,
                                               base_configuration: ConfigurationDomainModel,
                                               mover_count: int) -> None:
    base_configuration.mover_amount = mover_count

    ing_list = IngredientListDomainModel(
        id=2, name="Simple List", type=IngredientListType.MEDICINE,
        ingredients=[Ingredient(name="A")], ingredient_amount=1
    )

    tiles = [Tile(type=TileType.INTERFACE, x=0, y=0),
             Tile(type=TileType.DISPENSER, dispensed_types=["A"], x=1, y=0)]
    layout = LayoutDomainModel(
        id=2, name="Min Layout", type=LayoutType.LINE, tiles=tiles,
        tile_amount=2, interface_amount=1, dispenser_amount=1, filled=False,
        ingredient_list=ing_list
    )

    orders = [Order(items=[OrderItem(name="A", quantity=1.0)])]
    order_list = OrderListDomainModel(
        id=2, name="Min Orders", orders=orders,
        order_amount=1, type=OrderListType.MEDICINE
    )

    experiment = ExperimentDomainModel(
        id=101, name="Robustness Test", status=ExperimentStatus.RUNNING,
        layout=layout, configuration=base_configuration, order_list=order_list, task_id="rob-id"
    )

    result = cplex_medicine_solver.solve(experiment)
    assert result.status == ExperimentStatus.FINISHED
    assert verify_obtained_schedule(data=experiment, schedule=result.schedule)


def test_solver_handles_impossible_time_limit_with_cplex_medicine_solver(cplex_medicine_solver: CplexMedicineExperimentSolver,
                                              base_configuration: ConfigurationDomainModel) -> None:
    base_configuration.time_limit = 1
    base_configuration.mover_amount = 20
    base_configuration.warmup = False
    ing_list = IngredientListDomainModel(
        id=2, name="Simple List", type=IngredientListType.MEDICINE,
        ingredients=[Ingredient(name="A"), Ingredient(name="B"), Ingredient(name="C")], ingredient_amount=1
    )

    tiles = [Tile(type=TileType.INTERFACE, x=0, y=0),
             Tile(type=TileType.EMPTY, x=0, y=1),
             Tile(type=TileType.EMPTY, x=1, y=0),
             Tile(type=TileType.EMPTY, x=1, y=1),
             Tile(type=TileType.EMPTY, x=2, y=0),
             Tile(type=TileType.EMPTY, x=2, y=1),
             Tile(type=TileType.DISPENSER, dispensed_types=["A", "B", "C"], x=3, y=0),
             Tile(type=TileType.EMPTY, x=3, y=1)]
    layout = LayoutDomainModel(
        id=2, name="Min Layout", type=LayoutType.LINE, tiles=tiles,
        tile_amount=2, interface_amount=1, dispenser_amount=1, filled=False,
        ingredient_list=ing_list
    )
    orders = []
    for i in range(300):
        orders.append(Order(items=[OrderItem(name="A", quantity=8.0),
                           OrderItem(name="B", quantity=5.0),
                           OrderItem(name="C", quantity=9.0)]))
    order_list = OrderListDomainModel(
        id=2, name="Min Orders", orders=orders,
        order_amount=1, type=OrderListType.MEDICINE
    )

    experiment = ExperimentDomainModel(
        id=101, name="Robustness Test", status=ExperimentStatus.RUNNING,
        layout=layout, configuration=base_configuration, order_list=order_list, task_id="rob-id"
    )

    result = cplex_medicine_solver.solve(experiment)
    assert result.status == ExperimentStatus.FAILED
