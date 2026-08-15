"""runtime/vad.py -- endpointing on the real Silero ONNX model and real golden audio.

These run the shipped model, not a fake: the endpointing rule is simple, and what
can actually go wrong is the model interface (context, state, dtype) or the
buffer arithmetic that produces T0 -- both invisible to a fake.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

pytest.importorskip("onnxruntime")

from runtime.vad import RATE, Endpointer, SileroVAD, default_model_path

REPO = Path(__file__).resolve().parent.parent
GOLDEN = REPO / "data" / "audio" / "s1_16k"

pytestmark = pytest.mark.skipif(
    not GOLDEN.exists() or not default_model_path().exists(), reason="golden audio or Silero model absent"
)


def _golden(item: str) -> np.ndarray:
    audio, rate = sf.read(str(GOLDEN / f"{item}.wav"), dtype="int16")
    assert rate == RATE
    return audio


def _silence(seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * RATE), dtype=np.int16)


def _run(stream: np.ndarray, chunk: int = 1280, **kwargs) -> list:
    endpointer = Endpointer(**kwargs)
    out = []
    for i in range(0, stream.size, chunk):
        out += endpointer.feed(stream[i : i + chunk])
    return out


def test_one_utterance_between_silences_is_one_segment() -> None:
    speech = _golden("0001")
    stream = np.concatenate([_silence(1.0), speech, _silence(1.5)])
    (utt,) = _run(stream)
    assert not utt.forced
    # Inside the inserted file (which carries its own ~0.6 s lead-in), give or take the pad.
    assert 1.0 - 0.2 <= utt.start_s < utt.end_s <= 1.0 + speech.size / RATE + 0.25
    assert utt.end_s - utt.start_s > 1.0
    assert utt.audio.size == round((utt.end_s - utt.start_s) * RATE)


def test_t0_trails_end_of_speech_by_the_silence_window() -> None:
    """T0 minus the first silent window is min_silence plus < one window, so the
    default's worst-case wait stays inside Table 6's 500 ms."""
    stream = np.concatenate([_silence(1.0), _golden("0001"), _silence(1.5)])
    (utt,) = _run(stream)
    wait = utt.t0_s - (utt.end_s - 0.200)
    assert 0.450 <= wait < 0.450 + 512 / RATE + 1e-9 <= 0.500


def test_silence_alone_produces_nothing() -> None:
    assert _run(_silence(5.0)) == []


def test_two_utterances_are_two_segments() -> None:
    stream = np.concatenate([_silence(0.8), _golden("0001"), _silence(1.5), _golden("0002"), _silence(1.5)])
    utts = _run(stream)
    assert len(utts) == 2
    assert utts[0].end_s <= utts[1].start_s


def test_chunk_size_does_not_change_the_segments() -> None:
    """The microphone delivers whatever block size ALSA gives; the result must not depend on it."""
    stream = np.concatenate([_silence(0.8), _golden("0003"), _silence(1.5)])
    a = [(u.start_s, u.end_s, u.t0_s) for u in _run(stream, chunk=1280)]
    b = [(u.start_s, u.end_s, u.t0_s) for u in _run(stream, chunk=333)]
    assert a == b and a


def test_an_endless_utterance_is_cut_at_the_cap() -> None:
    # 0001 is ~3 s of unbroken speech; a 2 s cap must cut it.
    utts = _run(np.concatenate([_silence(1.0), _golden("0001"), _silence(1.5)]), max_utterance_s=2.0)
    assert utts[0].forced
    assert utts[0].end_s - utts[0].start_s == pytest.approx(2.0, abs=512 / RATE)


def test_segment_round_trips_through_wav(tmp_path: Path) -> None:
    stream = np.concatenate([_silence(1.0), _golden("0001"), _silence(1.5)])
    (utt,) = _run(stream)
    back, rate = sf.read(str(utt.to_wav(tmp_path / "u.wav")), dtype="int16")
    assert rate == RATE and np.array_equal(back, utt.audio)


def test_pad_longer_than_the_silence_window_is_refused() -> None:
    with pytest.raises(ValueError, match="speech_pad_ms"):
        Endpointer(SileroVAD(), min_silence_ms=100, speech_pad_ms=200)


def test_the_model_separates_speech_from_silence() -> None:
    vad = SileroVAD()
    speech = _golden("0001").astype(np.float32) / 32768.0
    probs = [vad(speech[i : i + 512]) for i in range(0, speech.size - 512, 512)]
    vad.reset()
    quiet = [vad(np.zeros(512, dtype=np.float32)) for _ in range(20)]
    assert max(probs) > 0.9 and max(quiet) < 0.1
