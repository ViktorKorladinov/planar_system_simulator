from datetime import datetime

import pandas as pd

from domain.enums import TileType, SolverType, LayoutType, ExperimentStatus, IngredientListType, OrderListType
from domain.models.common.tile import Tile
from domain.models.experiment import ExperimentDomainModel, MoverStep
from domain.models.ingredient_list import IngredientListDomainModel
from domain.models.layout import LayoutDomainModel
from domain.models.order_list import Order, OrderItem, OrderListDomainModel
from solvers.cplex_medicine.mapper import (
    map_placement_to_packer_result,
    map_order_domain_to_cplex,
    map_orders_domain_to_cplex,
    map_tiles_to_placement,
    map_layout_domain_to_cplex,
    map_experiment_to_cplex_experiment,
    map_schedule_row_to_task,
    map_cplex_tile_to_domain,
    map_finished_schedule_to_schedule,
    map_cplex_result_to_result
)
from solvers.cplex_medicine.models import CplexResult
from tests.factories.configuration_factory import get_configuration_domain_model
from tests.factories.ingredient_list_factory import get_ingredient_domain_model


def test_map_placement_to_packer_result() -> None:
    # Arrange
    placement = [['interface', 'AMLODIPINE,SIMVASTATIN', 'SIMVASTATIN', 'LISINOPRIL'],
                 ['empty', 'PARALEN', 'blocked', 'empty']]
    # Act
    result = map_placement_to_packer_result(placement)

    # Assert
    assert result == {
        "0": ['AMLODIPINE', 'SIMVASTATIN'],
        "1": ['SIMVASTATIN'],
        "2": ['LISINOPRIL'],
        "3": ['PARALEN']
    }


def test_map_placement_to_packer_result_empty() -> None:
    # Arrange
    placement = [['interface', 'empty', 'blocked'],
                 ['empty', 'blocked', 'interface']]
    # Act
    result = map_placement_to_packer_result(placement)

    # Assert
    assert result == {}


def test_map_order_domain_to_cplex() -> None:
    # Arrange
    order = Order(items=[
        OrderItem(name="AMLODIPINE", quantity=4),
        OrderItem(name="SIMVASTATIN", quantity=12),
        OrderItem(name="LISINOPRIL", quantity=6)])
    order_id = 3

    # Act
    result = map_order_domain_to_cplex(domain_model=order, order_id=order_id)

    # Assert
    assert result.model_dump(mode='json') == {
        "order_id": order_id,
        "drug_names": ["AMLODIPINE", "SIMVASTATIN", "LISINOPRIL"],
        "dosages": [4, 12, 6]
    }


def test_map_orders_domain_to_cplex() -> None:
    # Arrange
    orders = [
        Order(items=[
            OrderItem(name="AMLODIPINE", quantity=4),
            OrderItem(name="SIMVASTATIN", quantity=12),
            OrderItem(name="LISINOPRIL", quantity=6)]),
        Order(items=[
            OrderItem(name="LISINOPRIL", quantity=12),
            OrderItem(name="SIMVASTATIN", quantity=13)]),
        Order(items=[
            OrderItem(name="AMLODIPINE", quantity=4),
            OrderItem(name="LISINOPRIL", quantity=11),
            OrderItem(name="SIMVASTATIN", quantity=11)]),
        Order(items=[
            OrderItem(name="SIMVASTATIN", quantity=14),
            OrderItem(name="LISINOPRIL", quantity=2)])]

    # Act
    result = map_orders_domain_to_cplex(domain_models=orders)

    # Assert
    for i in range(len(orders)):
        assert result[i].model_dump(mode='json') == {
            "order_id": i,
            "drug_names": [orders[i].items[x].name for x in range(len(orders[i].items))],
            "dosages": [orders[i].items[x].quantity for x in range(len(orders[i].items))],
        }


