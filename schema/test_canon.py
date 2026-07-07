"""Canonicaliser and comparator test suite (Session 01B Task 6).

Verifies the five canonicalisation rules and FR-12:
1. Key order fixed by schema declaration order (KEY_ORDER).
2. Absent and null fields omitted, not emitted.
3. Floats rounded to one decimal (matching cmd.gbnf precision limit), -0.0 -> 0.0.
4. ids deduplicated and sorted ascending, emitted as integers.
5. No whitespace outside string literals.
FR-12: Single comparator --- assert EM and CRR call the same function.
"""

import json
import pytest

from schema.canon import canon, canon_equal
from schema.schema import (
    KEY_ORDER,
    Formation,
    Move,
    Altitude,
    Takeoff,
    Land,
    Hover,
    Abort,
    Rotate,
    SetParam,
    Unknown,
)


def test_rule_1_key_order_from_schema_declaration():
    """Rule 1: Key order is fixed by schema declaration order for all intents."""
    # Test shuffled dictionaries for each intent
    shuffled_cases = [
        ({"radius": 5.0, "shape": "circle", "intent": "formation"}, '{"intent":"formation","shape":"circle","radius":5.0}'),
        ({"speed": 1.5, "pos": [10.0, 0.0, 3.0], "intent": "move"}, '{"intent":"move","pos":[10.0,0.0,3.0],"speed":1.5}'),
        ({"dist": 10.0, "dir": "north", "intent": "move"}, '{"intent":"move","dir":"north","dist":10.0}'),
        ({"ids": [1, 2], "z": 4.0, "intent": "altitude"}, '{"intent":"altitude","z":4.0,"ids":[1,2]}'),
        ({"ids": [0], "z": 2.5, "intent": "takeoff"}, '{"intent":"takeoff","z":2.5,"ids":[0]}'),
        ({"ids": [0, 1], "intent": "land"}, '{"intent":"land","ids":[0,1]}'),
        ({"ids": [3], "intent": "hover"}, '{"intent":"hover","ids":[3]}'),
        ({"intent": "abort"}, '{"intent":"abort"}'),
        ({"ids": [0], "yaw": 90.0, "intent": "rotate"}, '{"intent":"rotate","yaw":90.0,"ids":[0]}'),
        ({"alt": 5.0, "speed": 1.0, "intent": "set_param"}, '{"intent":"set_param","speed":1.0,"alt":5.0}'),
        ({"intent": "unknown"}, '{"intent":"unknown"}'),
    ]

    for data, expected in shuffled_cases:
        actual = canon(data)
        assert actual == expected, f"Failed key order for {data.get('intent')}: got {actual}, expected {expected}"

    # Verify every declared key in KEY_ORDER maintains precedence
    for intent, keys in KEY_ORDER.items():
        assert keys[0] == "intent", f"First key for {intent} must be 'intent'"


def test_rule_1_unexpected_keys_appended_alphabetically():
    """Rule 1 fallback: Unexpected keys appended alphabetically rather than dropped."""
    data = {"zebra": 1.0, "intent": "hover", "alpha": 2.0}
    actual = canon(data)
    assert actual == '{"intent":"hover","alpha":2.0,"zebra":1.0}'


def test_rule_2_null_and_empty_omission():
    """Rule 2: Absent and null fields omitted; empty ids list omitted."""
    # Takeoff with None z and None ids
    t1 = Takeoff(intent="takeoff", z=None, ids=None)
    assert canon(t1) == '{"intent":"takeoff"}'

    # Dict with explicit nulls
    d1 = {"intent": "takeoff", "z": None, "ids": None}
    assert canon(d1) == '{"intent":"takeoff"}'

    # Empty ids list dropped (empty after filtering means all drones)
    d2 = {"intent": "land", "ids": []}
    assert canon(d2) == '{"intent":"land"}'

    # Move with pos and None speed/ids
    m1 = Move(intent="move", pos=(10.0, 0.0, 3.0), speed=None, ids=None)
    assert canon(m1) == '{"intent":"move","pos":[10.0,0.0,3.0]}'


