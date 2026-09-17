"""swarm/link.py -- the link from the state machine to the controller, on the kinematic backend.

The script of Chapter 6's demonstration (tab:demo-script) is run through a real
`FlightStateMachine` and a real `SwarmController`, in simulated time, and each step is checked
against the row's "State after" and "Expected behaviour". The speech side is not involved: the
commands are the ones the parser is expected to publish for each utterance.
"""

from __future__ import annotations

import numpy as np
import pytest

from schema.validate import validate
from swarm.control import CLAMP_DISTANCE
from swarm.fsm import FlightState, FlightStateMachine
from swarm.link import GROUND_Z, GroundNumpyEnv, Link, ground_layout


def _link() -> Link:
    env = GroundNumpyEnv()
    env.reset(0)
    return Link(env, FlightStateMachine(), clamp=True)


def _send(link: Link, raw: dict) -> str | None:
    """What the consumer does with one bus message: FSM first, then the link."""
    before = link.fsm.state
    cmd = link.fsm.handle_command(validate(raw))
    return None if cmd is None else link.dispatch(cmd, before)


def _run(link: Link, seconds: float) -> None:
    for _ in range(int(round(seconds / link.env.dt))):
        link.tick()


def _airborne(link: Link, z: float = 5.0) -> None:
    _send(link, {"intent": "takeoff", "z": z})
    _run(link, 10)
    assert link.fsm.state == FlightState.FLYING


def test_starts_landed_on_the_ground_with_motors_off():
    link = _link()
    _run(link, 1)
    assert link.fsm.state == FlightState.LANDED
    assert not link.motors_on
    np.testing.assert_allclose(link.env.positions, ground_layout())


def test_step1_takeoff_climbs_to_height_and_reports_altitude_reached():
    link = _link()
    _send(link, {"intent": "takeoff", "z": 5.0})
    assert link.fsm.state == FlightState.TAKING_OFF
    _run(link, 10)
    assert link.fsm.state == FlightState.FLYING
    np.testing.assert_allclose(link.env.positions[:, 2], 5.0, atol=0.2)
    # climbed in place: the ground layout's x/y are kept
    np.testing.assert_allclose(link.env.positions[:, :2], ground_layout()[:, :2], atol=0.3)


def test_step2_circle_of_radius_five():
    link = _link()
    _airborne(link)
    _send(link, {"intent": "formation", "shape": "circle", "radius": 5.0})
    _run(link, 15)
    positions = link.env.positions
    centroid = positions.mean(axis=0)
    radii = np.linalg.norm(positions[:, :2] - centroid[:2], axis=1)
    np.testing.assert_allclose(radii, 5.0, atol=0.5)
    np.testing.assert_allclose(positions[:, 2], 5.0, atol=0.5)


def test_step3_move_north_ten_metres_keeps_the_formation():
    link = _link()
    _airborne(link)
    _send(link, {"intent": "formation", "shape": "circle", "radius": 5.0})
    _run(link, 15)
    before = link.env.positions
    _send(link, {"intent": "move", "dir": "north", "dist": 10.0})
    _run(link, 15)
    shift = link.env.positions - before
    np.testing.assert_allclose(shift[:, 1], 10.0, atol=0.5)
    np.testing.assert_allclose(shift[:, [0, 2]], 0.0, atol=0.5)


def test_step4_hold_stops_lateral_motion_and_holds_altitude():
    link = _link()
    _airborne(link)
    _send(link, {"intent": "formation", "shape": "circle", "radius": 5.0})
    _run(link, 0.5)                     # mid-manoeuvre
    _send(link, {"intent": "hover"})
    held = link.controller.targets
    _run(link, 10)
    assert link.fsm.state == FlightState.FLYING
    np.testing.assert_allclose(link.env.positions, held, atol=0.5)
    assert np.all(np.linalg.norm(link.env.velocities, axis=1) < 0.1)


def test_step5_line_spaced_three_metres():
    link = _link()
    _airborne(link)
    _send(link, {"intent": "formation", "shape": "line", "spacing": 3.0})
    _run(link, 15)
    along = np.sort(link.env.positions[:, 1])
    np.testing.assert_allclose(np.diff(along), 3.0, atol=0.3)


def test_step6_land_descends_and_reports_ground_contact():
    link = _link()
    _airborne(link)
    _send(link, {"intent": "land"})
    assert link.fsm.state == FlightState.LANDING
    _run(link, 15)
    assert link.fsm.state == FlightState.LANDED
    assert not link.motors_on
    assert np.all(link.env.positions[:, 2] <= GROUND_Z)


