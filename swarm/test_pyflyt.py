"""FR-8: both backends fly the same controller.

Marked slow and kept small --- PyFlyt is rigid-body physics in PyBullet and costs
roughly a second of wall-clock per simulated second per five drones, so Exp-4's sweep
stays on the NumPy backend. What these tests establish is the thing the sweep cannot:
that the controller is not exploiting the double integrator.

The same `SwarmController`, with the same gains, drives both. If these pass only after
retuning, the Exp-4 numbers describe a controller that exists nowhere else.
"""

from __future__ import annotations

import numpy as np
import pytest

from swarm.control import SHAPES, SwarmController
from swarm.env import NumpyEnv

pytestmark = pytest.mark.slow

PyFlytEnv = pytest.importorskip("swarm.pyflyt_env", reason="PyFlyt not installed").PyFlytEnv

HOVER_SECONDS = 12.0
TOLERANCE = 0.5          # NFR-13's tau


def _fly(env, shape: str, seed: int = 42, seconds: float = HOVER_SECONDS):
    positions, velocities = env.reset(seed)
    controller = SwarmController(env.n, env.dt)
    targets = controller.command(shape, positions, spacing=2.0, radius=5.0)
    for _ in range(int(round(seconds / env.dt))):
        positions, velocities = env.step(controller.step(positions, velocities))
    return positions, targets


@pytest.mark.parametrize("shape", SHAPES)
def test_pyflyt_holds_the_formation(shape):
    env = PyFlytEnv(n=5)
    try:
        positions, targets = _fly(env, shape)
    finally:
        env.close()
    errors = np.linalg.norm(positions - targets, axis=1)
    assert np.mean(errors <= TOLERANCE) >= 0.85, f"FA {np.mean(errors <= TOLERANCE)}"


def test_pyflyt_does_not_sink_under_a_station_keeping_command():
    # The regression that cost an hour: mapping the acceleration command onto
    # `measured velocity + a*dt` re-issues PyFlyt's own steady-state altitude droop
    # as the next setpoint, the plant tracks it, and the drone is on the floor in two
    # seconds -- then ignores lateral commands because it has landed. The commanded
    # velocity is integrated internally instead.
    env = PyFlytEnv(n=5)
    try:
        positions, _ = _fly(env, "line")
    finally:
        env.close()
    assert positions[:, 2].min() > 1.0, "drones sank towards the ground"


def test_the_same_controller_and_gains_drive_both_backends():
    # FR-8 is about the controller, not about two separately tuned controllers.
    numpy_positions, numpy_targets = _fly(NumpyEnv(n=5), "line")
    env = PyFlytEnv(n=5)
    try:
        pyflyt_positions, pyflyt_targets = _fly(env, "line")
    finally:
        env.close()
    for positions, targets in ((numpy_positions, numpy_targets),
                               (pyflyt_positions, pyflyt_targets)):
        assert np.mean(np.linalg.norm(positions - targets, axis=1) <= TOLERANCE) >= 0.85
