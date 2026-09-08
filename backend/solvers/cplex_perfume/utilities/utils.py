import math

import pandas as pd
from docplex.cp.solution import CpoIntervalVarSolution
from pandas import DataFrame

from domain.enums import TileType
from solvers.cplex_perfume.models import Operation, Tile, CplexPerfumeData


# Processing times calculation
def proc_time(op: Operation, ingredients: dict, data: CplexPerfumeData) -> int:
    if op.label == TileType.MIXER.value:
        return data.mixer_primary_t if op.phase == 3 else data.mixer_final_t
    if op.label == TileType.CAPPER.value:
        return data.capper_t
    if op.label == TileType.INTERFACE.value:
        return data.interface_t
    ingredient_obj = ingredients[op.label]
    visc = ingredient_obj.viscosity
    return max(1, math.ceil(data.dispense_rate * op.volume_ml * (visc ** data.viscosity_exponent)))


def manhattan(a: Tile, b: Tile) -> int:
    return abs(a.row - b.row) + abs(a.col - b.col)


def travel_time(a: Tile, b: Tile, mover_speed: float) -> int:
    return math.ceil(mover_speed * manhattan(a, b))


# Build transition matrix
def build_transition_matrix(all_tiles: list[Tile], mover_speed: float) -> list[list[int]]:
    n = len(all_tiles)
    t_matrix = [[0] * n for _ in range(n)]
    for a in all_tiles:
        for b in all_tiles:
            t_matrix[a.idx][b.idx] = travel_time(a=a, b=b, mover_speed=mover_speed)
    return t_matrix


def solution_to_dataframe(solution: object, full_model: object) -> DataFrame:
    records = []
    for var in solution.get_all_var_solutions():
        if not isinstance(var, CpoIntervalVarSolution):
            continue
        var_name = var.get_name()
        if var_name not in full_model['var_info']:
            continue
        var_info = full_model["var_info"][var_name]
        records.append({
            "name": var.get_name(),
            "recipe": var_info["recipe"],
            "step": var_info["operation"],
            "dispenser_tile_id": var_info["dispenser"],
            "mover": var_info["mover"],
            "ingredient": var_info["ingredient"],
            "start": var.get_start(),
            "end": var.get_end(),
            "size": var.get_size(),  # optional, remove if not needed
        })

    return pd.DataFrame(records).sort_values("start").reset_index(drop=True)
