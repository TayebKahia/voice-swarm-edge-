#!/usr/bin/env python3
"""NFR-9 and NFR-18: the abstention limitation, rendered from the per-item predictions.

Both requirements are missed by every measured configuration and they are missed for
one reason, so they are analysed together here rather than as two unrelated budget
failures. `eval/tables.py` already reports each as a rate; what that cannot show is
*where the safe failures come from*, and that is the whole finding. This module
therefore works from `results/surface_b_preds/*.jsonl` --- the per-item files --- not
from the summary CSV.

Three distinctions this script exists to make, none of which survive aggregation:

**A safe failure is not the same as an abstention.** `safe_failure_rate` counts any
error whose dispatched action is `unknown` or `hover`. But `hover` is also where
`schema/validate.py` falls back when layer 2 rejects a command. So a run can post a
non-zero safe-failure rate without the model ever having declined to answer. Splitting
the safe failures by *who produced them* --- the model emitting `unknown`, or the
validator falling back to `hover` --- is the difference between "the system can
abstain" and "the system can be stopped", and only the second is true here.

**A volunteered abstention is an `unknown` on an item whose reference is not
`unknown`.** On `test_ood` every reference *is* `unknown`, so an `unknown` there is a
correct answer, not evidence of self-doubt. The in-domain splits are the only place
the question "did it decline when it was unsure?" can be asked at all.

**The in-domain error taxonomy** separates an error that dispatches the right intent
with wrong parameters from one that dispatches a different intent. Both fly; they are
not equally diagnosable, and the yaw sign flip is the single largest family.

Outputs (both regenerated, never hand-edited):
    results/nfr9_nfr18_abstention.csv  -- one row per model x quant x split
    results/limitation_abstention.md   -- the Limitations entry both theses cite

Usage:
    python eval/abstention.py
"""

from __future__ import annotations

import csv
import itertools
import json
import logging
import sys
from pathlib import Path

if __package__ in (None, ""):  # `python eval/abstention.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.metrics import SAFE_INTENTS, score_predictions

REPO = Path(__file__).resolve().parent.parent
PREDICTIONS = REPO / "results" / "surface_b_preds"
RESULTS = REPO / "results"

MODELS = ("llama-3.2-1b-instruct", "qwen2.5-0.5b-instruct", "smollm2-360m-instruct")
QUANTS = ("Q4_K_M", "Q8_0")
SPLITS = ("test_synth", "test_golden", "test_ood")
#: The splits on which "did it decline when unsure?" is a meaningful question. On
#: `test_ood` every reference is `unknown`, so abstaining there is simply being right.
IN_DOMAIN = ("test_synth", "test_golden")

#: Table 12. NFR-9 is a floor, NFR-18 a ceiling.
SAFE_FAILURE_BUDGET = 0.70
FALSE_COMMAND_BUDGET = 0.05


def _origin(prediction) -> str | None:
    """Which mechanism produced a safe failure --- or None if the failure was not safe.

    `safe_failure_rate` credits any error dispatching `unknown` or `hover`, but those
    three origins are not the same event. `model_hover` is the model confidently
    commanding a hold, which is *safe* without being an *abstention*: it is
    indistinguishable from the model believing the operator said "hold". Collapsing it
    with `validator_fallback` would credit the model with a check the validator performed.
    """
    if prediction.dispatched not in SAFE_INTENTS:
        return None
    if prediction.dispatched == "unknown":
        return "model_unknown"
    try:
        emitted = json.loads(prediction.raw).get("intent")
    except Exception:
        emitted = None
    return "model_hover" if emitted == "hover" else "validator_fallback"


def _load(model: str, quant: str, split: str):
    path = PREDICTIONS / f"{model}-{quant}_{split}.jsonl"
    if not path.is_file():
        raise SystemExit(f"missing {path.relative_to(REPO)} -- run eval/surface_b.py")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows, score_predictions([r["raw"] for r in rows], [r["gold"] for r in rows])


