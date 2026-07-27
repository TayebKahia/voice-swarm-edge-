#!/usr/bin/env python3
"""Fixed WER normalisation and the edit-distance primitives built on it.

`prd.md` §2.7 defines WER as "word-level edit distance after fixed normalisation:
lowercase, strip punctuation, expand digits via the mapping in `eval/norm.py`".
Every WER figure in either thesis --- Exp-0's accent table and Exp-3's SNR sweep ---
passes through `normalise` below, so this module is the operational definition of
that sentence.

**The digit mapping is imported, not restated.** `data/numwords.py` already owns it,
because the round-trip augmentation guard needed it first. Two mappings in one
repository would let the WER figure and the augmentation guard disagree about what
the same utterance says, and the disagreement would be silent: both would run, both
would produce plausible numbers (ADR-0004 D6). So `words_to_digits` is imported and
this module adds only the surrounding text hygiene.

Order of operations is load-bearing:

    1. lowercase
    2. expand spelled-out numbers    "seventeen point three"  ->  "17.3"
    3. strip punctuation             but NOT a period between two digits
    4. collapse whitespace

Steps 2 and 3 cannot be swapped. Stripping punctuation first turns an already-digit
decimal into an integer --- "17.3" -> "173" --- which scores a correct transcription
as a substitution. Expanding first means step 3 only ever sees decimals this module
produced, and it is told to leave those alone.

One scope limit, inherited and deliberately not patched around: `words_to_digits`
treats "minus"/"negative" as a sign only before a *spelled-out* number, so a
recogniser emitting the half-converted "negative 2.5" is not folded onto "-2.5".
Fixing that would mean either editing `data/numwords.py` --- which would change the
round-trip corpus that is already built and frozen --- or adding a second digit rule
here, which is the exact thing the paragraph above forbids. It is left alone because
it cannot bite: WER feeds only Exp-0 and Exp-3 (§2.7), and neither corpus contains a
negative number. Exp-1 compares through `canon`, not through this module.

Errors are counted, not just rated. A WER of 0.12 made of deletions is a recogniser
dropping words; the same rate made of insertions is one hallucinating them. Exp-3's
SNR sweep is expected to shift between those regimes, so `edits` returns the three
counts and `wer` is derived from them rather than the other way round.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

if __package__ in (None, ""):  # `python eval/norm.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.numwords import words_to_digits

__all__ = ["normalise", "tokenise", "Edits", "edits", "wer", "corpus_wer"]

#: Two characters `words_to_digits` emits are part of a number rather than
#: punctuation: the decimal point between two digits, and a leading minus sign. Both
#: are parked on sentinels across the punctuation strip and restored afterwards.
#:
#: The sign matters more than it looks. Without this, "minus two point five" and
#: "two point five" both normalise to "2.5" and a sign error scores as a correct
#: transcription --- on an `altitude` or a `pos` component that is the difference
#: between climbing and descending, and Exp-3 exists to find exactly that class of
#: recogniser failure.
#:
#: The sentinels are uppercase, and `normalise` lowercases before it substitutes, so
#: no input character can collide with them.
_DECIMAL_SENTINEL = "Q"
_MINUS_SENTINEL = "Z"

_DECIMAL = re.compile(r"(?<=\d)\.(?=\d)")
#: A minus is a sign only when it opens a number. In "3-4" it is a separator and
#: becomes a word boundary like any other hyphen.
_MINUS = re.compile(r"(?<![a-z0-9])-(?=\d)")
_RESTORE = [
    (re.compile(f"(?<=\\d){_DECIMAL_SENTINEL}(?=\\d)"), "."),
    (re.compile(f"{_MINUS_SENTINEL}(?=\\d)"), "-"),
]

#: Apostrophes close up --- "Samantha's" -> "samanthas", "don't" -> "dont". Every
#: other punctuation mark opens a word boundary, so "well-known" becomes two words.
#: Both conventions are applied to reference and hypothesis alike, so neither can
#: favour one side; what matters is only that the choice is fixed and written down.
_APOSTROPHES = re.compile(r"['‘’ʼ]")

#: The sentinels are spared here and restored immediately after.
_NOT_WORD = re.compile(f"[^a-z0-9\\s{_DECIMAL_SENTINEL}{_MINUS_SENTINEL}]")
_WHITESPACE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Apply the §2.7 normalisation. Idempotent."""
    lowered = text.lower()
    expanded = words_to_digits(lowered)
    parked = _MINUS.sub(_MINUS_SENTINEL, _DECIMAL.sub(_DECIMAL_SENTINEL, expanded))
    closed = _APOSTROPHES.sub("", parked)
    stripped = _NOT_WORD.sub(" ", closed)
    for pattern, replacement in _RESTORE:
        stripped = pattern.sub(replacement, stripped)
    return _WHITESPACE.sub(" ", stripped).strip()


