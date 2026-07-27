"""Tests for the Exp-0 analysis.

Table 16 makes a claim about a person, so the parts that decide what that claim says
--- how buckets are pooled, when an interval is withheld, and how the author's
position is computed --- are pinned here.
"""

from __future__ import annotations

import pytest

from eval.exp0 import MIN_BUCKET_FOR_CI, _bucket_seed, _ordinal, pooled, position, score


def row(bucket, reference, hypothesis):
    return {"bucket": bucket, "reference": reference, "hypothesis": hypothesis}


class TestScore:
    def test_groups_by_bucket(self):
        scored = score([row("A", "a b", "a b"), row("B", "c d", "c x")])
        assert set(scored) == {"A", "B"}
        assert scored["A"].wer == 0.0
        assert scored["B"].wer == 0.5

    def test_pools_errors_over_words_within_a_bucket(self):
        scored = score([row("A", "a b c d e f g h i j", "a b c d e f g h i j"),
                        row("A", "x", "y")])
        # Averaging the two rates would give 0.5; the pooled figure is 1/11.
        assert scored["A"].wer == pytest.approx(1 / 11)

    def test_keeps_substitutions_deletions_and_insertions_apart(self):
        scored = score([row("A", "a b c", "a x c d")])
        assert (scored["A"].sub, scored["A"].dele, scored["A"].ins) == (1, 0, 1)

    def test_unscoreable_references_are_dropped_not_counted_as_perfect(self):
        scored = score([row("A", "a b", "a b"), row("A", "...", "hello")])
        assert scored["A"].n == 1

    def test_n_and_total_words_are_reported(self):
        scored = score([row("A", "a b c", "a b c"), row("A", "d e", "d e")])
        assert (scored["A"].n, scored["A"].total_words) == (2, 5)


class TestConfidenceIntervals:
    def test_withheld_for_small_buckets(self):
        # A bootstrap over four utterances mostly reproduces the same four; the
        # interval would describe the resampler, not the accent.
        scored = score([row("A", f"w{i} x", "w0 x") for i in range(MIN_BUCKET_FOR_CI - 1)])
        low, high = scored["A"].ci(seed=1)
        assert low != low and high != high

    def test_produced_for_large_enough_buckets(self):
        scored = score([row("A", f"w{i} x y", "w0 x y") for i in range(MIN_BUCKET_FOR_CI)])
        low, high = scored["A"].ci(seed=1)
        assert low == low and low <= scored["A"].wer <= high

    def test_bucket_seed_is_stable_across_processes(self):
        # hash() is salted per interpreter run, so a hash()-derived seed would draw a
        # different published interval on every invocation (ADR-0004 D6).
        assert _bucket_seed("England English") == _bucket_seed("England English")
        assert _bucket_seed("England English") != _bucket_seed("Irish English")


class TestPosition:
    def test_counts_buckets_worse_than_the_author(self):
        worse, total, percentile = position(0.20, [0.10, 0.15, 0.25, 0.30])
        assert (worse, total) == (2, 4)
        assert percentile == 50.0

    def test_best_in_the_distribution(self):
        worse, _, percentile = position(0.05, [0.10, 0.20, 0.30])
        assert worse == 3 and percentile == 0.0

    def test_worst_in_the_distribution(self):
        worse, _, percentile = position(0.50, [0.10, 0.20, 0.30])
        assert worse == 0 and percentile == 100.0

    def test_empty_distribution_is_nan_not_zero(self):
        _, total, percentile = position(0.2, [])
        assert total == 0 and percentile != percentile


class TestPooled:
    def test_labels_the_group(self):
        scored = pooled([row("A", "a b", "a b"), row("B", "c d", "c d")], "Author")
        assert scored.bucket == "Author"
        assert scored.n == 2

    def test_empty_input_gives_an_empty_group_not_a_crash(self):
        assert pooled([], "Author").n == 0


class TestOrdinal:
    @pytest.mark.parametrize(
        "value,expected",
        [(1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th"), (11, "11th"), (12, "12th"),
         (13, "13th"), (21, "21st"), (53, "53rd"), (100, "100th")],
    )
    def test_suffixes(self, value, expected):
        assert _ordinal(value) == expected
