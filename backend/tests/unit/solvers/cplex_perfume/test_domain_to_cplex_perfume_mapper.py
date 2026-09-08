from typing import Dict
from unittest.mock import patch

import numpy as np
import pandas as pd

from domain.enums import NoteType, TileType, LayoutType, IngredientListType, OrderListType
from domain.models.common.tile import Tile
from domain.models.experiment import ExperimentDomainModel
from domain.models.ingredient_list import Ingredient, IngredientListDomainModel
from domain.models.layout import LayoutDomainModel
from domain.models.order_list import OrderListDomainModel, Order, OrderItem
from solvers.cplex_perfume.mapper import (
    get_recipes,
    map_tiles_layout_domain_to_perfume_tiles,
    map_experiment_domain_to_cplex_perfume_data,
    map_schedule_dataframe_to_simulation_dataframe
)
from solvers.cplex_perfume.models import Tile as PerfumeTile
from tests.factories.ingredient_list_factory import get_ingredient_domain_model


def test_get_recipes_assigns_correct_phases() -> None:
    # Arrange
    order = Order(
        items=[
            OrderItem(name="Rose Oil", quantity=2),
            OrderItem(name="mixer", quantity=0),
            OrderItem(name="Ethanol", quantity=5),
            OrderItem(name="mixer", quantity=0),
            OrderItem(name="capper", quantity=0)
        ],
        t_max=100
    )
    order_list = OrderListDomainModel(orders=[order], order_amount=1, type=OrderListType.PERFUME)

    ingredients: Dict[str, Ingredient] = {
        "Rose Oil": Ingredient(name="Rose Oil", note_type=NoteType.TOP_NOTE, viscosity=1.0, volatility_rank=1),
        "Ethanol": Ingredient(name="Ethanol", note_type=NoteType.PRIMARY_SOLVENT, viscosity=1.0, volatility_rank=5)
    }

    machines: Dict[str, list[PerfumeTile]] = {
        "interface": [PerfumeTile(idx=0, row=0, col=0, label="interface")],
        "Rose Oil": [PerfumeTile(idx=1, row=1, col=1, label="Rose Oil")],
        "mixer": [PerfumeTile(idx=2, row=2, col=2, label="mixer")],
        "Ethanol": [PerfumeTile(idx=3, row=3, col=3, label="Ethanol")],
        "capper": [PerfumeTile(idx=4, row=4, col=4, label="capper")]
    }

    # Act
    recipes = get_recipes(ingredients=ingredients, machines=machines, order_list=order_list)

    # Assert
    assert len(recipes) == 1
    ops = recipes[0]
    assert len(ops) == 5
    assert ops[0].label == "Rose Oil" and ops[0].phase == 2
    assert ops[1].label == "mixer" and ops[1].phase == 3
    assert ops[2].label == "Ethanol" and ops[2].phase == 4
    assert ops[3].label == "mixer" and ops[3].phase == 6
    assert ops[4].label == "capper" and ops[4].phase == 7


def test_map_tiles_layout_domain_to_perfume_tiles_flattens_multi_dispensers() -> None:
    # Arrange
    ingredients = [
        get_ingredient_domain_model(name="Water", note_type=NoteType.HEART_NOTE, viscosity=5.5,
                                    volatility_rank=3),
        get_ingredient_domain_model(name="Ethanol", note_type=NoteType.BASE_NOTE, viscosity=4.5,
                                    volatility_rank=2)
    ]
    ingredient_list = IngredientListDomainModel(
        id=1,
        name="Best List",
        type=IngredientListType.PERFUME,
        ingredients=ingredients,
        ingredient_amount=len(ingredients)
    )
    layout = LayoutDomainModel(
        id=1, name="Test", type=LayoutType.CUSTOM, tile_amount=3, interface_amount=1, dispenser_amount=1, filled=True,
        ingredient_list=ingredient_list,
        tiles=[
            Tile(type=TileType.INTERFACE, x=0, y=0),
            Tile(type=TileType.DISPENSER, x=0, y=1, dispensed_types=["Ethanol", "Water"]),
            Tile(type=TileType.MIXER, x=1, y=0),
            Tile(type=TileType.CAPPER, x=1, y=1)
        ]
    )

    # Act
    perfume_tiles = map_tiles_layout_domain_to_perfume_tiles(layout)

    # Assert
    assert len(perfume_tiles) == 5

    assert perfume_tiles[0].label == "interface"
    assert perfume_tiles[0].idx == 0
    assert perfume_tiles[0].row == 0
    assert perfume_tiles[0].col == 0

    assert perfume_tiles[1].label == "Ethanol"
    assert perfume_tiles[1].idx == 1
    assert perfume_tiles[1].row == 1
    assert perfume_tiles[1].col == 0

    assert perfume_tiles[2].label == "Water"
    assert perfume_tiles[2].idx == 2
    assert perfume_tiles[2].row == 1
    assert perfume_tiles[2].col == 0

    assert perfume_tiles[3].label == "mixer"
    assert perfume_tiles[3].idx == 3
    assert perfume_tiles[3].row == 0
    assert perfume_tiles[3].col == 1

    assert perfume_tiles[4].label == "capper"
    assert perfume_tiles[4].idx == 4
    assert perfume_tiles[4].row == 1
    assert perfume_tiles[4].col == 1


