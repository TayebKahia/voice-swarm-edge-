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

**McNemar uses the exact binomial test when discordant pairs are few.** Two models
scored on the same test set produce paired observations, so the only evidence about
which is better lives in the items they disagree on --- the discordant pairs `b` and
`c`. The textbook chi-square statistic is an asymptotic approximation to a binomial
with `n = b + c`, and at the counts this project actually produces (`b + c` runs from
1 to 41 on 200-item splits) the approximation is the wrong tool: its p-value is not
trustworthy below roughly 25 discordant pairs. `mcnemar()` therefore reports the exact
test by default and falls back to the corrected chi-square only above that threshold,
and carries *both* p-values on the result so a reader can see they agree.

The corollary matters more than the test. When `b + c` is 1, no test on earth can
reach significance --- the maximum attainable exact p-value is 1.0. A non-significant
McNemar there is a statement about the *evidence*, not about the models, and must
never be written up as "the two are equivalent".
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy.stats import binomtest, chi2

__all__ = ["nearest_rank", "bootstrap_ratio_ci", "mcnemar", "bonferroni_alpha",
           "McNemarResult", "BOOTSTRAP_RESAMPLES", "BOOTSTRAP_SEED",
           "EXACT_BELOW_DISCORDANT"]

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


# --------------------------------------------------------------------------
# McNemar's test on paired predictions


#: Below this many discordant pairs the chi-square approximation is not trustworthy
#: and `mcnemar()` reports the exact binomial test instead. 25 is the conventional
#: cut; every comparison this project runs falls below it, so the exact test is in
#: practice always the one of record --- the branch exists so a larger future split
#: does not silently keep using a test chosen for small samples.
EXACT_BELOW_DISCORDANT = 25


@dataclass(frozen=True)
class McNemarResult:
    """One paired comparison, with the contingency table it was computed from.

    The four cells are reported, not just the p-value: `b` and `c` are the entire
    evidence base, and a reader cannot tell a decisive comparison from a powerless
    one without them. `a` and `d` carry no information about the difference but do
    say how much of the split both systems agreed on, which is the context that
    makes `b` and `c` interpretable.
    """

    both_correct: int      # a: both right
    only_first: int        # b: first right, second wrong
    only_second: int       # c: first wrong, second right
    both_wrong: int        # d: both wrong
    statistic: float       # continuity-corrected chi-square, 1 df
    p_value: float         # from `test` --- the figure of record
    p_exact: float
    p_chi2: float
    test: str              # "exact" or "chi2_cc"

    @property
    def n(self) -> int:
        return self.both_correct + self.only_first + self.only_second + self.both_wrong

    @property
    def discordant(self) -> int:
        return self.only_first + self.only_second

    def significant_at(self, alpha: float) -> bool:
        return self.p_value < alpha


def mcnemar(first: Sequence[bool], second: Sequence[bool]) -> McNemarResult:
    """McNemar's test on two correct/incorrect vectors over the *same* items.

    The two sequences must be aligned item for item; pairing is the whole point of
    the test, and silently zipping two differently-ordered prediction files would
    produce a plausible number from a meaningless table.
    """
    if len(first) != len(second):
        raise ValueError(f"{len(first)} paired against {len(second)} --- not the same items")

    a = sum(1 for x, y in zip(first, second) if x and y)
    b = sum(1 for x, y in zip(first, second) if x and not y)
    c = sum(1 for x, y in zip(first, second) if not x and y)
    d = sum(1 for x, y in zip(first, second) if not x and not y)

    discordant = b + c
    if discordant == 0:
        # The two systems are right and wrong on exactly the same items. There is no
        # evidence of a difference and no test to run; p = 1 by definition, and the
        # chi-square statistic is 0 rather than the 0/0 the formula would give.
        return McNemarResult(a, b, c, d, 0.0, 1.0, 1.0, 1.0, "exact")

    p_exact = float(binomtest(b, discordant, 0.5).pvalue)
    statistic = (abs(b - c) - 1) ** 2 / discordant   # Edwards' continuity correction
    p_chi2 = float(chi2.sf(statistic, 1))

    exact = discordant < EXACT_BELOW_DISCORDANT
    return McNemarResult(a, b, c, d, statistic,
                         p_exact if exact else p_chi2, p_exact, p_chi2,
                         "exact" if exact else "chi2_cc")


def bonferroni_alpha(comparisons: int, *, family_alpha: float = 0.05) -> float:
    """The per-comparison threshold for a family of `comparisons` tests.

    Bonferroni is applied per *family* of related comparisons, not once across every
    test in the thesis: the three model-against-model pairs are one family and the
    three quantisation pairs are another, because they answer different questions and
    pooling them would penalise each for the other's existence.
    """
    if comparisons < 1:
        raise ValueError("a family has at least one comparison")
    return family_alpha / comparisons
