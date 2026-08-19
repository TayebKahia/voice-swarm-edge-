"""runtime/stream.py -- the loop that drives both branches from one 80 ms frame stream.

Everything here runs against fakes and a fake clock: what could be silently wrong
is the timing arithmetic Exp-2 reports (a frame's due time, T0 on the wall clock)
and the one structural claim of Table 7 -- the frame loop never waits on Branch B.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pytest

from runtime.bus import BusMessage
from runtime.pipeline import BranchBTrace
from runtime.stream import FRAME, FRAME_S, StreamLoop, WavSource, pin
from runtime.vad import Utterance


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def test_wav_source_yields_whole_frames_zero_padded_at_their_due_time() -> None:
    clock = FakeClock()
    audio = np.arange(FRAME * 2 + 100, dtype=np.int16)
    source = WavSource(audio, clock=clock, sleep=clock.sleep)

    frames = list(source)

    assert [f.size for f, _ in frames] == [FRAME] * 3
    assert frames[2][0][100:].sum() == 0                   # the tail is padded, not dropped
    assert source.t_start == 100.0
    # A frame is due once its last sample would have been captured live.
    assert [t for _, t in frames] == pytest.approx([100 + FRAME_S * (i + 1) for i in range(3)])
    assert clock.now == pytest.approx(100 + 3 * FRAME_S)   # paced, not burst


def test_wav_source_can_run_faster_than_real_time() -> None:
    clock = FakeClock()
    list(WavSource(np.zeros(FRAME * 4, dtype=np.int16), realtime=False, clock=clock, sleep=clock.sleep))
    assert clock.sleeps == []


def _message(seq: int, branch: str = "A") -> BusMessage:
    return BusMessage(seq=seq, branch=branch, command={"intent": "abort"}, t_publish=0.0)


@dataclass
class FakeRuntime:
    """Fires Branch A on chosen frames; Branch B blocks until released."""

    fire_on: set[int] = field(default_factory=set)
    release: threading.Event = field(default_factory=threading.Event)
    frames_seen: int = 0
    processed: list[Path] = field(default_factory=list)
    worker_threads: set[str] = field(default_factory=set)

    def on_wake_frame(self, frame: object) -> BusMessage | None:
        index = self.frames_seen
        self.frames_seen += 1
        return _message(index) if index in self.fire_on else None

    def process(self, audio_path: Path) -> BranchBTrace:
        self.worker_threads.add(threading.current_thread().name)
        assert audio_path.is_file()
        self.release.wait(timeout=5)
        self.processed.append(audio_path)
        return BranchBTrace(seq=1, transcript="t", raw="{}", message=_message(1, "B"),
                            t_start=0, t_transcribed=0, t_parsed=0, t_published=0)


@dataclass
class FakeEndpointer:
    """Emits one utterance when frame `at` is fed, with T0 at `t0_s` of stream time."""

    at: int
    t0_s: float
    fed: int = 0

    def feed(self, chunk: np.ndarray) -> list[Utterance]:
        self.fed += 1
        if self.fed - 1 != self.at:
            return []
        return [Utterance(audio=np.zeros(1600, dtype=np.int16), start_s=0.0, end_s=self.t0_s - 0.25,
                          t0_s=self.t0_s)]


def test_loop_records_branch_a_triggers_against_the_frame_that_carried_them() -> None:
    clock = FakeClock()
    runtime = FakeRuntime(fire_on={3})
    loop = StreamLoop(runtime, FakeEndpointer(at=-1, t0_s=0), clock=clock)

    result = loop.run(WavSource(np.zeros(FRAME * 6, dtype=np.int16), clock=clock, sleep=clock.sleep))

    assert len(result.branch_a) == 1
    event = result.branch_a[0]
    assert event.frame_index == 3
    assert event.t_due == pytest.approx(100 + 4 * FRAME_S)
    assert event.stream_s == pytest.approx(4 * FRAME_S)
    assert len(result.frames) == 6


def test_t0_on_the_wall_clock_accounts_for_samples_the_vad_has_not_consumed() -> None:
    """Endpointer T0 is stream time of the last sample it ran; the frame may hold more."""
    clock = FakeClock()
    runtime = FakeRuntime()
    runtime.release.set()
    loop = StreamLoop(runtime, FakeEndpointer(at=4, t0_s=0.384), clock=clock)

    result = loop.run(WavSource(np.zeros(FRAME * 6, dtype=np.int16), clock=clock, sleep=clock.sleep))

    record, = result.branch_b
    # Frame 4 is due at stream time 0.40 s; the VAD had consumed up to 0.384 s of it.
    assert record.t0_wall == pytest.approx(100 + 0.384)
    assert record.trace is not None and record.trace.raw == "{}"


def test_the_frame_loop_never_waits_on_branch_b() -> None:
    """Table 7: Branch A keeps its frame period while Branch B is busy."""
    clock = FakeClock()
    runtime = FakeRuntime(fire_on={8})
    loop = StreamLoop(runtime, FakeEndpointer(at=1, t0_s=0.16), clock=clock)
    source = WavSource(np.zeros(FRAME * 10, dtype=np.int16), clock=clock, sleep=clock.sleep)

    done = threading.Event()
    results = []
    thread = threading.Thread(target=lambda: (results.append(loop.run(source)), done.set()))
    thread.start()
    # Every frame, including the Branch A trigger after the utterance, is processed
    # while Branch B is still blocked on the first utterance.
    for _ in range(200):
        if runtime.frames_seen == 10:
            break
        threading.Event().wait(0.01)
    assert runtime.frames_seen == 10
    assert not done.is_set()          # run() waits for Branch B to drain before returning
    runtime.release.set()
    thread.join(timeout=5)
    assert results[0].branch_a[0].frame_index == 8
    assert len(results[0].branch_b) == 1
    assert runtime.worker_threads == {"branch-b"}


def test_branch_b_can_be_switched_off_and_utterances_are_still_recorded() -> None:
    clock = FakeClock()
    runtime = FakeRuntime()
    loop = StreamLoop(runtime, FakeEndpointer(at=2, t0_s=0.2), branch_b=False, clock=clock)

    result = loop.run(WavSource(np.zeros(FRAME * 4, dtype=np.int16), clock=clock, sleep=clock.sleep))

    record, = result.branch_b
    assert record.trace is None
    assert runtime.processed == []


def test_frame_stats_carry_lag_and_compute() -> None:
    clock = FakeClock()

    class SlowRuntime(FakeRuntime):
        def on_wake_frame(self, frame: object) -> BusMessage | None:
            clock.now += 0.01                     # 10 ms of spotter compute
            return super().on_wake_frame(frame)

    loop = StreamLoop(SlowRuntime(), FakeEndpointer(at=-1, t0_s=0), clock=clock)
    result = loop.run(WavSource(np.zeros(FRAME * 3, dtype=np.int16), clock=clock, sleep=clock.sleep))

    assert [f.compute_s for f in result.frames] == pytest.approx([0.01] * 3)
    assert all(f.lag_s >= 0 for f in result.frames)


def test_pin_is_a_no_op_without_cores(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr("os.sched_setaffinity", lambda pid, cores: calls.append((pid, set(cores))))
    pin(None)
    pin({0})
    assert calls == [(0, {0})]
