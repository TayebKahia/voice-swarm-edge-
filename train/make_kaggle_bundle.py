#!/usr/bin/env python3
"""Assemble the single zip that gets uploaded to Kaggle as a Dataset.

Nothing persists between Kaggle sessions (§2.8a trap 2), so everything the
notebook needs must arrive as a Dataset: the splits, the schema package the
exact-match comparator lives in, the fixed audit prompts Gate 3 is defined
against, and the three Table 14 configs.

`schema/` travels with the data deliberately. Exact match is `canon(pred) ==
canon(gold)` (§2.7), and `canon` is the *one* comparator (`schema/canon.py`).
Re-implementing a JSON comparison inside the notebook would mean the validation
metric that selects the checkpoint and the metric reported in Table 17 could
disagree about whether a prediction is correct --- silently, since both would run.

Usage:
    python train/make_kaggle_bundle.py
"""

from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUTPUT = REPO / "train" / "pfe_kaggle_data.zip"

#: Published path inside the zip -> source in the repo. The published paths are
#: what the notebook opens, so they are part of its interface.
CONTENTS: dict[str, str] = {
    "data/train.jsonl": "data/train.jsonl",
    "data/val.jsonl": "data/val.jsonl",
    "data/test_synth.jsonl": "data/test_synth.jsonl",
    "data/test_golden.jsonl": "data/test_golden.jsonl",
    "data/test_ood.jsonl": "data/test_ood.jsonl",
    "schema/__init__.py": "schema/__init__.py",
    "schema/schema.py": "schema/schema.py",
    "schema/canon.py": "schema/canon.py",
    "schema/validate.py": "schema/validate.py",
    "schema/cmd.gbnf": "schema/cmd.gbnf",
    "eval/fixed_audit_prompts.json": "eval/fixed_audit_prompts.json",
    "configs/qwen2.5-0.5b.yaml": "train/configs/qwen2.5-0.5b.yaml",
    "configs/smollm2-360m.yaml": "train/configs/smollm2-360m.yaml",
    "configs/llama-3.2-1b.yaml": "train/configs/llama-3.2-1b.yaml",
}


def build(output: Path = OUTPUT) -> Path:
    missing = [src for src in CONTENTS.values() if not (REPO / src).is_file()]
    if missing:
        raise SystemExit("missing from the repo:\n  " + "\n  ".join(missing))

    output.parent.mkdir(parents=True, exist_ok=True)
    # Deterministic member order so the zip's digest changes only when content does.
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for published in sorted(CONTENTS):
            archive.write(REPO / CONTENTS[published], published)
    return output


def main() -> int:
    output = build()
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"wrote {output.relative_to(REPO)}  ({output.stat().st_size / 1e6:.2f} MB)")
    print(f"sha256 {digest}")
    print(f"members {len(CONTENTS)}")
    print(
        "\nUpload as a Kaggle Dataset named  pfe-swarm-data\n"
        "  Kaggle -> Datasets -> New Dataset -> upload this zip -> title 'pfe-swarm-data'\n"
        "  Kaggle unpacks it, so the notebook reads /kaggle/input/pfe-swarm-data/data/train.jsonl"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
