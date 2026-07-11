"""Layer 2 --- semantic validator (PRD Sec. 5.2, validate.py).

Guarantees semantic correctness and physical safety:
1. Required-slot matrix enforcement.
2. Physical envelope clamping: CLAMP AND LOG, NEVER REJECT.
   - Altitude z in [0.5, 15.0] m (enforced for z, alt, and pos.z per ADR-0001).
   - Euclidean norm |pos| <= 50.0 m with proportional vector scaling.
   - Yaw periodic angle wrapping to [-180.0, 180.0] deg per ADR-0001.
   - Non-finite numbers (NaN, Inf) rejected with fallback to HOVER.
3. Drone identifier validation: ids in {0 ... SWARM_SIZE-1}, deduplicated and sorted.
   - Out-of-range ids dropped with a log entry.
   - All ids dropped => widening event logged and scope widened to all drones.
4. Fallback: validation failure, parse failure, or truncation => HOVER with structured log entry.
"""

from __future__ import annotations

import json
import logging
import math
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ValidationError as PydanticValidationError

from schema.logger import get_structured_logger
from schema.schema import (
    DECIMALS,
    DIRECTIONS,
    ENVELOPE,
    INTENTS,
    POS_MAX_NORM,
    SHAPES,
    SWARM_SIZE,
    Abort,
    Altitude,
    Command,
    Formation,
    Hover,
    Land,
    Move,
    Rotate,
    SetParam,
    Takeoff,
    Unknown,
)

__all__ = [
    "ValidationError",
    "validate",
    "validate_command",
    "logger",
]

logger = get_structured_logger("schema.validate")


class ValidationError(ValueError):
    """Raised when semantic validation fails and fallback is disabled."""


def _clamp_scalar(slot: str, value: float) -> float:
    """Clamp a scalar value to its physical envelope and log if changed."""
    if not math.isfinite(value):
        raise ValidationError(f"Non-finite numeric value for slot {slot!r}: {value}")

    low, high = ENVELOPE[slot]
    if value < low:
        logger.info(
            "Envelope clamp: slot=%s original=%s clamped=%s (below lower bound %s)",
            slot,
            value,
            low,
            low,
            extra={"event": "envelope_clamp", "slot": slot, "original": value, "clamped": low},
        )
        return low
    if value > high:
        logger.info(
            "Envelope clamp: slot=%s original=%s clamped=%s (above upper bound %s)",
            slot,
            value,
            high,
            high,
            extra={"event": "envelope_clamp", "slot": slot, "original": value, "clamped": high},
        )
        return high
    return value


def _wrap_yaw(yaw: float) -> float:
    """Wrap angular yaw heading periodically into [-180.0, 180.0] deg (ADR-0001)."""
    if not math.isfinite(yaw):
        raise ValidationError(f"Non-finite yaw value: {yaw}")

    # Identity on canonical [-180.0, 180.0] interval
    if -180.0 <= yaw <= 180.0:
        return round(yaw, DECIMALS)

    wrapped = round(((yaw + 180.0) % 360.0) - 180.0, DECIMALS)
    if wrapped == -180.0 and yaw > 0:
        wrapped = 180.0

    if wrapped != round(yaw, DECIMALS):
        logger.info(
            "Angle wrapped: slot=yaw original=%s wrapped=%s",
            yaw,
            wrapped,
            extra={"event": "angle_wrap", "slot": "yaw", "original": yaw, "wrapped": wrapped},
        )
    return wrapped


def _clamp_pos(pos: tuple[float, float, float]) -> tuple[float, float, float]:
    """Clamp 3D position vector: altitude z in [0.5, 15.0] m and rounded Euclidean norm round(|pos|, 1) <= 50.0 m (ADR-0001)."""
    x, y, z = pos
    if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
        raise ValidationError(f"Non-finite coordinate in pos vector: {pos}")

    # Enforce vertical flight ceiling and ground floor on z coordinate first
    z_low, z_high = ENVELOPE["z"]
    clamped_z = min(max(z, z_low), z_high)
    if clamped_z != z:
        logger.info(
            "Envelope clamp: slot=pos.z original=%s clamped=%s",
            z,
            clamped_z,
            extra={"event": "envelope_clamp", "slot": "pos.z", "original": z, "clamped": clamped_z},
        )

    # Check 3D Euclidean norm
    norm = math.sqrt(x * x + y * y + clamped_z * clamped_z)
    if norm > POS_MAX_NORM:
        # Scale horizontal displacement to fit within arena sphere at altitude clamped_z
        # This guarantees altitude never falls below ground floor (0.5 m)
        r_xy = math.hypot(x, y)
        max_r_xy = math.sqrt(max(0.0, POS_MAX_NORM * POS_MAX_NORM - clamped_z * clamped_z))
        if r_xy > max_r_xy and r_xy > 0.0:
            scale = max_r_xy / r_xy
            cx = round(x * scale, DECIMALS)
            cy = round(y * scale, DECIMALS)
        else:
            cx = round(x, DECIMALS)
            cy = round(y, DECIMALS)
        cz = round(clamped_z, DECIMALS)
    else:
        cx = round(x, DECIMALS)
        cy = round(y, DECIMALS)
        cz = round(clamped_z, DECIMALS)

    # Guard against 1-decimal rounding pushing norm over POS_MAX_NORM in both paths
    was_adjusted = False
    while round(math.sqrt(cx * cx + cy * cy + cz * cz), DECIMALS) > POS_MAX_NORM:
        was_adjusted = True
        if abs(cx) >= abs(cy) and abs(cx) > 0:
            cx = round(cx - math.copysign(0.1, cx), DECIMALS)
        elif abs(cy) > 0:
            cy = round(cy - math.copysign(0.1, cy), DECIMALS)
        else:
            break

    clamped = (cx, cy, cz)
    if norm > POS_MAX_NORM or was_adjusted:
        logger.info(
            "Envelope clamp: slot=pos original=%s norm=%.2f clamped=%s",
            pos,
            norm,
            clamped,
            extra={"event": "envelope_clamp", "slot": "pos", "original": list(pos), "norm": round(norm, 2), "clamped": list(clamped)},
        )

    return clamped