def tokenise(text: str) -> list[str]:
    """Normalise `text` and split it into the words WER counts over."""
    normalised = normalise(text)
    return normalised.split() if normalised else []


@dataclass(frozen=True)
class Edits:
    """Substitutions, deletions and insertions between one reference and one hypothesis.

    `ref_words` is the denominator. It is carried alongside the counts because
    corpus WER is *total errors over total reference words*, not the mean of the
    per-utterance rates --- averaging rates weights a three-word clip the same as a
    thirty-word one, which would let the shortest items in a bucket dominate it.
    """

    sub: int
    dele: int
    ins: int
    ref_words: int

    @property
    def total(self) -> int:
        return self.sub + self.dele + self.ins

    @property
    def rate(self) -> float:
        """WER for this pair alone. `nan` when the reference is empty."""
        if self.ref_words == 0:
            return float("nan")
        return self.total / self.ref_words


def edits(reference: str, hypothesis: str) -> Edits:
    """Levenshtein alignment over normalised words, with the three counts kept apart.

    Unit cost for all three operations, ties broken substitution > deletion >
    insertion. The tie-break is arbitrary but must be *fixed*: alignments of equal
    total cost can attribute the same error to a substitution or to a
    deletion-plus-insertion pair, and an unstable choice would make the S/D/I
    breakdown depend on dictionary iteration order rather than on the audio.
    """
    ref = tokenise(reference)
    hyp = tokenise(hypothesis)

    # row[j] = (cost, sub, del, ins) for ref[:i] against hyp[:j].
    row: list[tuple[int, int, int, int]] = [(j, 0, 0, j) for j in range(len(hyp) + 1)]

    for i in range(1, len(ref) + 1):
        previous, row = row, [(i, 0, i, 0)] + [(0, 0, 0, 0)] * len(hyp)
        for j in range(1, len(hyp) + 1):
            if ref[i - 1] == hyp[j - 1]:
                row[j] = previous[j - 1]
                continue
            substitute = (previous[j - 1][0] + 1, previous[j - 1][1] + 1, previous[j - 1][2], previous[j - 1][3])
            delete = (previous[j][0] + 1, previous[j][1], previous[j][2] + 1, previous[j][3])
            insert = (row[j - 1][0] + 1, row[j - 1][1], row[j - 1][2], row[j - 1][3] + 1)
            row[j] = min(substitute, delete, insert, key=lambda cell: cell[0])

    _, sub, dele, ins = row[len(hyp)]
    return Edits(sub=sub, dele=dele, ins=ins, ref_words=len(ref))


def wer(reference: str, hypothesis: str) -> float:
    """WER for a single pair. `nan` when the reference normalises to nothing."""
    return edits(reference, hypothesis).rate


def corpus_wer(pairs: Iterable[Sequence[str]]) -> float:
    """Pooled WER over `(reference, hypothesis)` pairs: total errors / total words.

    Pairs whose reference normalises to nothing contribute neither errors nor
    denominator --- they cannot be scored, and silently giving them a rate of 0 or 1
    would move the corpus figure without any recogniser having done anything.
    """
    errors = words = 0
    for reference, hypothesis in pairs:
        counted = edits(reference, hypothesis)
        if counted.ref_words == 0:
            continue
        errors += counted.total
        words += counted.ref_words
    return errors / words if words else float("nan")
