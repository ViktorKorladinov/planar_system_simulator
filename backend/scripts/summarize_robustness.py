"""
Summarize the robustness runs (batch 15: reference set + 99 validation sets, batch 16: extra CP seeds on the
reference set) into CSVs for the robustness figure.

For each mover count:
  - deviation of every validation set (seed 1) from the reference makespan, in percent; the reference makespan is
    the mean over all CP seeds on the reference set (seed 1 from batch 15 plus the seeds of batch 16), so solver
    noise of a single reference run does not shift all deviations;
  - deviation of every reference-set seed run from that mean, in percent;
  - for every run, the gap of the makespan to the lower bound of the same order set, (metric - LB) / metric in
    percent. The lower bound depends only on the order set, so this gap compares the layout across order sets
    with different amounts of work.

Usage:
    python summarize_robustness.py --runs data/results/robust_batch15_16_db.csv \
        --reference orders_set1 --metric routed_cmax --out ../../xplanar/experiments/robustness_v2

The input CSV is exported from the database of the experiment server with scripts/robustness_runs.sql:
    docker exec -i planar_db sh -c 'psql -U $POSTGRES_USER -d $POSTGRES_DB' < robustness_runs.sql > robust_batch15_16_db.csv
"""
import argparse
import csv
import os
import statistics
from collections import defaultdict


def read(path):
    with open(path) as f:
        return [r for r in csv.DictReader(f) if r.get("status", "").lower() == "finished"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", required=True, help="CSV with batch_id, order_list_name, mover_amount, ...")
    parser.add_argument("--base-batch", default="15")
    parser.add_argument("--seed-batch", default="16")
    parser.add_argument("--reference", default="orders_set1", help="Order list name of the reference set")
    parser.add_argument("--metric", default="routed_cmax")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    runs = read(args.runs)
    base = [r for r in runs if r["batch_id"] == args.base_batch]
    seeds = [r for r in runs if r["batch_id"] == args.seed_batch]
    os.makedirs(args.out, exist_ok=True)

    by_movers = defaultdict(list)
    for r in base:
        by_movers[int(r["mover_amount"])].append(r)
    seed_runs = defaultdict(list)
    for r in seeds:
        seed_runs[int(r["mover_amount"])].append(r)

    for m in sorted(by_movers):
        rows = by_movers[m]
        ref = [r for r in rows if args.reference in r["order_list_name"]]
        val = [r for r in rows if args.reference not in r["order_list_name"]]
        assert len(ref) == 1, f"{m} movers: expected one reference run, found {len(ref)}"
        reps = ref + [r for r in seed_runs[m] if args.reference in r["order_list_name"]]
        vals = [float(r[args.metric]) for r in reps]
        ref_c = statistics.mean(vals)
        dev = [100 * (float(r[args.metric]) - ref_c) / ref_c for r in val]
        gap = lambda r: 100 * (float(r[args.metric]) - float(r["lower_bound_cmax"])) / float(r[args.metric])
        with open(os.path.join(args.out, f"validation_m{m}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["order_list", args.metric, "deviation_pct", "lower_bound", "lb_gap_pct"])
            for r, d in zip(val, dev):
                w.writerow([r["order_list_name"], r[args.metric], round(d, 3), r["lower_bound_cmax"], round(gap(r), 3)])

        mean = ref_c
        sdev = [100 * (v - mean) / mean for v in vals]
        with open(os.path.join(args.out, f"seeds_m{m}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["random_seed", args.metric, "deviation_pct", "lower_bound", "lb_gap_pct"])
            for r, d in zip(reps, sdev):
                w.writerow([r["random_seed"], r[args.metric], round(d, 3), r["lower_bound_cmax"], round(gap(r), 3)])

        print(f"{m} movers: reference (seed mean) {ref_c:.0f}; {len(val)} validation sets: "
              f"mean dev {statistics.mean(dev):+.2f}%, min {min(dev):+.2f}%, max {max(dev):+.2f}%, "
              f"|dev|<=10%: {sum(abs(d) <= 10 for d in dev)}/{len(dev)}; "
              f"{len(vals)} seeds on reference: mean {mean:.0f}, range {min(sdev):+.2f}%..{max(sdev):+.2f}%, "
              f"CV {100 * statistics.stdev(vals) / mean:.2f}%")
        gv, gr = [gap(r) for r in val], [gap(r) for r in reps]
        ref_gap = statistics.mean(gr)
        print(f"   LB gap: reference (seed mean) {ref_gap:.2f}%; validation mean {statistics.mean(gv):.2f}%, "
              f"min {min(gv):.2f}%, max {max(gv):.2f}%, within 5 points of the reference: "
              f"{sum(abs(g - ref_gap) <= 5 for g in gv)}/{len(gv)}")


if __name__ == "__main__":
    main()
