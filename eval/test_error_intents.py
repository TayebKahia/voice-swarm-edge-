"""Tests for the golden-split error breakdown: only errors count, and "keeps the intent"
means the dispatched intent -- the field intent macro-F1 scores -- equals the reference."""

from __future__ import annotations

from eval.error_intents import errors_keeping_intent
from eval.metrics import score_predictions

GOLD = '{"intent":"move","pos":[1.0,2.0,3.0]}'


def test_a_correct_item_is_not_an_error():
    assert errors_keeping_intent(score_predictions([GOLD], [GOLD])) == (0, 0)


def test_a_wrong_parameter_keeps_the_intent():
    wrong_slot = '{"intent":"move","pos":[1.0,2.0,4.0]}'
    assert errors_keeping_intent(score_predictions([wrong_slot], [GOLD])) == (1, 1)


def test_a_wrong_intent_does_not():
    wrong_intent = '{"intent":"unknown"}'
    assert errors_keeping_intent(score_predictions([wrong_intent], [GOLD])) == (0, 1)
