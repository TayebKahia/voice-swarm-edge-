"""Adversarial and structural grammar test suite (Session 01B Task 5).

Delivers the comprehensive adversarial corpus testing both:
- Layer 1 (cmd.gbnf structural constraints in the constrained decoder)
- Layer 2 (validate.py semantic matrix, physical envelope clamping, identifier filtering, fallback)

Mandatory adversarial cases covered:
1. 1e999 exponential notation
2. 20-digit integer overflow
3. bare 2. trailing decimal
4. two decimals (2.55)
5. duplicate ids
6. out-of-range ids
7. radius on a line
8. move with both pos and dir
9. move with neither pos nor dir
10. set_param with no slots
11. emitted-null variants (z: null, ids: null, speed: null)
12. trailing commas
13. unicode in a shape name
14. every clamp boundary from both sides for all physical slots
"""

import math
import re
import pytest

from schema.schema import (
    Command,
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
    ENVELOPE,
    POS_MAX_NORM,
    SWARM_SIZE,
    GRAMMAR_PATH,
)
from schema.validate import validate, ValidationError

# ---------------------------------------------------------------------------
# GBNF Structural Grammar Model (Layer 1)
# Mirrors the exact productions of schema/cmd.gbnf
# ---------------------------------------------------------------------------

NUM_PATTERN = r"-?[0-9]{1,3}(?:\.[0-9])?"
IDLIST_PATTERN = r"[0-9](?:,[0-9])*"
SHAPE_PATTERN = r'"(?:circle|line|wedge|grid|column|flock)"'
DIR_PATTERN = r'"(?:north|south|east|west|up|down|forward|back|left|right)"'

O_RADIUS = rf'(?:,"radius":{NUM_PATTERN})?'
O_SPACING = rf'(?:,"spacing":{NUM_PATTERN})?'
O_SPEED = rf'(?:,"speed":{NUM_PATTERN})?'
O_ALT = rf'(?:,"alt":{NUM_PATTERN})?'
O_Z = rf'(?:,"z":{NUM_PATTERN})?'
O_IDS = rf'(?:,"ids":\[{IDLIST_PATTERN}\])?'

KV_POS = rf'"pos":\[{NUM_PATTERN},{NUM_PATTERN},{NUM_PATTERN}\]'
KV_DIR = rf'"dir":{DIR_PATTERN},"dist":{NUM_PATTERN}'

C_FORM = rf'{{\"intent\":\"formation\",\"shape\":{SHAPE_PATTERN}{O_RADIUS}{O_SPACING}{O_IDS}\}}'
C_MOVE = rf'{{\"intent\":\"move\",(?:{KV_POS}|{KV_DIR}){O_SPEED}{O_IDS}\}}'
C_ALT = rf'{{\"intent\":\"altitude\",\"z\":{NUM_PATTERN}{O_IDS}\}}'
C_TAKEOFF = rf'{{\"intent\":\"takeoff\"{O_Z}{O_IDS}\}}'
C_LAND = rf'{{\"intent\":\"land\"{O_IDS}\}}'
C_HOVER = rf'{{\"intent\":\"hover\"{O_IDS}\}}'
C_ABORT = r'\{"intent":"abort"\}'
C_ROT = rf'{{\"intent\":\"rotate\",\"yaw\":{NUM_PATTERN}{O_IDS}\}}'
C_PARAM = rf'{{\"intent\":\"set_param\"{O_SPEED}{O_SPACING}{O_ALT}\}}'
C_UNK = r'\{"intent":"unknown"\}'

GBNF_REGEX = re.compile(
    rf'^(?:{C_FORM}|{C_MOVE}|{C_ALT}|{C_TAKEOFF}|{C_LAND}|{C_HOVER}|{C_ABORT}|{C_ROT}|{C_PARAM}|{C_UNK})$'
)


def matches_gbnf(s: str) -> bool:
    """Return True if string conforms strictly to cmd.gbnf syntax."""
    return bool(GBNF_REGEX.match(s))


# ===========================================================================
# 1. Grammar File & Structural Validity Tests (Layer 1)
# ===========================================================================


