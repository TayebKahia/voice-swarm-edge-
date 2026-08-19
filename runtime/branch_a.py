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

The trained spotter is two openWakeWord heads built by `train/train_wake.py`
from `data/wake_corpus.py`'s corpus, loaded by `load_trained()`. `WakeDetector`
is the seam: `BranchA` depends on the interface, not on `openwakeword.Model`
directly, so the membership rule and the threshold logic are tested against a
fake, and the real model against real clips only in the `slow` tests.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Protocol

from schema.schema import Abort, Command, Hover

__all__ = ["BRANCH_A_CLASSES", "KEYWORD_TO_INTENT", "WakeDetector", "BranchA", "load_trained"]

#: Written by `train/train_wake.py`: two ONNX heads plus `wake_heads.json`.
MODEL_DIR = Path(__file__).resolve().parent / "models" / "wake"

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
    """Two-class detection, threshold, debounce, publish-on-trigger (Table 4's `branch_a.py`).

    Table 5's two off-diagonal confusions -- hearing `abort` for `hold` and the
    reverse -- are both fail-safe (Sec. 4.2: "confusion within a fail-safe set
    is a benign error class"), so ties are broken by score alone; no class gets
    priority over the other.

    **One keyword, one trigger.** The spotter scores every 80 ms frame, and a
    spoken phrase stays above threshold for several consecutive frames. Without
    a debounce one `swarm abort` publishes a burst of aborts, each re-cancelling
    the Branch B decode, and every count Exp-2 reports -- false accepts per hour,
    the 2x2 cross-trigger matrix -- counts frames instead of keywords. A class
    fires on a frame above threshold only if its previous above-threshold frame
    is more than `debounce_s` back, which is exactly how `train/train_wake.py`
    counts events, so the runtime and the reported rates cannot disagree.

    The refractory period is **per class**. A `swarm abort` spoken straight after
    a `swarm hold` must still get through: it is the more conservative command,
    and a shared refractory would silence it.
    """

    def __init__(
        self,
        detector: WakeDetector,
        *,
        threshold: float = 0.5,
        debounce_s: float = 1.0,
        frame_s: float = 0.08,
    ) -> None:
        self._detector = detector
        self._threshold = threshold
        self._refractory_frames = int(round(debounce_s / frame_s))
        self._frame = 0
        self._last_above: dict[str, int | None] = {c: None for c in BRANCH_A_CLASSES}

    def poll(self, frame: object) -> Command | None:
        """Run one frame through the spotter; return the triggered command, if any."""
        scores = self._detector.predict(frame)
        best_class: str | None = None
        best_score = self._threshold
        for keyword_class in BRANCH_A_CLASSES:
            score = scores.get(keyword_class, 0.0)
            if score < self._threshold:
                continue
            last = self._last_above[keyword_class]
            self._last_above[keyword_class] = self._frame
            if last is not None and self._frame - last <= self._refractory_frames:
                continue  # the same utterance, still above threshold
            if score >= best_score:
                best_class, best_score = keyword_class, score
        self._frame += 1
        if best_class is None:
            return None
        return _build_command(KEYWORD_TO_INTENT[best_class])

    def reset(self) -> None:
        """Forget every refractory window and clear the spotter's own state.

        For a harness that runs independent trials through one loaded model
        (Exp-2): without it a trial inherits the previous take's debounce and
        feature buffer. `openwakeword.Model.reset()` primes that buffer with
        unseeded `np.random` noise, so a caller that wants the scores
        `train_wake.py` reports seeds numpy first, as `stream_scores` does.
        """
        self._frame = 0
        self._last_above = {c: None for c in BRANCH_A_CLASSES}
        reset = getattr(self._detector, "reset", None)
        if reset is not None:
            reset()


def load_trained(model_dir: Path = MODEL_DIR) -> BranchA:
    """`BranchA` over the trained heads, at the operating point `train_wake.py` declared.

    The heads are gitignored and regenerated, so a file that does not match the
    hash in `wake_heads.json` is refused rather than run: the threshold in that
    file was selected for those exact weights and means nothing for others.
    `openwakeword.Model` expects 80 ms int16 frames (1,280 samples) per `poll`.
    """
    from openwakeword.model import Model

    record = json.loads((model_dir / "wake_heads.json").read_text())
    if tuple(record["classes"]) != BRANCH_A_CLASSES:
        raise ValueError(f"wake_heads.json classes {record['classes']} != {BRANCH_A_CLASSES}")
    paths = []
    for name in BRANCH_A_CLASSES:
        path = model_dir / record["heads"][name]["file"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != record["heads"][name]["sha256"]:
            raise ValueError(f"{path} does not match wake_heads.json; re-run train/train_wake.py")
        paths.append(str(path))
    return BranchA(
        Model(wakeword_models=paths, inference_framework="onnx"),
        threshold=record["threshold"],
        debounce_s=record.get("debounce_s", 1.0),
    )
