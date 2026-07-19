#!/usr/bin/env python3
"""Digital SNR mixing --- the only path by which noisy audio is produced.

`prd.md` §9.3: "SNR levels for Exp-3 are mixed *digitally* from session 1's clean
audio, so no level requires re-recording." Recording a second acoustic condition
instead would destroy Exp-3's internal validity: with a re-recorded noisy take,
room, distance, mic placement and voice all move together with the noise, and the
causal statement about SNR is gone. Mixing digitally holds every one of them fixed
so **noise is the only varying factor** (`IMPLEMENTATION_ROADMAP.md` §0.2, conflict 4).

Two design decisions follow from that, and both are load-bearing:

**SNR is defined on the active-speech level, not full-file RMS** (`prd.md` §9.3).
Full-file RMS would let leading silence set the level, which makes nominal SNR
depend on how promptly the speaker started --- a 4 s file with 2 s of run-in
measures ~3 dB quieter than the same utterance trimmed, so "10 dB" would mean
different things across the corpus. The active level here is the RMS over frames
within `ACTIVE_DYNAMIC_RANGE_DB` of the loudest frame; see `active_speech_rms`.

**The noise segment is chosen per item, not per (item, SNR).** Every SNR level for
one utterance is mixed from the *same* noise excerpt at a different gain. Drawing a
fresh excerpt per level would confound level with excerpt, and the ANOVA across SNR
in Exp-3 would be measuring both.

The speech is never touched: only the noise is scaled. If the sum clips, the whole
mixture is attenuated by a single factor, which leaves the ratio exact.

Usage:
    # Exp-3 sweep over the golden set, rotor noise, evaluation partition
    python data/mix_noise.py --input data/audio/s1 --output data/audio/mixed \\
        --sources dregon --partition eval

    # one file, one level, to stdout-ish
    python data/mix_noise.py --input clean.wav --output out/ --snr 10

Seeded throughout: `--seed` (default 42, `prd.md` Table 14) plus the item's stem
determine the excerpt, so a re-run reproduces the corpus byte-for-byte.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import soundfile as sf
import soxr

DATA_DIR = Path(__file__).resolve().parent
NOISE_DIR = DATA_DIR / "noise"
MANIFEST_PATH = DATA_DIR / "asset_manifest.json"

#: The four levels `prd.md` D3 specifies for round-trip augmentation. Exp-3 adds
#: `clean` as a fifth condition, which is the unmixed file and needs no mixing.
SNR_LEVELS: tuple[int, ...] = (20, 15, 10, 5)

DEFAULT_SEED = 42
TARGET_RATE = 16_000  # whisper.cpp's input rate; the corpus resamples to it offline

#: Frames quieter than this many dB below the loudest frame are treated as silence
#: or room tone and excluded from the speech level. 30 dB is the conventional
#: dynamic range for speech-activity gating and comfortably spans the level
#: difference between a stressed vowel and an unvoiced fricative.
ACTIVE_DYNAMIC_RANGE_DB = 30.0
ACTIVE_FRAME_MS = 20.0

#: Headroom left below full scale after mixing. Clipping would inject broadband
#: distortion that is not the noise under study, so the mixture is attenuated
#: instead and the attenuation is reported.
PEAK_CEILING = 0.99

EPS = 1e-12

#: An excerpt quieter than this (about -80 dBFS) is treated as silence rather than
#: as very quiet noise. Some ESC-50 clips are an event inside five seconds of room
#: tone, so a random window can land on a passage with nothing in it; scaling that
#: to hit a nominal SNR would need enormous gain and the file would not be at the
#: SNR its name claims.
NOISE_SILENCE_FLOOR = 1e-4

#: How many windows to try before giving up on a draw.
MAX_DRAW_ATTEMPTS = 24


class NoiseBankError(RuntimeError):
    """Raised when the noise corpus is absent or unusable."""


# --- levels ----------------------------------------------------------------


def rms(x: np.ndarray) -> float:
    """Root-mean-square of a float signal."""
    if x.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(x, dtype=np.float64))))


def active_speech_rms(
    x: np.ndarray,
    sample_rate: int,
    *,
    frame_ms: float = ACTIVE_FRAME_MS,
    dynamic_range_db: float = ACTIVE_DYNAMIC_RANGE_DB,
) -> float:
    """RMS over the speech-active region only.

    The signal is cut into `frame_ms` frames; frames whose RMS is more than
    `dynamic_range_db` below the loudest frame are dropped, and the level is the
    RMS over what remains. On a signal with no frame above the floor --- digital
    silence --- this falls back to the full-file RMS, which is 0, and the caller
    is expected to reject the file rather than divide by it.
    """
    frame = max(1, int(round(sample_rate * frame_ms / 1000.0)))
    if x.size < frame:
        return rms(x)

    usable = (x.size // frame) * frame
    frames = x[:usable].reshape(-1, frame)
    frame_rms = np.sqrt(np.mean(np.square(frames, dtype=np.float64), axis=1))

    peak = float(frame_rms.max())
    if peak <= EPS:
        return 0.0

    floor = peak * (10.0 ** (-dynamic_range_db / 20.0))
    active = frames[frame_rms >= floor]
    if active.size == 0:
        return rms(x)
    return rms(active.reshape(-1))


def load_mono(path: Path, target_rate: int = TARGET_RATE, channel: int = 0) -> np.ndarray:
    """Read `path` as float32 mono at `target_rate`, resampling with soxr VHQ."""
    audio, rate = sf.read(str(path), dtype="float32", always_2d=True)
    mono = audio[:, min(channel, audio.shape[1] - 1)]
    if rate != target_rate:
        mono = soxr.resample(mono, rate, target_rate, quality="VHQ")
    return np.ascontiguousarray(mono, dtype=np.float32)


# --- noise bank ------------------------------------------------------------


@dataclass(frozen=True)
class NoiseSource:
    """One noise recording, already at the target rate, with its provenance."""

    key: str
    corpus: str
    samples: np.ndarray


def _stable_seed(*parts: object) -> int:
    """A seed that survives interpreter restarts --- `hash()` does not."""
    blob = "\x1f".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(blob).digest()[:8], "big")


class NoiseBank:
    """The noise corpus, partitioned so augmentation and evaluation never share bytes.

    Training-time round-trip augmentation and the Exp-3 sweep both draw noise from
    here. They must not draw the *same* noise: a model tuned on transcripts whose
    errors were produced by excerpt *k* and then evaluated against excerpt *k* would
    report a robustness that does not generalise past those few seconds of audio.
    The split is by ESC-50 fold (1--4 augment, 5 evaluates --- ESC-50's folds keep
    clips from one source recording together, which is exactly the property needed)
    and by position within the DREGON flight (first 70% augments, last 30% evaluates).
    """

    AUG_FOLDS = (1, 2, 3, 4)
    EVAL_FOLDS = (5,)
    DREGON_AUG_FRACTION = 0.70

    def __init__(
        self,
        sources: Sequence[str] = ("dregon", "esc50"),
        partition: str = "aug",
        target_rate: int = TARGET_RATE,
        manifest_path: Path = MANIFEST_PATH,
    ) -> None:
        if partition not in {"aug", "eval", "all"}:
            raise ValueError(f"partition must be aug, eval or all; got {partition!r}")
        self.partition = partition
        self.target_rate = target_rate
        self.sources = tuple(sources)
        self._manifest = self._load_manifest(manifest_path)
        self._entries = self._select()
        self._cache: dict[str, NoiseSource] = {}
        if not self._entries:
            raise NoiseBankError(
                f"no noise available for sources={self.sources} partition={partition!r}. "
                f"Run `python data/fetch_assets.py --noise` first."
            )

    @staticmethod
    def _load_manifest(path: Path) -> dict[str, dict]:
        if not path.is_file():
            raise NoiseBankError(
                f"{path} not found. Run `python data/fetch_assets.py --noise` first."
            )
        return json.loads(path.read_text(encoding="utf-8")).get("assets", {})

    def _select(self) -> list[tuple[str, dict]]:
        chosen: list[tuple[str, dict]] = []
        for key, entry in sorted(self._manifest.items()):
            corpus = entry.get("corpus", "")
            if corpus == "DREGON" and "dregon" in self.sources:
                chosen.append((key, entry))
            elif corpus == "ESC-50" and "esc50" in self.sources and key.endswith(".wav"):
                fold = entry.get("esc50_fold")
                if self.partition == "all" or fold in (
                    self.AUG_FOLDS if self.partition == "aug" else self.EVAL_FOLDS
                ):
                    chosen.append((key, entry))
        return chosen

    def _load(self, key: str, entry: dict) -> NoiseSource:
        if key in self._cache:
            return self._cache[key]
        path = DATA_DIR.parent / entry["path"]
        if not path.is_file():
            raise NoiseBankError(f"{path} listed in the manifest but missing on disk")
        samples = load_mono(path, self.target_rate)
        if entry.get("corpus") == "DREGON" and self.partition != "all":
            cut = int(len(samples) * self.DREGON_AUG_FRACTION)
            samples = samples[:cut] if self.partition == "aug" else samples[cut:]
        source = NoiseSource(key=key, corpus=entry.get("corpus", "?"), samples=samples)
        self._cache[key] = source
        return source

    @property
    def keys(self) -> list[str]:
        return [key for key, _ in self._entries]

    @property
    def corpora(self) -> list[str]:
        return sorted({entry.get("corpus", "?") for _, entry in self._entries})

    def draw(self, n_samples: int, rng: np.random.Generator) -> tuple[np.ndarray, str]:
        """Return `n_samples` of noise and the key of the recording it came from.

        The corpus is drawn first and the recording second, so the two corpora are
        equally represented. Drawing uniformly over recordings would not do that:
        DREGON is a single long flight and ESC-50 is dozens of short clips, so
        rotor noise --- the condition RQ3 is actually about --- would appear in
        about one mixture in sixty-five.

        Short recordings are tiled rather than zero-padded: padding would hand the
        mixer a silent tail whose nominal SNR is infinite. A window that lands on a
        silent passage --- several ESC-50 clips are one event inside five seconds of
        room tone --- is redrawn rather than used, for the same reason.
        """
        for _ in range(MAX_DRAW_ATTEMPTS):
            corpus = self.corpora[int(rng.integers(len(self.corpora)))]
            candidates = [e for e in self._entries if e[1].get("corpus", "?") == corpus]
            key, entry = candidates[int(rng.integers(len(candidates)))]
            source = self._load(key, entry)
            samples = source.samples
            if samples.size == 0:
                raise NoiseBankError(f"{key} decoded to zero samples")
            if samples.size < n_samples:
                reps = int(np.ceil(n_samples / samples.size))
                samples = np.tile(samples, reps)
            offset = int(rng.integers(samples.size - n_samples + 1))
            excerpt = samples[offset : offset + n_samples].copy()
            if rms(excerpt) >= NOISE_SILENCE_FLOOR:
                return excerpt, key
        raise NoiseBankError(
            f"no non-silent excerpt of {n_samples} samples found in "
            f"{MAX_DRAW_ATTEMPTS} attempts over {len(self._entries)} recording(s)"
        )


# --- mixing ----------------------------------------------------------------


@dataclass(frozen=True)
class MixResult:
    """One mixed signal and the numbers that justify calling it `snr_db`."""

    audio: np.ndarray
    snr_db: float
    speech_active_rms: float
    noise_rms: float
    noise_gain: float
    peak_attenuation: float
    noise_key: str


def mix_at_snr(
    speech: np.ndarray,
    noise: np.ndarray,
    snr_db: float,
    sample_rate: int = TARGET_RATE,
    *,
    noise_key: str = "",
) -> MixResult:
    """Add `noise` to `speech` at `snr_db`, measured on the active-speech level.

    The speech is passed through unscaled so that its level is identical at every
    SNR --- in Exp-3 the speech must be the constant and the noise the variable.
    """
    if speech.shape != noise.shape:
        raise ValueError(f"length mismatch: speech {speech.shape} vs noise {noise.shape}")

    speech_level = active_speech_rms(speech, sample_rate)
    noise_level = rms(noise)
    if speech_level <= EPS:
        raise ValueError("speech has no active region; refusing to mix against silence")
    if noise_level <= EPS:
        raise ValueError(f"noise excerpt {noise_key!r} is silent; refusing to mix")

    gain = speech_level / (noise_level * (10.0 ** (snr_db / 20.0)))
    mixed = speech + gain * noise

    peak = float(np.max(np.abs(mixed))) if mixed.size else 0.0
    attenuation = 1.0
    if peak > PEAK_CEILING:
        attenuation = PEAK_CEILING / peak
        mixed = mixed * attenuation

    return MixResult(
        audio=mixed.astype(np.float32),
        snr_db=float(snr_db),
        speech_active_rms=speech_level,
        noise_rms=noise_level,
        noise_gain=gain,
        peak_attenuation=attenuation,
        noise_key=noise_key,
    )


def measure_snr(mixed: np.ndarray, noise_component: np.ndarray, sample_rate: int) -> float:
    """Recover the realised SNR of a mixture whose noise component is known.

    Used by the tests, and by `--self-check`, to confirm that what was asked for is
    what came out. Attenuation applied to the whole mixture cancels in the ratio.
    """
    speech = mixed - noise_component
    return 20.0 * np.log10((active_speech_rms(speech, sample_rate) + EPS) / (rms(noise_component) + EPS))


def rng_for_item(item_key: str, seed: int = DEFAULT_SEED) -> np.random.Generator:
    """The generator that picks an item's noise excerpt.

    Seeded from `(seed, item_key)` and deliberately **not** from the SNR, so every
    level of one utterance is mixed from the same excerpt. Exposed because callers
    that skip re-mixing a cached file still need to know which excerpt was used.
    """
    return np.random.default_rng(_stable_seed(seed, item_key))


def mix_one(
    speech: np.ndarray,
    snr_db: float,
    bank: NoiseBank,
    item_key: str,
    *,
    seed: int = DEFAULT_SEED,
    sample_rate: int = TARGET_RATE,
) -> MixResult:
    """Mix one utterance at one level, drawing the excerpt deterministically."""
    noise, key = bank.draw(speech.size, rng_for_item(item_key, seed))
    return mix_at_snr(speech, noise, snr_db, sample_rate, noise_key=key)


# --- CLI -------------------------------------------------------------------


def _wav_inputs(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(target.glob("*.wav"))


def run(
    input_path: Path,
    output_root: Path,
    *,
    levels: Iterable[int] = SNR_LEVELS,
    sources: Sequence[str] = ("dregon", "esc50"),
    partition: str = "eval",
    seed: int = DEFAULT_SEED,
    sample_rate: int = TARGET_RATE,
) -> int:
    inputs = _wav_inputs(input_path)
    if not inputs:
        print(f"[-] no .wav files under {input_path}")
        return 1

    bank = NoiseBank(sources=sources, partition=partition, target_rate=sample_rate)
    print(
        f"[*] {len(inputs)} file(s), levels {list(levels)} dB, "
        f"noise: {len(bank.keys)} recording(s) from {list(sources)} [{partition}]"
    )

    written = 0
    attenuated = 0
    for snr in levels:
        out_dir = output_root / f"snr{snr:02d}"
        out_dir.mkdir(parents=True, exist_ok=True)
        for wav in inputs:
            speech = load_mono(wav, sample_rate)
            result = mix_one(speech, snr, bank, wav.stem, seed=seed, sample_rate=sample_rate)
            sf.write(str(out_dir / wav.name), result.audio, sample_rate, subtype="PCM_16")
            written += 1
            if result.peak_attenuation < 1.0:
                attenuated += 1

    print(f"[+] wrote {written} file(s) under {output_root}")
    if attenuated:
        print(f"[*] {attenuated} mixture(s) attenuated for headroom (SNR unchanged)")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", type=Path, required=True, help="a .wav file or a directory of them")
    parser.add_argument("--output", type=Path, required=True, help="root for snrNN/ subdirectories")
    parser.add_argument(
        "--snr",
        type=int,
        action="append",
        dest="levels",
        help=f"SNR level in dB, repeatable (default: {' '.join(map(str, SNR_LEVELS))})",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["dregon", "esc50"],
        choices=["dregon", "esc50"],
        help="noise corpora to draw from (default: both)",
    )
    parser.add_argument(
        "--partition",
        default="eval",
        choices=["aug", "eval", "all"],
        help="which half of the noise corpus (default: eval --- augmentation must use aug)",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--rate", type=int, default=TARGET_RATE)
    args = parser.parse_args(argv)

    try:
        return run(
            args.input,
            args.output,
            levels=args.levels or SNR_LEVELS,
            sources=args.sources,
            partition=args.partition,
            seed=args.seed,
            sample_rate=args.rate,
        )
    except (NoiseBankError, ValueError) as exc:
        print(f"[-] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
