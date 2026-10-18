#!/usr/bin/env python3
"""
Aggregates the routing-overhead experiment matrix into the LaTeX tables and summary numbers used in the paper.

The base CSV is an export of the overhead matrix (export_experiment_results.py). Optionally, a CSV with reruns
can be supplied; each rerun must be named "Rerun of <original name> (exp <original experiment id>)" and replaces
the original run with that experiment ID. R_D/T can be overridden for every run with values recomputed by
recompute_post_hoc_metrics.py.

Generated tables:
    routing_cmax_effect_d10.tex, routing_cmax_effect_d1.tex          (per mover count, all topologies)
    routing_cmax_effect_d10_ext.tex, routing_cmax_effect_d1_ext.tex  (per mover count and topology)
    warmup_comparison.tex                                            (cold vs. warm start)

Usage:
    python summarize_overhead_matrix.py --base overhead_matrix_results.csv
    python summarize_overhead_matrix.py --base overhead_matrix_results.csv --reruns rerun_results.csv \
        --ratios overhead_recomputed.csv rerun_recomputed.csv --output-dir ../../../xplanar/figs/tables
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


def load_runs(base_path: str, reruns_paths: Optional[List[str]] = None,
              ratio_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Loads base runs, replaces the ones that were rerun, and optionally overrides R_D/T per experiment."""
    with open(base_path, encoding="utf-8") as f:
        runs = {row["experiment_id"]: row for row in csv.DictReader(f)}

    for reruns_path in reruns_paths or []:
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

    if ratio_paths:
        # Recomputed R_D/T (recompute_post_hoc_metrics.py), keyed by the ID of the experiment actually used
        ratios = {}
        for ratio_path in ratio_paths:
            with open(ratio_path, encoding="utf-8") as f:
                ratios.update({row["experiment_id"]: row["dispensing_to_travel_ratio"] for row in csv.DictReader(f)})
        missing = [row["experiment_id"] for row in runs.values() if row["experiment_id"] not in ratios]
        if missing:
            raise ValueError(f"No recomputed R_D/T for experiments {missing}; refusing to mix definitions")
        for row in runs.values():
            row["dispensing_to_travel_ratio"] = ratios[row["experiment_id"]]

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
            "lower_bound": float(row["lower_bound_cmax"]) if row.get("lower_bound_cmax") else None,
            "cp_bound": float(row["best_bound_internal"]) if row.get("best_bound_internal") else None,
            "order_set": row.get("order_list_name"),
            "seed": row.get("random_seed"),
        })
    return result


def select(runs: List[Dict[str, Any]], **criteria) -> List[Dict[str, Any]]:
    return [r for r in runs if all(r[k] == v for k, v in criteria.items())]


def thousands(value: float) -> str:
    """Formats a rounded number with LaTeX thousands separators."""
    return f"{round(value):,}".replace(",", "{,}")


def mean_sd(values: List[float]) -> str:
    return f"${thousands(statistics.mean(values))} \\pm {thousands(statistics.stdev(values))}$"


def main_table(runs: List[Dict[str, Any]], speed: int, speed_name: str, split_init: bool = False) -> str:
    rows = []
    groups = [(None, "")] if not split_init else [(False, "Cold & "), (True, "Warm & ")]
    for movers in MOVER_COUNTS:
        for warmup, init_label in groups:
            criteria = {"speed": speed, "movers": movers}
            if warmup is not None:
                criteria["warmup"] = warmup
            cell = select(runs, **criteria)
            mover_label = str(movers) if warmup in (None, False) else ""
            rows.append(
                f"            {mover_label} & {init_label}{mean_sd([r['scheduled'] for r in cell])} & "
                f"{mean_sd([r['routed'] for r in cell])} & "
                f"{statistics.mean(r['overhead_pct'] for r in cell):.2f} & "
                f"{max(r['overhead_pct'] for r in cell):.2f} & "
                f"{statistics.mean(r['r_dt'] for r in cell):.2f} \\\\")
        if split_init and movers != MOVER_COUNTS[-1]:
            rows.append("            \\midrule")
    first = {"speed": speed, "movers": MOVER_COUNTS[0], **({"warmup": False} if split_init else {})}
    n = len(select(runs, **first))
    label = "d10" if speed == 10 else "d1"
    init_header = "\\shortstack{Scheduler\\\\start} & " if split_init else ""
    init_caption = ("for cold and warm scheduler starts separately. Each row summarizes "
                    f"$n={n}$ runs across four topologies and five generated order sets."
                    if split_init else
                    f"Each cell summarizes $n={n}$ runs across four topologies, five generated order sets, and two "
                    "scheduler-initialization configurations.")
    return "\n".join([
        "\\begin{table}[ht]",
        "    \\centering",
        "    \\small",
        f"        \\begin{{tabular}}{{c|{'c|' if split_init else ''}c|c|c|c|c}}",
        "            \\toprule",
        f"            \\shortstack{{Mover\\\\count}} & {init_header}\\shortstack{{Scheduled $C_{{\\max}}$\\\\mean $\\pm$ SD}} & "
        "\\shortstack{Routed $C_{\\max}$\\\\mean $\\pm$ SD} & \\shortstack{Mean routing\\\\overhead [\\%]} & "
        "\\shortstack{Maximum\\\\overhead [\\%]} & \\shortstack{Mean $R_{D/T}$} \\\\",
        "            \\midrule",
        *rows,
        "            \\bottomrule",
        "        \\end{tabular}",
        f"    \\caption{{Scheduling and routing makespans at {speed_name} dispensing speed"
        f"{', ' if split_init else '. '}{init_caption} $R_{{D/T}}$ is the ratio of total drug-dispensing time "
        "to total transit time.}",
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
            diff = warm - cold
            cells.append(f"{thousands(cold)} & {thousands(warm)} & ${round(diff):+d}$ & ${diff / cold * 100:+.1f}$\\%")
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
        "            & Cold Start & Warm Start & Difference $\\Delta$ & Change [\\%] & Cold Start & Warm Start & "
        "Difference $\\Delta$ & Change [\\%] \\\\",
        "            \\midrule",
        *rows,
        "            \\bottomrule",
        "        \\end{tabular}",
        "    }",
        f"    \\caption{{Impact of constructive warm-start initialization on scheduled makespan ($C_{{\\max}}$) within "
        f"the 300s solver time limit across {len(runs)} runs ($n={n}$ per cell across four topologies and five "
        "generated order sets). $\\Delta$ is the warm-start minus the cold-start makespan; negative values indicate "
        "makespan reductions achieved by initializing CP Optimizer with the heuristic schedule.}",
        "    \\label{table:expRouting:warmup_comparison}",
        "\\end{table}",
        "",
    ])