def test_grammar_file_exists():
    """Verify cmd.gbnf exists on disk and is non-empty."""
    assert GRAMMAR_PATH.exists(), f"cmd.gbnf missing at {GRAMMAR_PATH}"
    content = GRAMMAR_PATH.read_text(encoding="utf-8")
    assert "root      ::= cmd" in content
    assert "num       ::=" in content


@pytest.mark.parametrize(
    "valid_cmd",
    [
        '{"intent":"formation","shape":"circle","radius":5.0}',
        '{"intent":"formation","shape":"line","spacing":2.0}',
        '{"intent":"formation","shape":"wedge","spacing":3.0,"ids":[0,1,2]}',
        '{"intent":"formation","shape":"grid","spacing":2.5}',
        '{"intent":"formation","shape":"column"}',
        '{"intent":"formation","shape":"flock"}',
        '{"intent":"move","pos":[10.0,0.0,3.0],"speed":1.5}',
        '{"intent":"move","pos":[-50.0,-25.5,0.0]}',
        '{"intent":"move","dir":"north","dist":10.0}',
        '{"intent":"move","dir":"forward","dist":5.5,"speed":1.0,"ids":[1]}',
        '{"intent":"altitude","z":4.0,"ids":[1,2]}',
        '{"intent":"altitude","z":15.0}',
        '{"intent":"takeoff","z":2.5,"ids":[0,1,2,3,4]}',
        '{"intent":"takeoff"}',
        '{"intent":"land","ids":[0,1]}',
        '{"intent":"land"}',
        '{"intent":"hover"}',
        '{"intent":"hover","ids":[2]}',
        '{"intent":"abort"}',
        '{"intent":"rotate","yaw":90.0}',
        '{"intent":"rotate","yaw":-180.0,"ids":[0]}',
        '{"intent":"set_param","speed":1.5}',
        '{"intent":"set_param","speed":1.5,"spacing":2.0,"alt":5.0}',
        '{"intent":"unknown"}',
    ],
)
def test_gbnf_accepts_valid_commands(valid_cmd: str):
    """Ensure structurally valid commands are accepted by cmd.gbnf."""
    assert matches_gbnf(valid_cmd), f"Valid command rejected by GBNF: {valid_cmd}"


# ===========================================================================
# 2. Structural Adversarial Corpus (Layer 1 Rejections)
# ===========================================================================


@pytest.mark.parametrize(
    "adversarial_str, reason",
    [
        ('{"intent":"formation","shape":"circle","radius":1e999}', "exponential notation 1e999"),
        ('{"intent":"move","pos":[10000000000000000000,0.0,3.0]}', "20-digit integer overflow"),
        ('{"intent":"altitude","z":2.}', "bare trailing decimal 2."),
        ('{"intent":"altitude","z":2.55}', "two decimals 2.55"),
        ('{"intent":"move","pos":[10.0,0.0,3.0],"dir":"north","dist":5.0}', "both pos and dir"),
        ('{"intent":"move","speed":1.5}', "neither pos nor dir in move"),
        ('{"intent":"takeoff","z":null}', "emitted-null variant z:null"),
        ('{"intent":"land","ids":null}', "emitted-null variant ids:null"),
        ('{"intent":"set_param","speed":null}', "emitted-null variant speed:null"),
        ('{"intent":"abort",}', "trailing comma in abort"),
        ('{"intent":"move","dir":"north","dist":10.0,}', "trailing comma in move"),
        ('{"intent":"formation","shape":"cîrcle"}', "unicode in shape name"),
        ('{"intent":"formation","shape":"circle\u0000"}', "null byte in shape name"),
        ('{"intent":"formation","shape":"triangle"}', "unsupported shape"),
        ('{"intent":"move","dir":"diagonal","dist":5.0}', "unsupported direction"),
        ('{"intent": "abort"}', "whitespace outside string literal"),
        ('{"intent":"altitude","z":.5}', "leading decimal without zero"),
        ('{"intent":"rotate","yaw":--90.0}', "double minus"),
        ('{"intent":"formation"}', "missing required shape in formation"),
        ('{"intent":"abort","ids":[0]}', "abort with illegal ids slot"),
    ],
)
def test_gbnf_rejects_structural_adversarial_corpus(adversarial_str: str, reason: str):
    """Verify cmd.gbnf structurally rejects all invalid syntax, nulls, overflows, and formatting."""
    assert not matches_gbnf(adversarial_str), f"GBNF erroneously accepted {reason}: {adversarial_str}"


