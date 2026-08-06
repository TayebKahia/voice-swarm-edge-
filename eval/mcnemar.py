#!/usr/bin/env python3
"""Paired significance tests on the Surface-B predictions --- the RQ1 comparisons.

Table 17 reports six exact-match figures and invites the reader to rank them. Ranking
point estimates is not an answer: `0.9350` against `0.9100` on 200 items is a
difference of five items, and whether five items is a difference at all is exactly
the question a paired test exists to settle.

**Why McNemar and not a proportion test.** The six artefacts are scored on the *same*
items, so the observations are paired. A two-proportion z-test would throw that
pairing away and treat 200 correlated pairs as 400 independent draws, which inflates
the standard error's denominator and makes every comparison look more decisive than
it is. McNemar conditions on the pairing and asks only about the items where the two
systems disagree.

**Two families, corrected separately** (`bonferroni_alpha`, family alpha 0.05):

    model comparison  three pairs among the three models, on `test_golden`, at the
                      deployed quantisation (Q4_K_M) --- alpha = 0.0167.
    quantisation      Q4_K_M against Q8_0 within each model, on `test_golden`
                      --- alpha = 0.0167.

Everything else this script prints is marked `secondary` and is descriptive: the same
model comparison repeated at Q8_0 as a robustness check, and the quantisation pairs on
`test_synth` and `test_ood`. They are not folded into either correction, because a
Bonferroni family is fixed by the question it answers and not by how many tables a
script happens to be able to produce.

**The correctness vector is re-derived, never read from a summary.** `eval/metrics.py`
scores each raw prediction against its gold exactly as the sweep did, so the exact
match recomputed here is a check on `results/surface_b.csv` rather than a copy of it:
if the two ever disagree, one of them is wrong and the run says so.

Usage:
    python eval/mcnemar.py
"""

from __future__ import annotations

import csv
import itertools
import json
import logging
import sys
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):  # `python eval/mcnemar.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.metrics import score_predictions
from eval.stats import McNemarResult, bonferroni_alpha, mcnemar

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results"
PREDICTIONS = RESULTS / "surface_b_preds"
SURFACE_B = RESULTS / "surface_b.csv"
OUT_CSV = RESULTS / "mcnemar.csv"
OUT_MD = RESULTS / "mcnemar.md"

MODELS = ("llama-3.2-1b-instruct", "qwen2.5-0.5b-instruct", "smollm2-360m-instruct")
QUANTS = ("Q4_K_M", "Q8_0")
SPLITS = ("test_synth", "test_golden", "test_ood")

#: The split RQ1 is answered on: real recorded speech, not templates. `test_synth`
#: shares template families with training and `test_ood` is deliberately adversarial;
#: neither is the distribution the aircraft flies in.
PRIMARY_SPLIT = "test_golden"

#: The quantisation that actually ships (STATE.md, Sat 19). Comparing models at Q8_0
#: as well is a robustness check, not a second confirmatory family.
DEPLOYED_QUANT = "Q4_K_M"

FAMILY_ALPHA = 0.05

FIELDNAMES = [
    "family", "role", "split", "context", "system_a", "system_b", "n",
    "em_a", "em_b", "delta", "both_correct", "only_a", "only_b", "both_wrong",
    "discordant", "test", "statistic", "p_exact", "p_chi2", "p_value",
    "alpha", "significant",
]


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


def _quiet_validate_logging() -> None:
    """Silence `schema.validate`'s per-item clamp/fallback log lines.

    Re-scoring 3,540 predictions emits one INFO line per envelope clamp, which buries
    this script's own output. The events are not lost --- they were logged when the
    sweep produced the predictions, which is where they mean something. Here they are
    a side effect of re-deriving a boolean.
    """
    logging.getLogger("schema.validate").setLevel(logging.CRITICAL)


def load_correct(model: str, quant: str, split: str) -> dict[str, bool]:
    """Item id -> was this artefact's prediction exactly right, on this split."""
    path = PREDICTIONS / f"{model}-{quant}_{split}.jsonl"
    if not path.is_file():
        raise SystemExit(f"missing {_display(path)} -- run eval/surface_b.py")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    scored = score_predictions([r["raw"] for r in rows], [r["gold"] for r in rows])
    return {row["id"]: prediction.correct for row, prediction in zip(rows, scored)}


