"""Flight state machine and Table 9 legality test suite (PRD Sec. 5.3, Table 9).

Verifies Table 9 legality, state transitions, rejection fallback to HOVER,
abort no-op handling, and manual non-vocal recovery from ABORTED.
"""

import pytest

from schema.schema import Abort, Hover, Move, Takeoff
from swarm.fsm import FlightState, FlightStateMachine, TABLE_9_LEGALITY


def test_initial_state_is_landed():
    """Default state machine starts in LANDED."""
    fsm = FlightStateMachine()
    assert fsm.state == FlightState.LANDED


def test_takeoff_transition():
    """takeoff in LANDED transitions to TAKING_OFF."""
    fsm = FlightStateMachine(FlightState.LANDED)
    res = fsm.handle_command('{"intent":"takeoff","z":2.5}')
    assert isinstance(res, Takeoff)
    assert fsm.state == FlightState.TAKING_OFF


def test_altitude_reached_transition():
    """TAKING_OFF transitions to FLYING when altitude is attained."""
    fsm = FlightStateMachine(FlightState.TAKING_OFF)
    fsm.on_altitude_reached()
    assert fsm.state == FlightState.FLYING


def test_land_transition():
    """land in FLYING transitions to LANDING."""
    fsm = FlightStateMachine(FlightState.FLYING)
    res = fsm.handle_command('{"intent":"land"}')
    assert res is not None
    assert res.intent == "land"
    assert fsm.state == FlightState.LANDING


def test_ground_contact_transition():
    """LANDING transitions to LANDED on ground contact."""
    fsm = FlightStateMachine(FlightState.LANDING)
    fsm.on_ground_contact()
    assert fsm.state == FlightState.LANDED


def test_abort_from_airborne_states():
    """abort from any airborne state transitions to ABORTED."""
    for state in (FlightState.TAKING_OFF, FlightState.FLYING, FlightState.LANDING):
        fsm = FlightStateMachine(state)
        res = fsm.handle_command('{"intent":"abort"}')
        assert isinstance(res, Abort)
        assert fsm.state == FlightState.ABORTED


def test_abort_in_landed_or_aborted_is_logged_noop():
    """abort in LANDED or ABORTED is a logged no-op, never an error."""
    for state in (FlightState.LANDED, FlightState.ABORTED):
        fsm = FlightStateMachine(state)
        res = fsm.handle_command('{"intent":"abort"}')
        assert res is None
        assert fsm.state == state


def test_unknown_never_dispatched():
    """unknown is logged only, never dispatched."""
    fsm = FlightStateMachine(FlightState.FLYING)
    res = fsm.handle_command('{"intent":"unknown"}')
    assert res is None
    assert fsm.state == FlightState.FLYING


@pytest.mark.parametrize(
    "intent, legal_states, illegal_states",
    [
        ("takeoff", [FlightState.LANDED], [FlightState.TAKING_OFF, FlightState.FLYING, FlightState.LANDING, FlightState.ABORTED]),
        ("land", [FlightState.TAKING_OFF, FlightState.FLYING], [FlightState.LANDED, FlightState.LANDING, FlightState.ABORTED]),
        ("hover", [FlightState.TAKING_OFF, FlightState.FLYING], [FlightState.LANDED, FlightState.LANDING, FlightState.ABORTED]),
        ("move", [FlightState.FLYING], [FlightState.LANDED, FlightState.TAKING_OFF, FlightState.LANDING, FlightState.ABORTED]),
        ("altitude", [FlightState.FLYING], [FlightState.LANDED, FlightState.TAKING_OFF, FlightState.LANDING, FlightState.ABORTED]),
        ("rotate", [FlightState.FLYING], [FlightState.LANDED, FlightState.TAKING_OFF, FlightState.LANDING, FlightState.ABORTED]),
        ("formation", [FlightState.FLYING], [FlightState.LANDED, FlightState.TAKING_OFF, FlightState.LANDING, FlightState.ABORTED]),
        ("set_param", [FlightState.LANDED, FlightState.TAKING_OFF, FlightState.FLYING, FlightState.LANDING], [FlightState.ABORTED]),
    ],
)
def test_table_9_legality(intent: str, legal_states: list[FlightState], illegal_states: list[FlightState]):
    """Table 9: Check legality across all defined states."""
    fsm = FlightStateMachine()
    for state in legal_states:
        assert fsm.is_legal(intent, state), f"{intent} should be legal in {state}"
    for state in illegal_states:
        assert not fsm.is_legal(intent, state), f"{intent} should be illegal in {state}"


