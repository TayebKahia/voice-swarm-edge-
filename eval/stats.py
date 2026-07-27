#!/usr/bin/env python3
"""Statistics shared by the experiments: percentiles, bootstrap intervals.

Two conventions are fixed here rather than left to whichever library a script
happens to import, because both change the numbers that go in a thesis.

**Percentiles are nearest-rank with no interpolation** (§2.7). NumPy's default is
linear interpolation, which invents a value that no trial produced --- for a p95
latency quoted against a 2500 ms requirement, that is a reported figure no run ever
achieved. Nearest-rank always returns an observed sample.

**Bootstrap resamples utterances, not error rates.** WER is a ratio of two sums, so
the resampling unit is the utterance and the statistic is recomputed as
`total errors / total reference words` on each replicate. Resampling per-utterance
rates and averaging them would answer a different question --- the mean of the rates
rather than the rate of the corpus --- and would weight a three-word clip equally
with a thirty-word one.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

__all__ = ["nearest_rank", "bootstrap_ratio_ci", "BOOTSTRAP_RESAMPLES", "BOOTSTRAP_SEED"]

#: Replicates. 10,000 puts the Monte-Carlo error on a 95% bound at well under a
#: tenth of a percentage point, which is finer than any WER difference reported.
BOOTSTRAP_RESAMPLES = 10_000

#: Fixed so the intervals in the thesis are reproducible from a clean clone. Callers
#: that need independent intervals per group pass a derived seed, never `hash()` ---
#: Python salts string hashing per process, so a `hash()`-derived seed would produce
#: different intervals on different runs (ADR-0004).
BOOTSTRAP_SEED = 20_260_919


def nearest_rank(samples: Sequence[float], percentile: float) -> float:
    """The nearest-rank percentile: ceil(p/100 * n)-th smallest observed value."""
    ordered = sorted(samples)
    if not ordered:
        return float("nan")
    rank = math.ceil(percentile / 100.0 * len(ordered))
    return ordered[max(1, min(rank, len(ordered))) - 1]


def bootstrap_ratio_ci(
    numerators: Sequence[float],
    denominators: Sequence[float],
    *,
    confidence: float = 95.0,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    """Percentile bootstrap CI for `sum(numerators) / sum(denominators)`.

    For WER: `numerators` are per-utterance error counts, `denominators` per-utterance
    reference-word counts. The pair is resampled together so an utterance's errors
    always travel with its own length.

    Returns `(nan, nan)` for fewer than two scoreable utterances --- with one
    observation every replicate is identical and the "interval" would be a point,
    which reads as certainty rather than as absence of evidence.
    """
    errors = np.asarray(numerators, dtype=float)
    words = np.asarray(denominators, dtype=float)
    if errors.shape != words.shape:
        raise ValueError(f"{errors.shape} numerators against {words.shape} denominators")

    keep = words > 0
    errors, words = errors[keep], words[keep]
    if errors.size < 2:
        return float("nan"), float("nan")

    rng = np.random.default_rng(seed)
    picks = rng.integers(0, errors.size, size=(resamples, errors.size))
    replicates = errors[picks].sum(axis=1) / words[picks].sum(axis=1)

    tail = (100.0 - confidence) / 2.0
    return nearest_rank(replicates, tail), nearest_rank(replicates, 100.0 - tail)
