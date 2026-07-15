#!/usr/bin/env python3
"""Harvest real whisper.cpp output on silence and noise --- OOD source (c).

`02_dataset_plan.md` §3.4 asks for "actual Whisper output on noise/silence", not
an impression of it. Whisper does not return an empty string when nobody speaks:
it was trained on subtitle corpora, so on silence it reaches for the most common
thing subtitles say over silence --- "Thank you.", "Thanks for watching!", the
Amara.org credit line. Those exact strings arrive at the LLM's prompt in the
deployed pipeline, so they belong in `test_ood.jsonl` verbatim.

This script is the only part of dataset generation that needs a model on disk, so
it is deliberately *separate* from `data/generate.py` and its output is
committed. `run_all.sh` reproduces the corpus from `data/asr_garbage.json`
without whisper.cpp, without weights, and without a network.

    python data/harvest_asr_garbage.py                 # find whisper.cpp, harvest
    WHISPER_CPP_DIR=/opt/whisper.cpp python data/harvest_asr_garbage.py

Exits non-zero and changes nothing if whisper.cpp is not available. When that
happens `data/ood.py` falls back to its authored pool and every affected row is
stamped `authored_asr_garbage_pending_harvest`, so the shortfall is visible in
the artefact instead of being absorbed into it.

The stimuli are synthesised here rather than recorded, for the same
reproducibility reason: a fixed seed, the stdlib `wave` module, and no assets.
The set spans what a drone microphone hears between commands --- digital silence,
room tone, broadband rotor wash, low-frequency airframe rumble, and wind gusts.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import wave
from array import array
from pathlib import Path

SAMPLE_RATE = 16_000  # whisper.cpp requires 16 kHz mono
SEED = 42

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = Path(__file__).parent / "asr_garbage.json"

BINARY_NAMES = ("whisper-cli", "main")
BINARY_SUBDIRS = ("build/bin", "bin", ".")
MODEL_RELPATH = "models/ggml-tiny.en.bin"

CANDIDATE_DIRS = (
    Path.home() / "whisper.cpp",
    Path("/opt/whisper.cpp"),
    Path("/usr/local/share/whisper.cpp"),
    REPO_ROOT / "third_party" / "whisper.cpp",
)


# --- stimulus synthesis ----------------------------------------------------


def _write_wav(path: Path, samples: array) -> None:
    with wave.open(str(path), "wb") as fp:
        fp.setnchannels(1)
        fp.setsampwidth(2)
        fp.setframerate(SAMPLE_RATE)
        fp.writeframes(samples.tobytes())


def _clip(value: float) -> int:
    return max(-32768, min(32767, int(value)))


def _silence(seconds: float) -> array:
    return array("h", [0] * int(SAMPLE_RATE * seconds))


def _white(seconds: float, amplitude: int, rng: random.Random) -> array:
    n = int(SAMPLE_RATE * seconds)
    return array("h", [_clip(rng.gauss(0.0, amplitude)) for _ in range(n)])


def _lowpass(source: array, alpha: float) -> array:
    """One-pole IIR low-pass. Turns white noise into rumble and wind."""
    out = array("h", [0] * len(source))
    state = 0.0
    for i, sample in enumerate(source):
        state += alpha * (sample - state)
        out[i] = _clip(state)
    return out


def _tone(seconds: float, freq: float, amplitude: int) -> array:
    n = int(SAMPLE_RATE * seconds)
    step = 2.0 * math.pi * freq / SAMPLE_RATE
    return array("h", [_clip(amplitude * math.sin(step * i)) for i in range(n)])


def _mix(*parts: array) -> array:
    length = max(len(p) for p in parts)
    out = array("h", [0] * length)
    for i in range(length):
        out[i] = _clip(sum(p[i] for p in parts if i < len(p)))
    return out


def _gusts(seconds: float, rng: random.Random) -> array:
    """Low-passed noise with a slow amplitude envelope: wind across the mic."""
    base = _lowpass(_white(seconds, 6000, rng), 0.02)
    n = len(base)
    out = array("h", [0] * n)
    for i in range(n):
        env = 0.5 * (1.0 - math.cos(2.0 * math.pi * 0.4 * i / SAMPLE_RATE))
        out[i] = _clip(base[i] * env)
    return out


def _clicks(seconds: float, rng: random.Random) -> array:
    out = _silence(seconds)
    for _ in range(int(seconds * 6)):
        at = rng.randrange(0, max(1, len(out) - 200))
        for j in range(120):
            out[at + j] = _clip(9000 * math.exp(-j / 20.0) * (1 if j % 2 else -1))
    return out


def build_stimuli(directory: Path) -> list[tuple[str, str]]:
    """Write the stimulus set. Returns `(filename, description)` pairs."""
    rng = random.Random(SEED)
    stimuli: list[tuple[str, array, str]] = [
        ("silence_2s", _silence(2.0), "digital silence, 2 s"),
        ("silence_5s", _silence(5.0), "digital silence, 5 s"),
        ("silence_10s", _silence(10.0), "digital silence, 10 s"),
        ("roomtone_3s", _white(3.0, 60, rng), "room tone, very low white noise"),
        ("roomtone_8s", _white(8.0, 90, rng), "room tone, 8 s"),
        ("white_low_4s", _white(4.0, 900, rng), "broadband noise, low level"),
        ("white_mid_4s", _white(4.0, 3500, rng), "broadband noise, mid level"),
        ("white_high_4s", _white(4.0, 9000, rng), "broadband noise, high level"),
        (
            "rotorwash_5s",
            _lowpass(_white(5.0, 12000, rng), 0.25),
            "band-limited rotor wash",
        ),
        (
            "rumble_5s",
            _mix(_tone(5.0, 55.0, 7000), _lowpass(_white(5.0, 4000, rng), 0.05)),
            "airframe rumble, 55 Hz plus low noise",
        ),
        (
            "rumble_harmonic_6s",
            _mix(_tone(6.0, 110.0, 5000), _tone(6.0, 220.0, 2500), _white(6.0, 800, rng)),
            "motor harmonics, 110/220 Hz",
        ),
        ("gusts_6s", _gusts(6.0, rng), "wind gusts across the microphone"),
        ("gusts_12s", _gusts(12.0, rng), "wind gusts, long window"),
        ("clicks_4s", _clicks(4.0, rng), "transient clicks, no speech"),
        (
            "clicks_in_noise_5s",
            _mix(_clicks(5.0, rng), _white(5.0, 700, rng)),
            "transient clicks over room tone",
        ),
        (
            "tone_sweep_pair_4s",
            _mix(_tone(4.0, 400.0, 4000), _tone(4.0, 1200.0, 2000)),
            "steady two-tone, speech band",
        ),
        (
            "roomtone_then_silence_9s",
            _mix(_white(4.0, 120, rng), _silence(9.0)),
            "room tone that stops, then silence",
        ),
        ("silence_1s", _silence(1.0), "digital silence, 1 s (below VAD window)"),
        ("white_mid_12s", _white(12.0, 3500, rng), "broadband noise, long window"),
        (
            "rotorwash_gusts_8s",
            _mix(_lowpass(_white(8.0, 9000, rng), 0.25), _gusts(8.0, rng)),
            "rotor wash plus wind",
        ),
    ]
    written: list[tuple[str, str]] = []
    for name, samples, description in stimuli:
        _write_wav(directory / f"{name}.wav", samples)
        written.append((f"{name}.wav", description))
    return written


# --- whisper.cpp discovery -------------------------------------------------


def find_whisper() -> tuple[Path, Path]:
    """Locate `(binary, model)`. Raises `FileNotFoundError` with what to do."""
    roots: list[Path] = []
    env_root = os.environ.get("WHISPER_CPP_DIR")
    if env_root:
        roots.append(Path(env_root))
    roots.extend(CANDIDATE_DIRS)

    tried: list[str] = []
    for root in roots:
        if not root.is_dir():
            tried.append(f"{root} (no such directory)")
            continue
        binary = None
        for subdir in BINARY_SUBDIRS:
            for name in BINARY_NAMES:
                candidate = root / subdir / name
                if candidate.is_file() and os.access(candidate, os.X_OK):
                    binary = candidate
                    break
            if binary:
                break
        model = root / MODEL_RELPATH
        if binary is None:
            tried.append(f"{root} (no {'/'.join(BINARY_NAMES)} under {BINARY_SUBDIRS})")
        elif not model.is_file():
            tried.append(f"{root} (binary found, missing {MODEL_RELPATH})")
        else:
            return binary, model

    on_path = shutil.which("whisper-cli") or shutil.which("whisper")
    if on_path:
        tried.append(f"{on_path} on PATH (found, but no {MODEL_RELPATH} beside it)")

    raise FileNotFoundError(
        "whisper.cpp with the tiny.en model was not found. Tried:\n  "
        + "\n  ".join(tried)
        + "\n\nBuild it and fetch the model, then re-run:\n"
        "  git clone https://github.com/ggml-org/whisper.cpp ~/whisper.cpp\n"
        "  cmake -B build -S ~/whisper.cpp && cmake --build build -j\n"
        "  ~/whisper.cpp/models/download-ggml-model.sh tiny.en\n"
        "Or point WHISPER_CPP_DIR at an existing checkout."
    )


def transcribe(binary: Path, model: Path, wav: Path) -> str:
    """Run whisper.cpp on one file and return its transcript, stripped."""
    result = subprocess.run(
        [
            str(binary),
            "-m", str(model),
            "-f", str(wav),
            "-nt",            # no timestamps: we want the text only
            "-np",            # no progress prints on stdout
            "-l", "en",
            "-t", "4",
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"whisper.cpp failed on {wav.name} (exit {result.returncode}):\n{result.stderr}"
        )
    # With -nt the transcript is stdout; whisper.cpp puts its banner on stderr.
    return " ".join(result.stdout.split())


# --- entry point -----------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--keep-wavs",
        type=Path,
        default=None,
        help="write the stimulus WAVs here instead of a temporary directory",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=OUTPUT_PATH, help="where to write the JSON"
    )
    args = parser.parse_args(argv)

    try:
        binary, model = find_whisper()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        print(
            "\nNothing was written. data/ood.py will use its authored fallback and "
            "stamp those rows 'authored_asr_garbage_pending_harvest'.",
            file=sys.stderr,
        )
        return 1

    print(f"whisper.cpp: {binary}")
    print(f"model:       {model}")

    with tempfile.TemporaryDirectory(prefix="asr-garbage-") as tmp:
        wav_dir = args.keep_wavs or Path(tmp)
        wav_dir.mkdir(parents=True, exist_ok=True)
        stimuli = build_stimuli(wav_dir)
        print(f"synthesised {len(stimuli)} stimuli into {wav_dir}")

        records: list[dict[str, str]] = []
        for filename, description in stimuli:
            text = transcribe(binary, model, wav_dir / filename)
            records.append({"stimulus": filename, "description": description, "text": text})
            print(f"  {filename:<26} -> {text!r}")

    payload = {
        "model": "tiny.en",
        "binary": str(binary),
        "sample_rate": SAMPLE_RATE,
        "seed": SEED,
        "note": (
            "whisper.cpp output on synthesised silence and noise. Verbatim: "
            "punctuation and bracket markers are the artefact under test."
        ),
        "records": records,
        "transcripts": [r["text"] for r in records],
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    unique = len({r["text"] for r in records})
    print(f"\nwrote {args.output} --- {len(records)} stimuli, {unique} distinct transcripts")
    if unique < len(records):
        print(
            f"({len(records) - unique} repeats: whisper converges on the same "
            "hallucination across stimuli, which is itself the finding)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
