#!/usr/bin/env python3
"""f16 GGUF -> Q8_0 and Q4_K_M. The six artefacts of Session 05A.

Three models times two quantisations. The f16 GGUFs come down from Kaggle, because
merging a LoRA adapter and converting to GGUF both need torch and peft and §0.5 keeps
those off this workstation. `llama-quantize` is pure C++ and runs here.

Every output is hashed. Table 18's quantisation delta is a claim about a specific
pair of files, and "the Q4_K_M model scored X" is unreproducible if nobody can say
which Q4_K_M. The manifest also records the `llama.cpp` build, because quantisation
formats are not frozen across versions --- a Q4_K_M produced by a different build is
a different artefact even from identical f16 input.

Usage:
    python train/quantise.py                       # everything found
    python train/quantise.py --input train/kaggle_out/gguf
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence

REPO = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO / "train" / "kaggle_out" / "gguf"
DEFAULT_OUTPUT = REPO / "gguf"
LLAMA_QUANTIZE = Path.home() / "llama.cpp" / "build" / "bin" / "llama-quantize"
LLAMA_CPP = Path.home() / "llama.cpp"

#: prd.md Table 8 costs these at ~8.5 and ~4.85 bits per weight.
QUANTISATIONS = ("Q8_0", "Q4_K_M")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _build_id() -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(LLAMA_CPP), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10)
        return completed.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def quantise(source: Path, output_dir: Path, kind: str,
             binary: Path = LLAMA_QUANTIZE) -> dict:
    stem = source.name.removesuffix("-f16.gguf").removesuffix(".gguf")
    target = output_dir / f"{stem}-{kind}.gguf"
    started = time.monotonic()
    completed = subprocess.run(
        [str(binary), str(source), str(target), kind],
        capture_output=True, text=True)
    elapsed = time.monotonic() - started

    if completed.returncode != 0 or not target.is_file():
        return {"model": stem, "quantisation": kind, "ok": False,
                "error": (completed.stderr or completed.stdout)[-500:]}
    return {
        "model": stem,
        "quantisation": kind,
        "ok": True,
        "path": str(target.relative_to(REPO)),
        "bytes": target.stat().st_size,
        "mb": round(target.stat().st_size / (1024 * 1024), 1),
        "sha256": _sha256(target),
        "seconds": round(elapsed, 1),
    }


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--binary", type=Path, default=LLAMA_QUANTIZE)
    parser.add_argument("--quantisations", nargs="+", default=list(QUANTISATIONS))
    args = parser.parse_args(argv)

    if not args.binary.is_file():
        raise SystemExit(
            f"llama-quantize not found at {args.binary}\n"
            f"  build it: cd ~/llama.cpp && cmake --build build -j --target llama-quantize\n"
            f"  (cmake lives in the conda env, not on the base PATH)")
    if not args.input.is_dir():
        raise SystemExit(
            f"no f16 GGUFs at {args.input}\n"
            f"  they come from the Kaggle notebook -- download them from the Output panel\n"
            f"  individually (they are too large for pfe_outputs.zip) into that directory.")

    sources = sorted(args.input.glob("*f16*.gguf")) or sorted(args.input.glob("*.gguf"))
    if not sources:
        raise SystemExit(f"no .gguf files in {args.input}")

    args.output.mkdir(parents=True, exist_ok=True)
    print(f"llama.cpp build : {_build_id()}")
    print(f"sources         : {len(sources)}")

    artefacts = []
    for source in sources:
        source_mb = source.stat().st_size / (1024 * 1024)
        print(f"\n{source.name}  ({source_mb:.0f} MB)")
        for kind in args.quantisations:
            record = quantise(source, args.output, kind, args.binary)
            artefacts.append(record)
            if record["ok"]:
                ratio = source_mb / record["mb"]
                print(f"  {kind:7s} {record['mb']:7.1f} MB  ({ratio:.2f}x)  "
                      f"{record['seconds']:5.1f}s  {record['sha256'][:12]}")
            else:
                print(f"  {kind:7s} FAILED\n{record['error']}")

    manifest = args.output / "artefacts.json"
    manifest.write_text(json.dumps({
        "llama_cpp_build": _build_id(),
        "quantisations": list(args.quantisations),
        "artefacts": artefacts,
    }, indent=2) + "\n", encoding="utf-8")

    ok = sum(1 for a in artefacts if a["ok"])
    print(f"\n{ok}/{len(artefacts)} artefacts -> {args.output}")
    print(f"wrote {manifest.relative_to(REPO)}")
    if ok != len(artefacts):
        return 1
    if ok != 6:
        print(f"\n[!] Session 05A expects SIX artefacts (3 models x 2 quantisations); got {ok}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
