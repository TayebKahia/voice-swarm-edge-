"""runtime/branch_a.py -- Table 5's membership rule (contribution C4).

The membership rule is exercised against a fake `WakeDetector`, so it holds
whatever the model does. The trained heads from `train/train_wake.py` are
tested at the end of the file, on held-out clips, marked `slow`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from runtime.branch_a import BRANCH_A_CLASSES, KEYWORD_TO_INTENT, BranchA
from schema.schema import Abort, Hover, INTENTS


@dataclass
class FakeDetector:
    scores: dict[str, float] = field(default_factory=dict)

    def predict(self, frame: object) -> dict[str, float]:
        return self.scores


def test_membership_is_exactly_two_intents() -> None:
    """Table 5 applies the two-part rule (Sec. 4.2) to all ten schema intents
    and exactly two survive. This test is the one place a silently-added
    third class would be caught."""
    assert BRANCH_A_CLASSES == ("swarm_hold", "swarm_abort")
    assert set(KEYWORD_TO_INTENT.values()) == {"hover", "abort"}
    # And both really are schema intents, not typos.
    assert set(KEYWORD_TO_INTENT.values()) <= set(INTENTS)


def test_poll_returns_hover_on_swarm_hold() -> None:
    branch_a = BranchA(FakeDetector({"swarm_hold": 0.9}))
    command = branch_a.poll(frame=None)
    assert command == Hover(intent="hover")


def test_poll_returns_abort_on_swarm_abort() -> None:
    branch_a = BranchA(FakeDetector({"swarm_abort": 0.95}))
    command = branch_a.poll(frame=None)
    assert command == Abort(intent="abort")


def test_poll_returns_none_below_threshold() -> None:
    branch_a = BranchA(FakeDetector({"swarm_hold": 0.4}), threshold=0.5)
    assert branch_a.poll(frame=None) is None


def test_poll_returns_none_with_no_scores() -> None:
    branch_a = BranchA(FakeDetector({}))
    assert branch_a.poll(frame=None) is None


def test_poll_picks_the_higher_scoring_class() -> None:
    """Sec. 4.2: both off-diagonal confusions are fail-safe, so ties are
    broken purely by score -- no class gets priority over the other."""
    branch_a = BranchA(FakeDetector({"swarm_hold": 0.6, "swarm_abort": 0.99}))
    assert branch_a.poll(frame=None) == Abort(intent="abort")

    branch_a = BranchA(FakeDetector({"swarm_hold": 0.99, "swarm_abort": 0.6}))
    assert branch_a.poll(frame=None) == Hover(intent="hover")


def test_poll_ignores_classes_outside_branch_a() -> None:
    """A detector reporting some other class name (e.g. a future model
    trained with extra heads) must not leak a third intent through."""
    branch_a = BranchA(FakeDetector({"takeoff": 0.99}))
    assert branch_a.poll(frame=None) is None


def test_threshold_is_a_configurable_boundary() -> None:
    branch_a = BranchA(FakeDetector({"swarm_hold": 0.5}), threshold=0.5)
    assert branch_a.poll(frame=None) == Hover(intent="hover")

    branch_a = BranchA(FakeDetector({"swarm_hold": 0.4999}), threshold=0.5)
    assert branch_a.poll(frame=None) is None


# --- the trained heads (train/train_wake.py) ---------------------------------

import json as _json
from pathlib import Path as _Path

import numpy as _np

from runtime.branch_a import MODEL_DIR

_REPO = _Path(__file__).resolve().parent.parent
_HAVE_HEADS = all((MODEL_DIR / f"{n}.onnx").exists() for n in BRANCH_A_CLASSES)


def _stream(branch_a: BranchA, wav: _Path) -> set[str]:
    """Feed a padded clip in 80 ms frames; return the intents that fired."""
    import soundfile as sf

    audio, _ = sf.read(str(wav), dtype="int16")
    pad = _np.zeros(16_000, dtype=_np.int16)
    audio = _np.concatenate([pad, audio, pad])
    fired = set()
    for i in range(0, audio.size - 1280 + 1, 1280):
        command = branch_a.poll(audio[i : i + 1280])
        if command is not None:
            fired.add(command.intent)
    return fired


def _first_test_clip(label: str) -> _Path:
    manifest = _json.loads((_REPO / "data/wake/wake_manifest.json").read_text())
    clip = next(c for c in manifest["clips"] if c["label"] == label and c["split"] == "test"
                and c["rir"] is None and c["noise_key"] is None)
    return _REPO / clip["path"]


@pytest.mark.slow
@pytest.mark.skipif(not _HAVE_HEADS, reason="run train/train_wake.py first")
@pytest.mark.parametrize(("label", "intent"), [("pos_swarm_hold", "hover"), ("pos_swarm_abort", "abort")])
def test_trained_heads_fire_on_a_held_out_keyword(label: str, intent: str) -> None:
    from runtime.branch_a import load_trained

    assert intent in _stream(load_trained(), _first_test_clip(label))


@pytest.mark.slow
@pytest.mark.skipif(not _HAVE_HEADS, reason="run train/train_wake.py first")
def test_trained_heads_refuse_weights_that_do_not_match_the_record(tmp_path: _Path) -> None:
    import shutil

    from runtime.branch_a import load_trained

    for f in MODEL_DIR.iterdir():
        shutil.copy(f, tmp_path / f.name)
    (tmp_path / "swarm_hold.onnx").write_bytes((tmp_path / "swarm_hold.onnx").read_bytes() + b"\0")
    with pytest.raises(ValueError, match="does not match"):
        load_trained(tmp_path)


# --- debounce: one keyword, one trigger ---------------------------------------


@dataclass
class ScriptedDetector:
    """Returns the next score dict on each predict() call."""

    script: list[dict[str, float]]
    calls: int = 0

    def predict(self, frame: object) -> dict[str, float]:
        scores = self.script[self.calls] if self.calls < len(self.script) else {}
        self.calls += 1
        return scores


def _run(script: list[dict[str, float]], **kwargs: float) -> list[str | None]:
    branch_a = BranchA(ScriptedDetector(script), threshold=0.5, **kwargs)
    out = []
    for _ in script:
        command = branch_a.poll(frame=None)
        out.append(None if command is None else command.intent)
    return out


def test_a_sustained_keyword_fires_once() -> None:
    """Eight consecutive above-threshold frames are one spoken phrase, one command."""
    fired = _run([{"swarm_abort": 0.99}] * 8)
    assert fired == ["abort"] + [None] * 7


def test_a_second_keyword_after_the_refractory_fires_again() -> None:
    # 1.0 s / 80 ms = 12.5 -> 12 frames. A gap of 13 frames is a new event.
    script = [{"swarm_hold": 0.9}] + [{}] * 12 + [{"swarm_hold": 0.9}]
    assert _run(script).count("hover") == 2


def test_a_second_keyword_inside_the_refractory_is_the_same_event() -> None:
    script = [{"swarm_hold": 0.9}] + [{}] * 11 + [{"swarm_hold": 0.9}]
    assert _run(script).count("hover") == 1


def test_abort_is_not_silenced_by_a_hold_refractory() -> None:
    """The more conservative command must always get through (per-class refractory)."""
    script = [{"swarm_hold": 0.9}] * 3 + [{"swarm_abort": 0.9}] * 3
    assert _run(script) == ["hover", None, None, "abort", None, None]


def test_debounce_matches_the_training_evaluator() -> None:
    """runtime and results/wake_training.md must count the same events."""
    import numpy as np

    from train.train_wake import count_events

    rng = np.random.default_rng(0)
    trace = (rng.random(400) > 0.93).astype(float)  # sparse bursts of above-threshold frames
    fired = _run([{"swarm_hold": v} for v in trace])
    assert fired.count("hover") == count_events(trace, 0.5)


def test_reset_starts_a_new_trial_with_no_refractory_and_a_clean_detector() -> None:
    """Exp-2 streams one take per trial through one loaded model; a trial must not
    inherit the previous take's debounce window or the spotter's feature buffer."""

    @dataclass
    class ResettableDetector(ScriptedDetector):
        resets: int = 0

        def reset(self) -> None:
            self.resets += 1

    detector = ResettableDetector([{"swarm_hold": 0.9}] * 4)
    branch_a = BranchA(detector, threshold=0.5)
    assert branch_a.poll(None) is not None
    assert branch_a.poll(None) is None          # same phrase, inside the refractory
    branch_a.reset()
    assert detector.resets == 1
    assert branch_a.poll(None) is not None      # a new trial fires at once


def test_reset_tolerates_a_detector_without_one() -> None:
    BranchA(FakeDetector({})).reset()
