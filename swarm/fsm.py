"""Layer 3 --- Flight State Machine and Table 9 legality (PRD Sec. 5.3, swarm/fsm.py).

Enforces flight state transitions and command legality:
1. States: LANDED, TAKING_OFF, FLYING, LANDING, ABORTED.
2. Transitions:
   - LANDED -> TAKING_OFF on takeoff
   - TAKING_OFF -> FLYING on target altitude reached
   - FLYING -> LANDING on land
   - LANDING -> LANDED on ground contact
   - abort from any airborne state -> ABORTED
3. Table 9 legality:
    - Rejections resolve to safe HOVER where Table 9 permits hovering
      (TAKING_OFF, FLYING). In states where hover is illegal (LANDED,
      LANDING, ABORTED), rejections resolve to a safe no-op (None).
    - abort in LANDED/ABORTED is a logged no-op, never an error.
    - unknown is never dispatched, logged only.
4. Manual non-vocal reset:
   - Recovery from ABORTED only when all drones report ground contact and near-zero velocity.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from enum import Enum
from typing import Any

from pydantic import BaseModel

from schema.logger import get_structured_logger
from schema.schema import Hover
from schema.validate import validate

__all__ = [
    "FlightState",
    "FlightStateMachine",
    "TABLE_9_LEGALITY",
    "logger",
]

logger = get_structured_logger("swarm.fsm")


class FlightState(str, Enum):
    LANDED = "LANDED"
    TAKING_OFF = "TAKING_OFF"
    FLYING = "FLYING"
    LANDING = "LANDING"
    ABORTED = "ABORTED"


# AIRBORNE_STATES removed: rejection fallback now uses is_legal("hover", ...)
# directly against Table 9, eliminating a second hand-maintained encoding
# that previously disagreed with TABLE_9_LEGALITY for LANDING.

# Table 9: Intent legality per state
TABLE_9_LEGALITY: dict[str, set[FlightState]] = {
    "takeoff": {FlightState.LANDED},
    "land": {FlightState.TAKING_OFF, FlightState.FLYING},
    "hover": {FlightState.TAKING_OFF, FlightState.FLYING},
    "abort": {FlightState.TAKING_OFF, FlightState.FLYING, FlightState.LANDING},
    "move": {FlightState.FLYING},
    "altitude": {FlightState.FLYING},
    "rotate": {FlightState.FLYING},
    "formation": {FlightState.FLYING},
    "set_param": {
        FlightState.LANDED,
        FlightState.TAKING_OFF,
        FlightState.FLYING,
        FlightState.LANDING,
    },
    "unknown": set(),  # Never dispatched
}


class FlightStateMachine:
    """Swarm Flight State Machine implementing PRD Table 9."""

    def __init__(self, initial_state: FlightState = FlightState.LANDED) -> None:
        self.state = initial_state

    def is_legal(self, intent: str, state: FlightState | None = None) -> bool:
        """Check if an intent is legal in the given (or current) state."""
        current = state if state is not None else self.state
        legal_states = TABLE_9_LEGALITY.get(intent, set())
        return current in legal_states

    def on_altitude_reached(self) -> FlightState:
        """Transition from TAKING_OFF to FLYING when altitude is attained."""
        if self.state == FlightState.TAKING_OFF:
            logger.info(
                "FSM transition: TAKING_OFF -> FLYING (target altitude reached)",
                extra={"event": "fsm_transition", "from": "TAKING_OFF", "to": "FLYING"},
            )
            self.state = FlightState.FLYING
        return self.state

    def on_ground_contact(self) -> FlightState:
        """Transition from LANDING to LANDED on ground contact."""
        if self.state == FlightState.LANDING:
            logger.info(
                "FSM transition: LANDING -> LANDED (ground contact reported)",
                extra={"event": "fsm_transition", "from": "LANDING", "to": "LANDED"},
            )
            self.state = FlightState.LANDED
        return self.state

    def manual_reset(self, all_ground_contact: bool, all_near_zero_velocity: bool) -> bool:
        """Manual non-vocal recovery from ABORTED to LANDED.

        Only permitted when every drone reports ground contact and near-zero velocity.
        """
        if self.state != FlightState.ABORTED:
            logger.warning(
                "Manual reset attempted while not in ABORTED state (current: %s)",
                self.state.value,
                extra={"event": "fsm_reset_rejected", "current_state": self.state.value},
            )
            return False

        if all_ground_contact and all_near_zero_velocity:
            logger.info(
                "FSM manual reset: ABORTED -> LANDED (ground contact and zero velocity confirmed)",
                extra={"event": "fsm_reset_success", "from": "ABORTED", "to": "LANDED"},
            )
            self.state = FlightState.LANDED
            return True

        logger.warning(
            "Manual reset refused: preconditions not met (ground_contact=%s, zero_velocity=%s)",
            all_ground_contact,
            all_near_zero_velocity,
            extra={
                "event": "fsm_reset_refused",
                "ground_contact": all_ground_contact,
                "zero_velocity": all_near_zero_velocity,
            },
        )
        return False

    def handle_command(self, cmd_input: Command | Mapping[str, Any] | str) -> Command | None:
        """Process an incoming command against Table 9 legality.

        Preserves original intent in audit logs and resolves rejections correctly:
          - Validated Command to dispatch if legal.
          - Abort command if abort triggered in airborne state.
          - Rejections resolve to HOVER only where Table 9 permits hovering
            (TAKING_OFF, FLYING). In states where hover is illegal (LANDED,
            LANDING, ABORTED), rejections resolve to a safe no-op (None).
          - None if unknown intent or abort no-op.
        """
        # Extract original intent before any Layer 2 fallback for audit preservation
        raw_intent: str | None = None
        if isinstance(cmd_input, str):
            try:
                raw_intent = json.loads(cmd_input).get("intent")
            except Exception:
                pass
        elif isinstance(cmd_input, Mapping):
            raw_intent = cmd_input.get("intent")  # type: ignore[assignment]
        elif isinstance(cmd_input, BaseModel):
            raw_intent = getattr(cmd_input, "intent", None)

        # Validate through Layer 2
        cmd = validate(cmd_input)
        effective_intent = raw_intent or cmd.intent

        # 1. Unknown: never dispatched, logged only
        if effective_intent == "unknown":
            logger.info(
                "Command intent 'unknown' received; logged only, never dispatched",
                extra={"event": "fsm_unknown_logged", "state": self.state.value},
            )
            return None

        # 2. Abort: legal in TAKING_OFF, FLYING, LANDING; logged no-op otherwise
        if effective_intent == "abort":
            if self.is_legal("abort", self.state):
                logger.warning(
                    "FSM EMERGENCY ABORT: %s -> ABORTED",
                    self.state.value,
                    extra={"event": "fsm_abort_triggered", "from": self.state.value, "to": "ABORTED"},
                )
                self.state = FlightState.ABORTED
                return cmd
            else:
                logger.info(
                    "Abort received in %s state: logged no-op, never an error",
                    self.state.value,
                    extra={"event": "fsm_abort_noop", "state": self.state.value},
                )
                return None

        # 3. Check Table 9 legality
        if self.is_legal(effective_intent, self.state):
            # Apply state transitions
            if effective_intent == "takeoff":
                logger.info(
                    "FSM transition: LANDED -> TAKING_OFF",
                    extra={"event": "fsm_transition", "from": "LANDED", "to": "TAKING_OFF"},
                )
                self.state = FlightState.TAKING_OFF
            elif effective_intent == "land":
                logger.info(
                    "FSM transition: %s -> LANDING",
                    self.state.value,
                    extra={"event": "fsm_transition", "from": self.state.value, "to": "LANDING"},
                )
                self.state = FlightState.LANDING
            return cmd

        # 4. Rejected: resolve to HOVER only where Table 9 permits hovering
        if self.is_legal("hover", self.state):
            logger.warning(
                "FSM command rejected: intent=%s is illegal in state=%s. Resolving to HOVER.",
                effective_intent,
                self.state.value,
                extra={
                    "event": "fsm_command_rejected",
                    "intent": effective_intent,
                    "state": self.state.value,
                    "fallback": "HOVER",
                },
            )
            return Hover(intent="hover")
        else:
            # Table 9 forbids HOVER in this state (LANDED, LANDING, ABORTED).
            # Returning None lets the current trajectory complete safely:
            #   - LANDED: drone stays grounded
            #   - LANDING: descent completes uninterrupted
            #   - ABORTED: remains aborted until manual reset
            logger.warning(
                "FSM command rejected: intent=%s is illegal in state=%s. Safe no-op (hover illegal here).",
                effective_intent,
                self.state.value,
                extra={
                    "event": "fsm_command_rejected",
                    "intent": effective_intent,
                    "state": self.state.value,
                    "action": "noop_hover_illegal",
                },
            )
            return None
