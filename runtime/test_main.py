"""runtime/main.py's `ReflexGate`: which utterances the parse path may still publish.

What could be silently wrong is the matching -- which utterance a reflex trigger suppresses --
and that depends on when the parse worker picks an utterance up, relative to the frames. The
first tests drive the gate's three calls in an explicit order, as `StreamLoop` would make them
(per frame: spotter, then endpointer; the worker's `process()` whenever it gets there), so the
worker's timing is chosen rather than raced. The last runs it inside the real `StreamLoop`.
Frames are 80 ms, so frame k ends at stream time 0.08 * (k + 1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from runtime.bus import BusMessage
from runtime.main import ReflexGate
from runtime.pipeline import BranchBTrace
from runtime.stream import FRAME, FRAME_S, StreamLoop, WavSource
from runtime.vad import Utterance


@dataclass
class FakeRuntime:
    """Fires the reflex on chosen frames; the parse path publishes one message per utterance."""

    fire_on: set[int] = field(default_factory=set)
    frames_seen: int = 0
    processed: int = 0

    def on_wake_frame(self, frame: object) -> BusMessage | None:
        index, self.frames_seen = self.frames_seen, self.frames_seen + 1
        if index not in self.fire_on:
            return None
        return BusMessage(seq=100 + index, branch="A", command={"intent": "hover"}, t_publish=0.0)

    def process(self, audio_path: Path) -> BranchBTrace:
        self.processed += 1
        message = BusMessage(seq=self.processed, branch="B", command={"intent": "formation"}, t_publish=0.0)
        return BranchBTrace(seq=message.seq, transcript="t", raw="{}", message=message,
                            t_start=0, t_transcribed=0, t_parsed=0, t_published=0)


@dataclass
class FakeEndpointer:
    """Emits an utterance starting at `start_s` when the frame keyed by its index is fed."""

    starts: dict[int, float]
    fed: int = 0

    def feed(self, chunk: np.ndarray) -> list[Utterance]:
        index, self.fed = self.fed, self.fed + 1
        if index not in self.starts:
            return []
        t0 = (index + 1) * FRAME_S
        return [Utterance(audio=np.zeros(1600, dtype=np.int16), start_s=self.starts[index],
                          end_s=t0 - 0.35, t0_s=t0)]


class Drive:
    def __init__(self, fire_on: set[int], starts: dict[int, float]) -> None:
        self.runtime = FakeRuntime(fire_on=fire_on)
        self.gate = ReflexGate(self.runtime, FakeEndpointer(starts))
        self.frame = np.zeros(FRAME, dtype=np.int16)

    def frames(self, n: int) -> "Drive":
        for _ in range(n):
            self.gate.on_wake_frame(self.frame)
            self.gate.feed(self.frame)
        return self

    def parse(self) -> bool:
        """The worker takes the next utterance; True if it was published."""
        return self.gate.process(Path("u.wav")).message is not None


def test_a_reflex_during_the_utterance_suppresses_its_parse():
    # "swarm hold": speech from 0.40 s, reflex on frame 10 (0.88 s), endpoint on frame 16.
    d = Drive({10}, {16: 0.40}).frames(17)
    assert d.parse() is False
    assert d.runtime.processed == 0                    # never transcribed, no number drawn


def test_an_utterance_with_no_reflex_is_parsed_as_before():
    d = Drive(set(), {16: 0.40}).frames(17)
    assert d.parse() is True


def test_a_reflex_before_the_utterance_does_not_suppress_it():
    d = Drive({2}, {16: 0.40}).frames(17)              # reflex at 0.24 s, speech from 0.40 s
    assert d.parse() is True


def test_a_reflex_in_the_frame_that_ends_the_utterance_still_belongs_to_it():
    d = Drive({16}, {16: 0.40}).frames(17)             # StreamLoop polls the spotter first
    assert d.parse() is False


def test_step_four_the_line_is_parsed_and_the_hold_is_not():
    # "form a line ..." endpointed on frame 12 and picked up at once; "swarm hold" from 1.20 s,
    # reflex on frame 18, endpoint on frame 24. The line reaches the parser as before, where the
    # reflex's preemption and the ordering rule deal with it; only the hold's copy is dropped.
    d = Drive({18}, {12: 0.10, 24: 1.20}).frames(13)
    assert d.parse() is True
    d.frames(12)
    assert d.parse() is False


def test_a_reflex_just_after_the_endpoint_suppresses_a_command_not_yet_started():
    # One breath: the endpointer closes the utterance on frame 20, the spotter reports on 22,
    # before the worker has picked the utterance up.
    d = Drive({22}, {20: 0.10}).frames(24)
    assert d.parse() is False


def test_a_command_queued_behind_a_slow_parse_does_not_override_a_later_hold():
    # Command A endpointed on frame 8 and started; command B endpointed on frame 16 while A is
    # still being parsed; "swarm hold" fires on frame 20. When the worker reaches B it would draw
    # a number newer than the hold's, so B is suppressed. A's number was drawn before the hold,
    # so it is the consumer's ordering rule that discards it, as before.
    d = Drive({20}, {8: 0.10, 16: 0.75}).frames(9)
    assert d.parse() is True                           # A started before the hold
    d.frames(16)
    assert d.parse() is False                          # B had not


def test_a_reflex_suppresses_only_utterances_that_started_before_it():
    d = Drive({14}, {8: 0.10, 16: 0.80, 24: 1.45}).frames(25)
    assert [d.parse(), d.parse(), d.parse()] == [False, False, True]


def test_inside_the_real_stream_loop():
    runtime = FakeRuntime(fire_on={10})
    gate = ReflexGate(runtime, FakeEndpointer({16: 0.40}))
    result = StreamLoop(gate, gate).run(WavSource(np.zeros(FRAME * 30, dtype=np.int16), realtime=False))
    record, = result.branch_b
    assert record.trace.aborted and record.trace.message is None
    assert runtime.processed == 0
    assert len(result.branch_a) == 1                   # the reflex itself is untouched
