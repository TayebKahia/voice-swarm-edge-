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
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

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
formation_configs = [
    # Circle (radius)
    ("F001", "formation", "shape:circle,radius", "Circle with explicit metric radius", "train"),
    ("F002", "formation", "shape:circle,radius,speed", "Circle with radius and transit speed", "train"),
    ("F003", "formation", "shape:circle,radius,ids", "Circle formation for subset of drones", "train"),
    ("F004", "formation", "shape:circle,radius", "Circle with conversational radius phrasing", "val"),
    ("F005", "formation", "shape:circle,radius,ids", "Circle subset formation radio register", "test_synth"),
    # Line (spacing)
    ("F006", "formation", "shape:line,spacing", "Linear formation with inter-drone spacing", "train"),
    ("F007", "formation", "shape:line,spacing,speed", "Line with spacing and transit speed", "train"),
    ("F008", "formation", "shape:line,spacing,ids", "Line formation for subset of drones", "train"),
    ("F009", "formation", "shape:line,spacing", "Line spacing imperative command", "val"),
    ("F010", "formation", "shape:line,spacing,ids", "Linear subset radio shorthand", "test_synth"),
    # Grid (spacing)
    ("F011", "formation", "shape:grid,spacing", "2D horizontal grid with spacing", "train"),
    ("F012", "formation", "shape:grid,spacing,speed", "Grid with spacing and transit speed", "train"),
    ("F013", "formation", "shape:grid,spacing,ids", "Grid formation for drone subset", "train"),
    ("F014", "formation", "shape:grid,spacing", "Grid formation conversational phrasing", "train"),
    # Column (spacing)
    ("F015", "formation", "shape:column,spacing", "Vertical column stack with spacing", "train"),
    ("F016", "formation", "shape:column,spacing,speed", "Column stack with transit speed", "train"),
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
    ("F043", "move", "dir:east,dist", "Eastward displacement imperative", "train"),
    ("F044", "move", "dir:west,dist,ids", "Westward subset displacement radio register", "train"),
    # Direction: Up / Down
    ("F045", "move", "dir:up,dist", "Relative upward climb by distance", "train"),
    ("F046", "move", "dir:up,dist,speed", "Upward climb with speed limit", "train"),
    ("F047", "move", "dir:down,dist", "Relative downward descent by distance", "train"),
    ("F048", "move", "dir:down,dist,speed", "Downward descent with speed limit", "train"),
    ("F049", "move", "dir:up,dist,ids", "Subset relative climb", "train"),
    # Direction: Body-relative (forward, back, left, right)
    ("F050", "move", "dir:forward,dist", "Body-relative forward translation", "train"),
    ("F051", "move", "dir:forward,dist,speed", "Forward translation with speed", "train"),
    ("F052", "move", "dir:back,dist", "Body-relative backward translation", "train"),
    ("F053", "move", "dir:left,dist", "Body-relative lateral left translation", "val"),
    ("F054", "move", "dir:right,dist", "Body-relative lateral right translation", "test_synth"),
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

FAMILY_MAP: dict[str, TemplateFamily] = {f.family_id: f for f in FAMILIES}


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
