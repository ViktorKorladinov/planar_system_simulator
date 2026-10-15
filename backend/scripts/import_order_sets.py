#!/usr/bin/env python3
"""
Converts orders produced by the synthetic data generator (diplomka/src/data_generator/main.py) into order sets in
the order-list JSON format used by the backend API.

The input file is semicolon-separated with columns SEQN;drug_names;dosages, where drug_names and dosages are
Python lists; the header line is optional. The orders are cut into consecutive, disjoint sets of --set-size orders
in file order (set k = orders (k-1)*size .. k*size-1).

Usage:
    python import_order_sets.py ../../diplomka/src/data_generator/generated_capsules_with_dosages.csv \
        --set-size 100 --num-sets 5 --output-dir data/order_sets
    python import_order_sets.py data/order_pool/generated_orders_seed2026.csv \
        --set-size 500 --num-sets 3 --prefix large_set --output-dir data/order_sets
    python import_order_sets.py data/order_pool/generated_orders_seed2026.csv \
        --offset 1500 --set-size 100 --num-sets 99 --prefix robust_val_ --digits 2 --output-dir data/order_sets
"""

import argparse
import ast
import json
import os
from typing import List, Dict, Any


def load_generated_orders(path: str) -> List[Dict[str, Any]]:
    """Loads one generator output file into backend order dictionaries."""
    with open(path, encoding="utf-8") as f:
        lines = [line for line in f.read().splitlines() if line.strip()]
    if lines and lines[0].startswith("SEQN"):
        lines = lines[1:]

    orders = []
    for line in lines:
        seqn, drug_names, dosages = line.split(";")
        names = ast.literal_eval(drug_names)
        quantities = ast.literal_eval(dosages)
        if len(names) != len(quantities):
            raise ValueError(f"Order {seqn} in {path} has {len(names)} drugs but {len(quantities)} dosages")
        orders.append({
            "seqn": int(seqn),
            "items": [{"name": name, "quantity": quantity} for name, quantity in zip(names, quantities)],
        })
    return orders


def main():
    parser = argparse.ArgumentParser(description="Convert generated orders to backend order-list JSON sets.")
    parser.add_argument("input", help="Generator output file")
    parser.add_argument("--set-size", type=int, default=100, help="Orders per set (default: 100)")
    parser.add_argument("--num-sets", type=int, required=True, help="Number of sets to create")
    parser.add_argument("--offset", type=int, default=0, help="Index of the first order used (default: 0)")
    parser.add_argument("--prefix", default="orders_set", help="Set name prefix (default: orders_set)")
    parser.add_argument("--digits", type=int, default=0, help="Zero-pad set numbers to this many digits")
    parser.add_argument("--output-dir", required=True, help="Directory for the JSON files")
    args = parser.parse_args()

    all_orders = load_generated_orders(args.input)
    all_orders = all_orders[args.offset:]
    if args.set_size * args.num_sets > len(all_orders):
        raise ValueError(f"{args.input} has only {len(all_orders)} orders")

    os.makedirs(args.output_dir, exist_ok=True)
    for index in range(1, args.num_sets + 1):
        orders = all_orders[(index - 1) * args.set_size:index * args.set_size]
        name = f"{args.prefix}{index:0{args.digits}d}" if args.digits else f"{args.prefix}{index}"
        payload = {
            "name": name,
            "type": "medicine",
            "source": f"{os.path.basename(args.input)}, SEQN {orders[0]['seqn']}-{orders[-1]['seqn']}",
            "orders": [{"items": order["items"]} for order in orders],
        }
        output_path = os.path.join(args.output_dir, f"{name}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        seqns = [order["seqn"] for order in orders]
        print(f"{output_path}: {len(orders)} orders (SEQN {min(seqns)}-{max(seqns)})")


if __name__ == "__main__":
    main()
