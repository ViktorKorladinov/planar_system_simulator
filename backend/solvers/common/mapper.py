from typing import Tuple, List, Dict, OrderedDict

from domain.enums import LayoutType, TileType
from domain.models.experiment import ExperimentDomainModel
from domain.models.layout import LayoutDomainModel
from solvers.common.models import SimulationData


def get_unavailable_coordinates(layout: LayoutDomainModel) -> List[List[int]]:
    """Returns list with coordinates of tiles that are blocked.

    Args:
        layout: The layout domain model.

    Returns:
        List with coordinates of tiles that are blocked.
    """
    result = []
    for tile in layout.tiles:
        if tile.type == TileType.BLOCKED:
            result.append([tile.x, tile.y])
    return result


def get_coordinate_dictionary(layout: LayoutDomainModel) -> Dict[str, List[Tuple[int, int]]]:
    """Returns dictionary with dispensed types or interfaces as keys and list of tuples with coordinates as values.

    Args:
        layout: The layout domain model.

    Returns:
        Dictionary with dispensed types or interfaces as keys and list of tuples with coordinates as values.
    """
    coord_dict = OrderedDict()
    sorted_tiles = sorted(layout.tiles, key=lambda t: (t.y, t.x))

    for tile in sorted_tiles:
        if tile.type in [TileType.EMPTY, TileType.BLOCKED]:
            continue

        if tile.type == TileType.INTERFACE:
            meds = ['interface']
        elif tile.type == TileType.CAPPER:
            meds = ['capper']
        elif tile.type == TileType.MIXER:
            meds = ['mixer']
        elif tile.dispensed_types:
            meds = tile.dispensed_types
        else:
            meds = []

        for med in meds:
            if med not in coord_dict:
                coord_dict[med] = []
            coord_dict[med].append((tile.x, tile.y))
    return coord_dict


def map_experiment_domain_to_simulation_data(domain_model: ExperimentDomainModel) -> SimulationData:
    """Maps experiment domain model to data required for creation of simulations

    Args:
        domain_model: The experiment domain model.

    Returns:
        Simulation data.
    """
    return SimulationData(
        row_amount=max(tile.y for tile in domain_model.layout.tiles) + 1,
        column_amount=max(tile.x for tile in domain_model.layout.tiles) + 1,
        filled=domain_model.layout.type == LayoutType.SQUARE or domain_model.layout.type == LayoutType.CUSTOM,
        unavailable_coordinates=get_unavailable_coordinates(domain_model.layout),
        coordinate_dict=get_coordinate_dictionary(domain_model.layout),
        mover_amount=domain_model.configuration.mover_amount
    )