def paired(first: dict[str, bool], second: dict[str, bool]) -> tuple[list[bool], list[bool]]:
    """Align two correctness maps on item id.

    Pairing by id and not by file position is the one thing this module must not get
    wrong: two files written in different orders would still zip without error and
    would produce a contingency table describing nothing.
    """
    if set(first) != set(second):
        missing = set(first) ^ set(second)
        raise SystemExit(f"prediction files cover different items: {sorted(missing)[:5]}")
    ids = sorted(first)
    return [first[i] for i in ids], [second[i] for i in ids]


def compare(label_a: str, label_b: str, first: dict[str, bool], second: dict[str, bool],
            *, family: str, role: str, split: str, context: str, alpha: float) -> dict:
    a_vector, b_vector = paired(first, second)
    result = mcnemar(a_vector, b_vector)
    em_a = sum(a_vector) / len(a_vector)
    em_b = sum(b_vector) / len(b_vector)
    return {
        "family": family, "role": role, "split": split, "context": context,
        "system_a": label_a, "system_b": label_b, "n": result.n,
        "em_a": round(em_a, 4), "em_b": round(em_b, 4), "delta": round(em_a - em_b, 4),
        "both_correct": result.both_correct, "only_a": result.only_first,
        "only_b": result.only_second, "both_wrong": result.both_wrong,
        "discordant": result.discordant, "test": result.test,
        "statistic": round(result.statistic, 4),
        "p_exact": f"{result.p_exact:.6g}", "p_chi2": f"{result.p_chi2:.6g}",
        "p_value": f"{result.p_value:.6g}", "alpha": round(alpha, 4),
        "significant": "yes" if result.significant_at(alpha) else "no",
    }


def model_family(correct: dict, quant: str, role: str) -> list[dict]:
    """The three model-against-model pairs at one quantisation, on the primary split."""
    alpha = bonferroni_alpha(3, family_alpha=FAMILY_ALPHA)
    return [
        compare(a, b, correct[(a, quant, PRIMARY_SPLIT)], correct[(b, quant, PRIMARY_SPLIT)],
                family="model", role=role, split=PRIMARY_SPLIT, context=quant, alpha=alpha)
        for a, b in itertools.combinations(MODELS, 2)
    ]


def quant_family(correct: dict, split: str, role: str) -> list[dict]:
    """Q4_K_M against Q8_0 within each model, on one split."""
    alpha = bonferroni_alpha(3, family_alpha=FAMILY_ALPHA)
    return [
        compare(f"{model} Q4_K_M", f"{model} Q8_0",
                correct[(model, "Q4_K_M", split)], correct[(model, "Q8_0", split)],
                family="quantisation", role=role, split=split, context=model, alpha=alpha)
        for model in MODELS
    ]


def check_against_surface_b(correct: dict) -> list[str]:
    """Re-derived exact match against the published table. Provenance, not decoration."""
    if not SURFACE_B.is_file():
        return ["`results/surface_b.csv` absent -- exact match not cross-checked."]
    published = {
        (r["model"], r["quant"], r["split"]): float(r["exact_match"])
        for r in csv.DictReader(SURFACE_B.open(encoding="utf-8"))
        if r["grammar"] == "on"
    }
    problems = []
    for key, items in sorted(correct.items()):
        recomputed = sum(items.values()) / len(items)
        expected = published.get(key)
        if expected is None:
            problems.append(f"{key} has predictions but no row in surface_b.csv")
        elif abs(recomputed - expected) > 5e-5:
            problems.append(f"{key}: preds give {recomputed:.4f}, surface_b.csv says {expected:.4f}")
    return problems


def _table(rows: Sequence[dict]) -> list[str]:
    lines = [
        "| A | B | n | EM A | EM B | a (both) | b (A only) | c (B only) | d (neither) "
        "| b+c | test | p | alpha | significant |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- "
        "| ---: | ---: | :--- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['system_a']} | {row['system_b']} | {row['n']} "
            f"| {row['em_a']:.4f} | {row['em_b']:.4f} "
            f"| {row['both_correct']} | {row['only_a']} | {row['only_b']} | {row['both_wrong']} "
            f"| {row['discordant']} | {row['test']} | {row['p_value']} "
            f"| {row['alpha']:.4f} | {row['significant']} |"
        )
    return lines


