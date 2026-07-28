"""Tests for the metrics of record.

Every one of these numbers goes in a thesis table, and each definition in §2.7 has a
plausible-looking wrong version that produces a number rather than an error. The
tests below are written against the wrong versions as much as the right ones.
"""

from __future__ import annotations

import pytest

from eval.metrics import (SAFE_INTENTS, exact_match, false_command_rate,
                          intent_macro_f1, safe_failure_rate, schema_validity,
                          score_predictions, slot_micro_f1, summarise)

MOVE = '{"intent":"move","dir":"north","dist":5.0}'
LAND = '{"intent":"land"}'
HOVER = '{"intent":"hover"}'
UNKNOWN = '{"intent":"unknown"}'
ROTATE = '{"intent":"rotate","yaw":90.0}'


def one(raw, gold):
    return score_predictions([raw], [gold])[0]


class TestExactMatch:
    def test_key_order_does_not_matter(self):
        # canon fixes key order (§6.1); a raw string compare would fail this.
        assert one('{"dist":5.0,"dir":"north","intent":"move"}', MOVE).correct

    def test_integer_and_float_forms_are_the_same_command(self):
        assert one('{"intent":"move","dir":"north","dist":5}', MOVE).correct

    def test_absent_and_null_are_the_same(self):
        assert one('{"intent":"land","ids":null}', LAND).correct

    def test_empty_ids_means_all_drones_and_matches_absent(self):
        assert one('{"intent":"land","ids":[]}', LAND).correct

    def test_a_different_value_is_not_a_match(self):
        assert not one('{"intent":"move","dir":"north","dist":6.0}', MOVE).correct

    def test_unparseable_output_is_not_a_match(self):
        assert not one("I think you want to move north", MOVE).correct

    def test_rate_over_a_corpus(self):
        predictions = score_predictions([MOVE, LAND, "garbage"], [MOVE, LAND, HOVER])
        assert exact_match(predictions) == pytest.approx(2 / 3)

    def test_empty_corpus_is_nan_not_zero(self):
        assert exact_match([]) != exact_match([])


class TestIntentMacroF1:
    def test_perfect(self):
        predictions = score_predictions([MOVE, LAND, HOVER], [MOVE, LAND, HOVER])
        assert intent_macro_f1(predictions) == 1.0

    def test_averages_over_reference_intents_only(self):
        # Ten intents exist; only two are exercised. Averaging over all ten would
        # drag the score down with intents the test set never asked for.
        predictions = score_predictions([MOVE, LAND], [MOVE, LAND])
        assert intent_macro_f1(predictions) == 1.0

    def test_is_unweighted_so_a_rare_intent_counts_equally(self):
        # Four moves right, one land wrong. Weighted by support this would be 0.8+;
        # unweighted, the failed class costs a full half.
        raws = [MOVE] * 4 + [HOVER]
        golds = [MOVE] * 4 + [LAND]
        assert intent_macro_f1(score_predictions(raws, golds)) == pytest.approx(0.5)

    def test_uses_the_dispatched_intent_not_the_raw_text(self):
        # Unparseable text dispatches hover, which is a wrong intent for a move.
        predictions = score_predictions(["nonsense"], [MOVE])
        assert intent_macro_f1(predictions) == 0.0


