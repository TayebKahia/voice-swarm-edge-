"""Tests for the training-mix assignment (`data/composition.py`).

The mix is a pre-registered proportion, not an outcome: `02_dataset_plan.md` §4
fixes it before any data exists. These tests hold the implementation to it, and to
the two properties that make the corpus reproducible --- determinism across
processes, and stability under reordering of `raw_pairs.jsonl`.
"""

from __future__ import annotations

import pytest

from data.composition import (
    COMPOSITION,
    DEFAULT_SEED,
    VARIANT_SNR,
    _quota,
    assign_variants,
    needs_roundtrip,
    snr_for,
    tally,
)


def rows(n: int, intents: tuple[str, ...] = ("move", "land", "abort")) -> list[dict]:
    return [
        {"id": f"F{i:03d}-p{i}", "gold_intent": intents[i % len(intents)]} for i in range(n)
    ]


def test_shares_are_the_plan_and_sum_to_one():
    assert COMPOSITION == {
        "clean": 0.50,
        "asr_20db": 0.20,
        "asr_10db": 0.15,
        "asr_5db": 0.10,
        "perturb": 0.05,
    }
    assert sum(COMPOSITION.values()) == pytest.approx(1.0)


def test_snr_mapping_covers_exactly_the_roundtrip_variants():
    assert VARIANT_SNR == {"asr_20db": 20, "asr_10db": 10, "asr_5db": 5}
    assert all(needs_roundtrip(v) for v in VARIANT_SNR)
    assert not needs_roundtrip("clean")
    assert not needs_roundtrip("perturb")
    assert snr_for("clean") is None


def test_quota_is_exact_and_uses_largest_remainder():
    """Independent rounding loses rows; the split has to account for all of them."""
    for n in (1, 7, 13, 100, 1941):
        counts = _quota(n, COMPOSITION)
        assert sum(counts.values()) == n
        for name, share in COMPOSITION.items():
            assert abs(counts[name] - n * share) <= 1


def test_assignment_covers_every_row_exactly_once():
    data = rows(500)
    assignment = assign_variants(data)
    assert set(assignment) == {r["id"] for r in data}
    assert set(assignment.values()) <= set(COMPOSITION)


def test_realised_shares_match_the_plan():
    data = rows(1941)
    counts = tally(assign_variants(data).values())
    for name, share in COMPOSITION.items():
        assert counts[name] / len(data) == pytest.approx(share, abs=0.005)


def test_every_intent_gets_the_mix():
    """Unstratified, `abort` --- smallest and most safety-critical --- could come
    out all-clean and never see a degraded transcript."""
    data = [
        {"id": f"a{i}", "gold_intent": "abort"} for i in range(40)
    ] + [{"id": f"m{i}", "gold_intent": "move"} for i in range(900)]

    assignment = assign_variants(data)
    for intent in ("abort", "move"):
        counts = tally(
            assignment[r["id"]] for r in data if r["gold_intent"] == intent
        )
        total = sum(1 for r in data if r["gold_intent"] == intent)
        for name, share in COMPOSITION.items():
            assert counts[name] / total == pytest.approx(share, abs=0.03), (intent, name)


def test_assignment_is_deterministic():
    data = rows(300)
    assert assign_variants(data) == assign_variants(data)


def test_assignment_survives_reordering_of_the_corpus():
    """Regenerating `raw_pairs.jsonl` must not re-roll every variant and invalidate
    the cached round-trip audio."""
    data = rows(300)
    shuffled = list(reversed(data))
    assert assign_variants(data) == assign_variants(shuffled)


def test_seed_changes_the_assignment():
    data = rows(300)
    assert assign_variants(data, seed=DEFAULT_SEED) != assign_variants(data, seed=7)


def test_adding_a_row_perturbs_few_existing_assignments():
    """Ids are ordered by a stable hash, so one new row shifts at most a boundary
    inside its own stratum rather than re-rolling the corpus."""
    data = rows(600)
    before = assign_variants(data)
    after = assign_variants(data + [{"id": "zzz-new", "gold_intent": "move"}])

    changed = sum(1 for k, v in before.items() if after[k] != v)
    assert changed <= len(COMPOSITION)