# ===========================================================================
# 3. Layer 2 Semantic Adversarial Corpus (validate.py)
# ===========================================================================


def test_radius_on_line_rejected():
    """Adversarial case 7: radius on a line formation without spacing fails required-slot matrix."""
    raw = '{"intent":"formation","shape":"line","radius":5.0}'
    # With fallback=False, must raise ValidationError because spacing is required
    with pytest.raises(ValidationError, match="requires spacing"):
        validate(raw, fallback=False)
    # With fallback=True (runtime default), must safely resolve to HOVER
    cmd = validate(raw, fallback=True)
    assert isinstance(cmd, Hover)


def test_superfluous_slots_dropped_with_log():
    """Superfluous slots (radius on line with spacing, or spacing on circle with radius) are dropped."""
    # Radius on line with valid spacing is dropped, preserving command execution
    raw_line = '{"intent":"formation","shape":"line","spacing":2.0,"radius":5.0}'
    cmd_line = validate(raw_line)
    assert isinstance(cmd_line, Formation)
    assert cmd_line.shape == "line"
    assert cmd_line.spacing == 2.0
    assert cmd_line.radius is None

    # Spacing on circle with valid radius is dropped
    raw_circle = '{"intent":"formation","shape":"circle","radius":5.0,"spacing":2.0}'
    cmd_circle = validate(raw_circle)
    assert isinstance(cmd_circle, Formation)
    assert cmd_circle.shape == "circle"
    assert cmd_circle.radius == 5.0
    assert cmd_circle.spacing is None

    # Radius on wedge is dropped, spacing preserved
    raw_wedge = '{"intent":"formation","shape":"wedge","spacing":2.0,"radius":5.0}'
    cmd_wedge = validate(raw_wedge)
    assert isinstance(cmd_wedge, Formation)
    assert cmd_wedge.shape == "wedge"
    assert cmd_wedge.spacing == 2.0
    assert cmd_wedge.radius is None

    # Radius and spacing on flock are dropped
    raw_flock = '{"intent":"formation","shape":"flock","spacing":2.0,"radius":5.0}'
    cmd_flock = validate(raw_flock)
    assert isinstance(cmd_flock, Formation)
    assert cmd_flock.shape == "flock"
    assert cmd_flock.radius is None
    assert cmd_flock.spacing is None

    # Superfluous slots on abort (e.g. ids, speed) dropped with slot_dropped log, NEVER degrading to Hover
    raw_abort_with_ids = '{"intent":"abort","ids":[0]}'
    cmd_abort = validate(raw_abort_with_ids)
    assert isinstance(cmd_abort, Abort)
    assert cmd_abort.intent == "abort"



def test_nan_and_infinity_rejected():
    """Defect 1: NaN and Infinity are non-finite, safely rejected to HOVER."""
    # Bare NaN in scalar slot
    raw_nan_z = '{"intent":"altitude","z":NaN}'
    with pytest.raises(ValidationError):
        validate(raw_nan_z, fallback=False)
    assert isinstance(validate(raw_nan_z, fallback=True), Hover)

    # NaN in yaw
    raw_nan_yaw = '{"intent":"rotate","yaw":NaN}'
    with pytest.raises(ValidationError):
        validate(raw_nan_yaw, fallback=False)
    assert isinstance(validate(raw_nan_yaw, fallback=True), Hover)

    # NaN in pos
    raw_nan_pos = '{"intent":"move","pos":[NaN, 0.0, 3.0]}'
    with pytest.raises(ValidationError):
        validate(raw_nan_pos, fallback=False)
    assert isinstance(validate(raw_nan_pos, fallback=True), Hover)

    # Infinity in scalar slot
    raw_inf_z = '{"intent":"altitude","z":Infinity}'
    with pytest.raises(ValidationError):
        validate(raw_inf_z, fallback=False)
    assert isinstance(validate(raw_inf_z, fallback=True), Hover)