def _filter_ids(raw_ids: Any) -> list[int] | None:
    """Filter ids to {0 ... SWARM_SIZE-1}, deduplicate, sort ascending.

    Out-of-range ids are dropped with a log line.
    Empty list after filtering => None (all drones) with explicit widening log.
    """
    if raw_ids is None:
        return None
    if not isinstance(raw_ids, (list, tuple)):
        raise ValidationError(f"ids must be a sequence of integers, got {type(raw_ids).__name__}")

    valid_ids: list[int] = []
    for item in raw_ids:
        try:
            val = int(item)
        except (ValueError, TypeError):
            logger.info(
                "Identifier dropped: non-integer id=%r",
                item,
                extra={"event": "id_dropped", "raw_id": item},
            )
            continue

        if 0 <= val < SWARM_SIZE:
            valid_ids.append(val)
        else:
            logger.info(
                "Identifier dropped: out-of-range id=%d (allowed [0, %d))",
                val,
                SWARM_SIZE,
                extra={"event": "id_dropped", "dropped_id": val, "swarm_size": SWARM_SIZE},
            )

    sorted_ids = sorted(set(valid_ids))
    if not sorted_ids:
        if raw_ids:
            logger.warning(
                "Identifier list empty after filtering: widening command scope to ALL drones",
                extra={"event": "ids_widened_to_all_drones", "raw_ids": raw_ids},
            )
        return None
    return sorted_ids


def _handle_fallback(reason: str, raw_input: Any, fallback: bool) -> Hover:
    """Log structured fallback record and return safe Hover command, or raise."""
    logger.warning(
        "Validation fallback to HOVER: reason=%s raw_input=%r",
        reason,
        raw_input,
        extra={"event": "validation_fallback", "reason": reason, "raw_input": str(raw_input)},
    )
    if not fallback:
        raise ValidationError(reason)
    return Hover(intent="hover")


