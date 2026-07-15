#!/usr/bin/env python3
"""Label-first synthetic generation --- Session 02A, `02_dataset_plan.md` §3.1.

    python data/generate.py

Writes, deterministically under seed 42:

    data/raw_pairs.jsonl             2,400 rows, 20 per family x 120 families
    data/test_ood.jsonl                150 eval-only OOD rows (§3.4)
    data/test_golden.jsonl             200 held-out rows for the Exp-1 benchmark
    data/test_golden_transcripts.txt   the same 200 transcripts, for recording

## Why label-first, and what it buys

The label is constructed first --- intent, then a legal slot combination, then
values sampled inside the §2.4 physical envelope --- and only then is text
produced for it (`data/surface_forms.py`). Nothing in this pipeline can produce a
row whose label disagrees with its transcript, because the transcript is derived
*from* the label and the label is never revisited. There is no annotation step,
so there is no annotation error, and `run_all.sh` reproduces all four files
byte-for-byte from a clean clone.

The order also matters for a subtler reason. Text-first generation would let the
sampler drift toward whatever is easy to say --- round numbers, five drones,
"take off" --- and the resulting corpus would be unbalanced in ways no assertion
could detect after the fact. Sampling the label first makes coverage a property
of the *sampler*, which is checkable, and this module checks it: every slot
combination, every enum value, and every diversity axis is counted and printed,
and the run fails if one is empty.

## The 20-row family budget, and where it flexes

20 rows x 120 families = 2,400, and because the 96/12/12 family split is fixed in
`data/template_families.py` the corpus split falls out near 1,920/240/240 without
any per-row split decision. Within a family the 20 rows are 2 or 3 distinct
*value samples* x K=8 paraphrases (§3.1 asks for K=8), so a family teaches both
"this phrasing means this label" and "this label survives a change of numbers".

Authored rows --- hard negatives (`data/hard_negatives.py`) and in-corpus
`unknown` (`data/ood.py`) --- *consume* that budget rather than adding to it, so a
family with 6 hard negatives generates 14 rows and still totals 20.

**Two families exceed 20, deliberately.** F117 (lexical near-misses) collects the
`unknown` half of nearly every contrast group in §3.3: "circle around the tree",
"drop the payload", "hoover the floor", "the grid is down". Roughly 39 rows want
to be there, because a decisive-token group is only worth authoring if both sides
of the boundary are present, and the near-miss side is almost always `unknown`.
Capping the family at 20 would mean deleting about nineteen of the
highest-value-per-row utterances in the corpus (§3.3's own description) to
preserve a round total that this file chose in the first place. So the cap does
not apply to authored rows: a family holds `max(20, authored)`.

The cost is that the corpus is 2,4xx rows rather than exactly 2,400 and the split
is 80.2/9.9/9.9 rather than exactly 80/10/10 --- both families are `train`. The
run prints the real numbers; nothing rounds them up.

## The gate

FR-1: every generated label is accepted by `schema/cmd.gbnf`. Checked here on
every row as it is built, by `data/gbnf.py` executing the frozen grammar file
itself --- not a regex mirror of it (README:56, Trap 5). Three further checks run
alongside, because grammar-acceptance alone is weaker than it looks:

- `canon(validate(target, fallback=False)) == target`, so the label is already
  canonical *and* already inside the envelope. A row that needed clamping would
  train the model to emit out-of-range values that Layer 2 then silently corrects.
- no duplicate transcripts anywhere in the corpus, and no near-duplicate across a
  split boundary (Jaccard >= 0.85), which is the surface-form half of Gate 2.
- family/intent agreement, so a row cannot drift out of the family that
  determines its split.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

if __package__ in (None, ""):  # `python data/generate.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.check_leakage import (
    get_token_ngrams,
    jaccard_similarity,
    normalize_transcript,
)
from data.gbnf import Grammar, load_grammar
from data.hard_negatives import HARD_NEGATIVES, HardNegative
from data.ood import F120_GOLDEN_ROWS, IN_CORPUS_UNKNOWN, ood_rows
from data.surface_forms import (
    ADDRESSING_MODES,
    ELLIPSIS_INTENTS,
    NUMBER_FORMS,
    REGISTERS,
    Axes,
    realise,
    synonym_pool,
)
from data.template_families import FAMILIES, FAMILY_MAP, TemplateFamily
from schema.canon import canon
from schema.schema import DIRECTIONS, ENVELOPE, SHAPES, SWARM_SIZE
from schema.validate import validate

DATA_DIR = Path(__file__).parent
RAW_PAIRS_PATH = DATA_DIR / "raw_pairs.jsonl"
TEST_OOD_PATH = DATA_DIR / "test_ood.jsonl"
TEST_GOLDEN_PATH = DATA_DIR / "test_golden.jsonl"
GOLDEN_TRANSCRIPTS_PATH = DATA_DIR / "test_golden_transcripts.txt"

SEED = 42
ROWS_PER_FAMILY = 20
PARAPHRASES_K = 8          # §3.1: "K=8 distinct ways a human operator would say this"
GOLDEN_ROWS = 200
NEAR_DUPLICATE_JACCARD = 0.85

# `dist` and `alt` are not in the PRD's Table 6; ADR-0001 derives them from the
# envelope that is (|pos| <= 50 bounds a displacement, alt is an altitude).
DIST_RANGE = (0.0, 50.0)


# --- value sampling --------------------------------------------------------
#
# Every sampled value is a multiple of 0.1 inside the §2.4 range, because that is
# exactly what `cmd.gbnf`'s `num` rule can express and what `canon()` rounds to.
# Sampling on the grid rather than sampling continuously and rounding keeps the
# distribution uniform over representable values --- rounding would double-weight
# the two endpoints.


def _grid(low: float, high: float, rng: random.Random, *, decimals: int = 1) -> float:
    step = 10**-decimals
    steps = int(round((high - low) / step))
    return round(low + rng.randint(0, steps) * step, decimals)


def _sample_scalar(slot: str, rng: random.Random) -> float:
    """A value for `slot`, biased so that whole numbers are not rare.

    Operators say "five metres" far more often than "four point three", and axis
    2's word forms are more natural over whole numbers. 60% integers keeps both
    populations well represented instead of making decimals the default.
    """
    low, high = DIST_RANGE if slot == "dist" else ENVELOPE[slot]
    if rng.random() < 0.6:
        lo_i, hi_i = int(low + 0.999), int(high)
        if lo_i <= hi_i:
            return float(rng.randint(lo_i, hi_i))
    return _grid(low, high, rng)


def _sample_pos(rng: random.Random) -> list[float]:
    """A waypoint with |pos| <= 50 and z inside the altitude envelope.

    Rejection sampling on the norm: the envelope is a spherical cap, and drawing
    each axis independently would put a fifth of the samples outside it. z is
    drawn from the altitude range rather than symmetrically, because a waypoint
    below ground is not a command anyone gives.
    """
    z_low, z_high = ENVELOPE["z"]
    for _ in range(1000):
        x = _grid(-40.0, 40.0, rng)
        y = _grid(-40.0, 40.0, rng)
        z = _sample_scalar("z", rng)
        if x * x + y * y + z * z <= 50.0 * 50.0:
            return [x, y, round(z, 1)]
    raise RuntimeError("rejection sampling for pos failed; check ENVELOPE")


def _sample_ids(rng: random.Random, mode: str) -> list[int]:
    """A 0-indexed id list consistent with the addressing mode.

    Sorted and deduplicated here so the label is canonical before `canon()` ever
    sees it, and non-empty so it never means "all drones" by accident.
    """
    if mode == "single":
        return [rng.randrange(SWARM_SIZE)]
    if mode == "range":
        length = rng.randint(2, min(3, SWARM_SIZE))
        start = rng.randrange(0, SWARM_SIZE - length + 1)
        return list(range(start, start + length))
    size = rng.randint(2, min(3, SWARM_SIZE))
    return sorted(rng.sample(range(SWARM_SIZE), size))


# --- slot patterns ---------------------------------------------------------


@dataclass(frozen=True)
class Pattern:
    """A parsed `slot_pattern` from `data/template_families.py`."""

    shape: str | None
    direction: str | None
    slots: tuple[str, ...]      # radius / spacing / speed / z / alt / yaw / dist / pos
    wants_ids: bool


def parse_pattern(slot_pattern: str) -> Pattern:
    """Read a family's `slot_pattern` into something the sampler can execute.

    The patterns are the 01B family table's own notation: comma-separated slot
    names, with `shape:` and `dir:` carrying an enum value, `ids` meaning the row
    addresses a subset, and `none` meaning no slots at all.
    """
    shape = direction = None
    slots: list[str] = []
    wants_ids = False
    for token in slot_pattern.split(","):
        token = token.strip()
        if not token or token == "none":
            continue
        if token.startswith("shape:"):
            shape = token.split(":", 1)[1]
            if shape not in SHAPES:
                raise ValueError(f"unknown shape {shape!r} in {slot_pattern!r}")
        elif token.startswith("dir:"):
            direction = token.split(":", 1)[1]
            if direction not in DIRECTIONS:
                raise ValueError(f"unknown direction {direction!r} in {slot_pattern!r}")
        elif token == "ids":
            wants_ids = True
        else:
            slots.append(token)
    return Pattern(shape, direction, tuple(slots), wants_ids)


def build_gold(
    family: TemplateFamily,
    pattern: Pattern,
    rng: random.Random,
    addressing: str,
) -> dict[str, object]:
    """Construct one label. This is the *only* place a label is created.

    Key insertion order follows `schema.schema.KEY_ORDER` by construction ---
    intent, then the intent's own slots, then ids --- so `canon()` has nothing to
    reorder and the written bytes match what the model is trained to emit.
    """
    intent = family.intent
    gold: dict[str, object] = {"intent": intent}

    if pattern.shape is not None:
        gold["shape"] = pattern.shape
    if pattern.direction is not None:
        gold["dir"] = pattern.direction

    for slot in pattern.slots:
        if slot == "pos":
            gold["pos"] = _sample_pos(rng)
        else:
            gold[slot] = _sample_scalar(slot, rng)

    if pattern.wants_ids:
        if addressing not in ("single", "subset", "range"):
            raise ValueError(f"family {family.family_id} needs ids, got addressing {addressing!r}")
        gold["ids"] = _sample_ids(rng, addressing)

    return gold


def _addressing_choices(pattern: Pattern) -> tuple[str, ...]:
    """Which addressing modes this family can use.

    A family whose pattern carries `ids` must address a subset --- otherwise the
    label would claim `ids` the transcript never mentions, and the model would be
    trained to invent them. A family without `ids` must *not* name a drone, which
    is the collective-intent case spike S3 found zero-shot models fail (they emit
    `ids:[1]` for "swarm"); fine-tuning owns it, so the corpus has to be
    unambiguous about it.
    """
    if pattern.wants_ids:
        return ("single", "subset", "range")
    return ("implicit_all", "explicit_all")


def sample_axes(
    pattern: Pattern,
    intent: str,
    rng: random.Random,
    *,
    register: str | None = None,
    number_form: str | None = None,
    addressing: str | None = None,
    synonym: str | None = None,
) -> Axes:
    """Draw an axis assignment, with any axis pinned by the caller."""
    return Axes(
        register=register if register is not None else rng.choice(REGISTERS),
        number_form=number_form if number_form is not None else rng.choice(NUMBER_FORMS),
        addressing=addressing if addressing is not None else rng.choice(_addressing_choices(pattern)),
        synonym=synonym if synonym is not None else "",
        disfluency=rng.random() < 0.25,
        politeness=rng.random() < 0.30,
        ellipsis=intent in ELLIPSIS_INTENTS and rng.random() < 0.20,
    )


# --- rows ------------------------------------------------------------------


def _record(
    row_id: str,
    family: TemplateFamily,
    variant: str,
    transcript: str,
    gold: dict[str, object],
    axes: Axes | None,
    *,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    """One §7.4 training record.

    `audio_path` and `snr_db` are declared here and left null on purpose: §7.4
    fixes the record shape for the whole project, and Session 02B fills these two
    in when it renders and augments audio. Writing the keys now means 02B rewrites
    values rather than reshaping the file, and any consumer written against §7.4
    works today.
    """
    record: dict[str, object] = {
        "id": row_id,
        "template_family": family.family_id,
        "split": family.split,
        "variant": variant,
        "transcript": transcript,
        "target": canon(gold),
        "gold_intent": gold["intent"],
        "audio_path": None,
        "snr_db": None,
    }
    if axes is not None:
        record["axes"] = axes.as_dict()
    if extra:
        record.update(extra)
    return record


def _literal_gold(gold: dict[str, object]) -> dict[str, object]:
    """Normalise an authored label's floats so `canon()` sees one decimal."""
    out: dict[str, object] = {}
    for key, value in gold.items():
        if isinstance(value, float):
            out[key] = round(value, 1)
        elif isinstance(value, list) and value and isinstance(value[0], float):
            out[key] = [round(v, 1) for v in value]
        else:
            out[key] = value
    return out


