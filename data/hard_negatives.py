"""Hard negatives --- `02_dataset_plan.md` §3.3, the highest-value 150 rows.

Near-miss pairs that differ in *one decisive token*. These are what separate a
model that has learned the task from one that has learned keyword
co-occurrence, and they are the only rows in the corpus where the surface form
is authored rather than composed: the trap *is* the wording, so it cannot be
delegated to a frame bank.

Every row here is a **contrast group** member. A group holds two or three
utterances that share a decisive token and disagree about what it means:

    "form a circle, radius five"   -> formation/circle
    "circle back twenty metres"    -> move/back
    "circle around the tree"       -> unknown   (no object model exists)

**All members of a group are in `train` families, by construction.** Splitting a
contrast group across a split boundary would put the easy half in training and
the hard half in test, which measures nothing and would trip Gate 2's
surface-form check besides.

## Negation --- and the one place the corpus is deliberately asymmetric

`02_dataset_plan.md` §3.3 requires `"don't land yet"` -> `hover`, not `land`: "a
model that gets this wrong lands a swarm on a 'don't land' command". So negated
commands map to `hover`. Layer 3 makes that safe in every state --- a `hover`
rejected in `LANDED` resolves to a grounded no-op rather than a Table 9
violation (`swarm/fsm.py`).

**`abort` is exempt, on purpose.** No utterance containing an abort word maps to
anything other than `{"intent":"abort"}` --- no `"don't abort"`, no
`"we aborted the last run"` -> `unknown`. The two error directions are not
symmetric: a spurious abort stops a swarm that did not need stopping, while a
missed abort is the failure the reflex path exists to prevent. Teaching the model
that "abort" is sometimes not an abort buys a little precision on a rare
utterance and pays for it in the one case that matters. Recorded in
`docs/adr/0002`.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["HardNegative", "HARD_NEGATIVES", "GROUPS"]


@dataclass(frozen=True)
class HardNegative:
    """One authored near-miss row: text, its label, and the family it belongs to."""

    group: str
    family_id: str
    text: str
    gold: dict[str, object]


def _hn(group: str, family_id: str, text: str, gold: dict[str, object]) -> HardNegative:
    return HardNegative(group, family_id, text, gold)


# --- the decisive-token groups --------------------------------------------
#
# Command-side members. Each lands in the train family whose slot pattern its
# label matches, so the family's own generated rows and its hard negatives share
# one label shape and differ only in how deliberately adversarial the wording is.

_CIRCLE: list[HardNegative] = [
    # "circle" the formation ...
    _hn("circle", "F001", "form a circle, radius five", {"intent": "formation", "shape": "circle", "radius": 5.0}),
    _hn("circle", "F001", "circle up at three metres radius", {"intent": "formation", "shape": "circle", "radius": 3.0}),
    _hn("circle", "F001", "everyone into a circle of radius eight", {"intent": "formation", "shape": "circle", "radius": 8.0}),
    _hn("circle", "F001", "make a ring two metres radius", {"intent": "formation", "shape": "circle", "radius": 2.0}),
    # ... versus "circle back", which is a move ...
    _hn("circle", "F052", "circle back twenty metres", {"intent": "move", "dir": "back", "dist": 20.0}),
    _hn("circle", "F052", "circle back ten metres", {"intent": "move", "dir": "back", "dist": 10.0}),
    _hn("circle", "F052", "circle back on yourselves five metres", {"intent": "move", "dir": "back", "dist": 5.0}),
    _hn("circle", "F052", "circle back thirty", {"intent": "move", "dir": "back", "dist": 30.0}),
    # ... versus "circle around the tree", which the system cannot ground.
    _hn("circle", "F117", "circle around the tree", {"intent": "unknown"}),
    _hn("circle", "F117", "circle around that building", {"intent": "unknown"}),
]

_DROP: list[HardNegative] = [
    _hn("drop", "F055", "drop to two metres", {"intent": "altitude", "z": 2.0}),
    _hn("drop", "F055", "drop to one point five metres", {"intent": "altitude", "z": 1.5}),
    _hn("drop", "F055", "drop down to four metres", {"intent": "altitude", "z": 4.0}),
    _hn("drop", "F055", "drop to 3 m", {"intent": "altitude", "z": 3.0}),
    _hn("drop", "F117", "drop the payload", {"intent": "unknown"}),
    _hn("drop", "F117", "drop the package", {"intent": "unknown"}),
]

_LINE: list[HardNegative] = [
    _hn("line", "F006", "line up two metres apart", {"intent": "formation", "shape": "line", "spacing": 2.0}),
    _hn("line", "F006", "line up with three metres between you", {"intent": "formation", "shape": "line", "spacing": 3.0}),
    _hn("line", "F006", "line abreast, one metre spacing", {"intent": "formation", "shape": "line", "spacing": 1.0}),
    _hn("line", "F006", "get in a line four metres apart", {"intent": "formation", "shape": "line", "spacing": 4.0}),
    _hn("line", "F117", "line of sight is clear", {"intent": "unknown"}),
    _hn("line", "F117", "the line is busy", {"intent": "unknown"}),
]

_HOLD: list[HardNegative] = [
    # "hold at <altitude>" is an altitude command ...
    _hn("hold", "F061", "hold at four metres", {"intent": "altitude", "z": 4.0}),
    _hn("hold", "F061", "hold at six point five metres", {"intent": "altitude", "z": 6.5}),
    _hn("hold", "F061", "hold altitude ten", {"intent": "altitude", "z": 10.0}),
    # ... "hold position" is a hover ...
    _hn("hold", "F085", "hold position", {"intent": "hover"}),
    _hn("hold", "F085", "hold what you've got", {"intent": "hover"}),
    _hn("hold", "F088", "hold station right there", {"intent": "hover"}),
    # ... and "hold on" is neither.
    _hn("hold", "F117", "hold on, i'm not ready", {"intent": "unknown"}),
    _hn("hold", "F117", "hold that thought", {"intent": "unknown"}),
]

_TAKE: list[HardNegative] = [
    _hn("take", "F067", "take off", {"intent": "takeoff"}),
    _hn("take", "F067", "take off now", {"intent": "takeoff"}),
    _hn("take", "F068", "take off to three metres", {"intent": "takeoff", "z": 3.0}),
    _hn("take", "F116", "take a photo of the field", {"intent": "unknown"}),
    _hn("take", "F116", "take a video while you're up there", {"intent": "unknown"}),
    _hn("take", "F117", "take five, everyone", {"intent": "unknown"}),
]

_UP: list[HardNegative] = [
    _hn("up", "F045", "go up five metres", {"intent": "move", "dir": "up", "dist": 5.0}),
    _hn("up", "F045", "up two metres", {"intent": "move", "dir": "up", "dist": 2.0}),
    _hn("up", "F045", "move up by seven metres", {"intent": "move", "dir": "up", "dist": 7.0}),
    _hn("up", "F062", "climb up to twelve metres", {"intent": "altitude", "z": 12.0}),
    _hn("up", "F062", "climb to fifteen metres", {"intent": "altitude", "z": 15.0}),
    _hn("up", "F062", "come up to nine metres", {"intent": "altitude", "z": 9.0}),
    # Bare comparatives carry no value, so no set_param can be built from them
    # (§2.4 requires at least one of speed / spacing / alt). §3.2 asks for both
    # cases deliberately: resolvable ellipsis below, unresolvable here.
    _hn("up", "F117", "higher", {"intent": "unknown"}),
    _hn("up", "F117", "a bit higher", {"intent": "unknown"}),
]

_SPEED: list[HardNegative] = [
    _hn("speed", "F107", "set the speed to one point five", {"intent": "set_param", "speed": 1.5}),
    _hn("speed", "F107", "slow down to zero point five metres per second", {"intent": "set_param", "speed": 0.5}),
    _hn("speed", "F107", "cap the speed at two metres per second", {"intent": "set_param", "speed": 2.0}),
    _hn("speed", "F107", "limit speed to zero point eight", {"intent": "set_param", "speed": 0.8}),
    _hn("speed", "F117", "faster", {"intent": "unknown"}),
    _hn("speed", "F117", "speed up a bit", {"intent": "unknown"}),
]

_SPACING: list[HardNegative] = [
    _hn("spacing", "F108", "tighten the spacing to two metres", {"intent": "set_param", "spacing": 2.0}),
    _hn("spacing", "F108", "set spacing to one metre", {"intent": "set_param", "spacing": 1.0}),
    _hn("spacing", "F108", "open the gap to four metres", {"intent": "set_param", "spacing": 4.0}),
    _hn("spacing", "F108", "separation three metres from now on", {"intent": "set_param", "spacing": 3.0}),
    _hn("spacing", "F117", "tighter", {"intent": "unknown"}),
    _hn("spacing", "F117", "closer together", {"intent": "unknown"}),
]

_TRANSIT_ALT: list[HardNegative] = [
    _hn("transit_alt", "F109", "set the transit altitude to six metres", {"intent": "set_param", "alt": 6.0}),
    _hn("transit_alt", "F109", "default height five metres", {"intent": "set_param", "alt": 5.0}),
    _hn("transit_alt", "F109", "cruise altitude eight metres", {"intent": "set_param", "alt": 8.0}),
    _hn("transit_alt", "F119", "set the transit", {"intent": "unknown"}),
]

_GRID: list[HardNegative] = [
    _hn("grid", "F011", "form a grid three metres apart", {"intent": "formation", "shape": "grid", "spacing": 3.0}),
    _hn("grid", "F011", "grid formation, two metre spacing", {"intent": "formation", "shape": "grid", "spacing": 2.0}),
    _hn("grid", "F011", "box grid five metres apart", {"intent": "formation", "shape": "grid", "spacing": 5.0}),
    _hn("grid", "F117", "the grid is down", {"intent": "unknown"}),
    _hn("grid", "F117", "check the grid reference", {"intent": "unknown"}),
]

_COLUMN: list[HardNegative] = [
    _hn("column", "F015", "stack up in a column two metres apart", {"intent": "formation", "shape": "column", "spacing": 2.0}),
    _hn("column", "F015", "column, three metre spacing", {"intent": "formation", "shape": "column", "spacing": 3.0}),
    _hn("column", "F117", "check the column of numbers", {"intent": "unknown"}),
    _hn("column", "F117", "the column on the left", {"intent": "unknown"}),
]

_WEDGE: list[HardNegative] = [
    _hn("wedge", "F019", "form a wedge", {"intent": "formation", "shape": "wedge"}),
    _hn("wedge", "F020", "wedge formation, two metres apart", {"intent": "formation", "shape": "wedge", "spacing": 2.0}),
    _hn("wedge", "F117", "wedge the door open", {"intent": "unknown"}),
]

_HOVER_HOMOPHONE: list[HardNegative] = [
    # whisper.cpp mishears "hover" as "hoover" often enough that the corpus has
    # to contain both, on opposite sides of the boundary.
    _hn("hover_homophone", "F085", "hover", {"intent": "hover"}),
    _hn("hover_homophone", "F088", "hover right where you are", {"intent": "hover"}),
    _hn("hover_homophone", "F117", "hoover the floor", {"intent": "unknown"}),
]

_NORTH: list[HardNegative] = [
    _hn("north", "F031", "head north fifteen metres", {"intent": "move", "dir": "north", "dist": 15.0}),
    _hn("north", "F031", "north twenty five metres", {"intent": "move", "dir": "north", "dist": 25.0}),
    _hn("north", "F117", "north of the river is restricted", {"intent": "unknown"}),
    _hn("north", "F117", "the north field is waterlogged", {"intent": "unknown"}),
]

_ROTATE: list[HardNegative] = [
    _hn("rotate", "F099", "rotate ninety degrees", {"intent": "rotate", "yaw": 90.0}),
    _hn("rotate", "F099", "rotate forty five degrees", {"intent": "rotate", "yaw": 45.0}),
    _hn("rotate", "F099", "turn one eighty", {"intent": "rotate", "yaw": 180.0}),
    _hn("rotate", "F117", "rotate the log files", {"intent": "unknown"}),
    _hn("rotate", "F117", "the rotor sounds rough", {"intent": "unknown"}),
]

_LAND: list[HardNegative] = [
    _hn("land", "F077", "land now", {"intent": "land"}),
    _hn("land", "F077", "bring them down and land", {"intent": "land"}),
    _hn("land", "F080", "land on the pad", {"intent": "land"}),
    _hn("land", "F117", "the landing gear looks bent", {"intent": "unknown"}),
    _hn("land", "F117", "we landed that contract", {"intent": "unknown"}),
]

_MOVE_OVER: list[HardNegative] = [
    _hn("move", "F031", "move north ten metres", {"intent": "move", "dir": "north", "dist": 10.0}),
    _hn("move", "F050", "move forward eight metres", {"intent": "move", "dir": "forward", "dist": 8.0}),
    _hn("move", "F117", "move over, i can't see the screen", {"intent": "unknown"}),
    _hn("move", "F117", "that was a smart move", {"intent": "unknown"}),
]

# --- negation: "don't land yet" -> hover, never land ----------------------
#
# F118's own description in data/template_families.py reads "Negation hard
# negatives: don't land yet -> resolves to hover", which is what these rows are.
# Its `intent` metadata column reads "unknown"; the description and the rows are
# the authority (Issue 27).

_NEGATION: list[HardNegative] = [
    _hn("negation_land", "F118", "don't land yet", {"intent": "hover"}),
    _hn("negation_land", "F118", "do not land", {"intent": "hover"}),
    _hn("negation_land", "F118", "negative, do not land", {"intent": "hover"}),
    _hn("negation_land", "F118", "cancel the landing", {"intent": "hover"}),
    _hn("negation_land", "F118", "hold off on landing", {"intent": "hover"}),
    _hn("negation_land", "F118", "belay that landing", {"intent": "hover"}),
    _hn("negation_land", "F118", "no, don't come down", {"intent": "hover"}),
    _hn("negation_takeoff", "F118", "don't take off yet", {"intent": "hover"}),
    _hn("negation_takeoff", "F118", "hold off on the takeoff", {"intent": "hover"}),
    _hn("negation_takeoff", "F118", "do not launch", {"intent": "hover"}),
    _hn("negation_move", "F118", "don't move", {"intent": "hover"}),
    _hn("negation_move", "F118", "don't go north", {"intent": "hover"}),
    _hn("negation_move", "F118", "stop moving", {"intent": "hover"}),
    _hn("negation_move", "F118", "stop climbing", {"intent": "hover"}),
    _hn("negation_move", "F118", "quit descending", {"intent": "hover"}),
    _hn("negation_formation", "F118", "stop forming the circle", {"intent": "hover"}),
    _hn("negation_formation", "F118", "don't change the formation", {"intent": "hover"}),
    _hn("negation_formation", "F118", "forget the grid, just stay", {"intent": "hover"}),
    _hn("negation_rotate", "F118", "don't rotate", {"intent": "hover"}),
    _hn("negation_rotate", "F118", "stop turning", {"intent": "hover"}),
]

# --- the remaining F117 slots ---------------------------------------------
#
# F117 holds exactly 20 rows (one family's worth). The groups above fill most of
# them; these complete the family with near-misses that have no natural partner
# elsewhere.

_F117_TAIL: list[HardNegative] = [
    _hn("misc_nearmiss", "F117", "form a queue at the canteen", {"intent": "unknown"}),
]

GROUPS: tuple[list[HardNegative], ...] = (
    _CIRCLE,
    _DROP,
    _LINE,
    _HOLD,
    _TAKE,
    _UP,
    _SPEED,
    _SPACING,
    _TRANSIT_ALT,
    _GRID,
    _COLUMN,
    _WEDGE,
    _HOVER_HOMOPHONE,
    _NORTH,
    _ROTATE,
    _LAND,
    _MOVE_OVER,
    _NEGATION,
    _F117_TAIL,
)

HARD_NEGATIVES: tuple[HardNegative, ...] = tuple(row for group in GROUPS for row in group)

# Guard the two properties that make these rows worth their weight: no abort
# utterance is ever labelled anything but abort (see the module docstring), and
# no two rows share a surface form.
_ABORT_WORDS = ("abort", "kill it", "all stop", "cut the motors", "emergency stop")
for _row in HARD_NEGATIVES:
    if any(word in _row.text for word in _ABORT_WORDS) and _row.gold["intent"] != "abort":
        raise AssertionError(
            f"hard negative {_row.text!r} contains an abort word but is labelled "
            f"{_row.gold['intent']!r}; see docs/adr/0002"
        )

_texts = [row.text for row in HARD_NEGATIVES]
if len(_texts) != len(set(_texts)):
    _dupes = sorted({t for t in _texts if _texts.count(t) > 1})
    raise AssertionError(f"duplicate hard-negative surface forms: {_dupes}")
