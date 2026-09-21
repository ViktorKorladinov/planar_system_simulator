#!/usr/bin/env python3
"""
Export experiment results from the planar system simulator to a clean CSV.

Can be run locally against a remote/local backend API (e.g. on the vortex server),
or run directly on the server against Postgres or the API.

Usage:
    python export_experiment_results.py --api-url http://localhost:8000 --output results.csv
    python export_experiment_results.py --batch-id 1 --output batch_1_results.csv
"""

import argparse
import csv
import json
import os
import sys
from typing import List, Dict, Any, Optional
import requests


def fetch_experiments_from_api(api_url: str, batch_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Fetch finished experiments and their simulation metrics via REST API."""
    page = 1
    size = 100
    all_experiments = []

    print(f"Fetching experiments from {api_url}...")
    while True:
        params = {"page": page, "size": size, "statuses": ["finished"]}
        if batch_id is not None:
            params["batch_id"] = batch_id

        try:
            resp = requests.get(f"{api_url}/api/v1/experiments/", params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

        experiments = data.get("experiments", [])
        if not experiments:
            break

        for exp in experiments:
            exp_id = exp["id"]
            # Fetch detailed simulation metrics
            try:
                sim_resp = requests.get(f"{api_url}/api/v1/simulations/{exp_id}", timeout=30)
                if sim_resp.status_code == 200:
                    sim_data = sim_resp.json()
                    exp["metrics"] = sim_data.get("metrics") or {}
                else:
                    exp["metrics"] = {}
            except Exception as e:
                print(f"Warning: could not fetch simulation details for experiment {exp_id}: {e}")
                exp["metrics"] = {}

            all_experiments.append(exp)

        if page >= data.get("total", 1):
            break
        page += 1

    return all_experiments


def flatten_experiment(exp: Dict[str, Any]) -> Dict[str, Any]:
    """Flattens experiment summary and simulation metrics into a single row."""
    m = exp.get("metrics") or {}

    # Core routing overheads: prefer detailed metrics if present, else fallback to summary
    scheduled_cmax = m.get("scheduled_cmax", exp.get("scheduled_cmax"))
    routed_cmax = m.get("routed_cmax", exp.get("routed_cmax"))
    routing_overhead_abs = m.get("routing_overhead_abs", exp.get("routing_overhead_abs"))
    routing_overhead_pct = m.get("routing_overhead_pct", exp.get("routing_overhead_pct"))
    routing_iterations = m.get("routing_iterations", exp.get("routing_iterations"))
    total_time_s = m.get("total_time_s", exp.get("total_time_s"))

    interruption_history = m.get("iterations_interruption_history")
    if isinstance(interruption_history, list):
        interruption_history_str = json.dumps(interruption_history)
    else:
        interruption_history_str = ""

    mover_busy_times = m.get("mover_busy_time_per_mover")
    if isinstance(mover_busy_times, dict):
        mover_busy_str = json.dumps(mover_busy_times)
    else:
        mover_busy_str = ""

    return {
        # Identifiers
        "experiment_id": exp.get("id"),
        "experiment_name": exp.get("name"),
        "batch_id": exp.get("batch_id"),
        "batch_name": exp.get("batch_name"),
        "status": exp.get("status"),
        "created_at": exp.get("created_at"),
        "finished_at": exp.get("finished_at"),

        # Layout & Configuration Parameters
        "layout_id": exp.get("layout_id"),
        "layout_name": exp.get("layout_name"),
        "layout_type": exp.get("layout_type"),
        "tile_amount": exp.get("tile_amount"),
        "interface_amount": exp.get("interface_amount"),
        "dispenser_amount": exp.get("dispenser_amount"),
        "solver_type": exp.get("solver_type"),
        "mover_amount": exp.get("mover_amount"),
        "dispensing_time": exp.get("dispensing_time"),
        "interface_time": exp.get("interface_time"),
        "batch_size": exp.get("batch_size"),
        "warmup": exp.get("warmup"),
        "time_limit": exp.get("time_limit"),
        "order_amount": exp.get("order_amount"),

        # Scheduled vs Routed C_max & Overheads
        "scheduled_cmax": scheduled_cmax,
        "routed_cmax": routed_cmax,
        "routing_overhead_abs": routing_overhead_abs,
        "routing_overhead_pct": routing_overhead_pct,
        "routing_iterations": routing_iterations,

        # Timing Breakdown
        "scheduling_time_s": m.get("scheduling_time_s"),
        "routing_time_s": m.get("routing_time_s"),
        "total_time_s": total_time_s,

        # Interruption & Conflict Diagnostics
        "initial_interruptions": m.get("initial_interruptions"),
        "final_interruptions": m.get("final_interruptions"),
        "iterations_interruption_history": interruption_history_str,

        # CPLEX Solver Metrics
        "cp_solve_status": m.get("cp_solve_status"),
        "best_bound_internal": m.get("best_bound_internal"),
        "internal_gap_pct": m.get("internal_gap_pct"),
        "solver_branches": m.get("solver_branches"),
        "solver_fails": m.get("solver_fails"),
        "solver_choice_points": m.get("solver_choice_points"),
        "warm_start_cmax": m.get("warm_start_cmax"),

        # Operational & Workload Metrics
        "total_transit_time": m.get("total_transit_time"),
        "total_dispensing_time": m.get("total_dispensing_time"),
        "total_wait_time": m.get("total_wait_time"),
        "dispensing_to_travel_ratio": m.get("dispensing_to_travel_ratio"),
        "mover_busy_time_per_mover": mover_busy_str,
        "task_count": m.get("task_count"),
        "batch_count": m.get("batch_count"),
    }


def main():
    parser = argparse.ArgumentParser(description="Export experiment results to CSV for paper analysis.")
    parser.add_argument("--api-url", default=os.getenv("BACKEND_URL", "http://localhost:8000"),
                        help="Backend API base URL (default: http://localhost:8000)")
    parser.add_argument("--batch-id", type=int, default=None,
                        help="Optional batch ID to filter by")
    parser.add_argument("--output", default="experiments_results.csv",
                        help="Output CSV filepath (default: experiments_results.csv)")
    args = parser.parse_args()

    experiments = fetch_experiments_from_api(api_url=args.api_url, batch_id=args.batch_id)
    print(f"Retrieved {len(experiments)} completed experiment(s).")

    if not experiments:
        print("No experiments found. Exiting.")
        return

    rows = [flatten_experiment(exp) for exp in experiments]
    fieldnames = list(rows[0].keys())

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully exported {len(rows)} records to: {args.output}")


if __name__ == "__main__":
    main()
