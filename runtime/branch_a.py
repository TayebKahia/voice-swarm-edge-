"""Branch A -- the reflex path (PRD Sec. 4.2 & Table 5, Table 4's `branch_a.py`).

Contribution C4 is the membership rule itself: a keyword class belongs in
Branch A only if it is both latency-decisive and fail-safe under a false
accept (Sec. 4.2). Table 5 applies that rule to all ten schema intents and
exactly two survive. This module is the one place that result is encoded --
nothing else may add a third class without re-deriving Sec. 4.2, which is why
the mapping below is asserted at import time rather than left to review.

`swarm hold` -> `{"intent":"hover"}`, `swarm abort` -> `{"intent":"abort"}`.
Both keyword names follow `data/wake_corpus.py`'s own directory convention
(`data/wake/pos_swarm_hold/`, `data/wake/pos_swarm_abort/`), so the trained
classifier's class labels and this mapping's keys agree without a translation
table to keep in sync.

No trained keyword-spotter model exists yet: `data/wake_corpus.py` built the
positive/negative corpus (3,000 + 5,040 clips, per STATE.md), but training the
openWakeWord classifier on it is separate work and is not done here -- this
task is the wiring, not the model. `WakeDetector` is the seam: `BranchA`
depends on the interface, not on `openwakeword.Model` directly, so a trained
model slots in later without touching this module, and tests exercise the
membership rule and the smoothing/threshold logic today against a fake.
"""

from __future__ import annotations

from typing import Protocol

from schema.schema import Abort, Command, Hover

__all__ = ["BRANCH_A_CLASSES", "KEYWORD_TO_INTENT", "WakeDetector", "BranchA"]

#: Table 5's result: exactly two of schema v1.0's ten intents qualify for
#: Branch A. Order matches PRD Sec. 4.2's presentation (hold, then abort).
BRANCH_A_CLASSES: tuple[str, ...] = ("swarm_hold", "swarm_abort")

KEYWORD_TO_INTENT: dict[str, str] = {
    "swarm_hold": "hover",
    "swarm_abort": "abort",
}

# Guards against a silent third class: contribution C4 is exactly two intents,
# and Sec. 4.2 explains at length why the obvious third ("resume") is
# deliberately excluded. A drifted mapping here would defeat that argument
# without anyone noticing until Exp-2.
assert set(KEYWORD_TO_INTENT) == set(BRANCH_A_CLASSES)
assert set(KEYWORD_TO_INTENT.values()) == {"hover", "abort"}, (
    "Branch A membership drifted from PRD Table 5: exactly two intents, "
    "'hover' and 'abort', may ever appear here (contribution C4, Sec. 4.2)."
)


class WakeDetector(Protocol):
    """What `BranchA` needs from a keyword-spotter binding.

    Matches `openwakeword.Model.predict(frame) -> {class_name: score}`, which
    is the shape `openwakeword.Model` already returns -- this Protocol exists
    so tests can supply a fake without importing that library or a model file.
    """

    def predict(self, frame: object) -> dict[str, float]: ...


def _build_command(intent: str) -> Command:
    if intent == "hover":
        return Hover(intent="hover")
    if intent == "abort":
        return Abort(intent="abort")
    raise AssertionError(f"unreachable: Branch A cannot carry intent {intent!r} (Table 5)")


class BranchA:
    """Two-class detection, threshold, publish-on-trigger (Table 4's `branch_a.py`).

    Table 5's two off-diagonal confusions -- hearing `abort` for `hold` and the
    reverse -- are both fail-safe (Sec. 4.2: "confusion within a fail-safe set
    is a benign error class"), so ties are broken by score alone; no class gets
    priority over the other.
    """

    def __init__(self, detector: WakeDetector, *, threshold: float = 0.5) -> None:
        self._detector = detector
        self._threshold = threshold

    def poll(self, frame: object) -> Command | None:
        """Run one frame through the spotter; return the triggered command, if any."""
        scores = self._detector.predict(frame)
        best_class: str | None = None
        best_score = self._threshold
        for keyword_class in BRANCH_A_CLASSES:
            score = scores.get(keyword_class, 0.0)
            if score >= best_score:
                best_class, best_score = keyword_class, score
        if best_class is None:
            return None
        return _build_command(KEYWORD_TO_INTENT[best_class])
