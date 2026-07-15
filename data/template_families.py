"""Template-family split assignment (PRD Sec. 9, FR-1, Session 01B Task 8).

Defines ~120 template families assigned to exactly one split BEFORE any generation:
- train: 96 families (80%)
- val: 12 families (10%)
- test_synth: 12 families (10%)

This split assignment prevents template leakage across splits, verified by Gate 2
(data/check_leakage.py).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

if __package__ in (None, ""):  # `python data/template_families.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schema.schema import KEY_ORDER

FAMILIES_JSON_PATH = Path(__file__).parent / "template_families.json"

SplitType = Literal["train", "val", "test_synth"]


@dataclass(frozen=True)
class TemplateFamily:
    family_id: str
    intent: str
    slot_pattern: str
    description: str
    split: SplitType


# Pre-assign 120 template families across all 10 intents
# Exactly 96 train, 12 val, 12 test_synth
FAMILIES: list[TemplateFamily] = []

# --- Formation (24 families: 20 train, 2 val, 2 test) ---
#
# Four families (F002, F007, F012, F016) carried a `speed` slot as assigned in
# 01B --- "circle with radius and transit speed". Schema v1.0 has no `speed` on
# `formation`: `Formation` declares shape/radius/spacing/ids and `c-form` in
# cmd.gbnf is `"shape":" shape o-radius o-spacing o-ids`, with no `o-speed`
# (Issue 30). Every row those four families produced would have been rejected by
# layer 1 and by `extra="forbid"` in layer 2.
#
# The unrepresentable `speed` slot is dropped, keeping the required size slot
# (`radius` for circle, `spacing` for line/grid/column) as mandated by Layer 2
# required-slot matrix (§2.4: circle requires radius; line, grid, column require
# spacing). Transit-speed phrasing lives on in `set_param` (F107, F110-F113),
# where the schema has a field for it.
formation_configs = [
    # Circle (radius)
    ("F001", "formation", "shape:circle,radius", "Circle with explicit metric radius", "train"),
    ("F002", "formation", "shape:circle,radius", "Circle with radius phrasing", "train"),
    ("F003", "formation", "shape:circle,radius,ids", "Circle formation for subset of drones", "train"),
    ("F004", "formation", "shape:circle,radius", "Circle with conversational radius phrasing", "val"),
    ("F005", "formation", "shape:circle,radius,ids", "Circle subset formation radio register", "test_synth"),
    # Line (spacing)
    ("F006", "formation", "shape:line,spacing", "Linear formation with inter-drone spacing", "train"),
    ("F007", "formation", "shape:line,spacing", "Line with spacing phrasing", "train"),
    ("F008", "formation", "shape:line,spacing,ids", "Line formation for subset of drones", "train"),
    ("F009", "formation", "shape:line,spacing", "Line spacing imperative command", "val"),
    ("F010", "formation", "shape:line,spacing,ids", "Linear subset radio shorthand", "test_synth"),
    # Grid (spacing)
    ("F011", "formation", "shape:grid,spacing", "2D horizontal grid with spacing", "train"),
    ("F012", "formation", "shape:grid,spacing", "Grid with spacing phrasing", "train"),
    ("F013", "formation", "shape:grid,spacing,ids", "Grid formation for drone subset", "train"),
    ("F014", "formation", "shape:grid,spacing", "Grid formation conversational phrasing", "train"),
    # Column (spacing)
    ("F015", "formation", "shape:column,spacing", "Vertical column stack with spacing", "train"),
    ("F016", "formation", "shape:column,spacing", "Column stack with spacing phrasing", "train"),
    ("F017", "formation", "shape:column,spacing,ids", "Column stack for drone subset", "train"),
    ("F018", "formation", "shape:column,spacing", "Column formation terse radio command", "train"),
    # Wedge
    ("F019", "formation", "shape:wedge", "V-formation wedge without explicit spacing", "train"),
    ("F020", "formation", "shape:wedge,spacing", "V-formation wedge with spacing", "train"),
    ("F021", "formation", "shape:wedge,ids", "Wedge formation for drone subset", "train"),
    ("F022", "formation", "shape:wedge,spacing", "Wedge formation conversational register", "train"),
    # Flock
    ("F023", "formation", "shape:flock", "Flock cohesive dynamic formation", "train"),
    ("F024", "formation", "shape:flock,ids", "Flock cohesive formation for subset", "train"),
]

for fid, intent, sp, desc, sp_type in formation_configs:
    FAMILIES.append(TemplateFamily(fid, intent, sp, desc, sp_type))  # type: ignore[arg-type]

# --- Move (30 families: 26 train, 2 val, 2 test) ---
move_configs = [
    # Pos (coordinate vector)
    ("F025", "move", "pos", "Absolute 3D waypoint coordinate move", "train"),
    ("F026", "move", "pos,speed", "Waypoint move with velocity limit", "train"),
    ("F027", "move", "pos,ids", "Waypoint move for specific drone subset", "train"),
    ("F028", "move", "pos,speed,ids", "Waypoint move with speed and subset addressing", "train"),
    ("F029", "move", "pos", "Terse coordinate dispatch (x,y,z)", "val"),
    ("F030", "move", "pos,speed", "Conversational coordinate navigation", "test_synth"),
    # Direction: North / South
    ("F031", "move", "dir:north,dist", "Cardinal displacement north with distance", "train"),
    ("F032", "move", "dir:north,dist,speed", "Displacement north with speed", "train"),
    ("F033", "move", "dir:north,dist,ids", "Subset displacement north", "train"),
    ("F034", "move", "dir:south,dist", "Cardinal displacement south with distance", "train"),
    ("F035", "move", "dir:south,dist,speed", "Displacement south with speed", "train"),
    ("F036", "move", "dir:south,dist,ids", "Subset displacement south", "train"),
    # Direction: East / West
    ("F037", "move", "dir:east,dist", "Cardinal displacement east with distance", "train"),
    ("F038", "move", "dir:east,dist,speed", "Displacement east with speed", "train"),
    ("F039", "move", "dir:east,dist,ids", "Subset displacement east", "train"),
    ("F040", "move", "dir:west,dist", "Cardinal displacement west with distance", "train"),
    ("F041", "move", "dir:west,dist,speed", "Displacement west with speed", "train"),
    ("F042", "move", "dir:west,dist,ids", "Subset displacement west", "train"),
    # F043 is the test_synth half of the split swap documented below, at F050.
    ("F043", "move", "dir:east,dist", "Eastward displacement imperative", "test_synth"),  # 01B: train
    ("F044", "move", "dir:west,dist,ids", "Westward subset displacement radio register", "train"),
    # Direction: Up / Down
    ("F045", "move", "dir:up,dist", "Relative upward climb by distance", "train"),
    ("F046", "move", "dir:up,dist,speed", "Upward climb with speed limit", "train"),
    ("F047", "move", "dir:down,dist", "Relative downward descent by distance", "train"),
    ("F048", "move", "dir:down,dist,speed", "Downward descent with speed limit", "train"),
    ("F049", "move", "dir:up,dist,ids", "Subset relative climb", "train"),
    # Direction: Body-relative (forward, back, left, right)
    #
    # Split swap applied in Session 02A, before any row was generated (Issue 28).
    # As assigned in 01B, `dir:left` (F053, val) and `dir:right` (F054,
    # test_synth) were each covered by exactly one family, and both of those
    # families sat outside `train` --- so two of the ten `dir` enum values would
    # never have appeared in a training example, while val drove checkpoint
    # selection on one of them and test_synth/test_golden scored the other. That
    # is ~8% of the held-out rows made unlearnable by a bookkeeping artefact, on
    # a benchmark whose bar is EM >= 0.85 (NFR-4).
    #
    # F053 and F054 move to `train`; F050 (`dir:forward`) goes to val and F043
    # (`dir:east`) to test_synth. Both donors leave their direction covered in
    # train --- forward by F051, east by F037/F038/F039 --- and the held-out
    # families keep the same slot pattern (`dir,dist`), so the 96/12/12 counts
    # and the pattern coverage of each split are unchanged.
    ("F050", "move", "dir:forward,dist", "Body-relative forward translation", "val"),
    ("F051", "move", "dir:forward,dist,speed", "Forward translation with speed", "train"),
    ("F052", "move", "dir:back,dist", "Body-relative backward translation", "train"),
    ("F053", "move", "dir:left,dist", "Body-relative lateral left translation", "train"),
    ("F054", "move", "dir:right,dist", "Body-relative lateral right translation", "train"),
]

for fid, intent, sp, desc, sp_type in move_configs:
    FAMILIES.append(TemplateFamily(fid, intent, sp, desc, sp_type))  # type: ignore[arg-type]

# --- Altitude (12 families: 10 train, 1 val, 1 test) ---
alt_configs = [
    ("F055", "altitude", "z", "Command absolute altitude target in meters", "train"),
    ("F056", "altitude", "z,ids", "Target altitude for single drone", "train"),
    ("F057", "altitude", "z,ids", "Target altitude for drone subset pair", "train"),
    ("F058", "altitude", "z", "Conversational altitude adjustment phrasing", "train"),
    ("F059", "altitude", "z", "Terse flight level command (FL/z)", "train"),
    ("F060", "altitude", "z,ids", "Lead drone altitude change", "train"),
    ("F061", "altitude", "z", "Minimum operational altitude command", "train"),
    ("F062", "altitude", "z", "Ceiling altitude command", "train"),
    ("F063", "altitude", "z,ids", "Follower drones altitude adjustment", "train"),
    ("F064", "altitude", "z", "Polite altitude request phrasing", "train"),
    ("F065", "altitude", "z,ids", "Subset altitude adjust conversational", "val"),
    ("F066", "altitude", "z", "Held-out altitude command phrasing", "test_synth"),
]

for fid, intent, sp, desc, sp_type in alt_configs:
    FAMILIES.append(TemplateFamily(fid, intent, sp, desc, sp_type))  # type: ignore[arg-type]

# --- Takeoff (10 families: 8 train, 1 val, 1 test) ---
takeoff_configs = [
    ("F067", "takeoff", "none", "Immediate default swarm takeoff", "train"),
    ("F068", "takeoff", "z", "Takeoff to specified initial hover altitude", "train"),
    ("F069", "takeoff", "ids", "Single drone launch command", "train"),
    ("F070", "takeoff", "z,ids", "Subset launch to target altitude", "train"),
    ("F071", "takeoff", "none", "Terse radio launch command (airborne)", "train"),
    ("F072", "takeoff", "z", "Launch and climb to survey altitude", "train"),
    ("F073", "takeoff", "ids", "Pair launch sequential addressing", "train"),
    ("F074", "takeoff", "none", "Conversational takeoff command", "train"),
    ("F075", "takeoff", "z", "Takeoff with explicit altitude meter unit", "val"),
    ("F076", "takeoff", "z,ids", "Held-out launch sequence phrasing", "test_synth"),
]

for fid, intent, sp, desc, sp_type in takeoff_configs:
    FAMILIES.append(TemplateFamily(fid, intent, sp, desc, sp_type))  # type: ignore[arg-type]

# --- Land (8 families: 6 train, 1 val, 1 test) ---
land_configs = [
    ("F077", "land", "none", "Immediate all-drone landing command", "train"),
    ("F078", "land", "ids", "Single drone targeted landing", "train"),
    ("F079", "land", "ids", "Subset pair landing command", "train"),
    ("F080", "land", "none", "Terse radio recovery command", "train"),
    ("F081", "land", "none", "Conversational landing request", "train"),
    ("F082", "land", "ids", "Return to pad subset command", "train"),
    ("F083", "land", "none", "Imperative touch down command", "val"),
    ("F084", "land", "ids", "Held-out landing phrasing", "test_synth"),
]

for fid, intent, sp, desc, sp_type in land_configs:
    FAMILIES.append(TemplateFamily(fid, intent, sp, desc, sp_type))  # type: ignore[arg-type]

# --- Hover (8 families: 6 train, 1 val, 1 test) ---
hover_configs = [
    ("F085", "hover", "none", "Immediate all-drone hover in place", "train"),
    ("F086", "hover", "ids", "Single drone position hold", "train"),
    ("F087", "hover", "ids", "Subset drone position freeze", "train"),
    ("F088", "hover", "none", "Halt translation and hold altitude", "train"),
    ("F089", "hover", "none", "Conversational hold command", "train"),
    ("F090", "hover", "ids", "Freeze lead drone position", "train"),
    ("F091", "hover", "none", "Station-keeping radio command", "val"),
    ("F092", "hover", "ids", "Held-out hover phrasing", "test_synth"),
]

for fid, intent, sp, desc, sp_type in hover_configs:
    FAMILIES.append(TemplateFamily(fid, intent, sp, desc, sp_type))  # type: ignore[arg-type]

# --- Abort (6 families: 4 train, 1 val, 1 test) ---
abort_configs = [
    ("F093", "abort", "none", "Emergency all-stop swarm abort", "train"),
    ("F094", "abort", "none", "Kill rotor thrust immediate shutdown", "train"),
    ("F095", "abort", "none", "Emergency flight termination protocol", "train"),
    ("F096", "abort", "none", "Critical safety cut motors", "train"),
    ("F097", "abort", "none", "Urgent abort safety reflex", "val"),
    ("F098", "abort", "none", "Held-out emergency abort phrasing", "test_synth"),
]

for fid, intent, sp, desc, sp_type in abort_configs:
    FAMILIES.append(TemplateFamily(fid, intent, sp, desc, sp_type))  # type: ignore[arg-type]

# --- Rotate (8 families: 6 train, 1 val, 1 test) ---
rotate_configs = [
    ("F099", "rotate", "yaw", "Heading yaw rotation by degrees", "train"),
    ("F100", "rotate", "yaw,ids", "Single drone yaw alignment", "train"),
    ("F101", "rotate", "yaw,ids", "Subset drone heading adjustment", "train"),
    ("F102", "rotate", "yaw", "Relative clockwise/counter-clockwise rotation", "train"),
    ("F103", "rotate", "yaw", "Cardinal facing turn (face north/south)", "train"),
    ("F104", "rotate", "yaw,ids", "Lead drone turn to angle", "train"),
    ("F105", "rotate", "yaw", "Pivot in place by angle", "val"),
    ("F106", "rotate", "yaw,ids", "Held-out rotation phrasing", "test_synth"),
]

for fid, intent, sp, desc, sp_type in rotate_configs:
    FAMILIES.append(TemplateFamily(fid, intent, sp, desc, sp_type))  # type: ignore[arg-type]

# --- SetParam (8 families: 6 train, 1 val, 1 test) ---
param_configs = [
    ("F107", "set_param", "speed", "Set cruise velocity parameter", "train"),
    ("F108", "set_param", "spacing", "Set default inter-drone spacing", "train"),
    ("F109", "set_param", "alt", "Set default transit altitude parameter", "train"),
    ("F110", "set_param", "speed,spacing", "Set speed and spacing concurrently", "train"),
    ("F111", "set_param", "speed,alt", "Set speed and transit altitude", "train"),
    ("F112", "set_param", "speed,spacing,alt", "Set full parameter trio", "train"),
    ("F113", "set_param", "speed", "Adjust maximum flight speed", "val"),
    ("F114", "set_param", "spacing,alt", "Held-out parameter configuration phrasing", "test_synth"),
]

for fid, intent, sp, desc, sp_type in param_configs:
    FAMILIES.append(TemplateFamily(fid, intent, sp, desc, sp_type))  # type: ignore[arg-type]

# --- Unknown & Hard Negatives (6 families: 4 train, 1 val, 1 test) ---
unknown_configs = [
    ("F115", "unknown", "none", "General conversational queries and weather chatter", "train"),
    ("F116", "unknown", "none", "Out-of-scope drone requests (take a photo, video)", "train"),
    ("F117", "unknown", "none", "Hard negative lexical near-misses (circle around tree)", "train"),
    ("F118", "unknown", "none", "Negation hard negatives: don't land yet -> resolves to hover", "train"),
    ("F119", "unknown", "none", "Truncated and fragmented speech utterances", "val"),
    ("F120", "unknown", "none", "Held-out OOD assistant queries from MASSIVE", "test_synth"),
]

for fid, intent, sp, desc, sp_type in unknown_configs:
    FAMILIES.append(TemplateFamily(fid, intent, sp, desc, sp_type))  # type: ignore[arg-type]

assert len(FAMILIES) == 120, f"Expected 120 families, got {len(FAMILIES)}"

# Verify exact split counts: 96 train, 12 val, 12 test_synth
TRAIN_FAMILIES = [f for f in FAMILIES if f.split == "train"]
VAL_FAMILIES = [f for f in FAMILIES if f.split == "val"]
TEST_FAMILIES = [f for f in FAMILIES if f.split == "test_synth"]

assert len(TRAIN_FAMILIES) == 96, f"Expected 96 train families, got {len(TRAIN_FAMILIES)}"
assert len(VAL_FAMILIES) == 12, f"Expected 12 val families, got {len(VAL_FAMILIES)}"
assert len(TEST_FAMILIES) == 12, f"Expected 12 test families, got {len(TEST_FAMILIES)}"

# Every enum value the schema admits must be reachable from `train`, or the model
# is asked at eval time for a token it was never shown. This is the regression
# guard for the F050/F053 and F043/F054 swap documented above (Issue 28); the
# assignment table is hand-maintained, so nothing else would catch a repeat.
_TRAIN_DIRS = {
    f.slot_pattern.split("dir:", 1)[1].split(",", 1)[0]
    for f in TRAIN_FAMILIES
    if "dir:" in f.slot_pattern
}
_ALL_DIRS = {
    f.slot_pattern.split("dir:", 1)[1].split(",", 1)[0]
    for f in FAMILIES
    if "dir:" in f.slot_pattern
}
assert _TRAIN_DIRS == _ALL_DIRS, f"directions held out of train: {sorted(_ALL_DIRS - _TRAIN_DIRS)}"

_TRAIN_SHAPES = {
    f.slot_pattern.split("shape:", 1)[1].split(",", 1)[0]
    for f in TRAIN_FAMILIES
    if "shape:" in f.slot_pattern
}
_ALL_SHAPES = {
    f.slot_pattern.split("shape:", 1)[1].split(",", 1)[0]
    for f in FAMILIES
    if "shape:" in f.slot_pattern
}
assert _TRAIN_SHAPES == _ALL_SHAPES, f"shapes held out of train: {sorted(_ALL_SHAPES - _TRAIN_SHAPES)}"

# The converse does *not* hold and cannot, at 12 held-out families over 10
# intents: only `circle` and `line` have a family in val/test_synth, so
# `grid`/`column`/`wedge`/`flock` are trained but never scored (Issue 29). The
# two that are held out are chosen to cover both formation slot types --- circle
# exercises `radius`, line exercises `spacing` --- so no *slot* goes unscored,
# only four `shape` enum values. Carried into the dataset card (Session 03).
_HELDOUT_SHAPES = {
    f.slot_pattern.split("shape:", 1)[1].split(",", 1)[0]
    for f in FAMILIES
    if "shape:" in f.slot_pattern and f.split != "train"
}
assert _HELDOUT_SHAPES == {"circle", "line"}, f"held-out shape coverage changed: {_HELDOUT_SHAPES}"

FAMILY_MAP: dict[str, TemplateFamily] = {f.family_id: f for f in FAMILIES}


# Every slot a family declares must be a field the frozen schema actually has for
# that intent. `KEY_ORDER` is derived from the Pydantic models themselves, so this
# compares the table against the contract rather than against a second copy of it
# (README:56, Trap 5) --- adding a model field is enough to widen it, and nothing
# here has to be kept in sync by hand.
#
# This is the regression guard for Issue 30: four `formation` families declared a
# `speed` slot the intent has no field for, which would have failed FR-1 on 80
# rows at generation time rather than here, at import.
def _pattern_keys(slot_pattern: str) -> set[str]:
    """The label keys a `slot_pattern` implies, in the 01B table's notation."""
    keys: set[str] = set()
    for token in slot_pattern.split(","):
        token = token.strip()
        if not token or token == "none":
            continue
        keys.add(token.split(":", 1)[0])  # `shape:circle` -> shape, `dir:east` -> dir
    return keys


