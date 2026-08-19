#!/usr/bin/env python3
"""Offline 3:1 resample of the golden set --- 48 kHz masters to the 16 kHz corpus.

`prd.md` D4 and `requirements.txt:27`: 48 kHz capture, **offline `soxr` VHQ**
resample to 16 kHz, **never ALSA `plug`**. ALSA's plug layer picks a converter
nobody recorded and can change it between boots, so the resampling applied to the
corpus would be unknown and unreproducible --- and it sits upstream of every WER
and CRR number in the project.

The masters in `data/audio/s1/` are never written to. This produces a *derived*
corpus in `data/audio/s1_16k/`, which is gitignored and rebuilt by re-running
this file. If the derived corpus is ever wrong it is thrown away; if a master is
ever wrong there is nothing to do.

**One gain for the whole session, not one per file.** S0 measured the BOYA
peaking at -36.06 dBFS, 16 dB under Table 22's target, and recorded the decision
to normalise offline. Normalising each file to its own ceiling would equalise a
shouted command and a trailing-off one, erasing exactly the level variation the
golden set exists to carry. A single scalar per session lifts the whole corpus so
that its loudest file lands on `PEAK_CEILING_DBFS` and every relative level is
preserved. The scalar is written to the manifest, so the operation is one
multiplication away from being undone.

The gain does not move any SNR in Exp-3: `mix_noise` levels the noise against
each file's *active-speech* RMS, so a common gain on the speech cancels.

Usage:
    python data/resample.py --session s1
    python data/resample.py --session s1 --no-normalise   # diagnostics only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Sequence

import numpy as np
import soundfile as sf
import soxr

if __package__ in (None, ""):  # `python data/resample.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.mix_noise import active_speech_rms

DATA_DIR = Path(__file__).resolve().parent
AUDIO_DIR = DATA_DIR / "audio"

SOURCE_RATE = 48_000
TARGET_RATE = 16_000
QUALITY = "VHQ"
OUTPUT_SUBTYPE = "PCM_16"

#: The ceiling the loudest file in a session is lifted to. -14 dBFS is the figure
#: recorded in the S0 report: high enough to keep quantisation noise irrelevant at
#: 16-bit, low enough that no inter-sample peak introduced by the resampler's
#: ringing can reach full scale.
PEAK_CEILING_DBFS = -14.0

#: A gain past this would mean the session was recorded ~20 dB under the chain S0
#: characterised, which is a capture fault, not something to paper over.
MAX_GAIN_DB = 24.0


def dbfs(level: float) -> float:
    return 20.0 * float(np.log10(max(level, 1e-12)))


def _display(path: Path) -> str:
    """Repo-relative when it can be, absolute otherwise (e.g. a scratch output)."""
    try:
        return str(path.resolve().relative_to(DATA_DIR.parent))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_master(path: Path) -> np.ndarray:
    """Read one 48 kHz mono master, refusing anything else."""
    audio, rate = sf.read(str(path), dtype="float32", always_2d=True)
    if rate != SOURCE_RATE:
        raise SystemExit(
            f"{path.name}: {rate} Hz, expected {SOURCE_RATE}. A master recorded at "
            "the wrong rate cannot be fixed here -- re-record it."
        )
    return np.ascontiguousarray(audio[:, 0], dtype=np.float32)


def remove_dc(audio: np.ndarray) -> tuple[np.ndarray, float]:
    """Subtract the constant offset, returning the signal and what was removed.

    A DC offset is a hardware artifact with no acoustic content --- S0 measured
    +0.0065 on this chain, about -43.7 dBFS and some 20 dB above the room floor.
    It wastes headroom, biases every RMS taken over the file, and survives
    resampling. Removing it here, in the derived corpus, keeps the masters as the
    ADC wrote them (ADR-0005 D1) while giving every consumer a centred signal. The
    removed constant is recorded per file, so the step is reversible.
    """
    if audio.size == 0:
        return audio, 0.0
    offset = float(np.mean(audio, dtype=np.float64))
    return (audio - offset).astype(np.float32), offset


def resample(audio: np.ndarray) -> np.ndarray:
    """The single resampling call in the project.

    `mix_noise.load_mono` makes the identical call, so a file that reaches a
    consumer through either path carries the same samples. `test_resample.py`
    asserts that rather than trusting it.
    """
    return np.ascontiguousarray(
        soxr.resample(audio, SOURCE_RATE, TARGET_RATE, quality=QUALITY), dtype=np.float32
    )


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--session", default="s1", choices=("s1", "s2", "s3"))
    parser.add_argument("--input", type=Path, help="default: data/audio/<session>")
    parser.add_argument("--output", type=Path, help="default: data/audio/<session>_16k")
    parser.add_argument(
        "--no-normalise",
        action="store_true",
        help="skip the session gain; the output is then a pure rate conversion",
    )
    parser.add_argument("--peak-dbfs", type=float, default=PEAK_CEILING_DBFS)
    parser.add_argument(
        "--glob",
        default="[0-9]*.wav",
        help="master filenames (default: numbered golden takes; the wake session is w*.wav)",
    )
    args = parser.parse_args(argv)

    source = args.input or (AUDIO_DIR / args.session)
    destination = args.output or (AUDIO_DIR / f"{args.session}_16k")
    masters = sorted(source.glob(args.glob))
    if not masters:
        raise SystemExit(f"no masters in {source} -- record the session first")
    destination.mkdir(parents=True, exist_ok=True)

    print(f"{len(masters)} masters in {source}")
    print(f"{SOURCE_RATE} -> {TARGET_RATE} Hz, soxr {QUALITY}, offline")

    # Pass 1: convert, and find the session peak on the *converted* signal, since
    # the resampler's ringing can push a sample above the master's own peak.
    converted: dict[str, np.ndarray] = {}
    offsets: dict[str, float] = {}
    session_peak = 0.0
    for path in masters:
        centred, offsets[path.stem] = remove_dc(read_master(path))
        samples = resample(centred)
        converted[path.stem] = samples
        session_peak = max(session_peak, float(np.max(np.abs(samples))) if samples.size else 0.0)

    if args.no_normalise:
        gain = 1.0
    else:
        gain = (10.0 ** (args.peak_dbfs / 20.0)) / max(session_peak, 1e-12)
        if dbfs(gain) > MAX_GAIN_DB:
            raise SystemExit(
                f"session gain would be {dbfs(gain):+.1f} dB (cap {MAX_GAIN_DB:.0f} dB). "
                "The session is far quieter than the chain S0 characterised -- check the "
                "microphone and ALSA capture level before normalising around it."
            )

    print(
        f"session peak {dbfs(session_peak):+.2f} dBFS -> gain {dbfs(gain):+.2f} dB "
        f"(ceiling {args.peak_dbfs:.1f} dBFS), one scalar for all {len(masters)} files"
    )

    records = []
    for path in masters:
        samples = converted[path.stem] * gain
        out_path = destination / path.name
        sf.write(out_path, samples, TARGET_RATE, subtype=OUTPUT_SUBTYPE)
        records.append(
            {
                "id": path.stem,
                "master": _display(path),
                "master_sha256": sha256(path),
                "output": _display(out_path),
                "seconds": round(samples.size / TARGET_RATE, 3),
                "dc_offset_removed": round(offsets[path.stem], 6),
                "peak_dbfs": round(dbfs(float(np.max(np.abs(samples)))), 2),
                "active_speech_dbfs": round(dbfs(active_speech_rms(samples, TARGET_RATE)), 2),
            }
        )

    manifest = {
        "session": args.session,
        "source_rate": SOURCE_RATE,
        "target_rate": TARGET_RATE,
        "resampler": f"soxr {soxr.__version__} quality={QUALITY}",
        "dc_removed": True,
        "normalised": not args.no_normalise,
        "peak_ceiling_dbfs": args.peak_dbfs if not args.no_normalise else None,
        "session_gain_db": round(dbfs(gain), 4),
        "session_peak_before_dbfs": round(dbfs(session_peak), 2),
        "files": records,
    }
    manifest_path = destination / "resample_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    active = [r["active_speech_dbfs"] for r in records]
    mean_offset = float(np.mean(list(offsets.values()))) if offsets else 0.0
    print(f"wrote {len(records)} files to {destination}")
    print(f"mean DC offset removed: {mean_offset:+.6f} ({dbfs(abs(mean_offset)):.1f} dBFS)")
    print(
        f"active-speech level: median {float(np.median(active)):.1f} dBFS, "
        f"range [{min(active):.1f}, {max(active):.1f}]"
    )
    print(f"manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
