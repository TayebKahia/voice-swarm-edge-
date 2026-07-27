#!/usr/bin/env python3
"""Exp-0 analysis: WER by accent bucket, and where the author sits in that spread.

`prd.md` NFR-11: "Word error rate of `tiny.en` on the author's speech, positioned
against a multi-speaker distribution", reported with a bootstrap 95% CI. Table 16
is the output. The point is **not** a pass/fail threshold --- there is no defensible
WER a thesis could declare acceptable in the abstract --- but a position: the golden
set has one speaker by deliberate choice (§9.3), and this is the only place the
project says anything about speakers who are not the author.

Three conditions are read, not one:

    results/exp0_transcripts.jsonl           300 Common Voice clips, domain prompt
    results/exp0_transcripts_noprompt.jsonl  the same clips, no prompt
    results/exp0_author.jsonl                the author's 200 golden utterances

**Why the prompt is a condition.** `data/asr.py` holds the deployed configuration and
it includes a prompt naming the command vocabulary. On the author's commands those
words are present and the prompt helps; on a Common Voice sentence about boots and
horizons they are absent and it can only bias the decoder toward words the speaker
did not say. That asymmetry inflates the native speakers' WER and leaves the
author's alone --- it flatters precisely the comparison this table exists to make
honestly. So the matched (unprompted) condition is what positions the author, the
prompted pass is reported beside it, and the gap between them is itself a reported
number rather than a silent choice.

**One confound cannot be removed and is stated instead of buried.** The author read
drone commands; the Common Voice speakers read general English. The two WERs are
over different text, so the position is indicative and is labelled as such. Closing
it properly would mean the author reading Common Voice sentences --- about twenty
would do --- which is recorded as the upgrade path rather than claimed as done.

Usage:
    python eval/exp0.py
    python eval/exp0.py --min-bucket 10
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):  # `python eval/exp0.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.norm import edits
from eval.stats import BOOTSTRAP_SEED, bootstrap_ratio_ci

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results"

PROMPTED = RESULTS / "exp0_transcripts.jsonl"
UNPROMPTED = RESULTS / "exp0_transcripts_noprompt.jsonl"
AUTHOR = RESULTS / "exp0_author.jsonl"
AUTHOR_UNPROMPTED = RESULTS / "exp0_author_noprompt.jsonl"

CSV_OUT = RESULTS / "exp0.csv"
TABLE_OUT = RESULTS / "table16_asr_speaker_sensitivity.md"

#: Buckets smaller than this are reported but carry no interval: a bootstrap over
#: four utterances reproduces the same four utterances in most replicates, so the
#: interval it draws is a statement about the resampler, not about the accent.
MIN_BUCKET_FOR_CI = 10


@dataclass(frozen=True)
class Scored:
    """One bucket's pooled WER and the per-utterance counts behind it."""

    bucket: str
    errors: list[int]
    words: list[int]
    sub: int
    dele: int
    ins: int

    @property
    def n(self) -> int:
        return len(self.errors)

    @property
    def total_words(self) -> int:
        return sum(self.words)

    @property
    def wer(self) -> float:
        return sum(self.errors) / self.total_words if self.total_words else float("nan")

    def ci(self, seed: int) -> tuple[float, float]:
        if self.n < MIN_BUCKET_FOR_CI:
            return float("nan"), float("nan")
        return bootstrap_ratio_ci(self.errors, self.words, seed=seed)


