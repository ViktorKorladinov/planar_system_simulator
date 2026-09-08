import re
from typing import Tuple


def tile_str_to_tuple(tile_str: str) -> Tuple[int, int]:
    """
    Extract coordinates from a tile string

    Args:
        tile_str: string representing a tile. (e.g., 'tile3x2')

    Returns:
        Tuple[int, int]: Tuple (x,y). (e.g. (3,2)).
    """
    match = re.match(r"tile(\d+)x(\d+)", tile_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    raise ValueError(f"Invalid tile string format: {tile_str}")


def mover_str_to_int(mover_str: str) -> int:
    """
    Extract index of a mover from a mover string

    Args:
        mover_str: string representing a mover. (e.g., 'mover18')

    Returns:
        int: int x. (e.g. 18).
    """
    match = re.match(r"mover(\d+)", mover_str)
    if match:
        return int(match.group(1))
    raise ValueError(f"Invalid mover string format: {mover_str}")


def topology_to_name(topology_file_name: str) -> str:
    match = re.search(r"/(\w+)_", topology_file_name)
    if match:
        return match.group(1)
    else:
        return "unknown_layout"
