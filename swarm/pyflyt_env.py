"""The PyFlyt backend --- the second half of FR-8.

The NumPy backend is a double integrator. It is fast enough to sweep Exp-4 in under a
minute, and that speed is exactly why it cannot be the only evidence: a controller
tuned against a double integrator may be relying on dynamics a real quadrotor does not
have. PyFlyt supplies rigid-body physics, rotor dynamics and an attitude loop, so a
hover that holds here is a hover that holds against something the controller cannot
have over-fitted to.

**The seam is a velocity setpoint** (QuadX flight mode 6: `vx, vy, vr, vz` in the
world frame). `swarm/control.py` produces an acceleration, which is integrated once
against the measured velocity to give the setpoint; PyFlyt's own attitude and rotor
loops take it from there. Mode 7 --- a position setpoint --- would have been simpler
and would have measured PyFlyt's built-in position controller rather than ours, which
is not what FR-8 is asking.

Physics runs at 240 Hz and control at 50 Hz, so one control tick is several physics
steps with the setpoint held between them. That is how a real flight stack works, and
it means the 50 Hz figure in FR-7 refers to the same thing on both backends.

**The commanded velocity is integrated internally, not read back from the vehicle.**
The obvious mapping --- setpoint = measured velocity + a*dt --- is wrong here and
fails in a way worth recording, because it looks correct and produces a plausible
crash. PyFlyt's inner loop has a small steady-state altitude droop; reading the
measured velocity back means a zero vertical acceleration command re-issues that droop
as the next setpoint, which the plant then tracks, producing more droop. The result is
a drone that falls to the ground in about two seconds under a command to hold station,
and then ignores lateral commands because it is sitting on the floor. Integrating the
command in the controller's own frame leaves the inner loop to reject its own error,
which is what it is for.
"""

from __future__ import annotations

import numpy as np

from swarm.env import DEFAULT_DT, DEFAULT_N, EnvLimits, SwarmEnv

__all__ = ["PyFlytEnv"]

#: PyFlyt's default. 240 / 50 = 4.8, so the control period is rounded to whole
#: physics steps and the true control rate is reported rather than assumed.
PHYSICS_HZ = 240


class PyFlytEnv(SwarmEnv):
    """Five QuadX drones in PyBullet, driven by world-frame velocity setpoints."""

    def __init__(self, n: int = DEFAULT_N, dt: float = DEFAULT_DT,
                 limits: EnvLimits | None = None, spawn_sigma: float = 0.5,
                 centroid: tuple[float, float, float] = (0.0, 0.0, 2.0),
                 render: bool = False, physics_hz: int = PHYSICS_HZ):
        self.n, self.dt = n, dt
        self.limits = limits or EnvLimits()
        self.spawn_sigma = spawn_sigma
        self.centroid = np.asarray(centroid, dtype=float)
        self.render = render
        self.physics_hz = physics_hz
        #: Whole physics steps per control tick; at least one.
        self.steps_per_tick = max(1, int(round(physics_hz * dt)))
        self.effective_control_hz = physics_hz / self.steps_per_tick
        self._aviary = None
        #: The commanded velocity, integrated from the acceleration command. Kept
        #: here rather than read from the vehicle -- see the module docstring.
        self._commanded_velocity = np.zeros((n, 3))

    def reset(self, seed: int) -> tuple[np.ndarray, np.ndarray]:
        from PyFlyt.core import Aviary

        rng = np.random.default_rng(seed)
        start = self.centroid + rng.normal(0.0, self.spawn_sigma, size=(self.n, 3))
        # PyBullet spawns below ~0.1 m intersect the ground plane and the drone never
        # leaves it; the NumPy backend clamps to the floor for the same reason.
        start[:, 2] = np.maximum(start[:, 2], 0.5)

        if self._aviary is not None:
            self._aviary.disconnect()
        self._aviary = Aviary(
            start_pos=start,
            start_orn=np.zeros((self.n, 3)),
            drone_type="quadx",
            render=self.render,
            physics_hz=self.physics_hz,
            seed=seed,
        )
        self._aviary.set_mode(6)          # vx, vy, vr, vz -- world-frame velocity
        self._commanded_velocity = np.zeros((self.n, 3))
        return self.positions, self.velocities

    def step(self, accelerations: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if self._aviary is None:
            raise RuntimeError("reset() before step()")
        accel = np.asarray(accelerations, dtype=float).reshape(self.n, 3)
        accel = _clip_norm(accel, self.limits.max_accel)

        self._commanded_velocity = _clip_norm(
            self._commanded_velocity + accel * self.dt, self.limits.max_speed)
        target = self._commanded_velocity
        for index in range(self.n):
            # [vx, vy, yaw rate, vz]; yaw is not commanded by the formation controller.
            self._aviary.set_setpoint(index, np.array([target[index][0], target[index][1],
                                                       0.0, target[index][2]]))
        for _ in range(self.steps_per_tick):
            self._aviary.step()
        return self.positions, self.velocities

    @property
    def positions(self) -> np.ndarray:
        return np.array([self._aviary.state(i)[3] for i in range(self.n)], dtype=float)

    @property
    def velocities(self) -> np.ndarray:
        return np.array([self._aviary.state(i)[2] for i in range(self.n)], dtype=float)

    def close(self) -> None:
        if self._aviary is not None:
            self._aviary.disconnect()
            self._aviary = None


def _clip_norm(vectors: np.ndarray, limit: float) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    scale = np.ones_like(norms)
    exceeded = norms > limit
    scale[exceeded] = limit / norms[exceeded]
    return vectors * scale
