"""The link from the flight state machine to the swarm controller (the demonstration's third prerequisite).

Chapter 4 records this link as not built: the state machine returned commands that reached no
controller, the controller accepted only a formation, and nothing reported the vehicles back to the
state machine. This module is the link, and it has three jobs.

**Map each dispatched command onto controller targets.** The controller flies every vehicle to a
target by PID; every intent the demonstration script uses is a choice of targets:

    takeoff      each vehicle climbs in place to `z` (DEFAULT_TAKEOFF_Z when none is spoken)
    formation    `SwarmController.command` about the current centroid -- circle, line, wedge only
    hover        each vehicle holds the position it is at
    move         the whole target set is translated by `dir`*`dist`, or so its centroid lands on `pos`
    altitude     every target moves to height `z`
    land, abort  each vehicle descends in place; motors stop on ground contact

A command the controller cannot execute -- a grid, column or flock (no slot generator), any command
naming a subset of vehicles with `ids`, a rotation, a parameter change -- becomes a hold where
Table 9 makes a hold legal and a logged no-op where it does not, which is the state machine's own
rule for a rejection. Speed is not applied: the controller has no speed input, and the backends'
3 m/s ceiling governs, as Chapter 4 already states for a formation change. The swarm carries no
heading, so `forward`/`back`/`left`/`right` are read as north/south/west/east.

**Report the vehicles back to the state machine.** Every vehicle within `ALTITUDE_TOLERANCE` of the
take-off height calls `on_altitude_reached`; every vehicle at or below `GROUND_Z` calls
`on_ground_contact`; the reset passes `manual_reset` the two reports it needs, ground contact and
every speed under `REST_SPEED`. These three thresholds are the link's, not the thesis's: none of the
experiments ran the state machine against vehicles, so none of them fixed one.

**Step the simulation** exactly as `swarm/simulate.run_trial` does: the controller sees the state the
backend produced, and on the kinematic backend the separation clamp corrects it first. On the
physics backend no clamp acts (Chapter 6, Part B); the closest approach is recorded, not corrected.

**The guard.** Before it moves anything, the link checks the dispatched command's intent against
Table 9 in the state the command arrived in, and refuses and logs it if that cell is illegal. On
the deployed route this never fires: the device validates before it publishes, and the reflex path
publishes constants. It exists because `FlightStateMachine.handle_command` judges legality on the
intent before validation (Chapter 4, "Legality of the original intent"): a `set_param` with no value
arriving during a landing is validated to a hold and dispatched, although a hold is illegal there.
The guard keeps that defect from stopping a descent without changing the state machine the thesis
describes.

The controller, its gains and both backends are the ones Chapter 5 measured, unmodified.
`_TargetController` and the two ground-start environments below subclass them rather than edit
them: the only additions are "fly to these targets", "start on the ground" and "motors off".
"""

from __future__ import annotations

import numpy as np

from schema.logger import get_structured_logger
from schema.schema import ENVELOPE
from swarm.control import (COLLISION_DISTANCE, SHAPES, ControlGains, SwarmController,
                           separation_clamp)
from swarm.env import DEFAULT_DT, DEFAULT_N, NumpyEnv, SwarmEnv
from swarm.fsm import TABLE_9_LEGALITY, FlightState, FlightStateMachine
from swarm.pyflyt_env import PyFlytEnv
from swarm.simulate import SLOT_TOLERANCE

__all__ = [
    "Link", "GroundNumpyEnv", "GroundPyFlytEnv", "ground_layout", "tick_seconds",
    "DEFAULT_TAKEOFF_Z", "ALTITUDE_TOLERANCE", "GROUND_Z", "REST_SPEED",
]

logger = get_structured_logger("swarm.link")

