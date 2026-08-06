"""Tests for the conventions the experiments share.

Each is a place where a reasonable-looking default silently changes a published
number: NumPy's interpolating percentile, bootstrapping the wrong unit, and --- for
McNemar --- reaching for the chi-square approximation at counts too small to support
it, or letting the concordant pairs leak into a test that must condition them away.
"""

from __future__ import annotations

import pytest

from eval.stats import (EXACT_BELOW_DISCORDANT, bonferroni_alpha,
                        bootstrap_ratio_ci, mcnemar, nearest_rank)


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


class TestMcNemar:
    def test_contingency_cells_partition_the_pairs(self):
        first = [True, True, False, False, True]
        second = [True, False, True, False, False]
        result = mcnemar(first, second)
        assert (result.both_correct, result.only_first,
                result.only_second, result.both_wrong) == (1, 2, 1, 1)
        assert result.n == 5
        assert result.discordant == 3

    def test_identical_vectors_give_p_one_and_no_discordance(self):
        vector = [True, False, True, True, False]
        result = mcnemar(vector, list(vector))
        assert result.discordant == 0
        assert result.p_value == 1.0
        assert result.statistic == 0.0

    def test_no_discordance_despite_different_accuracy_is_impossible(self):
        # A sanity check on the test's own logic: b == c == 0 forces equal accuracy,
        # so a zero-discordance result can never hide a real difference.
        first, second = [True, True, False], [True, True, False]
        assert sum(first) == sum(second)
        assert mcnemar(first, second).discordant == 0

    def test_the_concordant_cells_do_not_move_the_p_value(self):
        # McNemar conditions on the discordant pairs: padding both vectors with items
        # they both get right must not make the comparison look more decisive.
        first, second = [True] * 6 + [False] * 2, [False] * 6 + [True] * 2
        sparse = mcnemar(first, second)
        padded = mcnemar(first + [True] * 500, second + [True] * 500)
        assert sparse.p_value == padded.p_value
        assert padded.both_correct == sparse.both_correct + 500

    def test_exact_test_below_the_threshold_chi_square_above_it(self):
        few = mcnemar([True] * 5 + [False] * 5, [False] * 5 + [True] * 5)
        assert few.discordant < EXACT_BELOW_DISCORDANT
        assert few.test == "exact"

        many = mcnemar([True] * 30 + [False] * 30, [False] * 30 + [True] * 30)
        assert many.discordant >= EXACT_BELOW_DISCORDANT
        assert many.test == "chi2_cc"
        assert many.p_value == many.p_chi2

    def test_a_single_discordant_pair_can_never_reach_significance(self):
        # The corollary the write-up rests on: with b+c == 1 the smallest attainable
        # exact p-value is 1.0, so a null result there is about power, not equivalence.
        result = mcnemar([True] * 199 + [True], [True] * 199 + [False])
        assert result.discordant == 1
        assert result.p_value == 1.0

    def test_swapping_the_arguments_swaps_b_and_c_but_not_the_p_value(self):
        first = [True, True, True, False, False, False, True, False]
        second = [False, True, False, True, False, True, True, True]
        forward, reverse = mcnemar(first, second), mcnemar(second, first)
        assert forward.only_first == reverse.only_second
        assert forward.only_second == reverse.only_first
        assert forward.p_value == reverse.p_value

    def test_a_one_sided_disagreement_is_significant(self):
        result = mcnemar([True] * 12 + [False] * 8, [False] * 12 + [False] * 8)
        assert result.only_first == 12 and result.only_second == 0
        assert result.p_value < 0.001

    def test_unequal_lengths_are_rejected_rather_than_zipped(self):
        with pytest.raises(ValueError, match="not the same items"):
            mcnemar([True, False, True], [True, False])

    def test_significant_at_is_strict_and_uses_the_threshold_it_is_given(self):
        result = mcnemar([True] * 12 + [False] * 8, [False] * 12 + [False] * 8)
        assert result.p_value < 0.0167
        assert result.significant_at(0.0167)
        assert not result.significant_at(result.p_value)   # strict: p < alpha


class TestBonferroniAlpha:
    def test_three_comparisons_give_the_pre_registered_threshold(self):
        # Roadmap §Session 07: three pairwise comparisons, Bonferroni α = 0.0167.
        assert round(bonferroni_alpha(3), 4) == 0.0167

    def test_one_comparison_is_the_family_alpha_unchanged(self):
        assert bonferroni_alpha(1) == 0.05

    def test_an_empty_family_is_an_error_not_a_division(self):
        with pytest.raises(ValueError):
            bonferroni_alpha(0)
