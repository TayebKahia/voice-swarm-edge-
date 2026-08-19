"""One audio stream, both branches (Figure 1; the loop `runtime/pipeline.py` said was missing).

Every 80 ms frame goes to Branch A's spotter and to Branch B's endpointer, on the
calling thread -- Table 7's core 0. An endpointed utterance is handed to a worker
thread -- cores 1-3 -- which runs `PipelineRuntime.process` (STT, parse, validate,
publish). The frame loop never waits on that worker. That is the property NFR-1
depends on: Branch A must hold its budget *while* Branch B is decoding, so Branch B
may not be able to delay the next frame.

**The frame source is swappable.** A source is any iterable of `(frame, t_due)`:
1,280 int16 samples and the `time.monotonic()` instant the frame's last sample is
in the buffer. `WavSource` replays a file in real time, which is what Exp-2 does
deliberately: idle and loaded trials must hear identical audio, and every trial must
be reproducible from the repo. A microphone source (A11) yields the same pairs from
the capture callback, and nothing below changes.

**Times are wall-clock, anchored as prd.md Sec. 4.4 and 4.7 anchor them.** A
Branch A trigger carries the due time of the frame that fired it; latency from
keyword offset is the bus's `t_publish` minus the offset's wall time, so frame
quantisation is inside the figure, as Sec. 4.4 says it must be. A Branch B utterance
carries T0 on the wall clock: the endpointer's T0 is stream time of the last sample
it ran through the VAD, which can be up to one 32 ms window short of the frame's
end, and that remainder is subtracted rather than ignored.

Core pinning (`pin`) is per thread: Linux `sched_setaffinity(0, ...)` applies to the
calling thread, and a subprocess inherits the mask of the thread that spawned it --
so `whisper-cli`, started by the worker, lands on the worker's cores.
"""

from __future__ import annotations

import os
import queue
import tempfile
import threading
import time
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from runtime.bus import BusMessage
from runtime.pipeline import BranchBTrace
from runtime.vad import RATE, Utterance

__all__ = ["FRAME", "FRAME_S", "WavSource", "StreamLoop", "StreamResult", "pin"]

#: openWakeWord's frame: 80 ms at 16 kHz. The endpointer takes any chunk size.
FRAME = 1280
FRAME_S = FRAME / RATE


def pin(cores: set[int] | None) -> None:
    """Pin the calling thread (and anything it spawns from now on) to `cores`."""
    if cores:
        os.sched_setaffinity(0, cores)


class WavSource:
    """Replay int16 audio as 80 ms frames, each released at its real-time due instant."""

    def __init__(
        self,
        audio: np.ndarray,
        *,
        realtime: bool = True,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        audio = np.asarray(audio, dtype=np.int16)
        padded = -(-audio.size // FRAME) * FRAME
        self._audio = np.concatenate([audio, np.zeros(padded - audio.size, dtype=np.int16)])
        self._realtime = realtime
        self._clock = clock
        self._sleep = sleep
        self.t_start: float | None = None

    def __iter__(self) -> Iterator[tuple[np.ndarray, float]]:
        self.t_start = self._clock()
        for i in range(self._audio.size // FRAME):
            t_due = self.t_start + (i + 1) * FRAME_S
            if self._realtime:
                wait = t_due - self._clock()
                if wait > 0:
                    self._sleep(wait)
            yield self._audio[i * FRAME : (i + 1) * FRAME], t_due


class _Runtime(Protocol):
    def on_wake_frame(self, frame: object) -> BusMessage | None: ...
    def process(self, audio_path: Path) -> BranchBTrace: ...


class _Endpointer(Protocol):
    def feed(self, chunk: np.ndarray) -> list[Utterance]: ...


@dataclass(frozen=True)
class FrameStat:
    """Table 7's core-0 check: per-frame compute must stay under the frame period."""

    t_due: float
    lag_s: float       # how late the loop picked the frame up
    compute_s: float   # spotter + endpointer for this frame


@dataclass(frozen=True)
class BranchAEvent:
    message: BusMessage
    frame_index: int
    t_due: float
    stream_s: float    # stream time at the end of the frame that fired


@dataclass(frozen=True)
class BranchBRecord:
    utterance: Utterance
    t0_wall: float
    trace: BranchBTrace | None      # None when Branch B was switched off
    t_ready: float | None = None    # worker back at the queue, ready for the next utterance


@dataclass(frozen=True)
class StreamResult:
    frames: list[FrameStat]
    branch_a: list[BranchAEvent]
    branch_b: list[BranchBRecord]


class StreamLoop:
    """Drive `runtime` from one frame source. One `run()` per stream (per trial)."""

    def __init__(
        self,
        runtime: _Runtime,
        endpointer: _Endpointer,
        *,
        branch_b: bool = True,
        front_cores: set[int] | None = None,
        back_cores: set[int] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._runtime = runtime
        self._endpointer = endpointer
        self._branch_b = branch_b
        self._front = front_cores
        self._back = back_cores
        self._clock = clock

    def run(self, source: Iterable[tuple[np.ndarray, float]]) -> StreamResult:
        pin(self._front)
        frames: list[FrameStat] = []
        events: list[BranchAEvent] = []
        records: list[BranchBRecord] = []
        work: queue.Queue[tuple[Utterance, float] | None] = queue.Queue()

        with tempfile.TemporaryDirectory(prefix="stream-") as tmp:
            worker = threading.Thread(
                target=self._worker, args=(work, records, Path(tmp)), name="branch-b", daemon=True
            )
            if self._branch_b:
                worker.start()
            delivered = 0
            for index, (frame, t_due) in enumerate(source):
                t_pick = self._clock()
                delivered += frame.size
                message = self._runtime.on_wake_frame(frame)
                if message is not None:
                    events.append(BranchAEvent(message, index, t_due, delivered / RATE))
                for utterance in self._endpointer.feed(frame):
                    t0_wall = t_due - (delivered / RATE - utterance.t0_s)
                    if self._branch_b:
                        work.put((utterance, t0_wall))
                    else:
                        records.append(BranchBRecord(utterance, t0_wall, None))
                frames.append(FrameStat(t_due, max(0.0, t_pick - t_due), self._clock() - t_pick))
            if self._branch_b:
                work.put(None)
                worker.join()
        return StreamResult(frames, events, records)

    def _worker(self, work: queue.Queue, records: list[BranchBRecord], tmp: Path) -> None:
        pin(self._back)
        n = 0
        while (item := work.get()) is not None:
            utterance, t0_wall = item
            path = utterance.to_wav(tmp / f"u{n:03d}.wav")
            n += 1
            trace = self._runtime.process(path)
            records.append(BranchBRecord(utterance, t0_wall, trace, self._clock()))
