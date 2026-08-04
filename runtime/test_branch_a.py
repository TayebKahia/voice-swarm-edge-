"""runtime/branch_a.py -- Table 5's membership rule (contribution C4).

`BranchA` is exercised against a fake `WakeDetector`: no trained
openWakeWord model exists yet (see `runtime/branch_a.py`'s module docstring),
so these tests are the only guard on the membership rule until one does.
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
