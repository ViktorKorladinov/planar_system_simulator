#!/usr/bin/env python3
"""
Measures how long the makespan lower bound (SHPPN per order + P||Cmax) takes to compute and to prove optimal.

For each layout and order set, the per-order SHPPN processing times are computed once (timed). Then P||Cmax is
solved for every mover count with a time cap, recording the time to proven optimality, the time at which the
final incumbent was found, and the remaining gap if the cap is reached. The classical trivial bound
max(ceil(sum p / m), max p) is recorded for comparison.

Usage:
    python lower_bound_timing.py --layouts data/layouts/square64.json \
        --order-sets data/order_sets/orders_set1.json --movers 1 4 8 12 --time-cap 600 --output timing.csv
"""

import argparse
import csv
import json
import math
import os
import sys
import time
from typing import List, Dict, Any

import gurobipy as g

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from domain.enums import LayoutType  # noqa: E402
from solvers.common.utilities.path_optimizer import PathOptimizer  # noqa: E402
from solvers.cplex_medicine.mapper import map_placement_to_packer_result  # noqa: E402
from solvers.cplex_medicine.models import CplexLayout  # noqa: E402
from solvers.cplex_medicine.utilities.lowerbound_heuristic import get_patient_lbs, optimize, get_lower_bound  # noqa: E402

LAYOUT_TYPES = {"square": LayoutType.SQUARE, "doubleline": LayoutType.DOUBLE_LINE,
                "line": LayoutType.LINE, "ring": LayoutType.RING}


def load_layout(path: str):
    """Builds the CP layout model and path optimizer from a layout JSON file."""
    with open(path, encoding="utf-8") as f:
        placement = json.load(f)["placement"]
    name = os.path.basename(path).replace(".json", "")
    layout_type = next(t for prefix, t in LAYOUT_TYPES.items() if name.startswith(prefix))
    cells = [cell for row in placement for cell in row]
    layout = CplexLayout(
        type=layout_type,
        row_amount=len(placement),
        column_amount=len(placement[0]),
        placement=placement,
        tile_amount=sum(1 for c in cells if c not in ["interface", "empty", "blocked"]),
        interface_amount=cells.count("interface"),
        packer_result=map_placement_to_packer_result(placement),
    )
    unavailable = [[x, y] for y, row in enumerate(placement) for x, cell in enumerate(row) if cell == "blocked"]
    filled = layout_type in [LayoutType.SQUARE, LayoutType.CUSTOM]
    return name, layout, PathOptimizer(layout.row_amount, layout.column_amount, filled, unavailable)


def load_orders(path: str):
    with open(path, encoding="utf-8") as f:
        orders = json.load(f)["orders"]
    drug_lists = [set(item["name"] for item in order["items"]) for order in orders]
    dosage_lists = [[int(item["quantity"]) for item in order["items"]] for order in orders]
    return os.path.basename(path).replace(".json", ""), drug_lists, dosage_lists


def solve_pcmax(patient_time: List[int], movers: int, time_cap: float, threads) -> Dict[str, Any]:
    """Solves P||Cmax and records when the final incumbent was found."""
    incumbent_times = []

    def callback(model, where):
        if where == g.GRB.Callback.MIPSOL:
            incumbent_times.append((model.cbGet(g.GRB.Callback.RUNTIME), model.cbGet(g.GRB.Callback.MIPSOL_OBJ)))

    model, _ = optimize(movers, len(patient_time), patient_time, time_limit=time_cap, threads=threads,
                        callback=callback)
    best = model.ObjVal
    time_to_best = min((t for t, obj in incumbent_times if obj <= best + 1e-6), default=0.0)
    first_time, first_obj = incumbent_times[0] if incumbent_times else (0.0, best)
    return {
        "pcmax_runtime_s": round(model.Runtime, 3),
        "proven_optimal": model.Status == g.GRB.OPTIMAL,
        "time_to_first_incumbent_s": round(first_time, 3),
        "first_incumbent_cmax": round(first_obj),
        "time_to_best_incumbent_s": round(time_to_best, 3),
        "incumbent_cmax": round(best),
        "lower_bound_cmax": get_lower_bound(model),
        "mip_gap_pct": round(model.MIPGap * 100, 4),
        "trivial_bound": max(math.ceil(sum(patient_time) / movers), max(patient_time)),
    }


def main():
    parser = argparse.ArgumentParser(description="Time the SHPPN + P||Cmax lower bound computation.")
    parser.add_argument("--layouts", nargs="+", required=True, help="Layout JSON files")
    parser.add_argument("--order-sets", nargs="+", required=True, help="Order-list JSON files")
    parser.add_argument("--movers", nargs="+", type=int, required=True, help="Mover counts")
    parser.add_argument("--dispensing-time", type=int, default=10, help="Ticks per dispensed unit (default: 10)")
    parser.add_argument("--interface-time", type=int, default=3, help="Ticks per interface operation (default: 3)")
    parser.add_argument("--time-cap", type=float, default=600, help="P||Cmax time cap in seconds (default: 600)")
    parser.add_argument("--threads", type=int, default=None, help="Gurobi threads (default: Gurobi's choice)")
    parser.add_argument("--output", required=True, help="Output CSV filepath (appended to row by row)")
    args = parser.parse_args()

    fieldnames = None
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        for layout_path in args.layouts:
            layout_name, layout, path_optimizer = load_layout(layout_path)
            for orders_path in args.order_sets:
                set_name, drug_lists, dosage_lists = load_orders(orders_path)
                start = time.perf_counter()
                patient_time = get_patient_lbs(len(drug_lists), drug_lists, dosage_lists, args.interface_time,
                                               args.dispensing_time, layout, path_optimizer)
                shppn_time = time.perf_counter() - start
                for movers in args.movers:
                    row = {
                        "layout": layout_name, "order_set": set_name, "orders": len(drug_lists), "movers": movers,
                        "dispensing_time": args.dispensing_time, "interface_time": args.interface_time,
                        "time_cap_s": args.time_cap, "threads": args.threads,
                        "shppn_time_s": round(shppn_time, 3),
                        **solve_pcmax(patient_time, movers, args.time_cap, args.threads),
                    }
                    if fieldnames is None:
                        fieldnames = list(row.keys())
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                    writer.writerow(row)
                    f.flush()
                    print(f"{layout_name} {set_name} m={movers}: optimal={row['proven_optimal']} "
                          f"runtime={row['pcmax_runtime_s']}s gap={row['mip_gap_pct']}%", flush=True)


if __name__ == "__main__":
    main()