def test_rejection_resolves_to_hover_when_airborne():
    """Illegal command in airborne state (FLYING) resolves to HOVER fallback."""
    fsm = FlightStateMachine(FlightState.FLYING)
    # takeoff in FLYING is illegal -> resolves to HOVER
    res = fsm.handle_command('{"intent":"takeoff"}')
    assert isinstance(res, Hover)
    assert fsm.state == FlightState.FLYING


def test_rejection_in_landed_is_grounded_noop():
    """Illegal command in LANDED (e.g. move) refuses to HOVER and remains safe grounded no-op."""
    fsm = FlightStateMachine(FlightState.LANDED)
    res = fsm.handle_command('{"intent":"move","pos":[10.0,0.0,3.0]}')
    assert res is None
    assert fsm.state == FlightState.LANDED


def test_manual_reset_from_aborted():
    """Manual reset requires ground contact and zero velocity."""
    fsm = FlightStateMachine(FlightState.ABORTED)

    # Refused if airborne or moving
    assert not fsm.manual_reset(all_ground_contact=False, all_near_zero_velocity=False)
    assert fsm.state == FlightState.ABORTED

    assert not fsm.manual_reset(all_ground_contact=True, all_near_zero_velocity=False)
    assert fsm.state == FlightState.ABORTED

    # Accepted when all drones on ground and near-zero velocity
    assert fsm.manual_reset(all_ground_contact=True, all_near_zero_velocity=True)
    assert fsm.state == FlightState.LANDED


def test_rejection_in_landing_is_noop_not_hover():
    """Regression: illegal command during descent returns None, not HOVER.

    Table 9 forbids hover in LANDING, so a rejection in LANDING must NOT
    dispatch HOVER — that would arrest the descent at altitude.  Returning
    None lets the landing finish uninterrupted.
    """
    fsm = FlightStateMachine(FlightState.LANDING)
    # move is illegal in LANDING
    res = fsm.handle_command('{"intent":"move","pos":[10.0,0.0,3.0]}')
    assert res is None, "rejection in LANDING must return None, not Hover"
    assert fsm.state == FlightState.LANDING


@pytest.mark.parametrize("intent_json", [
    '{"intent":"takeoff"}',
    '{"intent":"altitude","z":5.0}',
    '{"intent":"rotate","yaw":90.0}',
    '{"intent":"formation","shape":"circle","radius":5.0}',
    '{"intent":"hover"}',
    '{"intent":"land"}',
])
def test_all_illegal_intents_in_landing_return_none(intent_json: str):
    """Every illegal intent in LANDING resolves to None, never HOVER."""
    fsm = FlightStateMachine(FlightState.LANDING)
    res = fsm.handle_command(intent_json)
    assert res is None, f"rejection of {intent_json} in LANDING must be None"
    assert fsm.state == FlightState.LANDING


def test_rejection_in_aborted_is_noop():
    """Illegal command in ABORTED returns None (hover is illegal there too)."""
    fsm = FlightStateMachine(FlightState.ABORTED)
    res = fsm.handle_command('{"intent":"move","pos":[10.0,0.0,3.0]}')
    assert res is None
    assert fsm.state == FlightState.ABORTED


def test_rejection_in_taking_off_resolves_to_hover():
    """Table 9 permits hover in TAKING_OFF, so rejection there gives HOVER."""
    fsm = FlightStateMachine(FlightState.TAKING_OFF)
    # move is illegal in TAKING_OFF
    res = fsm.handle_command('{"intent":"move","pos":[10.0,0.0,3.0]}')
    assert isinstance(res, Hover)
    assert fsm.state == FlightState.TAKING_OFF


