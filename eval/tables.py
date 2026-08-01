#!/usr/bin/env python3
"""Render Tables 17 and 18 from the measured CSVs. No number is typed by hand.

Table 17 (model comparison, RQ1) and Table 18 (the quantisation delta, contribution C3)
are joins of two files that were produced on two different machines:

  train/kaggle_out/surface_a.csv  -- FP16 under `transformers`, measured on Kaggle
  results/surface_b.csv           -- the quantised GGUF under `llama.cpp` + GBNF

Table 17's latency columns (p50/p95, tok/s, peak RSS) stay empty here on purpose: they are
Exp-1 on the Pi, and accuracy columns must not wait on hardware that is not the subject of
the accuracy claim. They are filled by the Exp-1 run, not by this script.

Usage:
    python eval/tables.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SURFACE_A = REPO / "train" / "kaggle_out" / "surface_a.csv"
SURFACE_B = REPO / "results" / "surface_b.csv"
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


def table17(surface_b: list[dict]) -> str:
    lines = [
        "### Table 17: Model comparison (Exp-1, RQ1)",
        "",
        "Surface B --- the quantised artefact under `llama.cpp` with the GBNF grammar, which is",
        "what the aircraft actually runs. Accuracy columns are from `results/surface_b.csv`;",
        "latency and memory columns are Exp-1 on the Pi and are filled by that run.",
        "",
        "| Model | Quant | Split | Intent-F1 | Slot-F1 | EM | Safe-fail | Schema-valid | p50/p95 | tok/s | Peak RSS |",
        "| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- | :--- |",
    ]
    for row in surface_b:
        lines.append(
            f"| {row['model']} | {row['quant']} | `{row['split']}` "
            f"| {_pct(_f(row['intent_macro_f1']))} "
            f"| {_pct(_f(row['slot_micro_f1']))} "
            f"| {_pct(_f(row['exact_match']))} "
            f"| {_pct(_f(row['safe_failure_rate']))} "
            f"| {_pct(_f(row['schema_validity']))} | -- | -- | -- |"
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


def run() -> int:
    surface_a, surface_b = _rows(SURFACE_A), _rows(SURFACE_B)
    written = []
    for name, text in (
        ("table17_model_comparison.md", table17(surface_b)),
        ("table18_quantisation_delta.md", table18(surface_a, surface_b, DELTA_SPLIT)),
        ("nfr18_false_command.md", nfr18(surface_b)),
    ):
        (RESULTS / name).write_text(text, encoding="utf-8")
        written.append(name)
    print("wrote " + ", ".join(f"results/{n}" for n in written))
    return 0


if __name__ == "__main__":
    sys.exit(run())
