#!/usr/bin/env python3
"""
Post-hoc audit of routed mover paths of finished experiments.

Checks two routing rules on the final mover paths stored for each experiment:
- Transit capacity: at most --capacity movers may transit the same tile at the same time step.
- Tile exclusivity: no two movers may be loading on the same tile at the same time step.

In runs made before the initial wait was marked as idle (`e`), each path starts with a block of loading
steps in which the mover waits at its first dispenser before its first operation and then performs it;
this block cannot be split using paths alone. Loading overlaps are therefore reported separately for steps
after each mover's initial block (unambiguous) and for steps involving an initial block.

Usage:
    python audit_routing_paths.py --batch-id 4
    python audit_routing_paths.py --batch-id 4 --output audit_batch_4.csv
"""

import argparse
import collections
import csv
import os
from typing import List, Dict, Any

import requests


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


def initial_block_length(path: List[Dict[str, Any]]) -> int:
    """Returns the number of leading loading steps (initial wait + first operation)."""
    for t, step in enumerate(path):
        if step["mode"] != "loading":
            return t
    return len(path)


def audit_paths(paths: List[List[Dict[str, Any]]], capacity: int) -> Dict[str, int]:
    """Computes transit-capacity and tile-exclusivity statistics for one set of mover paths."""
    horizon = max((len(path) for path in paths), default=0)
    initial_blocks = [initial_block_length(path) for path in paths]

    max_transiting = 0
    over_capacity_ticks = 0
    over_capacity_events = 0
    loading_overlap_ticks = 0
    loading_overlap_ticks_initial = 0
    previously_over_capacity = set()

    for t in range(horizon):
        transiting = collections.Counter()
        loading = collections.defaultdict(list)
        for m, path in enumerate(paths):
            if t >= len(path):
                continue
            pos = (path[t]["x"], path[t]["y"])
            if path[t]["mode"] == "transit":
                transiting[pos] += 1
            elif path[t]["mode"] == "loading":
                loading[pos].append(m)

        if transiting:
            max_transiting = max(max_transiting, max(transiting.values()))
        over_capacity = {pos for pos, count in transiting.items() if count > capacity}
        if over_capacity:
            over_capacity_ticks += 1
        # Count each continuous over-capacity event on a tile once
        over_capacity_events += len(over_capacity - previously_over_capacity)
        previously_over_capacity = over_capacity

        for movers in loading.values():
            if len(movers) < 2:
                continue
            if any(t < initial_blocks[m] for m in movers):
                loading_overlap_ticks_initial += 1
            else:
                loading_overlap_ticks += 1

    return {
        "max_transiting_on_tile": max_transiting,
        "over_capacity_ticks": over_capacity_ticks,
        "over_capacity_events": over_capacity_events,
        "loading_overlap_ticks": loading_overlap_ticks,
        "loading_overlap_ticks_initial_block": loading_overlap_ticks_initial,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit transit capacity and tile exclusivity of routed paths.")
    parser.add_argument("--api-url", default=os.getenv("BACKEND_URL", "http://localhost:8000"),
                        help="Backend API base URL (default: http://localhost:8000)")
    parser.add_argument("--batch-id", type=int, required=True, help="Batch ID to audit")
    parser.add_argument("--capacity", type=int, default=3,
                        help="Maximum number of movers transiting one tile simultaneously (default: 3)")
    parser.add_argument("--output", default=None, help="Optional CSV filepath with per-experiment results")
    args = parser.parse_args()

    experiments = fetch_finished_experiments(args.api_url, args.batch_id)
    print(f"Auditing {len(experiments)} finished experiment(s) of batch {args.batch_id}...")

    rows = []
    for exp in experiments:
        resp = requests.get(f"{args.api_url}/api/v1/simulations/{exp['id']}", timeout=120)
        resp.raise_for_status()
        paths = resp.json()["mover_paths"]["paths"]
        stats = audit_paths(paths, args.capacity)
        rows.append({
            "experiment_id": exp["id"],
            "experiment_name": exp.get("name"),
            "layout_name": exp.get("layout_name"),
            "mover_amount": exp.get("mover_amount"),
            "dispensing_time": exp.get("dispensing_time"),
            "warmup": exp.get("warmup"),
            **stats,
        })

    if not rows:
        print("No experiments found. Exiting.")
        return

    print(f"\nRuns with more than {args.capacity} movers transiting one tile: "
          f"{sum(r['over_capacity_events'] > 0 for r in rows)} / {len(rows)}")
    print(f"Total over-capacity events: {sum(r['over_capacity_events'] for r in rows)}")
    print(f"Maximum movers transiting one tile: {max(r['max_transiting_on_tile'] for r in rows)}")
    print(f"Runs with loading overlap after initial blocks: "
          f"{sum(r['loading_overlap_ticks'] > 0 for r in rows)} / {len(rows)} "
          f"(total ticks: {sum(r['loading_overlap_ticks'] for r in rows)})")
    print(f"Runs with loading overlap involving initial blocks: "
          f"{sum(r['loading_overlap_ticks_initial_block'] > 0 for r in rows)} / {len(rows)} "
          f"(total ticks: {sum(r['loading_overlap_ticks_initial_block'] for r in rows)})")

    print("\nPer configuration (layout, movers, dispensing time): runs, runs over capacity, events, max transiting")
    groups = collections.defaultdict(list)
    for r in rows:
        groups[(r["layout_name"], r["mover_amount"], r["dispensing_time"])].append(r)
    for key in sorted(groups, key=lambda k: (str(k[0]), k[1] or 0, k[2] or 0)):
        g = groups[key]
        print(key, len(g), sum(r["over_capacity_events"] > 0 for r in g),
              sum(r["over_capacity_events"] for r in g), max(r["max_transiting_on_tile"] for r in g))

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nPer-experiment results written to: {args.output}")


if __name__ == "__main__":
    main()
