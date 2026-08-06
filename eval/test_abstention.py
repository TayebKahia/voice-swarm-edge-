"""Tests for the abstention analysis --- chiefly `_origin`, which was wrong once.

The first version of this module classified every safe failure dispatching `hover` as
the validator falling back. That is wrong and it flattered the system in the direction
of the claim being made: a `hover` the *model* emitted is a command to hold, not the
validator catching anything. On the real predictions the two differ 24 to 3, so the
error would have inverted the finding rather than shifted it slightly.
"""

from __future__ import annotations

import pytest

from eval.abstention import _origin
from eval.metrics import score_predictions

HOVER = '{"intent":"hover","ids":[0]}'
MOVE = '{"intent":"move","pos":[1.0,2.0,3.0],"ids":[0]}'


def _one(raw: str, gold: str):
    return score_predictions([raw], [gold])[0]


def test_a_correct_command_has_no_safe_failure_origin():
    assert _origin(_one(MOVE, MOVE)) is None


def test_an_actionable_error_has_no_safe_failure_origin():
    wrong = '{"intent":"move","pos":[9.0,2.0,3.0],"ids":[0]}'
    assert _origin(_one(wrong, MOVE)) is None


def test_a_model_emitted_hover_is_not_credited_to_the_validator():
    """The distinction the first implementation got wrong."""
    assert _origin(_one(HOVER, MOVE)) == "model_hover"


def test_a_model_emitted_unknown_is_the_only_real_abstention():
    assert _origin(_one('{"intent":"unknown"}', MOVE)) == "model_unknown"


def test_a_layer_2_rejection_is_credited_to_the_validator():
    """A `formation` whose shape lacks its required slot: validate() falls back to HOVER.

    The model emitted `formation`, so the safe outcome is the validator's doing --- this
    is the shape of all three real fallbacks in `results/surface_b_preds/`.
    """
    assert _origin(_one('{"intent":"formation","shape":"grid"}', MOVE)) == "validator_fallback"


@pytest.mark.parametrize("raw", ["not json at all", ""])
def test_unparseable_output_falls_back_and_is_the_validators_doing(raw: str):
    assert _origin(_one(raw, MOVE)) == "validator_fallback"
