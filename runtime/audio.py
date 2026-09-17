"""Live microphone capture -- the frame source `runtime/stream.py` was written to accept.

`MicSource` yields exactly what `WavSource` yields: `(frame, t_due)`, 1,280 int16 samples at
16 kHz and the `time.monotonic()` instant the frame's last sample was in the buffer. Nothing
downstream changes; the capture source replaces the replay (Chapter 4, sec:audio-chain).

**The chain reproduces the one the golden set went through**, because the spotter's operating
point and every recognition figure were measured on that audio:

    capture   48 kHz mono from the USB microphone, found by name through
              `data/record_session.find_capture_device` -- the device S1 was recorded on --
              opened at its native rate, never through ALSA `plug` (prd.md D4)
    DC        removed. Offline, `data/resample.remove_dc` subtracted each file's mean; a live
              stream has no file, so a one-pole DC blocker (corner about 3.8 Hz) does it. This is
              the one step that differs from the golden set's.
    gain      one fixed scalar, like `data/resample.py`'s one gain per session. The default is
              S1's own (`data/audio/s1_16k/resample_manifest.json`), which lands live speech at the
              corpus's level only if the capture level in alsamixer is the one S1 was recorded at;
              `python runtime/main.py --level-check` prints the level to check it.
    resample  soxr at VHQ, 48 -> 16 kHz: the converter and quality of `data/resample.resample`,
              run as a stream (`soxr.ResampleStream`) rather than over a whole file.

`t_due` is taken when the capture callback delivers the 80 ms block that completes the frame. It
orders frames; no latency is reported from a live run (Chapter 6, sec:demonstration-protocol).
"""

from __future__ import annotations

import json
import queue
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import numpy as np

from runtime.stream import FRAME
from runtime.vad import RATE

__all__ = ["CAPTURE_RATE", "MicSource", "session_gain_db"]

REPO_ROOT = Path(__file__).resolve().parent.parent
GAIN_MANIFEST = REPO_ROOT / "data" / "audio" / "s1_16k" / "resample_manifest.json"

#: prd.md D4: the rate every master was captured at.
CAPTURE_RATE = 48_000
#: One 80 ms spotter frame of capture.
BLOCK = CAPTURE_RATE * FRAME // RATE
#: y[n] = x[n] - x[n-1] + a y[n-1]; corner (1 - a) * fs / (2 pi), about 3.8 Hz at 48 kHz.
DC_POLE = 0.9995


def session_gain_db(manifest: Path = GAIN_MANIFEST) -> float:
    """The golden session's gain, as `data/resample.py` recorded it."""
    return float(json.loads(manifest.read_text(encoding="utf-8"))["session_gain_db"])


class MicSource:
    """80 ms int16 frames at 16 kHz from the USB microphone, until `close()`."""

    def __init__(
        self,
        device: str | None = None,
        *,
        gain_db: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.device = device
        self.gain_db = session_gain_db() if gain_db is None else float(gain_db)
        self._gain = 10.0 ** (self.gain_db / 20.0)
        self._clock = clock
        self._stop = threading.Event()
        self.device_name: str | None = None
        #: Blocks PortAudio reported as overrun: audio lost before it reached this process.
        self.overflows = 0

    def close(self) -> None:
        self._stop.set()

    def __iter__(self) -> Iterator[tuple[np.ndarray, float]]:
        import sounddevice as sd
        import soxr
        from scipy.signal import lfilter

        from data.record_session import find_capture_device

        index, self.device_name = find_capture_device(self.device)
        blocks: queue.Queue[tuple[np.ndarray, float]] = queue.Queue()

        def callback(indata, _frames, _time, status) -> None:
            if status.input_overflow:
                self.overflows += 1
            blocks.put((indata[:, 0].copy(), self._clock()))

        b, a = np.array([1.0, -1.0]), np.array([1.0, -DC_POLE])
        zi = np.zeros(1)
        resampler = soxr.ResampleStream(CAPTURE_RATE, RATE, 1, dtype="float32", quality="VHQ")
        pending = np.zeros(0, dtype=np.float32)

        # The stream's callback thread inherits the opening thread's CPU mask, so a caller that
        # pinned itself to the front core (StreamLoop.run does) keeps capture there too.
        with sd.InputStream(device=index, samplerate=CAPTURE_RATE, channels=1, dtype="float32",
                            blocksize=BLOCK, callback=callback):
            while not self._stop.is_set():
                try:
                    block, t_block = blocks.get(timeout=0.5)
                except queue.Empty:
                    continue
                centred, zi = lfilter(b, a, block.astype(np.float64), zi=zi)
                out = resampler.resample_chunk((centred * self._gain).astype(np.float32))
                pending = np.concatenate([pending, out])
                while pending.size >= FRAME:
                    frame, pending = pending[:FRAME], pending[FRAME:]
                    yield np.clip(np.round(frame * 32767.0), -32768, 32767).astype(np.int16), t_block
