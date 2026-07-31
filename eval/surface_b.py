#!/usr/bin/env python3
"""Surface B --- the quantised artefacts, measured through `llama.cpp` as deployed.

Surface A is the FP16 model under `transformers`, measured on Kaggle. Surface B is the
same model after merge, conversion and quantisation, decoded by `llama.cpp` under the
GBNF grammar. The difference between them is **contribution C3**: what quantisation
costs, isolated from what fine-tuning bought (Table 18).

**Why this runs on the workstation and not the Pi.** Exact match is a property of the
weights, the grammar and the prompt, not of the machine: greedy decoding under a fixed
grammar is deterministic, so the Pi would return the same strings after a much longer
wait. The Pi is for Exp-1, where latency, peak RSS and thermals *are* the measurement.

**Tokenisation is not re-derived here.** The prompt goes through `/apply-template` and
then `/tokenize` with `add_special=false`, which is the pipeline Gate 3 proved
identical to the Kaggle side token for token. Letting the server add specials on its
own re-opens exactly the defect Gate 3 caught: Llama-3.2's template already emits
`<|begin_of_text|>`, and a second one is a prompt the model never trained on.

**One slot, sequential requests.** §2.7 rests exact match on decoding being
deterministic. Parallel slots change batch composition and therefore the order of
floating-point reductions, which can flip a token on a near-tie --- rare, but it would
make the headline accuracy figure depend on how many requests happened to be in flight.
Slower and reproducible beats faster and approximately right.

Predictions are written per item as they are produced: a crash costs the current
artefact rather than the run, and Session 07's McNemar test needs the paired per-item
predictions, not the summary.

Usage:
    python eval/surface_b.py
    python eval/surface_b.py --no-grammar        # the Table 19 ablation
    python eval/surface_b.py --models qwen2.5-0.5b-instruct-Q4_K_M
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):  # `python eval/surface_b.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.metrics import score_predictions, summarise

REPO = Path(__file__).resolve().parent.parent
GGUF_DIR = REPO / "gguf"
RESULTS = REPO / "results"
PREDICTIONS = RESULTS / "surface_b_preds"
GRAMMAR_PATH = REPO / "schema" / "cmd.gbnf"
AUDIT = REPO / "eval" / "fixed_audit_prompts.json"
LLAMA_SERVER = Path.home() / "llama.cpp" / "build" / "bin" / "llama-server"

SPLITS = ("test_synth", "test_golden", "test_ood")
PORT = 8912
CONTEXT = 1024
THREADS = 4

#: Enough for the longest canonical command plus its closing brace. The grammar cannot
#: run away the way spike S3's unbounded idlist did, but a cap keeps one pathological
#: item from stalling a 590-item sweep --- and with `--no-grammar` there is no
#: structural guarantee at all, which is precisely when a model degenerates.
MAX_TOKENS = 96


def _post(path: str, payload: dict, timeout: float = 120.0) -> dict:
    request = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def _wait_for_server(process: subprocess.Popen, timeout: float = 180.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"llama-server exited early ({process.returncode})")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                if json.loads(r.read()).get("status") == "ok":
                    return
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            time.sleep(1.0)
    raise RuntimeError("llama-server did not become healthy")


def _load_split(name: str) -> list[dict]:
    path = REPO / "data" / f"{name}.jsonl"
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def predict(system_prompt: str, text: str, grammar: str | None) -> str:
    """One utterance through the deployed decode path."""
    templated = _post("/apply-template", {
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": text}],
    })["prompt"]
    # add_special=false mirrors transformers' add_special_tokens=False, which is what
    # Gate 3 verified. See the module docstring.
    tokens = _post("/tokenize", {"content": templated, "add_special": False})["tokens"]

    payload = {"prompt": tokens, "temperature": 0.0, "n_predict": MAX_TOKENS,
               "cache_prompt": False}
    if grammar is not None:
        payload["grammar"] = grammar
    return _post("/completion", payload)["content"].strip()


def _rescore(tag: str, model: str, quant: str, splits: Sequence[str],
             grammar: str | None) -> list[dict]:
    records = []
    for split in splits:
        path = PREDICTIONS / f"{tag}_{split}.jsonl"
        if not path.is_file():
            continue
        rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        predictions = score_predictions([r["raw"] for r in rows], [r["gold"] for r in rows])
        summary = summarise(predictions, ood=(split == "test_ood"))
        records.append({"model": model, "quant": quant,
                        "grammar": "on" if grammar else "off",
                        "split": split, **summary})
    return records


def run_artefact(gguf: Path, grammar: str | None, system_prompt: str,
                 splits: Sequence[str], resume: bool) -> list[dict]:
    """Start a server for one artefact, sweep every split, stop it again."""
    model, _, quant = gguf.stem.rpartition("-")
    tag = f"{gguf.stem}{'' if grammar else '_nogrammar'}"

    pending = [s for s in splits
               if not (resume and (PREDICTIONS / f"{tag}_{s}.jsonl").is_file())]
    if not pending:
        print(f"{gguf.stem}: already complete, skipping")
        return _rescore(tag, model, quant, splits, grammar)

    process = subprocess.Popen(
        [str(LLAMA_SERVER), "-m", str(gguf), "--port", str(PORT), "-t", str(THREADS),
         "-c", str(CONTEXT), "--parallel", "1", "--log-disable"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        _wait_for_server(process)
        for split in pending:
            rows = _load_split(split)
            started = time.monotonic()
            out = PREDICTIONS / f"{tag}_{split}.jsonl"
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("w", encoding="utf-8") as handle:
                for index, row in enumerate(rows, 1):
                    raw = predict(system_prompt, row["transcript"], grammar)
                    handle.write(json.dumps({"id": row["id"], "transcript": row["transcript"],
                                             "gold": row["target"], "raw": raw}) + "\n")
                    if index % 60 == 0 or index == len(rows):
                        rate = index / (time.monotonic() - started)
                        print(f"  {gguf.stem:38s} {split:12s} {index:4d}/{len(rows)} "
                              f"({rate:.1f}/s)", flush=True)
    finally:
        process.terminate()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()

    return _rescore(tag, model, quant, splits, grammar)


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--models", nargs="+", help="artefact stems; default every quantised one")
    parser.add_argument("--splits", nargs="+", default=list(SPLITS))
    parser.add_argument("--no-grammar", action="store_true",
                        help="Table 19's ablation: decode without the GBNF constraint")
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--fresh", action="store_true", help="ignore existing predictions")
    args = parser.parse_args(argv)

    if not LLAMA_SERVER.is_file():
        raise SystemExit(f"llama-server not built at {LLAMA_SERVER}")

    artefacts = sorted(p for p in GGUF_DIR.glob("*.gguf") if "f16" not in p.stem)
    if args.models:
        wanted = set(args.models)
        artefacts = [p for p in artefacts if p.stem in wanted]
    if not artefacts:
        raise SystemExit(f"no quantised artefacts in {GGUF_DIR} -- run train/quantise.py")

    grammar = None if args.no_grammar else GRAMMAR_PATH.read_text()
    system_prompt = json.loads(AUDIT.read_text())["system_prompt"]
    csv_path = args.csv or (RESULTS / ("surface_b_nogrammar.csv" if args.no_grammar
                                       else "surface_b.csv"))

    print(f"artefacts : {len(artefacts)}")
    print(f"grammar   : {'OFF (Table 19 ablation)' if args.no_grammar else 'ON'}")
    print(f"splits    : {', '.join(args.splits)}\n")

    records = []
    for gguf in artefacts:
        records += run_artefact(gguf, grammar, system_prompt, args.splits, not args.fresh)

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["model", "quant", "grammar", "split", "n", "exact_match", "intent_macro_f1",
              "slot_micro_f1", "safe_failure_rate", "schema_validity", "false_command_rate"]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)

    print(f"\nwrote {csv_path.relative_to(REPO)}  ({len(records)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
