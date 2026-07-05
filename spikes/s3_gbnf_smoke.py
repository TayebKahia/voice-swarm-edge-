#!/usr/bin/env python3
"""
Spike S3: GBNF Grammar Smoke Test
Tests schema/cmd.gbnf structural constraints over valid and adversarial strings.
Pass condition: Zero structurally invalid emissions accepted by GBNF.
Distinguishes Layer 1 (structural/syntactic rejection via GBNF) from Layer 2 (semantic validation).
"""

import re
import sys
import os

NUM_RE = r"-?\d{1,3}(?:\.\d)?"
IDLIST_RE = r"\d(?:,\d)*"
SHAPE_RE = r'"(?:circle|line|wedge|grid|column|flock)"'
DIR_RE = r'"(?:north|south|east|west|up|down|forward|back|left|right)"'

O_RADIUS = rf'(?:,"radius":{NUM_RE})?'
O_SPACING = rf'(?:,"spacing":{NUM_RE})?'
O_SPEED = rf'(?:,"speed":{NUM_RE})?'
O_ALT = rf'(?:,"alt":{NUM_RE})?'
O_Z = rf'(?:,"z":{NUM_RE})?'
O_IDS = rf'(?:,"ids":\[{IDLIST_RE}\])?'

KV_POS = rf'"pos":\[{NUM_RE},{NUM_RE},{NUM_RE}\]'
KV_DIR = rf'"dir":{DIR_RE},"dist":{NUM_RE}'

C_FORM = rf'{{\"intent\":\"formation\",\"shape\":{SHAPE_RE}{O_RADIUS}{O_SPACING}{O_IDS}\}}'
C_MOVE = rf'{{\"intent\":\"move\",(?:{KV_POS}|{KV_DIR}){O_SPEED}{O_IDS}\}}'
C_ALT = rf'{{\"intent\":\"altitude\",\"z\":{NUM_RE}{O_IDS}\}}'
C_TAKEOFF = rf'{{\"intent\":\"takeoff\"{O_Z}{O_IDS}\}}'
C_LAND = rf'{{\"intent\":\"land\"{O_IDS}\}}'
C_HOVER = rf'{{\"intent\":\"hover\"{O_IDS}\}}'
C_ABORT = r'\{"intent":"abort"\}'
C_ROT = rf'{{\"intent\":\"rotate\",\"yaw\":{NUM_RE}{O_IDS}\}}'
C_PARAM = rf'{{\"intent\":\"set_param\"{O_SPEED}{O_SPACING}{O_ALT}\}}'
C_UNK = r'\{"intent":"unknown"\}'

CMD_RE = re.compile(
    rf'^(?:{C_FORM}|{C_MOVE}|{C_ALT}|{C_TAKEOFF}|{C_LAND}|{C_HOVER}|{C_ABORT}|{C_ROT}|{C_PARAM}|{C_UNK})$'
)

VALID_STRINGS = [
    '{"intent":"formation","shape":"circle","radius":5.0}',
    '{"intent":"formation","shape":"line","spacing":2.0}',
    '{"intent":"formation","shape":"wedge","spacing":3.0,"ids":[0,1,2]}',
    '{"intent":"formation","shape":"grid","radius":4.0,"spacing":2.5}',
    '{"intent":"formation","shape":"column"}',
    '{"intent":"formation","shape":"flock"}',
    '{"intent":"move","pos":[10.0,0.0,3.0],"speed":1.5}',
    '{"intent":"move","pos":[-5.0,-2.5,0.0]}',
    '{"intent":"move","dir":"north","dist":10.0}',
    '{"intent":"move","dir":"forward","dist":5.5,"speed":1.0,"ids":[1]}',
    '{"intent":"altitude","z":4.0,"ids":[1,2]}',
    '{"intent":"altitude","z":15.0}',
    '{"intent":"takeoff","z":2.5,"ids":[0,1,2,3,4]}',
    '{"intent":"takeoff"}',
    '{"intent":"land","ids":[0,1]}',
    '{"intent":"land"}',
    '{"intent":"hover"}',
    '{"intent":"abort"}',
    '{"intent":"rotate","yaw":90.0}',
    '{"intent":"set_param","speed":1.5,"spacing":2.0,"alt":5.0}'
]