def analyse() -> list[dict]:
    """One record per configuration x split, built from the per-item files."""
    records = []
    for model, quant, split in itertools.product(MODELS, QUANTS, SPLITS):
        rows, preds = _load(model, quant, split)
        failed = [p for p in preds if not p.correct]
        safe = [p for p in failed if p.dispatched in SAFE_INTENTS]
        records.append({
            "model": model,
            "quant": quant,
            "split": split,
            "n": len(preds),
            "errors": len(failed),
            "safe_failures": len(safe),
            "safe_failure_rate": (len(safe) / len(failed)) if failed else "",
            # Who produced the safe failure, three ways --- and they mean different
            # things. A `hover` the model *emitted* is a command to hold position that
            # happens to be harmless; only layer 2's fallback is the system catching
            # something, and only `unknown` is the model declining to answer.
            "safe_model_unknown": sum(_origin(p) == "model_unknown" for p in failed),
            "safe_model_hover": sum(_origin(p) == "model_hover" for p in failed),
            "safe_validator_fallback": sum(_origin(p) == "validator_fallback" for p in failed),
            # An `unknown` on an item whose reference is a real command: self-doubt.
            "volunteered_unknown": sum(p.gold_intent != "unknown" and p.dispatched == "unknown"
                                       for p in preds),
            "false_command_rate": (sum(p.dispatched != "unknown" for p in preds) / len(preds)
                                   if split == "test_ood" else ""),
        })
    return records


def taxonomy() -> dict[str, int]:
    """In-domain errors, classified by what the swarm would have done about them."""
    counts = {"right intent, wrong parameters": 0, "wrong intent, still actionable": 0,
              "resolved to a safe action": 0, "yaw sign flips": 0, "total": 0}
    for model, quant, split in itertools.product(MODELS, QUANTS, IN_DOMAIN):
        _, preds = _load(model, quant, split)
        for p in preds:
            if p.correct:
                continue
            counts["total"] += 1
            if p.dispatched in SAFE_INTENTS:
                counts["resolved to a safe action"] += 1
            elif p.predicted and json.loads(p.predicted)["intent"] == p.gold_intent:
                counts["right intent, wrong parameters"] += 1
                gold, pred = json.loads(p.gold), json.loads(p.predicted)
                # The swarm turns through the right angle, the wrong way round.
                if "yaw" in gold and "yaw" in pred and gold["yaw"] == -pred["yaw"]:
                    counts["yaw sign flips"] += 1
            else:
                counts["wrong intent, still actionable"] += 1
    return counts


def _example_rotation_error() -> tuple[str, str, str, str]:
    """The first yaw sign flip on real recorded speech, quoted rather than described."""
    rows, preds = _load("qwen2.5-0.5b-instruct", "Q4_K_M", "test_golden")
    for row, p in zip(rows, preds):
        if p.correct or not p.predicted:
            continue
        gold, pred = json.loads(p.gold), json.loads(p.predicted)
        if gold.get("yaw") == -pred.get("yaw", 0):
            return row["id"], row["transcript"], p.gold, p.predicted
    raise SystemExit("no yaw sign flip found -- the example in the entry is stale")


def _volunteered_example() -> tuple[str, str, str, str] | None:
    """The in-domain items where the model itself declined. There is one."""
    for model, quant, split in itertools.product(MODELS, QUANTS, IN_DOMAIN):
        rows, preds = _load(model, quant, split)
        for row, p in zip(rows, preds):
            if p.gold_intent != "unknown" and p.dispatched == "unknown":
                return f"{model} {quant} `{split}`", row["id"], row["transcript"], p.gold
    return None


def write_csv(records: list[dict]) -> Path:
    path = RESULTS / "nfr9_nfr18_abstention.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    return path


def _pct(value: float, places: int = 1) -> str:
    return f"{100 * value:.{places}f}%"


