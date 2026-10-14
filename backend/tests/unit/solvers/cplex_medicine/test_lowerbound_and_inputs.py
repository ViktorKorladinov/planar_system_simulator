from unittest.mock import MagicMock

from domain.enums import LayoutType
from solvers.common.utilities.path_optimizer import PathOptimizer
from solvers.cplex_medicine.mapper import map_placement_to_packer_result
from solvers.cplex_medicine.models import CplexLayout, CplexExperimentModel, CplexOrder
from solvers.cplex_medicine.utilities.batch_handler import ScheduleCreator
from solvers.cplex_medicine.utilities.lowerbound_heuristic import patient_tsp_lb, get_lower_bound

INTERFACE_TIME = 3


def _layout(placement, layout_type, interface_amount=1) -> CplexLayout:
    return CplexLayout(
        type=layout_type,
        row_amount=len(placement),
        column_amount=len(placement[0]),
        placement=placement,
        tile_amount=sum(1 for row in placement for cell in row if cell not in ['interface', 'empty', 'blocked']),
        interface_amount=interface_amount,
        packer_result=map_placement_to_packer_result(placement)
    )


def test_patient_lb_uses_travel_distance_on_line_layout():
    # Vertical line (4 rows x 1 column): interface at y=0, drug A at y=2 -> round trip of 4 moves
    placement = [['interface'], ['empty'], ['A'], ['empty']]
    layout = _layout(placement, LayoutType.LINE)
    path_optimizer = PathOptimizer(rows=4, cols=1, filled=False)

    lb, _ = patient_tsp_lb(['A'], [5], layout, INTERFACE_TIME, 1, path_optimizer)

    assert lb == 2 * INTERFACE_TIME + 5 + 4


def test_patient_lb_uses_travel_distance_on_square_layout():
    # 3x3 square: interface at (0, 0), drug A at (2, 2) -> 4 moves each way
    placement = [['interface', 'empty', 'empty'],
                 ['empty', 'empty', 'empty'],
                 ['empty', 'empty', 'A']]
    layout = _layout(placement, LayoutType.SQUARE)
    path_optimizer = PathOptimizer(rows=3, cols=3, filled=True)

    lb, _ = patient_tsp_lb(['A'], [5], layout, INTERFACE_TIME, 2, path_optimizer)

    assert lb == 2 * INTERFACE_TIME + 2 * 5 + 8


def test_get_lower_bound_uses_proven_bound_rounded_up():
    model = MagicMock()
    model.ObjBound = 9.4
    model.x = [0, 1, 12.0]  # incumbent must be ignored
    assert get_lower_bound(model) == 10

    model.ObjBound = 10.0000001
    assert get_lower_bound(model) == 10


def test_schedule_creator_uses_configured_interface_time_and_mover_amount():
    placement = [['interface', 'A', 'B']]
    data = CplexExperimentModel(
        orders=[CplexOrder(order_id=0, drug_names=['A', 'B'], dosages=[2, 4])],
        mover_amount=3,
        time_limit=1,
        dispensing_time=10,
        batch_size=100,
        process_amount=1,
        warmup=False,
        interface_time=7,
        layout=_layout(placement, LayoutType.SQUARE)
    )

    creator = ScheduleCreator(data)

    assert creator.patients_df.loc[0, 'dosages'] == [7, 7, 20, 40]
    assert creator.movers == ['mover0', 'mover1', 'mover2']
