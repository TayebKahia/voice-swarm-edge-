"""demo/workstation.py -- the consumer side, over a real UDP bus, driven by demo/rehearse.py's script.

Every step of tab:demo-script is published on a loopback bus exactly as the device would publish
it (step 4 with the line's number reserved before the reflex hold), received by `Station`, and
played out on the kinematic backend in simulated time. The state after each step is checked
against the script's "State after" column, and step 4's line must be discarded, not flown.
"""

from __future__ import annotations

import socket
import time

import numpy as np
import pytest

from demo.rehearse import REJECTIONS, SCRIPT, publish_step
from demo.workstation import Station, build
from runtime.bus import CommandBus
from swarm.fsm import FlightState
from swarm.link import ground_layout


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def rig():
    port = _free_port()
    listener = CommandBus(host="127.0.0.1", port=port, bind=True)
    station = Station(listener, build("numpy"), echo=False)
    publisher = CommandBus(host="127.0.0.1", port=port)
    yield station, publisher
    station.close()
    listener.close()
    publisher.close()


def _deliver(station: Station, expected: int, timeout: float = 2.0) -> None:
    target = station.received + expected
    deadline = time.monotonic() + timeout
    while station.received < target:
        assert time.monotonic() < deadline, "bus message not received"
        station.pump()
        time.sleep(0.005)


def _play(station: Station, seconds: float) -> None:
    for _ in range(int(round(seconds / station.link.env.dt))):
        station.tick()


def test_rejections_while_landed_move_nothing(rig):
    station, publisher = rig
    for step in REJECTIONS:
        _deliver(station, publish_step(publisher, step))
        _play(station, step.seconds)
        assert station.link.fsm.state.value == step.state_after
    assert not station.link.motors_on
    np.testing.assert_allclose(station.link.env.positions, ground_layout())


def test_whole_script_over_the_bus(rig):
    station, publisher = rig
    for step in SCRIPT:
        _deliver(station, publish_step(publisher, step))
        if step.number == "4":
            discarded = [e for e in list(station.events)[-2:] if e.outcome.startswith("discarded")]
            assert len(discarded) == 1 and "formation" in discarded[0].received
            assert station.link.controller.targets[:, 1].std() > 1.0   # still the moved circle's slots
        _play(station, step.seconds)
        assert station.link.fsm.state.value == step.state_after, f"step {step.number}"
    assert station.link.collisions == 0
    reported = [e.received for e in station.events if e.path == "vehicles"]
    assert reported == ["take-off height reached", "ground contact",
                        "take-off height reached", "ground contact"]
    assert station.reset()
    assert station.link.fsm.state == FlightState.LANDED


def test_step4_hold_prevents_the_line(rig):
    """Success criterion 2: the hold takes effect and the command spoken before it does not."""
    station, publisher = rig
    for step in SCRIPT[:3]:
        _deliver(station, publish_step(publisher, step))
        _play(station, step.seconds)
    _deliver(station, publish_step(publisher, SCRIPT[3]))
    _play(station, SCRIPT[3].seconds)
    p = station.link.env.positions
    # A line is spread along north at 3 m spacing (12 m end to end); the held circle is 10 m across.
    assert np.ptp(p[:, 1]) < 11.0
    assert np.all(np.linalg.norm(station.link.env.velocities, axis=1) < 0.1)


def test_reset_refused_while_airborne(rig):
    station, publisher = rig
    _deliver(station, publish_step(publisher, SCRIPT[0]))
    _play(station, SCRIPT[0].seconds)
    assert not station.reset()
    assert station.events[-1].outcome == "reset refused: not ABORTED"
