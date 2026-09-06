#!/usr/bin/env python3
"""Every figure, regenerated from `results/`. No figure is ever edited by hand.

**Figure 2 --- the accuracy/latency Pareto plot** (prd.md 8.2): exact match against
p95 latency, marker area proportional to peak RSS, one point per model x
quantisation, with the 2.5 s target as a vertical line.

Three things about that specification do not survive contact with what was actually
measured, and the figure states each of them on its own face rather than in a caption
a reader may not reach:

1. **Three of the six points do not exist.** The Sat-19 triage scoped Exp-1 to Q4_K_M
   (STATE.md), so no Q8_0 artefact has a latency or an RSS figure from the Pi. Their
   accuracy is known and their cost is not, which is not the same as their cost being
   zero --- they are named in a box on the axes instead of being plotted somewhere
   convenient.

2. **The x-axis is not the quantity NFR-2 bounds.** NFR-2's 2,500 ms runs end-to-end
   from end-of-speech and therefore includes VAD, STT, validation, the FSM and the
   bus; Exp-1 measured the SLM stages only (Table 6's prefill and decode rows,
   summed). Every plotted x is therefore a *lower bound* on the quantity the vertical
   line bounds, and a point left of the line has not met NFR-2 --- it has failed to
   rule itself out. Exp-2 measures the real thing. The directly comparable budget,
   drawn as a second line, is Table 6's own SLM allowance of 250 + 1,100 ms.

3. **No trial was thermally throttled, and the figure says so.** All 180 scored
   trials of the cooled run held the 2.4 GHz pinned clock at 67.5-74.1 C, so NFR-10
   passes at 0% against a 5% budget. The predecessor run throttled on 180/180 at a
   1.5 GHz cap and cost 25-41% of decode p95 (`results/thermal_headroom.md`). The
   thermal state stays on the figure for the same reason it did when it was bad: a
   Pareto plot invites the reader to treat the x-axis as a property of the model,
   and here it is partly a property of the enclosure.

**The keyword-spotter operating curve** (Ingenieur Ch 5, `fig:keyword-curve`): for each
reflex-path class, the false-reject rate on the synthetic test takes against the false
accepts per hour on the ambient-speech stream, as the common threshold sweeps the
selection grid, with the operating threshold marked. Everything plotted is read from
`results/wake_training.json`, which `train/train_wake.py` writes; the threshold is the
one that script selected on val, never re-selected here. Two things the figure states
on its face:

1. **The operating point's false-accept rate carries its interval.** One event in 0.43 h
   gives a 95% interval that straddles the 1/h budget, and that is the whole reason the
   criterion is "not demonstrated". A bare marker would read as a miss.

2. **The top of the curve is flat in false accepts.** The one test false accept survives
   every threshold from 0.88 up, so the points pile up at one x; they are drawn, not
   thinned, because that pile is the finding.

Usage:
    python eval/plots.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")           # no display on the workstation or in CI
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.transforms import blended_transform_factory

#: TrueType, not Type 3, in the PDF: Type 3 fonts are vector but render poorly in some
#: viewers and are rejected by some submission checkers.
matplotlib.rcParams["pdf.fonttype"] = 42

if __package__ in (None, ""):   # `python eval/plots.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.bench import aggregate, read_trials

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results"
SURFACE_B = RESULTS / "surface_b.csv"
#: The cooled run of record -- the PRD declares a Pi 5 with an active cooler
#: (PRD.tex:199) and names one as the mitigation for risk R-8 (PRD.tex:1841). The first
#: Exp-1 predated the cooler and throttled on 180/180 trials; it is kept and reported in
#: `results/thermal_headroom.md`, not plotted, because a Pareto frontier drawn from it
#: describes hardware this project never declared.
EXP1 = RESULTS / "exp1_cooled.csv"
FIGURE2 = RESULTS / "figure2_pareto"

#: The split Figure 2 plots. `test_golden` is real recorded speech; `test_synth`
#: shares template families with training and would flatter every point equally.
SPLIT = "test_golden"

#: NFR-2, end-to-end from end-of-speech. Drawn as specified, and drawn dashed and
#: annotated because the plotted x does not yet include the non-SLM stages.
NFR2_MS = 2500.0

#: Table 6's SLM allowance: prefill p95 250 ms + decode p95 1,100 ms. This one *is*
#: measured on the same quantity as the x-axis, which is why it is the solid line.
SLM_BUDGET_MS = 250.0 + 1100.0

#: NFR-4. The accuracy constraint of record; a configuration below it is not
#: deployable however fast it is, which is what makes this a Pareto plot and not a
#: latency ranking.
NFR4_EM = 0.85

#: The names the thesis prose uses. Each point is labelled, so one marker shape serves
#: every model and the legend needs to explain only fill (frontier) and area (memory).
#: The keyword-spotter record: held-out rates at every grid threshold, and the
#: operating threshold `train/train_wake.py` selected on val before test was scored.
WAKE_TRAINING = RESULTS / "wake_training.json"
FIGURE_KEYWORD = RESULTS / "figure_keyword_curve"

#: The two keyword criteria of the Ingenieur's tab:nonfunctional-requirements: false
#: accepts on ambient speech (both classes together) and false rejects per class.
KEYWORD_FA_BUDGET_PER_HOUR = 1.0
KEYWORD_FRR_BUDGET = 0.10

#: Class names as the thesis prints them, in the order the legend lists them.
KEYWORD_CLASSES = {"swarm_hold": "swarm hold", "swarm_abort": "swarm abort"}

DISPLAY = {"llama-3.2-1b-instruct": "Llama-3.2-1B", "qwen2.5-0.5b-instruct": "Qwen2.5-0.5B",
           "smollm2-360m-instruct": "SmolLM2-360M"}


def _display(path: Path) -> str:
    """Repo-relative when it can be, absolute when it cannot.

    `Path.relative_to` raises on a path outside the repository, which would replace
    an error message naming the missing sweep with an unrelated `ValueError` about
    subpaths --- the failure mode hiding the failure it was written to report.
    """
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def _rows(path: Path) -> list[dict]:
    if not path.is_file():
        raise SystemExit(f"missing {_display(path)} -- run the sweep that writes it")
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _exp1_summaries() -> dict[str, dict]:
    """Config stem -> Exp-1 summary, warm-up rows excluded by name, as Table 17 does."""
    rows = [r for r in read_trials(EXP1) if not r["config"].endswith("-warmup")]
    return {s["config"]: s for s in aggregate(rows)}


def _points() -> tuple[list[dict], list[dict]]:
    """(plottable, unmeasured) --- one entry per model x quantisation on `SPLIT`.

    A configuration is plottable when Exp-1 produced a latency for it. The split is
    deliberate: an unmeasured configuration is carried through with its accuracy so
    the figure can say it exists, rather than being dropped and silently reducing a
    six-point specification to a three-point plot.
    """
    exp1 = _exp1_summaries()
    plottable, unmeasured = [], []
    for row in _rows(SURFACE_B):
        if row["grammar"] != "on" or row["split"] != SPLIT:
            continue
        entry = {"model": row["model"], "quant": row["quant"],
                 "em": float(row["exact_match"]), "n_items": row["n"]}
        summary = exp1.get(f"{row['model']}-{row['quant']}")
        if summary and summary.get("total_p95") not in ("", None):
            entry["p95_ms"] = float(summary["total_p95"])
            entry["rss_mb"] = float(summary["peak_rss_mb"])
            entry["throttled"] = float(summary["throttled_fraction"])
            entry["n_latency"] = int(summary["n_latency"])
            plottable.append(entry)
        else:
            unmeasured.append(entry)
    return plottable, unmeasured


def pareto_frontier(points: list[dict]) -> list[dict]:
    """Non-dominated points: no other point is both faster and at least as accurate.

    Ties are kept rather than broken --- two configurations with the same accuracy and
    the same latency are both on the frontier, and picking one is the selection rule's
    job (prd.md 10.2), not the plot's.
    """
    frontier = [
        point for point in points
        if not any(other is not point
                   and other["p95_ms"] <= point["p95_ms"]
                   and other["em"] >= point["em"]
                   and (other["p95_ms"] < point["p95_ms"] or other["em"] > point["em"])
                   for other in points)
    ]
    return sorted(frontier, key=lambda p: p["p95_ms"])


def figure2() -> list[Path]:
    plottable, unmeasured = _points()
    if not plottable:
        raise SystemExit("no configuration has both an accuracy and an Exp-1 latency")

    figure, axes = plt.subplots(figsize=(7.2, 5.0))

    #: Marker *area* scales with RSS so the visual quantity a reader compares is the
    #: one the legend claims. Scaling the radius instead would make a 2x memory
    #: footprint look like a 4x one. The constant is chosen so the largest artefact
    #: measured (1.63 GB) is a legible dot rather than a blob covering its neighbours.
    area = lambda rss: 0.22 * rss

    frontier = pareto_frontier(plottable)
    if len(frontier) > 1:
        axes.plot([p["p95_ms"] for p in frontier], [p["em"] for p in frontier],
                  color="0.45", linewidth=1.0, linestyle="-", zorder=1,
                  label="Pareto frontier")

    for point in plottable:
        dominated = point not in frontier
        axes.scatter(point["p95_ms"], point["em"], s=area(point["rss_mb"]),
                     marker="o",
                     facecolor="white" if dominated else "#1f6feb",
                     edgecolor="#1f6feb", linewidth=1.6, zorder=3,
                     alpha=0.95)
        #: Label to the left of the marker, vertically centred: a label centred above or
        #: below spans about 700 ms of the axis and crossed a budget line on two of the
        #: three points. Every point sits right of 800 ms, so the left side has room.
        pad = 6 + (area(point["rss_mb"]) ** 0.5) / 2
        axes.annotate(
            f"{DISPLAY.get(point['model'], point['model'])} {point['quant']}\n"
            f"EM {point['em']:.3f} · p95 {point['p95_ms']:,.0f} ms\n"
            f"{point['rss_mb'] / 1024:.2f} GiB",
            xy=(point["p95_ms"], point["em"]),
            xytext=(-pad, 0), textcoords="offset points", ha="right", va="center",
            fontsize=7.5, color="0.15")

    axes.set_ylim(0.55, 1.0)
    axes.set_xlim(0, max(NFR2_MS, max(p["p95_ms"] for p in plottable)) * 1.12)

    #: Line labels sit in the top margin, above the plotting area, so that no label can
    #: land on a point annotation (the rotated in-axes labels did, on two points).
    top = blended_transform_factory(axes.transData, axes.transAxes)
    axes.axvline(SLM_BUDGET_MS, color="#b45309", linewidth=1.2, zorder=2)
    axes.text(SLM_BUDGET_MS, 1.015, "Language-model stage allowance\n1,350 ms (same quantity as the axis)",
              transform=top, ha="center", va="bottom", fontsize=7, color="#b45309")

    axes.axvline(NFR2_MS, color="#b91c1c", linewidth=1.4, linestyle="--", zorder=2)
    axes.text(NFR2_MS, 1.015, "End-to-end budget 2,500 ms\n(the axis measures part of it)",
              transform=top, ha="center", va="bottom", fontsize=7, color="#b91c1c")

    axes.axhline(NFR4_EM, color="#15803d", linewidth=1.2, linestyle=":", zorder=2)
    axes.text(40, NFR4_EM + 0.004, "Exact-match threshold 0.85", ha="left",
              va="bottom", fontsize=7.5, color="#15803d")

    if unmeasured:
        names = "\n".join(f"  · {DISPLAY.get(p['model'], p['model'])} {p['quant']}"
                          f"  EM {p['em']:.3f}" for p in unmeasured)
        axes.text(0.015, 0.03,
                  "Not plotted, not timed on the Raspberry Pi 5:\n" + names,
                  transform=axes.transAxes, fontsize=7.5, va="bottom", ha="left",
                  color="0.25",
                  bbox=dict(boxstyle="round,pad=0.45", facecolor="#f6f6f6",
                            edgecolor="0.75", linewidth=0.7))

    #: No in-figure title: the thesis caption names and numbers the figure, and a title
    #: typed here ("Figure 2") cannot follow the document's own numbering. The thermal
    #: state the title used to carry is in the caption.
    n_latency = {p["n_latency"] for p in plottable}
    n_items = {int(p["n_items"]) for p in plottable}
    axes.set_xlabel("Language-model prefill + decode, p95 (ms)\n"
                    f"Raspberry Pi 5, n = {min(n_latency)} timed runs per configuration")
    axes.set_ylabel(f"Exact match on {SPLIT} (n = {min(n_items)} items)")
    axes.grid(True, linewidth=0.4, color="0.9", zorder=0)
    axes.set_axisbelow(True)
    for spine in ("top", "right"):
        axes.spines[spine].set_visible(False)

    #: A size legend, not a colour one: marker area is the only channel carrying RSS,
    #: and a reader cannot decode it from the points alone.
    handles = [axes.scatter([], [], s=area(mb), facecolor="white", edgecolor="0.4",
                            linewidth=1.2, label=f"{mb / 1024:.1f} GiB peak memory")
               for mb in (512, 1024, 1536)]
    if len(frontier) > 1:
        handles.insert(0, axes.plot([], [], color="0.45", linewidth=1.0,
                                    label="Pareto frontier")[0])
    handles += [
        axes.scatter([], [], s=70, facecolor="#1f6feb", edgecolor="#1f6feb",
                     linewidth=1.6, label="non-dominated"),
        axes.scatter([], [], s=70, facecolor="white", edgecolor="#1f6feb",
                     linewidth=1.6, label="dominated"),
    ]
    #: Anchored in the empty band between the two budget lines, below the threshold.
    axes.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.52, 0.02), fontsize=7, frameon=True,
                borderpad=0.6, labelspacing=0.9, handletextpad=1.0, framealpha=0.95)

    figure.tight_layout()
    written = []
    for suffix in (".pdf", ".png"):
        path = FIGURE2.with_suffix(suffix)
        figure.savefig(path, dpi=200)
        written.append(path)
    plt.close(figure)
    return written


def keyword_curve(split: str = "test") -> dict:
    """The operating curve of one split, sorted by threshold, plus what the figure marks.

    Returned rather than plotted so the tests can check the data the figure is drawn
    from: which point is the operating point, and that the interval comes from the file.
    """
    if not WAKE_TRAINING.is_file():
        raise SystemExit(f"missing {_display(WAKE_TRAINING)} -- run train/train_wake.py")
    record = json.loads(WAKE_TRAINING.read_text(encoding="utf-8"))
    points = sorted(record["roc"][split], key=lambda p: p["threshold"])
    threshold = record["threshold"]
    operating = [p for p in points if p["threshold"] == threshold]
    if len(operating) != 1:
        raise SystemExit(f"operating threshold {threshold} is not on the {split} grid")
    return {"points": points, "threshold": threshold, "operating": operating[0],
            "fa_ci95": record[split]["ambient"]["per_hour_ci95"],
            "hours": record[split]["ambient"]["hours"],
            "n_positives": record[split]["positives"]["n"]}


def figure_keyword_curve() -> list[Path]:
    curve = keyword_curve("test")
    points, operating = curve["points"], curve["operating"]
    colours = {"swarm_hold": "#1f6feb", "swarm_abort": "#b45309"}

    figure, axes = plt.subplots(figsize=(7.2, 4.6))

    #: The interval first, so the curves draw over it. Shaded across the full height:
    #: it is an interval on the x-axis only, and a bar at one class's y would suggest
    #: it belonged to that class.
    low, high = curve["fa_ci95"]
    axes.axvspan(low, high, color="0.5", alpha=0.12, linewidth=0, zorder=0)
    #: Label inside the band, left of the budget line, so the line does not cross it.
    axes.text(low * 1.25, 0.045,
              "95% interval of the\nfalse-accept rate at the\noperating threshold",
              ha="left", va="top", fontsize=7, color="0.3")

    for key, label in KEYWORD_CLASSES.items():
        xs = [p["fa_per_hour_ambient"] for p in points]
        ys = [p["frr"][key] for p in points]
        n = curve["n_positives"][key]
        axes.plot(xs, ys, color=colours[key], linewidth=1.2, marker="o", markersize=2.5,
                  zorder=3, label=f"{label} (n = {n} test takes)")
        axes.scatter(operating["fa_per_hour_ambient"], operating["frr"][key], s=70,
                     facecolor="white", edgecolor=colours[key], linewidth=1.8, zorder=4)

    #: Two thresholds named on the curve, both read from the grid: the lowest, where
    #: the curve starts, and the operating one. Naming more would crowd the flat top.
    first = points[0]
    axes.annotate(f"threshold {first['threshold']:g}",
                  xy=(first["fa_per_hour_ambient"], first["frr"]["swarm_hold"]),
                  xytext=(0, 10), textcoords="offset points", ha="center",
                  fontsize=7, color="0.25")
    axes.annotate(f"operating threshold {curve['threshold']:g}\n"
                  f"{operating['fa_per_hour_ambient']:.2f} per hour; false rejects "
                  f"{operating['frr']['swarm_hold']:.3f} (hold), "
                  f"{operating['frr']['swarm_abort']:.3f} (abort)",
                  xy=(operating["fa_per_hour_ambient"], operating["frr"]["swarm_hold"]),
                  xytext=(14, 16), textcoords="offset points", ha="left", fontsize=7,
                  color="0.15", arrowprops=dict(arrowstyle="-", color="0.5", linewidth=0.6))

    axes.axvline(KEYWORD_FA_BUDGET_PER_HOUR, color="#b91c1c", linewidth=1.3, linestyle="--",
                 zorder=2)
    axes.text(KEYWORD_FA_BUDGET_PER_HOUR * 0.93, 0.082,
              f"false-accept budget\n{KEYWORD_FA_BUDGET_PER_HOUR:g} per hour",
              ha="right", va="top", fontsize=7, color="#b91c1c")
    axes.axhline(KEYWORD_FRR_BUDGET, color="#15803d", linewidth=1.2, linestyle=":", zorder=2)
    axes.text(max(p["fa_per_hour_ambient"] for p in points), KEYWORD_FRR_BUDGET + 0.002,
              f"false-reject budget {KEYWORD_FRR_BUDGET:.2f}", ha="right", va="bottom",
              fontsize=7, color="#15803d")

    #: Log x: the rates span 2.3 to 54 per hour, and the interval reaches down to 0.06.
    #: Every test point is above zero, so no point is lost to the log.
    axes.set_xscale("log")
    #: Plain numbers, not powers of ten: a rate of "0.1 per hour" reads without a
    #: conversion step, and the axis spans only three decades.
    axes.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    axes.set_xlim(low * 0.6, max(p["fa_per_hour_ambient"] for p in points) * 1.6)
    axes.set_ylim(-0.004, 0.118)
    axes.set_xlabel(f"False accepts per hour on ambient speech, both classes together "
                    f"({curve['hours']:.3f} h, test split)")
    axes.set_ylabel("False-reject rate (synthetic test takes)")
    axes.grid(True, which="both", linewidth=0.4, color="0.92", zorder=0)
    axes.set_axisbelow(True)
    for spine in ("top", "right"):
        axes.spines[spine].set_visible(False)
    axes.legend(loc="upper right", fontsize=7.5, frameon=True, framealpha=0.95,
                bbox_to_anchor=(1.0, 0.86))

    figure.tight_layout()
    written = []
    for suffix in (".pdf", ".png"):
        path = FIGURE_KEYWORD.with_suffix(suffix)
        figure.savefig(path, dpi=200)
        written.append(path)
    plt.close(figure)
    return written


def run() -> int:
    for path in figure_keyword_curve():
        print(f"wrote {_display(path)}")
    plottable, unmeasured = _points()
    for path in figure2():
        print(f"wrote {_display(path)}")
    print()
    for point in sorted(plottable, key=lambda p: p["p95_ms"]):
        frontier = "frontier " if point in pareto_frontier(plottable) else "dominated"
        print(f"  {frontier} {point['model']:24s} {point['quant']:7s} "
              f"EM {point['em']:.4f}  p95 {point['p95_ms']:8.2f} ms  "
              f"RSS {point['rss_mb'] / 1024:.2f} GiB")
    for point in unmeasured:
        print(f"  UNMEASURED {point['model']:24s} {point['quant']:7s} "
              f"EM {point['em']:.4f}  p95 -- (Exp-1 covers Q4_K_M only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
