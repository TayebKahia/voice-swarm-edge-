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

**The domain prompt is a condition here, not a constant.** `data/asr.py` carries the
deployed configuration, and that includes a prompt listing the command vocabulary
("swarm, drone, takeoff, land, ..."). On the author's commands those words are
present and the prompt helps --- spike S6 measured the benefit. On a Common Voice
sentence about boots and horizons they are absent, so the prompt can only bias the
decoder toward words the speaker did not say.

That asymmetry runs in the one direction that matters: it inflates the native
speakers' WER while leaving the author's untouched, which would flatter the author's
position in exactly the distribution Table 16 exists to place him honestly within.
So both conditions are run and both are reported. `--no-prompt` is the matched
condition for the Table 16 comparison; the prompted pass describes the deployed
configuration and is what Exp-3 inherits.

Writes one JSONL row per clip with the reference, the hypothesis and the accent
bucket. The WER itself is Session 04's `eval/norm.py` + `eval/exp0.py`, because
the normalisation is a committed contract (§2.7) and must not be improvised here.

Usage:
    python eval/exp0_transcribe.py                # deployed config, with the prompt
    python eval/exp0_transcribe.py --no-prompt    # matched condition for Table 16
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

from data.asr import DOMAIN_PROMPT, find_whisper, transcribe_batch

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "data" / "commonvoice" / "exp0_manifest.jsonl"
OUTPUT = REPO / "results" / "exp0_transcripts.jsonl"

#: The author's own half of Table 16. Same binary, same model, same normalisation
#: downstream --- only the speaker changes, which is the whole comparison.
GOLDEN_MANIFEST = REPO / "data" / "test_golden.jsonl"
GOLDEN_AUDIO = REPO / "data" / "audio" / "s1_16k"
GOLDEN_META = REPO / "data" / "audio" / "s1" / "session_meta.json"
GOLDEN_OUTPUT = REPO / "results" / "exp0_author.jsonl"

#: Not an accent label from the Common Voice taxonomy --- it is the author, and the
#: bucket name says so rather than inventing a category that corpus never had.
AUTHOR_BUCKET = "Author (L2 English, domain commands)"


def _commonvoice_rows(manifest: Path) -> list[dict]:
    rows = [json.loads(l) for l in manifest.read_text().splitlines() if l.strip()]
    for row in rows:
        row["path"] = REPO / row["path"]
    return rows


def _golden_rows(manifest: Path) -> list[dict]:
    """The 200 golden-set utterances, read from the 16 kHz resampled masters.

    `whisper.cpp` requires 16 kHz, and `data/resample.py` already produced exactly
    that from the 48 kHz captures. Re-deriving it here would be a second resampling
    path that could drift from the one the rest of the pipeline uses.
    """
    seconds = {
        take_id: take.get("seconds", 0.0)
        for take_id, take in json.loads(GOLDEN_META.read_text())["takes"].items()
    }
    rows = []
    for line in manifest.read_text().splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        rows.append(
            {
                "id": item["id"],
                "bucket": AUTHOR_BUCKET,
                "accents": AUTHOR_BUCKET,
                "age": "",
                "gender": "",
                "seconds": seconds.get(item["id"], 0.0),
                "sentence": item["transcript"],
                "path": GOLDEN_AUDIO / f"{item['id']}.wav",
            }
        )
    return rows


CORPORA = {"commonvoice": _commonvoice_rows, "golden": _golden_rows}


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--corpus",
        choices=sorted(CORPORA),
        default="commonvoice",
        help="commonvoice = the 300-clip multi-speaker sample; golden = the author's 200",
    )
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int, help="transcribe only the first N (smoke test)")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="decode without the domain prompt -- the matched condition for Table 16",
    )
    args = parser.parse_args(argv)

    if args.manifest is None:
        args.manifest = GOLDEN_MANIFEST if args.corpus == "golden" else MANIFEST
    if args.output is None:
        args.output = GOLDEN_OUTPUT if args.corpus == "golden" else OUTPUT
        if args.no_prompt:
            args.output = args.output.with_name(args.output.stem + "_noprompt.jsonl")
        if args.limit:
            # A smoke test must not be able to truncate the real results file. It
            # already happened once: `--limit 2` left a 2-row exp0_author.jsonl
            # where 200 rows had been, and only the line count gave it away.
            args.output = args.output.with_name(
                f"{args.output.stem}_limit{args.limit}.jsonl"
            )

    rows = CORPORA[args.corpus](args.manifest)
    if args.limit:
        rows = rows[: args.limit]

    binary, model = find_whisper()
    print(f"binary : {binary}")
    print(f"model  : {model.name}")
    print(f"corpus : {args.corpus}")
    print(f"clips  : {len(rows)}")
    print(f"prompt : {'NONE (matched condition)' if args.no_prompt else 'domain prompt (deployed config)'}")

    paths = [r["path"] for r in rows]
    missing = [p for p in paths if not p.is_file()]
    if missing:
        raise SystemExit(f"{len(missing)} clip(s) missing, e.g. {missing[0]}")

    started = time.monotonic()
    results = transcribe_batch(
        paths, threads=args.threads, prompt=None if args.no_prompt else DOMAIN_PROMPT
    )
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
                        "prompt": "" if args.no_prompt else DOMAIN_PROMPT,
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