def test_layer2_grammar_off_ablation_overflows():
    """Layer 2 handles unconstrained floats: 1e999 (inf) and 20-digit integers."""
    # 1e999 parses in Python float as inf -> rejected as non-finite to safe HOVER
    raw_overflow = '{"intent":"formation","shape":"circle","radius":1e999}'
    assert isinstance(validate(raw_overflow, fallback=True), Hover)

    # 20-digit integer in pos vector clamped by norm <= 50.0 while preserving altitude floor
    raw_20_digit = '{"intent":"move","pos":[10000000000000000000, 0.0, 3.0]}'
    cmd = validate(raw_20_digit)
    assert isinstance(cmd, Move)
    assert cmd.pos == (49.9, 0.0, 3.0)


def test_set_param_no_slots_rejected():
    """Adversarial case 10: set_param with no slots must fail Layer 2 validation."""
    raw = '{"intent":"set_param"}'
    with pytest.raises(ValidationError, match="requires at least one of"):
        validate(raw, fallback=False)
    cmd = validate(raw, fallback=True)
    assert isinstance(cmd, Hover)


def test_move_with_both_pos_and_dir_rejected():
    """Adversarial case 8: move with both pos and dir fails Layer 2."""
    raw = '{"intent":"move","pos":[10.0,0.0,3.0],"dir":"north","dist":5.0}'
    with pytest.raises(ValidationError, match="cannot specify both"):
        validate(raw, fallback=False)
    cmd = validate(raw, fallback=True)
    assert isinstance(cmd, Hover)


def test_move_with_neither_pos_nor_dir_rejected():
    """Adversarial case 9: move with neither pos nor dir fails Layer 2."""
    raw = '{"intent":"move","speed":1.5}'
    with pytest.raises(ValidationError, match="requires exactly one of"):
        validate(raw, fallback=False)
    cmd = validate(raw, fallback=True)
    assert isinstance(cmd, Hover)


def test_altitude_without_z_rejected():
    """Altitude without z slot fails Layer 2."""
    raw = '{"intent":"altitude","ids":[0]}'
    with pytest.raises(ValidationError, match="requires z slot"):
        validate(raw, fallback=False)
    assert isinstance(validate(raw, fallback=True), Hover)


def test_rotate_without_yaw_rejected():
    """Rotate without yaw slot fails Layer 2."""
    raw = '{"intent":"rotate"}'
    with pytest.raises(ValidationError, match="requires yaw slot"):
        validate(raw, fallback=False)
    assert isinstance(validate(raw, fallback=True), Hover)


def test_parse_failure_and_truncation_fallback():
    """Truncated tokens or malformed JSON safely fall back to HOVER."""
    truncated = '{"intent":"move","pos":[10.0,0.0,'
    cmd = validate(truncated, fallback=True)
    assert isinstance(cmd, Hover)

    with pytest.raises(ValidationError):
        validate(truncated, fallback=False)


# ===========================================================================
# 4. Identifier Handling Tests (Deduplication, Sorting, Filtering)
# ===========================================================================


def test_duplicate_ids_normalised():
    """Adversarial case 5: duplicate ids deduplicated and sorted ascending."""
    raw = '{"intent":"altitude","z":4.0,"ids":[2,0,2,1,0]}'
    cmd = validate(raw)
    assert isinstance(cmd, Altitude)
    assert cmd.ids == [0, 1, 2]


def test_out_of_range_ids_dropped():
    """Adversarial case 6: out-of-range ids dropped with a log line."""
    raw = '{"intent":"land","ids":[0, 1, 9, 100]}'
    cmd = validate(raw)
    assert isinstance(cmd, Land)
    assert cmd.ids == [0, 1]