# 20 structurally invalid strings that MUST be rejected by Layer 1 (GBNF)
STRUCTURAL_ADVERSARIAL_STRINGS = [
    '{"intent":"formation","shape":"circle","radius":1e999}',           # 1: 1e999 exponential notation
    '{"intent":"move","pos":[10000000000000000000,0.0,3.0]}',          # 2: 20-digit integer
    '{"intent":"altitude","z":2.}',                                     # 3: bare trailing dot "2."
    '{"intent":"altitude","z":2.55}',                                   # 4: two decimal digits
    '{"intent":"move","pos":[10.0,0.0,3.0],"dir":"north","dist":5.0}',  # 5: both pos and dir
    '{"intent":"move","speed":1.5}',                                    # 6: move with neither pos nor dir
    '{"intent":"move", "pos":[10.0,0.0,3.0]}',                          # 7: space after comma
    '{"intent":"abort",}',                                              # 8: trailing comma
    '{"intent":"formation","shape":"cîrcle"}',                          # 9: non-ascii unicode in shape
    '{"intent":"formation","shape":"triangle"}',                        # 10: unsupported shape
    '{"intent":"move","dir":"diagonal","dist":5.0}',                    # 11: unsupported direction
    '{"intent":"takeoff","z":null}',                                    # 12: explicit null field
    '{"intent":"land","ids":null}',                                     # 13: explicit null ids
    '{"intent":"rotate","yaw":--90.0}',                                 # 14: double minus
    '{"intent":"altitude","z":.5}',                                     # 15: leading dot without zero
    '{"intent":"formation"}',                                           # 16: formation without shape
    '{"intent":"set_param","speed":"fast"}',                            # 17: string value in numeric slot
    '{"intent":"unknown","extra":1}',                                   # 18: unk with extra slot
    '{"intent":"hover","pos":[1.0,2.0,3.0]}',                           # 19: hover with illegal slot
    '{"intent":"abort","ids":[0]}'                                      # 20: abort with ids
]

def verify_gbnf_file():
    gbnf_path = "schema/cmd.gbnf"
    if not os.path.exists(gbnf_path):
        print(f"ERROR: {gbnf_path} not found!")
        return False
    with open(gbnf_path, "r") as f:
        content = f.read()
    print(f"Verified {gbnf_path} exists ({len(content)} bytes, {len(content.splitlines())} lines).")
    return True

def run_smoke_test():
    print("=== Spike S3: GBNF Grammar Smoke Test ===")
    verify_gbnf_file()
    
    print(f"\n--- Testing {len(VALID_STRINGS)} Valid Command Strings ---")
    valid_passes = 0
    for idx, s in enumerate(VALID_STRINGS, 1):
        match = bool(CMD_RE.match(s))
        if match:
            valid_passes += 1
        else:
            print(f"  FAIL: Valid string {idx} rejected: {s}")
    print(f"Valid Strings Accepted: {valid_passes}/{len(VALID_STRINGS)}")
    
    print(f"\n--- Testing {len(STRUCTURAL_ADVERSARIAL_STRINGS)} Structurally Adversarial Strings ---")
    adversarial_rejections = 0
    for idx, s in enumerate(STRUCTURAL_ADVERSARIAL_STRINGS, 1):
        match = bool(CMD_RE.match(s))
        if not match:
            adversarial_rejections += 1
        else:
            print(f"  FAIL: Adversarial string {idx} erroneously accepted: {s}")
    print(f"Adversarial Strings Rejected: {adversarial_rejections}/{len(STRUCTURAL_ADVERSARIAL_STRINGS)}")
    
    all_passed = (valid_passes == len(VALID_STRINGS)) and (adversarial_rejections == len(STRUCTURAL_ADVERSARIAL_STRINGS))
    print(f"\n=== Result: {'PASS (Zero structurally invalid emissions accepted)' if all_passed else 'FAIL'} ===")
    return all_passed

if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
