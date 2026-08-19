"""eval/wake_real.py -- the interval and the labels, which decide what the report may claim."""

from __future__ import annotations

import pytest

from eval.wake_real import PROMPTS, clopper_pearson, labels


def test_zero_misses_in_twenty_still_leaves_the_upper_bound_above_nfr16() -> None:
    lo, hi = clopper_pearson(0, 20)
    assert lo == 0.0
    assert hi == pytest.approx(0.1684, abs=1e-4)   # the report's "~17%"
    assert hi > 0.10


def test_interval_matches_scipy_exact_binomial() -> None:
    from scipy.stats import binomtest

    ci = binomtest(1, 20).proportion_ci(method="exact")
    assert clopper_pearson(1, 20) == pytest.approx((ci.low, ci.high))


@pytest.mark.skipif(not PROMPTS.is_file(), reason="prompt list absent")
def test_the_prompt_list_is_twenty_of_each_class() -> None:
    classes = list(labels().values())
    assert classes.count("swarm_hold") == 20 and classes.count("swarm_abort") == 20
