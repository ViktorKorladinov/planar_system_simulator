#!/usr/bin/env python3
"""
Automated Experiment Matrix Runner for Planar System Simulator.

Creates and enqueues experiment matrices according to the paper specification:
- Phase 3.1: Router Overhead & Congestion Matrix (movers [1, 4, 8, 12] x speeds [10, 1] x topologies x 5 seeds)
- Phase 2.1: CP Time-Limit & Scalability Study (order counts [10, 25, 50, 99] x 8 movers x 5 seeds)
- Phase 2.2: Lower Bound Grid (order counts [25, 50, 99] x movers [2, 6, 10, 12] x 5 seeds)
- Phase 4.1: DAG-Based Batching Study (99 orders x batch sizes [None, 25, 50] x 8 movers x 5 seeds)
- Quick-Test: Fast smoke test (1 run, 10 orders, 10s budget)

Usage:
    # Quick test (verify setup in ~10 seconds):
    python run_experiments.py --mode quick-test

    # Router Overhead study (single topology or all topologies):
    python run_experiments.py --mode overhead --topology square --time-limit 600
    python run_experiments.py --mode overhead --topology all --time-limit 600

    # Scalability study:
    python run_experiments.py --mode scalability

    # Batching study:
    python run_experiments.py --mode batching

    # Lower bound grid:
    python run_experiments.py --mode lowerbound

    # Dry run (validates API payload without queueing):
    python run_experiments.py --mode overhead --dry-run
"""

import argparse
import copy
import json
import os
import random
import sys
import time
from typing import List, Dict, Any, Optional
import requests


TOPOLOGY_MAP = {
    "square": ("square", "data/layouts/square64.json"),
    "doubleline": ("double_line", "data/layouts/doubleline64.json"),
    "double_line": ("double_line", "data/layouts/doubleline64.json"),
    "line": ("line", "data/layouts/line64.json"),
    "ring": ("ring", "data/layouts/ring64.json"),
}


def resolve_file_path(path: str) -> str:
    """Finds existing file path across current working dir, repo root, and Docker container."""
    if os.path.exists(path):
        return path
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", path),
        os.path.join(os.path.dirname(__file__), "..", "..", path),
        os.path.join("/app", path),
        os.path.join("/app", "data", os.path.basename(path)),
        os.path.join("/app", "data", "layouts", os.path.basename(path)),
        os.path.join(os.path.dirname(__file__), "..", "data", os.path.basename(path)),
        os.path.join(os.path.dirname(__file__), "..", "data", "layouts", os.path.basename(path)),
        os.path.join("data", os.path.basename(path)),
        os.path.join("data", "layouts", os.path.basename(path)),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return path


def parse_layout_file(filepath: str, topology_type: str) -> Dict[str, Any]:
    """Parses a layout JSON file into a LayoutDTO payload for the backend API."""
    resolved = resolve_file_path(filepath)
    with open(resolved, "r", encoding="utf-8") as f:
        data = json.load(f)

    placement = data.get("placement", [])
    layout_meta = data.get("layout", {})
    n_rows = layout_meta.get("n", len(placement))
    m_cols = layout_meta.get("m", len(placement[0]) if placement else 0)
    unavailable_locs = {tuple(loc) for loc in layout_meta.get("unavailable_locations", [])}

    tiles = []
    drugs_collected = set()

    for y in range(n_rows):
        for x in range(m_cols):
            val = placement[y][x] if y < len(placement) and x < len(placement[y]) else "empty"
            if val == "interface":
                tiles.append({"type": "interface", "x": x, "y": y, "dispensed_types": None})
            elif val == "blocked" or (y, x) in unavailable_locs:
                tiles.append({"type": "blocked", "x": x, "y": y, "dispensed_types": None})
            elif val == "empty":
                tiles.append({"type": "empty", "x": x, "y": y, "dispensed_types": None})
            else:
                drug_names = [d.strip() for d in val.split(",") if d.strip()]
                for d in drug_names:
                    drugs_collected.add(d)
                tiles.append({"type": "dispenser", "x": x, "y": y, "dispensed_types": drug_names})

    sorted_drugs = sorted(list(drugs_collected))
    basename = os.path.basename(filepath).replace(".json", "")
    layout_name = f"Paper_{basename.upper()}"
    ingredient_list = {
        "name": f"Ingredients_{layout_name}",
        "type": "medicine",
        "ingredients": [
            {
                "name": drug,
                "note_type": None,
                "viscosity": None,
                "volatility_rank": None
            }
            for drug in sorted_drugs
        ]
    }

    return {
        "name": layout_name,
        "type": topology_type,
        "tiles": tiles,
        "ingredient_list": ingredient_list,
        "ingredient_list_id": None
    }


