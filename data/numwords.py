#!/usr/bin/env python3
"""Spelled-out numbers to digits --- "one hundred and twenty-eight point four" -> "128.4".

Written for one job and one job only: comparing a clean transcript against what
`whisper.cpp` heard. Whisper emits digits where the speaker said words, and this
corpus is full of spelled-out numbers, so a naive character comparison rates a
*correct* transcription as a destroyed one --- "one hundred and twenty-eight point
four" (37 characters) and "128.4" (5) share almost nothing. Fifteen perfectly
readable commands were being relabelled `unknown` on that basis, which would train
the model to refuse valid commands: a safety regression, not a data-quality one.

Scope is deliberately narrow. It handles the number forms this corpus actually
generates (`data/surface_forms.py`): zero through ninety-nine, hundreds with the
British "and", decimals via "point", and negatives via "minus"/"negative". It does
not handle thousands, ordinals, fractions or years, because the physical envelope
(§2.4) caps every slot at three integer digits and one decimal.

**`eval/norm.py` (Session 04) must use this same mapping.** WER is defined as
"word-level edit distance after fixed normalisation: lowercase, strip punctuation,
expand digits via the mapping in `eval/norm.py`" (§2.7). Two different digit
mappings in one repo means the WER figure and the augmentation guard disagree about
what the same utterance says.
"""

from __future__ import annotations

import re

UNITS: dict[str, int] = {
    "zero": 0, "nought": 0, "naught": 0, "oh": 0,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
}

TENS: dict[str, int] = {
    "twenty": 20, "thirty": 30, "forty": 40, "fourty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}

HUNDRED = "hundred"
POINT = "point"
NEGATIVES = {"minus", "negative"}

NUMBER_WORDS = set(UNITS) | set(TENS) | {HUNDRED}

#: `oh` and `point` are only number words in a numeric context. Outside one, "oh"
#: is a filler ("oh, and drone two") and dropping it would corrupt the sentence, so
#: neither can open a number.
CANNOT_OPEN = {"oh", POINT}

_TOKEN = re.compile(r"[a-z]+|[0-9]+(?:\.[0-9]+)?|[^\sa-z0-9]+|\s+", re.IGNORECASE)


def _format(value: float, is_decimal: bool) -> str:
    if is_decimal:
        text = f"{value:.10f}".rstrip("0")
        return text.rstrip(".") if text.endswith(".") else text
    return str(int(value))


def _consume(tokens: list[str], start: int) -> tuple[str | None, int]:
    """Parse one number starting at `tokens[start]`. Returns (text, next index)."""
    index = start
    negative = False

    if tokens[index].lower() in NEGATIVES:
        # Only a sign if a number actually follows.
        probe = index + 1
        while probe < len(tokens) and not tokens[probe].strip():
            probe += 1
        if probe >= len(tokens) or tokens[probe].lower() not in NUMBER_WORDS:
            return None, start
        negative, index = True, probe

    word = tokens[index].lower()
    if word not in NUMBER_WORDS or word in CANNOT_OPEN:
        return None, start

    total = 0
    current = 0
    seen = False
    end = index  # one past the last token that contributed, ignoring trailing space

    while index < len(tokens):
        token = tokens[index]
        if not token.strip():  # whitespace: crossed, but not consumed
            index += 1
            continue
        lowered = token.lower()

        if lowered in UNITS:
            current += UNITS[lowered]
            seen = True
        elif lowered in TENS:
            current += TENS[lowered]
            seen = True
        elif lowered == HUNDRED and seen:
            current = max(current, 1) * 100
        elif lowered == "and" and seen and current % 100 == 0 and current:
            pass  # "one hundred and twenty-eight"
        elif lowered == "-" and seen:
            pass  # "twenty-eight" arrives as three tokens
        else:
            break
        index += 1
        end = index

    if not seen:
        return None, start
    total += current

    # A decimal tail: "point four", "point nought five".
    probe = end
    while probe < len(tokens) and not tokens[probe].strip():
        probe += 1
    if probe < len(tokens) and tokens[probe].lower() == POINT:
        digits: list[str] = []
        cursor = probe + 1
        tail_end = cursor
        while cursor < len(tokens):
            token = tokens[cursor]
            if not token.strip():
                cursor += 1
                continue
            lowered = token.lower()
            if lowered in UNITS and UNITS[lowered] <= 9:
                digits.append(str(UNITS[lowered]))
                cursor += 1
                tail_end = cursor
                continue
            break
        if digits:
            value = float(f"{total}.{''.join(digits)}")
            return ("-" if negative else "") + _format(value, True), tail_end

    return ("-" if negative else "") + _format(total, False), end


def words_to_digits(text: str) -> str:
    """Rewrite every spelled-out number in `text` as digits, leaving the rest alone.

    Idempotent on text that is already digits, so it is safe to apply to both sides
    of a comparison without knowing which side came from the recogniser.
    """
    tokens = _TOKEN.findall(text)
    out: list[str] = []
    index = 0
    while index < len(tokens):
        rendered, next_index = _consume(tokens, index)
        if rendered is None:
            out.append(tokens[index])
            index += 1
        else:
            out.append(rendered)
            index = next_index
    return "".join(out)