def test_handle_command_accepts_pydantic_model_directly():
    """Regression (Defect B): handle_command accepts typed Pydantic models without TypeError."""
    from schema.schema import Altitude, Hover
    fsm = FlightStateMachine(FlightState.FLYING)
    res = fsm.handle_command(Altitude(intent="altitude", z=4.0))
    assert isinstance(res, Altitude)
    assert res.z == 4.0


def test_invalid_string_command_preserves_raw_intent_in_rejection_log(caplog):
    """Regression (Defect A & C): invalid string move in TAKING_OFF logs rejection with raw intent 'move'."""
    import logging
    fsm = FlightStateMachine(FlightState.TAKING_OFF)
    with caplog.at_level(logging.WARNING, logger="swarm.fsm"):
        # Syntactically invalid move (missing pos and dir/dist) -> Layer 2 falls back to Hover
        # But FSM must inspect raw_intent ('move') and log rejection of 'move' in TAKING_OFF!
        res = fsm.handle_command('{"intent":"move"}')
    
    assert isinstance(res, Hover)
    # Verify that the log message and structured record preserved 'move' rather than 'hover'
    records = [r for r in caplog.records if r.name == "swarm.fsm" and getattr(r, "event", None) == "fsm_command_rejected"]
    assert len(records) == 1
    assert getattr(records[0], "intent") == "move"
    assert getattr(records[0], "state") == "TAKING_OFF"



# =====================================================================
#  Gate 4 --- the Table 9 cell-coverage proof (FR-11)
#
#  The tests above exercise Table 9 in places; FR-11 asks for every
#  cell. "Every cell" is 5 flight states x 10 intents = 50, and the
#  proof has to be structural rather than a count somebody maintains by
#  hand: the parametrisation below is *generated* from the cross
#  product, so a cell cannot be missed without the generator changing.
#
#  Three things are separated deliberately, because each can be wrong
#  on its own:
#
#    1. TABLE_9_AS_SPECIFIED  -- Table 9 transcribed from prd.md Sec.
#       5.3 into this file, by hand, keyed on *strings*. It never
#       imports fsm.py's own table, or it would agree with it by
#       construction and prove nothing.
#    2. A cross-check of that transcription against prd.md itself,
#       parsed at run time. prd.md is untracked by design (roadmap
#       Sec. 0.4a), so this one skips rather than fails when the file
#       is absent -- it is a guard against a typo here, not a
#       dependency.
#    3. The 50-cell behavioural sweep through handle_command: what is
#       dispatched, what the state becomes, and the log entry.
# =====================================================================

import json
import logging
import re
from pathlib import Path

from schema.schema import INTENTS
from schema.validate import validate

ALL_STATE_NAMES = frozenset(s.value for s in FlightState)

# prd.md Sec. 5.3, Table 9, "Legal in" column, transcribed verbatim.
TABLE_9_AS_SPECIFIED: dict[str, frozenset[str]] = {
    "takeoff": frozenset({"LANDED"}),
    "land": frozenset({"TAKING_OFF", "FLYING"}),
    "hover": frozenset({"TAKING_OFF", "FLYING"}),
    "abort": frozenset({"TAKING_OFF", "FLYING", "LANDING"}),
    "move": frozenset({"FLYING"}),
    "altitude": frozenset({"FLYING"}),
    "rotate": frozenset({"FLYING"}),
    "formation": frozenset({"FLYING"}),
    "set_param": ALL_STATE_NAMES - {"ABORTED"},
    "unknown": frozenset(),  # "--" : never dispatched, logged only
}

