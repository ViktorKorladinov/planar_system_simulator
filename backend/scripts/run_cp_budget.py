#!/usr/bin/env python3
"""
Runs the CP scheduling model (without lower bound, warm start, or routing, so without Gurobi) for one instance
and one total time budget, and writes the result as JSON. Used for the time-limit and batching experiments.

The orders are split into consecutive batches of --batch-size (one batch if --batch-size >= number of orders);
the total budget is split evenly over the batches. The merged schedule is compressed exactly like the routing
phase does before routing (earliest start times over the fixed per-mover and per-tile sequences, i.e. the
longest path in the precedence DAG), which equals the optimum of the ScheduleExtender LP.

Usage:
    python run_cp_budget.py --layout data/layouts/square64.json --orders data/order_sets/large_set1.json \
        --num-orders 200 --movers 8 --batch-size 100 --time-budget 1000 --seed 1 --output result.json
"""

import argparse
import json
import math
import os
import platform
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from docplex.cp.config import context  # noqa: E402

from core.config import settings  # noqa: E402
from lower_bound_timing import load_layout  # noqa: E402
from solvers.common.utilities.convs import tile_str_to_tuple  # noqa: E402
from solvers.cplex_medicine.models import CplexExperimentModel, CplexOrder  # noqa: E402
from solvers.cplex_medicine.utilities.batch_handler import ScheduleCreator  # noqa: E402


def compress(schedule, path_optimizer) -> int:
    """Earliest start times over the per-mover (with travel) and per-tile sequences; returns the makespan."""
    schedule = schedule.sort_values("Start").reset_index(drop=True)
    start = [0] * len(schedule)
    last_by_mover, last_by_tile = {}, {}
    distance_cache = {}
    for i, task in schedule.iterrows():
        earliest = 0
        prev = last_by_mover.get(task["Mover"])
        if prev is not None:
            key = (schedule.at[prev, "Tile"], task["Tile"])
            if key not in distance_cache:
                path = path_optimizer.find_shortest_path(tile_str_to_tuple(key[0]), tile_str_to_tuple(key[1]))
                distance_cache[key] = len(path) - 1
            earliest = max(earliest, start[prev] + int(schedule.at[prev, "Length"]) + distance_cache[key])
        prev = last_by_tile.get(task["Tile"])
        if prev is not None:
            earliest = max(earliest, start[prev] + int(schedule.at[prev, "Length"]))
        start[i] = earliest
        last_by_mover[task["Mover"]] = i
        last_by_tile[task["Tile"]] = i
    return max(start[i] + int(schedule.at[i, "Length"]) for i in range(len(schedule)))


def main():
    parser = argparse.ArgumentParser(description="Run the CP scheduler for one instance and time budget.")
    parser.add_argument("--layout", required=True, help="Layout JSON file")
    parser.add_argument("--orders", required=True, help="Order-list JSON file")
    parser.add_argument("--num-orders", type=int, required=True, help="Use the first N orders of the file")
    parser.add_argument("--movers", type=int, required=True)
    parser.add_argument("--batch-size", type=int, required=True)
    parser.add_argument("--time-budget", type=int, required=True, help="Total CP time in seconds over all batches")
    parser.add_argument("--seed", type=int, default=None, help="CP random seed")
    parser.add_argument("--dispensing-time", type=int, default=10)
    parser.add_argument("--interface-time", type=int, default=3)
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()

    context.solver.local.execfile = settings.CPLEX_PATH if platform.processor() != "arm" else settings.ARM64_PATH

    layout_name, layout, path_optimizer = load_layout(args.layout)
    with open(args.orders, encoding="utf-8") as f:
        orders = json.load(f)["orders"]
    if args.num_orders > len(orders):
        raise ValueError(f"{args.orders} has only {len(orders)} orders")
    orders = orders[:args.num_orders]

    n_batches = math.ceil(len(orders) / args.batch_size)
    per_batch_limit = max(1, round(args.time_budget / n_batches))
    data = CplexExperimentModel(
        orders=[CplexOrder(order_id=i, drug_names=[item["name"] for item in order["items"]],
                           dosages=[int(item["quantity"]) for item in order["items"]])
                for i, order in enumerate(orders)],
        mover_amount=args.movers, time_limit=per_batch_limit, dispensing_time=args.dispensing_time,
        batch_size=args.batch_size, process_amount=1, warmup=False, interface_time=args.interface_time,
        layout=layout, random_seed=args.seed,
    )

    started = time.perf_counter()
    creator = ScheduleCreator(data, compute_lower_bound=False)
    try:
        batches = creator.run_multiple_batches(batch_size=args.batch_size)
    except KeyError:
        # A batch without any solution yields an empty schedule (no 'Start' column)
        batches = []
    merged = creator.merge_schedules([batch.tasks for batch in batches]) if batches else []
    wall_time = time.perf_counter() - started

    result = {
        "layout": layout_name,
        "orders_file": os.path.basename(args.orders),
        "num_orders": len(orders),
        "movers": args.movers,
        "batch_size": args.batch_size,
        "num_batches": n_batches,
        "time_budget_s": args.time_budget,
        "per_batch_time_limit_s": per_batch_limit,
        "seed": args.seed,
        "dispensing_time": args.dispensing_time,
        "interface_time": args.interface_time,
        "feasible": len(merged) > 0,
        "cp_cmax": int(merged["Finish"].max()) if len(merged) > 0 else None,
        "compressed_cmax": compress(merged, path_optimizer) if len(merged) > 0 else None,
        "batch_status": [batch.metrics.get("solve_status") for batch in batches],
        "batch_cmax": [int(batch.tasks["Finish"].max()) if len(batch.tasks) > 0 else None for batch in batches],
        "batch_progress": [batch.metrics.get("progress", []) for batch in batches],
        "wall_time_s": round(wall_time, 2),
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f)
    print(json.dumps({k: v for k, v in result.items() if k != "batch_progress"}))


if __name__ == "__main__":
    main()
