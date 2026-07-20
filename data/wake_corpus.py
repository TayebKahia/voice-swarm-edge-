#!/usr/bin/env python3
"""Two-class wake-word corpus --- Branch A's training data.

`prd.md` FR-6 fixes the membership rule and it is contribution **C4**: Branch A
carries **exactly two phrases**, `swarm hold` and `swarm abort`, and **no movement
verb may ever be added**. Both qualifying intents make the swarm do *less*, so a
false accept is always fail-safe. That is a latency argument with a safety
consequence, not a preference, and it decides the shape of this corpus: two
positive classes, and everything else --- including the rest of the command
vocabulary --- is a negative.

`IMPLEMENTATION_ROADMAP.md` Session 03 task 3: **one word-list entry per class**,
shared augmentation, **>= 3 h of negatives** drawn from LibriSpeech, Common Voice
or Speech Commands v2, and MIT RIRs for the impulse responses. A keyword is a
fixed phrase, so the variation that matters is acoustic --- voice, prosody, room,
background, level, and where in the buffer the phrase falls --- not lexical.

Four decisions are load-bearing and are recorded in ADR-0005:

**The corpus is split, and the split is by base rendition, not by clip.** Exp-2
reports a per-class ROC with a declared operating point (NFR-15/16). Measured on
clips whose un-augmented parent was trained on, that ROC is a statement about
memorisation. Every augmented variant of one Piper rendition lands in one split,
exactly as `build_splits.py` keeps a template family together.

**Train and test draw different rooms and different noise.** RIRs split 70/30 by
index; background noise comes from the `aug` partition for train/val and the
`eval` partition for test, the same partition `mix_noise.py` already enforces and
`check_leakage.py` already gates. Sharing them would make the held-out split
measure a room the model had heard.

**The keyword is placed at a random offset, never centred.** A model trained on
centred keywords learns the centring. Deployment feeds it a sliding buffer where
the phrase lands anywhere, and the failure appears only in Exp-2.

**Negatives include authored near-misses.** LibriSpeech gives natural speech and
Speech Commands gives `stop`/`go`/`up`/`down`/`left`/`right`, but neither contains
"swarm" or a command that begins with "hold". Those are the confusions that
actually cost false accepts here, so they are synthesised deliberately.

Usage:
    python data/wake_corpus.py                  # build everything
    python data/wake_corpus.py --classes-only   # positives, skip the 3 h of negatives
    python data/wake_corpus.py --report         # count what is on disk, build nothing
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence

import numpy as np
import soundfile as sf
import soxr

if __package__ in (None, ""):  # `python data/wake_corpus.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.mix_noise import NoiseBank, mix_at_snr
from data.tts_synth import PiperBank

DATA_DIR = Path(__file__).resolve().parent
WAKE_DIR = DATA_DIR / "wake"
SOURCE_DIR = WAKE_DIR / "_src"
MANIFEST_PATH = WAKE_DIR / "wake_manifest.json"

TARGET_RATE = 16_000
SUBTYPE = "PCM_16"
DEFAULT_SEED = 42

#: FR-6. Two entries, one phrase each. Adding a third is a specification change,
#: not a tuning knob --- see the module docstring.
WAKE_CLASSES: dict[str, str] = {
    "pos_swarm_hold": "swarm hold",
    "pos_swarm_abort": "swarm abort",
}

#: Every clip is this long. A fixed window means the trainer needs no padding
#: logic and "3 hours of negatives" is a count rather than an integral.
CLIP_SECONDS = 2.5
CLIP_SAMPLES = int(CLIP_SECONDS * TARGET_RATE)

#: Per class: 3 voices x 20 prosody renditions = 60 bases, each augmented 25
#: times = 1,500 clips. The bases carry the split; the augmentations carry the
#: acoustic variation.
BASES_PER_VOICE = 20
AUGS_PER_BASE = 25

LENGTH_SCALE_RANGE = (0.80, 1.30)
NOISE_SCALE_RANGE = (0.50, 0.90)
NOISE_W_RANGE = (0.60, 1.00)

RIR_PROBABILITY = 0.65
NOISE_PROBABILITY = 0.80
AUG_SNR_RANGE = (3.0, 25.0)
GAIN_RANGE_DB = (-9.0, 0.0)

#: The floor is 3 h (roadmap). The target overshoots it so that dropping a
#: corrupt source file does not put the corpus under the requirement.
NEGATIVE_HOURS = 3.5

SPLIT_SHARES: dict[str, float] = {"train": 0.70, "val": 0.10, "test": 0.20}

#: Train/val hear the first 70% of the MIT survey; the held-out split hears rooms
#: the model never trained in.
RIR_TRAIN_FRACTION = 0.70

#: Neither LibriSpeech nor Speech Commands contains "swarm", and nothing in either
#: begins a phrase with "hold". These are the near-misses that actually produce
#: false accepts on this keyword pair: the wake words' own constituent words in
#: isolation, the wake words inside longer phrases, and the Branch B command
#: vocabulary that a user will speak in the same session.
ADVERSARIAL_PHRASES: tuple[str, ...] = (
    "swarm",
    "hold",
    "abort",
    "swarm hover",
    "swarm move north",
    "swarm take off",
    "swarm land",
    "swarm form a circle",
    "swarm climb to four metres",
    "swarm set the speed to one point five",
    "hold on",
    "hold on a second",
    "hold your position",
    "hold that thought",
    "holding altitude",
    "abort the mission",
    "aborted",
    "we should abort",
    "warm",
    "swarm of bees",
    "the swarm is holding",
    "all units hold formation",
    "storm",
    "swab",
    "sworn",
    "old",
    "bold",
    "a board",
    "a boat",
    "take off and hold",
    "land and abort",
    "drone two hold",
    "hold at two metres",
    "abort at once",
    "swarm, what is your altitude",
    "is the swarm holding",
    "please hold",
    "put it on hold",
    "mission abort procedure",
    "swarm hold the line for me",
)
ADVERSARIAL_RENDITIONS = 6  # per phrase per voice


def _stable_seed(*parts: object) -> int:
    blob = "\x1f".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(blob).digest()[:8], "big")


def _rng(*parts: object) -> np.random.Generator:
    return np.random.default_rng(_stable_seed(*parts))


# --- source archives -------------------------------------------------------


@dataclass(frozen=True)
class Archive:
    key: str
    filename: str
    corpus: str
    licence: str
    homepage: str


ARCHIVES: tuple[Archive, ...] = (
    Archive(
        key="librispeech_dev_clean",
        filename="dev-clean.tar.gz",
        corpus="LibriSpeech dev-clean",
        licence="CC BY 4.0",
        homepage="https://www.openslr.org/12",
    ),
    Archive(
        key="speech_commands_v2_test",
        filename="speech_commands_test_set_v0.02.tar.gz",
        corpus="Speech Commands v0.02 (test set)",
        licence="CC BY 4.0",
        homepage="https://arxiv.org/abs/1804.03209",
    ),
    Archive(
        key="mit_ir_survey",
        filename="mit_ir_survey.zip",
        corpus="MIT Acoustical Reverberation Scene Statistics Survey",
        licence="CC BY 4.0 (Traer & McDermott, PNAS 2016)",
        homepage="https://mcdermottlab.mit.edu/Reverb/IR_Survey.html",
    ),
)


def extract_sources() -> dict[str, Path]:
    """Unpack each archive once, next to itself. Returns the extracted roots."""
    roots: dict[str, Path] = {}
    for archive in ARCHIVES:
        source = SOURCE_DIR / archive.filename
        if not source.is_file():
            raise SystemExit(
                f"missing {source}. Run `python data/fetch_assets.py --wake` first."
            )
        root = SOURCE_DIR / archive.key
        if not root.is_dir():
            root.mkdir(parents=True)
            print(f"  extracting {archive.filename} ...")
            if archive.filename.endswith(".zip"):
                with zipfile.ZipFile(source) as zf:
                    zf.extractall(root)
            else:
                with tarfile.open(source) as tf:
                    tf.extractall(root)
        roots[archive.key] = root
    return roots


# --- impulse responses -----------------------------------------------------


class RIRBank:
    """MIT survey impulse responses, partitioned so held-out clips get new rooms."""

    def __init__(self, root: Path, partition: str) -> None:
        paths = sorted(p for p in root.rglob("*.wav"))
        if not paths:
            raise SystemExit(f"no impulse responses under {root}")
        cut = int(len(paths) * RIR_TRAIN_FRACTION)
        self.partition = partition
        self.paths = paths[:cut] if partition == "train" else paths[cut:]
        self._cache: dict[str, np.ndarray] = {}

    def draw(self, rng: np.random.Generator) -> tuple[str, np.ndarray]:
        path = self.paths[int(rng.integers(len(self.paths)))]
        key = path.name
        if key not in self._cache:
            audio, rate = sf.read(str(path), dtype="float32", always_2d=True)
            mono = audio[:, 0]
            if rate != TARGET_RATE:
                mono = soxr.resample(mono, rate, TARGET_RATE, quality="VHQ")
            peak = float(np.max(np.abs(mono))) or 1.0
            self._cache[key] = np.ascontiguousarray(mono / peak, dtype=np.float32)
        return key, self._cache[key]


# --- augmentation ----------------------------------------------------------


def place_in_window(audio: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, float]:
    """Drop `audio` at a random offset inside a CLIP_SECONDS window of silence.

    Returns the window and the offset in seconds. The offset is the point: a
    keyword that is always centred teaches the model where to look, and the
    streaming buffer at deployment offers no such guarantee.
    """
    window = np.zeros(CLIP_SAMPLES, dtype=np.float32)
    if audio.size >= CLIP_SAMPLES:
        start = int(rng.integers(0, audio.size - CLIP_SAMPLES + 1))
        window[:] = audio[start : start + CLIP_SAMPLES]
        return window, 0.0
    offset = int(rng.integers(0, CLIP_SAMPLES - audio.size + 1))
    window[offset : offset + audio.size] = audio
    return window, offset / TARGET_RATE


def augment(
    clip: np.ndarray,
    rng: np.random.Generator,
    rirs: RIRBank,
    noise: NoiseBank,
    item_key: str,
) -> tuple[np.ndarray, dict]:
    """Room, background, level --- the three things that vary at deployment."""
    record: dict = {"rir": None, "noise_key": None, "snr_db": None, "noise_partition": None}

    if rng.random() < RIR_PROBABILITY:
        name, impulse = rirs.draw(rng)
        wet = np.convolve(clip, impulse)[: clip.size]
        peak = float(np.max(np.abs(wet)))
        if peak > 0:  # convolution changes the level; the mix stage sets it again
            wet = wet * (float(np.max(np.abs(clip))) / peak)
        clip = wet.astype(np.float32)
        record["rir"] = name

    if rng.random() < NOISE_PROBABILITY:
        snr = float(rng.uniform(*AUG_SNR_RANGE))
        excerpt, noise_key = noise.draw(clip.size, rng)
        # The bank, not the split, is the source of this field: DREGON is one
        # continuous flight split by *position*, so both partitions return the
        # same filename and the key alone cannot show which bytes were used.
        record["noise_partition"] = noise.partition
        try:
            clip = mix_at_snr(clip, excerpt, snr, TARGET_RATE, noise_key=noise_key).audio
        except ValueError:
            # A negative window can land on a pause between sentences, which has
            # no active region to measure an SNR against. Leaving it dry is
            # correct: a silent buffer is a negative the spotter must also reject.
            pass
        else:
            record["noise_key"] = noise_key
            record["snr_db"] = round(snr, 2)

    gain = 10.0 ** (float(rng.uniform(*GAIN_RANGE_DB)) / 20.0)
    clip = np.clip(clip * gain, -0.999, 0.999).astype(np.float32)
    record["gain_db"] = round(20.0 * float(np.log10(gain)), 2)
    return clip, record


# --- split assignment ------------------------------------------------------


def assign_splits(keys: Sequence[str], seed: int, salt: str) -> dict[str, str]:
    """Largest-remainder shares over a stably-ordered key list.

    Ordering by a hash of the key rather than by position means adding a speaker
    or a phrase does not re-roll the assignment of everything already built.
    """
    ordered = sorted(keys, key=lambda k: _stable_seed(seed, salt, k))
    total = len(ordered)
    exact = {name: total * share for name, share in SPLIT_SHARES.items()}
    counts = {name: int(value) for name, value in exact.items()}
    remainder = total - sum(counts.values())
    for name, _ in sorted(exact.items(), key=lambda kv: kv[1] - int(kv[1]), reverse=True):
        if remainder <= 0:
            break
        counts[name] += 1
        remainder -= 1

    assignment: dict[str, str] = {}
    index = 0
    for name in ("train", "val", "test"):
        for key in ordered[index : index + counts[name]]:
            assignment[key] = name
        index += counts[name]
    return assignment


def _banks(seed: int) -> dict[str, tuple[RIRBank, NoiseBank]]:
    roots = extract_sources()
    rir_root = roots["mit_ir_survey"]
    return {
        "train": (RIRBank(rir_root, "train"), NoiseBank(partition="aug")),
        "val": (RIRBank(rir_root, "train"), NoiseBank(partition="aug")),
        "test": (RIRBank(rir_root, "test"), NoiseBank(partition="eval")),
    }


# --- positives -------------------------------------------------------------


def synthesize_bases(
    bank: PiperBank, phrase: str, label: str, seed: int
) -> list[tuple[str, np.ndarray, dict]]:
    """One rendition per (voice, index): the unit the split is assigned over."""
    from piper import SynthesisConfig

    bases: list[tuple[str, np.ndarray, dict]] = []
    for voice in bank.voice_names:
        for index in range(BASES_PER_VOICE):
            key = f"{label}/{voice}/{index:03d}"
            rng = _rng(seed, "wake-base", key)
            settings = {
                "length_scale": round(float(rng.uniform(*LENGTH_SCALE_RANGE)), 4),
                "noise_scale": round(float(rng.uniform(*NOISE_SCALE_RANGE)), 4),
                "noise_w_scale": round(float(rng.uniform(*NOISE_W_RANGE)), 4),
            }
            chunks = list(bank._voice(voice).synthesize(phrase, SynthesisConfig(**settings)))
            if not chunks:
                raise SystemExit(f"Piper produced no audio for {key!r}: {phrase!r}")
            audio = np.concatenate([c.audio_float_array for c in chunks]).astype(np.float32)
            if chunks[0].sample_rate != TARGET_RATE:
                audio = soxr.resample(audio, chunks[0].sample_rate, TARGET_RATE, quality="VHQ")
            bases.append((key, np.ascontiguousarray(audio, dtype=np.float32), {"voice": voice, **settings}))
    return bases


def build_positives(seed: int, banks: dict) -> list[dict]:
    bank = PiperBank()
    records: list[dict] = []

    for label, phrase in WAKE_CLASSES.items():
        print(f"\n{label}: synthesising {len(bank.voice_names) * BASES_PER_VOICE} renditions "
              f"of {phrase!r}")
        bases = synthesize_bases(bank, phrase, label, seed)
        splits = assign_splits([key for key, _, _ in bases], seed, f"wake-{label}")

        out_root = WAKE_DIR / label
        for split in SPLIT_SHARES:
            (out_root / split).mkdir(parents=True, exist_ok=True)
            for stale in (out_root / split).glob("*.wav"):
                stale.unlink()

        for key, audio, settings in bases:
            split = splits[key]
            rirs, noise = banks[split]
            for variant in range(AUGS_PER_BASE):
                item_key = f"{key}/{variant:02d}"
                rng = _rng(seed, "wake-aug", item_key)
                window, offset = place_in_window(audio, rng)
                clip, applied = augment(window, rng, rirs, noise, item_key)

                name = f"{key.replace('/', '_')}_{variant:02d}.wav"
                path = out_root / split / name
                sf.write(str(path), clip, TARGET_RATE, subtype=SUBTYPE)
                records.append(
                    {
                        "path": str(path.relative_to(DATA_DIR.parent)),
                        "label": label,
                        "phrase": phrase,
                        "base": key,
                        "split": split,
                        "seconds": CLIP_SECONDS,
                        "keyword_offset_s": round(offset, 3),
                        "source": "piper",
                        **settings,
                        **applied,
                    }
                )
        print(f"  {sum(1 for r in records if r['label'] == label)} clips")
    return records


# --- negatives -------------------------------------------------------------


def librispeech_clips(root: Path) -> Iterator[tuple[str, str, np.ndarray]]:
    """Whole-window chunks of read speech, tagged with the LibriSpeech speaker."""
    for path in sorted(root.rglob("*.flac")):
        speaker = path.parts[-3]
        audio, rate = sf.read(str(path), dtype="float32", always_2d=True)
        mono = audio[:, 0]
        if rate != TARGET_RATE:
            mono = soxr.resample(mono, rate, TARGET_RATE, quality="VHQ")
        for index in range(mono.size // CLIP_SAMPLES):
            chunk = mono[index * CLIP_SAMPLES : (index + 1) * CLIP_SAMPLES]
            yield f"librispeech/{speaker}", f"{path.stem}_{index:03d}", np.ascontiguousarray(chunk)


def speech_commands_clips(root: Path, seed: int) -> Iterator[tuple[str, str, np.ndarray]]:
    """Command words packed into the window, grouped by their own speaker hash.

    `stop`, `go`, `up`, `down`, `left` and `right` are the false-activation
    hardening the roadmap names: they are the words a user will say to *this*
    system, at Branch B, while Branch A is listening.
    """
    paths = sorted(p for p in root.rglob("*.wav") if p.parent.name != "_background_noise_")
    by_speaker: dict[str, list[Path]] = {}
    for path in paths:
        speaker = path.stem.split("_")[0]
        by_speaker.setdefault(speaker, []).append(path)

    for speaker, speaker_paths in by_speaker.items():
        rng = _rng(seed, "speech-commands", speaker)
        order = list(rng.permutation(len(speaker_paths)))
        index = 0
        clip_number = 0
        while index < len(order):
            window = np.zeros(CLIP_SAMPLES, dtype=np.float32)
            cursor = int(rng.integers(0, int(0.3 * TARGET_RATE)))
            used = 0
            while index < len(order) and cursor < CLIP_SAMPLES:
                audio, rate = sf.read(str(speaker_paths[order[index]]), dtype="float32", always_2d=True)
                mono = audio[:, 0]
                if rate != TARGET_RATE:
                    mono = soxr.resample(mono, rate, TARGET_RATE, quality="VHQ")
                room = min(mono.size, CLIP_SAMPLES - cursor)
                window[cursor : cursor + room] = mono[:room]
                cursor += room + int(rng.integers(int(0.05 * TARGET_RATE), int(0.35 * TARGET_RATE)))
                index += 1
                used += 1
            if used:
                yield f"speech_commands/{speaker}", f"{speaker}_{clip_number:03d}", window
                clip_number += 1


def adversarial_clips(seed: int) -> Iterator[tuple[str, str, np.ndarray]]:
    """Authored near-misses, synthesised. Grouped by phrase so a phrase cannot
    appear in two splits --- otherwise the held-out false-accept rate is measured
    on a phrase the model was trained to reject."""
    from piper import SynthesisConfig

    bank = PiperBank()
    for phrase_index, phrase in enumerate(ADVERSARIAL_PHRASES):
        group = f"adversarial/{phrase_index:03d}"
        for voice in bank.voice_names:
            for rendition in range(ADVERSARIAL_RENDITIONS):
                key = f"{group}/{voice}/{rendition}"
                rng = _rng(seed, "adversarial", key)
                chunks = list(
                    bank._voice(voice).synthesize(
                        phrase,
                        SynthesisConfig(
                            length_scale=float(rng.uniform(*LENGTH_SCALE_RANGE)),
                            noise_scale=float(rng.uniform(*NOISE_SCALE_RANGE)),
                            noise_w_scale=float(rng.uniform(*NOISE_W_RANGE)),
                        ),
                    )
                )
                if not chunks:
                    continue
                audio = np.concatenate([c.audio_float_array for c in chunks]).astype(np.float32)
                if chunks[0].sample_rate != TARGET_RATE:
                    audio = soxr.resample(audio, chunks[0].sample_rate, TARGET_RATE, quality="VHQ")
                window, _ = place_in_window(np.ascontiguousarray(audio), rng)
                yield group, f"{phrase_index:03d}_{voice}_{rendition}", window


def build_negatives(seed: int, banks: dict, roots: dict[str, Path]) -> list[dict]:
    target_clips = int(NEGATIVE_HOURS * 3600 / CLIP_SECONDS)
    print(f"\nnegatives: target {target_clips} clips = {NEGATIVE_HOURS:.1f} h")

    pool: list[tuple[str, str, str, np.ndarray]] = []  # (source, group, name, audio)
    for group, name, audio in adversarial_clips(seed):
        pool.append(("adversarial", group, name, audio))
    print(f"  adversarial: {len(pool)}")

    before = len(pool)
    for group, name, audio in speech_commands_clips(roots["speech_commands_v2_test"], seed):
        pool.append(("speech_commands", group, name, audio))
    print(f"  speech_commands: {len(pool) - before}")

    before = len(pool)
    for group, name, audio in librispeech_clips(roots["librispeech_dev_clean"]):
        pool.append(("librispeech", group, name, audio))
        if len(pool) >= target_clips:
            break
    print(f"  librispeech: {len(pool) - before}")

    if len(pool) * CLIP_SECONDS / 3600 < 3.0:
        raise SystemExit(
            f"only {len(pool) * CLIP_SECONDS / 3600:.2f} h of negatives; the roadmap "
            "requires at least 3 h. Check that every source archive extracted."
        )

    splits = assign_splits(sorted({group for _, group, _, _ in pool}), seed, "wake-neg")

    out_root = WAKE_DIR / "neg"
    for split in SPLIT_SHARES:
        (out_root / split).mkdir(parents=True, exist_ok=True)
        for stale in (out_root / split).glob("*.wav"):
            stale.unlink()

    records: list[dict] = []
    for source, group, name, audio in pool:
        split = splits[group]
        rirs, noise = banks[split]
        item_key = f"neg/{group}/{name}"
        rng = _rng(seed, "wake-neg-aug", item_key)
        clip, applied = augment(audio, rng, rirs, noise, item_key)
        path = out_root / split / f"{source}_{name}.wav"
        sf.write(str(path), clip, TARGET_RATE, subtype=SUBTYPE)
        records.append(
            {
                "path": str(path.relative_to(DATA_DIR.parent)),
                "label": "neg",
                "source": source,
                "base": group,
                "split": split,
                "seconds": CLIP_SECONDS,
                **applied,
            }
        )
    return records


# --- manifest and reporting ------------------------------------------------


def summarise(records: list[dict]) -> dict:
    by_label: dict[str, dict] = {}
    for record in records:
        entry = by_label.setdefault(
            record["label"], {"clips": 0, "hours": 0.0, "splits": {}, "sources": {}}
        )
        entry["clips"] += 1
        entry["hours"] += record["seconds"] / 3600
        entry["splits"][record["split"]] = entry["splits"].get(record["split"], 0) + 1
        entry["sources"][record["source"]] = entry["sources"].get(record["source"], 0) + 1
    for entry in by_label.values():
        entry["hours"] = round(entry["hours"], 3)
    return by_label


def write_manifest(records: list[dict], seed: int) -> dict:
    summary = summarise(records)
    manifest = {
        "seed": seed,
        "sample_rate": TARGET_RATE,
        "clip_seconds": CLIP_SECONDS,
        "classes": WAKE_CLASSES,
        "split_shares": SPLIT_SHARES,
        "rir_train_fraction": RIR_TRAIN_FRACTION,
        "noise_partition": {"train": "aug", "val": "aug", "test": "eval"},
        "summary": summary,
        "clips": records,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def print_summary(summary: dict) -> None:
    print()
    print(f"{'class':<18}{'clips':>8}{'hours':>8}   {'train/val/test':<20}")
    for label in list(WAKE_CLASSES) + ["neg"]:
        entry = summary.get(label)
        if not entry:
            continue
        splits = entry["splits"]
        breakdown = "/".join(str(splits.get(s, 0)) for s in ("train", "val", "test"))
        print(f"{label:<18}{entry['clips']:>8}{entry['hours']:>8.2f}   {breakdown:<20}")
    negatives = summary.get("neg", {}).get("hours", 0.0)
    verdict = "PASS" if negatives >= 3.0 else "FAIL"
    print(f"\nnegatives {negatives:.2f} h (>= 3 h required)  {verdict}")


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--classes-only", action="store_true", help="positives only")
    parser.add_argument("--report", action="store_true", help="read the manifest, build nothing")
    args = parser.parse_args(argv)

    if args.report:
        if not MANIFEST_PATH.is_file():
            raise SystemExit(f"{MANIFEST_PATH} does not exist -- build the corpus first")
        print_summary(json.loads(MANIFEST_PATH.read_text())["summary"])
        return 0

    roots = extract_sources()
    banks = _banks(args.seed)

    records = build_positives(args.seed, banks)
    if not args.classes_only:
        records += build_negatives(args.seed, banks, roots)

    manifest = write_manifest(records, args.seed)
    print_summary(manifest["summary"])
    print(f"\nmanifest: {MANIFEST_PATH}")
    return 0 if manifest["summary"].get("neg", {}).get("hours", 0.0) >= 3.0 or args.classes_only else 1


if __name__ == "__main__":
    raise SystemExit(run())