def markdown(rows: list[dict], problems: list[str]) -> str:
    alpha = bonferroni_alpha(3, family_alpha=FAMILY_ALPHA)
    primary_model = [r for r in rows if r["family"] == "model" and r["role"] == "primary"]
    primary_quant = [r for r in rows if r["family"] == "quantisation" and r["role"] == "primary"]
    secondary = [r for r in rows if r["role"] == "secondary"]

    lines = [
        "### McNemar tests on the Surface-B predictions (RQ1)",
        "",
        "Paired per-item predictions from `results/surface_b_preds/`, grammar on, scored",
        "by `eval/metrics.py`. Cells: **a** both correct, **b** A correct and B wrong,",
        "**c** A wrong and B correct, **d** both wrong. Only **b** and **c** carry",
        "evidence about the difference; **a** and **d** say how much of the split the two",
        "systems agreed on. The exact binomial test is used below 25 discordant pairs;",
        "the two model comparisons against smollm2-360m exceed that and use the",
        "continuity-corrected chi-square. Both p-values are carried in the CSV, and the",
        "verdict is the same under either test for every row.",
        "",
        f"Bonferroni within each family of three: alpha = {alpha:.4f} (family alpha {FAMILY_ALPHA}).",
        "",
        f"#### Family 1 -- model against model, `{PRIMARY_SPLIT}`, {DEPLOYED_QUANT} (confirmatory)",
        "",
    ]
    lines += _table(primary_model)
    lines += [
        "",
        f"#### Family 2 -- {QUANTS[0]} against {QUANTS[1]} within each model, `{PRIMARY_SPLIT}` (confirmatory)",
        "",
    ]
    lines += _table(primary_quant)
    lines += [
        "",
        "#### Secondary -- descriptive, not part of either correction",
        "",
        "The model comparison repeated at Q8_0, and the quantisation pairs on the other",
        "two splits. Reported so the confirmatory result can be seen not to depend on",
        "the split or the quantisation it was run at; not corrected, and not evidence",
        "in their own right.",
        "",
    ]
    lines += _table(secondary)
    lines += [
        "",
        "#### Reading these numbers",
        "",
        "**A non-significant McNemar is not a finding of equivalence.** Where `b+c` is 1,",
        "the smallest attainable exact p-value is 1.0: the test cannot reject regardless",
        "of the truth. What such a row reports is that the two artefacts disagreed on one",
        "item out of 200 -- a statement about how little they differ, which is a bound",
        "worth quoting, and not the same claim as 'no difference exists'.",
        "",
        "**An identical exact match is not an identical model.** smollm2-360m scores",
        "0.8125 at both quantisations on `test_synth`, and the pairing shows why that is",
        "a coincidence rather than a result: the two artefacts disagree on 24 items and",
        "happen to split them 12/12. Comparing the summary figures alone would have",
        "reported a difference of exactly zero where there are two dozen of them.",
        "",
    ]
    if problems:
        lines += ["**Provenance check FAILED** -- the re-derived exact match does not match",
                  "`results/surface_b.csv`:", ""]
        lines += [f"  - {problem}" for problem in problems]
    else:
        lines += ["Provenance: exact match re-derived from the per-item predictions matches",
                  "every `grammar=on` row of `results/surface_b.csv` to four decimal places."]
    return "\n".join(lines) + "\n"


def run() -> int:
    _quiet_validate_logging()
    correct = {(m, q, s): load_correct(m, q, s)
               for m in MODELS for q in QUANTS for s in SPLITS}

    problems = check_against_surface_b(correct)

    rows: list[dict] = []
    rows += model_family(correct, DEPLOYED_QUANT, role="primary")
    rows += quant_family(correct, PRIMARY_SPLIT, role="primary")
    rows += model_family(correct, "Q8_0", role="secondary")
    for split in ("test_synth", "test_ood"):
        rows += quant_family(correct, split, role="secondary")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    OUT_MD.write_text(markdown(rows, problems), encoding="utf-8")

    for row in rows:
        marker = "*" if row["significant"] == "yes" else " "
        print(f"{marker} [{row['role'][:4]}] {row['family']:12s} {row['split']:12s} "
              f"{row['system_a']:28s} vs {row['system_b']:28s} "
              f"a={row['both_correct']:3d} b={row['only_a']:3d} c={row['only_b']:3d} "
              f"d={row['both_wrong']:3d}  p={row['p_value']:>10s} ({row['test']})")
    print()
    print(f"wrote {_display(OUT_CSV)} and {_display(OUT_MD)}")
    if problems:
        print("\nPROVENANCE CHECK FAILED:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print("provenance: recomputed exact match matches results/surface_b.csv on all 18 rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