def test_map_tiles_to_placement() -> None:
    # Arrange
    tiles = [
        Tile(type=TileType.INTERFACE, x=0, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["AMLODIPINE", "SIMVASTATIN"], x=1, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["SIMVASTATIN"], x=2, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["LISINOPRIL"], x=3, y=0),
        Tile(type=TileType.EMPTY, x=0, y=1),
        Tile(type=TileType.DISPENSER, dispensed_types=["PARALEN"], x=1, y=1),
        Tile(type=TileType.BLOCKED, x=2, y=1),
        Tile(type=TileType.EMPTY, x=3, y=1)]

    # Act
    result = map_tiles_to_placement(tiles=tiles)

    # Assert
    assert result == [['interface', 'AMLODIPINE,SIMVASTATIN', 'SIMVASTATIN', 'LISINOPRIL'],
                      ['empty', 'PARALEN', 'blocked', 'empty']]


def test_map_layout_domain_to_cplex() -> None:
    # Arrange
    ingredients = [
        get_ingredient_domain_model(),
        get_ingredient_domain_model(name="Aspirin", note_type=None, viscosity=None,
                                    volatility_rank=None),
        get_ingredient_domain_model(name="Lisinopril", note_type=None, viscosity=None,
                                    volatility_rank=None)
    ]
    ingredient_list = IngredientListDomainModel(
        id=1,
        name="Ingredient List",
        type=IngredientListType.MEDICINE,
        ingredients=ingredients,
        ingredient_amount=len(ingredients)
    )
    tiles = [
        Tile(type=TileType.INTERFACE, x=0, y=0),
        Tile(type=TileType.BLOCKED, x=0, y=1),
        Tile(type=TileType.EMPTY, x=1, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["Aspirin"], x=1, y=1),
        Tile(type=TileType.EMPTY, x=2, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["Aspirin", "Lisinopril"], x=2, y=1)]
    layout = LayoutDomainModel(
        id=1,
        name="layout",
        type=LayoutType.CUSTOM,
        tiles=tiles,
        tile_amount=len(tiles),
        interface_amount=sum(1 for tile in tiles if tile.type == TileType.INTERFACE),
        dispenser_amount=sum(1 for tile in tiles if tile.type == TileType.DISPENSER),
        filled=True,
        ingredient_list=ingredient_list,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # Act
    result = map_layout_domain_to_cplex(domain_model=layout)

    # Assert
    assert result.model_dump(mode='json') == {
        "type": layout.type,
        "row_amount": max(tile.y for tile in layout.tiles) + 1,
        "column_amount": max(tile.x for tile in layout.tiles) + 1,
        "placement": [['interface', 'empty', 'empty'], ['blocked', 'Aspirin', 'Aspirin,Lisinopril']],
        "tile_amount": layout.dispenser_amount,
        "interface_amount": layout.interface_amount,
        "packer_result": {
            "0": ['Aspirin'],
            "1": ['Aspirin', 'Lisinopril']
        }
    }


def test_map_experiment_to_cplex_experiment() -> None:
    # Arrange
    configuration = get_configuration_domain_model(
        solver_type=SolverType.CPLEX_MEDICINE,
        warmup=True,
        batch_size=100,
        dispense_rate=None,
        viscosity_exponent=None,
        mover_speed=None,
        mixer_primary_time=None,
        mixer_final_time=None,
        capper_time=None
    )
    tiles = [
        Tile(type=TileType.INTERFACE, x=0, y=0),
        Tile(type=TileType.BLOCKED, x=0, y=1),
        Tile(type=TileType.INTERFACE, x=2, y=0),
        Tile(type=TileType.DISPENSER, dispensed_types=["Aspirin", "Lisinopril"], x=2, y=1)
    ]
    ingredients = [
        get_ingredient_domain_model(),
        get_ingredient_domain_model(name="Aspirin", note_type=None, viscosity=None,
                                    volatility_rank=None),
        get_ingredient_domain_model(name="Lisinopril", note_type=None, viscosity=None,
                                    volatility_rank=None)
    ]
    ingredient_list = IngredientListDomainModel(
        id=1,
        name="Ingredient List",
        type=IngredientListType.MEDICINE,
        ingredients=ingredients,
        ingredient_amount=len(ingredients)
    )
    layout = LayoutDomainModel(
        id=1,
        name="Layout",
        type=LayoutType.CUSTOM,
        tiles=tiles,
        tile_amount=len(tiles),
        interface_amount=sum(1 for tile in tiles if tile.type == TileType.INTERFACE),
        dispenser_amount=sum(1 for tile in tiles if tile.type == TileType.DISPENSER),
        filled=not any(tile.type == TileType.BLOCKED for tile in tiles),
        ingredient_list=ingredient_list,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    orders = [Order(items=[OrderItem(name="Aspirin", quantity=3), OrderItem(name="Lisinopril", quantity=1)]),
              Order(items=[OrderItem(name="Aspirin", quantity=3)]),
              Order(items=[OrderItem(name="Aspirin", quantity=2), OrderItem(name="Lisinopril", quantity=2)])]
    order_list = OrderListDomainModel(
        id=3,
        name="Order List",
        orders=orders,
        order_amount=len(orders),
        type=OrderListType.MEDICINE
    )
    experiment = ExperimentDomainModel(
        status=ExperimentStatus.RUNNING,
        layout=layout,
        order_list=order_list,
        configuration=configuration
    )

    # Act
    result = map_experiment_to_cplex_experiment(domain_model=experiment)

    # Assert
    assert result.model_dump(mode='json', exclude={"layout", "orders"}) == {
        "mover_amount": experiment.configuration.mover_amount,
        "time_limit": experiment.configuration.time_limit,
        "dispensing_time": experiment.configuration.dispensing_time,
        "batch_size": experiment.configuration.batch_size,
        "process_amount": experiment.configuration.process_amount,
        "warmup": experiment.configuration.warmup,
        "interface_time": experiment.configuration.interface_time
    }


def test_map_cplex_tile_to_domain_interface() -> None:
    # Arrange
    cplex_type = "interface"
    x = 4
    y = 5

    # Act
    result = map_cplex_tile_to_domain(cplex_type=cplex_type, x=x, y=y)

    # Assert
    assert result.model_dump(mode='json') == {
        "type": TileType.INTERFACE.value,
        "dispensed_types": None,
        "x": x,
        "y": y
    }


def test_map_cplex_tile_to_domain_dispenser() -> None:
    # Arrange
    cplex_type = "ASPIRIN"
    x = 2
    y = 3

    # Act
    result = map_cplex_tile_to_domain(cplex_type=cplex_type, x=x, y=y)

    # Assert
    assert result.model_dump(mode='json') == {
        "type": TileType.DISPENSER.value,
        "dispensed_types": ["ASPIRIN"],
        "x": x,
        "y": y
    }


def test_map_schedule_row_to_task_with_medicine() -> None:
    # Arrange
    data = {
        "Mover": "mover2",
        "Patient": 3,
        "Length": 15,
        "Start": 100,
        "Finish": 115,
        "Medicine": "ASPIRIN",
        "Position": [5, 10],
        "TicksAdded": 2
    }
    df_row = pd.DataFrame([data]).iloc[0]
    task_id = 1

    # Act
    result = map_schedule_row_to_task(schedule_row=df_row, task_id=task_id)

    # Assert
    assert result.model_dump(mode='json') == {
        "task_id": task_id,
        "order_id": data['Patient'],
        "duration": data['Length'],
        "start": data['Start'],
        "end": data['Finish'],
        "tile": Tile(
            type=TileType.DISPENSER,
            dispensed_types=['ASPIRIN'],
            x=data['Position'][0],
            y=data['Position'][1]
        ).model_dump(mode='json'),
        "needed_dispensed_type": None,
        "mover_id": 2,
        "ticks_added": data['TicksAdded']
    }


def test_map_schedule_row_to_task_no_mover_id() -> None:
    # Arrange
    data = {
        "Mover": "unassigned_mover",
        "Patient": 1,
        "Length": 5,
        "Start": 0,
        "Finish": 5,
        "Medicine": "IBUPROFEN",
        "Position": [1, 1],
        "TicksAdded": 0
    }
    df_row = pd.DataFrame([data]).iloc[0]
    task_id = 2

    # Act
    result = map_schedule_row_to_task(schedule_row=df_row, task_id=task_id)

    # Assert
    assert result.mover_id == -1


def test_map_finished_schedule_to_schedule() -> None:
    # Arrange
    data = [{
        "Mover": "mover2",
        "Patient": 3,
        "Length": 15,
        "Start": 100,
        "Finish": 115,
        "Medicine": "ASPIRIN",
        "Position": [5, 10],
        "TicksAdded": 2
    }
        ,
        {
            "Mover": "mover3",
            "Patient": 4,
            "Length": 10,
            "Start": 120,
            "Finish": 130,
            "Medicine": "IBUPROFEN",
            "Position": [2, 8],
            "TicksAdded": 0
        }]
    df_data = pd.DataFrame(data)

    # Act
    result = map_finished_schedule_to_schedule(finished_schedule=df_data)

    # Assert
    assert result.tasks[0].model_dump(mode='json') == {
        "task_id": 0,
        "order_id": data[0]['Patient'],
        "duration": data[0]['Length'],
        "start": data[0]['Start'],
        "end": data[0]['Finish'],
        "tile": Tile(
            type=TileType.DISPENSER,
            dispensed_types=['ASPIRIN'],
            x=data[0]['Position'][0],
            y=data[0]['Position'][1]
        ).model_dump(mode='json'),
        "needed_dispensed_type": None,
        "mover_id": 2,
        "ticks_added": data[0]['TicksAdded']
    }
    assert result.tasks[1].model_dump(mode='json') == {
        "task_id": 1,
        "order_id": data[1]['Patient'],
        "duration": data[1]['Length'],
        "start": data[1]['Start'],
        "end": data[1]['Finish'],
        "tile": Tile(
            type=TileType.DISPENSER,
            dispensed_types=['IBUPROFEN'],
            x=data[1]['Position'][0],
            y=data[1]['Position'][1]
        ).model_dump(mode='json'),
        "needed_dispensed_type": None,
        "mover_id": 3,
        "ticks_added": data[1]['TicksAdded']
    }


def test_map_cplex_result_to_result(mover_step_domain_model: MoverStep) -> None:
    # Arrange
    df = pd.DataFrame([{
        "Mover": "mover2",
        "Patient": 3,
        "Length": 15,
        "Start": 100,
        "Finish": 115,
        "Medicine": "ASPIRIN",
        "Position": [5, 10],
        "TicksAdded": 2
    }])
    cplex_result = CplexResult(
        initial_schedule=df.copy(),
        finished_schedule=df.copy(),
        warmup_cmax_per_batch=[10.5, None, 12.0],
        pre_routing_cmax=100,
        post_routing_cmax=110,
        routing_time=0.45,
        merging_time=0.12,
        gap_stats=None,
        mover_paths=[[mover_step_domain_model], [mover_step_domain_model]],
        max_path=1,
        color_dict={"order1": "#FF0000", "tile1": "#00FF00"},
        gantt_files={}
    )

    # Act
    result = map_cplex_result_to_result(cplex_result)

    # Assert
    assert result.mover_paths == cplex_result.mover_paths
    assert result.max_path == cplex_result.max_path
    assert result.color_dict == cplex_result.color_dict
    assert result.scheduled_cmax == cplex_result.pre_routing_cmax
    assert result.routed_cmax == cplex_result.post_routing_cmax
    assert result.routing_overhead_abs == cplex_result.post_routing_cmax - cplex_result.pre_routing_cmax
    assert result.routing_time_s == cplex_result.routing_time
