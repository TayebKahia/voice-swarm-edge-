#!/usr/bin/env python3
"""Piper TTS for the bulk corpus --- the speech side of round-trip augmentation.

`prd.md` Limitations is explicit that "bulk audio is TTS, lacking the prosody,
breath, and channel variation of live speech", and that every *reported* CRR and
WER figure comes from the golden set instead. TTS audio exists here for one
purpose: to push each training transcript through the deployed ASR so the training
text carries that ASR's error distribution. It is never evaluated on.

Three voices, assigned deterministically per row. One voice would give
`whisper.cpp` a single narrow failure mode --- one speaking rate, one accent, one
set of confusable vowels --- and the fine-tuned model would learn to repair that
voice's errors rather than ASR error in general.

Speaking rate varies per row within a narrow band for the same reason, and every
clip is padded with leading and trailing silence: real capture has run-in, and it
is what makes `mix_noise.active_speech_rms` do work that a full-file RMS would not.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf
import soxr

if __package__ in (None, ""):  # `python data/tts_synth.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.mix_noise import TARGET_RATE

DATA_DIR = Path(__file__).resolve().parent
VOICES_DIR = DATA_DIR / "tts_voices"

VOICE_NAMES: tuple[str, ...] = (
    "en_US-lessac-medium",
    "en_US-ryan-medium",
    "en_GB-alba-medium",
)

#: Piper's `length_scale` is inverse speaking rate: 1.0 is the voice's nominal
#: pace, higher is slower. +-12% spans a natural range without the artefacts that
#: appear when a vocoder is pushed hard.
LENGTH_SCALE_RANGE = (0.88, 1.12)

#: Silence padded to each end, in seconds.
PAD_SECONDS = 0.25


class TTSUnavailable(RuntimeError):
    """Raised when the Piper voices have not been fetched."""


def _stable_seed(*parts: object) -> int:
    blob = "\x1f".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(blob).digest()[:8], "big")


@dataclass(frozen=True)
class Utterance:
    """One synthesised clip and the settings that produced it."""

    audio: np.ndarray
    sample_rate: int
    voice: str
    length_scale: float


class PiperBank:
    """The three voices, loaded lazily and held for the life of the run.

    Loading an ONNX voice costs far more than synthesising with it, so a corpus
    run must not reload per row.
    """

    def __init__(
        self,
        voices_dir: Path = VOICES_DIR,
        voice_names: tuple[str, ...] = VOICE_NAMES,
        target_rate: int = TARGET_RATE,
    ) -> None:
        self.voices_dir = voices_dir
        self.voice_names = tuple(voice_names)
        self.target_rate = target_rate
        self._loaded: dict[str, object] = {}

        missing = [n for n in self.voice_names if not (voices_dir / f"{n}.onnx").is_file()]
        if missing:
            raise TTSUnavailable(
                f"Piper voices missing: {', '.join(missing)}. "
                f"Run `python data/fetch_assets.py --voices` first."
            )

    def _voice(self, name: str):
        if name not in self._loaded:
            from piper import PiperVoice  # imported late: onnxruntime start-up is slow

            self._loaded[name] = PiperVoice.load(str(self.voices_dir / f"{name}.onnx"))
        return self._loaded[name]

    def settings_for(self, item_key: str, seed: int) -> tuple[str, float]:
        """Pick this row's voice and speaking rate, reproducibly across runs."""
        rng = np.random.default_rng(_stable_seed(seed, "tts", item_key))
        voice = self.voice_names[int(rng.integers(len(self.voice_names)))]
        length_scale = float(rng.uniform(*LENGTH_SCALE_RANGE))
        return voice, length_scale

    def synthesize(self, text: str, item_key: str, seed: int) -> Utterance:
        from piper import SynthesisConfig

        voice_name, length_scale = self.settings_for(item_key, seed)
        chunks = list(
            self._voice(voice_name).synthesize(
                text, SynthesisConfig(length_scale=length_scale)
            )
        )
        if not chunks:
            raise ValueError(f"Piper produced no audio for {item_key!r}: {text!r}")

        audio = np.concatenate([c.audio_float_array for c in chunks]).astype(np.float32)
        native_rate = chunks[0].sample_rate
        if native_rate != self.target_rate:
            audio = soxr.resample(audio, native_rate, self.target_rate, quality="VHQ")

        pad = np.zeros(int(self.target_rate * PAD_SECONDS), dtype=np.float32)
        audio = np.concatenate([pad, audio.astype(np.float32), pad])

        return Utterance(
            audio=audio,
            sample_rate=self.target_rate,
            voice=voice_name,
            length_scale=length_scale,
        )

    def synthesize_to(self, text: str, item_key: str, seed: int, path: Path) -> Utterance:
        """Synthesise and write a 16-bit PCM WAV, creating parent directories."""
        utterance = self.synthesize(text, item_key, seed)
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(path), utterance.audio, utterance.sample_rate, subtype="PCM_16")
        return utterance
