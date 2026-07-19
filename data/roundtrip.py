#!/usr/bin/env python3
"""ASR round-trip augmentation: transcript -> Piper -> noise -> whisper.cpp -> transcript.

    gold_json --> clean_transcript --> Piper TTS --> mix @ SNR --> whisper.cpp --> noisy
         |                                                                          |
         +----------------- the NOISY transcript pairs with the ORIGINAL -----------+

`02_dataset_plan.md` §4 calls this "the single highest-leverage item in the dataset
plan", and the reason is a distribution shift rather than a data volume: training on
clean text and inferring on `whisper.cpp` output is a train/test mismatch that
costs 10--20 points of exact match without ever showing up as a bug. The fix is to
train on text carrying the error distribution of the deployed recogniser, which is
what this produces --- not a hand-crafted approximation of it.

Only the **train** split is round-tripped. `val` and `test_synth` stay clean: `val`
selects checkpoints on exact match and `test_synth` is the paired sample McNemar
operates on, and both are measured on reference text (§2.6).

This script writes `data/roundtrip.jsonl`, the audit trail --- one record per
attempted round-trip with its voice, noise excerpt, realised SNR and similarity to
the clean form. `build_splits.py` consumes it. Re-running is cheap: a row whose
audio and transcript are already on disk is skipped unless `--force`.

Usage:
    python data/roundtrip.py                 # all assigned rows, resume where it stopped
    python data/roundtrip.py --limit 20      # smoke test
    python data/roundtrip.py --force         # re-synthesise everything
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import soundfile as sf

if __package__ in (None, ""):  # `python data/roundtrip.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.asr import DOMAIN_PROMPT, transcribe_batch
from data.composition import DEFAULT_SEED, assign_variants, needs_roundtrip, snr_for
from data.mix_noise import NoiseBank, TARGET_RATE, mix_one, rng_for_item
from data.tts_synth import PiperBank

DATA_DIR = Path(__file__).resolve().parent
RAW_PAIRS = DATA_DIR / "raw_pairs.jsonl"
TTS_DIR = DATA_DIR / "audio" / "tts"
MIXED_DIR = DATA_DIR / "audio" / "roundtrip"
OUTPUT = DATA_DIR / "roundtrip.jsonl"

#: Noise for augmentation comes from the `aug` partition only. The `eval`
#: partition is held back for Exp-3, so no excerpt the model was tuned against is
#: also an excerpt it is tested against (`mix_noise.NoiseBank`).
AUG_PARTITION = "aug"
AUG_SOURCES = ("dregon", "esc50")


def _display(path: Path) -> str:
    """Repo-relative when it can be, absolute otherwise (e.g. a scratch output)."""
    try:
        return str(path.resolve().relative_to(DATA_DIR.parent))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )


def plan(rows: Sequence[dict[str, Any]], seed: int) -> list[tuple[dict[str, Any], str, int]]:
    """The train rows needing a round-trip, with their variant and SNR."""
    train = [row for row in rows if row.get("split") == "train"]
    assignment = assign_variants(train, seed=seed)
    work = []
    for row in train:
        variant = assignment[row["id"]]
        if needs_roundtrip(variant):
            work.append((row, variant, snr_for(variant)))
    return work


def synthesise_and_mix(
    work: Sequence[tuple[dict[str, Any], str, int]],
    *,
    seed: int,
    force: bool,
) -> list[dict[str, Any]]:
    """Render every planned row to a mixed WAV, returning per-row provenance."""
    voices = PiperBank(target_rate=TARGET_RATE)
    bank = NoiseBank(sources=AUG_SOURCES, partition=AUG_PARTITION, target_rate=TARGET_RATE)
    TTS_DIR.mkdir(parents=True, exist_ok=True)
    MIXED_DIR.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    started = time.time()
    for index, (row, variant, snr) in enumerate(work, start=1):
        item_id = row["id"]
        clean_wav = TTS_DIR / f"{item_id}.wav"
        mixed_wav = MIXED_DIR / f"{item_id}__snr{snr:02d}.wav"

        if force or not clean_wav.is_file():
            utterance = voices.synthesize_to(row["transcript"], item_id, seed, clean_wav)
            voice, length_scale = utterance.voice, utterance.length_scale
            speech = utterance.audio
        else:
            voice, length_scale = voices.settings_for(item_id, seed)
            speech, _ = sf.read(str(clean_wav), dtype="float32")

        if force or not mixed_wav.is_file():
            result = mix_one(
                np.asarray(speech, dtype=np.float32),
                snr,
                bank,
                item_id,
                seed=seed,
                sample_rate=TARGET_RATE,
            )
            sf.write(str(mixed_wav), result.audio, TARGET_RATE, subtype="PCM_16")
            noise_key, attenuation = result.noise_key, result.peak_attenuation
        else:
            # The excerpt is a pure function of (seed, id), so it is recoverable
            # without re-mixing; the attenuation is not, and is reported as unknown
            # rather than guessed at.
            _, noise_key = bank.draw(len(speech), rng_for_item(item_id, seed))
            attenuation = None

        records.append(
            {
                "id": item_id,
                "variant": variant,
                "snr_db": snr,
                "clean_transcript": row["transcript"],
                "target": row["target"],
                "gold_intent": row["gold_intent"],
                "template_family": row.get("template_family"),
                "tts_voice": voice,
                "tts_length_scale": round(length_scale, 4),
                "noise_key": noise_key,
                "peak_attenuation": None if attenuation is None else round(attenuation, 6),
                "mixed_path": str(mixed_wav.relative_to(DATA_DIR.parent)),
            }
        )

        if index % 100 == 0 or index == len(work):
            rate = index / max(time.time() - started, 1e-9)
            print(f"    synth+mix {index}/{len(work)}  ({rate:.1f} rows/s)", flush=True)
    return records


def transcribe_all(records: Sequence[dict[str, Any]], threads: int) -> None:
    """Fill `asr_transcript` on every record, in place."""
    paths = [DATA_DIR.parent / record["mixed_path"] for record in records]
    started = time.time()
    results = transcribe_batch(paths, threads=threads)
    for record, result in zip(records, results):
        record["asr_transcript"] = result.text
        record["asr_ok"] = result.ok
        if not result.ok:
            record["asr_error"] = result.error
    elapsed = time.time() - started
    print(f"    whisper.cpp: {len(results)} files in {elapsed:.0f}s ({len(results)/max(elapsed,1e-9):.1f}/s)")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--limit", type=int, default=None, help="process only the first N rows")
    parser.add_argument("--force", action="store_true", help="re-synthesise and re-mix everything")
    parser.add_argument("--threads", type=int, default=4, help="whisper.cpp threads")
    parser.add_argument("--input", type=Path, default=RAW_PAIRS)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)

    rows = read_jsonl(args.input)
    work = plan(rows, args.seed)
    if args.limit:
        work = work[: args.limit]

    by_variant: dict[str, int] = {}
    for _, variant, _ in work:
        by_variant[variant] = by_variant.get(variant, 0) + 1
    print(f"[*] round-trip plan: {len(work)} rows " + ", ".join(f"{k}={v}" for k, v in sorted(by_variant.items())))
    print(f"[*] ASR: whisper.cpp tiny.en, domain prompt ({len(DOMAIN_PROMPT)} chars), -t {args.threads}")

    records = synthesise_and_mix(work, seed=args.seed, force=args.force)
    transcribe_all(records, args.threads)

    failed = [r for r in records if not r.get("asr_ok")]
    write_jsonl(args.output, records)
    print(f"[+] wrote {len(records)} records to {_display(args.output)}")
    if failed:
        print(f"[-] {len(failed)} row(s) had no transcript; build_splits.py will fall back to clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