def _tokens(text: str) -> frozenset[str]:
    norm = normalize_transcript(text)
    return frozenset(norm.split())


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _leakage_features(text: str) -> tuple[set[str], set[tuple[str, ...]]]:
    norm = normalize_transcript(text)
    return set(norm.split()), get_token_ngrams(norm, n=2)


def _leakage_sim(
    feat_a: tuple[set[str], set[tuple[str, ...]]],
    feat_b: tuple[set[str], set[tuple[str, ...]]],
) -> float:
    return max(jaccard_similarity(feat_a[0], feat_b[0]), jaccard_similarity(feat_a[1], feat_b[1]))


def generate_family_rows(
    family: TemplateFamily,
    rng: random.Random,
    authored: list[HardNegative],
    unknown_texts: list[str],
    seen_transcripts: set[str] | None = None,
    features_by_split: dict[str, list[tuple[set[str], set[tuple[str, ...]]]]] | None = None,
) -> list[dict[str, object]]:
    """The 20 rows for one family: authored rows first, then generated to fill.

    Authored rows come from `data/hard_negatives.py` (near-misses and negations)
    and `data/ood.py` (in-corpus `unknown`). They *consume* budget rather than
    extending it, so the family total is 20 either way.
    """
    rows: list[dict[str, object]] = []
    pattern = parse_pattern(family.slot_pattern)
    seen = seen_transcripts if seen_transcripts is not None else set()

    for index, negative in enumerate(authored, start=1):
        gold = _literal_gold(dict(negative.gold))
        seen.add(negative.text)
        if features_by_split is not None:
            features_by_split["train"].append(_leakage_features(negative.text))
        rows.append(
            _record(
                f"{family.family_id}-hn{index:02d}",
                family,
                "hard_negative",
                negative.text,
                gold,
                None,
                extra={"hard_negative": True, "contrast_group": negative.group},
            )
        )

    for index, text in enumerate(unknown_texts, start=1):
        seen.add(text)
        if features_by_split is not None:
            features_by_split[family.split].append(_leakage_features(text))
        rows.append(
            _record(
                f"{family.family_id}-u{index:02d}",
                family,
                "authored_unknown",
                text,
                {"intent": "unknown"},
                None,
            )
        )

    # Authored rows are never dropped to fit the budget --- see "where it flexes"
    # in the module docstring. A family holds max(ROWS_PER_FAMILY, authored).
    budget = max(0, ROWS_PER_FAMILY - len(rows))
    if budget == 0:
        return rows
    if family.intent == "unknown":
        raise AssertionError(
            f"family {family.family_id} is `unknown` but only {len(rows)} of "
            f"{ROWS_PER_FAMILY} rows are authored; the rest cannot be generated "
            f"(see data/surface_forms.py::_unknown_cores)"
        )

    # K=8 paraphrases per value sample. Two samples cover 16, a third covers the
    # remainder, so a family always shows the same label shape over more than one
    # set of numbers.
    per_sample: list[int] = []
    remaining = budget
    while remaining > 0:
        take = min(PARAPHRASES_K, remaining)
        per_sample.append(take)
        remaining -= take
    if len(per_sample) > 1 and per_sample[-1] == 1:
        per_sample[-2] += per_sample.pop()

    for sample_index, count in enumerate(per_sample, start=1):
        addressing_pool = _addressing_choices(pattern)
        addressing = rng.choice(addressing_pool)
        gold = build_gold(family, pattern, rng, addressing)
        pool = synonym_pool(gold, rng)

        reg_order = list(REGISTERS)
        num_order = list(NUMBER_FORMS)
        rng.shuffle(reg_order)
        rng.shuffle(num_order)

        for k in range(count):
            for attempt in range(200):
                axes = sample_axes(
                    pattern,
                    family.intent,
                    rng,
                    register=reg_order[(k + attempt) % len(reg_order)],
                    number_form=num_order[(k + attempt) % len(num_order)],
                    addressing=addressing,
                    synonym=pool[(k + attempt) % len(pool)],
                )
                transcript = realise(gold, axes, rng)
                if not transcript or transcript in seen:
                    continue
                if features_by_split is not None:
                    cand_feat = _leakage_features(transcript)
                    if family.split == "train":
                        conflict = False
                        for other in ("val", "test_synth"):
                            if any(
                                _leakage_sim(cand_feat, feat) >= NEAR_DUPLICATE_JACCARD
                                for feat in features_by_split[other]
                            ):
                                conflict = True
                                break
                        if conflict:
                            continue
                    else:
                        if any(
                            _leakage_sim(cand_feat, feat) >= NEAR_DUPLICATE_JACCARD
                            for feat in features_by_split["train"]
                        ):
                            continue
                break
            else:
                raise RuntimeError(
                    f"family {family.family_id} sample {sample_index} could not "
                    f"produce a distinct paraphrase {k + 1}/{count}; the frame "
                    f"bank for {family.intent} is too small"
                )
            seen.add(transcript)
            if features_by_split is not None:
                features_by_split[family.split].append(_leakage_features(transcript))
            rows.append(
                _record(
                    f"{family.family_id}-s{sample_index}p{k + 1:02d}",
                    family,
                    f"paraphrase_{sample_index}",
                    transcript,
                    gold,
                    axes,
                )
            )

    return rows