_SLOT_ERRORS = [
    f"{f.family_id} ({f.intent}) declares {sorted(_pattern_keys(f.slot_pattern) - set(KEY_ORDER[f.intent]))}"
    for f in FAMILIES
    if not _pattern_keys(f.slot_pattern) <= set(KEY_ORDER[f.intent])
]
assert not _SLOT_ERRORS, "slot patterns outside schema v1.0: " + "; ".join(_SLOT_ERRORS)

# The converse, as a coverage report rather than an assertion: which representable
# slots no family exercises. `pos` and `dir`/`dist` are alternatives in `c-move`,
# so a move family covers one or the other and never both.
UNCOVERED_SLOTS: dict[str, tuple[str, ...]] = {
    intent: tuple(
        sorted(
            set(keys)
            - {"intent"}
            - {k for f in FAMILIES if f.intent == intent for k in _pattern_keys(f.slot_pattern)}
        )
    )
    for intent, keys in KEY_ORDER.items()
}


def export_json(path: Path = FAMILIES_JSON_PATH) -> None:
    """Export the template families definition to a static JSON file."""
    data = [asdict(f) for f in FAMILIES]
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2)


if __name__ == "__main__":
    export_json()
    print(f"Exported 120 template families to {FAMILIES_JSON_PATH}")
    print(f"  train: {len(TRAIN_FAMILIES)} (80%)")
    print(f"  val: {len(VAL_FAMILIES)} (10%)")
    print(f"  test_synth: {len(TEST_FAMILIES)} (10%)")
    print("  slot patterns: all inside schema v1.0")
    for _intent, _slots in UNCOVERED_SLOTS.items():
        if _slots:
            print(f"  uncovered slots for {_intent}: {', '.join(_slots)}")