def test_step7_abort_descends_in_place_and_stops_motors():
    link = _link()
    _airborne(link)
    xy = link.env.positions[:, :2]
    _send(link, {"intent": "abort"})
    assert link.fsm.state == FlightState.ABORTED
    _run(link, 15)
    assert link.fsm.state == FlightState.ABORTED
    assert not link.motors_on
    assert np.all(link.env.positions[:, 2] <= GROUND_Z)
    np.testing.assert_allclose(link.env.positions[:, :2], xy, atol=0.3)


def test_step8_reset_only_on_the_ground_and_at_rest():
    link = _link()
    _airborne(link)
    _send(link, {"intent": "abort"})
    _run(link, 0.5)                     # still airborne
    assert not link.reset()
    assert link.fsm.state == FlightState.ABORTED
    _run(link, 15)
    assert link.reset()
    assert link.fsm.state == FlightState.LANDED


def test_aborted_ignores_every_spoken_command():
    link = _link()
    _airborne(link)
    _send(link, {"intent": "abort"})
    _run(link, 15)
    rest = link.env.positions
    for raw in ({"intent": "takeoff", "z": 5.0}, {"intent": "hover"}, {"intent": "land"},
                {"intent": "formation", "shape": "circle", "radius": 5.0}):
        assert _send(link, raw) is None
    _run(link, 2)
    np.testing.assert_allclose(link.env.positions, rest)


def test_commands_rejected_while_landed_produce_no_motion():
    link = _link()
    for raw in ({"intent": "formation", "shape": "circle", "radius": 5.0},
                {"intent": "move", "dir": "north", "dist": 10.0}, {"intent": "hover"},
                {"intent": "unknown"}):
        assert _send(link, raw) is None
    _run(link, 2)
    assert not link.motors_on
    np.testing.assert_allclose(link.env.positions, ground_layout())


@pytest.mark.parametrize("raw", [
    {"intent": "formation", "shape": "grid", "spacing": 2.0},
    {"intent": "formation", "shape": "circle", "radius": 5.0, "ids": [0, 1]},
    {"intent": "rotate", "yaw": 90.0},
])
def test_legal_but_unmapped_commands_hold_in_flight(raw):
    link = _link()
    _airborne(link)
    text = _send(link, raw)
    assert text is not None and text.endswith("-> hold")
    np.testing.assert_allclose(link.controller.targets, link.env.positions)


def test_guard_refuses_the_raw_intent_defect_during_landing():
    """Ch4: an unvalidated set_param with no value, received while LANDING, is validated to a hold
    and dispatched although a hold is illegal there. The link refuses it; the descent goes on."""
    link = _link()
    _airborne(link)
    _send(link, {"intent": "land"})
    before = link.fsm.state
    cmd = link.fsm.handle_command({"intent": "set_param"})   # unvalidated, as in the defect
    assert cmd is not None and cmd.intent == "hover"        # the defect itself, unchanged
    assert link.dispatch(cmd, before).startswith("refused")
    _run(link, 15)
    assert link.fsm.state == FlightState.LANDED


def test_takeoff_naming_a_subset_still_flies_the_whole_swarm():
    link = _link()
    _send(link, {"intent": "takeoff", "z": 3.0, "ids": [0]})
    _run(link, 10)
    assert link.fsm.state == FlightState.FLYING
    np.testing.assert_allclose(link.env.positions[:, 2], 3.0, atol=0.3)


def test_whole_script_keeps_separation_under_the_clamp():
    link = _link()
    script = [
        ({"intent": "takeoff", "z": 5.0}, 10),
        ({"intent": "formation", "shape": "circle", "radius": 5.0}, 12),
        ({"intent": "move", "dir": "north", "dist": 10.0}, 12),
        ({"intent": "hover"}, 3),
        ({"intent": "formation", "shape": "line", "spacing": 3.0}, 12),
        ({"intent": "land"}, 12),
        ({"intent": "takeoff", "z": 5.0}, 10),
        ({"intent": "abort"}, 12),
    ]
    for raw, seconds in script:
        _send(link, raw)
        _run(link, seconds)
    assert link.fsm.state == FlightState.ABORTED
    assert link.collisions == 0
    assert link.min_pair_distance >= CLAMP_DISTANCE - 1e-6
    assert link.reset()