def _read(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _bucket_seed(bucket: str) -> int:
    """A per-bucket bootstrap seed, stable across processes.

    `hash()` is salted per interpreter run, so a `hash()`-derived seed would draw a
    different interval every time the script is run (ADR-0004 D6, same reasoning as
    the split hashing).
    """
    import hashlib

    digest = hashlib.sha256(bucket.encode("utf-8")).hexdigest()[:8]
    return (BOOTSTRAP_SEED + int(digest, 16)) % (2**32)


def score(rows: Sequence[dict], *, by: str = "bucket") -> dict[str, Scored]:
    """Group rows and count edits. Unscoreable references are dropped, not zeroed."""
    grouped: dict[str, dict[str, list]] = {}
    for row in rows:
        counted = edits(row["reference"], row["hypothesis"])
        if counted.ref_words == 0:
            continue
        slot = grouped.setdefault(
            row[by], {"errors": [], "words": [], "sub": 0, "dele": 0, "ins": 0}
        )
        slot["errors"].append(counted.total)
        slot["words"].append(counted.ref_words)
        slot["sub"] += counted.sub
        slot["dele"] += counted.dele
        slot["ins"] += counted.ins
    return {
        name: Scored(name, s["errors"], s["words"], s["sub"], s["dele"], s["ins"])
        for name, s in grouped.items()
    }


def pooled(rows: Sequence[dict], label: str = "all") -> Scored:
    """Every row as one group --- the corpus figure, under `label`."""
    return score([dict(row, _all=label) for row in rows], by="_all").get(
        label, Scored(label, [], [], 0, 0, 0)
    )


def _ordinal(value: float) -> str:
    """53 -> '53rd'. Written out because '53th' in a thesis table is a tell."""
    number = int(round(value))
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def position(author_wer: float, bucket_wers: Sequence[float]) -> tuple[int, int, float]:
    """Where `author_wer` falls among the bucket WERs.

    Returns `(buckets_worse, total, percentile)`. Reported as a count as well as a
    percentage because with fifteen buckets a "73rd percentile" invites more
    precision than eleven-of-fifteen actually carries.
    """
    ordered = sorted(bucket_wers)
    worse = sum(1 for w in ordered if w > author_wer)
    better = sum(1 for w in ordered if w < author_wer)
    total = len(ordered)
    return worse, total, (better / total * 100.0) if total else float("nan")


def _fmt(value: float, places: int = 1) -> str:
    return "--" if value != value else f"{value * 100:.{places}f}"


def _table(
    buckets: dict[str, Scored], author: Scored | None, condition: str, prompted_gap: str
) -> str:
    lines = [
        f"### Table 16: ASR speaker sensitivity (Exp-0) --- {condition}",
        "",
        "| Accent bucket | n | words | WER % | 95% CI | S / D / I |",
        "| :--- | ---: | ---: | ---: | :--- | :--- |",
    ]
    for scored in sorted(buckets.values(), key=lambda s: s.wer):
        low, high = scored.ci(_bucket_seed(scored.bucket))
        interval = "n too small" if low != low else f"[{_fmt(low)}, {_fmt(high)}]"
        lines.append(
            f"| {scored.bucket} | {scored.n} | {scored.total_words} | {_fmt(scored.wer)} "
            f"| {interval} | {scored.sub} / {scored.dele} / {scored.ins} |"
        )

    if author is not None:
        low, high = author.ci(_bucket_seed(author.bucket))
        interval = "n too small" if low != low else f"[{_fmt(low)}, {_fmt(high)}]"
        worse, total, pct = position(author.wer, [s.wer for s in buckets.values()])
        lines += [
            f"| **{author.bucket}** | **{author.n}** | **{author.total_words}** "
            f"| **{_fmt(author.wer)}** | **{interval}** "
            f"| **{author.sub} / {author.dele} / {author.ins}** |",
            "",
            f"The author's WER is lower than {worse} of the {total} accent buckets "
            f"({_ordinal(pct)} percentile of the bucket distribution). "
            "The comparison is indicative, not matched: the author read drone commands "
            "and the Common Voice speakers read general English, so the two figures are "
            "over different text. No pass/fail is claimed --- NFR-11 asks for a position.",
            "",
            prompted_gap,
        ]
    return "\n".join(lines) + "\n"


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", type=Path, default=CSV_OUT)
    parser.add_argument("--table", type=Path, default=TABLE_OUT)
    args = parser.parse_args(argv)

    prompted = _read(PROMPTED)
    unprompted = _read(UNPROMPTED)
    author = _read(AUTHOR)
    author_unprompted = _read(AUTHOR_UNPROMPTED)

    if not prompted and not unprompted:
        raise SystemExit("no transcripts -- run eval/exp0_transcribe.py first")

    matched = unprompted or prompted
    condition = "matched condition, no domain prompt" if unprompted else "domain prompt"
    buckets = score(matched)
    author_rows = author_unprompted or author
    author_label = author_rows[0]["bucket"] if author_rows else "Author"
    author_matched = pooled(author_rows, author_label)
    author_scored = author_matched if author_matched.n else None

    # The prompt's effect on each corpus, measured rather than asserted.
    gap = ""
    if prompted and unprompted:
        with_prompt, without = pooled(prompted).wer, pooled(unprompted).wer
        delta = (with_prompt - without) * 100
        gap = (
            f"Domain prompt on Common Voice: {_fmt(without)} % -> {_fmt(with_prompt)} % "
            f"({delta:+.1f} pp). "
        )
    if author and author_unprompted:
        with_prompt, without = pooled(author).wer, pooled(author_unprompted).wer
        delta = (with_prompt - without) * 100
        gap += (
            f"Domain prompt on the author's commands: {_fmt(without)} % -> "
            f"{_fmt(with_prompt)} % ({delta:+.1f} pp). "
            "The deployed configuration keeps the prompt; Table 16 positions the author "
            "without it, because only the unprompted pass puts both speakers under the "
            "same condition."
        )

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    with args.csv.open("w", newline="", encoding="utf-8") as handle:
        # Explicit LF: csv defaults to CRLF, which makes every row of a
        # script-generated results file show as changed on a Linux checkout.
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            ["condition", "bucket", "n", "ref_words", "wer", "ci_low", "ci_high",
             "sub", "del", "ins"]
        )
        for name, rows in (("prompted", prompted), ("unprompted", unprompted),
                           ("author_prompted", author), ("author_unprompted", author_unprompted)):
            if not rows:
                continue
            for scored in sorted(score(rows).values(), key=lambda s: s.bucket):
                low, high = scored.ci(_bucket_seed(scored.bucket))
                writer.writerow(
                    [name, scored.bucket, scored.n, scored.total_words,
                     f"{scored.wer:.6f}", f"{low:.6f}", f"{high:.6f}",
                     scored.sub, scored.dele, scored.ins]
                )

    table = _table(buckets, author_scored, condition, gap)
    args.table.write_text(table, encoding="utf-8")

    print(table)
    print(f"wrote {args.csv}")
    print(f"wrote {args.table}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