# One canonical, Layer-2-clean payload per intent. These must pass
# validate() unchanged -- see test_every_cell_payload_survives_layer_2.
# A payload that fell back to Hover inside Layer 2 would make a cell
# below pass for the wrong reason.
VALID_PAYLOAD: dict[str, str] = {
    "takeoff": '{"intent":"takeoff","z":2.5}',
    "land": '{"intent":"land"}',
    "hover": '{"intent":"hover"}',
    "abort": '{"intent":"abort"}',
    "move": '{"intent":"move","pos":[10.0,0.0,3.0]}',
    "altitude": '{"intent":"altitude","z":5.0}',
    "rotate": '{"intent":"rotate","yaw":90.0}',
    "formation": '{"intent":"formation","shape":"circle","radius":5.0}',
    "set_param": '{"intent":"set_param","speed":1.0}',
    "unknown": '{"intent":"unknown"}',
}

# The cell matrix. Generated, never enumerated.
CELLS = [(state, intent) for state in FlightState for intent in INTENTS]
CELL_IDS = [f"{state.value}-{intent}" for state, intent in CELLS]


def _parse_table_9_from_prd() -> dict[str, frozenset[str]] | None:
    """Parse Table 9's "Legal in" column out of prd.md, or None if absent."""
    prd = Path(__file__).resolve().parent.parent / "prd.md"
    if not prd.exists():
        return None

    lines = prd.read_text(encoding="utf-8").splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.startswith("### Table 9")), None
    )
    if start is None:
        return None

    rows: list[list[str]] = []
    for line in lines[start:]:
        if not line.lstrip().startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= set(": -") for c in cells):  # the --- separator row
            continue
        rows.append(cells)

    if len(rows) < 2:
        return None
    rows = rows[1:]  # drop the header

    parsed: dict[str, frozenset[str]] = {}
    for intent_cell, legal_cell, *_ in rows:
        named = frozenset(re.findall(r"`([A-Z_]+)`", legal_cell))
        if "Every state except" in legal_cell:
            legal = ALL_STATE_NAMES - named
        else:
            legal = named  # a bare em dash yields the empty set
        for intent in re.findall(r"`([a-z_]+)`", intent_cell):
            parsed[intent] = legal
    return parsed


def test_table_9_transcription_is_complete():
    """The transcription covers the ten frozen intents and only real states."""
    assert set(TABLE_9_AS_SPECIFIED) == set(INTENTS)
    for intent, states in TABLE_9_AS_SPECIFIED.items():
        assert states <= ALL_STATE_NAMES, f"{intent} names a state that does not exist"


def test_transcription_matches_prd_table_9():
    """Guard the hand transcription against prd.md itself.

    prd.md is untracked by design, so this skips on a clean clone rather
    than failing: it protects against a typo in this file, and is not a
    dependency of the suite.
    """
    parsed = _parse_table_9_from_prd()
    if parsed is None:
        pytest.skip("prd.md not present (untracked by design); transcription unchecked")
    assert parsed == TABLE_9_AS_SPECIFIED


def test_fsm_table_matches_the_specification():
    """swarm/fsm.py's TABLE_9_LEGALITY is Table 9, cell for cell."""
    as_implemented = {
        intent: frozenset(s.value for s in states)
        for intent, states in TABLE_9_LEGALITY.items()
    }
    assert as_implemented == TABLE_9_AS_SPECIFIED


def test_the_cell_matrix_is_the_complete_cross_product():
    """The sweep below runs on every state x intent pair, all fifty."""
    assert len(CELLS) == len(FlightState) * len(INTENTS) == 50
    assert set(CELLS) == {(s, i) for s in FlightState for i in INTENTS}


@pytest.mark.parametrize("intent", INTENTS)
def test_every_cell_payload_survives_layer_2(intent: str):
    """Each sweep payload reaches Layer 3 as itself, not as a Layer-2 Hover."""
    assert validate(VALID_PAYLOAD[intent]).intent == intent
    assert json.loads(VALID_PAYLOAD[intent])["intent"] == intent


def _expected_state_after(state: FlightState, intent: str, legal: bool) -> FlightState:
    """Table 9's transitions, restated independently of fsm.py."""
    if not legal:
        return state
    if intent == "abort":
        return FlightState.ABORTED
    if intent == "takeoff":
        return FlightState.TAKING_OFF
    if intent == "land":
        return FlightState.LANDING
    return state


