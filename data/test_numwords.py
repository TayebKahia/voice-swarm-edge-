"""Tests for spelled-out-number conversion (`data/numwords.py`).

The regression this file guards against is concrete: before it existed, guard (ii)
relabelled fifteen correctly-transcribed commands as `unknown` purely because
whisper wrote "128.4" where the speaker said "one hundred and twenty-eight point
four". Training on those rows would teach the model to refuse valid commands.
"""

from __future__ import annotations

import pytest

from data.numwords import words_to_digits as convert


@pytest.mark.parametrize(
    ("spoken", "expected"),
    [
        ("zero", "0"),
        ("nought", "0"),
        ("five", "5"),
        ("ten", "10"),
        ("nineteen", "19"),
        ("twenty", "20"),
        ("twenty-seven", "27"),
        ("forty-eight", "48"),
        ("ninety-nine", "99"),
        ("one hundred", "100"),
        ("one hundred and seventy-two", "172"),
        ("one hundred and twenty-eight point four", "128.4"),
        ("nought point five", "0.5"),
        ("one point one", "1.1"),
        ("seventeen point two", "17.2"),
        ("minus nineteen point eight", "-19.8"),
        ("negative three", "-3"),
    ],
)
def test_bare_numbers(spoken, expected):
    assert convert(spoken) == expected


@pytest.mark.parametrize(
    ("spoken", "expected"),
    [
        ("go west twenty-seven", "go west 27"),
        ("drones two through three", "drones 2 through 3"),
        ("forty-eight point two to the south at one point one", "48.2 to the south at 1.1"),
        ("birds one, two and four, spin one hundred and seventy-two right",
         "birds 1, 2 and 4, spin 172 right"),
        ("move erm, to the east twenty-seven point five metres",
         "move erm, to the east 27.5 metres"),
        ("all drones, position seventeen point two, minus nineteen point eight, eleven",
         "all drones, position 17.2, -19.8, 11"),
    ],
)
def test_numbers_in_sentences_keep_their_spacing(spoken, expected):
    """Eating the space after a number would corrupt every following comparison."""
    assert convert(spoken) == expected


def test_is_idempotent_on_digits():
    """Safe to apply to both sides of a comparison without knowing their origin."""
    for text in ("128.4 already digits", "move north 10", "speed 0.4, drone 2"):
        assert convert(text) == text
        assert convert(convert(text)) == convert(text)


@pytest.mark.parametrize(
    "text",
    [
        "oh, and drone two",       # "oh" as a filler, not a zero
        "point of no return",      # "point" outside a number
        "minus the payload",       # "minus" with no number after it
        "a hundred metres",        # bare article: not a form this corpus generates
    ],
)
def test_number_words_outside_a_numeric_context_are_left_alone(text):
    converted = convert(text)
    # The non-numeric words must survive intact; "drone two" may become "drone 2".
    for word in ("oh,", "point of no return", "minus the payload", "hundred metres"):
        if word in text:
            assert word in converted or word.replace("two", "2") in converted


def test_filler_oh_is_not_swallowed():
    assert convert("oh, and drone two").startswith("oh, and drone")


def test_conversion_rescues_a_correct_transcription_from_looking_destroyed():
    """The exact regression: character similarity before and after."""
    from difflib import SequenceMatcher

    clean = "birds one thru two let's turn call it one hundred and twenty-eight point four"
    asr = "Birds 1 through 2, let's turn call it 128.4"

    raw = SequenceMatcher(None, clean.lower(), asr.lower()).ratio()
    normalised = SequenceMatcher(None, convert(clean).lower(), convert(asr).lower()).ratio()

    assert raw < 0.60
    assert normalised > 0.80


@pytest.mark.parametrize("text", ["", "   ", "...", "point", "minus", "and"])
def test_degenerate_input(text):
    assert isinstance(convert(text), str)


def test_empty_and_whitespace_are_preserved():
    assert convert("") == ""
    assert convert("   ") == "   "
