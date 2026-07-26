#!/usr/bin/env python3
"""Exp-0, transcription half: 300 Common Voice clips through `tiny.en`.

`IMPLEMENTATION_ROADMAP.md` Session 03 schedules this overnight and Part 8 puts
Exp-0 on the **never cut** list: the golden set has one speaker by deliberate
choice, and this is the only place the project says anything about speakers who
are not the author.

**It runs on the workstation, not the Pi, and that is not a compromise.** Exp-0
reports WER, which is a property of the acoustic model and the audio --- greedy
decode over a fixed model gives the same transcript on any machine. Nothing in
Exp-0 is timed. The Pi matters for Exp-1/2/3, where latency, thermals and RSS are
the measurement; here it would only mean waiting longer for identical text.

Writes one JSONL row per clip with the reference, the hypothesis and the accent
bucket. The WER itself is Session 04's `eval/norm.py` + `eval/exp0.py`, because
the normalisation is a committed contract (§2.7) and must not be improvised here.

Usage:
    python eval/exp0_transcribe.py
    python eval/exp0_transcribe.py --limit 20     # smoke test
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):  # `python eval/exp0_transcribe.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.asr import find_whisper, transcribe_batch

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "data" / "commonvoice" / "exp0_manifest.jsonl"
OUTPUT = REPO / "results" / "exp0_transcripts.jsonl"


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--limit", type=int, help="transcribe only the first N (smoke test)")
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args(argv)

    rows = [json.loads(l) for l in args.manifest.read_text().splitlines() if l.strip()]
    if args.limit:
        rows = rows[: args.limit]

    binary, model = find_whisper()
    print(f"binary : {binary}")
    print(f"model  : {model.name}")
    print(f"clips  : {len(rows)}")

    paths = [REPO / r["path"] for r in rows]
    missing = [p for p in paths if not p.is_file()]
    if missing:
        raise SystemExit(f"{len(missing)} clip(s) missing, e.g. {missing[0]}")

    started = time.monotonic()
    results = transcribe_batch(paths, threads=args.threads)
    elapsed = time.monotonic() - started

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row, result in zip(rows, results):
            handle.write(
                json.dumps(
                    {
                        "id": row["id"],
                        "bucket": row["bucket"],
                        "accents": row["accents"],
                        "age": row.get("age", ""),
                        "gender": row.get("gender", ""),
                        "seconds": row["seconds"],
                        "reference": row["sentence"],
                        "hypothesis": getattr(result, "text", str(result)),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    empty = sum(1 for r in results if not getattr(r, "text", "").strip())
    print(f"\n{len(results)} transcribed in {elapsed / 60:.1f} min ({elapsed / len(results):.2f} s/clip)")
    if empty:
        print(f"[!] {empty} clip(s) produced no text -- these become 100% WER, not dropped rows")
    print(f"wrote {args.output}")
    print("\nNext: Session 04 writes eval/norm.py, then eval/exp0.py computes WER per bucket.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