def ensure_layouts(api_url: str, topology: str) -> List[int]:
    """Finds or creates layout(s) for the requested topology."""
    if topology == "all":
        selected = [("square", TOPOLOGY_MAP["square"]),
                    ("double_line", TOPOLOGY_MAP["double_line"]),
                    ("line", TOPOLOGY_MAP["line"]),
                    ("ring", TOPOLOGY_MAP["ring"])]
    else:
        top_key = topology.lower()
        if top_key not in TOPOLOGY_MAP:
            raise ValueError(f"Unknown topology '{topology}'. Choose from: {list(TOPOLOGY_MAP.keys())} or 'all'")
        selected = [(top_key, TOPOLOGY_MAP[top_key])]

    existing_layouts_by_name = {}
    try:
        resp = requests.get(f"{api_url}/api/v1/layouts/", params={"size": 100}, timeout=15)
        if resp.status_code == 200:
            for lay in resp.json().get("layouts", []):
                if lay.get("dispenser_amount", 0) > 0:
                    existing_layouts_by_name[lay.get("name")] = lay["id"]
    except Exception as e:
        print(f"Warning checking layouts: {e}")

    layout_ids = []
    for _, (top_type, filepath) in selected:
        basename = os.path.basename(filepath).replace(".json", "")
        expected_name = f"Paper_{basename.upper()}"

        if expected_name in existing_layouts_by_name:
            lay_id = existing_layouts_by_name[expected_name]
            print(f"Using existing valid layout ID {lay_id} for '{expected_name}'")
            layout_ids.append(lay_id)
            continue

        resolved_path = resolve_file_path(filepath)
        if not os.path.exists(resolved_path):
            print(f"Warning: Layout file '{filepath}' (resolved '{resolved_path}') not found, skipping {top_type}")
            continue

        payload = parse_layout_file(resolved_path, top_type)
        resp = requests.post(f"{api_url}/api/v1/layouts/", json=payload, timeout=30)
        if resp.status_code in [200, 201]:
            lay_id = resp.json()["id"]
            print(f"Created new layout ID {lay_id} for '{expected_name}' ({top_type}) with {len(payload['tiles'])} tiles")
            layout_ids.append(lay_id)
        else:
            print(f"Error creating layout for {top_type}: {resp.status_code} {resp.text}")

    if not layout_ids:
        raise RuntimeError("No valid layouts could be loaded or created!")
    return layout_ids


def create_order_lists(api_url: str, order_file: str, seeds_count: int = 5,
                       subsets: Optional[List[int]] = None) -> List[int]:
    """Generates order sets with different seeds or subsets and uploads them."""
    resolved = resolve_file_path(order_file)
    with open(resolved, "r", encoding="utf-8") as f:
        data = json.load(f)

    base_orders = data.get("orders", [])
    order_list_ids = []

    # Check already registered order lists
    existing_map = {}
    try:
        resp = requests.get(f"{api_url}/api/v1/order_lists/", params={"size": 100}, timeout=15)
        if resp.status_code == 200:
            for ol in resp.json().get("order_lists", []):
                existing_map[ol["name"]] = ol["id"]
    except Exception:
        pass

    if subsets:
        for count in subsets:
            for seed in range(1, seeds_count + 1):
                name = f"Orders_N{count}_Seed{seed}"
                if name in existing_map:
                    order_list_ids.append(existing_map[name])
                    continue

                rng = random.Random(seed * 1000 + count)
                sampled = rng.sample(base_orders, min(count, len(base_orders)))
                payload = {"name": name, "type": "medicine", "orders": sampled}
                resp = requests.post(f"{api_url}/api/v1/order_lists/", json=payload, timeout=30)
                if resp.status_code in [200, 201]:
                    ol_id = resp.json()["id"]
                    order_list_ids.append(ol_id)
                    print(f"Created OrderList ID: {ol_id} ('{name}')")
                else:
                    raise RuntimeError(f"Failed to create order list: {resp.text}")
    else:
        for seed in range(1, seeds_count + 1):
            name = f"Orders_Full_Seed{seed}"
            if name in existing_map:
                order_list_ids.append(existing_map[name])
                continue

            rng = random.Random(seed * 42)
            shuffled = copy.deepcopy(base_orders)
            rng.shuffle(shuffled)
            payload = {"name": name, "type": "medicine", "orders": shuffled}
            resp = requests.post(f"{api_url}/api/v1/order_lists/", json=payload, timeout=30)
            if resp.status_code in [200, 201]:
                ol_id = resp.json()["id"]
                order_list_ids.append(ol_id)
                print(f"Created OrderList ID: {ol_id} ('{name}')")
            else:
                raise RuntimeError(f"Failed to create order list: {resp.text}")

    return order_list_ids


