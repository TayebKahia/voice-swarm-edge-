"""Tests for label-first generation --- Session 02A.

Two layers, because they fail differently:

**Component tests** exercise the pieces directly (number rendering, the 1-indexed
`ids` mapping, the pattern parser, the GBNF interpreter). These are fast and they
localise a break to one function.

**Corpus tests** read the written artefacts and re-assert every invariant over
them. That is deliberately redundant with `data/generate.py`'s own checks: those
run over in-memory rows, and the thing that actually gets trained on is the file.
JSONL serialisation, key omission, and float formatting all happen between the two
and each has its own way of going wrong. The corpus tests skip if the artefacts
are absent, so a fresh clone can run `pytest` before `python data/generate.py`.

Every test in here would have caught a bug that was live at some point in this
session; none of them is decoration.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from data.gbnf import Grammar, GrammarError, load_grammar
from data.generate import (
    GOLDEN_ROWS,
    NEAR_DUPLICATE_JACCARD,
    ROWS_PER_FAMILY,
    Pattern,
    _sample_ids,
    _sample_pos,
    _sample_scalar,
    build_gold,
    check_axis_coverage,
    check_cross_split_near_duplicates,
    check_enum_coverage,
    check_family_budget,
    check_family_intent,
    check_no_duplicates,
    check_rows,
    parse_pattern,
)
from data.hard_negatives import HARD_NEGATIVES
from data.ood import F120_GOLDEN_ROWS, IN_CORPUS_UNKNOWN, ood_rows
from data.surface_forms import (
    ADDRESSING_MODES,
    NUMBER_FORMS,
    REGISTERS,
    Axes,
    num_to_words,
    realise,
    render_number,
    spoken_ids,
    synonym_pool,
)
from data.template_families import FAMILIES, FAMILY_MAP
from schema.canon import canon
from schema.schema import DIRECTIONS, ENVELOPE, SHAPES, SWARM_SIZE
from schema.validate import validate

DATA_DIR = Path(__file__).parent
RAW_PAIRS = DATA_DIR / "raw_pairs.jsonl"
TEST_GOLDEN = DATA_DIR / "test_golden.jsonl"
TEST_OOD = DATA_DIR / "test_ood.jsonl"


def _load(path: Path) -> list[dict]:
    if not path.is_file():
        pytest.skip(f"{path.name} not generated yet --- run `python data/generate.py`")
    with open(path, encoding="utf-8") as fp:
        return [json.loads(line) for line in fp if line.strip()]


@pytest.fixture(scope="module")
def grammar() -> Grammar:
    return load_grammar()


@pytest.fixture(scope="module")
def raw_pairs() -> list[dict]:
    return _load(RAW_PAIRS)


@pytest.fixture(scope="module")
def golden() -> list[dict]:
    return _load(TEST_GOLDEN)


@pytest.fixture(scope="module")
def ood() -> list[dict]:
    return _load(TEST_OOD)


# --- the GBNF interpreter --------------------------------------------------
#
# The gate rests on this, so it is tested against the frozen grammar rather than
# against itself. The accept cases are §2.2's wire-format examples; the reject
# cases are the failures the `num` rule exists to make structurally impossible.


@pytest.mark.parametrize(
    "label",
    [
        '{"intent":"abort"}',
        '{"intent":"unknown"}',
        '{"intent":"hover"}',
        '{"intent":"hover","ids":[0,2]}',
        '{"intent":"land"}',
        '{"intent":"takeoff"}',
        '{"intent":"takeoff","z":3.0}',
        '{"intent":"takeoff","z":3.0,"ids":[1]}',
        '{"intent":"altitude","z":2.5}',
        '{"intent":"altitude","z":-0.5}',
        '{"intent":"formation","shape":"circle","radius":5.0}',
        '{"intent":"formation","shape":"line","spacing":2.0,"ids":[0,1,2]}',
        '{"intent":"formation","shape":"flock"}',
        '{"intent":"move","pos":[10.0,-5.0,3.0]}',
        '{"intent":"move","dir":"north","dist":15.0}',
        '{"intent":"move","dir":"north","dist":15.0,"speed":1.5,"ids":[0]}',
        '{"intent":"rotate","yaw":-90.0}',
        '{"intent":"rotate","yaw":180.0}',
        '{"intent":"set_param","speed":1.0}',
        '{"intent":"set_param","speed":1.0,"spacing":2.0,"alt":5.0}',
    ],
)
def test_grammar_accepts_valid_labels(grammar: Grammar, label: str) -> None:
    assert grammar.accepts(label), label


@pytest.mark.parametrize(
    "label,why",
    [
        ('{"intent":"abort"', "truncated: no closing brace"),
        ('{"intent":"abort"}}', "trailing brace"),
        ('{"intent":"altitude","z":2.55}', "two decimals: num allows one"),
        ('{"intent":"altitude","z":1e999}', "exponent notation"),
        ('{"intent":"altitude","z":2.}', "bare decimal point"),
        ('{"intent":"altitude","z":1234}', "four integer digits"),
        ('{"intent":"formation","shape":"square"}', "shape not in the enum"),
        ('{"intent":"move","dir":"sideways","dist":5.0}', "dir not in the enum"),
        ('{"intent":"move","dist":5.0}', "dir/dist pair broken"),
        ('{"intent":"move","pos":[1.0,2.0]}', "pos needs three components"),
        ('{"intent":"formation","shape":"circle",}', "trailing comma"),
        ('{"intent":"hover","ids":[5]}', "id outside 0..4 after the S3 amendment"),
        ('{"intent": "abort"}', "whitespace after the colon"),
        ('{"intent":"altitude"}', "altitude requires z"),
        ('{"intent":"fly"}', "intent not in the enum"),
        ("", "empty string"),
    ],
)
def test_grammar_rejects_invalid_labels(grammar: Grammar, label: str, why: str) -> None:
    assert not grammar.accepts(label), f"should reject ({why}): {label}"


def test_grammar_rejects_prefix_match(grammar: Grammar) -> None:
    """A truncated label must fail, which needs whole-string matching.

    This is the S3 hardware failure: an unbounded repetition ran past `-n` and
    produced a valid *prefix*. A prefix-matching acceptor would pass it.
    """
    full = '{"intent":"move","dir":"north","dist":15.0}'
    assert grammar.accepts(full)
    for cut in range(1, len(full)):
        assert not grammar.accepts(full[:cut]), f"accepted a prefix: {full[:cut]!r}"


def test_grammar_reads_the_repetition_amendment() -> None:
    """`{m,n}` must parse --- `idlist` uses it, and S3 recommended it."""
    g = Grammar.parse('root ::= "a" ( "," "a" ){0,2}')
    assert g.accepts("a")
    assert g.accepts("a,a")
    assert g.accepts("a,a,a")
    assert not g.accepts("a,a,a,a")


def test_grammar_rejects_unknown_rule() -> None:
    with pytest.raises(GrammarError, match="undefined rules"):
        Grammar.parse('root ::= missing')


def test_grammar_rejects_empty_repetition() -> None:
    with pytest.raises(GrammarError, match="empty"):
        Grammar.parse('root ::= empty*\nempty ::= "a"?').accepts("aa")


# --- numbers and the ids mapping ------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        (0.0, "zero"),
        (1.0, "one"),
        (5.0, "five"),
        (15.0, "fifteen"),
        (20.0, "twenty"),
        (45.0, "forty-five"),
        (90.0, "ninety"),
        (180.0, "one hundred and eighty"),
        (-90.0, "minus ninety"),
        (1.5, "one point five"),
        (0.5, "nought point five"),
        (2.8, "two point eight"),
    ],
)
def test_num_to_words(value: float, expected: str) -> None:
    assert num_to_words(value) == expected


def test_num_to_words_half_form() -> None:
    assert num_to_words(4.5, half=True) == "four and a half"
    assert num_to_words(0.5, half=True) == "half"
    assert num_to_words(4.0, half=True) == "four"


@pytest.mark.parametrize("form", NUMBER_FORMS)
def test_render_number_covers_every_form(form: str) -> None:
    rng = random.Random(0)
    for unit in ("m", "mps", "deg", None):
        out = render_number(2.5, form, unit, rng)
        assert out and out == out.strip()


def test_spoken_ids_is_one_indexed() -> None:
    """Roadmap 02A task 3: `[0]` is spoken "drone one"."""
    assert spoken_ids([0]) == [1]
    assert spoken_ids([0, 2]) == [1, 3]
    assert spoken_ids([4]) == [5]


def test_transcripts_speak_one_indexed_ids() -> None:
    """The 0-/1-indexed boundary, end to end.

    Spike S3 found zero-shot models never do this conversion, so fine-tuning owns
    it --- which means the corpus has to be right about it in every row. A row
    saying "drone one" with `ids:[1]` would teach the exact bug.
    """
    rng = random.Random(7)
    gold = {"intent": "hover", "ids": [0]}
    axes = Axes("imperative", "word", "single", "hover", False, False, False)
    text = realise(gold, axes, rng)
    assert " one" in text
    assert " zero" not in text


# --- the pattern parser ---------------------------------------------------


def test_parse_pattern_none() -> None:
    assert parse_pattern("none") == Pattern(None, None, (), False)


def test_parse_pattern_shape_and_slots() -> None:
    assert parse_pattern("shape:circle,radius,ids") == Pattern("circle", None, ("radius",), True)


def test_parse_pattern_direction() -> None:
    assert parse_pattern("dir:north,dist,speed") == Pattern(
        None, "north", ("dist", "speed"), False
    )


def test_parse_pattern_rejects_unknown_enum() -> None:
    with pytest.raises(ValueError, match="unknown shape"):
        parse_pattern("shape:hexagon,radius")
    with pytest.raises(ValueError, match="unknown direction"):
        parse_pattern("dir:sideways,dist")


def test_every_family_pattern_parses() -> None:
    """The family table is hand-maintained, so its notation is worth checking."""
    for family in FAMILIES:
        parse_pattern(family.slot_pattern)


# --- sampling -------------------------------------------------------------


@pytest.mark.parametrize("slot", ["radius", "spacing", "z", "speed", "yaw", "alt"])
def test_sampled_scalars_are_in_envelope_and_on_the_grid(slot: str) -> None:
    rng = random.Random(3)
    low, high = ENVELOPE[slot]
    for _ in range(500):
        value = _sample_scalar(slot, rng)
        assert low <= value <= high, f"{slot}={value} outside [{low},{high}]"
        assert round(value, 1) == value, f"{slot}={value} has more than one decimal"


def test_sampled_pos_respects_the_norm_bound() -> None:
    rng = random.Random(4)
    z_low, z_high = ENVELOPE["z"]
    for _ in range(500):
        x, y, z = _sample_pos(rng)
        assert x * x + y * y + z * z <= 50.0 * 50.0 + 1e-6
        assert z_low <= z <= z_high
        for component in (x, y, z):
            assert round(component, 1) == component


@pytest.mark.parametrize("mode", ["single", "subset", "range"])
def test_sampled_ids_are_canonical(mode: str) -> None:
    rng = random.Random(5)
    for _ in range(300):
        ids = _sample_ids(rng, mode)
        assert ids, "empty ids would silently mean all drones"
        assert ids == sorted(set(ids)), f"not deduped and sorted: {ids}"
        assert all(0 <= i < SWARM_SIZE for i in ids)
        if mode == "single":
            assert len(ids) == 1


def test_build_gold_key_order_matches_canon() -> None:
    """Labels are built in `KEY_ORDER`, so `canon()` never has to reorder."""
    rng = random.Random(6)
    for family in FAMILIES:
        if family.intent == "unknown":
            continue
        pattern = parse_pattern(family.slot_pattern)
        addressing = "single" if pattern.wants_ids else "implicit_all"
        gold = build_gold(family, pattern, rng, addressing)
        assert json.dumps(gold, separators=(",", ":")) == canon(gold), family.family_id


def test_build_gold_is_deterministic_under_seed() -> None:
    family = FAMILY_MAP["F001"]
    pattern = parse_pattern(family.slot_pattern)
    first = build_gold(family, pattern, random.Random(42), "implicit_all")
    second = build_gold(family, pattern, random.Random(42), "implicit_all")
    assert first == second


# --- authored rows --------------------------------------------------------


def test_hard_negative_count() -> None:
    assert len(HARD_NEGATIVES) >= 150


def test_hard_negatives_are_grammatical(grammar: Grammar) -> None:
    for row in HARD_NEGATIVES:
        label = canon(row.gold)
        assert grammar.accepts(label), f"{row.text!r} -> {label}"


def test_hard_negatives_are_in_envelope() -> None:
    """An authored value out of range would train the model to be clamped."""
    for row in HARD_NEGATIVES:
        label = canon(row.gold)
        assert canon(validate(json.loads(label), fallback=False)) == label, row.text


def test_hard_negatives_all_train() -> None:
    for row in HARD_NEGATIVES:
        assert FAMILY_MAP[row.family_id].split == "train", row.text


def test_abort_is_never_relabelled() -> None:
    """ADR-0003 decision 3: no abort utterance maps to anything but abort."""
    for row in HARD_NEGATIVES:
        if "abort" in row.text:
            assert row.gold["intent"] == "abort", row.text


def test_negation_resolves_to_hover() -> None:
    """§3.3: "don't land yet" must be hover, never land."""
    negations = [r for r in HARD_NEGATIVES if r.family_id == "F118"]
    assert len(negations) >= 20
    for row in negations:
        assert row.gold == {"intent": "hover"}, row.text
    texts = {r.text for r in negations}
    assert "don't land yet" in texts


def test_ood_quarters_are_balanced() -> None:
    rows = ood_rows()
    assert len(rows) == 150
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.source] = counts.get(row.source, 0) + 1
    assert len(counts) == 4, counts
    assert max(counts.values()) - min(counts.values()) <= 2, counts


def test_ood_provenance_is_never_optimistic() -> None:
    """A row may only claim `massive_mined` / `harvested` if that happened."""
    allowed = {
        "massive_mined",
        "massive_taxonomy_authored",
        "authored",
        "authored_asr_garbage_pending_harvest",
    }
    for row in ood_rows():
        assert row.provenance in allowed or row.provenance.endswith("_harvested"), row.provenance


def test_unknown_and_ood_texts_are_disjoint() -> None:
    corpus = {r.text for r in IN_CORPUS_UNKNOWN}
    golden_unknown = {r.text for r in F120_GOLDEN_ROWS}
    ood_texts = {r.text for r in ood_rows()}
    assert not corpus & ood_texts
    assert not corpus & golden_unknown
    assert not golden_unknown & ood_texts


# --- the written corpus ---------------------------------------------------


def test_raw_pairs_row_count(raw_pairs: list[dict]) -> None:
    """At least 20 per family, and the overage is small and accounted for.

    The baseline is 20 x 120 = 2,400. F117 and F116 run over it because their
    authored near-misses are not droppable (see generate.py's docstring), so this
    is a floor plus a ceiling on the excess rather than an equality.
    """
    baseline = ROWS_PER_FAMILY * len(FAMILIES)
    assert baseline == 2400
    assert baseline <= len(raw_pairs) <= baseline + 60


def test_raw_pairs_split_proportions(raw_pairs: list[dict]) -> None:
    """Near 80/10/10. The overage families are all `train`, so val/test are exact."""
    counts: dict[str, int] = {}
    for row in raw_pairs:
        counts[row["split"]] = counts.get(row["split"], 0) + 1
    assert set(counts) == {"train", "val", "test_synth"}
    assert counts["val"] == 240
    assert counts["test_synth"] == 240
    assert counts["train"] >= 1920
    assert 0.79 <= counts["train"] / len(raw_pairs) <= 0.81


def test_every_family_holds_its_budget(raw_pairs: list[dict]) -> None:
    """`max(20, authored)` per family --- no family short, none padded."""
    counts: dict[str, int] = {}
    authored: dict[str, int] = {}
    for row in raw_pairs:
        fid = row["template_family"]
        counts[fid] = counts.get(fid, 0) + 1
        if row["variant"] in ("hard_negative", "authored_unknown"):
            authored[fid] = authored.get(fid, 0) + 1
    assert len(counts) == len(FAMILIES)
    off = {
        fid: (n, authored.get(fid, 0))
        for fid, n in counts.items()
        if n != max(ROWS_PER_FAMILY, authored.get(fid, 0))
    }
    assert not off, off


def test_record_shape_matches_section_7_4(raw_pairs: list[dict]) -> None:
    """§7.4 fixes the record shape for the whole project."""
    required = {
        "id",
        "template_family",
        "split",
        "variant",
        "transcript",
        "target",
        "gold_intent",
        "audio_path",
        "snr_db",
    }
    for row in raw_pairs:
        assert required <= set(row), sorted(required - set(row))


def test_ids_are_unique(raw_pairs: list[dict], golden: list[dict]) -> None:
    for rows, name in ((raw_pairs, "raw_pairs"), (golden, "test_golden")):
        ids = [row["id"] for row in rows]
        assert len(ids) == len(set(ids)), f"{name} has duplicate ids"


def test_every_label_is_grammatical(
    grammar: Grammar, raw_pairs: list[dict], golden: list[dict], ood: list[dict]
) -> None:
    """FR-1, over the files that actually get trained on."""
    for rows, name in ((raw_pairs, "raw_pairs"), (golden, "golden"), (ood, "ood")):
        for row in rows:
            assert grammar.accepts(row["target"]), f"{name} {row['id']}: {row['target']}"


def test_every_label_is_canonical_and_in_envelope(
    raw_pairs: list[dict], golden: list[dict]
) -> None:
    for rows in (raw_pairs, golden):
        for row in rows:
            target = row["target"]
            assert canon(validate(json.loads(target), fallback=False)) == target, row["id"]


def test_null_fields_are_omitted_from_targets(raw_pairs: list[dict]) -> None:
    """Trap 7: nulls in the wire format cost ~22 tokens a row for nothing."""
    for row in raw_pairs:
        assert "null" not in row["target"], row["id"]


def test_targets_have_no_whitespace(raw_pairs: list[dict]) -> None:
    for row in raw_pairs:
        assert " " not in row["target"], row["id"]


def test_corpus_invariants_via_generate(raw_pairs: list[dict], golden: list[dict], grammar: Grammar) -> None:
    """Re-run generate.py's own checks over the written rows."""
    check_rows(raw_pairs, grammar, "raw_pairs")
    check_rows(golden, grammar, "test_golden")
    check_family_intent(raw_pairs)
    check_family_intent(golden)
    check_no_duplicates(raw_pairs + golden)
    check_enum_coverage(raw_pairs)
    check_family_budget(raw_pairs)
    check_axis_coverage(raw_pairs)


def test_no_cross_split_near_duplicates(raw_pairs: list[dict], golden: list[dict]) -> None:
    offenders = check_cross_split_near_duplicates(raw_pairs, golden)
    assert not offenders, (
        f"{len(offenders)} held-out rows are near-paraphrases of training rows at "
        f"Jaccard >= {NEAR_DUPLICATE_JACCARD}: {offenders[:5]}"
    )


def _audit_row(row_id: str, split: str, text: str, intent: str = "move") -> dict:
    return {"id": row_id, "split": split, "gold_intent": intent, "transcript": text}


def test_near_duplicate_audit_sees_golden_rows() -> None:
    """`test_golden` must be audited, not just `val` and `test_synth`.

    Golden rows carry `split="test_synth"` for provenance, so an audit that
    buckets on that field alone silently never compares them --- which is what
    this guards. The 200 golden rows are the corpus's most valuable eval set.
    """
    train = [_audit_row("T1", "train", "move north 10 metres everyone")]
    golden = [_audit_row("G1", "test_synth", "move north 10 metres everyone")]
    offenders = check_cross_split_near_duplicates(train, golden)
    assert [o[0] for o in offenders] == ["G1"], offenders



def test_near_duplicate_audit_keeps_hard_negatives() -> None:
    """Cross-intent overlap is the *point* of a contrast group, never leakage."""
    rows = [
        _audit_row("T3", "train", "hover now", intent="hover"),
        _audit_row("V3", "val", "hover now", intent="unknown"),
    ]
    assert check_cross_split_near_duplicates(rows) == []


def test_train_covers_every_shape_and_direction(raw_pairs: list[dict]) -> None:
    """Issue 28's regression guard, over the rows rather than the family table."""
    shapes, directions = set(), set()
    for row in raw_pairs:
        if row["split"] != "train":
            continue
        parsed = json.loads(row["target"])
        if parsed["intent"] == "formation":
            shapes.add(parsed["shape"])
        elif parsed["intent"] == "move" and "dir" in parsed:
            directions.add(parsed["dir"])
    assert shapes == set(SHAPES), sorted(set(SHAPES) - shapes)
    assert directions == set(DIRECTIONS), sorted(set(DIRECTIONS) - directions)


def test_every_intent_appears_in_train(raw_pairs: list[dict]) -> None:
    intents = {row["gold_intent"] for row in raw_pairs if row["split"] == "train"}
    assert intents == {
        "formation", "move", "altitude", "takeoff", "land",
        "hover", "abort", "rotate", "set_param", "unknown",
    }


def test_paraphrase_groups_share_a_label(raw_pairs: list[dict]) -> None:
    """K=8 paraphrases per value sample: same label, eight different sentences."""
    groups: dict[tuple[str, str], set[str]] = {}
    texts: dict[tuple[str, str], set[str]] = {}
    for row in raw_pairs:
        if not row["variant"].startswith("paraphrase_"):
            continue
        key = (row["template_family"], row["variant"])
        groups.setdefault(key, set()).add(row["target"])
        texts.setdefault(key, set()).add(row["transcript"])
    assert groups
    for key, labels in groups.items():
        assert len(labels) == 1, f"{key} spans {len(labels)} labels"
        assert len(texts[key]) > 1, f"{key} has only one distinct transcript"


def test_hard_negatives_are_in_the_corpus(raw_pairs: list[dict]) -> None:
    authored = {row.text for row in HARD_NEGATIVES}
    written = {row["transcript"] for row in raw_pairs if row.get("hard_negative")}
    assert written == authored, sorted(authored ^ written)[:5]


def test_contrast_groups_do_not_straddle_splits(raw_pairs: list[dict]) -> None:
    """A group split across the boundary trains the easy half and scores the hard."""
    by_group: dict[str, set[str]] = {}
    for row in raw_pairs:
        group = row.get("contrast_group")
        if group:
            by_group.setdefault(group, set()).add(row["split"])
    assert by_group
    straddling = {g: s for g, s in by_group.items() if s != {"train"}}
    assert not straddling, straddling


# --- the golden set -------------------------------------------------------


def test_golden_row_count(golden: list[dict]) -> None:
    assert len(golden) == GOLDEN_ROWS == 200


def test_golden_comes_only_from_test_synth_families(golden: list[dict]) -> None:
    """Not val: val selects checkpoints, so golden from val leaks into selection."""
    for row in golden:
        assert FAMILY_MAP[row["template_family"]].split == "test_synth", row["id"]


def test_golden_ids_are_sequential_and_padded(golden: list[dict]) -> None:
    assert [row["id"] for row in golden] == [f"{i:04d}" for i in range(1, GOLDEN_ROWS + 1)]


def test_golden_audio_paths_match_ids(golden: list[dict]) -> None:
    """The id is the join key with the Session 02B recordings."""
    for row in golden:
        assert row["audio_path"] == f"data/audio/s1/{row['id']}.wav"


def test_golden_covers_all_ten_intents(golden: list[dict]) -> None:
    counts: dict[str, int] = {}
    for row in golden:
        counts[row["gold_intent"]] = counts.get(row["gold_intent"], 0) + 1
    assert len(counts) == 10, counts
    assert min(counts.values()) >= 10, counts


def test_golden_is_disjoint_from_raw_pairs(golden: list[dict], raw_pairs: list[dict]) -> None:
    corpus = {row["transcript"] for row in raw_pairs}
    for row in golden:
        assert row["transcript"] not in corpus, row["id"]


def test_golden_transcripts_file_matches_jsonl(golden: list[dict]) -> None:
    path = DATA_DIR / "test_golden_transcripts.txt"
    if not path.is_file():
        pytest.skip("test_golden_transcripts.txt not generated yet")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(golden)
    for line, row in zip(lines, golden):
        row_id, _, transcript = line.partition("\t")
        assert row_id == row["id"]
        assert transcript == row["transcript"]


# --- test_ood -------------------------------------------------------------


def test_ood_is_eval_only(ood: list[dict]) -> None:
    """Every OOD row must be outside the corpus splits, or it leaks into training."""
    for row in ood:
        assert row["split"] == "test_ood", row["id"]
        assert row["template_family"] == "OOD", row["id"]


def test_ood_labels_are_all_unknown(ood: list[dict]) -> None:
    for row in ood:
        assert row["target"] == '{"intent":"unknown"}', row["id"]


def test_ood_has_four_sources(ood: list[dict]) -> None:
    sources = {row["ood_source"] for row in ood}
    assert sources == {
        "massive_assistant",
        "drone_adjacent_unsupported",
        "asr_garbage",
        "truncated_fragment",
    }


def test_ood_rows_carry_provenance(ood: list[dict]) -> None:
    for row in ood:
        assert row["provenance"], row["id"]


def test_ood_asr_rows_may_be_empty_or_punctuated(ood: list[dict]) -> None:
    """Source (c) is verbatim ASR output, so the corpus convention does not apply.

    The runtime sees these strings exactly as whisper emits them --- including the
    empty string on silence --- so normalising them here would test something the
    pipeline never encounters.
    """
    asr = [row for row in ood if row["ood_source"] == "asr_garbage"]
    assert asr
    assert any(row["transcript"] != row["transcript"].lower() or
               (row["transcript"] and row["transcript"][-1] in ".!?") or
               row["transcript"] == ""
               for row in asr)


def test_ood_is_disjoint_from_corpus(ood: list[dict], raw_pairs: list[dict], golden: list[dict]) -> None:
    corpus = {row["transcript"] for row in raw_pairs} | {row["transcript"] for row in golden}
    for row in ood:
        assert row["transcript"] not in corpus, row["id"]
