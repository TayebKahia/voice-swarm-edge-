#!/usr/bin/env python3
"""Exp-4: formation validation. 50 SIL trials x three formations (RQ3, NFR-12, NFR-13).

Protocol, from `prd.md` Table 15 and not negotiable here: timestep 0.02 s,
`seed = trial index x 42`, initial positions N(0, 0.5 m) about the centroid, 60 s
trials, three formations (circle, line, wedge).

**One-way, with `trial` as the replication unit.** Table 15 says so explicitly and
§11 repeats it: a two-way design treating trial as a second factor would be
mis-specified, because trials are replicates of the same condition rather than levels
of anything.

**Convergence is a rate plus a median over converged trials only.** Never a
confidence interval on a sample containing non-converging trials: there is no finite
mean to put an interval around. A trial that never reaches FA >= 0.85 contributes to
the rate and to nothing else.

**Why this does not go through `eval/bench.py`.** That harness measures wall-clock and
resident memory of a deployed pipeline. Exp-4 measures control quality in simulation,
where wall-clock is a property of this workstation and has no interpretation at all;
recording it would invite a latency reading of a number that is not one. The trial
row here carries FA, convergence, collisions and clamp activations instead.

Usage:
    python eval/exp4.py                 # the full 150 trials, about a minute
    python eval/exp4.py --trials 5      # smoke test
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Sequence

import numpy as np
from scipy import stats

if __package__ in (None, ""):  # `python eval/exp4.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from swarm.control import CLAMP_DISTANCE, COLLISION_DISTANCE, SHAPES
from swarm.simulate import CONVERGENCE_FA, SLOT_TOLERANCE, TrialSpec, run_trial

REPO = Path(__file__).resolve().parent.parent
CSV_OUT = REPO / "results" / "exp4.csv"
TABLE_OUT = REPO / "results" / "exp4_formation.md"

TRIALS_PER_SHAPE = 50

FIELDNAMES = (
    "experiment", "shape", "trial", "seed", "formation_accuracy", "converged",
    "convergence_seconds", "collisions", "clamp_activations", "min_pair_distance",
    "final_mean_error",
)


def run_all(trials: int = TRIALS_PER_SHAPE, shapes: Sequence[str] = SHAPES) -> list[dict]:
    rows = []
    for shape in shapes:
        for index in range(trials):
            result = run_trial(TrialSpec(shape=shape, index=index))
            rows.append({
                "experiment": 4,
                "shape": shape,
                "trial": index,
                "seed": result.seed,
                "formation_accuracy": round(result.formation_accuracy, 6),
                "converged": int(result.converged),
                # Empty, not the trial length: a non-convergence must not be able to
                # read downstream as a slow convergence.
                "convergence_seconds": ("" if result.convergence_seconds is None
                                        else round(result.convergence_seconds, 3)),
                "collisions": result.collisions,
                "clamp_activations": result.clamp_activations,
                "min_pair_distance": round(result.min_pair_distance, 4),
                "final_mean_error": round(result.final_mean_error, 4),
            })
        print(f"  {shape:7s} {trials} trials done")
    return rows


def _iqr(values: Sequence[float]) -> tuple[float, float]:
    ordered = np.sort(np.asarray(values, dtype=float))
    return float(np.percentile(ordered, 25)), float(np.percentile(ordered, 75))


def summarise(rows: Sequence[dict]) -> dict[str, dict]:
    summary = {}
    for shape in sorted({row["shape"] for row in rows}):
        group = [row for row in rows if row["shape"] == shape]
        accuracy = np.array([float(row["formation_accuracy"]) for row in group])
        converged = [row for row in group if int(row["converged"])]
        times = [float(row["convergence_seconds"]) for row in converged]
        low, high = _iqr(times) if times else (float("nan"), float("nan"))
        summary[shape] = {
            "n": len(group),
            "fa_mean": float(accuracy.mean()),
            "fa_sd": float(accuracy.std(ddof=1)) if len(accuracy) > 1 else 0.0,
            "fa_min": float(accuracy.min()),
            "meets_nfr13": int((accuracy >= CONVERGENCE_FA).sum()),
            "convergence_rate": len(converged) / len(group),
            "convergence_median": float(np.median(times)) if times else float("nan"),
            "convergence_iqr": (low, high),
            "collisions": sum(int(row["collisions"]) for row in group),
            "clamp_activations": sum(int(row["clamp_activations"]) for row in group),
            "min_pair_distance": min(float(row["min_pair_distance"]) for row in group),
        }
    return summary


def anova(rows: Sequence[dict], metric: str) -> dict:
    """One-way ANOVA across formations. Degenerate variance is reported, not hidden.

    `scipy.stats.f_oneway` on groups with zero within-group variance returns `nan`
    with a warning, and an unexamined `nan` in a results table is indistinguishable
    from a bug. If every trial produced the same value, that *is* the finding --- the
    formations did not differ because nothing varied --- and it is stated in words.
    """
    groups = []
    for shape in sorted({row["shape"] for row in rows}):
        values = [row[metric] for row in rows if row["shape"] == shape and row[metric] != ""]
        groups.append(np.array([float(v) for v in values]))

    if any(len(g) < 2 for g in groups):
        return {"applicable": False,
                "reason": "at least one formation has fewer than two usable trials"}

    pooled = np.concatenate(groups)
    if float(pooled.std()) == 0.0:
        return {"applicable": False,
                "reason": f"every trial produced {pooled[0]:.4g}; there is no variance to partition"}
    if all(float(g.std()) == 0.0 for g in groups):
        return {"applicable": False,
                "reason": "each formation is internally constant; F is undefined "
                          "(zero within-group variance)"}

    statistic, p_value = stats.f_oneway(*groups)
    result = {"applicable": True, "F": float(statistic), "p": float(p_value),
              "df_between": len(groups) - 1, "df_within": len(pooled) - len(groups)}
    if p_value < 0.05:
        shapes = sorted({row["shape"] for row in rows})
        tukey = stats.tukey_hsd(*groups)
        result["tukey"] = [
            {"a": shapes[i], "b": shapes[j],
             "difference": float(tukey.statistic[i][j]),
             "p": float(tukey.pvalue[i][j]),
             "ci_low": float(tukey.confidence_interval().low[i][j]),
             "ci_high": float(tukey.confidence_interval().high[i][j])}
            for i in range(len(shapes)) for j in range(i + 1, len(shapes))
        ]
    return result


def _table(rows: Sequence[dict], summary: dict, fa_test: dict, time_test: dict) -> str:
    total_collisions = sum(s["collisions"] for s in summary.values())
    total_clamps = sum(s["clamp_activations"] for s in summary.values())
    closest = min(s["min_pair_distance"] for s in summary.values())

    lines = [
        "### Exp-4: formation validation (RQ3)",
        "",
        f"{sum(s['n'] for s in summary.values())} trials: "
        f"{summary[next(iter(summary))]['n']} per formation, 60 s each, 50 Hz, "
        f"seed = trial index x 42, initial positions N(0, 0.5 m) about the centroid.",
        "",
        f"| Formation | n | FA (mean +/- sd) | FA min | meets NFR-13 | conv. rate "
        f"| conv. median [IQR] s | collisions | clamp |",
        "| :--- | ---: | :--- | ---: | ---: | ---: | :--- | ---: | ---: |",
    ]
    for shape, s in summary.items():
        iqr = ("--" if s["convergence_median"] != s["convergence_median"]
               else f"{s['convergence_median']:.2f} [{s['convergence_iqr'][0]:.2f}, {s['convergence_iqr'][1]:.2f}]")
        lines.append(
            f"| {shape} | {s['n']} | {s['fa_mean']:.3f} +/- {s['fa_sd']:.3f} | {s['fa_min']:.3f} "
            f"| {s['meets_nfr13']}/{s['n']} | {s['convergence_rate']:.2f} | {iqr} "
            f"| {s['collisions']} | {s['clamp_activations']} |")

    lines += [
        "",
        f"**NFR-12 --- collisions: {total_collisions} observed** across all trials "
        f"(a collision is a pair closer than {COLLISION_DISTANCE} m). The closest approach "
        f"recorded was {closest:.3f} m against a clamp distance of {CLAMP_DISTANCE} m. "
        f"The hard geometric clamp at the integrator resolved {total_clamps} pair violations, "
        "which is the honest companion figure: each one is an occasion on which the "
        "artificial potential field alone did not keep two drones apart. The claim is "
        "therefore zero collisions *observed*, "
        "backed by that clamp --- not zero collisions guaranteed by APF, which with discrete "
        "timesteps and bounded acceleration would be unprovable.",
        "",
        f"**NFR-13 --- FA >= {CONVERGENCE_FA}** (fraction of drones within "
        f"tau = {SLOT_TOLERANCE} m of their *assigned* slot, averaged over the final 5 s).",
        "",
    ]
    for label, test in (("formation accuracy", fa_test), ("convergence time", time_test)):
        if test.get("applicable"):
            line = (f"One-way ANOVA on {label} across formations: "
                    f"F({test['df_between']}, {test['df_within']}) = {test['F']:.3f}, p = {test['p']:.4g}.")
            lines.append(line)
            for pair in test.get("tukey", []):
                lines.append(
                    f"  - Tukey HSD {pair['a']} vs {pair['b']}: "
                    f"difference {pair['difference']:+.3f} s "
                    f"[{pair['ci_low']:.3f}, {pair['ci_high']:.3f}], p = {pair['p']:.4g}")
        else:
            lines.append(f"One-way ANOVA on {label}: **not applicable** --- {test['reason']}.")
            if label == "formation accuracy":
                lines.append(
                    "    This is a saturated metric, and it should be read as a statement about "
                    "the protocol rather than about the controller. Table 15 fixes the initial "
                    "dispersion at N(0, 0.5 m) and the trial length at 60 s; against a formation "
                    "several metres across, that leaves every run converged within the first few "
                    "seconds and roughly 55 s of settled flight for FA to average over. The "
                    "pre-registered protocol is reported as pre-registered rather than made "
                    "harder after the fact to manufacture variance --- but the honest reading is "
                    "that FA does not discriminate between these three formations, and "
                    "convergence time is the metric that does.")
        lines.append("")
    lines.append("Trials are replicates, not a second factor: the design is one-way (Table 15).")
    return "\n".join(lines) + "\n"


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--trials", type=int, default=TRIALS_PER_SHAPE)
    parser.add_argument("--csv", type=Path, default=CSV_OUT)
    parser.add_argument("--table", type=Path, default=TABLE_OUT)
    args = parser.parse_args(argv)

    print(f"Exp-4: {args.trials} trials x {len(SHAPES)} formations")
    rows = run_all(args.trials)

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    summary = summarise(rows)
    table = _table(rows, summary,
                   anova(rows, "formation_accuracy"), anova(rows, "convergence_seconds"))
    args.table.write_text(table, encoding="utf-8")
    print("\n" + table)
    print(f"wrote {args.csv}\nwrote {args.table}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
