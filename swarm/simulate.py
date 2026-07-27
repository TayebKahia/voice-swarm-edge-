"""One Exp-4 trial, and the metrics computed from it.

The protocol is fixed by `prd.md` Table 15 and is not a parameter of the experiment:
**timestep 0.02 s, seed = trial index x 42, initial positions N(0, 0.5 m) about the
centroid, 60 s trials.** Those four live in `TrialSpec` so a caller cannot quietly
differ from the published protocol.

Two metrics need their definitions stated rather than inferred.

**FA** is the fraction of drones within tau = 0.5 m of their *assigned* slot, averaged
over the final 5 s --- not the closest slot. A swarm that settles into the right shape
with two drones exchanged has formed the formation but not executed the command, and
measuring against the assignment is what makes that distinction.

**Convergence** is reported as a *rate* plus a median and IQR *over converged trials
only*. A mean convergence time over a sample containing trials that never converge
has no finite value to estimate, so no confidence interval can be put around it.
`converged=False` rows carry an empty time rather than the trial length, which would
silently turn a non-convergence into a slow convergence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from swarm.control import (COLLISION_DISTANCE, ControlGains, SwarmController,
                           separation_clamp)
from swarm.env import DEFAULT_DT, DEFAULT_N, NumpyEnv, SwarmEnv

__all__ = ["TrialSpec", "TrialResult", "run_trial", "SEED_MULTIPLIER"]

#: prd.md Table 15: seed = trial index x 42.
SEED_MULTIPLIER = 42

#: NFR-13's tolerance.
SLOT_TOLERANCE = 0.5

#: FA is averaged over the final 5 s of the trial.
FINAL_WINDOW_SECONDS = 5.0

#: A trial has converged once FA >= this, and the convergence time is the first
#: moment it does. NFR-13 uses the same threshold for the final-window figure.
CONVERGENCE_FA = 0.85


@dataclass(frozen=True)
class TrialSpec:
    """The published Exp-4 protocol. Defaults are the protocol, not suggestions."""

    shape: str
    index: int
    n: int = DEFAULT_N
    dt: float = DEFAULT_DT
    duration_seconds: float = 60.0
    spawn_sigma: float = 0.5
    radius: float = 5.0
    spacing: float = 2.0

    @property
    def seed(self) -> int:
        return self.index * SEED_MULTIPLIER

    @property
    def ticks(self) -> int:
        return int(round(self.duration_seconds / self.dt))


@dataclass
class TrialResult:
    shape: str
    index: int
    seed: int
    formation_accuracy: float
    converged: bool
    convergence_seconds: float | None
    collisions: int
    clamp_activations: int
    min_pair_distance: float
    final_mean_error: float
    fa_series: np.ndarray = field(repr=False, default_factory=lambda: np.empty(0))


def _formation_accuracy(positions: np.ndarray, targets: np.ndarray) -> float:
    return float(np.mean(np.linalg.norm(positions - targets, axis=1) <= SLOT_TOLERANCE))


def run_trial(spec: TrialSpec, env: SwarmEnv | None = None,
              gains: ControlGains | None = None) -> TrialResult:
    """Run one trial and return its metrics.

    The loop order matters and mirrors a real flight stack: the controller sees the
    state the integrator produced *and the clamp corrected*, never the uncorrected
    one. Feeding it pre-clamp positions would let it act on a state that never
    existed, and the clamp would show up as an unmodelled disturbance.
    """
    env = env or NumpyEnv(n=spec.n, dt=spec.dt, spawn_sigma=spec.spawn_sigma)
    positions, velocities = env.reset(spec.seed)

    controller = SwarmController(spec.n, spec.dt, gains)
    controller.command(spec.shape, positions, radius=spec.radius, spacing=spec.spacing)
    targets = controller.targets

    fa_series = np.zeros(spec.ticks)
    collisions = clamp_activations = 0
    min_pair = np.inf
    convergence_tick: int | None = None

    for tick in range(spec.ticks):
        accel = controller.step(positions, velocities)
        positions, velocities = env.step(accel)

        positions, velocities, activations = separation_clamp(positions, velocities)
        clamp_activations += activations
        if activations and isinstance(env, NumpyEnv):
            env.set_state(positions, velocities)

        distance = np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)
        np.fill_diagonal(distance, np.inf)
        closest = float(distance.min())
        min_pair = min(min_pair, closest)
        # Counted AFTER the clamp: this is the number NFR-12 reports, and it is
        # expected to be zero by construction. `clamp_activations` is the honest
        # companion figure -- how often the potential field alone was not enough.
        if closest < COLLISION_DISTANCE:
            collisions += 1

        fa_series[tick] = _formation_accuracy(positions, targets)
        if convergence_tick is None and fa_series[tick] >= CONVERGENCE_FA:
            convergence_tick = tick

    window = max(1, int(round(FINAL_WINDOW_SECONDS / spec.dt)))
    final_fa = float(fa_series[-window:].mean())

    return TrialResult(
        shape=spec.shape,
        index=spec.index,
        seed=spec.seed,
        formation_accuracy=final_fa,
        converged=convergence_tick is not None,
        convergence_seconds=None if convergence_tick is None else convergence_tick * spec.dt,
        collisions=collisions,
        clamp_activations=clamp_activations,
        min_pair_distance=float(min_pair),
        final_mean_error=float(np.linalg.norm(positions - targets, axis=1).mean()),
        fa_series=fa_series,
    )
