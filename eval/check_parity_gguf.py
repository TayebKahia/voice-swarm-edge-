#!/usr/bin/env python3
"""Gate 3, llama.cpp side: does a GGUF tokenise the audit prompts the way training did?

`eval/test_template_parity.py` checks the HuggingFace side against the committed
audit prompts. This checks the other half, which needs a running `llama-server` and
so cannot live in the test suite: it starts the server on a GGUF, pushes the ten
fixed audit prompts through `/apply-template` then `/tokenize`, and compares BOTH
the formatted text and the token IDs against `train/kaggle_out/parity_hf.json`.

**Why token IDs and not just text.** Two tokenisers can render byte-identical text
and still segment it differently -- SentencePiece merge ranking is not unique. The
model is trained on one segmentation and, if they differ, served on another. Nothing
errors; accuracy just degrades. That is the failure prd.md Sec. 10.1 calls this
project's highest-cost silent one, and comparing rendered text alone would miss it
entirely.

Models whose chat template refuses a system role have the system prompt folded into
the user turn (see `train/configs/*.yaml`, `supports_system_role`). The fold is
applied here too, from the same `system_role_folded` flag the notebook recorded, so
that this compares the prompt the model was actually trained on rather than a
different one that happens to pass.

Usage:
    python eval/check_parity_gguf.py h2o-danube3-500m-chat gguf/h2o-danube3-500m-chat-f16.gguf
    python eval/check_parity_gguf.py qwen2.5-0.5b-instruct gguf/qwen2.5-0.5b-instruct-Q4_K_M.gguf
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PARITY = REPO / "train" / "kaggle_out" / "parity_hf.json"
LLAMA_SERVER = Path.home() / "llama.cpp" / "build" / "bin" / "llama-server"


def _post(port: int, path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(request, timeout=120).read())


def _wait(port: int, process: subprocess.Popen, timeout: float = 180.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            raise SystemExit(f"llama-server exited early ({process.returncode})")
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=3).read()
            return
        except (urllib.error.URLError, OSError):
            time.sleep(2)
    raise SystemExit("llama-server did not become healthy")


def check(model: str, gguf: Path, port: int = 8891) -> int:
    parity = json.loads(PARITY.read_text(encoding="utf-8"))
    if model not in parity["models"]:
        raise SystemExit(f"{model} not in {PARITY.relative_to(REPO)}; "
                         f"have: {sorted(parity['models'])}")
    records = parity["models"][model]
    system_prompt = parity["system_prompt"]
    folded = parity.get("system_role_folded", {}).get(model, False)
    if not gguf.is_file():
        raise SystemExit(f"no such GGUF: {gguf}")
    if not LLAMA_SERVER.is_file():
        raise SystemExit(f"llama-server not built at {LLAMA_SERVER}")

    print(f"model   {model}")
    print(f"gguf    {gguf.relative_to(REPO) if gguf.is_relative_to(REPO) else gguf}")
    print(f"prompts {len(records)}  |  system role folded into user turn: {folded}")

    process = subprocess.Popen(
        [str(LLAMA_SERVER), "-m", str(gguf), "--port", str(port),
         "-c", "512", "-ngl", "0", "--no-webui"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    text_bad, ids_bad = [], []
    try:
        _wait(port, process)
        for record in records:
            if folded:
                messages = [{"role": "user",
                             "content": f"{system_prompt}\n\n{record['user_text']}"}]
            else:
                messages = [{"role": "system", "content": system_prompt},
                            {"role": "user", "content": record["user_text"]}]
            rendered = _post(port, "/apply-template", {"messages": messages})["prompt"]
            tokens = _post(port, "/tokenize",
                           {"content": rendered, "add_special": False})["tokens"]
            if rendered != record["formatted"]:
                text_bad.append(record["id"])
            if tokens != record["token_ids"]:
                ids_bad.append((record["id"], record["token_ids"], tokens))
    finally:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()

    n = len(records)
    print(f"\nformatted text : {n - len(text_bad)}/{n} identical")
    print(f"token IDs      : {n - len(ids_bad)}/{n} identical")

    if ids_bad and not text_bad:
        # The interesting case: same string, different segmentation. Localise it,
        # because "token IDs differ" is not actionable and "' dr'+'one' vs
        # ' dro'+'ne'" is.
        _, hf_ids, cpp_ids = ids_bad[0]
        index = next((i for i, (a, b) in enumerate(zip(hf_ids, cpp_ids)) if a != b), None)
        print("\nText renders identically; the tokenisers segment it differently.")
        print(f"  first divergence at token index {index}")
        print(f"  lengths: hf={len(hf_ids)} cpp={len(cpp_ids)}")
        if index is not None:
            print(f"  hf  {hf_ids[index:index + 3]}")
            print(f"  cpp {cpp_ids[index:index + 3]}")

    ok = not text_bad and not ids_bad
    print("\nGATE 3 (llama.cpp side):", "PASS" if ok else "FAIL")
    if not ok:
        print("A Surface-B number for this model would be measured under a tokenisation")
        print("the model was not trained on. Do not run Surface B until this is resolved.")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model", help="model name as it appears in parity_hf.json")
    ap.add_argument("gguf", type=Path, help="path to the GGUF to check")
    ap.add_argument("--port", type=int, default=8891)
    args = ap.parse_args()
    return check(args.model, args.gguf, args.port)


if __name__ == "__main__":
    sys.exit(main())
