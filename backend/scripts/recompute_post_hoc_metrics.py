#!/usr/bin/env python3
"""
Recomputes metrics of finished experiments that do not depend on the CP schedule, using the current code:

- lower_bound_cmax: SHPPN + P||Cmax makespan lower bound (proven Gurobi bound), only with --lower-bound.
- dispensing_to_travel_ratio: nominal drug-dispensing time (dispensing_time x total ordered quantity)
  divided by the stored total transit time.

Layouts, configurations, and order lists are fetched from the backend API; the computation runs locally,
so it uses the code of this checkout rather than the code deployed on the server.

Usage:
    python recompute_post_hoc_metrics.py --batch-id 7 --lower-bound --output lowerbound_recomputed.csv
    python recompute_post_hoc_metrics.py --batch-id 4 --output overhead_recomputed.csv
"""

import argparse
import csv
import os
import sys
from typing import List, Dict, Any, Tuple

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from domain.enums import LayoutType, TileType  # noqa: E402
from domain.models.common.tile import Tile  # noqa: E402
from solvers.common.utilities.path_optimizer import PathOptimizer  # noqa: E402
from solvers.cplex_medicine.mapper import map_tiles_to_placement, map_placement_to_packer_result  # noqa: E402
from solvers.cplex_medicine.models import CplexLayout, CplexExperimentModel, CplexOrder  # noqa: E402
from solvers.cplex_medicine.utilities.lowerbound_heuristic import (  # noqa: E402
    load_real_patients, get_patient_lbs, optimize, get_lower_bound
)


def fetch_finished_experiments(api_url: str, batch_id: int) -> List[Dict[str, Any]]:
    """Fetch summaries of finished experiments of the given batch via REST API."""
    page = 1
    experiments = []
    while True:
        params = {"page": page, "size": 100, "statuses": ["finished"], "batch_id": batch_id}
        resp = requests.get(f"{api_url}/api/v1/experiments/", params=params, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("experiments"):
            break
        experiments.extend(data["experiments"])
        if page >= data.get("total", 1):
            break
        page += 1
    return experiments


def build_cplex_data(detail: Dict[str, Any]) -> Tuple[CplexExperimentModel, PathOptimizer]:
    """Builds the CP solver input and path optimizer from an experiment detail response."""
    tiles = [Tile(type=TileType(t["type"]), dispensed_types=t.get("dispensed_types"), x=t["x"], y=t["y"])
             for t in detail["layout"]["tiles"]]
    placement = map_tiles_to_placement(tiles)
    layout_type = LayoutType(detail["layout"]["type"])
    layout = CplexLayout(
        type=layout_type,
        row_amount=len(placement),
        column_amount=len(placement[0]),
        placement=placement,
        tile_amount=sum(1 for t in tiles if t.type == TileType.DISPENSER),
        interface_amount=sum(1 for t in tiles if t.type == TileType.INTERFACE),
        packer_result=map_placement_to_packer_result(placement),
    )
    config = detail["configuration"]
    orders = [CplexOrder(order_id=i, drug_names=[item["name"] for item in order["items"]],
                         dosages=[int(item["quantity"]) for item in order["items"]])
              for i, order in enumerate(detail["order_list"]["orders"])]
    data = CplexExperimentModel(
        orders=orders,
        mover_amount=config["mover_amount"],
        time_limit=config["time_limit"],
        dispensing_time=config["dispensing_time"],
        batch_size=config["batch_size"],
        process_amount=config["process_amount"],
        warmup=config["warmup"],
        interface_time=config["interface_time"],
        layout=layout,
    )
    filled = layout_type in [LayoutType.SQUARE, LayoutType.CUSTOM]
    unavailable = [[t.x, t.y] for t in tiles if t.type == TileType.BLOCKED]
    path_optimizer = PathOptimizer(layout.row_amount, layout.column_amount, filled, unavailable)
    return data, path_optimizer


def main():
    parser = argparse.ArgumentParser(description="Recompute schedule-independent metrics of finished experiments.")
    parser.add_argument("--api-url", default=os.getenv("BACKEND_URL", "http://localhost:8000"),
                        help="Backend API base URL (default: http://localhost:8000)")
    parser.add_argument("--batch-id", type=int, required=True, help="Batch ID to process")
    parser.add_argument("--lower-bound", action="store_true", help="Also recompute the makespan lower bound")
    parser.add_argument("--output", required=True, help="Output CSV filepath")
    args = parser.parse_args()

    experiments = fetch_finished_experiments(args.api_url, args.batch_id)
    print(f"Processing {len(experiments)} finished experiment(s) of batch {args.batch_id}...")

    patient_time_cache: Dict[Tuple[int, int, int, int], List[int]] = {}
    rows = []
    for exp in experiments:
        detail = requests.get(f"{args.api_url}/api/v1/experiments/{exp['id']}", timeout=120).json()
        metrics = requests.get(f"{args.api_url}/api/v1/simulations/{exp['id']}", timeout=120).json()["metrics"]
        data, path_optimizer = build_cplex_data(detail)

        total_quantity = sum(sum(order.dosages) for order in data.orders)
        nominal_dispensing = data.dispensing_time * total_quantity
        transit = metrics["total_transit_time"]
        row = {
            "experiment_id": exp["id"],
            "experiment_name": exp.get("name"),
            "layout_name": exp.get("layout_name"),
            "mover_amount": data.mover_amount,
            "dispensing_time": data.dispensing_time,
            "warmup": data.warmup,
            "order_amount": len(data.orders),
            "order_list_id": detail["order_list_id"],
            "scheduled_cmax": metrics["scheduled_cmax"],
            "routed_cmax": metrics["routed_cmax"],
            "total_transit_time": transit,
            "nominal_dispensing_time": nominal_dispensing,
            "dispensing_to_travel_ratio_old": metrics["dispensing_to_travel_ratio"],
            "dispensing_to_travel_ratio": round(nominal_dispensing / transit, 4) if transit else 0.0,
        }

        if args.lower_bound:
            key = (detail["layout_id"], detail["order_list_id"], data.dispensing_time, data.interface_time)
            if key not in patient_time_cache:
                patient_list, dosage_list = load_real_patients(data)
                patient_time_cache[key] = get_patient_lbs(len(data.orders), patient_list, dosage_list,
                                                          data.interface_time, data.dispensing_time, data.layout,
                                                          path_optimizer)
            model, _ = optimize(data.mover_amount, len(data.orders), patient_time_cache[key])
            row.update({
                "warm_start_cmax_old": metrics.get("warm_start_cmax"),
                "lower_bound_cmax": get_lower_bound(model),
                "lower_bound_proven_optimal": model.MIPGap < 1e-9,
                "gap_to_scheduled_pct": round((metrics["scheduled_cmax"] - get_lower_bound(model))
                                              / metrics["scheduled_cmax"] * 100, 2),
            })
        rows.append(row)
        print(f"  {len(rows)}/{len(experiments)} done", end="\r", flush=True)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