class TestSlotMicroF1:
    def test_counts_slots_even_when_the_intent_is_wrong(self):
        # §2.7: "regardless of intent correctness". This is what makes Slot-F1
        # diagnostic instead of a second copy of exact match.
        prediction = score_predictions(
            ['{"intent":"formation","shape":"circle"}'],
            ['{"intent":"move","dir":"north","dist":5.0}'])
        assert exact_match(prediction) == 0.0
        assert slot_micro_f1(prediction) == 0.0

        partial = score_predictions(
            ['{"intent":"rotate","dir":"north","dist":5.0}'], [MOVE])
        assert exact_match(partial) == 0.0
        assert slot_micro_f1(partial) == 1.0

    def test_intent_itself_is_not_a_slot(self):
        # Otherwise every correct intent inflates the slot score.
        prediction = score_predictions([LAND], [LAND])
        assert slot_micro_f1(prediction) != slot_micro_f1(score_predictions([MOVE], [MOVE]))

    def test_micro_average_pools_across_items(self):
        # Item 1: two slots, both right. Item 2: one slot, wrong.
        # Pooled tp=2 fp=1 fn=1 -> P=R=2/3 -> F1=2/3.
        # The mean of the two per-item F1s would be 0.5, which is the wrong average.
        raws = ['{"intent":"move","dir":"north","dist":5.0}', '{"intent":"rotate","yaw":45.0}']
        golds = [MOVE, ROTATE]
        assert slot_micro_f1(score_predictions(raws, golds)) == pytest.approx(2 / 3)

    def test_missing_slots_count_as_false_negatives(self):
        prediction = score_predictions(['{"intent":"move","dir":"north"}'], [MOVE])
        assert slot_micro_f1(prediction) == pytest.approx(2 / 3)

    def test_no_slots_anywhere_is_nan_not_one(self):
        assert slot_micro_f1(score_predictions([LAND], [LAND])) != \
               slot_micro_f1(score_predictions([LAND], [LAND]))


class TestSafeFailureRate:
    def test_denominator_is_failed_items_only(self):
        # Nine correct, one failed safely. Over all items this would read 0.1;
        # the metric answers "when it was wrong, was it harmless?" -> 1.0.
        raws = [MOVE] * 9 + ["garbage"]
        golds = [MOVE] * 10
        assert safe_failure_rate(score_predictions(raws, golds)) == 1.0

    def test_a_wrong_but_confident_command_is_unsafe(self):
        prediction = score_predictions([ROTATE], [MOVE])
        assert safe_failure_rate(prediction) == 0.0

    def test_unknown_and_hover_both_count_as_safe(self):
        assert SAFE_INTENTS == {"unknown", "hover"}
        for safe in (UNKNOWN, HOVER):
            assert safe_failure_rate(score_predictions([safe], [MOVE])) == 1.0

    def test_perfect_run_reports_nan_not_one(self):
        # There is no safe-failure rate for a run with no failures; 1.0 would claim
        # a safety property from zero evidence.
        result = safe_failure_rate(score_predictions([MOVE], [MOVE]))
        assert result != result


class TestFalseCommandRate:
    def test_hover_is_a_false_command_on_ood_input(self):
        # Safe elsewhere, but on speech that was not a command the correct output is
        # `unknown`; dispatching a hover is still acting on it.
        assert false_command_rate(score_predictions([HOVER], [UNKNOWN])) == 1.0

    def test_unknown_is_the_only_correct_ood_output(self):
        assert false_command_rate(score_predictions([UNKNOWN], [UNKNOWN])) == 0.0

    def test_rate_over_a_corpus(self):
        raws = [UNKNOWN, UNKNOWN, MOVE, HOVER]
        assert false_command_rate(score_predictions(raws, [UNKNOWN] * 4)) == 0.5


class TestSchemaValidity:
    def test_well_formed_json_is_valid(self):
        assert schema_validity(score_predictions([MOVE, LAND], [MOVE, LAND])) == 1.0

    def test_garbage_is_not(self):
        assert schema_validity(score_predictions(["{oops", "x"], [MOVE, LAND])) == 0.0

    def test_truncated_json_is_not_valid(self):
        # Spike S3's failure mode: an unbounded id list truncated by -n.
        truncated = '{"intent":"land","ids":[1,2,3,4,5,1,2,3'
        assert schema_validity(score_predictions([truncated], [LAND])) == 0.0


class TestSummarise:
    def test_reports_every_metric_of_record(self):
        summary = summarise(score_predictions([MOVE, LAND], [MOVE, LAND]))
        assert set(summary) == {"n", "exact_match", "intent_macro_f1", "slot_micro_f1",
                                "safe_failure_rate", "schema_validity"}

    def test_false_command_rate_only_for_ood(self):
        predictions = score_predictions([UNKNOWN], [UNKNOWN])
        assert "false_command_rate" not in summarise(predictions)
        assert "false_command_rate" in summarise(predictions, ood=True)

    def test_mismatched_lengths_are_rejected(self):
        with pytest.raises(ValueError):
            score_predictions([MOVE], [MOVE, LAND])