# --- golden set ------------------------------------------------------------
#
# test_golden is drawn from the 12 test_synth families only. Not val: val selects
# checkpoints, so golden rows from val families would let selection see the
# templates it is later scored on. The 200 rows are allocated across intents
# roughly in proportion to how much of the command space each one covers, then
# realised the same way as raw_pairs --- same sampler, same frame bank, held-out
# families.


def _golden_allocation() -> dict[str, int]:
    """Per-intent row counts summing to exactly `GOLDEN_ROWS`.

    Weighted by slot-space size, not uniformly: `move` and `formation` carry
    almost all of the schema's parameter surface, and `abort` has none at all, so
    an even split would spend a quarter of the benchmark on five one-word intents.
    """
    weights = {
        "move": 34,
        "formation": 34,
        "altitude": 22,
        "set_param": 22,
        "rotate": 22,
        "takeoff": 16,
        "land": 12,
        "hover": 12,
        "abort": 10,
        "unknown": 16,
    }
    if sum(weights.values()) != GOLDEN_ROWS:
        raise AssertionError(f"golden allocation sums to {sum(weights.values())}, want {GOLDEN_ROWS}")
    return weights


def generate_golden(
    rng: random.Random,
    seen_transcripts: set[str] | None = None,
    features_by_split: dict[str, list[tuple[set[str], set[tuple[str, ...]]]]] | None = None,
) -> list[dict[str, object]]:
    """The 200 benchmark rows, numbered `0001`..`0200`.

    The id is the join key with `data/audio/s1/<id>.wav`, which Session 02B
    records against, so it is zero-padded and stable under re-runs.
    """
    by_intent: dict[str, list[TemplateFamily]] = defaultdict(list)
    for family in FAMILIES:
        if family.split == "test_synth":
            by_intent[family.intent].append(family)

    allocation = _golden_allocation()
    missing = sorted(set(allocation) - set(by_intent))
    if missing:
        raise AssertionError(f"no test_synth family for intents {missing}")

    unknown_pool = [row.text for row in F120_GOLDEN_ROWS]
    rows: list[dict[str, object]] = []
    seen = seen_transcripts if seen_transcripts is not None else set()

    for intent, count in allocation.items():
        families = by_intent[intent]
        if intent == "unknown":
            if len(unknown_pool) < count:
                raise AssertionError(
                    f"need {count} golden unknown rows, have {len(unknown_pool)}"
                )
            for index in range(count):
                family = families[index % len(families)]
                text = unknown_pool[index]
                if text in seen:
                    raise AssertionError(f"duplicate golden transcript {text!r}")
                seen.add(text)
                if features_by_split is not None:
                    features_by_split["test_synth"].append(_leakage_features(text))
                rows.append(
                    _record("", family, "golden_unknown", text, {"intent": "unknown"}, None)
                )
            continue

        for index in range(count):
            family = families[index % len(families)]
            pattern = parse_pattern(family.slot_pattern)
            for attempt in range(200):
                addressing = rng.choice(_addressing_choices(pattern))
                gold = build_gold(family, pattern, rng, addressing)
                pool = synonym_pool(gold, rng)
                axes = sample_axes(
                    pattern,
                    intent,
                    rng,
                    register=REGISTERS[index % len(REGISTERS)],
                    number_form=NUMBER_FORMS[index % len(NUMBER_FORMS)],
                    addressing=addressing,
                    synonym=pool[(index + attempt) % len(pool)],
                )
                transcript = realise(gold, axes, rng)
                if not transcript or transcript in seen:
                    continue
                if features_by_split is not None:
                    cand_feat = _leakage_features(transcript)
                    if any(
                        _leakage_sim(cand_feat, feat) >= NEAR_DUPLICATE_JACCARD
                        for feat in features_by_split["train"]
                    ):
                        continue
                break
            else:
                raise RuntimeError(f"could not find a distinct golden row for {intent}")
            seen.add(transcript)
            if features_by_split is not None:
                features_by_split["test_synth"].append(_leakage_features(transcript))
            rows.append(_record("", family, "golden", transcript, gold, axes))

    if len(rows) != GOLDEN_ROWS:
        raise AssertionError(f"golden set has {len(rows)} rows, want {GOLDEN_ROWS}")

    # Shuffle before numbering so the recording session is not 34 formations in a
    # row --- a reader's voice drifts, and a block-ordered set would confound
    # intent with vocal fatigue in the Exp-1 numbers.
    rng.shuffle(rows)
    for index, row in enumerate(rows, start=1):
        row["id"] = f"{index:04d}"
        row["audio_path"] = f"data/audio/s1/{index:04d}.wav"
    return rows


