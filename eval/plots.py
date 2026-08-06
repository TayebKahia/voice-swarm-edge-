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

3. **Every trial was thermally throttled.** All 180 scored Exp-1 trials ran at a
   1.5 GHz cap against a 2.4 GHz pinned target, no active cooler fitted (STATE.md,
   NFR-10 missed 100% against a 5% budget). The latency axis describes an uncooled
   Pi 5. This is stated on the figure because a Pareto plot invites the reader to
   treat the x-axis as a property of the model, and here it is partly a property of
   the enclosure.

Usage:
    python eval/plots.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")           # no display on the workstation or in CI
import matplotlib.pyplot as plt

if __package__ in (None, ""):   # `python eval/plots.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.bench import aggregate, read_trials

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results"
SURFACE_B = RESULTS / "surface_b.csv"
EXP1 = RESULTS / "exp1.csv"
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

MARKERS = {"llama-3.2-1b-instruct": "o", "qwen2.5-0.5b-instruct": "s",
           "smollm2-360m-instruct": "^"}


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
                 "em": float(row["exact_match"])}
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
                     marker=MARKERS.get(point["model"], "D"),
                     facecolor="white" if dominated else "#1f6feb",
                     edgecolor="#1f6feb", linewidth=1.6, zorder=3,
                     alpha=0.95)
        #: Label below the marker by default, above when a label below would land on
        #: the NFR-4 rule and make two unrelated things illegible at once.
        above = 0 < point["em"] - NFR4_EM < 0.10
        pad = 10 + (area(point["rss_mb"]) ** 0.5) / 2
        axes.annotate(
            f"{point['model'].replace('-instruct', '')} {point['quant']}\n"
            f"EM {point['em']:.3f} · p95 {point['p95_ms']:.0f} ms · "
            f"{point['rss_mb'] / 1024:.2f} GB",
            xy=(point["p95_ms"], point["em"]),
            xytext=(0, pad if above else -pad),
            textcoords="offset points", ha="center",
            va="bottom" if above else "top", fontsize=7.5, color="0.15")

    axes.axvline(SLM_BUDGET_MS, color="#b45309", linewidth=1.2, zorder=2)
    axes.text(SLM_BUDGET_MS - 95, 0.995, "Table 6 SLM budget 1,350 ms\n(same quantity as the axis)",
              rotation=90, ha="right", va="top", fontsize=7, color="#b45309")

    axes.axvline(NFR2_MS, color="#b91c1c", linewidth=1.4, linestyle="--", zorder=2)
    axes.text(NFR2_MS - 30, 0.995, "NFR-2 end-to-end 2,500 ms\n(axis is SLM stages only)",
              rotation=90, ha="right", va="top", fontsize=7, color="#b91c1c")

    axes.axhline(NFR4_EM, color="#15803d", linewidth=1.2, linestyle=":", zorder=2)
    axes.text(axes.get_xlim()[1] - 60, NFR4_EM - 0.010, "NFR-4  EM ≥ 0.85", ha="right",
              va="top", fontsize=7.5, color="#15803d")

    if unmeasured:
        names = "\n".join(f"  · {p['model'].replace('-instruct', '')} {p['quant']}"
                          f"  EM {p['em']:.3f}" for p in unmeasured)
        axes.text(0.015, 0.03,
                  "Not plotted — no Pi measurement exists\n"
                  "(Exp-1 scoped to Q4_K_M, Sat-19 triage):\n" + names,
                  transform=axes.transAxes, fontsize=7.5, va="bottom", ha="left",
                  color="0.25",
                  bbox=dict(boxstyle="round,pad=0.45", facecolor="#f6f6f6",
                            edgecolor="0.75", linewidth=0.7))

    throttled = {p["throttled"] for p in plottable}
    thermal = ("every trial thermally throttled (1.5 GHz cap, no active cooler)"
               if throttled == {1.0}
               else f"throttled fraction {min(throttled):.2f}–{max(throttled):.2f}")
    n_latency = {p["n_latency"] for p in plottable}

    axes.set_xlabel("SLM prefill + decode, p95 (ms) — Raspberry Pi 5, "
                    f"n = {min(n_latency)} timed runs per config")
    axes.set_ylabel(f"Exact match on `{SPLIT}` (n = 200 items)")
    axes.set_title("Figure 2 — Accuracy/latency Pareto frontier, Surface B\n"
                   + thermal, fontsize=10.5)
    axes.grid(True, linewidth=0.4, color="0.9", zorder=0)
    axes.set_axisbelow(True)
    axes.set_ylim(0.55, 1.0)
    axes.set_xlim(0, max(NFR2_MS, max(p["p95_ms"] for p in plottable)) * 1.12)
    for spine in ("top", "right"):
        axes.spines[spine].set_visible(False)

    #: A size legend, not a colour one: marker area is the only channel carrying RSS,
    #: and a reader cannot decode it from the points alone.
    handles = [axes.scatter([], [], s=area(mb), facecolor="white", edgecolor="0.4",
                            linewidth=1.2, label=f"{mb / 1024:.1f} GB peak RSS")
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
    axes.legend(handles=handles, loc="upper left", fontsize=7, frameon=True,
                borderpad=0.6, labelspacing=0.9, handletextpad=1.0, framealpha=0.95)

    figure.tight_layout()
    written = []
    for suffix in (".pdf", ".png"):
        path = FIGURE2.with_suffix(suffix)
        figure.savefig(path, dpi=200)
        written.append(path)
    plt.close(figure)
    return written


def run() -> int:
    plottable, unmeasured = _points()
    for path in figure2():
        print(f"wrote {_display(path)}")
    print()
    for point in sorted(plottable, key=lambda p: p["p95_ms"]):
        frontier = "frontier " if point in pareto_frontier(plottable) else "dominated"
        print(f"  {frontier} {point['model']:24s} {point['quant']:7s} "
              f"EM {point['em']:.4f}  p95 {point['p95_ms']:8.2f} ms  "
              f"RSS {point['rss_mb'] / 1024:.2f} GB")
    for point in unmeasured:
        print(f"  UNMEASURED {point['model']:24s} {point['quant']:7s} "
              f"EM {point['em']:.4f}  p95 -- (Exp-1 covers Q4_K_M only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
