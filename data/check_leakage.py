"""Split leakage verification gate (PRD Sec. 9, FR-1, Gate 2).

Verifies strict isolation between training and evaluation splits across two axes:
1. Template Family Isolation: No template family ID spans across split boundaries.
2. Surface-Form Lexical Isolation: No identical or near-duplicate transcripts
   (via token Jaccard similarity > 0.85 or exact string match) cross between
   train and held-out splits (val, test_synth, test_golden).

Exit Codes:
- 0: All leakage checks passed strictly (Gate 2 GREEN).
- 1: Leakage detected across split boundaries or configuration invalid.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

FAMILIES_JSON_PATH = Path(__file__).parent / "template_families.json"
DATA_DIR = Path(__file__).parent


def normalize_transcript(text: str) -> str:
    """Normalize text for lexical comparison (lowercase, strip punctuation and extra spaces)."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_token_ngrams(text: str, n: int = 3) -> set[tuple[str, ...]]:
    """Extract word n-grams from text."""
    tokens = text.split()
    if len(tokens) < n:
        return {tuple(tokens)}
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def jaccard_similarity(set_a: set[Any], set_b: set[Any]) -> float:
    """Compute Jaccard similarity coefficient between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def check_template_family_integrity(families_path: Path = FAMILIES_JSON_PATH) -> list[str]:
    """Verify integrity of pre-assigned template families."""
    errors: list[str] = []
    if not families_path.is_file():
        errors.append(f"Template families file not found: {families_path}")
        return errors

    with open(families_path, encoding="utf-8") as fp:
        try:
            families = json.load(fp)
        except json.JSONDecodeError as e:
            return [f"Failed to parse {families_path}: {e}"]

    if len(families) != 120:
        errors.append(f"Expected exactly 120 template families, found {len(families)}")

    family_ids = [f["family_id"] for f in families if "family_id" in f]
    if len(family_ids) != len(set(family_ids)):
        duplicates = [fid for fid in family_ids if family_ids.count(fid) > 1]
        errors.append(f"Duplicate family IDs detected: {set(duplicates)}")

    splits: dict[str, int] = {}
    for f in families:
        sp = f.get("split", "unknown")
        splits[sp] = splits.get(sp, 0) + 1

    if splits.get("train", 0) != 96:
        errors.append(f"Expected 96 train families, found {splits.get('train', 0)}")
    if splits.get("val", 0) != 12:
        errors.append(f"Expected 12 val families, found {splits.get('val', 0)}")
    if splits.get("test_synth", 0) != 12:
        errors.append(f"Expected 12 test_synth families, found {splits.get('test_synth', 0)}")

    return errors


def check_dataset_split_leakage(
    train_rows: list[dict[str, Any]],
    held_out_rows: list[dict[str, Any]],
    held_out_name: str = "held_out",
    sim_threshold: float = 0.85,
) -> list[str]:
    """Check for family ID overlap and surface-form lexical near-duplicates."""
    errors: list[str] = []

    # `template_family` is the key §7.4 fixes for the record format; `family_id`
    # is accepted as a fallback for hand-written fixtures. Reading only
    # `family_id` (as this did before Session 02A) meant both sets came out empty
    # on a conformant corpus and the overlap check passed without comparing
    # anything --- a gate that cannot fail. Issue 26.
    def _family(row: dict[str, Any]) -> str | None:
        return row.get("template_family") or row.get("family_id")

    train_families = {f for r in train_rows if (f := _family(r))}
    held_out_families = {f for r in held_out_rows if (f := _family(r))}

    if not train_families or not held_out_families:
        errors.append(
            f"no template_family on {'train' if not train_families else held_out_name} rows; "
            f"the family-overlap check cannot run (expected key 'template_family', §7.4)"
        )

    overlap_families = train_families & held_out_families
    if overlap_families:
        errors.append(
            f"Family ID leakage between train and {held_out_name}: {sorted(overlap_families)}"
        )

    # Surface form leakage check
    train_transcripts: dict[str, str] = {}
    train_ngrams: dict[str, set[tuple[str, ...]]] = {}
    for r in train_rows:
        text = r.get("transcript") or r.get("text") or ""
        norm = normalize_transcript(text)
        if norm:
            train_transcripts[norm] = text
            train_ngrams[norm] = get_token_ngrams(norm, n=2)

    leakage_count = 0
    for r in held_out_rows:
        text = r.get("transcript") or r.get("text") or ""
        norm = normalize_transcript(text)
        if not norm:
            continue

        # Exact match
        if norm in train_transcripts:
            errors.append(
                f"Exact transcript match across split (train vs {held_out_name}): {text!r}"
            )
            leakage_count += 1
            if leakage_count >= 10:
                break
            continue

        # Near-duplicate check via token set and n-gram Jaccard similarity
        held_tokens = set(norm.split())
        ngrams = get_token_ngrams(norm, n=2)
        for train_norm, t_ngrams in train_ngrams.items():
            train_tokens = set(train_norm.split())
            token_sim = jaccard_similarity(held_tokens, train_tokens)
            ngram_sim = jaccard_similarity(ngrams, t_ngrams)
            sim = max(token_sim, ngram_sim)
            if sim >= sim_threshold:
                errors.append(
                    f"Surface-form near-duplicate ({sim:.2f}) across split (train vs {held_out_name}):\n"
                    f"  held-out: {text!r}\n"
                    f"  train:    {train_transcripts[train_norm]!r}"
                )
                leakage_count += 1
                break
        if leakage_count >= 10:
            break

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify dataset split isolation (Gate 2).")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on any detected leakage or validation failure.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Jaccard similarity threshold for near-duplicate surface form rejection (default: 0.85).",
    )
    args = parser.parse_args()

    print("Running Gate 2 split leakage verification...")
    all_errors: list[str] = []

    # 1. Template families static integrity
    family_errors = check_template_family_integrity(FAMILIES_JSON_PATH)
    all_errors.extend(family_errors)
    if family_errors:
        print("[-] Template family integrity check FAILED:")
        for err in family_errors:
            print(f"    - {err}")
    else:
        print("[+] Template family integrity: PASS (120 families: 96 train, 12 val, 12 test_synth)")

    # 2. Check the generated corpus.
    #
    # Session 02A writes one `raw_pairs.jsonl` carrying a `split` field per row
    # rather than three pre-split files; the per-split files arrive in 02B, after
    # augmentation, because a row's variants must land in its own split. Both
    # layouts are read here so the gate works before and after that step.
    raw_pairs_file = DATA_DIR / "raw_pairs.jsonl"
    train_file = DATA_DIR / "train.jsonl"
    val_file = DATA_DIR / "val.jsonl"
    test_file = DATA_DIR / "test_synth.jsonl"
    golden_file = DATA_DIR / "test_golden.jsonl"

    def _rows(path: Path) -> list[dict[str, Any]]:
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    held_out_sets: list[tuple[str, list[dict[str, Any]]]] = []
    train_rows: list[dict[str, Any]] = []

    if train_file.is_file():
        print("[*] Inspecting pre-split files for leakage...")
        train_rows = _rows(train_file)
        for split_file, split_name in [(val_file, "val"), (test_file, "test_synth")]:
            if split_file.is_file():
                held_out_sets.append((split_name, _rows(split_file)))
    elif raw_pairs_file.is_file():
        print("[*] Inspecting raw_pairs.jsonl for leakage...")
        all_rows = _rows(raw_pairs_file)
        train_rows = [r for r in all_rows if r.get("split") == "train"]
        for split_name in ("val", "test_synth"):
            held = [r for r in all_rows if r.get("split") == split_name]
            if held:
                held_out_sets.append((split_name, held))
        print(
            f"    {len(all_rows)} rows: {len(train_rows)} train, "
            + ", ".join(f"{len(h)} {n}" for n, h in held_out_sets)
        )

    if train_rows and golden_file.is_file():
        held_out_sets.append(("test_golden", _rows(golden_file)))

    if train_rows:
        for split_name, held_rows in held_out_sets:
            split_errors = check_dataset_split_leakage(
                train_rows, held_rows, split_name, sim_threshold=args.threshold
            )
            all_errors.extend(split_errors)
            if split_errors:
                print(f"[-] Leakage detected between train and {split_name}:")
                for err in split_errors[:5]:
                    print(f"    - {err}")
            else:
                print(
                    f"[+] Split isolation (train vs {split_name}): PASS "
                    f"({len(held_rows)} rows, 0 overlaps, 0 near-duplicates)"
                )
    else:
        print("[*] Generated data splits not yet materialized (Session 02A pending). Family assignments verified.")

    if all_errors:
        print(f"\n[-] Gate 2 FAILED with {len(all_errors)} errors.")
        return 1

    print("\n[+] Gate 2 verification SUCCESSFUL: No leakage detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