def build_configurations(mode: str, time_limit: int) -> List[Dict[str, Any]]:
    """Builds the list of ConfigurationDTOs for the chosen study mode."""
    configs = []

    if mode == "quick-test":
        configs.append({
            "name": "Quick_M2_T10_Speed10",
            "solver_type": "cplex_medicine",
            "mover_amount": 2,
            "dispensing_time": 10,
            "interface_time": 3,
            "time_limit": min(time_limit, 10),
            "batch_size": 100,
            "process_amount": 1,
            "warmup": False
        })
    elif mode == "overhead":
        for mover_count in [1, 4, 8, 12]:
            for dispensing_time in [10, 1]:  # standard=10, fast=1
                for warmup in [False, True]:
                    speed_label = "std" if dispensing_time == 10 else "fast"
                    warm_label = "warm" if warmup else "cold"
                    configs.append({
                        "name": f"Overhead_M{mover_count}_{speed_label}_{warm_label}",
                        "solver_type": "cplex_medicine",
                        "mover_amount": mover_count,
                        "dispensing_time": dispensing_time,
                        "interface_time": 3,
                        "time_limit": time_limit,
                        "batch_size": 100,
                        "process_amount": 1,
                        "warmup": warmup
                    })
    elif mode == "batching":
        for batch_size in [100, 25, 50]:
            bs_label = f"B{batch_size}" if batch_size != 100 else "unbatched"
            configs.append({
                "name": f"Batching_M8_{bs_label}",
                "solver_type": "cplex_medicine",
                "mover_amount": 8,
                "dispensing_time": 10,
                "interface_time": 3,
                "time_limit": time_limit,
                "batch_size": batch_size,
                "process_amount": 1,
                "warmup": False
            })
    elif mode == "scalability":
        configs.append({
            "name": "Scalability_M8_std",
            "solver_type": "cplex_medicine",
            "mover_amount": 8,
            "dispensing_time": 10,
            "interface_time": 3,
            "time_limit": time_limit,
            "batch_size": 100,
            "process_amount": 1,
            "warmup": False
        })
    elif mode == "lowerbound":
        for mover_count in [2, 6, 10, 12]:
            configs.append({
                "name": f"LowerBound_M{mover_count}",
                "solver_type": "cplex_medicine",
                "mover_amount": mover_count,
                "dispensing_time": 10,
                "interface_time": 3,
                "time_limit": time_limit,
                "batch_size": 100,
                "process_amount": 1,
                "warmup": True
            })
    elif mode == "all":
        configs.extend(build_configurations("overhead", time_limit))
        configs.extend(build_configurations("batching", time_limit))

    return configs


