"""The canonicaliser and the single comparator (PRD Sec. 6.1, FR-12).

`canon(obj)` is applied to *both* the prediction and the reference before any
comparison. Every accuracy number in either thesis comes from it:

    Exact match (EM)              reference text in, canon() compares
    Command recognition rate      audio in, canon() compares

They differ only in input modality and measurement point. That is deliberate:
because the comparator is identical, the gap between EM and CRR on the same
items is the *cost of the speech-recognition stage*, and it is reported as a
finding rather than absorbed into one end-to-end score (PRD Sec. 6.1).

The five rules, verbatim from the PRD:

    1. Key order fixed by schema declaration order.
    2. Absent and null fields omitted, not emitted.
    3. Floats rounded to one decimal --- matching cmd.gbnf's `num` precision.
    4. `ids` deduplicated and sorted ascending.
    5. No whitespace outside string literals.

Two commands are equal if and only if their canonical forms are byte-identical.

This module normalises; it does not validate. A command outside the physical
envelope canonicalises fine --- clamping is layer 2 (validate.py). Keeping the
two apart is what lets Exp-1 measure the model rather than the validator.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from pydantic import BaseModel

import math

from schema.schema import DECIMALS, KEY_ORDER

__all__ = ["canon", "canon_equal"]


def _fmt_num(value: float | int) -> str:
    """Format a number at exactly DECIMALS places (rule 3).

    Always one decimal, so a reference authored as `5` and a decode of `5.0`
    reach the same bytes. Negative zero is normalised to `0.0`; without that,
    a value of -0.04 would round to `-0.0` and compare unequal to `0.0`
    despite being the same commanded position.
    Non-finite values (NaN, Infinity) are rejected to guarantee valid JSON.
    """
    f_val = float(value)
    if not math.isfinite(f_val):
        raise ValueError(f"canon() cannot format non-finite number: {value}")
    rounded = round(f_val, DECIMALS)
    if rounded == 0:
        rounded = 0.0
    return f"{rounded:.{DECIMALS}f}"


def _fmt_ids(ids: Sequence[int]) -> str:
    """Deduplicate and sort ascending (rule 4).

    Identifiers are emitted as integers, never `1.0`. Out-of-range filtering
    is layer 2's job, not the canonicaliser's --- canon() must be able to
    render whatever it is handed, including a reference under review.
    Non-integer elements are skipped to keep canon() total on malformed inputs.
    """
    cleaned: list[int] = []
    for item in ids:
        try:
            cleaned.append(int(item))
        except (ValueError, TypeError):
            continue
    return "[" + ",".join(str(i) for i in sorted(set(cleaned))) + "]"


def _fmt_value(key: str, value: object) -> str:
    if key == "ids":
        return _fmt_ids(value)  # type: ignore[arg-type]
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        # Not reachable through the schema; guarded because bool is a subclass
        # of int in Python and would otherwise format as 1.0 / 0.0.
        raise TypeError(f"boolean value for {key!r} is not part of schema v1.0")
    if isinstance(value, (int, float)):
        return _fmt_num(value)
    if isinstance(value, Sequence):
        # `pos` --- a fixed 3-vector. Rendered element-wise at one decimal.
        return "[" + ",".join(_fmt_num(v) for v in value) + "]"  # type: ignore[arg-type]
    raise TypeError(f"unsupported value type for {key!r}: {type(value).__name__}")


def _ordered_keys(intent: object, present: Sequence[str]) -> list[str]:
    """Rule 1, with a deterministic fallback.

    For a known intent, declared order comes from KEY_ORDER, which is derived
    from the Pydantic models themselves. Any key not in the declaration --- a
    stray field on a hand-authored reference, or output from the grammar-off
    ablation where structure is not guaranteed --- is appended in alphabetical
    order rather than dropped. Dropping it would hide a real disagreement
    inside an exact-match comparison; appending it makes the two forms differ,
    which is the correct outcome.
    """
    declared = KEY_ORDER.get(intent) if isinstance(intent, str) else None
    if declared is None:
        # Unknown or missing intent: `intent` first if present, then the rest
        # alphabetically. Keeps canon() total, so a malformed prediction still
        # produces bytes to compare instead of raising.
        rest = sorted(k for k in present if k != "intent")
        return (["intent"] if "intent" in present else []) + rest
    extra = sorted(k for k in present if k not in declared)
    return [k for k in declared if k in present] + extra


def canon(obj: Mapping[str, object] | BaseModel) -> str:
    """Return the canonical single-line wire form of a command.

    Accepts a plain mapping (a decoded prediction, a JSONL reference row) or a
    schema model. Returns bytes-as-str; compare with `==` or use canon_equal.
    """
    if isinstance(obj, BaseModel):
        data: Mapping[str, object] = obj.model_dump()
    elif isinstance(obj, Mapping):
        data = obj
    else:
        raise TypeError(f"canon() expects a mapping or model, got {type(obj).__name__}")

    # Rule 2: absent and null fields omitted. An empty `ids` list is dropped
    # too --- "empty after filtering means all drones" (PRD Sec. 5.2), which is
    # exactly what an absent `ids` means. Leaving it in would give one command
    # two canonical forms and quietly break exact match.
    present = {
        key: value
        for key, value in data.items()
        if value is not None and not (key == "ids" and len(value) == 0)  # type: ignore[arg-type]
    }

    parts = [
        f"{json.dumps(key)}:{_fmt_value(key, present[key])}"
        for key in _ordered_keys(present.get("intent"), list(present))
    ]
    # Rule 5: no whitespace outside string literals.
    return "{" + ",".join(parts) + "}"


def canon_equal(
    a: Mapping[str, object] | BaseModel,
    b: Mapping[str, object] | BaseModel,
) -> bool:
    """The single comparator helper (byte-identity comparison canon(a) == canon(b))."""
    return canon(a) == canon(b)