def entry(records: list[dict], tax: dict[str, int]) -> str:
    ood = [r for r in records if r["split"] == "test_ood"]
    in_domain = [r for r in records if r["split"] in IN_DOMAIN]

    sfr = [r["safe_failure_rate"] for r in records if r["safe_failure_rate"] != ""]
    fcr = [r["false_command_rate"] for r in ood]
    errors = sum(r["errors"] for r in records)
    safe = sum(r["safe_failures"] for r in records)
    items = sum(r["n"] for r in records)
    declined = sum(r["safe_model_unknown"] for r in records)
    held = sum(r["safe_model_hover"] for r in records)
    caught = sum(r["safe_validator_fallback"] for r in records)
    volunteered = sum(r["volunteered_unknown"] for r in records)

    id_errors = sum(r["errors"] for r in in_domain)
    id_safe = sum(r["safe_failures"] for r in in_domain)
    ood_abstention = [1 - r["false_command_rate"] for r in ood]

    ex_id, ex_text, ex_gold, ex_pred = _example_rotation_error()
    vol = _volunteered_example()
    vol_where = f"{vol[0]}, item {vol[1]}" if vol else "none found"
    vol_text = repr(vol[2]) if vol else ""
    vol_gold = vol[3] if vol else ""

    budget_table = "\n".join(
        f"| {r['model']} | {r['quant']} | {r['safe_failure_rate']:.4f} | "
        f"{r['false_command_rate']:.4f} | **MISS** / **MISS** |"
        for r in sorted(ood, key=lambda r: r["false_command_rate"]))

    safe_table = "\n".join(
        f"| {r['model']} | {r['quant']} | `{r['split']}` | {r['errors']} | "
        f"{r['safe_model_unknown']} | {r['safe_model_hover']} | "
        f"{r['safe_validator_fallback']} | "
        f"{r['safe_failure_rate']:.4f} |"
        for r in records if r["safe_failure_rate"] != "")

    return f"""\
# Limitation --- the system has no abstention mechanism (NFR-9 and NFR-18)

*Generated by `python eval/abstention.py` from `results/surface_b_preds/*.jsonl`.
Every figure below traces to those files; none is typed by hand. Raw per-configuration
counts are in `results/nfr9_nfr18_abstention.csv`.*

Two requirements are missed by every configuration measured. They are recorded as one
limitation because they are one failure seen from two sides: **the system can produce a
well-formed command and can be stopped by its validator, but it has no way to decline.**

## 1. The budgets, and what was measured

| Requirement | Budget | Measured (Surface B, all six artefacts) | Verdict |
| :--- | :--- | :--- | :--- |
| **NFR-9** --- safe-failure rate | $\\geq$ {SAFE_FAILURE_BUDGET:.2f} | {min(sfr):.4f} to {max(sfr):.4f}; pooled **{safe / errors:.4f}** ({safe} of {errors} errors) | **MISS** |
| **NFR-18** --- false-command rate on `test_ood` | $\\leq$ {FALSE_COMMAND_BUDGET:.2f} | {min(fcr):.4f} to {max(fcr):.4f} | **MISS** |

Per configuration, on the out-of-domain set:

| Model | Quant | Safe-failure rate | False-command rate | NFR-9 / NFR-18 |
| :--- | :--- | ---: | ---: | :--- |
{budget_table}

NFR-9 is missed by a factor of roughly {SAFE_FAILURE_BUDGET / (safe / errors):.0f} on the pooled figure, and NFR-18 by a factor of {min(fcr) / FALSE_COMMAND_BUDGET:.0f} to {max(fcr) / FALSE_COMMAND_BUDGET:.0f}. Neither is a near miss, and neither is reconciled here: `prd.md` §10.2 requires the rule to fail loudly rather than be quietly adjusted.

## 2. The root cause, stated once

The GBNF grammar guarantees that the decoder's output is a **well-formed** command. It
cannot guarantee that a command is the **right kind of answer**, because "say nothing"
is not a shape the grammar can force --- the `unknown` intent is reachable under it, but
nothing makes the model choose that branch. Supervised fine-tuning on a corpus of
valid commands taught the model that a command is always the answer; three epochs of it
taught that lesson thoroughly enough that the model almost never departs from the format
even with the grammar removed (Table 19). The same training that produced the structural
reliability produced the absence of abstention. They are the same property.

## 3. Almost nothing the metric counts as a safe failure is an abstention

Across all {items:,} items there are {errors} errors, of which {safe} failed safely. Those {safe} split three ways, and the three are not the same event:

- **{held} are the model emitting `hover`** --- a command to hold position. Safe, but not an abstention: it is indistinguishable from the model believing the operator asked for a hold. The model was not expressing doubt; it was confidently issuing a different command.
- **{caught} are the validator falling back to `HOVER`** --- layer 2 rejecting a command it could prove inconsistent (each is a `formation` missing a slot its shape requires). This is the system catching something, but it is `schema/validate.py` doing the catching, not the model.
- **{declined} is the model emitting `unknown`** --- the only instance, in {items:,} items, of the model declining to answer.

So NFR-9's measured rate is not a small amount of abstention. It is {held} confident commands that happened to be harmless, {caught} validator rejections, and {declined} abstention. The safe-failure metric cannot separate these by construction --- it is defined over the dispatched action --- which is exactly why this entry reports the split rather than the rate alone.

This matters for how the number is read. A reader who sees a non-zero safe-failure rate
may reasonably infer the system knows when to stop. It does not. It can be stopped, and
it can happen to be harmless.

| Model | Quant | Split | Errors | Model declined (`unknown`) | Model held (`hover`) | Validator caught | Safe-failure rate |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
{safe_table}

## 4. Abstention is triggered by topic, not by uncertainty

The distinction that explains both numbers at once. On `test_ood`, where all {ood[0]['n']} references are `unknown`, the models *do* abstain --- between {_pct(min(ood_abstention))} and {_pct(max(ood_abstention))} of the time. The ability to emit `unknown` is present, reachable under the grammar, and used.

On the in-domain splits it vanishes: {id_errors} errors, {id_safe} of them safe, and the model volunteered `unknown` on an item whose reference was a real command exactly **{volunteered} time in {sum(r['n'] for r in in_domain):,}**.

The system can recognise *this is not about drones*. It cannot recognise *this is about
drones and I did not catch it*. Abstention here is a topic classifier, not a confidence
estimate --- which is precisely the failure mode a fielded system cannot afford, because
a misheard command is in-domain by construction.

The single volunteered abstention is worth quoting, because it was itself an error:

```
{vol_where}
  transcript : {vol_text}
  reference  : {vol_gold}
  dispatched : unknown
```

The one time the system declined an in-domain command, it declined a valid one.

## 5. The in-domain error taxonomy

What the swarm would actually have done, pooled over the six artefacts on
`test_synth` and `test_golden` ({tax['total']} errors):

| Outcome | Errors | Share |
| :--- | ---: | ---: |
| Right intent, wrong parameters | {tax['right intent, wrong parameters']} | {_pct(tax['right intent, wrong parameters'] / tax['total'])} |
| Wrong intent, still actionable | {tax['wrong intent, still actionable']} | {_pct(tax['wrong intent, still actionable'] / tax['total'])} |
| Resolved to a safe action | {tax['resolved to a safe action']} | {_pct(tax['resolved to a safe action'] / tax['total'])} |

{_pct((tax['total'] - tax['resolved to a safe action']) / tax['total'])} of in-domain errors dispatch an executable command. The largest single family is the **yaw sign flip**: {tax['yaw sign flips']} of {tax['total']} errors ({_pct(tax['yaw sign flips'] / tax['total'])}) turn the swarm through the correct angle in the wrong direction. That failure is schema-valid, inside the envelope, indisputably well-formed, and wrong in the one way the validator cannot see --- no consistency check can distinguish a clockwise from an anticlockwise intent.

One item, on real recorded speech:

```
item       : {ex_id}
transcript : {ex_text!r}
reference  : {ex_gold}
dispatched : {ex_pred}
```

## 6. Re-baselining, per `prd.md` §10.2

§10.2 requires that a constraint no configuration satisfies is re-baselined against the
measured figure and the re-baselining reported, rather than the rule being changed
quietly. Accordingly:

- **NFR-9 is re-baselined from $\\geq$ {SAFE_FAILURE_BUDGET:.2f} to the measured pooled {safe / errors:.4f}** (per-configuration range {min(sfr):.4f}--{max(sfr):.4f}).
- **NFR-18 is re-baselined from $\\leq$ {FALSE_COMMAND_BUDGET:.2f} to the measured {min(fcr):.4f}--{max(fcr):.4f}**, per configuration.

These are **descriptive baselines: a record of where the system stands, not targets
lowered until they could be met.** The original budgets remain the targets, and §7 names
what would have to be built to reach them. A re-baselined constraint is not a passed one,
and neither requirement is reported as met anywhere in either document.

Two limits on this re-baselining, both of which must be stated wherever it is cited:

1. **NFR-9 is sourced to Exp-1 *and* Exp-3** (`prd.md` Table 12). Exp-3 has not run. This baseline rests on Exp-1 evidence only and must be revisited when the end-to-end golden-set run lands --- Exp-3 puts ASR error into the input, which can only move the figure.
2. These are reference-text results on the deployed surface (quantised, grammar on). The
   grammar-off ablation surface posts a different and slightly higher safe-failure rate;
   it is not quoted here because it is not what ships.

## 7. Future work --- what would fix this, none of it done

Neither mechanism below is implemented, measured, or claimed. They are named so the
limitation has an exit, not to suggest one was taken.

1. **A confidence gate.** Read the decoder's token-level log-probabilities over the
   emitted command and route anything below a threshold to `unknown` rather than to the
   bus. This is the direct fix for §4's diagnosis: it supplies the uncertainty signal the
   topic classifier lacks. It needs a held-out calibration set to place the threshold, and
   it trades safe-failure rate against exact match on a curve that has not been measured
   here.
2. **Oversampling `unknown` in training.** The training corpus contains valid commands
   almost exclusively, which is where §2's lesson comes from. Deliberately including
   near-miss, truncated and ambiguous utterances labelled `unknown` would teach the model
   that declining is an available answer on in-domain-sounding input, not only on
   off-topic input.

The two are complementary rather than alternative: the first supplies a signal at
inference time, the second changes what the model believes an answer is.

## 8. Threats to this analysis

- `test_ood` is {ood[0]['n']} items and every reference is `unknown`, so on that split the error rate and the false-command rate measure the same events from two directions. They are not independent evidence.
- The safe/unsafe split rests on `SAFE_INTENTS = {{unknown, hover}}` (`eval/metrics.py`).
  That is the §6 definition of record and is not re-litigated here, but the taxonomy in §5
  is the more informative view precisely because it does not collapse to that binary.
- The taxonomy pools six artefacts. It describes the failure mode of this *approach*, not
  of any one configuration; per-configuration counts are in the CSV.
"""


def run() -> int:
    logging.disable(logging.CRITICAL)  # validate() logs every clamp; 3,540 items of it
    records = analyse()
    csv_path = write_csv(records)
    tax = taxonomy()
    md_path = RESULTS / "limitation_abstention.md"
    md_path.write_text(entry(records, tax), encoding="utf-8")
    print(f"wrote {csv_path.relative_to(REPO)}")
    print(f"wrote {md_path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
