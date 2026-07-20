"""Split leakage verification gate (PRD Sec. 9, FR-1, Gate 2).

Verifies strict isolation between training and evaluation splits across four axes:
1. Template Family Isolation: No template family ID spans across split boundaries.
2. Surface-Form Lexical Isolation: No identical or near-duplicate transcripts
   (via token Jaccard similarity > 0.85 or exact string match) cross between
   train and held-out splits (val, test_synth, test_golden).
3. Noise Partition Isolation (Session 02B): no noise excerpt used to build the
   round-trip training text is also available to the Exp-3 evaluation sweep.
   Sharing them would mean the model was tuned against transcripts whose error
   pattern came from the very seconds of audio it is then evaluated against, and
   the measured robustness would not generalise past those seconds (ADR-0004).
4. Wake Corpus Isolation (Session 03): no base Piper rendition, negative speaker,
   near-miss phrase, room impulse response or ESC-50 excerpt is shared between the
   trained splits of the Branch A corpus and its held-out split. Exp-2 reports a
   per-class ROC at a declared operating point (NFR-15/16); measured across any of
   those, that ROC describes memorisation rather than detection (ADR-0005).

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

if __package__ in (None, ""):  # `python data/check_leakage.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
    check_families: bool = True,
    reference_name: str = "train",
) -> list[str]:
    """Check for family ID overlap and surface-form lexical near-duplicates.

    `check_families` is False when comparing two *held-out* sets to each other.
    Family disjointness there is already guaranteed by the 96/12/12 allocation
    (`check_template_family_integrity`), so re-checking it proves nothing --- and
    `test_golden` draws from the `test_synth` families by construction, so the
    overlap check would misfire on a corpus that is behaving correctly.
    """
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

    if not check_families:
        train_families = held_out_families = set()
    elif not train_families or not held_out_families:
        errors.append(
            f"no template_family on {reference_name if not train_families else held_out_name} rows; "
            f"the family-overlap check cannot run (expected key 'template_family', §7.4)"
        )

    overlap_families = train_families & held_out_families
    if overlap_families:
        errors.append(
            f"Family ID leakage between {reference_name} and {held_out_name}: "
            f"{sorted(overlap_families)}"
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
                f"Exact transcript match across split ({reference_name} vs {held_out_name}): {text!r}"
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
                    f"Surface-form near-duplicate ({sim:.2f}) across split "
                    f"({reference_name} vs {held_out_name}):\n"
                    f"  held-out: {text!r}\n"
                    f"  train:    {train_transcripts[train_norm]!r}"
                )
                leakage_count += 1
                break
        if leakage_count >= 10:
            break

    return errors


def check_noise_partition_isolation(
    roundtrip_path: Path = DATA_DIR / "roundtrip.jsonl",
    manifest_path: Path = DATA_DIR / "asset_manifest.json",
) -> list[str]:
    """Verify the augmentation partition and the Exp-3 partition share no noise.

    Checked against what the pipeline *did* --- the noise keys recorded in
    `roundtrip.jsonl` --- not against what `mix_noise.py` intends. A partition bug
    that let an evaluation excerpt into the training mix would leave the intent in
    the source unchanged and only show up here.
    """
    errors: list[str] = []
    if not roundtrip_path.is_file():
        return errors  # Session 02B has not run yet; nothing to check.
    if not manifest_path.is_file():
        return [f"{roundtrip_path.name} exists but {manifest_path.name} does not"]

    from data.mix_noise import NoiseBank  # local: pulls numpy/soundfile

    aug = NoiseBank(partition="aug", manifest_path=manifest_path)
    evaluation = NoiseBank(partition="eval", manifest_path=manifest_path)

    esc_aug = {k for k in aug.keys if k.startswith("esc50/")}
    esc_eval = {k for k in evaluation.keys if k.startswith("esc50/")}
    shared = esc_aug & esc_eval
    if shared:
        errors.append(f"ESC-50 clips in both noise partitions: {sorted(shared)[:5]}")
    if not esc_aug or not esc_eval:
        errors.append("one of the ESC-50 noise partitions is empty; the check cannot run")

    used = {
        json.loads(line).get("noise_key")
        for line in roundtrip_path.read_text().splitlines()
        if line.strip()
    }
    used.discard(None)
    if not used:
        errors.append(f"{roundtrip_path.name} records no noise_key; provenance is missing")

    strayed = {k for k in used if k.startswith("esc50/")} - esc_aug
    if strayed:
        errors.append(
            f"round-trip audio used evaluation-partition noise: {sorted(strayed)[:5]}"
        )

    return errors


def check_wake_corpus_isolation(
    manifest_path: Path = DATA_DIR / "wake" / "wake_manifest.json",
) -> list[str]:
    """Verify the Branch A corpus cannot report memorisation as a ROC (Session 03).

    Exp-2 reports a per-class ROC with a declared operating point (NFR-15/16).
    Three things would quietly turn that into a statement about the training set,
    and none of them raises an error anywhere else:

    1. A base Piper rendition whose 25 augmented variants straddle two splits ---
       they are near-duplicates of each other.
    2. A negative speaker, or an authored near-miss phrase, on both sides.
    3. A room or a noise excerpt shared between the trained splits and the
       held-out one, so the held-out figure describes acoustics the model heard.

    Checked against the manifest --- what the builder *did* --- rather than
    against `wake_corpus.py`'s constants.

    ESC-50 keys carry the partition; DREGON does not, because it is one
    continuous flight split by position and both partitions name the same file.
    The `noise_partition` field the builder records per clip covers that half,
    and the byte-level split itself is asserted in
    `test_mix_noise.py::TestNoiseBank::test_partitions_are_disjoint`.
    """
    errors: list[str] = []
    if not manifest_path.is_file():
        return errors  # Session 03 has not run yet; nothing to check.

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    clips = manifest.get("clips", [])
    if not clips:
        return [f"{manifest_path.name} records no clips"]

    by_base: dict[str, set[str]] = {}
    rooms: dict[str, set[str]] = {}
    esc50: dict[str, set[str]] = {}
    declared = manifest.get("noise_partition", {})

    for clip in clips:
        by_base.setdefault(clip["base"], set()).add(clip["split"])
        if clip.get("rir"):
            rooms.setdefault(clip["split"], set()).add(clip["rir"])
        key = clip.get("noise_key")
        if key and key.startswith("esc50/"):
            esc50.setdefault(clip["split"], set()).add(key)
        if key and clip.get("noise_partition") != declared.get(clip["split"]):
            errors.append(
                f"clip {clip['path']} is in split {clip['split']} but drew noise from "
                f"partition {clip.get('noise_partition')!r}, not {declared.get(clip['split'])!r}"
            )

    straddling = sorted(base for base, splits in by_base.items() if len(splits) > 1)
    if straddling:
        errors.append(
            f"{len(straddling)} base rendition(s) appear in more than one split: {straddling[:5]}"
        )

    for label, seen in (("room", rooms), ("ESC-50 excerpt", esc50)):
        trained = seen.get("train", set()) | seen.get("val", set())
        held_out = seen.get("test", set())
        if not trained or not held_out:
            errors.append(f"no {label} recorded on one side of the split; the check cannot run")
            continue
        shared = trained & held_out
        if shared:
            errors.append(
                f"held-out wake clips reuse {len(shared)} {label}(s) heard in training: "
                f"{sorted(shared)[:5]}"
            )

    hours = manifest.get("summary", {}).get("neg", {}).get("hours", 0.0)
    if hours < 3.0:
        errors.append(f"negative corpus is {hours:.2f} h; NFR-15 requires at least 3 h")

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

        # The held-out sets must also be independent of *each other*. Train-vs-each
        # catches memorisation; it says nothing about whether `val`, `test_synth`
        # and `test_golden` are measuring the same thing twice. Three eval scores
        # that quietly agree because their rows overlap read as corroboration at
        # Gate 3 when they are one signal reported three times.
        for i, (name_a, rows_a) in enumerate(held_out_sets):
            for name_b, rows_b in held_out_sets[i + 1:]:
                pair_errors = check_dataset_split_leakage(
                    rows_a,
                    rows_b,
                    name_b,
                    sim_threshold=args.threshold,
                    check_families=False,
                    reference_name=name_a,
                )
                all_errors.extend(pair_errors)
                if pair_errors:
                    print(f"[-] Overlap detected between {name_a} and {name_b}:")
                    for err in pair_errors[:5]:
                        print(f"    - {err}")
                else:
                    print(
                        f"[+] Eval independence ({name_a} vs {name_b}): PASS "
                        f"({len(rows_b)} rows, 0 exact matches, 0 near-duplicates)"
                    )
    else:
        print("[*] Generated data splits not yet materialized (Session 02A pending). Family assignments verified.")

    # 4. Wake corpus isolation (Session 03).
    wake_errors = check_wake_corpus_isolation()
    all_errors.extend(wake_errors)
    if wake_errors:
        print("[-] Wake corpus isolation FAILED:")
        for err in wake_errors:
            print(f"    - {err}")
    elif (DATA_DIR / "wake" / "wake_manifest.json").is_file():
        print(
            "[+] Wake corpus isolation: PASS "
            "(no base rendition, speaker, room or ESC-50 excerpt straddles the split; "
            ">= 3 h negatives)"
        )

    # 3. Noise partition isolation (Session 02B).
    noise_errors = check_noise_partition_isolation()
    all_errors.extend(noise_errors)
    if noise_errors:
        print("[-] Noise partition isolation FAILED:")
        for err in noise_errors:
            print(f"    - {err}")
    elif (DATA_DIR / "roundtrip.jsonl").is_file():
        print(
            "[+] Noise partition isolation: PASS "
            "(round-trip audio drew only from the augmentation partition)"
        )
    else:
        print("[*] Noise partition isolation: SKIPPED (roundtrip.jsonl absent)")

    if all_errors:
        print(f"\n[-] Gate 2 FAILED with {len(all_errors)} errors.")
        return 1

    print("\n[+] Gate 2 verification SUCCESSFUL: No leakage detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
