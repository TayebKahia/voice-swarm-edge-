"""Command schema v1.0 --- the frozen contract.

Frozen on D1 per PRD Sec. 5. Ten intents, single-line JSON wire format, fixed
key order, null fields omitted.

Omitting null fields rather than emitting them explicitly cuts a typical
command from roughly 40 tokens to about 18 --- at Pi 5 decode rates, close to
a full second of latency per command (PRD Sec. 5).

This module is the one place a valid command is defined. `data/`, `train/`,
`runtime/`, and `eval/` all import it. Duplicating any part of it elsewhere
produces a silent accuracy collapse with no error message.

Three validation layers guard the output:

    layer 1  schema/cmd.gbnf     structure  (guaranteed by the decoder)
    layer 2  schema/validate.py  meaning    (clamps and logs, never rejects)
    layer 3  swarm/fsm.py        legality   (Table 9, rejects to HOVER)

This module holds the *shape* of a command: vocabularies, field order, and the
physical envelope. The *rules* --- required slots, clamping, identifier
filtering --- are layer 2, in validate.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "GRAMMAR_PATH",
    "SWARM_SIZE",
    "INTENTS",
    "SHAPES",
    "DIRECTIONS",
    "KEY_ORDER",
    "ENVELOPE",
    "POS_MAX_NORM",
    "DECIMALS",
    "Command",
    "COMMAND_MODELS",
    "Formation",
    "Move",
    "Altitude",
    "Takeoff",
    "Land",
    "Hover",
    "Abort",
    "Rotate",
    "SetParam",
    "Unknown",
]

# The grammar handed to llama.cpp as --grammar-file. Layer 1 lives in a file
# rather than a string because llama.cpp reads it directly and because the
# spike-S3 smoke test runs against the same bytes the runtime uses.
GRAMMAR_PATH = Path(__file__).with_name("cmd.gbnf")

# N in FR-7. Identifiers are a subset of {0 ... SWARM_SIZE-1}.
SWARM_SIZE = 5

# Floats are rounded to one decimal everywhere, matching the `num` rule's
# precision limit in cmd.gbnf. The metric matches what the decoder can
# produce (PRD Sec. 6.1, rule 3).
DECIMALS = 1

INTENTS: tuple[str, ...] = (
    "formation",
    "move",
    "altitude",
    "takeoff",
    "land",
    "hover",
    "abort",
    "rotate",
    "set_param",
    "unknown",
)

SHAPES: tuple[str, ...] = ("circle", "line", "wedge", "grid", "column", "flock")

DIRECTIONS: tuple[str, ...] = (
    "north",
    "south",
    "east",
    "west",
    "up",
    "down",
    "forward",
    "back",
    "left",
    "right",
)

Shape = Literal["circle", "line", "wedge", "grid", "column", "flock"]
Direction = Literal[
    "north", "south", "east", "west", "up", "down", "forward", "back", "left", "right"
]


# --- the physical envelope (PRD Sec. 5.2) --------------------------------
#
# Layer 2 clamps to these and logs; it never rejects. A clamped command is
# safer than a dropped one.
#
# `dist` and `alt` are NOT given ranges by the PRD, but cmd.gbnf can emit
# either up to 999.9, so a value is required to write the code at all. The
# ranges below are reasoned by analogy and recorded in docs/adr/0001; they are
# the one place this module goes beyond the frozen contract.
ENVELOPE: dict[str, tuple[float, float]] = {
    "radius": (1.0, 10.0),
    "spacing": (1.0, 5.0),
    "z": (0.5, 15.0),
    "speed": (0.2, 2.0),
    "yaw": (-180.0, 180.0),  # Canonical range; enforced via periodic wrapping in _wrap_yaw (ADR-0001)
    "dist": (0.0, 50.0),  # ADR-0001, by analogy with POS_MAX_NORM
    "alt": (0.5, 15.0),  # ADR-0001, by analogy with `z`
}

# |pos| <= 50 m. Read as the Euclidean norm and clamped by scaling the vector,
# so the commanded direction survives the clamp --- per-component clamping
# would silently rotate the target. ADR-0001.
POS_MAX_NORM = 50.0


class _Command(BaseModel):
    """Base for the ten intent models.

    `extra="forbid"` makes an unexpected key a validation failure rather than
    something silently carried into the canonical form, where it would corrupt
    an exact-match comparison. Layer 1 already makes stray keys unemittable;
    this is the boundary check for hand-authored references and for the
    grammar-off ablation in Table 19, where structure is no longer guaranteed.

    Field declaration order IS the wire order --- see KEY_ORDER below.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    def to_wire(self) -> str:
        from schema.canon import canon
        return canon(self)


class Formation(_Command):
    intent: Literal["formation"] = "formation"
    shape: Shape
    radius: float | None = None
    spacing: float | None = None
    ids: list[int] | None = None


class Move(_Command):
    intent: Literal["move"] = "move"
    pos: tuple[float, float, float] | None = None
    dir: Direction | None = None
    dist: float | None = None
    speed: float | None = None
    ids: list[int] | None = None


class Altitude(_Command):
    intent: Literal["altitude"] = "altitude"
    z: float
    ids: list[int] | None = None


class Takeoff(_Command):
    intent: Literal["takeoff"] = "takeoff"
    z: float | None = None
    ids: list[int] | None = None


class Land(_Command):
    intent: Literal["land"] = "land"
    ids: list[int] | None = None


class Hover(_Command):
    intent: Literal["hover"] = "hover"
    ids: list[int] | None = None


class Abort(_Command):
    intent: Literal["abort"] = "abort"


class Rotate(_Command):
    intent: Literal["rotate"] = "rotate"
    yaw: float
    ids: list[int] | None = None


class SetParam(_Command):
    intent: Literal["set_param"] = "set_param"
    speed: float | None = None
    spacing: float | None = None
    alt: float | None = None


class Unknown(_Command):
    intent: Literal["unknown"] = "unknown"


COMMAND_MODELS: tuple[type[_Command], ...] = (
    Formation,
    Move,
    Altitude,
    Takeoff,
    Land,
    Hover,
    Abort,
    Rotate,
    SetParam,
    Unknown,
)

Command = Annotated[
    Union[
        Formation,
        Move,
        Altitude,
        Takeoff,
        Land,
        Hover,
        Abort,
        Rotate,
        SetParam,
        Unknown,
    ],
    Field(discriminator="intent"),
]

# Rule 1 of the canonical form is "key order fixed by schema declaration
# order" (PRD Sec. 6.1). Deriving it from the models rather than restating it
# makes that rule literally true: there is no second list to drift.
KEY_ORDER: dict[str, tuple[str, ...]] = {
    model.model_fields["intent"].default: tuple(model.model_fields)
    for model in COMMAND_MODELS
}

# Guard against a model being added to the union but not to COMMAND_MODELS,
# which would leave canon() without a key order for that intent and silently
# fall back to alphabetical.
assert set(KEY_ORDER) == set(INTENTS), (
    f"KEY_ORDER covers {sorted(KEY_ORDER)}, INTENTS declares {sorted(INTENTS)}"
)
