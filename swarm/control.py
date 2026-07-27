"""The swarm controller: formation slots, Boids, APF separation, PID (FR-7).

Four terms, in descending authority:

1. **PID to an assigned formation slot.** This is what actually flies the formation.
2. **APF separation** --- a repulsive potential that grows as drones close.
3. **Boids cohesion and alignment**, weakly weighted. FR-7 names Boids and it earns
   its place on the approach, where it keeps the group together before slots are
   assigned; once slots dominate, cohesion is largely redundant and is weighted
   accordingly rather than dropped, which would make FR-7 false.
4. **A hard geometric separation clamp at the integrator** --- not a force. After the
   positions are written, any pair closer than `CLAMP_DISTANCE` is pushed apart until
   it is not.

Point 4 is the whole basis of the NFR-12 claim, and the claim is carefully worded:
**zero collisions *observed*, backed by the clamp --- not zero collisions guaranteed
by APF.** A potential field guarantees nothing here. Timesteps are discrete and
acceleration is bounded, so there is always a closing speed from which no force can
stop a drone in time; APF additionally has well-known local-minima and oscillation
modes. Claiming a guarantee invites a question that cannot be answered, so the
controller carries a mechanism that *can* be defended and the metric reports how
often it had to act.

That is why two numbers are recorded, not one: `clamp_activations` (how often the
potential field was insufficient) and `collisions` (how often two drones were closer
than `COLLISION_DISTANCE` after the clamp, which should be zero by construction).
Reporting only the second would hide the work the first is doing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linear_sum_assignment

__all__ = [
    "SHAPES", "formation_slots", "assign_slots", "separation_clamp",
    "ControlGains", "SwarmController", "CLAMP_DISTANCE", "COLLISION_DISTANCE",
]

#: The three shapes Exp-4 sweeps. `schema/schema.py` declares six; `column` and
#: `flock` are valid commands but are not part of the formation-quality experiment.
SHAPES: tuple[str, ...] = ("circle", "line", "wedge")

#: Below this the clamp intervenes. Chosen as roughly twice the rotor-tip diameter of
#: a small quadrotor, so the clamp fires while there is still airspace between hulls
#: rather than at the moment of contact. Not given by the PRD; recorded here for the
#: same reason ADR-0001 records the envelope bounds it had to invent.
CLAMP_DISTANCE = 0.80

#: What counts as a collision in the reported metric: closer than two hull radii.
#: Strictly smaller than CLAMP_DISTANCE, so the clamp has margin to work in and a
#: reported collision means the clamp itself failed, not merely that drones were close.
COLLISION_DISTANCE = 0.35


# --------------------------------------------------------------------------
# formation geometry


def formation_slots(
    shape: str,
    n: int,
    centre: np.ndarray | tuple[float, float, float] = (0.0, 0.0, 2.0),
    *,
    radius: float = 5.0,
    spacing: float = 2.0,
    heading: float = 0.0,
) -> np.ndarray:
    """`(n, 3)` target positions for `shape`, centred on `centre`.

    Every shape is generated about the origin and then rotated by `heading` and
    translated, so the three differ only in their offsets and a heading change can
    never mean something different for one shape than another.
    """
    if shape not in SHAPES:
        raise ValueError(f"unknown shape {shape!r}; Exp-4 sweeps {SHAPES}")
    if n < 1:
        raise ValueError("n must be at least 1")

    if shape == "circle":
        angles = np.arange(n) * (2.0 * np.pi / n)
        offsets = np.column_stack([radius * np.cos(angles), radius * np.sin(angles), np.zeros(n)])
    elif shape == "line":
        # Centred on the middle drone, so the formation does not translate with n.
        along = (np.arange(n) - (n - 1) / 2.0) * spacing
        offsets = np.column_stack([np.zeros(n), along, np.zeros(n)])
    else:  # wedge
        # Apex forward, two arms trailing at +/- 30 degrees. Drone 0 leads; the rest
        # alternate sides so the formation stays symmetric for odd and even n alike.
        half_angle = np.deg2rad(30.0)
        offsets = np.zeros((n, 3))
        for index in range(1, n):
            rank = (index + 1) // 2
            side = 1.0 if index % 2 else -1.0
            offsets[index] = [-rank * spacing * np.cos(half_angle),
                              side * rank * spacing * np.sin(half_angle), 0.0]
        # Re-centre on the centroid. Left apex-centred, the wedge's mean sits behind
        # `centre` while the circle's and the line's sit on it, so commanding the
        # three about the same point would hand the wedge a longer approach --- a
        # translation difference that Exp-4's one-way ANOVA would read as a
        # difference between formations.
        offsets -= offsets.mean(axis=0)

    cos_h, sin_h = np.cos(heading), np.sin(heading)
    rotation = np.array([[cos_h, -sin_h, 0.0], [sin_h, cos_h, 0.0], [0.0, 0.0, 1.0]])
    return offsets @ rotation.T + np.asarray(centre, dtype=float)


def assign_slots(positions: np.ndarray, slots: np.ndarray) -> np.ndarray:
    """Assign drones to slots minimising total squared distance (Hungarian).

    Returns `assignment` such that drone `i` targets `slots[assignment[i]]`.

    Greedy nearest-slot assignment is the obvious alternative and is wrong: it
    routinely produces crossing paths, which sends two drones through the same volume
    and turns a formation change into the exact event NFR-12 is about. The optimal
    assignment does not eliminate crossings but removes the ones that exist only
    because of the assignment.
    """
    positions = np.asarray(positions, dtype=float)
    slots = np.asarray(slots, dtype=float)
    cost = np.sum((positions[:, None, :] - slots[None, :, :]) ** 2, axis=2)
    _, assignment = linear_sum_assignment(cost)
    return assignment


# --------------------------------------------------------------------------
# the hard clamp


def separation_clamp(
    positions: np.ndarray,
    velocities: np.ndarray | None = None,
    *,
    min_distance: float = CLAMP_DISTANCE,
    iterations: int = 64,
    tolerance: float = 1e-9,
) -> tuple[np.ndarray, np.ndarray | None, int]:
    """Project positions apart until no pair is closer than `min_distance`.

    Returns `(positions, velocities, activations)`, where `activations` is the number
    of pairs that were too close **when the clamp was entered** --- that is, the
    violations the dynamics actually produced, not the internal sweeps used to fix
    them.

    Applied *after* the integrator writes positions, which is what makes it a
    geometric guarantee on the recorded state rather than another force that can be
    outrun. Each violating pair is separated by half the deficit each; the sweep
    repeats because separating one pair can close another.

    The iteration cap is generous because a chain of three converges slowly: pushing
    the outer pair apart closes the inner one, and the Gauss-Seidel sweep approaches
    the feasible configuration geometrically rather than reaching it in one pass.
    Eight sweeps leave a chain of three about 3 mm short of `min_distance`, which is
    harmless against a collision threshold less than half that --- but a clamp that
    only approximately enforces the distance it advertises makes NFR-12's wording
    harder to defend than it needs to be, so it runs to convergence instead.

    Velocities lose their *approaching* radial component as well. Position-only
    clamping leaves the closing speed intact, so the pair re-penetrates on the next
    tick and the clamp fires forever --- which would read in the log as a permanent
    collision rather than a resolved one.
    """
    positions = np.asarray(positions, dtype=float).copy()
    velocities = None if velocities is None else np.asarray(velocities, dtype=float).copy()
    activations = 0

    for sweep in range(iterations):
        delta = positions[:, None, :] - positions[None, :, :]
        distance = np.linalg.norm(delta, axis=2)
        np.fill_diagonal(distance, np.inf)
        rows, cols = np.where(distance < min_distance - tolerance)
        pairs = [(i, j) for i, j in zip(rows, cols) if i < j]
        if not pairs:
            break
        if sweep == 0:
            # Only the first sweep is counted. Later sweeps are this routine
            # converging on its own correction, not the dynamics producing new
            # violations, and counting them would make the reported figure a
            # function of the iteration cap rather than of the controller.
            activations = len(pairs)

        for i, j in pairs:
            offset = positions[i] - positions[j]
            separation = float(np.linalg.norm(offset))
            if separation < 1e-9:
                # Exactly coincident: no axis to separate along. Pick a deterministic
                # one from the pair's indices so a trial stays reproducible.
                offset = np.zeros(3)
                offset[(i + j) % 3] = 1.0
                separation = 1.0
            unit = offset / separation
            push = 0.5 * (min_distance - separation)
            positions[i] += unit * push
            positions[j] -= unit * push

            if velocities is not None:
                closing = float(np.dot(velocities[i] - velocities[j], unit))
                if closing < 0.0:                       # they are approaching
                    velocities[i] -= unit * (closing / 2.0)
                    velocities[j] += unit * (closing / 2.0)

    return positions, velocities, activations


# --------------------------------------------------------------------------
# the controller


@dataclass(frozen=True)
class ControlGains:
    """PID on the slot error, plus the weights of the three auxiliary terms.

    `kd` is set slightly above critical damping for `kp` (2*sqrt(kp) = 2.83). A
    formation that overshoots its slot converges faster on paper and spends the final
    five seconds oscillating across the tau = 0.5 m boundary, which is exactly the
    window FA is measured over.
    """

    kp: float = 2.0
    ki: float = 0.05
    kd: float = 3.0
    integral_limit: float = 2.0     # anti-windup, metres-seconds

    separation_gain: float = 6.0
    separation_radius: float = 1.5  # APF influence distance, metres
    cohesion_gain: float = 0.15
    alignment_gain: float = 0.25


class SwarmController:
    """Stateful controller: holds the integral term and the current slot assignment.

    Slots are assigned once when a formation is commanded and then held. Re-solving
    the assignment every tick lets two drones swap targets mid-flight whenever noise
    makes the swap marginally cheaper, and the result is a pair flying through each
    other --- a chattering failure that looks like a controller instability.
    """

    def __init__(self, n: int, dt: float, gains: ControlGains | None = None):
        self.n, self.dt = n, dt
        self.gains = gains or ControlGains()
        self._integral = np.zeros((n, 3))
        self._targets = np.zeros((n, 3))
        self._assigned = False

    def command(self, shape: str, positions: np.ndarray, **kwargs) -> np.ndarray:
        """Set the formation and assign slots from the current positions."""
        centre = kwargs.pop("centre", None)
        if centre is None:
            centre = np.asarray(positions, dtype=float).mean(axis=0)
        slots = formation_slots(shape, self.n, centre, **kwargs)
        self._targets = slots[assign_slots(positions, slots)]
        self._integral[:] = 0.0
        self._assigned = True
        return self._targets.copy()

    @property
    def targets(self) -> np.ndarray:
        return self._targets.copy()

    def step(self, positions: np.ndarray, velocities: np.ndarray) -> np.ndarray:
        """One tick: `(n, 3)` acceleration command."""
        if not self._assigned:
            raise RuntimeError("command() must set a formation before step()")
        positions = np.asarray(positions, dtype=float)
        velocities = np.asarray(velocities, dtype=float)
        gains = self.gains

        error = self._targets - positions
        self._integral = np.clip(
            self._integral + error * self.dt, -gains.integral_limit, gains.integral_limit)
        accel = gains.kp * error + gains.ki * self._integral - gains.kd * velocities

        accel += self._separation(positions)

        # Boids, weakly: the formation term owns the trajectory.
        accel += gains.cohesion_gain * (positions.mean(axis=0) - positions)
        accel += gains.alignment_gain * (velocities.mean(axis=0) - velocities)
        return accel

    def _separation(self, positions: np.ndarray) -> np.ndarray:
        """APF repulsion, vectorised. Zero beyond `separation_radius`."""
        gains = self.gains
        delta = positions[:, None, :] - positions[None, :, :]
        distance = np.linalg.norm(delta, axis=2)
        np.fill_diagonal(distance, np.inf)

        active = distance < gains.separation_radius
        if not active.any():
            return np.zeros_like(positions)

        # Standard APF gradient: (1/d - 1/d0) / d^2, along the unit separation.
        safe = np.where(active, np.maximum(distance, 1e-6), 1.0)
        magnitude = np.where(
            active, gains.separation_gain * (1.0 / safe - 1.0 / gains.separation_radius) / safe**2, 0.0)
        unit = delta / safe[:, :, None]
        return np.sum(unit * magnitude[:, :, None], axis=1)