def test_map_experiment_domain_to_cplex_perfume_data(experiment_domain_model: ExperimentDomainModel) -> None:
    # Arrange
    experiment_domain_model.configuration.time_limit = 120
    experiment_domain_model.configuration.dispense_rate = 3.5
    experiment_domain_model.configuration.viscosity_exponent = 0.8
    experiment_domain_model.configuration.mixer_primary_time = 15
    experiment_domain_model.configuration.mixer_final_time = 25
    experiment_domain_model.configuration.capper_time = 10

    # Act
    cplex_data = map_experiment_domain_to_cplex_perfume_data(experiment_domain_model)

    # Assert
    assert cplex_data.time_limit == 120
    assert cplex_data.dispense_rate == 3.5
    assert cplex_data.viscosity_exponent == 0.8
    assert cplex_data.mixer_primary_t == 15
    assert cplex_data.mixer_final_t == 25
    assert cplex_data.capper_t == 10
    assert "interface" in cplex_data.machines
    assert len(cplex_data.tiles_flat) > 0
    assert len(cplex_data.tmax_values) == len(experiment_domain_model.order_list.orders)
    assert cplex_data.tmax_values[0] == experiment_domain_model.order_list.orders[0].t_max


@patch("solvers.cplex_perfume.mapper.get_coordinate_dictionary")
@patch("solvers.cplex_perfume.mapper.map_tiles_layout_domain_to_perfume_tiles")
def test_map_schedule_dataframe_to_simulation_dataframe_standard_flow(mock_map_tiles, mock_coord_dict) -> None:
    # Arrange
    ingredients = [
        get_ingredient_domain_model(name="Lisinopril", note_type=None, viscosity=None,
                                    volatility_rank=None),
        get_ingredient_domain_model(name="Ethanol", note_type=None, viscosity=None,
                                    volatility_rank=None)
    ]
    ingredient_list = IngredientListDomainModel(
        id=1,
        name="Best List",
        type=IngredientListType.MEDICINE,
        ingredients=ingredients,
        ingredient_amount=len(ingredients)
    )
    layout = LayoutDomainModel(id=1, name="Test", type=LayoutType.CUSTOM, tile_amount=0, interface_amount=0,
                               dispenser_amount=0, filled=True, ingredient_list=ingredient_list, tiles=[])

    mock_coord_dict.return_value = {"Ethanol": [(1, 1)]}
    mock_map_tiles.return_value = [
        PerfumeTile(idx=0, col=0, row=0, label="Lisinopril"),
        PerfumeTile(idx=1, col=1, row=1, label="Ethanol"),
    ]
    cplex_df = pd.DataFrame([
        {"recipe": 0, "ingredient": "Lisinopril", "dispenser_tile_id": 0, "size": 5, "start": 0, "end": 5, "mover": 0},
        {"recipe": 0, "ingredient": "Ethanol", "dispenser_tile_id": 1, "size": 10, "start": 10, "end": 20, "mover": 0},
    ])

    # Act
    sim_df = map_schedule_dataframe_to_simulation_dataframe(schedule=cplex_df, layout=layout)

    # Assert
    assert len(sim_df) == 2

    assert sim_df.iloc[0]["Task"] == "Job 1"
    assert sim_df.iloc[0]["Medicine"] == "Lisinopril"
    assert sim_df.iloc[0]["Tile"] == "tile0x0"
    assert sim_df.iloc[0]["Dispenser"] == 0

    assert sim_df.iloc[1]["Medicine"] == "Ethanol"
    assert sim_df.iloc[1]["Tile"] == "tile1x1"
    assert sim_df.iloc[1]["Start"] == 10
    assert sim_df.iloc[1]["Finish"] == 20
    assert sim_df.iloc[1]["Mover"] == "mover0"


@patch("solvers.cplex_perfume.mapper.get_coordinate_dictionary")
@patch("solvers.cplex_perfume.mapper.map_tiles_layout_domain_to_perfume_tiles")
def test_map_schedule_dataframe_to_simulation_dataframe_skips_nans_and_handles_missing_dispensers(mock_map_tiles,
                                                                                                  mock_coord_dict) -> None:
    # Arrange
    ingredients = [
        get_ingredient_domain_model(name="Aspirin", note_type=None, viscosity=None,
                                    volatility_rank=None),
        get_ingredient_domain_model(name="Lisinopril", note_type=None, viscosity=None,
                                    volatility_rank=None)
    ]
    ingredient_list = IngredientListDomainModel(
        id=1,
        name="Best List",
        type=IngredientListType.MEDICINE,
        ingredients=ingredients,
        ingredient_amount=len(ingredients)
    )
    layout = LayoutDomainModel(id=1, name="Test", type=LayoutType.CUSTOM, tile_amount=0, interface_amount=0,
                               dispenser_amount=0, filled=True, ingredient_list=ingredient_list, tiles=[])
    mock_coord_dict.return_value = {}
    mock_map_tiles.return_value = [
        PerfumeTile(idx=0, col=2, row=2, label="UnknownMedicine")
    ]
    cplex_df = pd.DataFrame([
        {"recipe": 0, "ingredient": "UnknownMedicine", "dispenser_tile_id": 0, "size": 10, "start": 0, "end": 10,
         "mover": 1},
        {"recipe": 1, "ingredient": "interface", "dispenser_tile_id": 0, "size": np.nan, "start": np.nan, "end": np.nan,
         "mover": 1},
    ])

    # Act
    sim_df = map_schedule_dataframe_to_simulation_dataframe(schedule=cplex_df, layout=layout)

    # Assert
    assert len(sim_df) == 1

    assert sim_df.iloc[0]["Medicine"] == "UnknownMedicine"
    assert sim_df.iloc[0]["Tile"] == "tile2x2"
    assert sim_df.iloc[0]["Dispenser"] == 0
