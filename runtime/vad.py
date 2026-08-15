"""Branch B endpointing: Silero VAD over a live stream (Table 4's `runtime/vad.py`).

Branch B's entry point used to be an already-segmented WAV. On a live microphone
nothing segments the audio, so this module does: it takes the 16 kHz stream in
any chunk size, finds where an utterance starts and ends, and emits the segment
together with **T0**, which prd.md Sec. 4.7 defines as the timestamp of the last
PCM sample in the buffer at the moment end-of-speech is declared. T0 is the
anchor for every Branch B latency in Exp-2, so it is computed here, where the
decision is made, and not reconstructed later.

**The model runs on onnxruntime directly, not through the silero-vad package.**
That package's wrapper imports torch, which is kept off this stack (prd.md SS0.5)
and would cost the Pi hundreds of MB for a 2 MB model. `SileroVAD` reproduces its
`OnnxWrapper` exactly: 512-sample windows at 16 kHz, the previous 64 samples
prepended as context, a (2, 1, 128) recurrent state carried across calls.
`Endpointer` reproduces `VADIterator`'s rule: speech starts at the first window
at or above `threshold`, and ends once probability has stayed below
`threshold - 0.15` for `min_silence_ms`. The 0.15 hysteresis is Silero's own.

**min_silence_ms is the budget line, not a tuning knob.** Table 6 gives VAD
endpointing 500 ms p95 -- the wall-clock wait to be sure speech has ended. The
wait is min_silence_ms plus up to one 32 ms window, so the default is the
largest round value that fits: 450 ms, worst case 482 ms. It was derived from
the budget, NOT tuned on audio: the golden set is Exp-2's test set.

What the budget costs was measured once, as a diagnostic (Wed 23 Sep): with 1.5 s
of silence either side, the fraction of the 200 golden utterances that endpoint
into more than one segment is 17.5% at 400 ms, 10.5% at 500, 2.5% at 700 and 0
at 1,000. The golden set is disfluent by design ("okay so, abort... abort now"),
and each extra segment reaches the parser as a separate, partial command. The
500 ms line in Table 6 is therefore a latency/segmentation trade, and it is
reported as one rather than resolved here.

**Segments are padded by `speech_pad_ms` on both sides.** Silero's 30 ms default
clips plosive onsets that whisper then mis-hears; 200 ms is taken from the
buffer, so it costs no latency. It must not exceed min_silence_ms, or the tail
pad would reach past audio the stream has delivered.
"""

from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

__all__ = ["SileroVAD", "Utterance", "Endpointer", "default_model_path"]

RATE = 16_000
WINDOW = 512       # samples per Silero call at 16 kHz (32 ms)
CONTEXT = 64       # samples of the previous window prepended to each call


def default_model_path() -> Path:
    """The ONNX file shipped inside the silero-vad wheel (pinned in requirements.txt)."""
    import importlib.util

    spec = importlib.util.find_spec("silero_vad")
    if spec is None or spec.origin is None:
        raise FileNotFoundError("silero-vad is not installed; it ships the ONNX model this module runs")
    return Path(spec.origin).parent / "data" / "silero_vad.onnx"


class SileroVAD:
    """Speech probability per 512-sample window. Stateful: feed windows in order."""

    def __init__(self, model_path: Path | None = None) -> None:
        import onnxruntime as ort

        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1  # prd.md Sec. 4.5: this runs on core 0 beside Branch A
        self._session = ort.InferenceSession(
            str(model_path or default_model_path()), sess_options=opts, providers=["CPUExecutionProvider"]
        )
        self.reset()

    def reset(self) -> None:
        self._state = np.zeros((2, 1, 128), dtype=np.float32)
        self._context = np.zeros((1, CONTEXT), dtype=np.float32)

    def __call__(self, window: np.ndarray) -> float:
        if window.shape != (WINDOW,):
            raise ValueError(f"expected {WINDOW} samples, got {window.shape}")
        x = np.concatenate([self._context, window.astype(np.float32)[None, :]], axis=1)
        prob, self._state = self._session.run(
            None, {"input": x, "state": self._state, "sr": np.array(RATE, dtype=np.int64)}
        )
        self._context = x[:, -CONTEXT:]
        return float(prob[0, 0])