def monitor_batch(api_url: str, batch_id: int, poll_interval: int = 10) -> None:
    """Monitors batch execution until all experiments finish."""
    print(f"\nMonitoring Batch ID {batch_id}...")
    start_time = time.time()

    while True:
        try:
            resp = requests.get(f"{api_url}/api/v1/experiments/batch/{batch_id}", timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                experiments = data.get("experiments", [])
                total = len(experiments)
                finished = sum(1 for e in experiments if e.get("status") == "finished")
                failed = sum(1 for e in experiments if e.get("status") == "failed")
                running = sum(1 for e in experiments if e.get("status") == "running")
                queued = sum(1 for e in experiments if e.get("status") == "queued")

                elapsed = int(time.time() - start_time)
                progress = f"[{finished + failed}/{total}] Finished: {finished}, Failed: {failed}, Running: {running}, Queued: {queued} (Elapsed: {elapsed}s)"
                print(f"\r{progress}", end="", flush=True)

                if finished + failed >= total and total > 0:
                    print(f"\nBatch {batch_id} complete! Finished: {finished}, Failed: {failed}.")
                    break
        except Exception as e:
            print(f"\nError checking batch status: {e}")

        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description="Run experiment matrix for Planar System Simulator.")
    parser.add_argument("--mode", choices=["quick-test", "overhead", "scalability", "batching", "lowerbound", "all"],
                        default="quick-test", help="Study to run (default: quick-test)")
    parser.add_argument("--topology", default="square",
                        help="Topology to evaluate: 'square', 'doubleline', 'line', 'ring', or 'all' (default: square)")
    parser.add_argument("--api-url", default=os.getenv("BACKEND_URL", "http://localhost:8000"),
                        help="Backend API URL (default: http://localhost:8000)")
    parser.add_argument("--time-limit", type=int, default=600,
                        help="CP solver time limit in seconds (default: 600)")
    parser.add_argument("--seeds", type=int, default=5,
                        help="Number of independent order set replications (default: 5)")
    parser.add_argument("--order-file", default="orders.json",
                        help="Path to base orders JSON file (default: orders.json)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate matrix with API without queueing")
    parser.add_argument("--no-wait", action="store_true",
                        help="Do not wait for batch to complete")
    parser.add_argument("--output", default=None,
                        help="CSV file path to automatically export results after completion")
    args = parser.parse_args()

    print("=" * 65)
    print(f"Planar Experiment Runner | Mode: '{args.mode}' | Topology: '{args.topology}'")
    print(f"API URL: {args.api_url} | Time limit: {args.time_limit}s | Replications: {args.seeds}")
    print("=" * 65)

    # 1. Ensure Layout(s)
    layout_ids = ensure_layouts(args.api_url, args.topology)

    # 2. Ensure Order Lists
    if args.mode == "quick-test":
        order_list_ids = create_order_lists(args.api_url, args.order_file, seeds_count=1, subsets=[10])
    elif args.mode in ["scalability", "lowerbound"]:
        subsets = [10, 25, 50, 99] if args.mode == "scalability" else [25, 50, 99]
        order_list_ids = create_order_lists(args.api_url, args.order_file, seeds_count=args.seeds, subsets=subsets)
    else:
        order_list_ids = create_order_lists(args.api_url, args.order_file, seeds_count=args.seeds)

    # 3. Build Configurations
    configurations = build_configurations(args.mode, args.time_limit)

    matrix_size = len(layout_ids) * len(configurations) * len(order_list_ids)
    print(f"\nMatrix plan: {len(layout_ids)} layout(s) x {len(configurations)} config(s) x {len(order_list_ids)} order set(s) = {matrix_size} experiment run(s).")

    # 4. Enqueue Matrix via POST /api/v1/experiments/batch/matrix
    matrix_payload = {
        "name": f"Matrix_{args.mode.upper()}",
        "layout_ids": layout_ids,
        "layouts": None,
        "configuration_ids": None,
        "configurations": configurations,
        "order_list_ids": order_list_ids,
        "order_lists": None
    }

    url = f"{args.api_url}/api/v1/experiments/batch/matrix"
    params = {"dry_run": args.dry_run}

    print("Submitting matrix to backend...")
    resp = requests.post(url, json=matrix_payload, params=params, timeout=60)
    if resp.status_code not in [200, 201]:
        print(f"Error submitting matrix: {resp.status_code} {resp.text}")
        sys.exit(1)

    result_data = resp.json()
    batch_id = result_data.get("id")
    created_amount = result_data.get("created_amount", matrix_size)
    print(f"Successfully created matrix batch! Batch ID: {batch_id}, Experiments: {created_amount}")

    if args.dry_run:
        print("Dry run complete. No experiments were enqueued.")
        return

    # 5. Monitor progress if requested
    if not args.no_wait and batch_id:
        monitor_batch(args.api_url, batch_id)

        # 6. Export results
        if args.output:
            output_csv = args.output
        elif os.path.exists("/app/data/plots"):
            output_csv = f"/app/data/plots/{args.mode}_results.csv"
        else:
            output_csv = f"{args.mode}_results.csv"

        print(f"\nExporting results to {output_csv}...")
        export_cmd = f"python {os.path.join(os.path.dirname(__file__), 'export_experiment_results.py')} --api-url {args.api_url} --batch-id {batch_id} --output {output_csv}"
        os.system(export_cmd)


if __name__ == "__main__":
    main()
