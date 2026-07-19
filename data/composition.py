#!/usr/bin/env python3
"""Which training rows get which augmentation variant, and why the mix is a mix.

`02_dataset_plan.md` §4 fixes the composition of the final training set:

    clean 50% | ASR round-trip @20 dB 20% | @10 dB 15% | @5 dB 10% | perturbed 5%

**Assignment is substitution, not inflation.** A row assigned `asr_10db` has its
*surface form* replaced by what `whisper.cpp` heard at 10 dB, while keeping its
original `target` --- "pair the NOISY transcript with the ORIGINAL `gold_json`"
(§4). It does not gain a second row. That is what keeps `train_synth` at the
$\\approx$1,900 pairs `prd.md` Table 13 specifies while still being 50% clean; the
alternative reading, appending a round-trip row beside every clean one, doubles the
split to ~3,900 and contradicts the table. It is also what the de-duplication guard
is for: under inflation, a round-trip that returns the clean string would sit next
to its own twin and quietly double that row's weight.

**Why the clean half exists at all.** Deployment always feeds `whisper.cpp` output,
so a purely round-tripped training set would match deployment more closely. But
Exp-1 measures exact match on **reference text** (`IMPLEMENTATION_ROADMAP.md` §2.6)
--- human-authored transcripts, not ASR output. The model has to hold both
distributions. 50/50 is what covers them.

Assignment is stratified by intent. Left to an unstratified draw, the ten intents
would receive the mix in proportion to their row counts, and `abort` --- the
smallest and the most safety-critical --- could plausibly come out all-clean and
never be trained against a degraded transcript at all.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any, Iterable, Mapping, Sequence

#: Variant name -> share of the training split. Names follow the `§7.4` record
#: format, which writes the round-trip levels as `asr_<n>db`.
COMPOSITION: dict[str, float] = {
    "clean": 0.50,
    "asr_20db": 0.20,
    "asr_10db": 0.15,
    "asr_5db": 0.10,
    "perturb": 0.05,
}

#: Variant -> SNR in dB, for the variants that involve mixing.
VARIANT_SNR: dict[str, int] = {"asr_20db": 20, "asr_10db": 10, "asr_5db": 5}

DEFAULT_SEED = 42


def _stable_seed(*parts: object) -> int:
    blob = "\x1f".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(blob).digest()[:8], "big")


def _quota(n: int, shares: Mapping[str, float]) -> dict[str, int]:
    """Split `n` items across `shares` by largest remainder.

    Largest remainder rather than rounding each share independently: rounding
    leaves the total off by a few rows, and the shortfall would land wherever the
    iteration happened to end.
    """
    exact = {name: n * share for name, share in shares.items()}
    counts = {name: int(value) for name, value in exact.items()}
    remaining = n - sum(counts.values())
    order = sorted(exact, key=lambda name: (-(exact[name] - counts[name]), name))
    for name in order[:remaining]:
        counts[name] += 1
    return counts


def assign_variants(
    rows: Sequence[Mapping[str, Any]],
    *,
    seed: int = DEFAULT_SEED,
    shares: Mapping[str, float] = COMPOSITION,
    stratify_key: str = "gold_intent",
) -> dict[str, str]:
    """Map row id -> variant name, deterministically and stratified.

    Ordering inside each stratum is by a stable hash of `(seed, id)` rather than by
    a shuffled list, so the assignment survives a change in row order in
    `raw_pairs.jsonl` --- regenerating the corpus with one extra row would
    otherwise re-roll every downstream variant and invalidate the cached audio.
    """
    strata: dict[Any, list[str]] = defaultdict(list)
    for row in rows:
        strata[row.get(stratify_key)].append(row["id"])

    assignment: dict[str, str] = {}
    for stratum in sorted(strata, key=str):
        ids = sorted(strata[stratum], key=lambda i: (_stable_seed(seed, "variant", i), i))
        counts = _quota(len(ids), shares)
        cursor = 0
        for name in shares:  # insertion order: clean first, then descending SNR
            for item_id in ids[cursor : cursor + counts[name]]:
                assignment[item_id] = name
            cursor += counts[name]
    return assignment


def snr_for(variant: str) -> int | None:
    """The SNR a variant is mixed at, or None if it involves no audio."""
    return VARIANT_SNR.get(variant)


def needs_roundtrip(variant: str) -> bool:
    return variant in VARIANT_SNR


def tally(variants: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {name: 0 for name in COMPOSITION}
    for variant in variants:
        counts[variant] = counts.get(variant, 0) + 1
    return counts
