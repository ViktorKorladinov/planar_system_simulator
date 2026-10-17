#!/usr/bin/env python3
"""
Runs the CP scheduling model (without lower bound or routing) for one instance and one total time budget, and
writes the result as JSON. Used for the time-limit and batching experiments.

The orders are split into consecutive batches of --batch-size (one batch if --batch-size >= number of orders);
the total budget is split evenly over the batches. With --parallel-batches, every batch gets the full budget
instead, which is the wall-clock time when the independent batches run in parallel on separate cores.

With --warm-cache, the CP model of every batch is warm-started with the order-to-mover assignment of the
P||Cmax model over the orders of that batch (the same warm start as in the routing matrix). The warm start does
not depend on the time budget, so it is computed once per batch and stored in the cache file; runs with
--require-cache never call Gurobi and can run in parallel, and --warm-only only fills the cache. The time spent
on the warm start is stored in the cache and reported as warm_time_s. The merged schedule is compressed exactly like the routing
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
from solvers.common.utilities.path_optimizer import PathOptimizer  # noqa: E402
from solvers.cplex_medicine.utilities.batch_handler import ScheduleCreator  # noqa: E402


class WarmCacheScheduleCreator(ScheduleCreator):
    """ScheduleCreator whose warm start uses only the orders of the current batch and is cached on disk."""

    def __init__(self, data, cache_path, require_cache=False):
        super().__init__(data, compute_lower_bound=False)
        self.cache_path = cache_path
        self.require_cache = require_cache
        self.cache = {}
        if os.path.exists(cache_path):
            with open(cache_path, encoding="utf-8") as f:
                self.cache = json.load(f)
        self.batch_index = 0
        self.batch_offset = 0

    def run_multiple_batches(self, batch_size=None):
        batch_size = batch_size or len(self.patients_df)
        results = []
        for k, i in enumerate(range(0, len(self.patients_df), batch_size)):
            self.batch_index, self.batch_offset = k, i
            batch_df = self.patients_df.iloc[i:i + batch_size].copy()
            batch_df.reset_index(inplace=True, drop=True)
            results.append(self.run_batch(batch_df))
        return results

    def compute_warm_start(self, n_orders):
        from solvers.cplex_medicine.utilities.lowerbound_heuristic import get_patient_arrangement
        started = time.perf_counter()
        orders = self.data.orders[self.batch_offset:self.batch_offset + n_orders]
        g_model, _, x = get_patient_arrangement(
            path_optimizer=PathOptimizer(self.rows, self.cols, self.filled, self.unavailable_coords),
            data=self.data.model_copy(update={"orders": orders}), time_limit=settings.LOWER_BOUND_TIME_LIMIT)
        assignment = [[j for j in range(n_orders) if x[i, j].x > 0.5] for i in range(self.data.mover_amount)]
        return {"assignment": assignment, "warm_cmax": float(g_model.x[-1]),
                "time_s": round(time.perf_counter() - started, 2)}

    def apply_warmup(self, m, task_wraps, m_range, p_range, path_optimizer):
        key = str(self.batch_index)
        if key not in self.cache:
            if self.require_cache:
                raise RuntimeError(f"warm start of batch {key} missing in {self.cache_path}")
            self.cache[key] = self.compute_warm_start(len(p_range))
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f)
        warmstart = m.create_empty_solution()
        for i, orders in enumerate(self.cache[key]["assignment"]):
            for j in orders:
                warmstart.add_interval_var_solution(task_wraps[i][j], presence=True)
        m.set_starting_point(warmstart)
        return self.cache[key]["warm_cmax"], None

    def warm_time(self):
        return round(sum(v["time_s"] for v in self.cache.values()), 2)


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
    parser.add_argument("--output", default=None, help="Output JSON file (required unless --warm-only)")
    parser.add_argument("--parallel-batches", action="store_true", help="Give every batch the full time budget")
    parser.add_argument("--warm-cache", default=None, help="Warm-start cache file (enables the warm start)")
    parser.add_argument("--require-cache", action="store_true", help="Fail instead of calling Gurobi")
    parser.add_argument("--warm-only", action="store_true", help="Only compute the warm-start cache")
    args = parser.parse_args()
    if args.output is None and not args.warm_only:
        parser.error("--output is required")

    context.solver.local.execfile = settings.CPLEX_PATH if platform.processor() != "arm" else settings.ARM64_PATH

    layout_name, layout, path_optimizer = load_layout(args.layout)
    with open(args.orders, encoding="utf-8") as f:
        orders = json.load(f)["orders"]
    if args.num_orders > len(orders):
        raise ValueError(f"{args.orders} has only {len(orders)} orders")
    orders = orders[:args.num_orders]

    n_batches = math.ceil(len(orders) / args.batch_size)
    per_batch_limit = args.time_budget if args.parallel_batches else max(1, round(args.time_budget / n_batches))
    data = CplexExperimentModel(
        orders=[CplexOrder(order_id=i, drug_names=[item["name"] for item in order["items"]],
                           dosages=[int(item["quantity"]) for item in order["items"]])
                for i, order in enumerate(orders)],
        mover_amount=args.movers, time_limit=per_batch_limit, dispensing_time=args.dispensing_time,
        batch_size=args.batch_size, process_amount=1, warmup=args.warm_cache is not None, interface_time=args.interface_time,
        layout=layout, random_seed=args.seed,
    )

    if args.warm_cache is not None:
        os.makedirs(os.path.dirname(args.warm_cache) or ".", exist_ok=True)
        creator = WarmCacheScheduleCreator(data, args.warm_cache, require_cache=args.require_cache)
    else:
        creator = ScheduleCreator(data, compute_lower_bound=False)
    if args.warm_only:
        for k, i in enumerate(range(0, len(orders), args.batch_size)):
            creator.batch_index, creator.batch_offset = k, i
            if str(k) not in creator.cache:
                creator.cache[str(k)] = creator.compute_warm_start(len(orders[i:i + args.batch_size]))
                with open(args.warm_cache, "w", encoding="utf-8") as f:
                    json.dump(creator.cache, f)
        print(f"warm start cached in {args.warm_cache}: {len(creator.cache)} batches, {creator.warm_time()} s")
        return

    started = time.perf_counter()
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
        "parallel_batches": args.parallel_batches,
        "warm_start": args.warm_cache is not None,
        "warm_time_s": creator.warm_time() if args.warm_cache is not None else None,
        "warm_cmax": [batch.warmup_cmax for batch in batches] if args.warm_cache is not None else None,
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
