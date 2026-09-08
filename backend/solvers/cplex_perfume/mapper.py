from typing import List, Dict

import pandas as pd

from domain.enums import TileType, NotePhase
from domain.models.experiment import ExperimentDomainModel
from domain.models.ingredient_list import Ingredient
from domain.models.layout import LayoutDomainModel
from domain.models.order_list import OrderListDomainModel
from solvers.common.mapper import get_coordinate_dictionary
from solvers.cplex_perfume.models import CplexPerfumeData, Tile, Operation


def get_recipes(ingredients: Dict[str, Ingredient], machines: Dict[str, List[Tile]],
                order_list: OrderListDomainModel) -> list[list[Operation]]:
    """Converts orders into lists of operations.
    Args:
        ingredients: Dictionary with ingredient names as keys and ingredients as values.
        machines: Dictionary with labels as keys and corresponding tiles as values.
        order_list: List with orders that should be completed.
    Returns:
        List with lists of operations for each order.
    """
    recipes = []

    for order in order_list.orders:
        names = [item.name for item in order.items]
        volumes = [item.quantity for item in order.items]

        # Find the index of first PRIMARY_SOLVENT to disambiguate MIXER phases
        psolv_idx = next(
            (i for i, n in enumerate(names)
             if n in ingredients and
             ingredients[n].note_type.name == "PRIMARY_SOLVENT"),
            len(names)
        )

        mixer_count = 0
        ops = []
        for step, (name, vol) in enumerate(zip(names, volumes)):
            if name == "mixer":
                phase = 3 if step < psolv_idx else 6
                mixer_count += 1
            elif name == "capper":
                phase = 7
            elif name == "interface":
                phase = 0
            else:
                note_type = ingredients[name].note_type
                phase = NotePhase[note_type.name].value

            ops.append(Operation(
                step=step,
                phase=phase,
                label=name,
                volume_ml=vol,
                candidates=machines.get(name, [])
            ))

        recipes.append(ops)

    return recipes


def map_tiles_layout_domain_to_perfume_tiles(layout: LayoutDomainModel) -> List[Tile]:
    """Maps tiles from layout domain model to list of tiles required by Cplex perfume solver.

    Args:
        layout: Layout domain model which should be mapped.

    Returns:
        List of tiles required by Cplex perfume solver.
    """
    tiles = []
    idx = 0
    for tile in layout.tiles:
        if tile.type == TileType.DISPENSER:
            for dispensed_type in tile.dispensed_types:
                tiles.append(Tile(idx=idx, col=tile.x, row=tile.y, label=dispensed_type))
                idx += 1
        elif tile.type == TileType.CAPPER:
            tiles.append(Tile(idx=idx, col=tile.x, row=tile.y, label='capper'))
            idx += 1
        elif tile.type == TileType.MIXER:
            tiles.append(Tile(idx=idx, col=tile.x, row=tile.y, label='mixer'))
            idx += 1
        elif tile.type == TileType.INTERFACE:
            tiles.append(Tile(idx=idx, col=tile.x, row=tile.y, label='interface'))
            idx += 1
    return tiles


def map_experiment_domain_to_cplex_perfume_data(domain_model: ExperimentDomainModel) -> CplexPerfumeData:
    """Maps experiment domain model to daa required by Cplex perfume solver.

    Args:
        domain_model: Experiment domain model which should be mapped.

    Returns:
        Cplex perfumed data.
    """
    tiles_flat = map_tiles_layout_domain_to_perfume_tiles(domain_model.layout)
    ingredients = {ingredient.name: ingredient for ingredient in domain_model.layout.ingredient_list.ingredients}
    machines = {}
    for tile in tiles_flat:
        machines.setdefault(tile.label, []).append(tile)
    return CplexPerfumeData(
        ingredients=ingredients,
        tiles_flat=tiles_flat,
        machines=machines,
        recipes_raw=get_recipes(ingredients=ingredients, machines=machines, order_list=domain_model.order_list),
        tmax_values=[order.t_max for order in domain_model.order_list.orders],
        time_limit=domain_model.configuration.time_limit,
        process_amount=domain_model.configuration.process_amount,
        dispense_rate=domain_model.configuration.dispense_rate,
        viscosity_exponent=domain_model.configuration.viscosity_exponent,
        mover_speed=domain_model.configuration.mover_speed,
        mixer_final_t=domain_model.configuration.mixer_final_time,
        mixer_primary_t=domain_model.configuration.mixer_primary_time,
        capper_t=domain_model.configuration.capper_time,
        interface_t=domain_model.configuration.interface_time,
        mover_amount=domain_model.configuration.mover_amount
    )


def map_schedule_dataframe_to_simulation_dataframe(
        schedule: pd.DataFrame,
        layout: LayoutDomainModel
) -> pd.DataFrame:
    """Maps initial schedule to Dataframe required as starting point for simulation creation.

    Args:
        schedule: Initial schedule generated by solver.
        layout: Experiment layout.

    Returns:
        Dataframe required as starting point for simulation creation.
    """
    coord_dict = get_coordinate_dictionary(layout)
    data = []
    tiles = map_tiles_layout_domain_to_perfume_tiles(layout)

    for _, row in schedule.iterrows():
        # Skip rows with unscheduled tasks
        if pd.isna(row['size']) or pd.isna(row['start']) or pd.isna(row['end']):
            continue
        patient_id = int(row['recipe'])
        medicine = str(row['ingredient'])
        tile_id = int(row['dispenser_tile_id'])
        tile = tiles[tile_id]
        tile_str = f"tile{tile.col}x{tile.row}"
        coords = (tile.col, tile.row)

        if medicine in ['mixer', 'capper', 'interface']:
            dispenser_id = 0
        else:
            if medicine in coord_dict:
                try:
                    dispenser_id = coord_dict[medicine].index(coords)
                except ValueError:
                    dispenser_id = 0
            else:
                dispenser_id = 0

        data.append({
            "Task": f"Job {patient_id + 1}",
            "Medicine": medicine,
            "Tile": tile_str,
            "Patient": patient_id,
            "Length": int(row['size']),
            "Start": int(row['start']),
            "Mover": f"mover{int(row['mover'])}",
            "Finish": int(row['end']),
            "Dispenser": dispenser_id
        })
    return pd.DataFrame(data)