@pytest.mark.parametrize("state, intent", CELLS, ids=CELL_IDS)
def test_table_9_cell(state: FlightState, intent: str, caplog):
    """One Table 9 cell: what is dispatched, the state after, the log entry.

    Rejections resolve to HOVER with a log entry wherever Table 9 permits
    hovering. In LANDED, LANDING and ABORTED -- the three states where
    Table 9 declares `hover` itself illegal -- the fallback is a logged
    no-op instead, per ADR-0002: dispatching HOVER there would spin up a
    grounded swarm, arrest a descent at altitude, or fly out of an abort.
    Either way a rejection is never silent and never a movement command.
    """
    legal = state.value in TABLE_9_AS_SPECIFIED[intent]
    hover_legal_here = state.value in TABLE_9_AS_SPECIFIED["hover"]

    fsm = FlightStateMachine(state)
    with caplog.at_level(logging.INFO, logger="swarm.fsm"):
        res = fsm.handle_command(VALID_PAYLOAD[intent])

    events = [
        r for r in caplog.records
        if r.name == "swarm.fsm" and getattr(r, "event", None) is not None
    ]
    event_names = [r.event for r in events]

    if intent == "unknown":
        # "Never dispatched; logged only."
        assert res is None
        assert event_names == ["fsm_unknown_logged"]
    elif intent == "abort" and not legal:
        # "accepted as a logged no-op, never an error"
        assert res is None
        assert event_names == ["fsm_abort_noop"]
    elif legal:
        assert res is not None, f"{intent} is legal in {state.value} and must dispatch"
        assert res.intent == intent
        assert "fsm_command_rejected" not in event_names
    else:
        rejections = [r for r in events if r.event == "fsm_command_rejected"]
        assert len(rejections) == 1, "a rejection is logged exactly once"
        assert rejections[0].intent == intent, "the log names the rejected intent"
        assert rejections[0].state == state.value
        if hover_legal_here:
            assert isinstance(res, Hover), "rejection resolves to HOVER"
        else:
            assert res is None, "hover is illegal here: safe no-op instead (ADR-0002)"

    assert fsm.state == _expected_state_after(state, intent, legal)
    assert res is None or res.intent != "unknown", "unknown is never dispatched"


@pytest.mark.parametrize("state", list(FlightState), ids=[s.value for s in FlightState])
def test_no_rejection_is_ever_silent(state: FlightState):
    """Every rejection in every state carries a structured log entry.

    The per-cell test asserts this cell by cell; this asserts it as the
    property Gate 4 is actually about, in one place a reader can check.
    """
    rejected = [i for i in INTENTS if state.value not in TABLE_9_AS_SPECIFIED[i]]
    for intent in rejected:
        fsm = FlightStateMachine(state)
        caplog_records: list[logging.LogRecord] = []
        handler = logging.Handler()
        handler.emit = caplog_records.append  # type: ignore[method-assign]
        log = logging.getLogger("swarm.fsm")
        log.addHandler(handler)
        try:
            res = fsm.handle_command(VALID_PAYLOAD[intent])
        finally:
            log.removeHandler(handler)

        assert any(getattr(r, "event", None) for r in caplog_records), (
            f"{intent} rejected in {state.value} with no structured log entry"
        )
        assert res is None or isinstance(res, Hover), (
            f"{intent} rejected in {state.value} resolved to {res!r}, "
            "which is neither HOVER nor a no-op"
        )


def test_recovery_out_of_aborted_is_reachable_only_off_the_voice_path():
    """FR-11's explicit non-vocal recovery path.

    ABORTED is a dead end for every one of the ten intents -- the loop
    below is the proof -- and manual_reset() is the only way out.
    """
    for intent in INTENTS:
        fsm = FlightStateMachine(FlightState.ABORTED)
        fsm.handle_command(VALID_PAYLOAD[intent])
        assert fsm.state == FlightState.ABORTED, f"{intent} escaped ABORTED by voice"

    fsm = FlightStateMachine(FlightState.ABORTED)
    assert fsm.manual_reset(all_ground_contact=True, all_near_zero_velocity=True)
    assert fsm.state == FlightState.LANDED
