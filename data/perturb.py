#!/usr/bin/env python3
"""Hand-injected perturbation --- the 5% slice of the training mix.

`02_dataset_plan.md` §4 describes it as "homophones, dropped articles,
lowercase/no-punctuation (Whisper's output style)". It covers the errors the
round-trip does not reliably produce: `whisper.cpp` on clean Piper TTS at 20 dB is
often *correct*, so homophone confusions that a human speaker would trigger appear
rarely, and a 5% hand-built slice guarantees they appear at all.

The substitutions are the ones that matter for this vocabulary rather than a
general homophone list: `two`/`to`, `four`/`for`, `eight`/`ate`, `one`/`won`,
`meters`/`metres`. Each of those collides with a slot value --- "drone two" heard
as "drone to" is a dropped identifier, not a spelling mistake --- which is exactly
the failure the model has to learn to read through.

Seeded and idempotent: `perturb(text, key, seed)` returns the same string forever.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path
from typing import Callable

import numpy as np

if __package__ in (None, ""):  # `python data/perturb.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.numwords import words_to_digits

#: Applied word-for-word, case-insensitively, on token boundaries. The pairs are
#: directional lists: a rule fires only when the *first* form is present.
HOMOPHONES: tuple[tuple[str, str], ...] = (
    ("two", "to"),
    ("to", "two"),
    ("four", "for"),
    ("for", "four"),
    ("eight", "ate"),
    ("one", "won"),
    ("won", "one"),
    ("metres", "meters"),
    ("meters", "metres"),
    ("their", "there"),
    ("there", "their"),
    ("right", "write"),
    ("by", "buy"),
    ("no", "know"),
    ("hear", "here"),
    ("here", "hear"),
    ("wait", "weight"),
    ("sea", "see"),
    ("be", "bee"),
)

ARTICLES = ("a", "an", "the")

#: Retained for `test_perturb.py`'s coverage assertion and for readers: the digit
#: rewriting itself is `data/numwords.py`, which handles compound numbers.
DIGIT_WORDS: dict[str, str] = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
}

#: How many operations one row receives. More than two and the utterance stops
#: being a perturbation of the original and becomes a different sentence, which
#: belongs in the `unknown` bucket rather than this one.
OPERATIONS_PER_ROW = (1, 2)


def _stable_seed(*parts: object) -> int:
    blob = "\x1f".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(blob).digest()[:8], "big")


def _tokens(text: str) -> list[str]:
    return text.split()


#: Everything except word characters, whitespace, apostrophe, hyphen and period.
#: The period is spared here and filtered in a second pass, because a period with a
#: digit on each side is a decimal separator: stripping it turns "1.5" into "15", a
#: tenfold slot error paired with the *original* label. That is the one kind of
#: corruption this file must never introduce. Whisper writes decimals with the
#: point, so only sentence punctuation is ASR-style noise.
_NON_WORD = re.compile(r"[^\w\s'.-]")
_NON_DECIMAL_PERIOD = re.compile(r"(?<!\d)\.|\.(?!\d)")


def strip_punctuation(text: str, rng: np.random.Generator) -> str:
    """Whisper's output style at its plainest: no commas, no terminal stop.

    Decimal separators survive --- see `_NON_DECIMAL_PERIOD`.
    """
    stripped = _NON_DECIMAL_PERIOD.sub("", _NON_WORD.sub("", text))
    return re.sub(r"\s+", " ", stripped).strip()


def drop_article(text: str, rng: np.random.Generator) -> str:
    tokens = _tokens(text)
    positions = [i for i, t in enumerate(tokens) if t.strip(".,!?").lower() in ARTICLES]
    if not positions:
        return text
    index = positions[int(rng.integers(len(positions)))]
    return " ".join(tokens[:index] + tokens[index + 1 :])


def swap_homophone(text: str, rng: np.random.Generator) -> str:
    candidates = [
        (source, target)
        for source, target in HOMOPHONES
        if re.search(rf"\b{re.escape(source)}\b", text, flags=re.IGNORECASE)
    ]
    if not candidates:
        return text
    source, target = candidates[int(rng.integers(len(candidates)))]
    return re.sub(rf"\b{re.escape(source)}\b", target, text, count=1, flags=re.IGNORECASE)


def digitise_number(text: str, rng: np.random.Generator) -> str:
    """Rewrite spelled-out numbers as digits, the way whisper does.

    Delegates to `numwords`, which reads a whole number at once: word-at-a-time
    substitution turns "one point five" into "1 point five" rather than "1.5", and
    "one hundred and seventy-two" into "1 hundred and seventy-two".
    """
    return words_to_digits(text)


def lowercase(text: str, rng: np.random.Generator) -> str:
    return text.lower()


OPERATIONS: tuple[tuple[str, Callable[[str, np.random.Generator], str]], ...] = (
    ("strip_punctuation", strip_punctuation),
    ("drop_article", drop_article),
    ("swap_homophone", swap_homophone),
    ("digitise_number", digitise_number),
    ("lowercase", lowercase),
)


def perturb(text: str, item_key: str, seed: int = 42) -> tuple[str, list[str]]:
    """Return the perturbed text and the names of the operations that fired.

    An operation with nothing to act on --- `drop_article` on a sentence with no
    article --- returns the text unchanged and is not reported as having fired, so
    the audit trail says what actually happened rather than what was attempted.
    """
    rng = np.random.default_rng(_stable_seed(seed, "perturb", item_key))
    count = int(rng.integers(OPERATIONS_PER_ROW[0], OPERATIONS_PER_ROW[1] + 1))
    order = rng.permutation(len(OPERATIONS))

    result = text
    applied: list[str] = []
    for index in order:
        if len(applied) >= count:
            break
        name, operation = OPERATIONS[int(index)]
        candidate = operation(result, rng)
        if candidate != result:
            result = candidate
            applied.append(name)
    return result, applied
