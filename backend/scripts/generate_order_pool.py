#!/usr/bin/env python3
"""
Generates a reproducible pool of synthetic orders with the data generator version that produced the original
orders (diplomka commit 431c51b, copied to scripts/vendor/data_generator_431c51b.py; drugs per order uniform in
[3, 7]). Later versions of the generator changed the drug-count logic and give a different distribution.

The generator has no seed option; this wrapper seeds NumPy's global random state (used for the multivariate
normal samples, the drug counts, and the dosages) and calls main() with the settings used for the paper
(40 drugs, 3-7 drugs per order). Input files are read from diplomka/src/data_generator. Must be run with the
generator's Python environment, from any directory:

    ../../diplomka/src/data_generator/.env/bin/python scripts/generate_order_pool.py \
        --num-orders 12000 --seed 2026 --output data/order_pool/generated_orders_seed2026.csv
"""

import argparse
import os
import sys

import numpy as np

GENERATOR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "diplomka", "src",
                                             "data_generator"))


def main():
    parser = argparse.ArgumentParser(description="Generate a seeded pool of synthetic orders.")
    parser.add_argument("--num-orders", type=int, required=True, help="Number of orders to generate")
    parser.add_argument("--seed", type=int, required=True, help="NumPy random seed")
    parser.add_argument("--output", required=True, help="Output CSV (SEQN;drug_names;dosages)")
    args = parser.parse_args()

    output = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output), exist_ok=True)

    # The generator reads its input files relative to the generator directory
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
    os.chdir(GENERATOR_DIR)
    import data_generator_431c51b as generator  # noqa: E402

    np.random.seed(args.seed)
    generator.main(num_vars=40, num_samples=args.num_orders,
                   marginals_filename="feat_probs.csv", corr_matrix_filename="correlation_matrix.csv",
                   sorted_names_filename="drug_names.csv", output_filename=output,
                   threshold_drugs_per_sample=(3, 7))
    print(f"Generated {args.num_orders} orders with seed {args.seed} to {output}")


if __name__ == "__main__":
    main()
