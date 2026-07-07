"""Tests for template families and split leakage verification (data/)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from data.check_leakage import (
    check_dataset_split_leakage,
    check_template_family_integrity,
    jaccard_similarity,
    normalize_transcript,
)
from data.template_families import (
    FAMILIES,
    FAMILIES_JSON_PATH,
    FAMILY_MAP,
    TEST_FAMILIES,
    TRAIN_FAMILIES,
    VAL_FAMILIES,
    TemplateFamily,
)
from schema.schema import INTENTS


def test_template_families_total_and_split_counts():
    """Verify exactly 120 families with 96 train (80%), 12 val (10%), 12 test_synth (10%)."""
    assert len(FAMILIES) == 120
    assert len(TRAIN_FAMILIES) == 96
    assert len(VAL_FAMILIES) == 12
    assert len(TEST_FAMILIES) == 12


def test_template_families_ids_unique():
    """Verify all 120 family IDs are unique and well-formed (F001 ... F120)."""
    ids = [f.family_id for f in FAMILIES]
    assert len(ids) == len(set(ids))
    assert ids[0] == "F001"
    assert ids[-1] == "F120"


def test_json_and_python_definitions_synchronized():
    """Verify data/template_families.json matches data/template_families.py exactly."""
    assert FAMILIES_JSON_PATH.is_file(), f"Missing {FAMILIES_JSON_PATH}"
    with open(FAMILIES_JSON_PATH, encoding="utf-8") as fp:
        json_data = json.load(fp)

    py_data = [asdict(f) for f in FAMILIES]
    assert json_data == py_data, "data/template_families.json has drifted from template_families.py"


def test_all_intents_represented_in_val_and_test():
    """Verify that every intent appears in both validation and held-out test splits."""
    val_intents = {f.intent for f in VAL_FAMILIES}
    test_intents = {f.intent for f in TEST_FAMILIES}

    for intent in INTENTS:
        assert intent in val_intents, f"Intent {intent!r} missing from val families"
        assert intent in test_intents, f"Intent {intent!r} missing from test_synth families"


def test_check_leakage_on_valid_families():
    """Verify check_template_family_integrity reports zero errors on canonical families."""
    errors = check_template_family_integrity(FAMILIES_JSON_PATH)
    assert errors == []


def test_check_leakage_detects_surface_form_and_family_overlap():
    """Verify check_dataset_split_leakage flags exact matches, near-duplicates, and family ID collisions."""
    train_rows = [
        {"family_id": "F001", "transcript": "swarm circle with radius five meters"},
        {"family_id": "F006", "transcript": "form a line with two meter spacing"},
    ]

    # Exact match leakage
    exact_leak_rows = [
        {"family_id": "F004", "transcript": "swarm circle with radius five meters"}
    ]
    errors_exact = check_dataset_split_leakage(train_rows, exact_leak_rows, "val")
    assert any("Exact transcript match" in e for e in errors_exact)

    # Near-duplicate leakage
    near_leak_rows = [
        {"family_id": "F004", "transcript": "swarm circle radius five meters"}
    ]
    errors_near = check_dataset_split_leakage(train_rows, near_leak_rows, "val", sim_threshold=0.75)
    assert any("near-duplicate" in e for e in errors_near)

    # Cross-split family ID overlap
    id_leak_rows = [
        {"family_id": "F001", "transcript": "completely distinct phrasing for holding pattern"}
    ]
    errors_id = check_dataset_split_leakage(train_rows, id_leak_rows, "val")
    assert any("Family ID leakage" in e for e in errors_id)