def lower_bound_table(runs: List[Dict[str, Any]]) -> str:
    """Lower bound (SHPPN + P||Cmax) and CP Optimizer's internal bound versus the scheduled makespan.

    Warm-start runs are the proposed configuration; the cold-start gap is reported for comparison.
    """
    def gaps(cell, field):
        return [(r["scheduled"] - (r[field] or 0.0)) / r["scheduled"] * 100 for r in cell]

    rows = []
    for speed, speed_name in SPEEDS:
        for movers in MOVER_COUNTS:
            warm = select(runs, speed=speed, movers=movers, warmup=True)
            cold = select(runs, speed=speed, movers=movers, warmup=False)
            gap_warm, gap_cold = gaps(warm, "lower_bound"), gaps(cold, "lower_bound")
            speed_label = f"\\multirow{{{len(MOVER_COUNTS)}}}{{*}}{{{speed_name.capitalize()}}}" \
                if movers == MOVER_COUNTS[0] else ""
            rows.append(
                f"            {speed_label} & {movers} & {thousands(statistics.mean(r['lower_bound'] for r in warm))} & "
                f"{thousands(statistics.mean(r['scheduled'] for r in warm))} & "
                f"{statistics.mean(gap_warm):.2f} ({min(gap_warm):.2f}--{max(gap_warm):.2f}) & "
                f"{statistics.mean(gap_cold):.2f} & {statistics.mean(gaps(warm, 'cp_bound')):.2f} \\\\")
        if speed != SPEEDS[-1][0]:
            rows.append("            \\midrule")
    n = len(select(runs, speed=SPEEDS[0][0], movers=MOVER_COUNTS[0], warmup=True))
    return "\n".join([
        "\\begin{table}[htbp]",
        "    \\centering",
        "    \\resizebox{\\textwidth}{!}{%",
        "        \\begin{tabular}{c|c|cc|ccc}",
        "            \\toprule",
        "            \\multirow{2}{*}{\\shortstack{Dispensing\\\\speed}} & \\multirow{2}{*}{\\shortstack{Mover\\\\count}} & "
        "\\multicolumn{2}{c|}{Mean value} & \\multicolumn{3}{c}{Gap of the scheduled $C_{\\max}$ to the bound [\\%]} \\\\",
        "            \\cmidrule(lr){3-4}\\cmidrule(lr){5-7}",
        "             & & SHPPN LB & Scheduled $C_{\\max}$ (warm start) & Warm-started schedule to SHPPN LB, "
        "mean (min--max) & Cold-started schedule to SHPPN LB, mean & Warm-started schedule to CP bound, mean \\\\",
        "            \\midrule",
        *rows,
        "            \\bottomrule",
        "        \\end{tabular}",
        "    }",
        f"    \\caption{{Lower bounds versus scheduled makespan. SHPPN LB is the bound of Section~\\ref{{sec:lowerbound}}; "
        f"CP bound is the objective bound reported by CP Optimizer at its time limit. Each row summarizes $n={n}$ runs "
        "with 100 orders per scheduler start (four topologies, five generated order sets). The gap of the cold-started "
        "schedule is given for comparison. Gaps are $(C_{\\max} - \\text{bound}) / C_{\\max}$.}",
        "    \\label{table:expFour:compar_wide}",
        "\\end{table}",
        "",
    ])