#: A take-off with no height spoken. The schema makes `z` optional and fixes no default; 2 m is
#: the height `formation_slots` centres a formation on when none is given.
DEFAULT_TAKEOFF_Z = 2.0
#: Take-off height reached: every vehicle within the formation-accuracy tolerance of it.
ALTITUDE_TOLERANCE = SLOT_TOLERANCE
#: Ground contact. The kinematic floor is exactly 0; a PyFlyt QuadX rests at about 0.01 m.
GROUND_Z = 0.05
#: "Nearly at rest" for the reset.
REST_SPEED = 0.1
#: Spacing of the ground layout: a regular pentagon of this circumradius (side 2.35 m for five),
#: well outside both the clamp distance and the separation field's reach.
LAYOUT_RADIUS = 2.0

_UNIT = {
    "north": (0.0, 1.0, 0.0), "south": (0.0, -1.0, 0.0),
    "east": (1.0, 0.0, 0.0), "west": (-1.0, 0.0, 0.0),
    "up": (0.0, 0.0, 1.0), "down": (0.0, 0.0, -1.0),
    # No swarm heading exists; body-relative directions are read in the world frame.
    "forward": (0.0, 1.0, 0.0), "back": (0.0, -1.0, 0.0),
    "left": (-1.0, 0.0, 0.0), "right": (1.0, 0.0, 0.0),
}


def ground_layout(n: int = DEFAULT_N, z: float = 0.0, radius: float = LAYOUT_RADIUS) -> np.ndarray:
    """`(n, 3)` start positions on a regular polygon about the origin, at height `z`."""
    angles = np.pi / 2 + np.arange(n) * (2.0 * np.pi / n)
    return np.column_stack([radius * np.cos(angles), radius * np.sin(angles), np.full(n, z)])


