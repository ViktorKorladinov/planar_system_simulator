"""
Summarize the scheduling-only time-limit / batching runs (run_cp_budget.py) into CSVs for the paper figures.

For every (number of orders, batch size, time budget), the compressed makespan is aggregated over the order sets
(large_set1-3). A point is written only if every order set produced a feasible schedule; the count of feasible
runs is printed for every configuration.

Usage:
    python summarize_cp_budget.py --results data/results/cp_budget --out ../../xplanar/experiments/cp_budget
"""
import argparse
import csv
import glob
import json
import os
import statistics
from collections import defaultdict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="data/results/cp_budget", help="Folder with run_cp_budget JSONs")
    parser.add_argument("--out", required=True, help="Output folder for the figure CSVs")
    args = parser.parse_args()

    runs = defaultdict(list)
    for path in glob.glob(os.path.join(args.results, "*.json")):
        with open(path) as f:
            d = json.load(f)
        key = (d["num_orders"], d["batch_size"], d["time_budget_s"])
        feasible = d.get("feasible") and d.get("compressed_cmax") is not None
        runs[key].append(d["compressed_cmax"] if feasible else None)

    os.makedirs(args.out, exist_ok=True)
    for n, b in sorted({(k[0], k[1]) for k in runs}):
        rows = []
        for t in sorted(k[2] for k in runs if k[0] == n and k[1] == b):
            vals = runs[(n, b, t)]
            ok = [v for v in vals if v is not None]
            print(f"orders={n:3d} batch={b:3d} budget={t:5d}: feasible {len(ok)}/{len(vals)}"
                  + (f", mean {statistics.mean(ok):.0f}" if ok else ""))
            if ok and len(ok) == len(vals):
                mean = statistics.mean(ok)
                rows.append({"timelimit": t, "Cmax": round(mean, 1), "min": min(ok), "max": max(ok),
                             "errminus": round(mean - min(ok), 1), "errplus": round(max(ok) - mean, 1),
                             "n": len(ok)})
        name = f"orders{n}_batch{b}.csv"
        with open(os.path.join(args.out, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["timelimit", "Cmax", "min", "max", "errminus", "errplus", "n"])
            w.writeheader()
            w.writerows(rows)


if __name__ == "__main__":
    main()
