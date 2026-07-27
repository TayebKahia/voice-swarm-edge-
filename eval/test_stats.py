"""Tests for the two conventions the experiments share.

Both are places where a reasonable-looking default silently changes a published
number: NumPy's interpolating percentile, and bootstrapping the wrong unit.
"""

from __future__ import annotations

import pytest

from eval.stats import bootstrap_ratio_ci, nearest_rank


class TestNearestRank:
    def test_returns_an_observed_value_never_an_interpolated_one(self):
        samples = [10.0, 20.0, 30.0, 40.0]
        # numpy.percentile(samples, 95) would give 38.5, which no trial produced.
        assert nearest_rank(samples, 95) in samples

    def test_p100_is_the_maximum_and_p0_the_minimum(self):
        samples = [5, 1, 9, 3]
        assert nearest_rank(samples, 100) == 9
        assert nearest_rank(samples, 0) == 1

    def test_ceiling_rank(self):
        # ceil(0.5 * 4) = 2 -> the 2nd smallest.
        assert nearest_rank([1, 2, 3, 4], 50) == 2

    def test_single_sample(self):
        assert nearest_rank([7.0], 95) == 7.0

    def test_empty_is_nan_not_an_exception(self):
        result = nearest_rank([], 95)
        assert result != result

    def test_input_is_not_mutated(self):
        samples = [3, 1, 2]
        nearest_rank(samples, 50)
        assert samples == [3, 1, 2]


class TestBootstrapRatioCi:
    def test_interval_brackets_the_point_estimate(self):
        errors, words = [1, 0, 2, 0, 1, 3, 0, 0, 1, 2], [10] * 10
        low, high = bootstrap_ratio_ci(errors, words)
        assert low <= sum(errors) / sum(words) <= high

    def test_deterministic_across_calls(self):
        errors, words = [1, 0, 2, 1], [10, 10, 10, 10]
        assert bootstrap_ratio_ci(errors, words) == bootstrap_ratio_ci(errors, words)

    def test_any_seed_brackets_the_point_estimate(self):
        # The seed selects which replicates are drawn, not which answer is right:
        # every seed must produce an interval containing the observed ratio.
        errors, words = [1, 0, 2, 1, 3, 0] * 8, [10] * 48
        point = sum(errors) / sum(words)
        for seed in (1, 2, 12345, 20260919):
            low, high = bootstrap_ratio_ci(errors, words, seed=seed)
            assert low <= point <= high, f"seed {seed} excluded the point estimate"

    def test_fewer_than_two_observations_gives_nan_not_a_point(self):
        # One observation would resample to itself every time; an interval of zero
        # width reads as certainty rather than as absence of evidence.
        low, high = bootstrap_ratio_ci([1], [10])
        assert low != low and high != high

    def test_zero_denominator_rows_are_dropped(self):
        with_unscoreable = bootstrap_ratio_ci([1, 0, 2, 5], [10, 10, 10, 0])
        without = bootstrap_ratio_ci([1, 0, 2], [10, 10, 10])
        assert with_unscoreable == without

    def test_perfect_corpus_has_a_zero_width_interval_at_zero(self):
        assert bootstrap_ratio_ci([0, 0, 0, 0], [10] * 4) == (0.0, 0.0)

    def test_narrower_interval_with_more_data(self):
        few = bootstrap_ratio_ci([1, 0, 2, 1] * 2, [10] * 8)
        many = bootstrap_ratio_ci([1, 0, 2, 1] * 50, [10] * 200)
        assert (many[1] - many[0]) < (few[1] - few[0])

    def test_mismatched_lengths_are_rejected(self):
        with pytest.raises(ValueError):
            bootstrap_ratio_ci([1, 2], [10])
