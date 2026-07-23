"""Tests for intra-annotator test--retest (`data/annotate.py`).

`prd.md` §9.3 is the project's only annotation-quality claim, and it rests on
procedure rather than on arithmetic: the right 50 items, a sealed first pass, and
a second pass the annotator cannot have remembered. The arithmetic is trivial; the
procedure is what these tests hold in place.
"""

from __future__ import annotations

import json
from collections import Counter

import pytest

from data.annotate import (
    SUBSET_SIZE,
    card_block,
    choose_subset,
    compare,
    presentation_order,
    read_golden,
    seal,
    slot_pairs,
    write_pass,
)


@pytest.fixture(scope="module")
def golden():
    return read_golden()


def test_the_subset_is_fifty_items(golden):
    assert len(set(choose_subset(golden))) == SUBSET_SIZE == 50


def test_the_subset_is_stable_across_runs(golden):
    assert choose_subset(golden) == choose_subset(golden)


def test_every_intent_is_represented_including_abort(golden):
    """A uniform draw of 50 from 200 would expect ~2.5 `abort` rows and could
    return none. `abort` is the one intent whose misapplication is a safety
    matter, so it is the one the agreement figure most needs to cover."""
    by_id = {row["id"]: row["gold_intent"] for row in golden}
    counts = Counter(by_id[i] for i in choose_subset(golden))
    assert len(counts) == 10
    assert counts["abort"] >= 2


def test_the_two_passes_see_the_same_items_in_different_orders(golden):
    subset = choose_subset(golden)
    first, second = presentation_order(subset, 1), presentation_order(subset, 2)
    assert set(first) == set(second)
    assert first != second


def test_presentation_order_is_itself_reproducible(golden):
    subset = choose_subset(golden)
    assert presentation_order(subset, 2) == presentation_order(subset, 2)


# --- the seal --------------------------------------------------------------


def _labels(n: int) -> dict[str, dict]:
    return {
        f"{i:04d}": {
            "id": f"{i:04d}",
            "label": 'intent=hover',
            "raw": '{"intent":"hover"}',
            "at": "2026-09-14T20:00:00+01:00",
        }
        for i in range(1, n + 1)
    }


def test_an_incomplete_pass_cannot_be_sealed(tmp_path):
    """Sealing 31 of 50 would leave the agreement figure without a denominator."""
    path = tmp_path / "annot_pass1.jsonl"
    labels = _labels(31)
    write_pass(path, labels, sorted(labels))
    with pytest.raises(SystemExit, match="not 50"):
        seal(path, tmp_path / "seal.json")


def test_sealing_records_the_hash_and_the_moment(tmp_path):
    path, seal_path = tmp_path / "annot_pass1.jsonl", tmp_path / "seal.json"
    labels = _labels(50)
    write_pass(path, labels, sorted(labels))
    assert seal(path, seal_path) == 0
    record = json.loads(seal_path.read_text())
    assert record["items"] == 50
    assert len(record["sha256"]) == 64
    assert record["sealed"]


def test_a_sealed_pass_that_was_edited_afterwards_is_flagged(tmp_path):
    """Pass 1 is the authoritative gold label. Reopening it silently would make
    every downstream number a statement about a file that no longer exists."""
    path, seal_path = tmp_path / "annot_pass1.jsonl", tmp_path / "seal.json"
    labels = _labels(50)
    write_pass(path, labels, sorted(labels))
    seal(path, seal_path)

    labels["0001"]["label"] = "intent=abort"
    write_pass(path, labels, sorted(labels))
    assert seal(path, seal_path) == 1  # non-zero: the file no longer matches its seal


def test_resealing_an_untouched_pass_is_a_no_op(tmp_path):
    path, seal_path = tmp_path / "annot_pass1.jsonl", tmp_path / "seal.json"
    labels = _labels(50)
    write_pass(path, labels, sorted(labels))
    seal(path, seal_path)
    first = seal_path.read_text()
    assert seal(path, seal_path) == 0
    assert seal_path.read_text() == first  # the seal date does not move


# --- the comparison --------------------------------------------------------


def _pass(entries: dict[str, str]) -> dict[str, dict]:
    return {
        item_id: {"id": item_id, "label": raw_to_label(raw), "raw": raw, "at": "2026-09-20T10:00:00+01:00"}
        for item_id, raw in entries.items()
    }


def raw_to_label(raw: str) -> str:
    from schema.canon import canon

    return canon(json.loads(raw))


