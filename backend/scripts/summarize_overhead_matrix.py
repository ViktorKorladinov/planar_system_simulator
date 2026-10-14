#!/usr/bin/env python3
"""
Aggregates the routing-overhead experiment matrix into the LaTeX tables and summary numbers used in the paper.

The base CSV is an export of the overhead matrix (export_experiment_results.py). Optionally, a CSV with reruns
can be supplied; each rerun must be named "Rerun of <original name> (exp <original experiment id>)" and replaces
the original run with that experiment ID.

Generated tables:
    routing_cmax_effect_d10.tex, routing_cmax_effect_d1.tex          (per mover count, all topologies)
    routing_cmax_effect_d10_ext.tex, routing_cmax_effect_d1_ext.tex  (per mover count and topology)
    warmup_comparison.tex                                            (cold vs. warm start)

Usage:
    python summarize_overhead_matrix.py --base overhead_matrix_results.csv
    python summarize_overhead_matrix.py --base overhead_matrix_results.csv --reruns rerun_results.csv \
        --output-dir ../../../xplanar/figs/tables
"""

import argparse
import csv
import os
import re
import statistics
from typing import List, Dict, Any, Optional

TOPOLOGIES = [("Paper_SQUARE64", "Square"), ("Paper_DOUBLELINE64", "Doubleline"),
              ("Paper_RING64", "Ring"), ("Paper_LINE64", "Line")]
MOVER_COUNTS = [1, 4, 8, 12]
SPEEDS = [(10, "standard"), (1, "fast")]
RERUN_NAME_PATTERN = re.compile(r"^Rerun of .* \(exp (\d+)\)$")


