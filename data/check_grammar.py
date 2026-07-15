#!/usr/bin/env python3
"""Gate for Session 02A: every generated label is accepted by `schema/cmd.gbnf`.

    python data/check_grammar.py                    # all four artefacts
    python data/check_grammar.py data/raw_pairs.jsonl
    python data/check_grammar.py --no-llama         # skip the cross-check

Exit 0 if every label in every file is accepted, 1 otherwise. This is FR-1, and
the roadmap requires the gate to be run over the artefacts rather than asserted
during generation --- `data/generate.py` checks as it builds, which catches a bug
before it reaches disk, but only a pass over the *written files* proves that what
landed on disk is what was checked.

## Two acceptors, on purpose

`data/gbnf.py` parses `schema/cmd.gbnf` and matches against it. That removes the
duplication risk (README:56, Trap 5) but introduces a different one: if the
interpreter is wrong in the same direction as the generator, the gate passes and
Exp-1 fails. So where `llama.cpp` is built this script also runs
`llama-gbnf-validator` --- the parser that will actually constrain decoding at
inference time --- and *disagreement between the two is a failure*, even when the
Python side accepts.

The cross-check runs over the set of **distinct** labels rather than all rows.
2,750 rows collapse to a few hundred distinct labels, and the validator is a
process launch per label, so this is the difference between seconds and minutes
for identical coverage.

If `llama-gbnf-validator` is not on this machine the script says so and still
exits 0 on the Python result alone. That is a real gap in gate strength, not a
pass to be quoted without the caveat: the printed summary names which acceptors
ran, and that line is what belongs in the issue tracker.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.gbnf import Grammar, load_grammar
from schema.schema import GRAMMAR_PATH

DATA_DIR = Path(__file__).parent
REPO_ROOT = DATA_DIR.parent

DEFAULT_FILES = (
    DATA_DIR / "raw_pairs.jsonl",
    DATA_DIR / "test_golden.jsonl",
    DATA_DIR / "test_ood.jsonl",
)

VALIDATOR_NAMES = ("llama-gbnf-validator", "gbnf-validator")
VALIDATOR_DIRS = (
    Path.home() / "llama.cpp" / "build" / "bin",
    Path.home() / "llama.cpp" / "build",
    Path("/opt/llama.cpp/build/bin"),
    Path("/usr/local/bin"),
    REPO_ROOT / "third_party" / "llama.cpp" / "build" / "bin",
)


def find_validator() -> Path | None:
    """Locate `llama-gbnf-validator`, or None if it is not on this machine."""
    env = os.environ.get("LLAMA_CPP_DIR")
    dirs = [Path(env) / "build" / "bin", Path(env) / "build"] if env else []
    dirs.extend(VALIDATOR_DIRS)
    for directory in dirs:
        for name in VALIDATOR_NAMES:
            candidate = directory / name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return candidate
    for name in VALIDATOR_NAMES:
        found = shutil.which(name)
        if found:
            return Path(found)
    return None


def validator_accepts(validator: Path, grammar: Path, label: str) -> tuple[bool, str]:
    """Ask `llama-gbnf-validator` about one label.

    It takes the candidate as a *file*, so each call writes one. The temporary
    file carries no trailing newline: the grammar does not admit one, and adding
    it would make every label fail for a reason that has nothing to do with the
    corpus.
    """
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fp:
        fp.write(label)
        temp_path = Path(fp.name)
    try:
        result = subprocess.run(
            [str(validator), str(grammar), str(temp_path)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    finally:
        temp_path.unlink(missing_ok=True)


def read_labels(path: Path) -> list[tuple[str, str]]:
    """`(row_id, target)` for every row in a JSONL artefact."""
    labels: list[tuple[str, str]] = []
    with open(path, encoding="utf-8") as fp:
        for line_no, line in enumerate(fp, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_no}: not valid JSON --- {exc}") from exc
            if "target" not in row:
                raise SystemExit(f"{path}:{line_no}: row has no 'target' field")
            labels.append((str(row.get("id", line_no)), row["target"]))
    return labels


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "files", nargs="*", type=Path, default=None, help="JSONL artefacts (default: all three)"
    )
    parser.add_argument("--grammar", type=Path, default=Path(GRAMMAR_PATH))
    parser.add_argument(
        "--no-llama", action="store_true", help="skip the llama-gbnf-validator cross-check"
    )
    args = parser.parse_args(argv)

    files = args.files or [p for p in DEFAULT_FILES]
    missing = [p for p in files if not p.is_file()]
    if missing:
        print("missing artefacts (run `python data/generate.py` first):", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        return 1

    grammar: Grammar = load_grammar(args.grammar)
    print(f"grammar: {args.grammar}")

    failures: list[tuple[str, str, str]] = []
    total = 0
    distinct: set[str] = set()

    for path in files:
        labels = read_labels(path)
        rejected = 0
        for row_id, label in labels:
            total += 1
            distinct.add(label)
            if not grammar.accepts(label):
                rejected += 1
                failures.append((str(path), row_id, label))
        status = "REJECTED " + str(rejected) if rejected else "all accepted"
        print(f"  {path.name:<28} {len(labels):>5} labels  {status}")

    print(f"\ndata/gbnf.py: {total} labels checked, {len(distinct)} distinct, "
          f"{len(failures)} rejected")

    if failures:
        print("\nrejected labels:", file=sys.stderr)
        for path, row_id, label in failures[:20]:
            print(f"  {path} {row_id}: {label}", file=sys.stderr)
        if len(failures) > 20:
            print(f"  ... and {len(failures) - 20} more", file=sys.stderr)
        return 1

    acceptors = ["data/gbnf.py"]
    if args.no_llama:
        print("\nllama-gbnf-validator: skipped (--no-llama)")
    else:
        validator = find_validator()
        if validator is None:
            print(
                "\nllama-gbnf-validator: NOT FOUND --- the gate rests on data/gbnf.py "
                "alone.\n"
                "  Build llama.cpp (or set LLAMA_CPP_DIR) and re-run to cross-check "
                "against\n"
                "  the parser that constrains decoding at inference time."
            )
        else:
            print(f"\nllama-gbnf-validator: {validator}")
            print(f"cross-checking {len(distinct)} distinct labels...")
            disagreements: list[tuple[str, str]] = []
            counts: Counter[bool] = Counter()
            for label in sorted(distinct):
                ok, output = validator_accepts(validator, args.grammar, label)
                counts[ok] += 1
                if not ok:
                    disagreements.append((label, output))
            print(f"  accepted {counts[True]}, rejected {counts[False]}")
            if disagreements:
                print(
                    "\nDISAGREEMENT: data/gbnf.py accepted labels that "
                    "llama-gbnf-validator rejects.\n"
                    "One of the two is wrong about the frozen grammar, and the "
                    "decoder-side one is\nthe one that will bite at inference time.",
                    file=sys.stderr,
                )
                for label, output in disagreements[:10]:
                    print(f"  {label}\n    {output}", file=sys.stderr)
                return 1
            acceptors.append(str(validator))

    print(f"\nGATE PASS --- {total} labels accepted by: {', '.join(acceptors)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
