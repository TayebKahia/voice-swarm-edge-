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


def run() -> int:
    surface_a, surface_b = _rows(SURFACE_A), _rows(SURFACE_B)
    written = []
    for name, text in (
        ("table17_model_comparison.md", table17(surface_b)),
        ("table18_quantisation_delta.md", table18(surface_a, surface_b, DELTA_SPLIT)),
        ("nfr18_false_command.md", nfr18(surface_b)),
        ("table19_grammar_ablation.md", table19(surface_b, _rows(SURFACE_B_NOGRAMMAR))),
    ):
        (RESULTS / name).write_text(text, encoding="utf-8")
        written.append(name)
    print("wrote " + ", ".join(f"results/{n}" for n in written))
    return 0


if __name__ == "__main__":
    sys.exit(run())