def validate(raw: str | Mapping[str, Any] | BaseModel, fallback: bool = True) -> Command:
    """Validate and clamp a command, returning a safe Command object.

    On any validation failure, parse failure, or truncation:
      - If fallback=True (default): logs a structured event and returns Hover(intent="hover").
      - If fallback=False: raises ValidationError.
    """
    # 1. Parse raw input
    if isinstance(raw, BaseModel):
        data: dict[str, Any] = raw.model_dump()
    elif isinstance(raw, Mapping):
        data = dict(raw)
    elif isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                return _handle_fallback(f"JSON must be an object, got {type(parsed).__name__}", raw, fallback)
            data = parsed
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return _handle_fallback(f"JSON parse error: {e}", raw, fallback)
    else:
        return _handle_fallback(f"Expected str, Mapping, or BaseModel, got {type(raw).__name__}", raw, fallback)

    # 2. Check intent
    intent = data.get("intent")
    if intent not in INTENTS:
        return _handle_fallback(f"Unknown or missing intent: {intent!r}", raw, fallback)

    # 3. Filter and normalize ids if present
    if "ids" in data:
        try:
            data["ids"] = _filter_ids(data["ids"])
        except ValidationError as e:
            return _handle_fallback(str(e), raw, fallback)

    # 4. Enforce required-slot matrix & intent-specific constraints
    try:
        if intent == "formation":
            shape = data.get("shape")
            if shape not in SHAPES:
                return _handle_fallback(f"Formation requires valid shape, got {shape!r}", raw, fallback)
            if shape == "circle":
                if data.get("radius") is None:
                    return _handle_fallback("Formation shape circle requires radius", raw, fallback)
                if data.get("spacing") is not None:
                    logger.info(
                        "Superfluous slot dropped: slot=spacing on formation circle",
                        extra={"event": "slot_dropped", "slot": "spacing", "shape": "circle"},
                    )
                    data.pop("spacing", None)
            elif shape in ("line", "grid", "column"):
                if data.get("spacing") is None:
                    return _handle_fallback(f"Formation shape {shape} requires spacing", raw, fallback)
                if data.get("radius") is not None:
                    logger.info(
                        "Superfluous slot dropped: slot=radius on formation %s",
                        shape,
                        extra={"event": "slot_dropped", "slot": "radius", "shape": shape},
                    )
                    data.pop("radius", None)
            elif shape == "wedge":
                if data.get("radius") is not None:
                    logger.info(
                        "Superfluous slot dropped: slot=radius on formation wedge",
                        extra={"event": "slot_dropped", "slot": "radius", "shape": "wedge"},
                    )
                    data.pop("radius", None)
            elif shape == "flock":
                for superfluous in ("radius", "spacing"):
                    if data.get(superfluous) is not None:
                        logger.info(
                            "Superfluous slot dropped: slot=%s on formation flock",
                            superfluous,
                            extra={"event": "slot_dropped", "slot": superfluous, "shape": "flock"},
                        )
                        data.pop(superfluous, None)

        elif intent == "move":
            has_pos = data.get("pos") is not None
            has_dir = data.get("dir") is not None
            has_dist = data.get("dist") is not None

            if has_pos and (has_dir or has_dist):
                return _handle_fallback("Move command cannot specify both pos and dir/dist", raw, fallback)
            if not has_pos and not (has_dir and has_dist):
                return _handle_fallback("Move requires exactly one of pos or (dir and dist)", raw, fallback)
            if has_dir and data["dir"] not in DIRECTIONS:
                return _handle_fallback(f"Invalid move direction: {data['dir']!r}", raw, fallback)
            if has_pos:
                pos_val = data["pos"]
                if not (isinstance(pos_val, (list, tuple)) and len(pos_val) == 3):
                    return _handle_fallback("Move pos must be a 3-element vector [x, y, z]", raw, fallback)

        elif intent == "altitude":
            if data.get("z") is None:
                return _handle_fallback("Altitude command requires z slot", raw, fallback)

        elif intent == "rotate":
            if data.get("yaw") is None:
                return _handle_fallback("Rotate command requires yaw slot", raw, fallback)

        elif intent == "set_param":
            has_speed = data.get("speed") is not None
            has_spacing = data.get("spacing") is not None
            has_alt = data.get("alt") is not None
            if not (has_speed or has_spacing or has_alt):
                return _handle_fallback(
                    "SetParam requires at least one of speed, spacing, or alt", raw, fallback
                )

        elif intent == "abort":
            # Abort takes no slots. Drop all stray slots with a structured log event
            # so an emergency abort NEVER degrades to Hover fallback.
            stray_keys = [k for k in list(data) if k != "intent"]
            for k in stray_keys:
                logger.info(
                    "Superfluous slot dropped on emergency abort: slot=%s",
                    k,
                    extra={"event": "slot_dropped", "slot": k, "intent": "abort"},
                )
                data.pop(k, None)

        elif intent == "unknown":
            stray_keys = [k for k in list(data) if k != "intent"]
            for k in stray_keys:
                data.pop(k, None)

        # 5. Apply physical envelope clamping & wrapping to present slots
        for slot in ("radius", "spacing", "z", "speed", "dist", "alt"):
            if data.get(slot) is not None:
                val = float(data[slot])
                data[slot] = _clamp_scalar(slot, val)

        if data.get("yaw") is not None:
            data["yaw"] = _wrap_yaw(float(data["yaw"]))

        if data.get("pos") is not None:
            pos_tuple = (float(data["pos"][0]), float(data["pos"][1]), float(data["pos"][2]))
            data["pos"] = _clamp_pos(pos_tuple)

        # 6. Instantiate typed Pydantic model
        clean_data = {k: v for k, v in data.items() if v is not None}

        if intent == "formation":
            return Formation(**clean_data)
        elif intent == "move":
            return Move(**clean_data)
        elif intent == "altitude":
            return Altitude(**clean_data)
        elif intent == "takeoff":
            return Takeoff(**clean_data)
        elif intent == "land":
            return Land(**clean_data)
        elif intent == "hover":
            return Hover(**clean_data)
        elif intent == "abort":
            return Abort(**clean_data)
        elif intent == "rotate":
            return Rotate(**clean_data)
        elif intent == "set_param":
            return SetParam(**clean_data)
        elif intent == "unknown":
            return Unknown(**clean_data)
        else:
            return _handle_fallback(f"Unmapped intent {intent}", raw, fallback)

    except (ValidationError, ValueError, TypeError, PydanticValidationError) as e:
        return _handle_fallback(f"Schema validation error: {e}", raw, fallback)


validate_command = validate
