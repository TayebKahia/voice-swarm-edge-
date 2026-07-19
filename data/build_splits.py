#!/usr/bin/env python3
"""Assemble `train.jsonl` / `val.jsonl` / `test_synth.jsonl` --- the two guards live here.

Inputs: `raw_pairs.jsonl` (Session 02A, one row per label with its split already
assigned by template family) and `roundtrip.jsonl` (the ASR round-trip audit trail).
Output: the three split files in the `§7.4` record format, plus
`roundtrip_rejects.jsonl` --- every row the guards acted on, for the one-time
eyeball pass `02_dataset_plan.md` §4 asks for.

**Guard (i) --- de-duplication.** "Round-tripping often returns the clean string,
and near-duplicates inflate your effective epoch count." Under substitution
(`composition.py`) an identity round-trip is harmless on its own --- the row simply
stays clean --- but two *different* rows can collapse onto the same transcript once
the recogniser has had its say. When they carry the same target that is a duplicate
and one is dropped; when they carry different targets it is worse than a duplicate,
because the model is being shown one input with two answers, and the later row is
reverted to its clean form rather than dropped, so the label survives.

**Guard (ii) --- destroyed utterances.** "If a round-trip destroys the utterance
beyond human recognition, relabel it `unknown` rather than keeping a corrupt ->
command pair." Automated on character similarity against the clean form; below
`DESTROYED_SIMILARITY` the row keeps its degraded transcript and its target becomes
`{"intent":"unknown"}`. Relabelling rather than dropping is deliberate: a transcript
too damaged to read *should* produce `unknown`, so these rows are training signal
for the safe-failure behaviour NFR-9 measures, not waste.

`val` and `test_synth` pass through clean and untouched.

Usage:
    python data/build_splits.py
    python data/build_splits.py --report-only     # print the composition, write nothing
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict, deque
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable, Sequence

if __package__ in (None, ""):  # `python data/build_splits.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.composition import COMPOSITION, DEFAULT_SEED, assign_variants, needs_roundtrip
from data.numwords import words_to_digits
from data.perturb import perturb

DATA_DIR = Path(__file__).resolve().parent
RAW_PAIRS = DATA_DIR / "raw_pairs.jsonl"
ROUNDTRIP = DATA_DIR / "roundtrip.jsonl"
REJECTS = DATA_DIR / "roundtrip_rejects.jsonl"
CARD_PATH = DATA_DIR / "dataset_card.md"
CARD_BEGIN = "<!-- composition:begin -->"
CARD_END = "<!-- composition:end -->"
SPLIT_FILES = {
    "train": DATA_DIR / "train.jsonl",
    "val": DATA_DIR / "val.jsonl",
    "test_synth": DATA_DIR / "test_synth.jsonl",
}

UNKNOWN_TARGET = '{"intent":"unknown"}'

#: Character-similarity floor, below which a round-trip counts as having destroyed
#: the utterance. 0.55 sits well clear of the ordinary degradations --- "form a
#: circle" -> "4m a circle" scores around 0.8 and is a transcript a person still
#: reads correctly --- while catching the cases where whisper returned a fragment,
#: a subtitle artefact, or nothing at all.
DESTROYED_SIMILARITY = 0.55

#: The `§7.4` key order. Written explicitly so the files are diffable and so a new
#: field cannot silently appear in the middle of the record.
RECORD_KEYS = (
    "id",
    "template_family",
    "split",
    "variant",
    "transcript",
    "target",
    "gold_intent",
    "audio_path",
    "snr_db",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )


def normalise(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace --- for comparison only.

    Matches `check_leakage.normalize_transcript`, so a pair this file calls
    identical is a pair the Gate 2 check also calls identical.
    """
    text = re.sub(r"[^\w\s]", "", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def similarity(a: str, b: str) -> float:
    """Character-level similarity of two transcripts, in [0, 1].

    Measured twice --- as written, and with spelled-out numbers rewritten as digits
    --- and the better score wins. Whisper emits "128.4" where the speaker said "one
    hundred and twenty-eight point four", and on the raw strings that *correct*
    transcription scores 0.54: below the destroyed threshold, so guard (ii) would
    relabel a perfectly readable command `unknown` and teach the model to refuse it.
    Fifteen rows in the first build were exactly that case.

    Taking the maximum rather than only the digit-normalised score keeps the guard
    honest in the other direction: a transcript that `numwords` cannot parse is
    still compared on its own terms rather than scored against a mangled rewrite.
    """
    plain = SequenceMatcher(None, normalise(a), normalise(b)).ratio()
    numeric = SequenceMatcher(
        None, normalise(words_to_digits(a)), normalise(words_to_digits(b))
    ).ratio()
    return max(plain, numeric)


def to_record(row: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    """Project a raw row onto the `§7.4` record, carrying 02A's provenance along.

    Session 02A wrote the *generation* variant (`paraphrase_2`, `hard_negative`,
    `authored_unknown`) into `variant`. `§7.4` reserves that key for the
    *augmentation* variant (`clean`, `asr_10db`, ...), so generation provenance
    moves to `source_variant` and nothing is lost.
    """
    record = {
        "id": row["id"],
        "template_family": row.get("template_family"),
        "split": row.get("split"),
        "variant": "clean",
        "transcript": row["transcript"],
        "target": row["target"],
        "gold_intent": row["gold_intent"],
        "audio_path": None,
        "snr_db": None,
    }
    record.update({k: v for k, v in overrides.items() if k in RECORD_KEYS})

    extras = {"source_variant": row.get("variant")}
    for key in ("hard_negative", "contrast_group"):
        if key in row:
            extras[key] = row[key]
    extras.update({k: v for k, v in overrides.items() if k not in RECORD_KEYS})
    return {**record, **{k: v for k, v in extras.items() if v is not None}}


def apply_augmentation(
    train_rows: Sequence[dict[str, Any]],
    roundtrip: Sequence[dict[str, Any]],
    *,
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter]:
    """Substitute each train row's surface form per its assigned variant.

    Returns `(records, rejects, actions)`. `actions` counts what the guards did, so
    the caller can report realised composition rather than the intended one.
    """
    assignment = assign_variants(train_rows, seed=seed)
    by_id = {record["id"]: record for record in roundtrip}
    actions: Counter = Counter()
    rejects: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []

    for row in train_rows:
        item_id = row["id"]
        variant = assignment[item_id]

        if variant == "clean":
            records.append(to_record(row))
            actions["clean"] += 1
            continue

        if variant == "perturb":
            text, operations = perturb(row["transcript"], item_id, seed)
            if text == row["transcript"]:
                # Nothing in this sentence was perturbable --- no article, no
                # homophone, no number, no punctuation. Say so rather than counting
                # it toward the 5%. The comparison is on the raw string, not the
                # normalised one: stripping punctuation and re-casing *is* the
                # perturbation §4 asks for ("Whisper's output style"), and
                # `normalise` erases exactly those two changes.
                records.append(to_record(row))
                actions["perturb_noop_to_clean"] += 1
                continue
            records.append(
                to_record(row, variant="perturb", transcript=text, perturb_ops=operations)
            )
            actions["perturb"] += 1
            continue

        trip = by_id.get(item_id)
        if trip is None or not trip.get("asr_ok") or not trip.get("asr_transcript", "").strip():
            # No transcript came back. Falling through to clean keeps the label and
            # is reported; silently dropping the row would shrink the split without
            # anything saying so.
            records.append(to_record(row))
            actions["asr_missing_to_clean"] += 1
            rejects.append(
                {
                    "id": item_id,
                    "reason": "asr_missing",
                    "variant": variant,
                    "clean": row["transcript"],
                    "asr": (trip or {}).get("asr_transcript", ""),
                }
            )
            continue

        asr = trip["asr_transcript"]
        score = similarity(row["transcript"], asr)

        identical = normalise(asr) == normalise(row["transcript"])
        if identical:
            # §4 warns that "round-tripping often returns the clean string". It
            # does --- about a quarter of the time at these levels. The row keeps
            # its variant and SNR, because the provenance is true and the text is a
            # real sample from the recogniser's output distribution; re-rolling
            # until it degraded would keep only the utterances whisper fails on and
            # bias the corpus away from the distribution it exists to reproduce.
            # The flag is what lets the dataset card report text-distinctness
            # separately from provenance.
            actions["roundtrip_identical"] += 1

        if score < DESTROYED_SIMILARITY:
            records.append(
                to_record(
                    row,
                    variant=variant,
                    transcript=asr,
                    target=UNKNOWN_TARGET,
                    gold_intent="unknown",
                    snr_db=trip["snr_db"],
                    relabelled_from=row["gold_intent"],
                    asr_similarity=round(score, 4),
                )
            )
            actions["relabelled_unknown"] += 1
            rejects.append(
                {
                    "id": item_id,
                    "reason": "destroyed_relabelled_unknown",
                    "variant": variant,
                    "snr_db": trip["snr_db"],
                    "similarity": round(score, 4),
                    "clean": row["transcript"],
                    "asr": asr,
                    "was": row["gold_intent"],
                }
            )
            continue

        records.append(
            to_record(
                row,
                variant=variant,
                transcript=asr,
                snr_db=trip["snr_db"],
                asr_similarity=round(score, 4),
                roundtrip_identical=identical or None,
            )
        )
        actions[variant] += 1

    return records, rejects, actions


def deduplicate(
    records: list[dict[str, Any]], raw_by_id: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Counter]:
    """Guard (i). Collapse identical transcripts; on a label conflict, revert.

    Which row reverts matters. If a round-trip transcript lands on some *other*
    row's clean text --- "land the swarm" heard as "land", which is already a row
    --- then reverting whichever arrived second would sometimes discard the clean
    row and keep the degraded one. The augmented member of the pair always gives
    way, so the corpus never loses an authored surface form to an ASR collision.

    Reverting can collide again, so reverted rows go back through the queue. It
    terminates: a reverted row is clean, and a clean row is never reverted.
    """
    queue = deque(records)
    kept: list[dict[str, Any]] = []
    index: dict[str, int] = {}  # normalised transcript -> position in `kept`
    rejects: list[dict[str, Any]] = []
    actions: Counter = Counter()

    def revert(record: dict[str, Any]) -> dict[str, Any] | None:
        raw = raw_by_id.get(record["id"])
        return to_record(raw) if raw is not None else None

    while queue:
        record = queue.popleft()
        key = normalise(record["transcript"])
        position = index.get(key)

        if position is None:
            index[key] = len(kept)
            kept.append(record)
            continue

        held = kept[position]

        if held["target"] == record["target"]:
            actions["dropped_duplicate"] += 1
            rejects.append(
                {
                    "id": record["id"],
                    "reason": "duplicate_transcript",
                    "duplicate_of": held["id"],
                    "transcript": record["transcript"],
                }
            )
            continue

        # Same text, two different answers. One of them has to stop claiming it.
        rejects.append(
            {
                "id": record["id"],
                "reason": "label_conflict",
                "conflicts_with": held["id"],
                "collided_on": record["transcript"],
                "target": record["target"],
                "other_target": held["target"],
            }
        )

        if record["variant"] != "clean" and (reverted := revert(record)) is not None:
            queue.appendleft(reverted)
            actions["reverted_conflict_to_clean"] += 1
        elif held["variant"] != "clean" and (reverted := revert(held)) is not None:
            kept[position] = record
            queue.appendleft(reverted)
            actions["reverted_conflict_to_clean"] += 1
        else:
            # Both are clean, so 02A's global transcript uniqueness has been
            # violated upstream. Drop and report rather than pick a winner.
            actions["dropped_conflict"] += 1
            rejects[-1]["reason"] = "label_conflict_unresolvable_dropped"

    return kept, rejects, actions


def realised_composition(records: Sequence[dict[str, Any]]) -> Counter:
    return Counter(record["variant"] for record in records)


def card_table(records: Sequence[dict[str, Any]], actions: Counter, splits: dict[str, int]) -> str:
    """The §6a composition block, rendered from what was actually written.

    Intended *and* realised, side by side. The gap is guard activity --- rows the
    recogniser handed back unchanged, transcripts it destroyed, collisions --- and
    reporting only the intended figures would describe a corpus that does not exist.
    """
    realised = realised_composition(records)
    total = len(records)
    # Counted on what was written, not on what `apply_augmentation` saw: a row it
    # flagged can still have been removed by guard (i), and two numbers a line
    # apart that differ by one read as an error even when both are right.
    identical = sum(1 for r in records if r.get("roundtrip_identical"))
    lines = [
        CARD_BEGIN,
        "",
        "| Variant | Intended | Realised | Rows |",
        "|---|---:|---:|---:|",
    ]
    for name, share in COMPOSITION.items():
        lines.append(
            f"| `{name}` | {share:.0%} | {realised.get(name, 0) / max(total, 1):.1%} "
            f"| {realised.get(name, 0)} |"
        )
    lines += [
        f"| **total** | 100% | 100% | **{total}** |",
        "",
        f"Of the {identical} round-trip rows "
        f"the recogniser returned unchanged, none is re-rolled: an identity round-trip is a "
        f"true sample from the ASR output distribution, and re-drawing until it degraded would "
        f"keep only the utterances whisper fails on. Counting text rather than provenance, the "
        f"corpus is "
        f"{(realised.get('clean', 0) + identical) / max(total, 1):.1%} clean.",
        "",
        "Guard and fall-back activity:",
        "",
        "| Action | Rows | Meaning |",
        "|---|---:|---|",
    ]
    for name, note in (
        ("roundtrip_identical", "recogniser returned the clean wording; row keeps its variant"),
        ("relabelled_unknown", "guard (ii): transcript destroyed, target -> `unknown`"),
        ("perturb_noop_to_clean", "nothing in the sentence was perturbable"),
        ("asr_missing_to_clean", "no transcript came back; fell back to clean"),
        ("dropped_duplicate", "guard (i): same text, same target"),
        ("reverted_conflict_to_clean", "guard (i): same text, different target"),
        ("dropped_conflict", "guard (i): unresolvable, both clean"),
    ):
        count = identical if name == "roundtrip_identical" else actions.get(name, 0)
        lines.append(f"| `{name}` | {count} | {note} |")
    lines += [
        "",
        "Split sizes as written: "
        + ", ".join(f"`{k}` {v}" for k, v in splits.items())
        + ".",
        "",
        CARD_END,
    ]
    return "\n".join(lines)


def update_card(block: str, card_path: Path = CARD_PATH) -> bool:
    if not card_path.is_file():
        return False
    text = card_path.read_text(encoding="utf-8")
    start, end = text.find(CARD_BEGIN), text.find(CARD_END)
    if start < 0 or end < 0:
        return False
    card_path.write_text(text[:start] + block + text[end + len(CARD_END) :], encoding="utf-8")
    return True


def report(title: str, counts: Counter, total: int) -> None:
    print(f"\n{title}")
    for name, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"    {name:<32} {count:>5}  {count / max(total, 1):6.1%}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--raw", type=Path, default=RAW_PAIRS)
    parser.add_argument("--roundtrip", type=Path, default=ROUNDTRIP)
    parser.add_argument("--report-only", action="store_true", help="print, write nothing")
    args = parser.parse_args(argv)

    raw = read_jsonl(args.raw)
    if not raw:
        print(f"[-] {args.raw} is empty or missing")
        return 1
    roundtrip = read_jsonl(args.roundtrip)

    by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in raw:
        by_split[row.get("split", "?")].append(row)

    train_rows = by_split.get("train", [])
    expected_trips = sum(1 for v in assign_variants(train_rows, seed=args.seed).values() if needs_roundtrip(v))
    print(f"[*] raw_pairs: {len(raw)} rows " + ", ".join(f"{k}={len(v)}" for k, v in sorted(by_split.items())))
    print(f"[*] roundtrip.jsonl: {len(roundtrip)} records (plan expects {expected_trips})")
    if len(roundtrip) < expected_trips:
        print("    [!] short of the plan --- run `python data/roundtrip.py` first; "
              "missing rows fall back to clean and are listed in roundtrip_rejects.jsonl")

    records, rejects, actions = apply_augmentation(train_rows, roundtrip, seed=args.seed)
    raw_by_id = {row["id"]: row for row in train_rows}
    records, dedup_rejects, dedup_actions = deduplicate(records, raw_by_id)
    rejects += dedup_rejects
    actions += dedup_actions

    splits = {"train": records}
    for name in ("val", "test_synth"):
        splits[name] = [to_record(row) for row in by_split.get(name, [])]

    report("Intended composition (02_dataset_plan.md §4)",
           Counter({k: round(v * len(train_rows)) for k, v in COMPOSITION.items()}), len(train_rows))
    report("Realised composition (train.jsonl)", realised_composition(records), len(records))
    report("Guard actions", actions, len(train_rows))

    print("\nSplit sizes")
    for name, rows in splits.items():
        print(f"    {name:<32} {len(rows):>5}")

    if args.report_only:
        print("\n[*] --report-only: nothing written")
        return 0

    for name, rows in splits.items():
        write_jsonl(SPLIT_FILES[name], rows)
        print(f"[+] wrote {SPLIT_FILES[name].name} ({len(rows)} rows)")
    write_jsonl(REJECTS, rejects)
    print(f"[+] wrote {REJECTS.name} ({len(rejects)} rows) --- eyeball these once")

    block = card_table(records, actions, {k: len(v) for k, v in splits.items()})
    if update_card(block):
        print(f"[+] dataset_card.md §6a rewritten from what was written")
    else:
        print(f"[!] dataset_card.md has no {CARD_BEGIN} block; §6a not updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