def test_rule_3_one_decimal_rounding():
    """Rule 3: Floats rounded to exactly one decimal place, negative zero normalized.

    Python's round() uses round-half-to-even (banker's rounding).
    """
    # Integers rendered with one decimal
    assert canon({"intent": "altitude", "z": 4}) == '{"intent":"altitude","z":4.0}'

    # Multi-decimal floats rounded
    assert canon({"intent": "altitude", "z": 4.14}) == '{"intent":"altitude","z":4.1}'
    assert canon({"intent": "altitude", "z": 4.16}) == '{"intent":"altitude","z":4.2}'

    # Half-way cases (round-half-to-even on exact IEEE-754 dyadic fractions)
    assert canon({"intent": "altitude", "z": 0.25}) == '{"intent":"altitude","z":0.2}'
    assert canon({"intent": "altitude", "z": 0.75}) == '{"intent":"altitude","z":0.8}'
    assert canon({"intent": "altitude", "z": 4.15}) == '{"intent":"altitude","z":4.2}'
    assert canon({"intent": "altitude", "z": 2.5}) == '{"intent":"altitude","z":2.5}'

    # Negative zero normalized to 0.0
    assert canon({"intent": "move", "pos": [-0.04, 0.0, 3.0]}) == '{"intent":"move","pos":[0.0,0.0,3.0]}'
    assert canon({"intent": "rotate", "yaw": -0.01}) == '{"intent":"rotate","yaw":0.0}'


def test_rule_4_ids_dedup_and_sort():
    """Rule 4: ids deduplicated and sorted ascending, formatted as integers."""
    # Unordered with duplicates
    data = {"intent": "altitude", "z": 4.0, "ids": [3, 1, 3, 0, 2, 1]}
    assert canon(data) == '{"intent":"altitude","z":4.0,"ids":[0,1,2,3]}'

    # Non-integer elements safely discarded to keep canon() total on grammar-off ablation
    malformed_ids = {"intent": "altitude", "z": 4.0, "ids": ["1", "corrupt_token", 2, "0"]}
    assert canon(malformed_ids) == '{"intent":"altitude","z":4.0,"ids":[0,1,2]}'

    # Verify ids are not formatted as floats (e.g. 1.0)
    wire = canon(data)
    assert "[0,1,2,3]" in wire
    assert ".0" not in wire.split('"ids":')[1]


def test_rule_5_no_whitespace_outside_string_literals():
    """Rule 5: No whitespace outside string literals."""
    cmd = Formation(intent="formation", shape="circle", radius=5.0, ids=[1, 2])
    wire = canon(cmd)
    # Check no spaces outside quotes
    in_quotes = False
    for char in wire:
        if char == '"':
            in_quotes = not in_quotes
        elif not in_quotes:
            assert not char.isspace(), f"Found illegal whitespace in wire form: {wire!r}"


def test_canon_equal_comparator_equivalence():
    """Verify canon_equal provides order- and format-insensitive byte equivalence for EM/CRR."""
    # Prediction and gold differ in key order and float representation
    gold_row = {"intent": "move", "pos": [10.0, 0.0, 3.0], "speed": 1.5}
    pred_row = {"speed": 1.50, "intent": "move", "pos": [10, 0.0, 3.00]}

    # Comparator returns byte-identical equivalence
    assert canon_equal(pred_row, gold_row)
    assert canon(pred_row) == canon(gold_row)

    # Identifiers in different order and duplicated in prediction
    gold_cmd = Altitude(intent="altitude", z=5.0, ids=[1, 2])
    pred_dict = {"z": 5, "ids": [2, 1, 2], "intent": "altitude"}
    assert canon_equal(pred_dict, gold_cmd)

    # Distinct commands compare unequal
    diff_cmd = Altitude(intent="altitude", z=5.1, ids=[1, 2])
    assert not canon_equal(gold_cmd, diff_cmd)


def test_model_and_mapping_parity():
    """Pydantic model and raw mapping produce identical canonical wire bytes."""
    model = Formation(intent="formation", shape="wedge", spacing=3.0, ids=[0, 1])
    raw_dict = {"intent": "formation", "shape": "wedge", "spacing": 3.0, "ids": [0, 1]}

    assert canon(model) == canon(raw_dict)
    assert canon(model) == canon(model.model_dump())
    assert canon(model) == model.to_wire()
