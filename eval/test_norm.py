"""Tests for the fixed WER normalisation.

The normalisation is a *definition*, not an implementation detail: §2.7 defines WER
in terms of it, so a silent change here restates the metric. These tests pin the
four behaviours that definition depends on --- the ordering of expansion against
punctuation stripping, the two characters that survive the strip, the single source
of the digit mapping, and the pooled corpus denominator.
"""

from __future__ import annotations

import pytest

from data.numwords import words_to_digits
from eval.norm import Edits, corpus_wer, edits, normalise, tokenise, wer


class TestNormalise:
    def test_lowercases_and_strips_punctuation(self):
        assert normalise("Samantha's boots felt HEAVY.") == "samanthas boots felt heavy"

    def test_apostrophes_close_up_other_punctuation_opens_a_boundary(self):
        assert normalise("don't") == "dont"
        assert normalise("well-known") == "well known"

    def test_expands_spelled_out_numbers(self):
        assert normalise("move seventeen point three meters") == "move 17.3 meters"

    def test_spelled_out_and_digit_forms_converge(self):
        assert normalise("about seventeen point three") == normalise("about 17.3")

    def test_decimal_point_survives_the_punctuation_strip(self):
        # The whole reason expansion runs before stripping: "17.3" must not become
        # "17 3", which would score a correct transcription as an error.
        assert normalise("move 17.3 meters") == "move 17.3 meters"
        assert tokenise("move 17.3 meters") == ["move", "17.3", "meters"]

    def test_sign_survives_the_punctuation_strip(self):
        # Without this, an altitude of -2.5 and one of 2.5 normalise identically.
        assert normalise("altitude minus two point five") == "altitude -2.5"
        assert normalise("altitude -2.5") == "altitude -2.5"

    def test_a_sign_error_is_scored_as_an_error(self):
        assert wer("altitude minus two point five", "altitude two point five") > 0

    def test_hyphen_between_digits_is_a_separator_not_a_sign(self):
        assert normalise("drone 3-4 hold") == "drone 3 4 hold"

    def test_sentinels_cannot_collide_with_input(self):
        # Lowercasing happens first, so no input character reaches the sentinel space.
        assert normalise("Q Z quick zebra") == "q z quick zebra"

    @pytest.mark.parametrize(
        "text",
        [
            "move seventeen point three meters",
            "altitude minus two point five",
            "Samantha's boots felt HEAVY.",
            "drone one and four eastward",
            "",
        ],
    )
    def test_idempotent(self, text):
        # Applied to both sides of a comparison without knowing which side came from
        # the recogniser, so it must be safe to apply twice.
        assert normalise(normalise(text)) == normalise(text)

    def test_empty_and_punctuation_only_normalise_to_nothing(self):
        assert normalise("") == ""
        assert normalise("...") == ""
        assert tokenise("...") == []

    def test_digit_mapping_is_the_one_in_data_numwords(self):
        # ADR-0004 D6: two mappings in one repo would let the WER figure and the
        # augmentation guard disagree about what the same utterance says.
        spoken = "one hundred and twenty-eight point four"
        assert words_to_digits(spoken) in normalise(spoken)


class TestEdits:
    def test_identical_strings_have_no_errors(self):
        assert edits("move forward five", "move forward five") == Edits(0, 0, 0, 3)

    def test_substitution(self):
        assert edits("move forward five", "move backward five") == Edits(1, 0, 0, 3)

    def test_deletion(self):
        assert edits("move forward five", "move five") == Edits(0, 1, 0, 3)

    def test_insertion(self):
        assert edits("move five", "move forward five") == Edits(0, 0, 1, 2)

    def test_total_and_rate_derive_from_the_counts(self):
        counted = edits("move forward five", "move backward")
        assert counted.total == counted.sub + counted.dele + counted.ins
        assert counted.rate == pytest.approx(counted.total / counted.ref_words)

    def test_normalisation_is_applied_before_alignment(self):
        assert edits("Move Forward, five.", "move forward five").total == 0

    def test_empty_reference_gives_nan_not_zero(self):
        # An unscoreable pair must not silently read as a perfect one.
        assert edits("...", "hello").ref_words == 0
        assert wer("...", "hello") != wer("...", "hello")  # nan

    def test_counts_are_stable_across_repeated_calls(self):
        # The tie-break must not depend on iteration order.
        pair = ("the quick brown fox jumps", "quick brown foxes jump over")
        assert {edits(*pair) for _ in range(20)} == {edits(*pair)}


class TestCorpusWer:
    def test_pools_errors_over_words_rather_than_averaging_rates(self):
        pairs = [("a b c d e f g h i j", "a b c d e f g h i j"), ("x", "y")]
        # Mean of per-utterance rates would be 0.5; the pooled figure is 1/11.
        assert corpus_wer(pairs) == pytest.approx(1 / 11)

    def test_unscoreable_pairs_contribute_to_neither_side(self):
        scoreable = [("a b", "a x")]
        assert corpus_wer(scoreable + [("...", "hello")]) == corpus_wer(scoreable)

    def test_all_unscoreable_gives_nan(self):
        result = corpus_wer([("...", "hello")])
        assert result != result  # nan

    def test_perfect_corpus_is_zero(self):
        assert corpus_wer([("a b", "a b"), ("c", "c")]) == 0.0
