#!/usr/bin/env python3
"""Intra-annotator test--retest --- the project's only annotation-quality claim.

`prd.md` §9.3: agreement is measured on **50 golden-set utterances** by
**test--retest with a single annotator**. The author labels the 50 against the
schema, **seals** that pass, then relabels the same items **cold** after a gap,
and the two passes are compared. `IMPLEMENTATION_ROADMAP.md` §0.2 conflict 2
rejects the inter-annotator Cohen's kappa that `02_dataset_plan.md` proposes: it
needs a second person the project does not have, and it measures a stronger claim
the PRD deliberately never makes.

**Pass 1 is the authoritative gold label.** The dataset freezes at Gate 5, so
pass 2 measures the *stability* of the schema's application, not a revision of it.
A schema gap found by pass 2 is future work; it does not trigger regeneration.

What makes the second pass a measurement rather than a recital is that the
annotator has forgotten the first. Three things protect that, and the tool
enforces all three because a human cannot enforce them on themselves:

1. **The gap.** Wall-clock time between the seal and pass 2. It is recorded from
   the sealed file's own timestamp, so the figure reported in the thesis is the
   interval that actually elapsed and not the one that was planned.
2. **A different presentation order.** Order is a strong recall cue and costs
   nothing to remove; pass 2 is shuffled under a different seed.
3. **No sight of anything already decided.** Pass 2 never displays pass 1, and
   neither pass displays `test_golden.jsonl`'s generated `target` --- these rows
   were built label-first, so showing the target would turn annotation into
   proof-reading.

Entry is free-form JSON validated against the frozen schema. It is deliberately
not a guided intent-then-slots form: a form resolves the ambiguities the
measurement exists to find, and would inflate agreement by construction.

Usage:
    python data/annotate.py --pass 1          # label, then seal
    python data/annotate.py --seal            # seal pass 1 (also offered on exit)
    python data/annotate.py --pass 2          # cold relabel; refuses before the seal
    python data/annotate.py --compare         # the §7 table for the dataset card
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):  # `python data/annotate.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schema.canon import canon
from schema.schema import INTENTS
from schema.validate import ValidationError, validate

DATA_DIR = Path(__file__).resolve().parent
ANNOT_DIR = DATA_DIR / "annot"
GOLDEN_PATH = DATA_DIR / "test_golden.jsonl"
CARD_PATH = DATA_DIR / "dataset_card.md"
CARD_BEGIN = "<!-- annotation:begin -->"
CARD_END = "<!-- annotation:end -->"

SUBSET_SIZE = 50
DEFAULT_SEED = 42

PASS1_PATH = ANNOT_DIR / "annot_pass1.jsonl"
PASS2_PATH = ANNOT_DIR / "annot_pass2.jsonl"
SEAL_PATH = ANNOT_DIR / "annot_pass1.seal.json"
SUBSET_PATH = ANNOT_DIR / "annot_subset.txt"


def _stable_seed(*parts: object) -> int:
    blob = "\x1f".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(blob).digest()[:8], "big")


def _display(path: Path) -> str:
    """Repo-relative when it can be, absolute otherwise (e.g. a pytest tmp dir)."""
    try:
        return str(path.resolve().relative_to(DATA_DIR.parent))
    except ValueError:
        return str(path)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_golden(path: Path = GOLDEN_PATH) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def choose_subset(rows: list[dict], size: int = SUBSET_SIZE, seed: int = DEFAULT_SEED) -> list[str]:
    """Stratify by intent, then fill by stable hash.

    A uniform sample of 50 from 200 would, on the golden set's intent mix, be
    expected to contain fewer than two `abort` rows and could easily contain
    none. `abort` is the one intent whose misapplication is a safety matter, so
    it is the one the agreement figure most needs to cover.
    """
    by_intent: dict[str, list[str]] = {}
    for row in rows:
        by_intent.setdefault(row["gold_intent"], []).append(row["id"])
    for ids in by_intent.values():
        ids.sort(key=lambda i: _stable_seed(seed, "annot-subset", i))

    chosen: list[str] = []
    intents = sorted(by_intent)
    position = 0
    while len(chosen) < size and any(len(by_intent[i]) > position for i in intents):
        for intent in intents:
            if len(chosen) >= size:
                break
            if len(by_intent[intent]) > position:
                chosen.append(by_intent[intent][position])
        position += 1
    if len(chosen) < size:
        raise SystemExit(f"only {len(chosen)} golden rows available; need {size}")
    return sorted(chosen[:size])


def presentation_order(ids: Sequence[str], which: int, seed: int = DEFAULT_SEED) -> list[str]:
    """Pass 1 and pass 2 see the same items in different orders."""
    return sorted(ids, key=lambda i: _stable_seed(seed, f"annot-order-{which}", i))


# --- the labelling loop ----------------------------------------------------


HELP = f"""
  Write the command as single-line JSON. Null fields are omitted (roadmap §2.2).
  Intents: {', '.join(INTENTS)}
  Examples: {{"intent":"move","dir":"north","dist":10.0}}
            {{"intent":"formation","shape":"circle","radius":5.0}}
            {{"intent":"hover"}}   {{"intent":"unknown"}}
  Commands: [?] this help · [s] skip (leave unlabelled) · [q] save and quit
