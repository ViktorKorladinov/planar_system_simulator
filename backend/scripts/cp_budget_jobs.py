#!/usr/bin/env python3
"""
Writes the job list for the time-limit and batching experiments (one line of run_cp_budget.py arguments per run).

Time-limit experiment: unbatched runs (batch size = number of orders) for 10-500 orders.
Batching experiment: batched runs for 100-500 orders; its unbatched curves are the time-limit runs.
Every curve is evaluated at each time budget, on each order set, with 8 movers on the 64-tile square layout.
Jobs are sorted by budget (longest first) to balance parallel execution.

Usage:
    python cp_budget_jobs.py --output data/results/cp_budget/jobs.txt
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
    args = parser.parse_args()

    runs = [(n, n) for n in TIME_LIMIT_SIZES] + [(n, b) for n, sizes in BATCH_SIZES.items() for b in sizes]
    jobs = []
    for budget in BUDGETS:
        for orders_path in ORDER_SETS:
            set_name = os.path.basename(orders_path).replace(".json", "")
            for num_orders, batch_size in runs:
                output = f"{args.results_dir}/{set_name}_n{num_orders}_b{batch_size}_t{budget}_m{MOVERS}_s{SEED}.json"
                jobs.append((budget, f"--layout {LAYOUT} --orders {orders_path} --num-orders {num_orders} "
                                     f"--movers {MOVERS} --batch-size {batch_size} --time-budget {budget} "
                                     f"--seed {SEED} --output {output}"))
    jobs.sort(key=lambda job: -job[0])

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(job for _, job in jobs) + "\n")
    print(f"Wrote {len(jobs)} jobs to {args.output}; total CP time {sum(b for b, _ in jobs) / 3600:.1f} h")


if __name__ == "__main__":
    main()
