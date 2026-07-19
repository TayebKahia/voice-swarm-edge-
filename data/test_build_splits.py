"""Tests for split assembly and the two augmentation guards (`data/build_splits.py`).

`02_dataset_plan.md` §4 states the guards in one sentence each. They are worth
testing carefully because both failures are silent: an inflated split still trains,
and a corrupt-to-command pair still looks like a valid row.
"""

from __future__ import annotations

import json

import pytest

from data.build_splits import (
    DESTROYED_SIMILARITY,
    RECORD_KEYS,
    UNKNOWN_TARGET,
    apply_augmentation,
    deduplicate,
    normalise,
    similarity,
    to_record,
)
from data.check_leakage import normalize_transcript
from data.composition import DEFAULT_SEED, assign_variants, needs_roundtrip

MOVE = '{"intent":"move","dir":"north","dist":10.0}'
LAND = '{"intent":"land"}'


def raw(item_id: str, transcript: str, target: str = MOVE, intent: str = "move") -> dict:
    return {
        "id": item_id,
        "template_family": "F001",
        "split": "train",
        "variant": "paraphrase_1",
        "transcript": transcript,
        "target": target,
        "gold_intent": intent,
        "audio_path": None,
        "snr_db": None,
    }


def trip(item_id: str, row: dict, asr: str, snr: int = 10) -> dict:
    return {
        "id": item_id,
        "variant": f"asr_{snr}db",
        "snr_db": snr,
        "clean_transcript": row["transcript"],
        "target": row["target"],
        "gold_intent": row["gold_intent"],
        "asr_transcript": asr,
        "asr_ok": True,
    }


def variant_of(rows, seed=DEFAULT_SEED):
    return assign_variants(rows, seed=seed)


def pick(rows, wanted, seed=DEFAULT_SEED):
    """An id from `rows` whose assigned variant is `wanted`."""
    assignment = variant_of(rows, seed)
    for row in rows:
        if assignment[row["id"]] == wanted:
            return row
    raise AssertionError(f"no row assigned {wanted}")


# --- record shape ----------------------------------------------------------


def test_record_follows_the_section_7_4_key_order():
    record = to_record(raw("x1", "move north ten"))
    assert list(record)[: len(RECORD_KEYS)] == list(RECORD_KEYS)


def test_generation_provenance_moves_to_source_variant():
    """§7.4 reserves `variant` for the augmentation variant; 02A's value survives."""
    record = to_record(raw("x1", "move north ten"))
    assert record["variant"] == "clean"
    assert record["source_variant"] == "paraphrase_1"


def test_hard_negative_fields_are_carried_through():
    row = raw("x1", "don't land yet", target='{"intent":"hover"}', intent="hover")
    row["hard_negative"] = True
    row["contrast_group"] = "land"
    record = to_record(row)
    assert record["hard_negative"] is True
    assert record["contrast_group"] == "land"


def test_normalise_agrees_with_the_gate_2_checker():
    """A pair this file calls identical must be one `check_leakage.py` also does."""
    for text in ("Form a circle, RADIUS five.", "  don't   land  yet ", "10m — north"):
        assert normalise(text) == normalize_transcript(text)


# --- substitution, not inflation -------------------------------------------


def test_augmentation_does_not_add_rows():
    """`prd.md` Table 13 puts train_synth at ~1,900 pairs; appending a round-trip
    row beside every clean one would make it ~3,900."""
    rows = [raw(f"r{i:03d}", f"move north {i} metres") for i in range(200)]
    trips = [
        trip(r["id"], r, f"move north {i} meters, roughly")
        for i, r in enumerate(rows)
    ]
    records, _, _ = apply_augmentation(rows, trips, seed=DEFAULT_SEED)
    assert len(records) == len(rows)
    assert {r["id"] for r in records} == {r["id"] for r in rows}


def test_noisy_transcript_keeps_the_original_target():
    """The single most important line in §4."""
    rows = [raw(f"r{i:03d}", f"move north {i} metres") for i in range(200)]
    target_row = pick(rows, "asr_10db")
    trips = [trip(target_row["id"], target_row, "move north 4 meters or so")]

    records, _, _ = apply_augmentation(rows, trips, seed=DEFAULT_SEED)
    got = next(r for r in records if r["id"] == target_row["id"])

    assert got["transcript"] == "move north 4 meters or so"
    assert got["target"] == target_row["target"] == MOVE
    assert got["snr_db"] == 10
    assert got["variant"] == "asr_10db"


def test_identity_roundtrip_keeps_its_provenance_and_is_flagged():
    """§4 warns the recogniser often returns the clean string. When it does, the row
    keeps its variant and SNR --- an identity round-trip is a true sample from the
    ASR output distribution, and re-rolling until it degraded would keep only the
    utterances whisper fails on. The flag is what lets the dataset card report
    text-distinctness separately from provenance."""
    rows = [raw(f"r{i:03d}", f"move north {i} metres") for i in range(200)]
    target_row = pick(rows, "asr_10db")
    restyled = target_row["transcript"].upper() + "."
    trips = [trip(target_row["id"], target_row, restyled)]

    records, _, actions = apply_augmentation(rows, trips, seed=DEFAULT_SEED)
    got = next(r for r in records if r["id"] == target_row["id"])

    assert got["variant"] == "asr_10db"
    assert got["snr_db"] == 10
    assert got["transcript"] == restyled
    assert got["roundtrip_identical"] is True
    assert actions["roundtrip_identical"] == 1


