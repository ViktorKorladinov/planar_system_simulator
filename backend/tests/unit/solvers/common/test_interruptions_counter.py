import pandas as pd

from domain.enums import MoverMode
from domain.models.experiment import MoverStep
from solvers.common.utilities.interruptions_counter import analyze_interruptions

SHARED_TILE = (5, 5)


def _step(x: int, y: int, mode: MoverMode) -> MoverStep:
    return MoverStep(x=x, y=y, mode=mode, order="Patient 0")


def _build_instance(mover_amount: int, shared_ticks: int = 1):
    """Each mover loads on its own tile during ticks 0-1, moves at tick 2 and then transits
    the shared tile for `shared_ticks` consecutive ticks starting at tick 3."""
    schedule = pd.DataFrame({
        'Tile': [f"tile{10 + m}x0" for m in range(mover_amount)],
        'Mover': [f"mover{m}" for m in range(mover_amount)],
        'Start': [0] * mover_amount,
        'Finish': [2] * mover_amount,
        'Length': [2] * mover_amount,
    })
    paths = []
    for m in range(mover_amount):
        path = [_step(10 + m, 0, MoverMode.LOADING), _step(10 + m, 0, MoverMode.LOADING),
                _step(10 + m, 1, MoverMode.TRANSIT)]
        path += [_step(*SHARED_TILE, MoverMode.TRANSIT) for _ in range(shared_ticks)]
        paths.append(path)
    return schedule, paths


def test_three_transiting_movers_are_within_capacity():
    schedule, paths = _build_instance(3)
    stats = analyze_interruptions(schedule, paths)
    assert [s['interruptions'] for s in stats] == [0, 0, 0]


def test_fourth_transiting_mover_is_penalized():
    schedule, paths = _build_instance(4)
    stats = analyze_interruptions(schedule, paths)
    assert [s['transit_interruptions'] for s in stats] == [0, 0, 0, 1]
    assert [s['interruptions'] for s in stats] == [0, 0, 0, 1]
    assert all(s['task_interruptions'] == 0 for s in stats)


def test_excess_movers_receive_staggered_penalties():
    schedule, paths = _build_instance(5)
    stats = analyze_interruptions(schedule, paths)
    assert [s['transit_interruptions'] for s in stats] == [0, 0, 0, 1, 2]


def test_continuous_congestion_is_penalized_once():
    schedule, paths = _build_instance(4, shared_ticks=3)
    stats = analyze_interruptions(schedule, paths)
    assert [s['transit_interruptions'] for s in stats] == [0, 0, 0, 1]


def test_congestion_fix_can_be_disabled():
    schedule, paths = _build_instance(5)
    stats = analyze_interruptions(schedule, paths, use_transit_congestion_fix=False)
    assert [s['interruptions'] for s in stats] == [0, 0, 0, 0, 0]


def test_dispensing_interruptions_are_still_counted():
    # mover1 transits over mover0's dispensing tile during tick 1 of its task
    schedule = pd.DataFrame({
        'Tile': ["tile0x0", "tile3x0"],
        'Mover': ["mover0", "mover1"],
        'Start': [0, 4],
        'Finish': [3, 6],
        'Length': [3, 2],
    })
    paths = [
        [_step(0, 0, MoverMode.LOADING) for _ in range(3)],
        [_step(1, 0, MoverMode.TRANSIT), _step(0, 0, MoverMode.TRANSIT), _step(1, 0, MoverMode.TRANSIT),
         _step(2, 0, MoverMode.TRANSIT), _step(3, 0, MoverMode.LOADING), _step(3, 0, MoverMode.LOADING)],
    ]
    stats = analyze_interruptions(schedule, paths)
    assert stats[0]['task_interruptions'] == 1
    assert stats[0]['transit_interruptions'] == 0
    assert stats[0]['interruptions'] == 1
    assert stats[1]['interruptions'] == 0