def variation_table(set_runs: List[Dict[str, Any]], seed_runs: List[Dict[str, Any]], seed_set: str) -> str:
    """Coefficient of variation of the makespans across order sets versus across CP random seeds."""
    def mean_cv(runs: List[Dict[str, Any]], speed: int, movers: int, field: str) -> float:
        groups: Dict[tuple, List[float]] = {}
        for r in select(runs, speed=speed, movers=movers):
            groups.setdefault((r["layout"], r["warmup"]), []).append(r[field])
        return statistics.mean(statistics.stdev(v) / statistics.mean(v) * 100 for v in groups.values())

    seed_group = [r for r in seed_runs if r["order_set"] == seed_set]
    set_group = [r for r in set_runs if r["seed"] in (None, "", "1")]
    rows = []
    for speed, speed_name in SPEEDS:
        for movers in MOVER_COUNTS:
            speed_label = f"\\multirow{{{len(MOVER_COUNTS)}}}{{*}}{{{speed_name.capitalize()}}}" \
                if movers == MOVER_COUNTS[0] else ""
            rows.append(
                f"            {speed_label} & {movers} & "
                f"{mean_cv(seed_group, speed, movers, 'scheduled'):.2f} & {mean_cv(seed_group, speed, movers, 'routed'):.2f} & "
                f"{mean_cv(set_group, speed, movers, 'scheduled'):.2f} & {mean_cv(set_group, speed, movers, 'routed'):.2f} \\\\")
        if speed != SPEEDS[-1][0]:
            rows.append("            \\midrule")
    n_seeds = len({r["seed"] for r in seed_group})
    n_sets = len({r["order_set"] for r in set_group})
    return "\n".join([
        "\\begin{table}[htbp]",
        "    \\centering",
        "        \\begin{tabular}{c|c|cc|cc}",
        "            \\toprule",
        "            \\multirow{2}{*}{\\shortstack{Dispensing\\\\speed}} & \\multirow{2}{*}{\\shortstack{Mover\\\\count}} & "
        f"\\multicolumn{{2}}{{c|}}{{{n_seeds} solver seeds, one order set}} & "
        f"\\multicolumn{{2}}{{c}}{{{n_sets} order sets, one seed}} \\\\",
        "            \\cmidrule(lr){3-4}\\cmidrule(lr){5-6}",
        "             & & Scheduled & Routed & Scheduled & Routed \\\\",
        "            \\midrule",
        *rows,
        "            \\bottomrule",
        "        \\end{tabular}",
        "    \\caption{Variation of the makespan caused by the solver versus by the instance: mean coefficient of "
        "variation [\\%] of the scheduled and routed $C_{\\max}$ over CP Optimizer random seeds on a fixed order set, "
        "and over independently generated order sets with a fixed seed. Means are taken over the four topologies "
        "and the two scheduler-initialization configurations.}",
        "    \\label{table:expRouting:variation}",
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
    parser.add_argument("--reruns", nargs="*", default=None,
                        help="Optional CSV export(s) of reruns replacing original runs")
    parser.add_argument("--ratios", nargs="*", default=None,
                        help="Optional CSV(s) from recompute_post_hoc_metrics.py overriding R_D/T for every run")
    parser.add_argument("--output-dir", default=None, help="Directory to write the LaTeX tables to")
    parser.add_argument("--split-init", action="store_true",
                        help="Report cold and warm scheduler starts in separate rows of the main tables")
    parser.add_argument("--lower-bound", action="store_true", help="Also write lower_bound_comparison.tex")
    parser.add_argument("--seed-runs", nargs="*", default=None,
                        help="CSV export(s) with additional CP seeds; writes variation_table.tex")
    parser.add_argument("--seed-order-set", default="orders_set1", help="Order set used for the seed runs")
    args = parser.parse_args()

    runs = load_runs(args.base, args.reruns, args.ratios)
    print_summary(runs)

    if args.output_dir:
        tables = {
            "routing_cmax_effect_d10.tex": main_table(runs, 10, "standard", args.split_init),
            "routing_cmax_effect_d1.tex": main_table(runs, 1, "fast", args.split_init),
            "routing_cmax_effect_d10_ext.tex": ext_table(runs, 10, "standard"),
            "routing_cmax_effect_d1_ext.tex": ext_table(runs, 1, "fast"),
            "warmup_comparison.tex": warmup_table(runs),
        }
        if args.lower_bound:
            tables["lower_bound_comparison.tex"] = lower_bound_table(runs)
        if args.seed_runs:
            seed_runs = [r for path in args.seed_runs for r in load_runs(path)]
            seed_runs += [r for r in runs if r["order_set"] == args.seed_order_set]
            tables["variation_table.tex"] = variation_table(runs, seed_runs, args.seed_order_set)
        os.makedirs(args.output_dir, exist_ok=True)
        for filename, content in tables.items():
            with open(os.path.join(args.output_dir, filename), "w", encoding="utf-8") as f:
                f.write(content)
        print(f"\nWrote {len(tables)} tables to {args.output_dir}")


if __name__ == "__main__":
    main()
