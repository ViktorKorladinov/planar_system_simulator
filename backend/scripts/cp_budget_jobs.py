#!/usr/bin/env python3
"""
Writes the job list for the time-limit and batching experiments (one line of run_cp_budget.py arguments per run).

Time-limit experiment: unbatched runs (batch size = number of orders) for 10-500 orders.
Batching experiment: batched runs for 100-500 orders; its unbatched curves are the time-limit runs.
Every curve is evaluated at each time budget, on each order set, with 8 movers on the 64-tile square layout.
Jobs are sorted by budget (longest first) to balance parallel execution.

With --warm, every run is warm-started from a cached P||Cmax assignment per batch; --warm-jobs writes the
job list that fills these caches (run it with at most 2 parallel jobs: it uses Gurobi). With --parallel-batches,
only the batched curves are written and every batch gets the full time budget.

Usage:
    python cp_budget_jobs.py --output data/results/cp_budget/jobs.txt
    python cp_budget_jobs.py --warm --results-dir data/results/cp_budget_warm \
        --output data/results/cp_budget_warm/jobs.txt --warm-jobs data/results/cp_budget_warm/warm_jobs.txt
    python cp_budget_jobs.py --warm --parallel-batches --budgets 50 100 300 500 1000 \
        --results-dir data/results/cp_budget_warm_parallel --warm-cache-dir data/results/cp_budget_warm/warm_cache \
        --output data/results/cp_budget_warm_parallel/jobs.txt
"""

import argparse
import os

LAYOUT = "data/layouts/square64.json"
ORDER_SETS = ["data/order_sets/large_set1.json", "data/order_sets/large_set2.json", "data/order_sets/large_set3.json"]
BUDGETS = [50, 100, 300, 500, 1000, 2000]
MOVERS = 8
SEED = 1
TIME_LIMIT_SIZES = [10, 20, 50, 100, 200, 300, 500]
BATCH_SIZES = {100: [50], 200: [50, 100], 300: [50, 100], 500: [50, 100]}


def main():
    parser = argparse.ArgumentParser(description="Write the job list for the time-limit and batching experiments.")
    parser.add_argument("--output", required=True, help="Job list file")
    parser.add_argument("--results-dir", default="data/results/cp_budget", help="Directory for result JSON files")
    parser.add_argument("--budgets", type=int, nargs="*", default=BUDGETS)
    parser.add_argument("--warm", action="store_true", help="Warm-start every run from the cache")
    parser.add_argument("--warm-cache-dir", default=None, help="Cache directory (default: RESULTS_DIR/warm_cache)")
    parser.add_argument("--warm-jobs", default=None, help="Also write the job list that fills the warm-start caches")
    parser.add_argument("--parallel-batches", action="store_true", help="Batched curves only, full budget per batch")
    args = parser.parse_args()
    cache_dir = args.warm_cache_dir or f"{args.results_dir}/warm_cache"

    runs = [(n, n) for n in TIME_LIMIT_SIZES] + [(n, b) for n, sizes in BATCH_SIZES.items() for b in sizes]
    if args.parallel_batches:
        runs = [(n, b) for n, b in runs if b < n]
    jobs, warm_jobs = [], set()
    for budget in args.budgets:
        for orders_path in ORDER_SETS:
            set_name = os.path.basename(orders_path).replace(".json", "")
            for num_orders, batch_size in runs:
                output = f"{args.results_dir}/{set_name}_n{num_orders}_b{batch_size}_t{budget}_m{MOVERS}_s{SEED}.json"
                instance = (f"--layout {LAYOUT} --orders {orders_path} --num-orders {num_orders} "
                            f"--movers {MOVERS} --batch-size {batch_size}")
                extra = " --parallel-batches" if args.parallel_batches else ""
                if args.warm:
                    cache = f"{cache_dir}/{set_name}_n{num_orders}_b{batch_size}_m{MOVERS}.json"
                    extra += f" --warm-cache {cache} --require-cache"
                    warm_jobs.add(f"{instance} --time-budget 1 --warm-cache {cache} --warm-only")
                jobs.append((budget, f"{instance} --time-budget {budget} --seed {SEED}{extra} --output {output}"))
    jobs.sort(key=lambda job: -job[0])

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(job for _, job in jobs) + "\n")
    print(f"Wrote {len(jobs)} jobs to {args.output}")
    if args.warm_jobs:
        with open(args.warm_jobs, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(warm_jobs)) + "\n")
        print(f"Wrote {len(warm_jobs)} warm-start jobs to {args.warm_jobs}")


if __name__ == "__main__":
    main()