@dataclass(frozen=True)
class Utterance:
    """One endpointed segment. All times are seconds from the start of the stream."""

    audio: np.ndarray   # int16, padded segment
    start_s: float      # segment start (speech onset minus pad)
    end_s: float        # segment end (end of speech plus pad)
    t0_s: float         # prd.md Sec. 4.7: last sample in the buffer when end was declared
    forced: bool = False  # cut by max_utterance_s rather than by silence

    def to_wav(self, path: Path) -> Path:
        """16 kHz mono S16_LE -- the format runtime/stt.py hands to whisper.cpp."""
        with wave.open(str(path), "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(RATE)
            f.writeframes(np.ascontiguousarray(self.audio, dtype="<i2").tobytes())
        return path


class Endpointer:
    """Stream in, utterances out. `feed()` takes int16 chunks of any length."""

    def __init__(
        self,
        vad: SileroVAD | None = None,
        *,
        threshold: float = 0.5,
        min_silence_ms: int = 450,
        speech_pad_ms: int = 200,
        max_utterance_s: float = 15.0,
    ) -> None:
        if speech_pad_ms > min_silence_ms:
            raise ValueError("speech_pad_ms may not exceed min_silence_ms: the tail pad would outrun the stream")
        self._vad = vad or SileroVAD()
        self._threshold = threshold
        self._min_silence = int(RATE * min_silence_ms / 1000)
        self._pad = int(RATE * speech_pad_ms / 1000)
        self._max = int(RATE * max_utterance_s)
        self.reset()

    def reset(self) -> None:
        self._vad.reset()
        self._pending = np.zeros(0, dtype=np.int16)  # samples not yet a full window
        self._buf = np.zeros(0, dtype=np.int16)      # audio kept for the current/next segment
        self._buf_start = 0                           # absolute index of _buf[0]
        self._consumed = 0                            # absolute samples run through the VAD
        self._triggered = False
        self._speech_start = 0
        self._temp_end = 0

    def feed(self, chunk: np.ndarray) -> list[Utterance]:
        chunk = np.asarray(chunk, dtype=np.int16)
        self._pending = np.concatenate([self._pending, chunk])
        out: list[Utterance] = []
        while self._pending.size >= WINDOW:
            window, self._pending = self._pending[:WINDOW], self._pending[WINDOW:]
            utterance = self._step(window)
            if utterance is not None:
                out.append(utterance)
        return out

    def _step(self, window: np.ndarray) -> Utterance | None:
        self._buf = np.concatenate([self._buf, window])
        self._consumed += WINDOW
        prob = self._vad(window.astype(np.float32) / 32768.0)
        window_start = self._consumed - WINDOW

        if prob >= self._threshold:
            self._temp_end = 0
            if not self._triggered:
                self._triggered = True
                # Clamped to the buffer: right after an emit, the onset pad cannot
                # reach back into audio that already belongs to the previous segment.
                self._speech_start = max(self._buf_start, window_start - self._pad)
        elif self._triggered and prob < self._threshold - 0.15:
            if not self._temp_end:
                self._temp_end = window_start  # silence began at this window
            if self._consumed - self._temp_end >= self._min_silence:
                return self._emit(self._temp_end + self._pad, forced=False)

        if self._triggered and self._consumed - self._speech_start >= self._max:
            return self._emit(self._consumed, forced=True)

        if not self._triggered:  # idle: keep only what a future onset pad can reach back to
            keep = self._pad + WINDOW
            if self._buf.size > keep:
                self._buf_start += self._buf.size - keep
                self._buf = self._buf[-keep:]
        return None

    def _emit(self, end: int, *, forced: bool) -> Utterance:
        lo = self._speech_start - self._buf_start
        hi = min(end, self._consumed) - self._buf_start
        utterance = Utterance(
            audio=self._buf[lo:hi].copy(),
            start_s=self._speech_start / RATE,
            end_s=min(end, self._consumed) / RATE,
            t0_s=self._consumed / RATE,
            forced=forced,
        )
        self._triggered = False
        self._temp_end = 0
        self._buf_start = self._consumed
        self._buf = np.zeros(0, dtype=np.int16)
        return utterance