def test_a_genuinely_degraded_roundtrip_is_not_flagged_identical():
    rows = [raw(f"r{i:03d}", f"move north {i} metres") for i in range(200)]
    target_row = pick(rows, "asr_10db")
    trips = [trip(target_row["id"], target_row, "move north, uh, 4 meters")]

    records, _, actions = apply_augmentation(rows, trips, seed=DEFAULT_SEED)
    got = next(r for r in records if r["id"] == target_row["id"])

    assert "roundtrip_identical" not in got
    assert actions["roundtrip_identical"] == 0


def test_missing_transcript_falls_back_to_clean_and_is_reported():
    """Dropping the row would shrink the split with nothing saying so."""
    rows = [raw(f"r{i:03d}", f"move north {i} metres") for i in range(200)]
    target_row = pick(rows, "asr_10db")

    records, rejects, actions = apply_augmentation(rows, [], seed=DEFAULT_SEED)
    got = next(r for r in records if r["id"] == target_row["id"])

    assert len(records) == len(rows)
    assert got["variant"] == "clean"
    assert actions["asr_missing_to_clean"] >= 1
    assert any(x["id"] == target_row["id"] and x["reason"] == "asr_missing" for x in rejects)


# --- guard (ii): destroyed utterances --------------------------------------


def test_destroyed_utterance_is_relabelled_unknown_not_dropped():
    """A transcript too damaged to read *should* produce `unknown` --- that is
    training signal for the safe-failure rate, not waste."""
    rows = [raw(f"r{i:03d}", f"move north {i} metres") for i in range(200)]
    target_row = pick(rows, "asr_10db")
    trips = [trip(target_row["id"], target_row, "Thanks for watching!")]

    records, rejects, actions = apply_augmentation(rows, trips, seed=DEFAULT_SEED)
    got = next(r for r in records if r["id"] == target_row["id"])

    assert got["target"] == UNKNOWN_TARGET
    assert got["gold_intent"] == "unknown"
    assert got["transcript"] == "Thanks for watching!"
    assert got["relabelled_from"] == "move"
    assert actions["relabelled_unknown"] == 1
    assert any(x["reason"] == "destroyed_relabelled_unknown" for x in rejects)


def test_ordinary_degradation_is_kept_with_its_label():
    """"form a circle" -> "4m a circle" is still readable and must not be relabelled."""
    assert similarity("form a circle, radius five", "4m a circle, radius 5.") > DESTROYED_SIMILARITY


def test_a_correct_transcription_is_never_called_destroyed():
    """Whisper writes "128.4" for "one hundred and twenty-eight point four". On raw
    characters that scores 0.54 --- below the threshold --- and the first build
    relabelled fifteen readable commands `unknown` on exactly that basis."""
    pairs = [
        ("birds one thru two let's turn call it one hundred and twenty-eight point four",
         "Birds 1 through 2, let's turn call it 128.4"),
        ("all drones, position seventeen point two, minus nineteen point eight, eleven",
         "all drones, position, 17.2, minus 19.8, 11"),
        ("forty-eight point two to the south at one point one",
         "48.2 to the south at 1.1"),
        ("birds one, two and four, spin one hundred and seventy-two right",
         "birds, 1, 2, and 4, spin 172 right"),
    ]
    for clean, asr in pairs:
        assert similarity(clean, asr) >= DESTROYED_SIMILARITY, (clean, asr)


def test_similarity_threshold_separates_readable_from_destroyed():
    readable = [
        ("move north ten metres", "move north 10 meters"),
        ("drone two climb to four", "drone to climb to 4"),
        ("form a circle radius five", "4m a circle radius 5"),
    ]
    destroyed = [
        ("move north ten metres", "Thanks for watching!"),
        ("form a wedge spacing two", "[BLANK_AUDIO]"),
        ("set the speed to one point five", "you"),
    ]
    for clean, asr in readable:
        assert similarity(clean, asr) >= DESTROYED_SIMILARITY, (clean, asr)
    for clean, asr in destroyed:
        assert similarity(clean, asr) < DESTROYED_SIMILARITY, (clean, asr)


# --- guard (i): de-duplication ---------------------------------------------


def test_identical_transcripts_with_one_target_collapse_to_one_row():
    records = [
        to_record(raw("a", "move north ten")),
        to_record(raw("b", "move north ten")),
    ]
    kept, rejects, actions = deduplicate(records, {})

    assert [r["id"] for r in kept] == ["a"]
    assert actions["dropped_duplicate"] == 1
    assert rejects[0]["duplicate_of"] == "a"


