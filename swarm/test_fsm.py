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