# --- checks ----------------------------------------------------------------


def check_rows(rows: list[dict[str, object]], grammar: Grammar, label: str) -> None:
    """Every invariant a row must satisfy, checked on every row.

    Grammar acceptance is the roadmap's gate (FR-1). The canonical-and-in-envelope
    check is the one that catches the subtler bug: a label can be perfectly
    grammatical and still be out of range, and Layer 2 would clamp it at inference
    time --- so training on it teaches the model to emit values the runtime then
    silently rewrites, and every EM measurement afterwards is off by that margin.
    """
    for row in rows:
        target = row["target"]
        if not isinstance(target, str):
            raise AssertionError(f"{label} {row['id']}: target is not a string")
        if not grammar.accepts(target):
            raise AssertionError(f"{label} {row['id']}: cmd.gbnf rejects {target}")

        parsed = json.loads(target)
        recanon = canon(validate(parsed, fallback=False))
        if recanon != target:
            raise AssertionError(
                f"{label} {row['id']}: not canonical or out of envelope\n"
                f"  wrote:      {target}\n"
                f"  validate(): {recanon}"
            )
        if parsed["intent"] != row["gold_intent"]:
            raise AssertionError(f"{label} {row['id']}: gold_intent disagrees with target")

        ids = parsed.get("ids")
        if ids is not None:
            if not ids:
                raise AssertionError(f"{label} {row['id']}: empty ids list")
            if sorted(set(ids)) != ids:
                raise AssertionError(f"{label} {row['id']}: ids not deduped and sorted: {ids}")
            if any(not 0 <= i < SWARM_SIZE for i in ids):
                raise AssertionError(f"{label} {row['id']}: ids outside 0..{SWARM_SIZE - 1}: {ids}")

        transcript = row["transcript"]
        if not isinstance(transcript, str) or not transcript.strip():
            raise AssertionError(f"{label} {row['id']}: empty transcript")
        if transcript != transcript.lower():
            raise AssertionError(f"{label} {row['id']}: transcript is not lowercase")
        if transcript.rstrip()[-1] in ".!?":
            raise AssertionError(f"{label} {row['id']}: transcript has terminal punctuation")


