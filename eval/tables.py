#!/usr/bin/env python3
"""Render Tables 17 and 18 from the measured CSVs. No number is typed by hand.

Table 17 (model comparison, RQ1) and Table 18 (the quantisation delta, contribution C3)
are joins of two files that were produced on two different machines:

  train/kaggle_out/surface_a.csv  -- FP16 under `transformers`, measured on Kaggle
  results/surface_b.csv           -- the quantised GGUF under `llama.cpp` + GBNF

Table 17's latency columns (p50/p95, tok/s, peak RSS) come from a third file, produced on a
third machine:

  results/exp1.csv                -- per-trial timing/RSS/thermal rows from the Pi (eval/exp1.py)

Exp-1 covers only the **Q4_K_M** configurations (STATE.md triage: 60 timed runs, not the PRD's
200, Q8_0 dropped from the hardware sweep). A Q8_0 row therefore keeps `--` in those columns
here -- not because the script forgot, but because nothing measured it. Table 19's Decode p95
is pooled over the same three Q4_K_M configs and is explicit that Q8_0 latency was never run.

Usage:
    python eval/tables.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

if __package__ in (None, ""):  # `python eval/tables.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.bench import aggregate, read_trials

REPO = Path(__file__).resolve().parent.parent
SURFACE_A = REPO / "train" / "kaggle_out" / "surface_a.csv"
SURFACE_B = REPO / "results" / "surface_b.csv"
SURFACE_B_NOGRAMMAR = REPO / "results" / "surface_b_nogrammar.csv"
EXP1 = REPO / "results" / "exp1.csv"
RESULTS = REPO / "results"

SPLITS = ("test_synth", "test_golden", "test_ood")
#: The headline split for Table 18. The golden set is real recorded speech through the real
#: ASR, so it is the honest place to ask what quantisation costs; test_synth is TTS and
#: flatters every configuration equally.
DELTA_SPLIT = "test_golden"

#: Table 12, NFR-18.
FALSE_COMMAND_BUDGET = 0.05


def _rows(path: Path) -> list[dict]:
    if not path.is_file():
        raise SystemExit(f"missing {path.relative_to(REPO)} -- run the sweep that writes it")
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _f(value: str) -> float | None:
    return float(value) if value not in ("", None) else None


def _pct(value: float | None, places: int = 1) -> str:
    return "--" if value is None else f"{100 * value:.{places}f}"


def _exp1_summaries() -> dict[str, dict]:
    """Exp-1 config (== a Q4_K_M gguf stem, e.g. `qwen2.5-0.5b-instruct-Q4_K_M`) -> summary.

    Warm-up rows are excluded by name (`<stem>-warmup`), never by discarding CSV rows --
    every request the Pi answered is still in `results/exp1.csv` for inspection.
    """
    if not EXP1.is_file():
        return {}
    rows = [r for r in read_trials(EXP1) if not r["config"].endswith("-warmup")]
    return {s["config"]: s for s in aggregate(rows)}


def table17(surface_b: list[dict]) -> str:
    exp1 = _exp1_summaries()
    lines = [
        "### Table 17: Model comparison (Exp-1, RQ1)",
        "",
        "Surface B --- the quantised artefact under `llama.cpp` with the GBNF grammar, which is",
        "what the aircraft actually runs. Accuracy columns are from `results/surface_b.csv`;",
        "latency, throughput and memory columns are `results/exp1.csv`, measured on the Pi.",
        "p50/p95 is SLM prefill+decode combined (Table 6's two SLM rows summed). Exp-1 covers",
        "only Q4_K_M (STATE.md triage) -- a Q8_0 row keeps `--` because it was never measured",
        "on the hardware, not because the join failed.",
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
        lines.append(
            f"| {row['model']} | {row['quant']} | `{row['split']}` "
            f"| {_pct(_f(row['intent_macro_f1']))} "
            f"| {_pct(_f(row['slot_micro_f1']))} "
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
        "`llama.cpp` is given `schema/cmd.gbnf`. Decode p95 is `results/exp1.csv`, the Pi ---",
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


def run() -> int:
    surface_a, surface_b = _rows(SURFACE_A), _rows(SURFACE_B)
    written = []
    for name, text in (
        ("table17_model_comparison.md", table17(surface_b)),
        ("table18_quantisation_delta.md", table18(surface_a, surface_b, DELTA_SPLIT)),
        ("nfr18_false_command.md", nfr18(surface_b)),
        ("table19_grammar_ablation.md", table19(surface_b, _rows(SURFACE_B_NOGRAMMAR))),
        ("table33_iso_parameter.md", table33(surface_a)),
    ):
        (RESULTS / name).write_text(text, encoding="utf-8")
        written.append(name)
    print("wrote " + ", ".join(f"results/{n}" for n in written))
    return 0


if __name__ == "__main__":
    sys.exit(run())
