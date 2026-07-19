"""Tests for hand-injected perturbation (`data/perturb.py`).

This is the 5% slice that covers what the round-trip does not reliably produce.
The properties that matter: it is seeded, it reports only the operations that
actually fired, and it never mangles a sentence past the point where it is still a
perturbation of the original.
"""

from __future__ import annotations

import pytest

from data.perturb import (
    ARTICLES,
    DIGIT_WORDS,
    OPERATIONS,
    OPERATIONS_PER_ROW,
    digitise_number,
    drop_article,
    lowercase,
    perturb,
    strip_punctuation,
    swap_homophone,
)
import numpy as np

RNG = lambda: np.random.default_rng(0)  # noqa: E731


def test_strip_punctuation_matches_whispers_plainest_style():
    assert strip_punctuation("Form a circle, radius five.", RNG()) == "Form a circle radius five"


def test_strip_punctuation_keeps_intra_word_marks():
    """"don't" must survive: the negation is the whole point of that row."""
    assert strip_punctuation("don't land yet.", RNG()) == "don't land yet"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("circle, 1.5 radius, all units", "circle 1.5 radius all units"),
        ("speed 0.4, drone 2", "speed 0.4 drone 2"),
        ("move to 10.0, 0.0, 3.0.", "move to 10.0 0.0 3.0"),
        ("climb to 4. now", "climb to 4 now"),
    ],
)
def test_strip_punctuation_never_eats_a_decimal_separator(text, expected):
    """"1.5" -> "15" is a tenfold slot error paired with the original label, and no
    recogniser produces it. It shipped once; this is the guard."""
    assert strip_punctuation(text, RNG()) == expected


def test_digitise_number_reads_a_compound_number_whole():
    """Word-at-a-time substitution gives "1 point five" and "1 hundred and
    seventy-two"; whisper writes "1.5" and "172"."""
    assert digitise_number("climb to one point five metres", RNG()) == "climb to 1.5 metres"
    assert digitise_number("spin one hundred and seventy-two right", RNG()) == "spin 172 right"


def test_drop_article_removes_exactly_one():
    out = drop_article("form a circle around the tree", RNG())
    assert len([t for t in out.split() if t in ARTICLES]) == 1


def test_drop_article_is_a_noop_without_articles():
    text = "drone two climb to four metres"
    assert drop_article(text, RNG()) == text


def test_homophone_swap_hits_the_slot_colliding_pairs():
    """"drone two" heard as "drone to" is a dropped identifier, not a typo."""
    assert swap_homophone("drone two go north", RNG()) == "drone to go north"


def test_homophone_swap_replaces_only_the_first_occurrence():
    out = swap_homophone("two and two", RNG())
    assert out == "to and two"


def test_homophone_swap_is_word_bounded():
    """"towards" must not become "twoards"."""
    text = "head towards the tower"
    assert swap_homophone(text, RNG()) == text


def test_digitise_number_matches_whispers_habit():
    assert digitise_number("climb to five metres", RNG()) == "climb to 5 metres"


def test_digit_words_cover_zero_through_ten():
    assert set(DIGIT_WORDS) >= {
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"
    }


def test_lowercase():
    assert lowercase("Form A Circle", RNG()) == "form a circle"


# --- the driver ------------------------------------------------------------


def test_perturb_is_deterministic():
    text = "Form a circle, radius five metres."
    assert perturb(text, "F001-p01") == perturb(text, "F001-p01")


def test_perturb_differs_by_item_key():
    text = "Form a circle, radius five metres."
    assert perturb(text, "F001-p01") != perturb(text, "F002-p01")


def test_perturb_applies_at_most_the_declared_number_of_operations():
    text = "Please, could the drone two climb to five metres?"
    for i in range(60):
        _, applied = perturb(text, f"row{i}")
        assert len(applied) <= OPERATIONS_PER_ROW[1]
        assert set(applied) <= {name for name, _ in OPERATIONS}


def test_perturb_reports_only_operations_that_changed_the_text():
    """An operation with nothing to act on is not reported as having fired."""
    for i in range(60):
        text = "north"
        result, applied = perturb(text, f"bare{i}")
        if result == text:
            assert applied == []


def test_perturb_changes_typical_command_text():
    changed = 0
    samples = [
        "Form a circle, radius five metres.",
        "Drone two, climb to four metres.",
        "Please move the swarm north by ten.",
        "Set the speed to one point five.",
    ]
    for i, text in enumerate(samples):
        result, applied = perturb(text, f"s{i}")
        if result != text:
            changed += 1
            assert applied
    assert changed == len(samples)


@pytest.mark.parametrize("text", ["", "   ", "."])
def test_perturb_tolerates_degenerate_input(text):
    result, applied = perturb(text, "degenerate")
    assert isinstance(result, str)
    assert isinstance(applied, list)