"""


def label_interactively(
    items: list[tuple[str, str]], existing: dict[str, dict], which: int
) -> tuple[dict[str, dict], bool]:
    """Returns the labels and whether the annotator worked to the end."""
    labels = dict(existing)
    print(HELP)
    pending = [(i, t) for i, t in items if i not in labels]
    print(f"{len(pending)} to label, {len(labels)} already done.\n")

    for position, (item_id, transcript) in enumerate(pending, start=1):
        while True:
            print("=" * 72)
            print(f"[{position}/{len(pending)}]")
            print()
            print(f"    {transcript}")
            print()
            raw = input("  label> ").strip()
            if raw == "?":
                print(HELP)
                continue
            if raw.lower() == "q":
                return labels, False
            if raw.lower() == "s":
                break
            try:
                command = validate(raw, fallback=False)
            except (ValidationError, ValueError, json.JSONDecodeError) as exc:
                print(f"  rejected: {exc}")
                continue
            labels[item_id] = {
                "id": item_id,
                "label": canon(command),
                "raw": raw,
                "at": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            }
            print(f"  -> {labels[item_id]['label']}")
            break
    return labels, True


def write_pass(path: Path, labels: dict[str, dict], order: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(labels[i], ensure_ascii=False) for i in order if i in labels]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def read_pass(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    return {
        record["id"]: record
        for record in (json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip())
    }


# --- the seal --------------------------------------------------------------


def seal(pass1_path: Path = PASS1_PATH, seal_path: Path = SEAL_PATH) -> int:
    if not pass1_path.is_file():
        raise SystemExit(f"{pass1_path} does not exist -- run --pass 1 first")
    labels = read_pass(pass1_path)
    if len(labels) != SUBSET_SIZE:
        raise SystemExit(
            f"{pass1_path.name} holds {len(labels)} labels, not {SUBSET_SIZE}. "
            "Seal a complete pass or the agreement figure has no denominator."
        )
    if seal_path.is_file():
        existing = json.loads(seal_path.read_text(encoding="utf-8"))
        print(f"already sealed {existing['sealed']} (sha256 {existing['sha256'][:12]}...)")
        if existing["sha256"] != sha256_of(pass1_path):
            print(
                "  WARNING: the file has changed since it was sealed. Pass 1 is the\n"
                "  authoritative gold label and must not be reopened -- restore it from\n"
                "  git, or record the edit explicitly in STATE.md and the Limitations."
            )
            return 1
        return 0

    record = {
        "sealed": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "sha256": sha256_of(pass1_path),
        "items": len(labels),
        "file": _display(pass1_path),
    }
    seal_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"sealed {len(labels)} labels at {record['sealed']}")
    print(f"sha256 {record['sha256']}")
    print("\nDo not reopen pass 1. Record the seal date in STATE.md, and schedule pass 2.")
    return 0


# --- comparison ------------------------------------------------------------


def slot_pairs(label: str) -> set[str]:
    """The `(key, canonical value)` pairs of a canonical command, intent excluded.

    `IMPLEMENTATION_ROADMAP.md` §2.7 defines Slot-F1 over that multiset
    "regardless of intent correctness", so intent is reported on its own line and
    does not also inflate the slot figure. Values come from `canon`, so 4 and 4.0
    are already the same string before they are compared.
    """
    fields = json.loads(label)
    return {f"{key}={json.dumps(value, sort_keys=True)}" for key, value in fields.items()
            if key != "intent"}


def compare(pass1: dict[str, dict], pass2: dict[str, dict]) -> dict:
    shared = sorted(set(pass1) & set(pass2))
    if not shared:
        raise SystemExit("the two passes share no items")

    exact = 0
    intent_agree = 0
    slot_tp = slot_p1 = slot_p2 = 0
    disagreements: list[dict] = []

    for item_id in shared:
        a, b = pass1[item_id]["label"], pass2[item_id]["label"]
        intent_a = json.loads(pass1[item_id]["raw"]).get("intent")
        intent_b = json.loads(pass2[item_id]["raw"]).get("intent")
        if a == b:
            exact += 1
        else:
            disagreements.append(
                {"id": item_id, "pass1": a, "pass2": b, "intent_differs": intent_a != intent_b}
            )
        intent_agree += int(intent_a == intent_b)

        fields_a, fields_b = slot_pairs(a), slot_pairs(b)
        slot_tp += len(fields_a & fields_b)
        slot_p1 += len(fields_a)
        slot_p2 += len(fields_b)

    precision = slot_tp / slot_p2 if slot_p2 else 0.0
    recall = slot_tp / slot_p1 if slot_p1 else 0.0
    slot_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "n": len(shared),
        "exact_agreement": round(exact / len(shared), 4),
        "intent_agreement": round(intent_agree / len(shared), 4),
        "slot_f1": round(slot_f1, 4),
        "disagreements": disagreements,
    }


def gap_days(seal_path: Path, pass2_path: Path) -> float | None:
    if not (seal_path.is_file() and pass2_path.is_file()):
        return None
    sealed = _dt.datetime.fromisoformat(json.loads(seal_path.read_text())["sealed"])
    records = read_pass(pass2_path)
    if not records:
        return None
    latest = max(_dt.datetime.fromisoformat(r["at"]) for r in records.values())
    return round((latest - sealed).total_seconds() / 86400, 2)


def card_block(result: dict, gap: float | None) -> str:
    """The §7 block. Reports the disagreements and withholds the rate.

    `prd.md` §9.3: at a two-day interval a matching pair of labels is as easily
    recall as schema clarity, so an agreement percentage would measure memory. The
    rate is *not* rendered here --- it stays in `--compare`'s stdout as a working
    number and never reaches the card, because the card is what gets read.

    What survives the short interval is the asymmetry: recall can only push the
    two passes together, never apart. So an item labelled two different ways is
    evidence the schema admits two readings regardless of the gap, and those items
    are the output.
    """
    disagreements = result["disagreements"]
    interval = f"{gap:.1f} days" if gap is not None else "TBD — pass 2 not recorded"
    lines = [
        CARD_BEGIN,
        "",
        "| Field | Value |",
        "|---|---|",
        "| Pass 1 | `annot/annot_pass1.jsonl` — sealed under SHA-256, authoritative |",
        "| Pass 2 | `annot/annot_pass2.jsonl` — reshuffled, blind to pass 1 |",
        f"| Interval | {interval} |",
        f"| Items | {result['n']} |",
        "| Agreement rate | **not reported** — see below |",
        f"| Schema ambiguities found | {len(disagreements)} |",
        "",
        "**No agreement rate is reported.** At this interval a matching pair of",
        "labels is as easily recall as schema clarity, so a percentage would measure",
        "memory; it is withheld rather than caveated.",
        "",
        "What the comparison does support is one-directional: **recall can only push",
        "the two passes toward agreement, never apart.** An item labelled two",
        "different ways is therefore evidence that the schema admits two readings, at",
        "any interval.",
        "",
    ]
    if disagreements:
        lines += [
            f"The {len(disagreements)} item(s) below are that evidence. The count is a",
            "**lower bound**: recall will have masked ambiguities a cold reader would",
            "have hit.",
            "",
            "| id | pass 1 | pass 2 | intent moved |",
            "|---|---|---|---|",
        ]
        for d in disagreements:
            lines.append(
                f"| {d['id']} | `{d['pass1']}` | `{d['pass2']}` | "
                f"{'yes' if d['intent_differs'] else 'no'} |"
            )
        lines.append("")
    else:
        lines += [
            "**No disagreement appeared.** This is not evidence that the schema is",
            "unambiguous --- only that this interval was too short to find one. Stated",
            "explicitly so the null result cannot be read as a positive one.",
            "",
        ]
    lines.append(CARD_END)
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


# --- CLI -------------------------------------------------------------------


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pass", dest="which", type=int, choices=(1, 2))
    parser.add_argument("--seal", action="store_true")
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args(argv)

    ANNOT_DIR.mkdir(parents=True, exist_ok=True)

    if args.seal:
        return seal()

    if args.compare:
        pass1, pass2 = read_pass(PASS1_PATH), read_pass(PASS2_PATH)
        if not pass1 or not pass2:
            raise SystemExit("both passes must exist before they can be compared")
        result = compare(pass1, pass2)
        gap = gap_days(SEAL_PATH, PASS2_PATH)
        # The rates stay here, as working numbers. `card_block` does not render
        # them: at this interval they measure recall, and the card is what a
        # reader sees. See `prd.md` §9.3.
        print(json.dumps({k: v for k, v in result.items() if k != "disagreements"}, indent=2))
        print("  (rates above are diagnostic only and are NOT reported -- prd.md §9.3)")
        print(f"gap: {gap} days" if gap is not None else "gap: unknown (no seal record)")
        print(f"\nschema ambiguities found: {len(result['disagreements'])}")
        for d in result["disagreements"]:
            print(f"  {d['id']}  {d['pass1']}   !=   {d['pass2']}")
        print("dataset card §7 rewritten" if update_card(card_block(result, gap)) else
              f"[!] {CARD_PATH.name} has no {CARD_BEGIN} block; §7 not updated")
        return 0

    if args.which is None:
        parser.error("choose --pass 1, --pass 2, --seal or --compare")

    rows = read_golden()
    by_id = {row["id"]: row for row in rows}

    if SUBSET_PATH.is_file():
        subset = [l.strip() for l in SUBSET_PATH.read_text().splitlines() if l.strip()]
    else:
        subset = choose_subset(rows, seed=args.seed)
        SUBSET_PATH.write_text("\n".join(subset) + "\n", encoding="utf-8")
        print(f"subset of {len(subset)} chosen, stratified by intent -> {SUBSET_PATH.name}")

    if args.which == 2:
        if not SEAL_PATH.is_file():
            raise SystemExit(
                "pass 1 is not sealed. Pass 2 before the seal is not a cold relabel and\n"
                "the agreement figure would not mean what §9.3 says it means."
            )
        sealed = json.loads(SEAL_PATH.read_text())["sealed"]
        elapsed = (_dt.datetime.now().astimezone() - _dt.datetime.fromisoformat(sealed)).days
        print(f"pass 1 sealed {sealed} -- {elapsed} days ago")
        if elapsed < 1:
            print(
                "  Less than a day. This measures recall, not schema stability.\n"
                "  Run it on the scheduled day instead."
            )
            if input("  type 'override' to continue: ").strip() != "override":
                return 2

    target = PASS1_PATH if args.which == 1 else PASS2_PATH
    order = presentation_order(subset, args.which, args.seed)
    items = [(i, by_id[i]["transcript"]) for i in order]

    print(f"\nAnnotation pass {args.which}: {len(items)} items, presentation order {args.which}.")
    print("You are labelling from the transcript against the frozen schema.")
    if args.which == 2:
        print("Pass 1 is not shown and must not be opened.\n")

    labels, finished = label_interactively(items, read_pass(target), args.which)
    write_pass(target, labels, order)
    print(f"\n{len(labels)} / {len(items)} labelled -> {target}")

    if args.which == 1 and finished and len(labels) == SUBSET_SIZE:
        print("\nPass 1 is complete. Sealing now starts the interval.")
        if input("seal? [y/N] ").strip().lower() == "y":
            return seal()
        print("Not sealed. Run `python data/annotate.py --seal` when ready.")
    return 0 if finished else 1


if __name__ == "__main__":
    raise SystemExit(run())
