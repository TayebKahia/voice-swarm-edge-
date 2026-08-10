#!/usr/bin/env python3
"""Merge a PARTIAL Kaggle run's outputs into `train/kaggle_out/` without losing the
models already there.

The notebook prints `unzip -o pfe_outputs.zip -d train/kaggle_out/`, and for a full
run that is right. For a PARTIAL run -- the `ONLY` escape hatch, used to add one
model to a finished set -- it is destructive: `surface_a.csv` and `parity_hf.json`
in the zip describe only the model that just trained, and `-o` would overwrite the
versions describing the other three. Those two files are the sole record of every
other model's Surface-A numbers and Gate 3 HF side. They are git-tracked, so the
loss is recoverable, but it should not happen in the first place.

Per-model artefacts (`adapters/<model>/`, `preds_<model>_<split>.jsonl`) carry the
model name in their path and cannot collide, so those are copied straight across.
The two aggregate files are merged key-by-key instead.

Usage:
    python train/merge_kaggle_out.py ~/Downloads/pfe_outputs.zip
    python train/merge_kaggle_out.py ~/Downloads/pfe_outputs.zip --dry-run
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "train" / "kaggle_out"


def _merge_surface_a(staged: Path, target: Path, dry: bool) -> list[str]:
    """Append the new run's rows, keeping every row already present.

    Keyed on (model, surface, split) so re-running this script is idempotent: a
    model merged twice replaces its own rows rather than duplicating them.
    """
    notes: list[str] = []
    if not staged.is_file():
        return ["surface_a.csv: not in the zip, nothing to merge"]

    new_rows = list(csv.DictReader(staged.open()))
    if target.is_file():
        old_rows = list(csv.DictReader(target.open()))
    else:
        old_rows, notes = [], ["surface_a.csv: no existing file, writing fresh"]

    key = lambda r: (r["model"], r["surface"], r["split"])
    incoming = {key(r) for r in new_rows}
    kept = [r for r in old_rows if key(r) not in incoming]
    dropped = len(old_rows) - len(kept)

    merged = kept + new_rows
    models_before = sorted({r["model"] for r in old_rows})
    models_after = sorted({r["model"] for r in merged})
    notes.append(f"surface_a.csv: {len(old_rows)} existing + {len(new_rows)} new "
                 f"-> {len(merged)} rows ({dropped} replaced)")
    notes.append(f"  models before: {models_before}")
    notes.append(f"  models after : {models_after}")

    if set(models_before) - set(models_after):
        raise SystemExit(f"REFUSING: merge would lose models "
                         f"{sorted(set(models_before) - set(models_after))}")

    if not dry:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=new_rows[0].keys())
        writer.writeheader()
        writer.writerows(merged)
        target.write_text(buf.getvalue())
    return notes


def _merge_parity(staged: Path, target: Path, dry: bool) -> list[str]:
    """Union the per-model records; assert the system prompt has not drifted."""
    notes: list[str] = []
    if not staged.is_file():
        return ["parity_hf.json: not in the zip, nothing to merge"]

    new = json.loads(staged.read_text())
    old = json.loads(target.read_text()) if target.is_file() else {"models": {}}

    if old.get("system_prompt") and old["system_prompt"] != new["system_prompt"]:
        raise SystemExit(
            "REFUSING: the system prompt differs between runs.\n"
            f"  existing: {old['system_prompt']!r}\n"
            f"  incoming: {new['system_prompt']!r}\n"
            "Gate 3 compares token IDs derived from this string; merging two "
            "different prompts would silently compare unlike with unlike.")

    models = dict(old.get("models", {}))
    before = sorted(models)
    models.update(new.get("models", {}))
    after = sorted(models)

    folded = dict(old.get("system_role_folded", {}))
    folded.update(new.get("system_role_folded", {}))

    merged = {"system_prompt": new["system_prompt"], "models": models}
    if folded:
        merged["system_role_folded"] = folded

    notes.append(f"parity_hf.json: models before {before}")
    notes.append(f"                models after  {after}")
    if folded:
        notes.append(f"                system_role_folded: {folded}")
    if set(before) - set(after):
        raise SystemExit("REFUSING: merge would lose parity records")

    if not dry:
        target.write_text(json.dumps(merged, indent=2))
    return notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("zip_path", type=Path, help="the downloaded pfe_outputs.zip")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change, write nothing")
    args = ap.parse_args()

    if not args.zip_path.is_file():
        raise SystemExit(f"no such file: {args.zip_path}")

    OUT.mkdir(parents=True, exist_ok=True)
    notes: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp)
        with zipfile.ZipFile(args.zip_path) as archive:
            archive.extractall(staging)

        # Per-model artefacts: namespaced by model, so a straight copy is safe.
        copied = []
        for src in sorted(staging.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(staging)
            if rel.name in {"surface_a.csv", "parity_hf.json"}:
                continue
            if rel.suffix == ".ipynb":          # the executed notebook, not an artefact
                continue
            dest = OUT / rel
            copied.append(str(rel))
            if not args.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
        notes.append(f"copied {len(copied)} per-model files:")
        notes += [f"  {c}" for c in copied]

        notes += _merge_surface_a(staging / "surface_a.csv",
                                  OUT / "surface_a.csv", args.dry_run)
        notes += _merge_parity(staging / "parity_hf.json",
                               OUT / "parity_hf.json", args.dry_run)

    print("\n".join(notes))
    print("\nDRY RUN -- nothing written." if args.dry_run else "\nmerged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
