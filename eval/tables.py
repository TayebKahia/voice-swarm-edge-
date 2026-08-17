#!/usr/bin/env python3
"""Render Tables 17 and 18 from the measured CSVs. No number is typed by hand.

Table 17 (model comparison, RQ1) and Table 18 (the quantisation delta, contribution C3)
are joins of two files that were produced on two different machines:

  train/kaggle_out/surface_a.csv  -- FP16 under `transformers`, measured on Kaggle
  results/surface_b.csv           -- the quantised GGUF under `llama.cpp` + GBNF

Table 17's latency columns (p50/p95, tok/s, peak RSS) come from a third file, produced on a
third machine:

  results/exp1_cooled.csv         -- per-trial timing/RSS/thermal rows from the Pi (eval/exp1.py),
                                     the cooled run of record; results/exp1.csv is its uncooled
                                     predecessor, reported in results/thermal_headroom.md

Exp-1 covers only the **Q4_K_M** configurations (STATE.md triage: 60 timed runs, not the PRD's
200, Q8_0 dropped from the hardware sweep). A Q8_0 row therefore keeps `--` in those columns
here -- not because the script forgot, but because nothing measured it. Table 19's Decode p95
is pooled over the same three Q4_K_M configs and is explicit that Q8_0 latency was never run.

Usage:
    python eval/tables.py
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

if __package__ in (None, ""):  # `python eval/tables.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.bench import aggregate, read_trials

REPO = Path(__file__).resolve().parent.parent
SURFACE_A = REPO / "train" / "kaggle_out" / "surface_a.csv"
SURFACE_B = REPO / "results" / "surface_b.csv"
SURFACE_B_NOGRAMMAR = REPO / "results" / "surface_b_nogrammar.csv"
#: Exp-1 of record. The PRD declares the target as a Raspberry Pi 5 with an **active
#: cooler** (PRD.tex:199) and names one as the mitigation for risk R-8, "thermal
#: throttling corrupts latency figures" (PRD.tex:1841). The first Exp-1 ran before the
#: cooler was fitted and throttled on 180/180 scored trials, so it measured a
#: configuration this project never declared. The cooled run is the protocol-compliant
#: measurement and the one these tables report.
EXP1 = REPO / "results" / "exp1_cooled.csv"
#: Kept, not discarded. NFR-10 must "always be reported" (prd.md:538), and the delta
#: between the two runs is itself a result: what sustained throttling costs a
#: sub-billion model on a passively-cooled Pi 5. Rendered by `thermal_headroom()`.
EXP1_THROTTLED = REPO / "results" / "exp1.csv"
RESULTS = REPO / "results"

SPLITS = ("test_synth", "test_golden", "test_ood")
#: The headline split for Table 18. The golden set is real recorded speech through the real
#: ASR, so it is the honest place to ask what quantisation costs; test_synth is TTS and
#: flatters every configuration equally.
DELTA_SPLIT = "test_golden"

#: Table 12, NFR-18.
FALSE_COMMAND_BUDGET = 0.05

#: Splits whose gold targets carry no slots at all, so slot-F1 has no dynamic range on them.
#: `test_ood` is the abstention set: 150 out-of-domain utterances whose gold is
#: `{"intent":"unknown"}` and nothing else -- 0 gold slot pairs across all 150 items. With
#: zero gold slots, true positives and false negatives are pinned at 0, so precision is 0
#: whenever the model emits any slot at all and `slot_micro_f1` can only ever return 0.0
#: (it emitted something) or `nan` (it emitted nothing). It cannot tell one spurious slot
#: apart from thirty-one, which is the only question worth asking on this split -- and
#: `false_command_rate` already answers it, on a scale that means something. Printing the
#: arithmetically-correct 0.0 next to 97.5 and 94.5 in the same column reads as a collapse
#: in slot filling that never happened, so Table 17 prints `--` instead.
NO_SLOT_SPLITS = ("test_ood",)


def _rows(path: Path) -> list[dict]:
    if not path.is_file():
        raise SystemExit(f"missing {path.relative_to(REPO)} -- run the sweep that writes it")
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _f(value: str) -> float | None:
    return float(value) if value not in ("", None) else None


def _pct(value: float | None, places: int = 1) -> str:
    return "--" if value is None else f"{100 * value:.{places}f}"


def _exp1_summaries(path: Path = EXP1) -> dict[str, dict]:
    """Exp-1 config (== a Q4_K_M gguf stem, e.g. `qwen2.5-0.5b-instruct-Q4_K_M`) -> summary.

    Warm-up rows are excluded by name (`<stem>-warmup`), never by discarding CSV rows --
    every request the Pi answered is still in the CSV for inspection. The path is a
    parameter so the same aggregation renders both the cooled run of record and the
    throttled one, with no second code path to keep in step.
    """
    if not path.is_file():
        return {}
    rows = [r for r in read_trials(path) if not r["config"].endswith("-warmup")]
    return {s["config"]: s for s in aggregate(rows)}


#: 2.4 GHz pinned by the `performance` governor / 1.5 GHz held under throttle (STATE.md, Exp-1).
CLOCK_RATIO = 2.4 / 1.5


def table17(surface_b: list[dict]) -> str:
    exp1 = _exp1_summaries()
    lines = [
        "### Table 17: Model comparison (Exp-1, RQ1)",
        "",
        "Surface B --- the quantised artefact under `llama.cpp` with the GBNF grammar, which is",
        "what the aircraft actually runs. Accuracy columns are from `results/surface_b.csv`;",
        f"latency, throughput and memory columns are `results/{EXP1.name}`, measured on",
        "the Pi with an active cooler fitted: 0 of 180 scored trials throttled, 67.5--74.1 C.",
        "The earlier uncooled run throttled on 180/180 and is reported separately, in the",
        "thermal-headroom table. p50/p95 is the SLM prefill and decode stages combined. Exp-1",
        "on the hardware covers only Q4_K_M -- a Q8_0 row keeps `--` because it was never measured",
        "on the hardware, not because the join failed. Slot-F1 is `--` on `test_ood` because that",
        "split carries no gold slots: its gold target is `{\"intent\":\"unknown\"}` on all 150 items,",
        "so the metric has no dynamic range there. What the models do emit on those items is",
        "reported properly by the false-command rate (NFR-18).",
        "",
        "| Model | Quant | Split | Intent-F1 | Slot-F1 | EM | Safe-fail | Schema-valid | p50/p95 (ms) | tok/s | Peak RSS |",
        "| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: | :--- |",
    ]
    for row in surface_b:
        summary = exp1.get(f"{row['model']}-{row['quant']}")
        if summary:
            p50 = summary.get("total_p50", "")
            p95 = summary.get("total_p95", "")
            latency = "--" if p50 == "" or p95 == "" else f"{p50}/{p95}"
            tok_s = summary.get("tokens_per_second", "--") or "--"
            rss = summary.get("peak_rss_mb", "")
            rss_str = "--" if rss == "" else f"{rss / 1024:.2f} GB"
        else:
            latency, tok_s, rss_str = "--", "--", "--"
        # `--`, not 0.0, where the split has no gold slots to score -- see NO_SLOT_SPLITS.
        slot_f1 = None if row["split"] in NO_SLOT_SPLITS else _f(row["slot_micro_f1"])
        lines.append(
            f"| {row['model']} | {row['quant']} | `{row['split']}` "
            f"| {_pct(_f(row['intent_macro_f1']))} "
            f"| {_pct(slot_f1)} "
            f"| {_pct(_f(row['exact_match']))} "
            f"| {_pct(_f(row['safe_failure_rate']))} "
            f"| {_pct(_f(row['schema_validity']))} | {latency} | {tok_s} | {rss_str} |"
        )
    return "\n".join(lines) + "\n"


def table18(surface_a: list[dict], surface_b: list[dict], split: str) -> str:
    fp16 = {r["model"]: _f(r["exact_match"]) for r in surface_a
            if r["surface"] == "A_fp16_finetuned" and r["split"] == split}
    lines = [
        f"### Table 18: Quantisation delta --- exact match on `{split}`",
        "",
        "Surface A is FP16 under `transformers` with no grammar. Surface B is the same",
        "adapter merged, converted and quantised, decoded by `llama.cpp` under the GBNF",
        "constraint. The delta therefore measures the *deployment pipeline*, not weight",
        "precision alone --- the grammar is part of what changes, and on out-of-domain input",
        "it is the dominant term.",
        "",
        "| Model | Quant | FP16 EM (surface A) | Quantised EM (surface B) | Delta (pp) |",
        "| :--- | :--- | ---: | ---: | ---: |",
    ]
    for row in surface_b:
        if row["split"] != split:
            continue
        before, after = fp16.get(row["model"]), _f(row["exact_match"])
        delta = "--" if before is None or after is None else f"{100 * (after - before):+.1f}"
        lines.append(f"| {row['model']} | {row['quant']} | {_pct(before)} | {_pct(after)} | {delta} |")
    return "\n".join(lines) + "\n"


def nfr18(surface_b: list[dict]) -> str:
    lines = [
        "### NFR-18: false-command rate on out-of-domain input",
        "",
        f"Budget: <= {FALSE_COMMAND_BUDGET:.2f}. Measured on `test_ood`, Surface B.",
        "",
        "| Model | Quant | False-command rate | Verdict |",
        "| :--- | :--- | ---: | :--- |",
    ]
    for row in surface_b:
        rate = _f(row.get("false_command_rate", ""))
        if rate is None:
            continue
        verdict = "MEETS" if rate <= FALSE_COMMAND_BUDGET else "**MISS**"
        lines.append(f"| {row['model']} | {row['quant']} | {rate:.4f} | {verdict} |")
    return "\n".join(lines) + "\n"


def _exp1_decode_p95_q4km() -> str:
    """Decode p95 pooled over every scored Exp-1 trial, all three Q4_K_M configs together.

    Exp-1 never ran Q8_0 on the Pi (STATE.md triage), so this is a Q4_K_M-only figure,
    not the six-artefact pool the accuracy columns are. Said explicitly in the caption
    rather than left for a reader to assume it covers what the EM columns cover.
    """
    if not EXP1.is_file():
        return "--"
    from eval.stats import nearest_rank
    rows = [r for r in read_trials(EXP1) if not r["config"].endswith("-warmup")]
    samples = [float(r["slm_decode_ms"]) for r in rows if r.get("slm_decode_ms") not in ("", None)]
    return f"{nearest_rank(samples, 95):.1f} ms" if samples else "--"


def table19(constrained: list[dict], ablated: list[dict]) -> str:
    """Table 19, the grammar ablation --- contribution C1 measured rather than asserted."""

    def totals(rows: list[dict]) -> tuple[int, int, float]:
        items = sum(int(r["n"]) for r in rows)
        valid = sum(_f(r["schema_validity"]) * int(r["n"]) for r in rows)
        matched = sum(_f(r["exact_match"]) * int(r["n"]) for r in rows)
        return items, round(items - valid), matched / items

    on_items, on_invalid, on_em = totals(constrained)
    off_items, off_invalid, off_em = totals(ablated)
    decode_p95 = _exp1_decode_p95_q4km()
    lines = [
        "### Table 19: Grammar ablation",
        "",
        "Same six artefacts, same 590 items, same greedy decode; the only change is whether",
        f"`llama.cpp` is given `schema/cmd.gbnf`. Decode p95 is `results/{EXP1.name}`, the Pi ---",
        "the workstation's decode time is not the deployed latency. It is pooled over the",
        "**three Q4_K_M configs only** (Exp-1 did not run Q8_0 on hardware); the grammar-off",
        "row has no Pi measurement at all -- the ablation itself only ran on the workstation.",
        "",
        "| Condition | Items | Schema validity | Malformed | EM (pooled) | Decode p95 |",
        "| :--- | ---: | ---: | ---: | ---: | :--- |",
        f"| Grammar on | {on_items} | {1 - on_invalid / on_items:.4f} | {on_invalid} "
        f"| {on_em:.4f} | {decode_p95} |",
        f"| Grammar off | {off_items} | {1 - off_invalid / off_items:.4f} | {off_invalid} "
        f"| {off_em:.4f} | -- |",
        "",
        "Pooled over every model, quantisation and split. Exact match is pooled by item, not",
        "averaged over the eighteen rows, so the larger splits carry their real weight.",
    ]
    return "\n".join(lines) + "\n"


def _model_meta() -> dict[str, dict]:
    """Per-model metadata (parameter count, family) from `train/configs/*.yaml`.

    Read rather than hardcoded, for the same reason every other number here is read:
    a parameter count typed into this file can drift from the config the model was
    actually trained under, and nothing would catch it. Requires PyYAML, which is in
    the project environment.
    """
    import yaml

    meta = {}
    for path in sorted((REPO / "train" / "configs").glob("*.yaml")):
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        if "params" not in cfg:
            raise SystemExit(f"{path.name} has no `params` -- Table 33 needs it")
        meta[cfg["name"]] = {"params": int(cfg["params"]), "family": cfg["family"]}
    return meta


def table33(surface_a: list[dict]) -> str:
    """Table 33 --- the Surface-A comparison across all four models.

    Not in prd.md's frozen table set (1-32), and deliberately separate from Table 17
    rather than folded into it: Table 17 reports Surface B, the quantised artefact
    that ships, and h2o-danube3 has no Surface B (scoped to the reference surface --
    see its config's scope_note). Putting a model with no Surface B into Table 17
    would mean a row of blanks in the table that answers RQ1.

    What this table exists for. The other three models sit at three parameter counts
    in three different families, so size and family are perfectly aliased and no
    pairwise comparison can separate them. h2o-danube3-500m is an iso-parameter
    control against qwen2.5-0.5b (514M vs 494M, different families, identical
    recipe), which splits the two effects apart for the first time.
    """
    meta = _model_meta()
    finetuned = [r for r in surface_a if r["surface"] == "A_fp16_finetuned"]
    by_model: dict[str, dict[str, float | None]] = {}
    for row in finetuned:
        by_model.setdefault(row["model"], {})[row["split"]] = _f(row["exact_match"])

    missing = [m for m in by_model if m not in meta]
    if missing:
        raise SystemExit(f"no config metadata for {missing} -- add params/family")

    order = sorted(by_model, key=lambda m: meta[m]["params"])
    lines = [
        "### Table 33: Surface-A model comparison, all four models",
        "",
        "FP16 under `transformers`, fine-tuned, greedy. Generated by `eval/tables.py` from",
        "`train/kaggle_out/surface_a.csv`; parameter counts and families from",
        "`train/configs/*.yaml`. Ordered by parameter count.",
        "",
        "| Model | Params | Family | " + " | ".join(SPLITS) + " |",
        "| :--- | ---: | :--- | " + " | ".join("---:" for _ in SPLITS) + " |",
    ]
    for model in order:
        cells = [f"{by_model[model].get(s):.4f}" if by_model[model].get(s) is not None
                 else "--" for s in SPLITS]
        lines.append(f"| `{model}` | {meta[model]['params'] / 1e6:,.0f} M | "
                     f"{meta[model]['family']} | " + " | ".join(cells) + " |")

    # The two contrasts the table exists to support, computed rather than asserted.
    lines += ["", "#### The two effects, separated", ""]
    pairs = []
    ranked = [(m, meta[m]["params"], by_model[m].get(DELTA_SPLIT)) for m in order]
    ranked = [r for r in ranked if r[2] is not None]

    # Iso-parameter: the closest pair by parameter count from different families.
    best = None
    for i, (m_a, p_a, e_a) in enumerate(ranked):
        for m_b, p_b, e_b in ranked[i + 1:]:
            if meta[m_a]["family"] == meta[m_b]["family"]:
                continue
            spread = abs(p_a - p_b) / min(p_a, p_b)
            if best is None or spread < best[0]:
                best = (spread, m_a, p_a, e_a, m_b, p_b, e_b)
    if best:
        _, m_a, p_a, e_a, m_b, p_b, e_b = best
        pairs.append(
            f"- **Family, at matched size** (`{m_a}` {p_a/1e6:,.0f} M vs `{m_b}` "
            f"{p_b/1e6:,.0f} M --- {_pct(abs(p_a - p_b) / min(p_a, p_b))}% apart): "
            f"**{abs(e_a - e_b) * 100:.1f} pp** on `{DELTA_SPLIT}` "
            f"({e_a:.4f} vs {e_b:.4f}).")

    # Size: the widest parameter spread available.
    lo, hi = ranked[0], ranked[-1]
    pairs.append(
        f"- **Size, across the full range** (`{lo[0]}` {lo[1]/1e6:,.0f} M vs `{hi[0]}` "
        f"{hi[1]/1e6:,.0f} M, {hi[1]/lo[1]:.1f}x): "
        f"**{(hi[2] - lo[2]) * 100:+.1f} pp** on `{DELTA_SPLIT}` "
        f"({lo[2]:.4f} -> {hi[2]:.4f}).")

    # Is the largest model bracketed by smaller ones? Stated only if true.
    largest = ranked[-1]
    better = [m for m, _, e in ranked[:-1] if e > largest[2]]
    if better:
        pairs.append(
            f"- **The largest model is not the best.** `{largest[0]}` "
            f"({largest[1]/1e6:,.0f} M, {largest[2]:.4f}) is beaten on `{DELTA_SPLIT}` by "
            + ", ".join(f"`{m}`" for m in better)
            + ". Parameter count does not order this table.")
    lines += pairs
    lines += [
        "",
        "Caveat carried from `train/configs/h2o-danube3-500m.yaml`: the recipe is frozen",
        "at three epochs for every model, and the per-epoch validation curves show",
        "`h2o-danube3-500m-chat` and `smollm2-360m-instruct` still improving at epoch 3",
        "while the other two have converged. Part of any gap is therefore convergence",
        "under a fixed budget rather than capability. The claim this table supports is",
        "about performance **under an identical three-epoch budget**, not about capability.",
        "",
    ]
    return "\n".join(lines)


def thermal_headroom(cooled: dict[str, dict], throttled: dict[str, dict]) -> str:
    """The cost of running the declared hardware without its declared cooler.

    Reports NFR-10 for both runs, which prd.md:538 requires be "always reported", and
    the per-configuration delta. The two runs are otherwise identical -- same board,
    same 60 scored trials per config after the same ten-minute warm-up, same pinned
    cores, same governor, same artefacts -- so the difference isolates cooling.
    """
    lines = [
        "### Thermal headroom --- the cooled run of record against the uncooled one",
        "",
        "`results/exp1_cooled.csv` (of record) against `results/exp1.csv`. Identical protocol:",
        "same board, same three Q4_K_M artefacts, 60 scored trials per configuration after a",
        "ten-minute warm-up, cores pinned to 1--3, `performance` governor, swap disabled. The",
        "only difference is the active cooler the hardware specification declares, which was",
        "not fitted for the first run. The delta therefore isolates cooling. Accuracy is unaffected and is not repeated here:",
        "Surface B is decoded greedily under a fixed grammar on the workstation, so it does",
        "not vary with the board's clock.",
        "",
        "| Config | Run | Throttled trials | Temp max | Decode p95 (ms) | SLM total p95 (ms) | tok/s |",
        "| :--- | :--- | :--- | ---: | ---: | ---: | ---: |",
    ]
    for config in sorted(cooled):
        for run, summaries in (("cooled", cooled), ("uncooled", throttled)):
            summary = summaries.get(config)
            if not summary:
                continue
            share = _f(summary.get("throttled_fraction"))
            lines.append(
                f"| {config} | {run} | {'--' if share is None else f'{100 * share:.0f}%'} "
                f"| {_f(summary.get('max_temperature_c')) or float('nan'):.1f} "
                f"| {_f(summary.get('slm_decode_p95')) or float('nan'):.1f} "
                f"| {_f(summary.get('total_p95')) or float('nan'):.1f} "
                f"| {_f(summary.get('tokens_per_second')) or float('nan'):.2f} |")

    lines += ["", "**NFR-10 (proportion of trials with a non-zero throttle flag, budget 5%).**"]
    for run, summaries, path in (("Cooled", cooled, "results/exp1_cooled.csv"),
                                 ("Uncooled", throttled, "results/exp1.csv")):
        shares = [_f(s.get("throttled_fraction")) for s in summaries.values()]
        shares = [v for v in shares if v is not None]
        if not shares:
            continue
        worst = max(shares)
        verdict = "MEETS" if worst <= 0.05 else "MISSES"
        lines.append(f"- {run} (`{path}`): worst configuration {100 * worst:.0f}% --- "
                     f"**{verdict}**.")

    deltas = []
    for config in sorted(cooled):
        hot, cold = throttled.get(config), cooled.get(config)
        if not (hot and cold):
            continue
        hot_p95, cold_p95 = _f(hot.get("slm_decode_p95")), _f(cold.get("slm_decode_p95"))
        hot_tps, cold_tps = _f(hot.get("tokens_per_second")), _f(cold.get("tokens_per_second"))
        if None in (hot_p95, cold_p95, hot_tps, cold_tps) or not (hot_p95 and hot_tps):
            continue
        deltas.append((config, 100 * (cold_p95 - hot_p95) / hot_p95,
                       100 * (cold_tps - hot_tps) / hot_tps))
    if deltas:
        lines += [
            "",
            "**What the cooler bought.** Decode p95 and throughput, cooled against uncooled:",
            "",
        ]
        lines += [f"- `{c}`: decode p95 {dp:+.1f}%, throughput {dt:+.1f}%."
                  for c, dp, dt in deltas]
        # Stated from the data, not asserted: an earlier version claimed the 1.6x clock
        # ratio bounded every gain, and smollm2's 1.685x throughput gain falsified it.
        largest = max(deltas, key=lambda d: d[2])[0]
        above = [c for c, _, dt in deltas if 1 + dt / 100 > CLOCK_RATIO]
        lines += [
            "",
            f"The effect is largest on `{largest}`. The uncooled run held 1.5 GHz against the",
            f"2.4 GHz the `performance` governor pins, a {CLOCK_RATIO:.1f}x clock ratio. "
            + (f"The throughput gain of {', '.join(f'`{c}`' for c in above)} exceeds that ratio, so "
               "the core clock alone does not account for the difference; this run does not "
               "identify the remaining term."
               if above else
               "No throughput gain reaches that ratio, so the clock is the dominant term but not "
               "the only one."),
            "",
        ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# LaTeX emission
#
# The thesis may not hand-copy a number out of a CSV into a `tabular` (the
# thesis-writing skill's rule 8, "never hand-type a number that a script could
# produce"). These renderers therefore convert the markdown each table function
# already returns, rather than formatting the numbers a second time: one code
# path decides what a cell says, so the `.md` under results/ and the `.tex` the
# chapter inputs cannot drift apart. A rule added to a table above --
# NO_SLOT_SPLITS, say -- reaches the PDF with no second edit.
# ---------------------------------------------------------------------------

#: Build products of the document, not measurements -- results/ holds what the
#: harness measured, and nothing here is a new number.
GENERATED = REPO / "thesis" / "generated"

_TEX_ESCAPES = (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"),
                ("}", r"\}"), ("~", r"\textasciitilde{}"),
                ("^", r"\textasciicircum{}"))


def _tex_escape(text: str) -> str:
    for char, replacement in _TEX_ESCAPES:
        text = text.replace(char, replacement)
    return text


#: Inline markdown emphasis, longest marker first so `**` is not eaten as two `*`.
_EMPHASIS = ((re.compile(r"\*\*(.+?)\*\*"), r"\\textbf{\1}"),
             (re.compile(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])"), r"\\emph{\1}"))


def _tex_cell(cell: str) -> str:
    """One markdown cell or caption line -> LaTeX.

    Backticks become \\texttt; `**x**` and `*x*` become \\textbf and \\emph. Emphasis is
    resolved before escaping, on the escaped fragments, so a literal underscore inside an
    emphasised run still reaches the PDF as an underscore.
    """
    out, parts = [], cell.strip().split("`")
    for index, part in enumerate(parts):
        if index % 2:
            out.append(r"\texttt{" + _tex_escape(part) + "}")
            continue
        text = _tex_escape(part)
        for pattern, replacement in _EMPHASIS:
            text = pattern.sub(replacement, text)
        out.append(text)
    return "".join(out)


def _align(spec: str) -> str:
    spec = spec.strip()
    if spec.startswith(":") and spec.endswith(":"):
        return "c"
    return "r" if spec.endswith(":") else "l"


#: Applied to LaTeX cells only, and only to *labels* -- never to a number. Table 17 carries
#: eleven columns and runs 52pt past the text block at full width; every model in this
#: project is an instruction-tuned checkpoint, so the suffix distinguishes nothing and
#: dropping it is what makes the table fit without shrinking the type further. The markdown
#: under results/ keeps the full artefact stem, because that is the measurement record.
_TEX_ABBREVIATIONS = (("-instruct", ""),)


def markdown_to_latex(markdown: str, label: str, size: str = r"\footnotesize",
                      colsep_pt: int = 4, abbreviate: bool = False) -> str:
    """Render the single pipe-table in `markdown` as a LaTeX table float.

    The prose above the table becomes the caption, because the skill asks captions to be
    self-contained: a reader must be able to read the table without the body text. Prose
    below the table (Table 33's three-epoch caveat, Table 19's pooled note) becomes a
    note under the rule, where it stays attached to the numbers it qualifies.
    """
    lines = markdown.splitlines()
    table = [l for l in lines if l.lstrip().startswith("|")]
    if len(table) < 3:
        raise ValueError(f"{label}: expected a header, a rule and at least one row")
    first, last = lines.index(table[0]), lines.index(table[-1])

    title = next((l.lstrip("# ").strip() for l in lines[:first] if l.startswith("#")), "")
    caption_lines = [l for l in lines[:first] if l.strip() and not l.startswith("#")]
    notes_lines = [l for l in lines[last + 1:] if l.strip()]

    def cell(text: str) -> str:
        if abbreviate:
            for long, short in _TEX_ABBREVIATIONS:
                text = text.replace(long, short)
        return _tex_cell(text)

    header = [cell(c) for c in table[0].strip().strip("|").split("|")]
    column_spec = "".join(_align(c) for c in table[1].strip().strip("|").split("|"))
    body = [[cell(c) for c in row.strip().strip("|").split("|")] for row in table[2:]]
    for index, row in enumerate(body):
        if len(row) != len(header):
            raise ValueError(
                f"{label}: row {index} has {len(row)} cells, header has {len(header)}")

    # Joined *before* conversion, not after: the markdown wraps at 90 columns, so a
    # `*run*` or a `` `path` `` in a caption routinely straddles a line break and a
    # per-line conversion would leave the marker in the PDF as a literal asterisk.
    # "Table 16:" is stripped: LaTeX numbers the float itself, and a heading used as the
    # caption would otherwise print as "Table 4.1: Table 16: ...".
    heading = _tex_cell(re.sub(r"^Table \d+:\s*", "", title))
    caption = _tex_cell(" ".join(caption_lines)) or heading
    # The List of Tables gets the heading, not the paragraph: a five-sentence entry with
    # an unbreakable \texttt{path} in it runs 60pt into the margin there.
    short = heading or caption
    rule = " " + chr(92) * 2
    out = [
        "% Generated by eval/tables.py -- do not edit; edit the renderer and re-run.",
        r"\begin{table}[htbp]",
        r"  \centering",
        "  " + size,
        r"  \setlength{\tabcolsep}{" + str(colsep_pt) + "pt}",
        r"  \caption[" + short + "]{" + caption + "}",
        r"  \label{" + label + "}",
        r"  \begin{tabular}{" + column_spec + "}",
        r"    \toprule",
        "    " + " & ".join(header) + rule,
        r"    \midrule",
    ]
    out += ["    " + " & ".join(row) + rule for row in body]
    out += [r"    \bottomrule", r"  \end{tabular}"]
    if notes_lines:
        out += [r"  \par\medskip",
                r"  \begin{minipage}{\textwidth}\footnotesize\raggedright "
                + _tex_cell(" ".join(notes_lines)) + r"\end{minipage}"]
    out += [r"\end{table}", ""]
    return "\n".join(out)



#: stem -> (LaTeX label, font size, \tabcolsep, abbreviate labels). Table 17 carries eleven
#: columns and needs both tighter settings; the rest are comfortable at footnotesize.
_TABLES = (
    ("table17_model_comparison", "tab:model-comparison", r"\scriptsize", 2, True),
    ("table18_quantisation_delta", "tab:quantisation-delta", r"\footnotesize", 5, False),
    ("nfr18_false_command", "tab:false-command", r"\footnotesize", 5, False),
    ("table19_grammar_ablation", "tab:grammar-ablation", r"\scriptsize", 3, False),
    ("table33_iso_parameter", "tab:iso-parameter", r"\footnotesize", 5, False),
    ("thermal_headroom", "tab:thermal-headroom", r"\scriptsize", 3, True),
)

#: Rendered to LaTeX here but computed elsewhere: `eval/exp0.py` owns Table 16 and writes
#: its markdown. Converting it here rather than duplicating the emitter in exp0.py keeps
#: one markdown-to-LaTeX path for the whole document, at the cost of this module reading a
#: file it does not produce -- which is why the read is tolerant of the file's absence.
_FOREIGN_TABLES = (
    ("table16_asr_speaker_sensitivity", "tab:asr-sensitivity", r"\scriptsize", 3, False),
)


def run() -> int:
    surface_a, surface_b = _rows(SURFACE_A), _rows(SURFACE_B)
    rendered = {
        "table17_model_comparison": table17(surface_b),
        "table18_quantisation_delta": table18(surface_a, surface_b, DELTA_SPLIT),
        "nfr18_false_command": nfr18(surface_b),
        "table19_grammar_ablation": table19(surface_b, _rows(SURFACE_B_NOGRAMMAR)),
        "table33_iso_parameter": table33(surface_a),
        "thermal_headroom": thermal_headroom(_exp1_summaries(),
                                             _exp1_summaries(EXP1_THROTTLED)),
    }
    written = []
    for stem, text in rendered.items():
        (RESULTS / f"{stem}.md").write_text(text, encoding="utf-8")
        written.append(f"results/{stem}.md")

    GENERATED.mkdir(parents=True, exist_ok=True)
    for stem, label, size, colsep, abbreviate in _TABLES:
        tex = markdown_to_latex(rendered[stem], label, size=size, colsep_pt=colsep,
                                abbreviate=abbreviate)
        (GENERATED / f"{stem}.tex").write_text(tex, encoding="utf-8")
        written.append(f"thesis/generated/{stem}.tex")

    for stem, label, size, colsep, abbreviate in _FOREIGN_TABLES:
        source = RESULTS / f"{stem}.md"
        if not source.is_file():
            print(f"  skipped {stem}: results/{stem}.md not written yet "
                  f"(run the experiment that owns it)")
            continue
        tex = markdown_to_latex(source.read_text(encoding="utf-8"), label, size=size,
                                colsep_pt=colsep, abbreviate=abbreviate)
        (GENERATED / f"{stem}.tex").write_text(tex, encoding="utf-8")
        written.append(f"thesis/generated/{stem}.tex")
    print("wrote " + ", ".join(written))
    return 0


if __name__ == "__main__":
    sys.exit(run())