def check_family_intent(rows: list[dict[str, object]]) -> None:
    """A row's intent must match its family's, so its split means what it says.

    F118 is the one documented exemption: the family table records its intent as
    `unknown` while its description and its rows are `hover` (Issue 27). The
    description and the rows are the authority --- `02_dataset_plan.md` §3.3 is
    explicit that "don't land yet" must resolve to `hover`.
    """
    table = {f.family_id: f for f in FAMILIES}
    for row in rows:
        family = table[row["template_family"]]
        if family.family_id == "F118":
            if row["gold_intent"] != "hover":
                raise AssertionError(f"F118 row {row['id']} is {row['gold_intent']}, want hover")
            continue
        if row["gold_intent"] != family.intent:
            raise AssertionError(
                f"row {row['id']} is {row['gold_intent']} but family "
                f"{family.family_id} is {family.intent}"
            )


def check_no_duplicates(rows: list[dict[str, object]]) -> None:
    seen: dict[str, str] = {}
    for row in rows:
        text = row["transcript"]
        if text in seen:
            raise AssertionError(
                f"duplicate transcript {text!r} in rows {seen[text]} and {row['id']}"
            )
        seen[text] = row["id"]


def check_cross_split_near_duplicates(rows: list[dict[str, object]]) -> list[tuple[str, str, float]]:
    """No held-out row may be a near-paraphrase of a training row.

    Family disjointness (Gate 2) is necessary but not sufficient: two different
    families can independently produce "hover" for the same label. Jaccard over
    tokens catches what family bookkeeping cannot.

    Compared within an intent only. Across intents high overlap is *desirable* ---
    that is what the hard negatives are --- so a global comparison would flag the
    corpus's most valuable rows.
    """
    buckets: dict[str, dict[str, list[tuple[str, frozenset[str]]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        buckets[row["gold_intent"]][row["split"]].append((row["id"], _tokens(row["transcript"])))

    offenders: list[tuple[str, str, float]] = []
    for intent, by_split in buckets.items():
        train = by_split.get("train", [])
        for split in ("val", "test_synth"):
            for held_id, held_tokens in by_split.get(split, []):
                for train_id, train_tokens in train:
                    score = _jaccard(held_tokens, train_tokens)
                    if score >= NEAR_DUPLICATE_JACCARD:
                        offenders.append((held_id, train_id, score))
    return offenders


def axis_histogram(rows: list[dict[str, object]]) -> dict[str, Counter]:
    counts: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        axes = row.get("axes")
        if not axes:
            continue
        for axis, value in axes.items():
            counts[axis][str(value)] += 1
    return counts


def check_axis_coverage(rows: list[dict[str, object]]) -> dict[str, Counter]:
    """Every value of every axis must appear. §3.2 is a requirement, not a hope."""
    counts = axis_histogram(rows)
    expected = {
        "register": set(REGISTERS),
        "number_form": set(NUMBER_FORMS),
        "addressing": set(ADDRESSING_MODES),
        "disfluency": {"True", "False"},
        "politeness": {"True", "False"},
        "ellipsis": {"True", "False"},
    }
    for axis, values in expected.items():
        seen = set(counts[axis])
        missing = values - seen
        if missing:
            raise AssertionError(f"axis {axis} never took values {sorted(missing)}")
    if not counts["synonym"]:
        raise AssertionError("axis synonym was never recorded")
    return counts


def check_family_budget(rows: list[dict[str, object]]) -> None:
    """Every family holds `max(ROWS_PER_FAMILY, authored)` rows, and no family is short.

    The overage is only legitimate where authored rows caused it. A family that
    generated its way past 20 would mean the paraphrase loop is miscounting, and a
    family under 20 would silently shrink the corpus.
    """
    counts: Counter[str] = Counter()
    authored: Counter[str] = Counter()
    for row in rows:
        counts[row["template_family"]] += 1
        if row["variant"] in ("hard_negative", "authored_unknown"):
            authored[row["template_family"]] += 1

    families = {f.family_id for f in FAMILIES}
    missing = families - set(counts)
    if missing:
        raise AssertionError(f"families with no rows: {sorted(missing)}")
    extra = set(counts) - families
    if extra:
        raise AssertionError(f"rows for unknown families: {sorted(extra)}")

    for family_id, count in sorted(counts.items()):
        expected = max(ROWS_PER_FAMILY, authored[family_id])
        if count != expected:
            raise AssertionError(
                f"family {family_id} has {count} rows, want {expected} "
                f"({authored[family_id]} authored)"
            )


def check_enum_coverage(rows: list[dict[str, object]]) -> None:
    """Every shape and direction the schema admits must appear in `train`.

    The regression guard for Issue 28. `data/template_families.py` asserts the
    same property over the family table; this asserts it over the rows actually
    written, which is what training reads.
    """
    shapes: set[str] = set()
    directions: set[str] = set()
    for row in rows:
        if row["split"] != "train":
            continue
        parsed = json.loads(row["target"])
        if parsed["intent"] == "formation":
            shapes.add(parsed["shape"])
        elif parsed["intent"] == "move" and "dir" in parsed:
            directions.add(parsed["dir"])
    if shapes != set(SHAPES):
        raise AssertionError(f"shapes missing from train rows: {sorted(set(SHAPES) - shapes)}")
    if directions != set(DIRECTIONS):
        raise AssertionError(
            f"directions missing from train rows: {sorted(set(DIRECTIONS) - directions)}"
        )


# --- assembly --------------------------------------------------------------


def _authored_by_family() -> tuple[dict[str, list[HardNegative]], dict[str, list[str]]]:
    negatives: dict[str, list[HardNegative]] = defaultdict(list)
    for negative in HARD_NEGATIVES:
        negatives[negative.family_id].append(negative)
    unknowns: dict[str, list[str]] = defaultdict(list)
    for row in IN_CORPUS_UNKNOWN:
        unknowns[row.family_id].append(row.text)
    return negatives, unknowns


def build_raw_pairs(
    rng: random.Random,
    seen: set[str] | None = None,
    features_by_split: dict[str, list[tuple[set[str], set[tuple[str, ...]]]]] | None = None,
) -> list[dict[str, object]]:
    negatives, unknowns = _authored_by_family()
    if seen is None:
        seen = set()

    for neg_list in negatives.values():
        for neg in neg_list:
            seen.add(neg.text)
            if features_by_split is not None:
                features_by_split["train"].append(_leakage_features(neg.text))
    for fid, unk_list in unknowns.items():
        sp = FAMILY_MAP[fid].split
        for text in unk_list:
            seen.add(text)
            if features_by_split is not None:
                features_by_split[sp].append(_leakage_features(text))

    rows: list[dict[str, object]] = []
    for family in FAMILIES:
        rows.extend(
            generate_family_rows(
                family,
                rng,
                negatives.get(family.family_id, []),
                unknowns.get(family.family_id, []),
                seen_transcripts=seen,
                features_by_split=features_by_split,
            )
        )
    return rows


def build_ood() -> list[dict[str, object]]:
    """`test_ood.jsonl` --- eval only, never trained on."""
    rows: list[dict[str, object]] = []
    for index, row in enumerate(ood_rows(), start=1):
        record: dict[str, object] = {
            "id": f"ood-{index:04d}",
            "template_family": "OOD",
            "split": "test_ood",
            "variant": row.source,
            "transcript": row.text,
            "target": canon({"intent": "unknown"}),
            "gold_intent": "unknown",
            "audio_path": None,
            "snr_db": None,
            "ood_source": row.source,
            "provenance": row.provenance,
        }
        if row.massive_intent is not None:
            record["massive_intent"] = row.massive_intent
        rows.append(record)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with open(path, "w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args(argv)

    grammar = load_grammar()
    rng = random.Random(args.seed)

    seen: set[str] = set()
    features_by_split: dict[str, list[tuple[set[str], set[tuple[str, ...]]]]] = defaultdict(list)

    ood = build_ood()
    for row in ood:
        seen.add(row["transcript"])

    raw_pairs = build_raw_pairs(rng, seen=seen, features_by_split=features_by_split)
    golden = generate_golden(rng, seen_transcripts=seen, features_by_split=features_by_split)

    # --- gate: FR-1 and the invariants around it
    check_rows(raw_pairs, grammar, "raw_pairs")
    check_rows(golden, grammar, "test_golden")
    for row in ood:
        if not grammar.accepts(row["target"]):
            raise AssertionError(f"OOD {row['id']}: cmd.gbnf rejects {row['target']}")

    check_family_intent(raw_pairs)
    check_family_intent(golden)
    check_no_duplicates(raw_pairs + golden)
    check_enum_coverage(raw_pairs)
    check_family_budget(raw_pairs)
    counts = check_axis_coverage(raw_pairs)

    near_dupes = check_cross_split_near_duplicates(raw_pairs)

    write_jsonl(RAW_PAIRS_PATH, raw_pairs)
    write_jsonl(TEST_OOD_PATH, ood)
    write_jsonl(TEST_GOLDEN_PATH, golden)
    GOLDEN_TRANSCRIPTS_PATH.write_text(
        "".join(f"{row['id']}\t{row['transcript']}\n" for row in golden), encoding="utf-8"
    )

    # --- report
    splits = Counter(row["split"] for row in raw_pairs)
    intents = Counter(row["gold_intent"] for row in raw_pairs)
    variants = Counter(row["variant"] for row in raw_pairs)

    print(f"seed {args.seed}\n")
    print(f"raw_pairs.jsonl            {len(raw_pairs)} rows -> {RAW_PAIRS_PATH}")
    for split in ("train", "val", "test_synth"):
        pct = 100.0 * splits[split] / len(raw_pairs)
        print(f"  {split:<12} {splits[split]:>5}  ({pct:.1f}%)")
    over = sorted(
        (fid, n)
        for fid, n in Counter(r["template_family"] for r in raw_pairs).items()
        if n > ROWS_PER_FAMILY
    )
    if over:
        print(
            f"  ({len(raw_pairs) - ROWS_PER_FAMILY * len(FAMILIES)} rows over the "
            f"{ROWS_PER_FAMILY}x{len(FAMILIES)} baseline, from authored rows in "
            + ", ".join(f"{fid}={n}" for fid, n in over)
            + ")"
        )
    print()
    print("  intent distribution")
    for intent, count in sorted(intents.items(), key=lambda kv: -kv[1]):
        print(f"    {intent:<12} {count:>5}")
    print()
    print("  row provenance")
    for variant, count in sorted(variants.items()):
        print(f"    {variant:<20} {count:>5}")
    print(f"    {'hard negatives':<20} {sum(1 for r in raw_pairs if r.get('hard_negative')):>5}")
    print()

    print("  diversity axes (§3.2)")
    for axis in ("register", "number_form", "addressing", "disfluency", "politeness", "ellipsis"):
        items = ", ".join(f"{k}={v}" for k, v in sorted(counts[axis].items()))
        print(f"    {axis:<12} {items}")
    print(f"    {'synonym':<12} {len(counts['synonym'])} distinct head words")
    print()

    print(f"test_ood.jsonl             {len(ood)} rows -> {TEST_OOD_PATH}")
    for source, count in Counter(row["ood_source"] for row in ood).items():
        print(f"    {source:<28} {count:>4}")
    print("  provenance")
    for prov, count in sorted(Counter(row["provenance"] for row in ood).items()):
        print(f"    {prov:<40} {count:>4}")
    print()

    print(f"test_golden.jsonl          {len(golden)} rows -> {TEST_GOLDEN_PATH}")
    print(f"test_golden_transcripts.txt {len(golden)} lines -> {GOLDEN_TRANSCRIPTS_PATH}")
    for intent, count in sorted(
        Counter(row["gold_intent"] for row in golden).items(), key=lambda kv: -kv[1]
    ):
        print(f"    {intent:<12} {count:>4}")
    print()

    unique_labels = len({row["target"] for row in raw_pairs})
    print(f"gate: cmd.gbnf accepted {len(raw_pairs) + len(golden) + len(ood)} labels "
          f"({unique_labels} distinct in raw_pairs)")
    print(f"gate: canon(validate(target)) == target on all {len(raw_pairs) + len(golden)} rows")
    print(f"gate: {len(raw_pairs) + len(golden)} transcripts, no duplicates")
    if near_dupes:
        print(f"WARNING: {len(near_dupes)} cross-split near-duplicates at Jaccard >= "
              f"{NEAR_DUPLICATE_JACCARD}:")
        for held_id, train_id, score in near_dupes[:10]:
            print(f"    {held_id} ~ {train_id}  {score:.2f}")
        return 1
    print(f"gate: no cross-split near-duplicates at Jaccard >= {NEAR_DUPLICATE_JACCARD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