def test_label_conflict_reverts_to_clean_rather_than_dropping():
    """One input with two answers is worse than a duplicate; the label survives."""
    original = raw("b", "land the swarm now", target=LAND, intent="land")
    records = [
        to_record(raw("a", "move north ten")),
        to_record(original, variant="asr_5db", transcript="move north ten", snr_db=5),
    ]
    kept, rejects, actions = deduplicate(records, {"b": original})

    assert len(kept) == 2
    reverted = next(r for r in kept if r["id"] == "b")
    assert reverted["transcript"] == "land the swarm now"
    assert reverted["target"] == LAND
    assert reverted["variant"] == "clean"
    assert actions["reverted_conflict_to_clean"] == 1
    assert rejects[0]["reason"] == "label_conflict"


def test_label_conflict_reverts_the_augmented_row_not_the_later_one():
    """An ASR collision must never cost the corpus an authored surface form."""
    augmented_raw = raw("a", "land the swarm now", target=LAND, intent="land")
    clean_raw = raw("b", "move north ten")
    records = [
        # The degraded row arrives first and lands on b's clean text.
        to_record(augmented_raw, variant="asr_5db", transcript="move north ten", snr_db=5),
        to_record(clean_raw),
    ]
    kept, _, actions = deduplicate(records, {"a": augmented_raw, "b": clean_raw})

    assert len(kept) == 2
    assert {r["id"]: r["transcript"] for r in kept} == {
        "a": "land the swarm now",
        "b": "move north ten",
    }
    assert {r["id"]: r["target"] for r in kept} == {"a": LAND, "b": MOVE}
    assert actions["reverted_conflict_to_clean"] == 1


def test_reverting_into_a_second_collision_still_terminates():
    """A reverted row is clean, and a clean row is never reverted again."""
    a = raw("a", "land now", target=LAND, intent="land")
    b = raw("b", "move north ten")
    records = [
        to_record(a, variant="asr_5db", transcript="move north ten", snr_db=5),
        to_record(b),
        to_record(raw("c", "land now")),  # collides with a's reverted clean form
    ]
    kept, rejects, actions = deduplicate(records, {"a": a, "b": b})

    assert {r["id"] for r in kept} == {"a", "b"}
    assert actions["dropped_duplicate"] == 0
    assert actions["dropped_conflict"] == 1
    assert any(r["reason"] == "label_conflict_unresolvable_dropped" for r in rejects)


def test_deduplication_is_case_and_punctuation_insensitive():
    records = [
        to_record(raw("a", "move north ten")),
        to_record(raw("b", "Move north, ten.")),
    ]
    kept, _, actions = deduplicate(records, {})
    assert len(kept) == 1
    assert actions["dropped_duplicate"] == 1


def test_distinct_transcripts_are_all_kept():
    records = [to_record(raw(f"r{i}", f"move north {i} metres")) for i in range(25)]
    kept, rejects, _ = deduplicate(records, {})
    assert len(kept) == 25
    assert rejects == []


# --- the real corpus -------------------------------------------------------


@pytest.mark.parametrize("name", ["train", "val", "test_synth"])
def test_split_files_conform_to_the_record_format(name):
    from data.build_splits import SPLIT_FILES

    path = SPLIT_FILES[name]
    if not path.is_file():
        pytest.skip(f"{path.name} not built yet")

    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert rows
    for row in rows:
        assert list(row)[: len(RECORD_KEYS)] == list(RECORD_KEYS), row["id"]
        assert row["split"] == name
        assert isinstance(row["transcript"], str) and row["transcript"].strip()
        assert row["target"].startswith('{"intent":')
        if row["variant"] in ("clean", "perturb"):
            assert row["snr_db"] is None
        else:
            assert row["snr_db"] in (20, 15, 10, 5)


def test_held_out_splits_are_never_augmented():
    """`val` selects checkpoints and `test_synth` is the McNemar paired sample;
    both are measured on reference text (§2.6)."""
    from data.build_splits import SPLIT_FILES

    for name in ("val", "test_synth"):
        path = SPLIT_FILES[name]
        if not path.is_file():
            pytest.skip(f"{path.name} not built yet")
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        assert all(row["variant"] == "clean" for row in rows)
        assert all(row["snr_db"] is None for row in rows)


def test_train_transcripts_are_unique():
    from data.build_splits import SPLIT_FILES

    path = SPLIT_FILES["train"]
    if not path.is_file():
        pytest.skip("train.jsonl not built yet")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    seen = [normalise(row["transcript"]) for row in rows]
    assert len(seen) == len(set(seen))


def test_roundtrip_plan_and_audit_trail_agree():
    from data.build_splits import ROUNDTRIP, RAW_PAIRS, read_jsonl

    if not ROUNDTRIP.is_file():
        pytest.skip("roundtrip.jsonl not built yet")

    train = [r for r in read_jsonl(RAW_PAIRS) if r.get("split") == "train"]
    planned = {i for i, v in assign_variants(train).items() if needs_roundtrip(v)}
    recorded = {r["id"] for r in read_jsonl(ROUNDTRIP)}
    assert planned == recorded
