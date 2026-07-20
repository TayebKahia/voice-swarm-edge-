#!/usr/bin/env python3
"""Exp-0's material --- 300 Common Voice clips, stratified by accent.

`IMPLEMENTATION_ROADMAP.md` Session 04 task 4: Exp-0 reports bootstrap 95% CI on
WER, **WER per accent bucket**, and **the author positioned as a percentile, not
pass/fail**. That framing is the reason this corpus exists. The golden set has one
speaker by deliberate choice (§0.2 conflict 1) --- holding the speaker fixed is
what makes noise the only varying factor in Exp-3 --- and the cost of that choice
is that nothing in the golden set says whether `tiny.en` works for anyone else.
Exp-0 is where that external validity is recovered, and it recovers it only if the
sample spans accents rather than averaging over one.

So the sampling is stratified by accent bucket and not uniform. A uniform draw
from this shard would be 39% United States English and would put four of the
twenty-odd accent groups at zero, which is precisely the reading that would make
the author's own WER look unremarkable for the wrong reason.

**Provenance, stated plainly:** Mozilla's own download endpoint requires a browser
consent step, so the bytes come from `fsicoli/common_voice_17_0`, an ungated
mirror of the same 17.0 release. The corpus, the release and the CC0 licence are
Mozilla's; the mirror is recorded as a mirror in `asset_manifest.json` and in the
dataset card rather than cited as the official distribution.

Usage:
    python data/commonvoice.py               # sample, decode, write the manifest
    python data/commonvoice.py --report      # summarise what is already on disk
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import tarfile
from collections import Counter
from pathlib import Path
from typing import Sequence

import numpy as np
import soundfile as sf
import soxr

if __package__ in (None, ""):  # `python data/commonvoice.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATA_DIR = Path(__file__).resolve().parent
CV_DIR = DATA_DIR / "commonvoice"
SRC_DIR = CV_DIR / "_src"
CLIPS_DIR = CV_DIR / "clips"
MANIFEST_PATH = CV_DIR / "exp0_manifest.jsonl"
SUMMARY_PATH = CV_DIR / "exp0_summary.json"

TARGET_RATE = 16_000
SUBTYPE = "PCM_16"
SAMPLE_SIZE = 300
DEFAULT_SEED = 42

#: Community validation: Common Voice promotes a clip to `validated` at two
#: up-votes. A clip carrying any down-vote has had its transcript disputed, and a
#: disputed reference makes a meaningless WER.
MIN_UP_VOTES = 2
MAX_DOWN_VOTES = 0

#: Clips outside this range are not comparable to the golden set, whose utterances
#: run 2-8 s. A 1 s clip gives WER a denominator of three or four words.
MIN_SECONDS = 1.5
MAX_SECONDS = 12.0


def _stable_seed(*parts: object) -> int:
    blob = "\x1f".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(blob).digest()[:8], "big")


#: An accent label held by fewer than this many source rows is free text, not a
#: group: this shard carries "ohio", "northern cali" and "Deutsch English", each
#: entered once. A bucket of one has no reportable WER, so they are pooled rather
#: than each becoming a stratum the sampler then has to fill.
MIN_BUCKET_ROWS = 10
OTHER_BUCKET = "Other (free-text accent labels)"


def _first_accent(raw: str) -> str:
    """Split on the first comma that is not inside parentheses.

    Common Voice's own labels contain commas --- "India and South Asia (India,
    Pakistan, Sri Lanka)" is one label --- and a naive `split(",")` truncates it
    to "India and South Asia (India", which is what the first build of this file
    wrote into the manifest for 69 of the 300 clips.
    """
    depth = 0
    for index, character in enumerate(raw):
        if character == "(":
            depth += 1
        elif character == ")":
            depth = max(0, depth - 1)
        elif character == "," and depth == 0:
            return raw[:index].strip()
    return raw.strip()


def accent_bucket(raw: str, known: frozenset[str] | None = None) -> str:
    """One bucket per clip.

    Common Voice lets a speaker tick several accents, and 10 rows in this shard
    tick two. Splitting the clip across buckets would double-count it in the
    per-bucket WER; the first entry is taken and the full string is kept in the
    manifest so the choice is inspectable.
    """
    first = _first_accent(raw)
    if known is not None and first not in known:
        return OTHER_BUCKET
    return first


def populated_buckets(rows: list[dict]) -> frozenset[str]:
    counts = Counter(_first_accent(row["accents"]) for row in rows)
    return frozenset(name for name, count in counts.items() if count >= MIN_BUCKET_ROWS)


def read_rows(tsv_path: Path) -> list[dict]:
    with tsv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        return [row for row in reader]


def eligible(rows: list[dict]) -> list[dict]:
    keep = []
    for row in rows:
        if not row.get("accents", "").strip():
            continue
        try:
            if int(row["up_votes"]) < MIN_UP_VOTES or int(row["down_votes"]) > MAX_DOWN_VOTES:
                continue
        except (KeyError, ValueError):
            continue
        keep.append(row)
    return keep


def stratified_sample(rows: list[dict], size: int, seed: int) -> list[dict]:
    """Round-robin over accent buckets, largest bucket last.

    Filling by round robin rather than by proportional quota gives the small
    buckets --- Welsh, Singaporean, West Indies --- a non-zero count before the
    large ones take the remainder, which is what makes a per-bucket WER reportable
    at all. The buckets are unequal and the manifest says so; a bucket of four is
    reported with its n beside it, never smoothed away.
    """
    known = populated_buckets(rows)
    by_bucket: dict[str, list[dict]] = {}
    for row in rows:
        by_bucket.setdefault(accent_bucket(row["accents"], known), []).append(row)
    for bucket, items in by_bucket.items():
        items.sort(key=lambda r: _stable_seed(seed, "cv-sample", bucket, r["path"]))

    order = sorted(by_bucket, key=lambda b: (len(by_bucket[b]), b))
    chosen: list[dict] = []
    position = 0
    while len(chosen) < size and any(len(by_bucket[b]) > position for b in order):
        for bucket in order:
            if len(chosen) >= size:
                break
            if len(by_bucket[bucket]) > position:
                chosen.append(by_bucket[bucket][position])
        position += 1
    return chosen[:size]


def decode(member: tarfile.ExFileObject) -> tuple[np.ndarray, float]:
    audio, rate = sf.read(member, dtype="float32", always_2d=True)
    mono = audio[:, 0]
    seconds = mono.size / rate
    if rate != TARGET_RATE:
        mono = soxr.resample(mono, rate, TARGET_RATE, quality="VHQ")
    return np.ascontiguousarray(mono, dtype=np.float32), seconds


def build(seed: int) -> int:
    tsv_path = SRC_DIR / "test.tsv"
    tar_path = SRC_DIR / "en_test_0.tar"
    for path in (tsv_path, tar_path):
        if not path.is_file():
            raise SystemExit(
                f"missing {path}. Run `python data/fetch_assets.py --commonvoice` first."
            )

    rows = read_rows(tsv_path)
    usable = eligible(rows)
    known = populated_buckets(usable)
    print(f"{len(rows)} rows, {len(usable)} with an accent label and a clean validation record")
    print(f"{len(known)} accent groups with >= {MIN_BUCKET_ROWS} rows; the rest pool into one")

    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    for stale in CLIPS_DIR.glob("*.wav"):
        stale.unlink()

    # Oversample: some clips fall outside the duration window and are replaced
    # rather than silently leaving the sample short of 300.
    candidates = stratified_sample(usable, SAMPLE_SIZE * 3, seed)
    wanted = {row["path"]: row for row in candidates}

    records: list[dict] = []
    with tarfile.open(tar_path) as archive:
        for member in archive:
            if len(records) >= SAMPLE_SIZE:
                break
            name = Path(member.name).name
            row = wanted.get(name)
            if row is None or not member.isfile():
                continue
            handle = archive.extractfile(member)
            if handle is None:
                continue
            try:
                audio, seconds = decode(handle)
            except Exception as exc:  # a handful of shard members fail to decode
                print(f"  skipped {name}: {exc}")
                continue
            if not (MIN_SECONDS <= seconds <= MAX_SECONDS):
                continue

            out_path = CLIPS_DIR / f"{Path(name).stem}.wav"
            sf.write(str(out_path), audio, TARGET_RATE, subtype=SUBTYPE)
            records.append(
                {
                    "id": Path(name).stem,
                    "path": str(out_path.relative_to(DATA_DIR.parent)),
                    "sentence": row["sentence"],
                    "accents": row["accents"],
                    "bucket": accent_bucket(row["accents"], known),
                    "age": row.get("age", ""),
                    "gender": row.get("gender", ""),
                    "seconds": round(seconds, 3),
                    "client_id": row["client_id"][:16],
                }
            )

    if len(records) < SAMPLE_SIZE:
        print(f"[!] only {len(records)} clips met the duration window; expected {SAMPLE_SIZE}")

    records.sort(key=lambda r: r["id"])
    MANIFEST_PATH.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8"
    )

    buckets = Counter(r["bucket"] for r in records)
    summary = {
        "seed": seed,
        "clips": len(records),
        "hours": round(sum(r["seconds"] for r in records) / 3600, 3),
        "speakers": len({r["client_id"] for r in records}),
        "buckets": dict(buckets.most_common()),
        "source": "Common Voice 17.0 en test (mirror fsicoli/common_voice_17_0)",
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report(summary)
    return 0 if len(records) >= SAMPLE_SIZE else 1


def report(summary: dict) -> None:
    print(
        f"\n{summary['clips']} clips, {summary['hours']:.2f} h, "
        f"{summary['speakers']} distinct speakers"
    )
    print(f"{'accent bucket':<52}{'n':>5}")
    for bucket, count in summary["buckets"].items():
        print(f"{bucket:<52}{count:>5}")
    print(f"\nmanifest: {MANIFEST_PATH}")


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args(argv)

    if args.report:
        if not SUMMARY_PATH.is_file():
            raise SystemExit(f"{SUMMARY_PATH} does not exist -- build the sample first")
        report(json.loads(SUMMARY_PATH.read_text()))
        return 0
    return build(args.seed)


if __name__ == "__main__":
    raise SystemExit(run())