def load_runs(base_path: str, reruns_path: Optional[str]) -> List[Dict[str, Any]]:
    """Loads base runs and replaces the ones that were rerun."""
    with open(base_path, encoding="utf-8") as f:
        runs = {row["experiment_id"]: row for row in csv.DictReader(f)}

    if reruns_path:
        with open(reruns_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                match = RERUN_NAME_PATTERN.match(row["experiment_name"] or "")
                if not match:
                    raise ValueError(f"Rerun name does not reference original experiment: {row['experiment_name']}")
                original_id = match.group(1)
                if original_id not in runs:
                    raise ValueError(f"Original experiment {original_id} not found in base CSV")
                original = runs[original_id]
                for key in ["layout_name", "mover_amount", "dispensing_time", "warmup"]:
                    if row[key] != original[key]:
                        raise ValueError(f"Rerun {row['experiment_id']} differs from original in {key}")
                runs[original_id] = row

    result = []
    for row in runs.values():
        result.append({
            "layout": row["layout_name"],
            "movers": int(row["mover_amount"]),
            "speed": int(row["dispensing_time"]),
            "warmup": row["warmup"] == "True",
            "scheduled": float(row["scheduled_cmax"]),
            "routed": float(row["routed_cmax"]),
            "overhead_pct": float(row["routing_overhead_pct"]),
            "iterations": int(row["routing_iterations"]),
            "r_dt": float(row["dispensing_to_travel_ratio"]),
        })
    return result


def select(runs: List[Dict[str, Any]], **criteria) -> List[Dict[str, Any]]:
    return [r for r in runs if all(r[k] == v for k, v in criteria.items())]


def thousands(value: float) -> str:
    """Formats a rounded number with LaTeX thousands separators."""
    return f"{round(value):,}".replace(",", "{,}")


def mean_sd(values: List[float]) -> str:
    return f"${thousands(statistics.mean(values))} \\pm {thousands(statistics.stdev(values))}$"


def main_table(runs: List[Dict[str, Any]], speed: int, speed_name: str) -> str:
    rows = []
    for movers in MOVER_COUNTS:
        cell = select(runs, speed=speed, movers=movers)
        rows.append(
            f"            {movers} & {mean_sd([r['scheduled'] for r in cell])} & "
            f"{mean_sd([r['routed'] for r in cell])} & "
            f"{statistics.mean(r['overhead_pct'] for r in cell):.2f} & "
            f"{max(r['overhead_pct'] for r in cell):.2f} & "
            f"{statistics.mean(r['r_dt'] for r in cell):.2f} \\\\")
    n = len(select(runs, speed=speed, movers=MOVER_COUNTS[0]))
    label = "d10" if speed == 10 else "d1"
    return "\n".join([
        "\\begin{table}[ht]",
        "    \\centering",
        "    \\resizebox{\\textwidth}{!}{%",
        "        \\begin{tabular}{c|c|c|c|c|c}",
        "            \\toprule",
        "            \\shortstack{Mover\\\\count} & \\shortstack{Scheduled $C_{\\max}$\\\\mean $\\pm$ SD} & "
        "\\shortstack{Routed $C_{\\max}$\\\\mean $\\pm$ SD} & \\shortstack{Mean routing\\\\overhead [\\%]} & "
        "\\shortstack{Maximum\\\\overhead [\\%]} & \\shortstack{Mean $R_{D/T}$} \\\\",
        "            \\midrule",
        *rows,
        "            \\bottomrule",
        "        \\end{tabular}",
        "    }",
        f"    \\caption{{Scheduling and routing makespans at {speed_name} dispensing speed. Each cell summarizes "
        f"$n={n}$ runs across four topologies, five generated order sets, and two scheduler-initialization "
        "configurations. $R_{D/T}$ is the ratio of total dispensing to total transit time.}",
        f"    \\label{{table:expRouting:cmax_{label}}}",
        "\\end{table}",
        "",
    ])


def ext_table(runs: List[Dict[str, Any]], speed: int, speed_name: str) -> str:
    rows = []
    for movers in MOVER_COUNTS:
        cells = []
        for layout, _ in TOPOLOGIES:
            cell = select(runs, speed=speed, movers=movers, layout=layout)
            scheduled = statistics.mean(r["scheduled"] for r in cell)
            routed = statistics.mean(r["routed"] for r in cell)
            overhead_pct = statistics.mean(r["overhead_pct"] for r in cell)
            cells.append(f"{round(scheduled)} & +{round(routed - scheduled)}~({overhead_pct:.1f}\\%)")
        rows.append(f"            {movers} & " + " & ".join(cells) + " \\\\")
    n = len(select(runs, speed=speed, movers=MOVER_COUNTS[0], layout=TOPOLOGIES[0][0]))
    label = "d10" if speed == 10 else "d1"
    headers = " &\n".join(f"            \\multicolumn{{2}}{{c}}{{{name} $C_{{\\max}}$}}" for _, name in TOPOLOGIES)
    return "\n".join([
        "\\begin{table}[ht]",
        "    \\centering",
        "    \\resizebox{\\textwidth}{!}{%",
        "        \\begin{tabular}{c|c|c|c|c|c|c|c|c}",
        "            \\toprule",
        "            \\multirow{2}{*}{\\shortstack{Mover\\\\count}} &",
        headers + " \\\\",
        "            \\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\\cmidrule(lr){8-9}",
        "             & Scheduling & Routing & Scheduling & Routing & Scheduling & Routing & Scheduling & Routing \\\\",
        "            \\midrule",
        *rows,
        "            \\bottomrule",
        "        \\end{tabular}",
        "    }",
        f"    \\caption{{Per-topology breakdown of scheduling and routing makespans at {speed_name} dispensing speed "
        f"($d={speed}$), supplementing Table~\\ref{{table:expRouting:cmax_{label}}}. Each entry reports the mean "
        f"across $n={n}$ runs (five order sets $\\times$ two solver initializations).}}",
        f"    \\label{{table:expRouting:cmax_{label}_full}}",
        "\\end{table}",
        "",
    ])


def warmup_table(runs: List[Dict[str, Any]]) -> str:
    rows = []
    for movers in MOVER_COUNTS:
        cells = []
        for speed, _ in SPEEDS:
            cold = statistics.mean(r["scheduled"] for r in select(runs, speed=speed, movers=movers, warmup=False))
            warm = statistics.mean(r["scheduled"] for r in select(runs, speed=speed, movers=movers, warmup=True))
            diff = cold - warm
            cells.append(f"{thousands(cold)} & {thousands(warm)} & {round(diff):+d} & {diff / cold * 100:.1f}\\%")
        rows.append(f"            {movers} & " + " & ".join(cells) + " \\\\")
    n = len(select(runs, speed=10, movers=MOVER_COUNTS[0], warmup=False))
    return "\n".join([
        "\\begin{table}[ht]",
        "    \\centering",
        "    \\resizebox{\\textwidth}{!}{%",
        "        \\begin{tabular}{c|cccc|cccc}",
        "            \\toprule",
        "            \\multirow{2}{*}{\\shortstack{Mover\\\\count}} & ",
        "            \\multicolumn{4}{c|}{Standard Dispensing Speed ($d=10$)} & ",
        "            \\multicolumn{4}{c}{Fast Dispensing Speed ($d=1$)} \\\\",
        "            \\cmidrule(lr){2-5}\\cmidrule(lr){6-9}",
        "            & Cold Start & Warm Start & Difference $\\Delta$ & Improvement [\\%] & Cold Start & Warm Start & "
        "Difference $\\Delta$ & Improvement [\\%] \\\\",
        "            \\midrule",
        *rows,
        "            \\bottomrule",
        "        \\end{tabular}",
        "    }",
        f"    \\caption{{Impact of constructive warm-start initialization on scheduled makespan ($C_{{\\max}}$) within "
        f"the 300s solver time limit across {len(runs)} runs ($n={n}$ per cell across four topologies and five "
        "generated order sets). Positive differences indicate makespan reductions achieved by initializing CP "
        "Optimizer with the heuristic schedule.}",
        "    \\label{table:expRouting:warmup_comparison}",
        "\\end{table}",
        "",
    ])


def print_summary(runs: List[Dict[str, Any]]) -> None:
    overheads = [r["overhead_pct"] for r in runs]
    iterations = [r["iterations"] for r in runs]
    print(f"Runs: {len(runs)}")
    print(f"Routing overhead: mean {statistics.mean(overheads):.2f}%, max {max(overheads):.2f}%")
    print(f"Routing iterations: mean {statistics.mean(iterations):.2f}, max {max(iterations)}")
    for speed, name in SPEEDS:
        for movers in [MOVER_COUNTS[0], MOVER_COUNTS[-1]]:
            cell = select(runs, speed=speed, movers=movers)
            print(f"{name} speed, {movers} mover(s): mean R_D/T {statistics.mean(r['r_dt'] for r in cell):.2f}, "
                  f"mean overhead {statistics.mean(r['overhead_pct'] for r in cell):.2f}%")


def main():
    parser = argparse.ArgumentParser(description="Aggregate the routing-overhead matrix into paper tables.")
    parser.add_argument("--base", required=True, help="CSV export of the overhead matrix")
    parser.add_argument("--reruns", default=None, help="Optional CSV export of reruns replacing original runs")
    parser.add_argument("--output-dir", default=None, help="Directory to write the LaTeX tables to")
    args = parser.parse_args()

    runs = load_runs(args.base, args.reruns)
    print_summary(runs)

    if args.output_dir:
        tables = {
            "routing_cmax_effect_d10.tex": main_table(runs, 10, "standard"),
            "routing_cmax_effect_d1.tex": main_table(runs, 1, "fast"),
            "routing_cmax_effect_d10_ext.tex": ext_table(runs, 10, "standard"),
            "routing_cmax_effect_d1_ext.tex": ext_table(runs, 1, "fast"),
            "warmup_comparison.tex": warmup_table(runs),
        }
        os.makedirs(args.output_dir, exist_ok=True)
        for filename, content in tables.items():
            with open(os.path.join(args.output_dir, filename), "w", encoding="utf-8") as f:
                f.write(content)
        print(f"\nWrote {len(tables)} tables to {args.output_dir}")


if __name__ == "__main__":
    main()