class GroundNumpyEnv(NumpyEnv):
    """The kinematic backend, started on the ground rather than spawned about (0, 0, 2)."""

    def reset(self, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
        super().reset(seed)
        self.set_state(ground_layout(self.n), np.zeros((self.n, 3)))
        return self.positions, self.velocities

    def idle(self) -> tuple[np.ndarray, np.ndarray]:
        """Motors off: nothing moves."""
        self.set_state(self.positions, np.zeros((self.n, 3)))
        return self.positions, self.velocities


class GroundPyFlytEnv(PyFlytEnv):
    """The physics backend, started on the ground.

    `PyFlytEnv.reset` spawns about (0, 0, 2) with sigma 0.5 m and lifts every spawn to 0.5 m; with no
    clamp on this backend, five vehicles that close would risk colliding before the first command.
    This reset spawns them on `ground_layout` at 0.05 m, from which they settle onto the plane
    (a QuadX rests at about 0.01 m).

    "Motors off" is a zero velocity setpoint, not PyFlyt's disarm: a disarmed drone stops updating
    its state, so its position would go stale and ground contact could never be read from it.
    """

    SPAWN_Z = 0.05

    def reset(self, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
        from PyFlyt.core import Aviary

        if self._aviary is not None:
            self._aviary.disconnect()
        self._aviary = Aviary(
            start_pos=ground_layout(self.n, self.SPAWN_Z),
            start_orn=np.zeros((self.n, 3)),
            drone_type="quadx",
            render=self.render,
            physics_hz=self.physics_hz,
            seed=seed,
        )
        self._aviary.set_mode(6)
        return self.idle()

    @property
    def tick_seconds(self) -> float:
        """Simulated time per `step`: `steps_per_tick` Aviary steps of one control period each.

        Five steps of 1/120 s = 41.67 ms, the 24 Hz of Chapter 6's limitation -- not the 20 ms the
        controller integrates with, and not `effective_control_hz`, which counts Aviary steps as
        physics steps.
        """
        return self.steps_per_tick * float(self._aviary.step_period)

    def idle(self) -> tuple[np.ndarray, np.ndarray]:
        """Motors off: forget the integrated setpoint, command zero velocity, let physics run."""
        self._commanded_velocity = np.zeros((self.n, 3))
        for index in range(self.n):
            self._aviary.set_setpoint(index, np.zeros(4))
        for _ in range(self.steps_per_tick):
            self._aviary.step()
        return self.positions, self.velocities


def tick_seconds(env: SwarmEnv) -> float:
    """Wall-clock seconds one `step` stands for, so a real-time loop can pace the backend."""
    return float(getattr(env, "tick_seconds", env.dt))


class _TargetController(SwarmController):
    """`SwarmController` with one addition: fly to arbitrary targets, not only formation slots.

    `hold_at` does what `command` does after it has computed slots -- set the targets, clear the
    integral, mark the controller assigned -- and nothing else; `step` is inherited unchanged.
    """

    @property
    def assigned(self) -> bool:
        return self._assigned

    def hold_at(self, targets: np.ndarray) -> np.ndarray:
        self._targets = np.asarray(targets, dtype=float).reshape(self.n, 3).copy()
        self._integral[:] = 0.0
        self._assigned = True
        return self._targets.copy()


class Link:
    """State machine -> controller -> backend, and the backend's state back to the state machine."""

    def __init__(self, env: SwarmEnv, fsm: FlightStateMachine, *, clamp: bool,
                 gains: ControlGains | None = None) -> None:
        self.env = env
        self.fsm = fsm
        self.clamp = clamp
        self.controller = _TargetController(env.n, env.dt, gains)
        self.motors_on = False
        self._takeoff_z: float | None = None
        self.ticks = 0
        self.clamp_activations = 0
        #: Ticks whose closest pair was under COLLISION_DISTANCE, counted after the clamp where
        #: there is one -- run_trial's `collisions`.
        self.collisions = 0
        self.min_pair_distance = float("inf")

    # ------------------------------------------------------------------ commands

    def dispatch(self, cmd, state_before: FlightState) -> str:
        """Apply one command the state machine returned. Returns what was done, for the display."""
        intent = cmd.intent
        if state_before not in TABLE_9_LEGALITY.get(intent, set()):
            return self._log("link_refused_illegal",
                             f"refused: {intent} is illegal in {state_before.value}",
                             intent=intent, state=state_before.value)

        positions = self.env.positions
        unsupported = self._unsupported(cmd)
        if unsupported is not None:
            return self._hold_or_noop(unsupported, intent)

        if intent == "takeoff":
            z = DEFAULT_TAKEOFF_Z if cmd.z is None else float(cmd.z)
            self._takeoff_z = z
            self._fly_to(np.column_stack([positions[:, :2], np.full(self.env.n, z)]))
            return self._log("link_takeoff", f"climb in place to {z:g} m", z=z)

        if intent == "formation":
            kwargs = {k: float(v) for k, v in (("radius", cmd.radius), ("spacing", cmd.spacing))
                      if v is not None}
            self.controller.command(cmd.shape, positions, **kwargs)
            self.motors_on = True
            size = ", ".join(f"{k} {v:g} m" for k, v in kwargs.items())
            return self._log("link_formation", f"{cmd.shape}" + (f" ({size})" if size else ""),
                             shape=cmd.shape, **kwargs)

        if intent == "hover":
            self._fly_to(positions)
            return self._log("link_hold", "hold position")

        if intent == "move":
            targets = self.controller.targets if self.controller.assigned else positions
            if cmd.pos is not None:
                delta = np.asarray(cmd.pos, dtype=float) - targets.mean(axis=0)
                what = f"centroid to {tuple(cmd.pos)}"
            else:
                delta = np.asarray(_UNIT[cmd.dir]) * float(cmd.dist)
                what = f"{cmd.dir} {float(cmd.dist):g} m"
            moved = targets + delta
            moved[:, 2] = np.maximum(moved[:, 2], ENVELOPE["z"][0])
            self._fly_to(moved)
            return self._log("link_move", f"move {what}", delta=delta.round(2).tolist())

        if intent == "altitude":
            targets = (self.controller.targets if self.controller.assigned else positions).copy()
            targets[:, 2] = float(cmd.z)
            self._fly_to(targets)
            return self._log("link_altitude", f"altitude {float(cmd.z):g} m", z=float(cmd.z))

        if intent in ("land", "abort"):
            self._fly_to(np.column_stack([positions[:, :2], np.zeros(self.env.n)]))
            return self._log(f"link_{intent}", "descend in place, motors off on contact")

        return self._hold_or_noop(f"no mapping for {intent}", intent)

    def reset(self) -> bool:
        """The non-vocal reset out of ABORTED, fed the two reports the state machine asks for."""
        positions, velocities = self.env.positions, self.env.velocities
        grounded = bool(np.all(positions[:, 2] <= GROUND_Z))
        at_rest = bool(np.all(np.linalg.norm(velocities, axis=1) < REST_SPEED))
        ok = self.fsm.manual_reset(grounded, at_rest)
        if ok:
            self.motors_on = False
            self._takeoff_z = None
        return ok

    # ------------------------------------------------------------------ simulation

    def tick(self) -> None:
        """Advance the backend one step, then report the vehicles to the state machine."""
        if self.motors_on:
            accel = self.controller.step(self.env.positions, self.env.velocities)
            positions, velocities = self.env.step(accel)
            if self.clamp:
                positions, velocities, activations = separation_clamp(positions, velocities)
                self.clamp_activations += activations
                if activations:
                    self.env.set_state(positions, velocities)
        else:
            positions, velocities = self.env.idle()
        self.ticks += 1

        distance = np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)
        np.fill_diagonal(distance, np.inf)
        closest = float(distance.min())
        self.min_pair_distance = min(self.min_pair_distance, closest)
        if closest < COLLISION_DISTANCE:
            self.collisions += 1

        self._feedback(positions)

    def _feedback(self, positions: np.ndarray) -> None:
        state = self.fsm.state
        if state == FlightState.TAKING_OFF and self._takeoff_z is not None:
            if np.all(np.abs(positions[:, 2] - self._takeoff_z) <= ALTITUDE_TOLERANCE):
                self.fsm.on_altitude_reached()
        elif state in (FlightState.LANDING, FlightState.ABORTED) and self.motors_on:
            if np.all(positions[:, 2] <= GROUND_Z):
                if state == FlightState.LANDING:
                    self.fsm.on_ground_contact()
                self.motors_on = False
                self._takeoff_z = None
                self._log("link_motors_off", "ground contact: motors off", state=self.fsm.state.value)

    # ------------------------------------------------------------------ helpers

    def _fly_to(self, targets: np.ndarray) -> None:
        self.controller.hold_at(targets)
        self.motors_on = True

    def _unsupported(self, cmd) -> str | None:
        # A take-off or a landing has already moved the whole swarm's flight state, so it is
        # executed for the whole swarm; honouring it for a subset would strand the state machine
        # in TAKING_OFF or LANDING, waiting for vehicles that were never commanded.
        if getattr(cmd, "ids", None) is not None and cmd.intent not in ("takeoff", "land"):
            return f"ids {cmd.ids}: the controller commands the whole swarm"
        if cmd.intent == "formation" and cmd.shape not in SHAPES:
            return f"no slot generator for {cmd.shape}"
        return None

    def _hold_or_noop(self, reason: str, intent: str) -> str:
        if self.fsm.is_legal("hover") and self.motors_on:
            self._fly_to(self.env.positions)
            return self._log("link_unsupported_hold", f"{reason} -> hold", intent=intent, reason=reason)
        return self._log("link_unsupported_noop", f"{reason} -> no-op", intent=intent, reason=reason)

    def _log(self, event: str, text: str, **fields) -> str:
        logger.info("link: %s", text, extra={"event": event, **fields})
        return text