def test_empty_ids_after_filtering_means_all_drones():
    """All ids filtered out => None (meaning all drones, not an error)."""
    raw = '{"intent":"hover","ids":[5, 6, 7]}'
    cmd = validate(raw)
    assert isinstance(cmd, Hover)
    assert cmd.ids is None


# ===========================================================================
# 5. Physical Envelope Clamping: Every Boundary From Both Sides
# ===========================================================================


class TestClampBoundaries:
    """Tests every clamp boundary from both sides (below, at, above)."""

    # --- Radius [1.0, 10.0] ---
    def test_radius_lower_boundary_both_sides(self):
        # below lower -> clamped to 1.0
        cmd_below = validate('{"intent":"formation","shape":"circle","radius":0.9}')
        assert isinstance(cmd_below, Formation) and cmd_below.radius == 1.0

        # at lower -> 1.0
        cmd_at = validate('{"intent":"formation","shape":"circle","radius":1.0}')
        assert isinstance(cmd_at, Formation) and cmd_at.radius == 1.0

        # above lower -> 1.1
        cmd_above = validate('{"intent":"formation","shape":"circle","radius":1.1}')
        assert isinstance(cmd_above, Formation) and cmd_above.radius == 1.1

    def test_radius_upper_boundary_both_sides(self):
        # below upper -> 9.9
        cmd_below = validate('{"intent":"formation","shape":"circle","radius":9.9}')
        assert isinstance(cmd_below, Formation) and cmd_below.radius == 9.9

        # at upper -> 10.0
        cmd_at = validate('{"intent":"formation","shape":"circle","radius":10.0}')
        assert isinstance(cmd_at, Formation) and cmd_at.radius == 10.0

        # above upper -> clamped to 10.0
        cmd_above = validate('{"intent":"formation","shape":"circle","radius":10.1}')
        assert isinstance(cmd_above, Formation) and cmd_above.radius == 10.0

    # --- Spacing [1.0, 5.0] ---
    def test_spacing_lower_boundary_both_sides(self):
        # below lower -> clamped to 1.0
        cmd_below = validate('{"intent":"formation","shape":"line","spacing":0.9}')
        assert isinstance(cmd_below, Formation) and cmd_below.spacing == 1.0

        # at lower -> 1.0
        cmd_at = validate('{"intent":"formation","shape":"line","spacing":1.0}')
        assert isinstance(cmd_at, Formation) and cmd_at.spacing == 1.0

        # above lower -> 1.1
        cmd_above = validate('{"intent":"formation","shape":"line","spacing":1.1}')
        assert isinstance(cmd_above, Formation) and cmd_above.spacing == 1.1

    def test_spacing_upper_boundary_both_sides(self):
        # below upper -> 4.9
        cmd_below = validate('{"intent":"formation","shape":"line","spacing":4.9}')
        assert isinstance(cmd_below, Formation) and cmd_below.spacing == 4.9

        # at upper -> 5.0
        cmd_at = validate('{"intent":"formation","shape":"line","spacing":5.0}')
        assert isinstance(cmd_at, Formation) and cmd_at.spacing == 5.0

        # above upper -> clamped to 5.0
        cmd_above = validate('{"intent":"formation","shape":"line","spacing":5.1}')
        assert isinstance(cmd_above, Formation) and cmd_above.spacing == 5.0

    # --- Altitude z [0.5, 15.0] ---
    def test_z_lower_boundary_both_sides(self):
        # below lower -> clamped to 0.5
        cmd_below = validate('{"intent":"altitude","z":0.4}')
        assert isinstance(cmd_below, Altitude) and cmd_below.z == 0.5

        # at lower -> 0.5
        cmd_at = validate('{"intent":"altitude","z":0.5}')
        assert isinstance(cmd_at, Altitude) and cmd_at.z == 0.5

        # above lower -> 0.6
        cmd_above = validate('{"intent":"altitude","z":0.6}')
        assert isinstance(cmd_above, Altitude) and cmd_above.z == 0.6

    def test_z_upper_boundary_both_sides(self):
        # below upper -> 14.9
        cmd_below = validate('{"intent":"altitude","z":14.9}')
        assert isinstance(cmd_below, Altitude) and cmd_below.z == 14.9

        # at upper -> 15.0
        cmd_at = validate('{"intent":"altitude","z":15.0}')
        assert isinstance(cmd_at, Altitude) and cmd_at.z == 15.0

        # above upper -> clamped to 15.0
        cmd_above = validate('{"intent":"altitude","z":15.1}')
        assert isinstance(cmd_above, Altitude) and cmd_above.z == 15.0

    # --- Speed [0.2, 2.0] ---
    def test_speed_lower_boundary_both_sides(self):
        # below lower -> clamped to 0.2
        cmd_below = validate('{"intent":"set_param","speed":0.1}')
        assert isinstance(cmd_below, SetParam) and cmd_below.speed == 0.2

        # at lower -> 0.2
        cmd_at = validate('{"intent":"set_param","speed":0.2}')
        assert isinstance(cmd_at, SetParam) and cmd_at.speed == 0.2

        # above lower -> 0.3
        cmd_above = validate('{"intent":"set_param","speed":0.3}')
        assert isinstance(cmd_above, SetParam) and cmd_above.speed == 0.3

    def test_speed_upper_boundary_both_sides(self):
        # below upper -> 1.9
        cmd_below = validate('{"intent":"set_param","speed":1.9}')
        assert isinstance(cmd_below, SetParam) and cmd_below.speed == 1.9

        # at upper -> 2.0
        cmd_at = validate('{"intent":"set_param","speed":2.0}')
        assert isinstance(cmd_at, SetParam) and cmd_at.speed == 2.0

        # above upper -> clamped to 2.0
        cmd_above = validate('{"intent":"set_param","speed":2.1}')
        assert isinstance(cmd_above, SetParam) and cmd_above.speed == 2.0

    # --- Yaw Periodic Wrapping [-180.0, 180.0] ---
    def test_yaw_wrapping_boundaries(self):
        # -180.0 and 180.0 remain canonical boundaries
        assert validate('{"intent":"rotate","yaw":-180.0}').yaw == -180.0
        assert validate('{"intent":"rotate","yaw":180.0}').yaw == 180.0
        assert validate('{"intent":"rotate","yaw":-179.9}').yaw == -179.9
        assert validate('{"intent":"rotate","yaw":179.9}').yaw == 179.9

        # Continuous periodic modulo wrapping
        assert validate('{"intent":"rotate","yaw":-180.1}').yaw == 179.9
        assert validate('{"intent":"rotate","yaw":180.1}').yaw == -179.9
        assert validate('{"intent":"rotate","yaw":270.0}').yaw == -90.0
        assert validate('{"intent":"rotate","yaw":360.0}').yaw == 0.0
        assert validate('{"intent":"rotate","yaw":-270.0}').yaw == 90.0
        assert validate('{"intent":"rotate","yaw":720.0}').yaw == 0.0

    # --- Distance [0.0, 50.0] ---
    def test_dist_lower_boundary_both_sides(self):
        # below lower -> clamped to 0.0
        cmd_below = validate('{"intent":"move","dir":"north","dist":-0.1}')
        assert isinstance(cmd_below, Move) and cmd_below.dist == 0.0

        # at lower -> 0.0
        cmd_at = validate('{"intent":"move","dir":"north","dist":0.0}')
        assert isinstance(cmd_at, Move) and cmd_at.dist == 0.0

        # above lower -> 0.1
        cmd_above = validate('{"intent":"move","dir":"north","dist":0.1}')
        assert isinstance(cmd_above, Move) and cmd_above.dist == 0.1

    def test_dist_upper_boundary_both_sides(self):
        # below upper -> 49.9
        cmd_below = validate('{"intent":"move","dir":"north","dist":49.9}')
        assert isinstance(cmd_below, Move) and cmd_below.dist == 49.9

        # at upper -> 50.0
        cmd_at = validate('{"intent":"move","dir":"north","dist":50.0}')
        assert isinstance(cmd_at, Move) and cmd_at.dist == 50.0

        # above upper -> clamped to 50.0
        cmd_above = validate('{"intent":"move","dir":"north","dist":50.1}')
        assert isinstance(cmd_above, Move) and cmd_above.dist == 50.0

    # --- Altitude Target in SetParam alt [0.5, 15.0] ---
    def test_alt_lower_boundary_both_sides(self):
        # below lower -> clamped to 0.5
        cmd_below = validate('{"intent":"set_param","alt":0.4}')
        assert isinstance(cmd_below, SetParam) and cmd_below.alt == 0.5

        # at lower -> 0.5
        cmd_at = validate('{"intent":"set_param","alt":0.5}')
        assert isinstance(cmd_at, SetParam) and cmd_at.alt == 0.5

        # above lower -> 0.6
        cmd_above = validate('{"intent":"set_param","alt":0.6}')
        assert isinstance(cmd_above, SetParam) and cmd_above.alt == 0.6

    def test_alt_upper_boundary_both_sides(self):
        # below upper -> 14.9
        cmd_below = validate('{"intent":"set_param","alt":14.9}')
        assert isinstance(cmd_below, SetParam) and cmd_below.alt == 14.9

        # at upper -> 15.0
        cmd_at = validate('{"intent":"set_param","alt":15.0}')
        assert isinstance(cmd_at, SetParam) and cmd_at.alt == 15.0

        # above upper -> clamped to 15.0
        cmd_above = validate('{"intent":"set_param","alt":15.1}')
        assert isinstance(cmd_above, SetParam) and cmd_above.alt == 15.0

    # --- Position: Altitude [0.5, 15.0] and Euclidean Norm <= 50.0 m ---
    def test_pos_norm_and_altitude_boundaries(self):
        # Altitude ceiling clamp: pos.z clamped to 15.0
        cmd_ceiling = validate('{"intent":"move","pos":[0.0,0.0,40.0]}')
        assert isinstance(cmd_ceiling, Move)
        assert cmd_ceiling.pos == (0.0, 0.0, 15.0)

        # Ground floor clamp: pos.z clamped to 0.5
        cmd_ground = validate('{"intent":"move","pos":[0.0,0.0,-10.0]}')
        assert isinstance(cmd_ground, Move)
        assert cmd_ground.pos == (0.0, 0.0, 0.5)

        # Within envelope (norm = 30.0 < 50.0, z = 10.0) -> unchanged
        cmd_inside = validate('{"intent":"move","pos":[20.0,20.0,10.0]}')
        assert isinstance(cmd_inside, Move)
        assert cmd_inside.pos == (20.0, 20.0, 10.0)

        # At boundary (norm = 50.0) -> unchanged
        cmd_at = validate('{"intent":"move","pos":[30.0,40.0,0.5]}')
        assert isinstance(cmd_at, Move)
        assert cmd_at.pos == (30.0, 40.0, 0.5)

        # Above boundary (norm = 60.0) -> horizontal scaled to satisfy sphere norm <= 50.0 while preserving altitude z = 1.0
        cmd_above = validate('{"intent":"move","pos":[60.0,0.0,1.0]}')
        assert isinstance(cmd_above, Move)
        assert cmd_above.pos == (50.0, 0.0, 1.0)

        # 3D vector scaled horizontally preserving altitude floor z >= 0.5
        cmd_diag = validate('{"intent":"move","pos":[36.0,48.0,0.5]}')
        assert isinstance(cmd_diag, Move)
        assert cmd_diag.pos == (30.0, 40.0, 0.5)

        # Regression: pos within boundary whose 1-decimal coordinate rounding would exceed 50.0 m
        # [35.35, 35.35, 0.5] -> norm = 49.995 m, but rounding to (35.4, 35.4, 0.5) gives 50.066 m
        cmd_round_guard = validate('{"intent":"move","pos":[35.35,35.35,0.5]}')
        assert isinstance(cmd_round_guard, Move)
        assert cmd_round_guard.pos == (35.3, 35.4, 0.5)
        assert round(math.sqrt(sum(c * c for c in cmd_round_guard.pos)), 1) <= 50.0
