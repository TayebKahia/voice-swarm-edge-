"""`SwarmEnv` --- the abstraction the controller is written against (FR-7, FR-8).

Two backends exist for one reason: iteration speed and fidelity are different needs.
The NumPy backend is a double integrator with the same bounds as the quadrotor, runs
a 60 s five-drone trial in well under a second, and is what Exp-4's sweep uses.
PyFlyt is a real rigid-body simulation and is what proves the controller is not
exploiting the toy dynamics.

The controller never sees either. It receives positions and velocities and returns
accelerations, so the same `swarm/control.py` drives both --- which is the only way a
PyFlyt hover smoke test says anything about the NumPy trials.

Conventions, fixed here so nothing downstream has to guess:

* positions and velocities are `(n, 3)` float arrays, metres and m/s, ENU with +z up;
* `dt` is 0.02 s --- 50 Hz, per FR-7 and the Exp-4 protocol;
* `step` takes a `(n, 3)` **acceleration** command and advances one tick.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

__all__ = ["SwarmEnv", "NumpyEnv", "EnvLimits", "DEFAULT_DT", "DEFAULT_N"]

#: 50 Hz. FR-7 and the Exp-4 protocol both fix this; it is not a tuning knob.
DEFAULT_DT = 0.02
DEFAULT_N = 5


@dataclass(frozen=True)
class EnvLimits:
    """Actuation bounds.

    These are what make "zero collisions guaranteed by APF" an unmakeable claim
    (NFR-12): with a bounded acceleration and a finite timestep, there is always a
    closing speed from which no controller can stop in time. The separation clamp in
    `control.py` exists precisely because the potential field cannot be trusted alone.
    """

    max_speed: float = 3.0          # m/s
    max_accel: float = 4.0          # m/s^2
    min_altitude: float = 0.0       # ground plane; the floor is not penetrable


class SwarmEnv(ABC):
    """N drones, fixed timestep, acceleration in and state out."""

    n: int
    dt: float

    @abstractmethod
    def reset(self, seed: int) -> tuple[np.ndarray, np.ndarray]:
        """Place the drones and return `(positions, velocities)`."""

    @abstractmethod
    def step(self, accelerations: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Advance one tick and return the new `(positions, velocities)`."""

    @property
    @abstractmethod
    def positions(self) -> np.ndarray: ...

    @property
    @abstractmethod
    def velocities(self) -> np.ndarray: ...


class NumpyEnv(SwarmEnv):
    """Vectorised double integrator with the quadrotor's bounds.

    Semi-implicit (symplectic) Euler: velocity is updated first and the *new*
    velocity moves the position. Explicit Euler injects energy on every tick, which
    in a formation controller shows up as a slow oscillation about the slot that
    looks exactly like an under-damped gain and would be tuned against rather than
    recognised as an integrator artefact.
    """

    def __init__(self, n: int = DEFAULT_N, dt: float = DEFAULT_DT,
                 limits: EnvLimits | None = None,
                 spawn_sigma: float = 0.5, centroid: tuple[float, float, float] = (0.0, 0.0, 2.0)):
        self.n, self.dt = n, dt
        self.limits = limits or EnvLimits()
        #: Exp-4 spawns N(0, 0.5 m) about the centroid (prd.md Table 15).
        self.spawn_sigma = spawn_sigma
        self.centroid = np.asarray(centroid, dtype=float)
        self._positions = np.zeros((n, 3))
        self._velocities = np.zeros((n, 3))

    def reset(self, seed: int) -> tuple[np.ndarray, np.ndarray]:
        # A seeded Generator, not the legacy global RNG: trial i must reproduce
        # exactly, and `seed = trial index * 42` is part of the published protocol.
        rng = np.random.default_rng(seed)
        self._positions = self.centroid + rng.normal(0.0, self.spawn_sigma, size=(self.n, 3))
        self._positions[:, 2] = np.maximum(self._positions[:, 2], self.limits.min_altitude)
        self._velocities = np.zeros((self.n, 3))
        return self.positions, self.velocities

    def step(self, accelerations: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        accel = np.asarray(accelerations, dtype=float).reshape(self.n, 3)
        accel = _clip_norm(accel, self.limits.max_accel)

        self._velocities = _clip_norm(self._velocities + accel * self.dt, self.limits.max_speed)
        self._positions = self._positions + self._velocities * self.dt

        below = self._positions[:, 2] < self.limits.min_altitude
        self._positions[below, 2] = self.limits.min_altitude
        self._velocities[below, 2] = np.maximum(self._velocities[below, 2], 0.0)
        return self.positions, self.velocities

    def set_state(self, positions: np.ndarray, velocities: np.ndarray | None = None) -> None:
        """Overwrite the state --- used by the separation clamp, which acts on positions."""
        self._positions = np.asarray(positions, dtype=float).reshape(self.n, 3).copy()
        if velocities is not None:
            self._velocities = np.asarray(velocities, dtype=float).reshape(self.n, 3).copy()

    @property
    def positions(self) -> np.ndarray:
        return self._positions.copy()

    @property
    def velocities(self) -> np.ndarray:
        return self._velocities.copy()


def _clip_norm(vectors: np.ndarray, limit: float) -> np.ndarray:
    """Scale each row down to `limit` if it exceeds it, preserving direction.

    Per-component clipping would silently rotate the commanded vector --- the same
    reason `schema/validate.py` clamps `pos` by scaling the whole vector rather than
    each axis (ADR-0001).
    """
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    scale = np.ones_like(norms)
    exceeded = norms > limit
    scale[exceeded] = limit / norms[exceeded]
    return vectors * scale
