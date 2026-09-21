import pandas as pd
import pytest

from domain.enums import MoverMode, ExperimentStatus, GraphType, LayoutType, SolverType
from domain.models.experiment import Result, MoverStep, ExperimentDomainModel
from domain.models.layout import LayoutDomainModel
from domain.models.configuration import ConfigurationDomainModel
from domain.models.order_list import OrderListDomainModel, Order, OrderItem
from domain.models.common.tile import Tile
from mappers.domain.experiment_mapper import (
    map_experiment_domain_to_summary_response_dto,
    map_experiment_domain_to_simulation_get_response_dto
)
from solvers.common.models import SimulationData
from solvers.common.utilities.simulation_creator import create_simulation
from tests.factories.experiment_factory import get_experiment_domain_model


def test_result_domain_model_fields():
    """Verify that all new metrics can be populated and dumped correctly."""
    result = Result(
        mover_paths=[[
            MoverStep(x=0, y=0, mode=MoverMode.TRANSIT, order="order_0"),
            MoverStep(x=0, y=1, mode=MoverMode.LOADING, order="order_0"),
            MoverStep(x=0, y=1, mode=MoverMode.WAIT_REST, order="order_0"),
        ]],
        max_path=3,
        color_dict={"order_0": "blue"},
        scheduled_cmax=100,
        routed_cmax=120,
        routing_overhead_abs=20,
        routing_overhead_pct=20.0,
        routing_iterations=3,
        routing_time_s=1.234,
        scheduling_time_s=5.678,
        total_time_s=6.912,
        initial_interruptions=5,
        final_interruptions=0,
        iterations_interruption_history=[5, 2, 0],
        cp_solve_status="Optimal",
        best_bound_internal=95.0,
        internal_gap_pct=5.0,
        solver_branches=1200,
        solver_fails=30,
        solver_choice_points=1500,
        warm_start_cmax=90.0,
        total_transit_time=1,
        total_dispensing_time=1,
        total_wait_time=1,
        dispensing_to_travel_ratio=1.0,
        mover_busy_time_per_mover={"mover_0": 2},
        task_count=10,
        batch_count=2,
    )

    data = result.model_dump(mode="json")
    assert data["scheduled_cmax"] == 100
    assert data["routed_cmax"] == 120
    assert data["routing_overhead_abs"] == 20
    assert data["routing_overhead_pct"] == 20.0
    assert data["routing_iterations"] == 3
    assert data["iterations_interruption_history"] == [5, 2, 0]
    assert data["cp_solve_status"] == "Optimal"
    assert data["best_bound_internal"] == 95.0
    assert data["dispensing_to_travel_ratio"] == 1.0

    restored = Result.model_validate(data)
    assert restored.scheduled_cmax == 100
    assert restored.routing_overhead_abs == 20
    assert restored.routing_iterations == 3


def test_map_summary_and_simulation_response_dtos():
    """Verify that summary and simulation response mappers expose the new metrics."""
    result = Result(
        mover_paths=[[MoverStep(x=0, y=0, mode=MoverMode.LOADING, order="order_0")]],
        max_path=1,
        color_dict={},
        scheduled_cmax=50,
        routed_cmax=55,
        routing_overhead_abs=5,
        routing_overhead_pct=10.0,
        routing_iterations=2,
        routing_time_s=0.25,
        scheduling_time_s=1.5,
        total_time_s=1.75,
        best_bound_internal=48.0,
    )

    domain_model = get_experiment_domain_model()
    domain_model.result = result

    summary_dto = map_experiment_domain_to_summary_response_dto(domain_model)
    assert summary_dto.scheduled_cmax == 50
    assert summary_dto.routed_cmax == 55
    assert summary_dto.routing_overhead_abs == 5
    assert summary_dto.routing_overhead_pct == 10.0
    assert summary_dto.routing_iterations == 2
    assert summary_dto.total_time_s == 1.75

    sim_dto = map_experiment_domain_to_simulation_get_response_dto(domain_model)
    assert sim_dto.metrics is not None
    assert sim_dto.metrics["scheduled_cmax"] == 50
    assert sim_dto.metrics["routed_cmax"] == 55
    assert sim_dto.metrics["routing_overhead_abs"] == 5
    assert sim_dto.metrics["best_bound_internal"] == 48.0
    assert sim_dto.metrics["routing_time_s"] == 0.25
