#!/usr/bin/env python3
"""The metrics of record (§2.7). A metric absent from that table appears in no thesis.

Each definition below is the one in the table, implemented once and shared by Exp-1,
Exp-3 and the grammar ablation. Four of them have a detail that is easy to get subtly
wrong, and wrong in a way that produces a plausible number rather than an error:

**Exact match** compares `canon(pred) == canon(gold)`. Never a string compare of raw
model output and never a `dict ==`: the canonical form fixes key order, number
formatting and the omission of nulls (§6.1), so `{"intent":"move","dist":4}` and
`{"dist":4.0,"intent":"move"}` are the same command and must score as one.

**Intent macro-F1** averages over the intents *present in the reference*, unweighted.
Averaging over all ten would let an intent the test set never exercises contribute a
zero, and weighting by support would turn the macro average back into an accuracy.

**Slot-F1** is micro-averaged over `(key, canonical value)` pairs across all items
**regardless of intent correctness**. An item with the right slots and the wrong
intent still contributes its slots; that is what makes Slot-F1 diagnostic rather than
a second copy of exact match.

**Safe-failure rate** has **failed items as its denominator** --- not all items. It
answers "when it got the command wrong, did it do something harmless?", and computing
it over everything would turn a model that is merely accurate into a model that is
safe, which are different properties and are reported side by side for that reason.

The dispatched action comes from `schema/validate.py` with its fallback on, because
that is what the runtime actually dispatches: layer 2 never rejects, it clamps or
falls back to `Hover`. Scoring the raw text instead would measure a string the system
never acts on.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

if __package__ in (None, ""):  # `python eval/metrics.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# One definition of a slot pair in the repository. `data/annotate.py` owns it because
# the annotation comparison needed it first; re-deriving it here would let the two
# disagree about what counts as a slot, silently (ADR-0004 D6).
from data.annotate import slot_pairs
from schema.canon import canon
from schema.validate import validate

__all__ = [
    "Prediction", "score_predictions", "exact_match", "intent_macro_f1",
    "slot_micro_f1", "safe_failure_rate", "false_command_rate", "schema_validity",
]

#: Intents that constitute a safe failure: the swarm is told to do nothing, or to
#: hold. Both make it do *less*, so neither can turn a misheard command into motion.
SAFE_INTENTS = frozenset({"unknown", "hover"})


@dataclass(frozen=True)
class Prediction:
    """One model output, parsed the way the runtime parses it."""

    raw: str
    gold: str                 # canonical
    predicted: str | None     # canonical, or None when the text is not a command
    dispatched: str           # the intent layer 2 actually dispatches
    parsed_ok: bool           # did the raw text parse as schema-valid JSON at all

    @property
    def correct(self) -> bool:
        return self.predicted is not None and self.predicted == self.gold

    @property
    def gold_intent(self) -> str:
        return json.loads(self.gold)["intent"]


def _parse(raw: str, gold: str) -> Prediction:
    predicted, parsed_ok = None, False
    try:
        decoded = json.loads(raw)
        predicted = canon(decoded)
        parsed_ok = True
    except Exception:
        decoded = None

    # What the runtime would actually fly. validate() clamps and falls back; it
    # never raises, so a failure here is a bug rather than a bad prediction.
    try:
        dispatched = validate(raw if decoded is None else decoded, fallback=True).intent
    except Exception:
        dispatched = "hover"
    return Prediction(raw=raw, gold=gold, predicted=predicted,
                      dispatched=dispatched, parsed_ok=parsed_ok)


def score_predictions(raws: Sequence[str], golds: Sequence[str]) -> list[Prediction]:
    if len(raws) != len(golds):
        raise ValueError(f"{len(raws)} predictions against {len(golds)} references")
    return [_parse(raw, gold) for raw, gold in zip(raws, golds)]


def exact_match(predictions: Iterable[Prediction]) -> float:
    items = list(predictions)
    return sum(p.correct for p in items) / len(items) if items else float("nan")


def intent_macro_f1(predictions: Iterable[Prediction]) -> float:
    items = list(predictions)
    if not items:
        return float("nan")
    intents = sorted({p.gold_intent for p in items})

    scores = []
    for intent in intents:
        tp = sum(1 for p in items if p.gold_intent == intent and p.dispatched == intent)
        fp = sum(1 for p in items if p.gold_intent != intent and p.dispatched == intent)
        fn = sum(1 for p in items if p.gold_intent == intent and p.dispatched != intent)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(scores) / len(scores)


def slot_micro_f1(predictions: Iterable[Prediction]) -> float:
    tp = fp = fn = 0
    for prediction in predictions:
        gold = slot_pairs(prediction.gold)
        predicted = slot_pairs(prediction.predicted) if prediction.predicted else set()
        tp += len(gold & predicted)
        fp += len(predicted - gold)
        fn += len(gold - predicted)
    if not (tp or fp or fn):
        return float("nan")          # no slots anywhere; not a perfect score
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def safe_failure_rate(predictions: Iterable[Prediction]) -> float:
    """Among items that were NOT exactly right, the fraction that failed safely.

    `nan` when nothing failed --- there is no safe-failure rate to report for a
    perfect run, and returning 1.0 would claim a safety property from no evidence.
    """
    failed = [p for p in predictions if not p.correct]
    if not failed:
        return float("nan")
    return sum(p.dispatched in SAFE_INTENTS for p in failed) / len(failed)


def false_command_rate(predictions: Iterable[Prediction]) -> float:
    """NFR-18, on the OOD set: anything dispatched that is not `unknown`.

    `hover` counts as a false command here even though it is a safe failure
    elsewhere. On out-of-distribution input the correct behaviour is to recognise
    that nothing was commanded; dispatching a hover to a swarm that was not addressed
    is still acting on speech that was not a command.
    """
    items = list(predictions)
    if not items:
        return float("nan")
    return sum(p.dispatched != "unknown" for p in items) / len(items)


def schema_validity(predictions: Iterable[Prediction]) -> float:
    """NFR-6. Under GBNF this is 1.0 by construction; the ablation is where it moves."""
    items = list(predictions)
    return sum(p.parsed_ok for p in items) / len(items) if items else float("nan")


def summarise(predictions: Sequence[Prediction], *, ood: bool = False) -> dict[str, float]:
    summary = {
        "n": len(predictions),
        "exact_match": exact_match(predictions),
        "intent_macro_f1": intent_macro_f1(predictions),
        "slot_micro_f1": slot_micro_f1(predictions),
        "safe_failure_rate": safe_failure_rate(predictions),
        "schema_validity": schema_validity(predictions),
    }
    if ood:
        summary["false_command_rate"] = false_command_rate(predictions)
    return summary