def test_identical_passes_agree_completely():
    entries = {"0001": '{"intent":"hover"}', "0002": '{"intent":"abort"}'}
    result = compare(_pass(entries), _pass(entries))
    assert result["exact_agreement"] == 1.0
    assert result["intent_agreement"] == 1.0
    assert result["disagreements"] == []


def test_a_slot_that_moved_is_a_disagreement_without_an_intent_change():
    """The interesting disagreements are the ones where the intent held and a
    slot did not --- those localise a schema ambiguity rather than a misreading."""
    first = _pass({"0001": '{"intent":"move","dir":"north","dist":10.0}'})
    second = _pass({"0001": '{"intent":"move","dir":"north","dist":20.0}'})
    result = compare(first, second)
    assert result["exact_agreement"] == 0.0
    assert result["intent_agreement"] == 1.0
    assert result["disagreements"][0]["intent_differs"] is False
    # `dir` held, `dist` moved: partial credit, and intent does not inflate it.
    assert result["slot_f1"] == pytest.approx(0.5)


def test_slot_f1_excludes_intent_so_it_cannot_inflate_agreement():
    """§2.7 defines Slot-F1 "regardless of intent correctness". Counting intent
    as a slot would score a pair that agrees on nothing else at 0.5."""
    first = _pass({"0001": '{"intent":"altitude","z":4.0}'})
    second = _pass({"0001": '{"intent":"altitude","z":5.0}'})
    assert compare(first, second)["slot_f1"] == 0.0


def test_an_intent_that_moved_is_marked_as_such():
    first = _pass({"0001": '{"intent":"hover"}'})
    second = _pass({"0001": '{"intent":"land"}'})
    assert compare(first, second)["disagreements"][0]["intent_differs"] is True


def test_agreement_is_a_fraction_of_the_shared_items():
    first = _pass({"0001": '{"intent":"hover"}', "0002": '{"intent":"abort"}'})
    second = _pass({"0001": '{"intent":"hover"}', "0002": '{"intent":"land"}'})
    result = compare(first, second)
    assert result["n"] == 2
    assert result["exact_agreement"] == 0.5


def test_the_card_block_lists_every_disagreement_not_just_the_count():
    first = _pass({"0001": '{"intent":"hover"}'})
    second = _pass({"0001": '{"intent":"land"}'})
    block = card_block(compare(first, second), gap=6.0)
    assert "6.0 days" in block
    assert "0001" in block  # the reader can judge it rather than take the aggregate


def test_slot_pairs_splits_the_canonical_form():
    assert slot_pairs(raw_to_label('{"intent":"move","dir":"north","dist":10.0}'))


# --- what the card may and may not claim (prd.md SS9.3) --------------------


def test_the_card_never_renders_an_agreement_rate():
    """At a two-day interval a matching pair is as easily recall as schema
    clarity. The rate stays a working number in stdout; the card is what a reader
    sees, and it must not carry a figure the interval cannot support."""
    entries = {f"{i:04d}": '{"intent":"hover"}' for i in range(1, 11)}
    block = card_block(compare(_pass(entries), _pass(entries)), gap=2.0)
    assert "100.0%" not in block and "100%" not in block
    assert "Exact agreement" not in block
    assert "Intent agreement" not in block
    assert "not reported" in block


def test_the_card_states_that_no_disagreement_is_not_a_positive_result():
    """Otherwise the construction is heads-I-win: a clean run would read as
    evidence of clarity when it is evidence of nothing."""
    entries = {"0001": '{"intent":"hover"}'}
    block = card_block(compare(_pass(entries), _pass(entries)), gap=2.0)
    assert "not evidence that the schema is" in block


def test_the_card_calls_the_disagreement_count_a_lower_bound():
    """Recall masks ambiguities a cold reader would have hit, so the count
    understates. Claiming it as complete would overstate the evidence."""
    first = _pass({"0001": '{"intent":"hover"}'})
    second = _pass({"0001": '{"intent":"land"}'})
    block = card_block(compare(first, second), gap=2.0)
    assert "lower bound" in block
    assert "0001" in block


def test_compare_still_computes_the_rates_for_diagnostics():
    """Withheld from the card is not the same as not computed --- the working
    numbers stay available to the author."""
    first = _pass({"0001": '{"intent":"hover"}', "0002": '{"intent":"abort"}'})
    second = _pass({"0001": '{"intent":"hover"}', "0002": '{"intent":"land"}'})
    result = compare(first, second)
    assert result["exact_agreement"] == 0.5
    assert "intent_agreement" in result and "slot_f1" in result
