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

**Two differences are conventions, not divergences, and are normalised explicitly.**
`llama-server`'s `/apply-template` omits the leading BOS piece, because llama.cpp adds
it at tokenisation time rather than in the prompt string; and Llama-3.2's template
calls `strftime_now`, so it renders *today's* date into the system turn while
`parity_hf.json` carries the date of the Kaggle run. Both are re-aligned before
comparison, each is only applied when it fully accounts for the difference, and every
normalisation applied is named in the report. Treating either as a parity failure
would have condemned a model that is in fact byte-identical -- llama-3.2-1b failed
this check on both counts, on a prompt that differs from its training rendering by
one date.

Models whose chat template refuses a system role have the system prompt folded into
the user turn (see `train/configs/*.yaml`, `supports_system_role`). The fold is
applied here too, from the same `system_role_folded` flag the notebook recorded, so
that this compares the prompt the model was actually trained on rather than a
different one that happens to pass.

A run needs a built `llama-server` and a multi-hundred-megabyte GGUF, so it cannot be
re-run from a clean checkout and cannot live in CI. `--report` therefore persists the
verdict to `results/gate3_parity.json` and re-renders `results/gate3_parity.md` from
it, so the finding survives as an artefact rather than as terminal scrollback. Records
are keyed by model and replaced in place, so re-running one model does not disturb the
others -- including the passing control, whose value is that it was measured under the
same harness as the failure.

Usage:
    python eval/check_parity_gguf.py h2o-danube3-500m-chat gguf/h2o-danube3-500m-chat-f16.gguf --report
    python eval/check_parity_gguf.py qwen2.5-0.5b-instruct gguf/qwen2.5-0.5b-instruct-Q4_K_M.gguf --report
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PARITY = REPO / "train" / "kaggle_out" / "parity_hf.json"
REPORT_JSON = REPO / "results" / "gate3_parity.json"
REPORT_MD = REPO / "results" / "gate3_parity.md"
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


TODAY_LINE = "Today Date:"


def _align(hf: str, cpp: str, bos: str) -> tuple[str, list[str]]:
    """Re-align cpp onto hf for the two known conventions; name what was applied.

    All-or-nothing: the rules are applied in sequence and kept only if together they
    make the two renderings identical. A normalisation that merely narrows a mismatch
    is discarded and the raw strings are compared, so no rule here can mask a real
    divergence. Llama-3.2 needs both rules at once, which is why they are not each
    guarded by their own equality test.
    """
    candidate, notes = cpp, []
    if bos and hf.startswith(bos) and not candidate.startswith(bos):
        candidate = bos + candidate
        notes.append("bos-prefix")
    if TODAY_LINE in hf and TODAY_LINE in candidate:
        def line(text: str) -> str:
            start = text.index(TODAY_LINE)
            end = text.find("\n", start)
            return text[start:end if end != -1 else len(text)]
        hf_line, cpp_line = line(hf), line(candidate)
        if hf_line != cpp_line:
            candidate = candidate.replace(cpp_line, hf_line, 1)
            notes.append("today-date")
    return (candidate, notes) if candidate == hf else (cpp, [])


def _piece(port: int, token: int) -> str:
    """The string one token id stands for, asked of the server rather than guessed."""
    try:
        return _post(port, "/detokenize", {"tokens": [token]})["content"]
    except Exception:
        return "?"


def _save(record: dict) -> None:
    """Replace this model's record in place; leave every other model's alone."""
    store = {"records": {}}
    if REPORT_JSON.is_file():
        store = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    store.setdefault("records", {})[record["model"]] = record
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(store, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    REPORT_MD.write_text(_render(store), encoding="utf-8")


def _render(store: dict) -> str:
    records = [store["records"][k] for k in sorted(store["records"])]
    lines = [
        "### Gate 3, llama.cpp side --- chat-template and tokenisation parity",
        "",
        "Generated by `eval/check_parity_gguf.py --report`; no number here is typed by",
        "hand. Each row pushes the ten committed audit prompts through a running",
        "`llama-server` on the named GGUF via `/apply-template` then `/tokenize`, and",
        "compares both the rendered text and the token IDs against",
        "`train/kaggle_out/parity_hf.json` --- the segmentation the adapter was trained",
        "under. Identical text with different IDs is the failure that matters: nothing",
        "raises, and the model is simply served on a segmentation it never saw.",
        "",
        "The *Normalised* column names the conventions re-aligned before comparison, each",
        "applied only where it accounts for the whole difference: `bos-prefix` because",
        "`/apply-template` omits the leading BOS piece that llama.cpp adds at tokenisation",
        "time, and `today-date` because Llama-3.2's template renders the current date into",
        "the system turn, which is not the date the adapter was trained on. Neither is a",
        "property of the model; a checker that called them failures would condemn a model",
        "whose prompt is otherwise byte-identical.",
        "",
        "| Model | GGUF | Prompts | System role folded | Normalised | Text identical | Token IDs identical | Gate 3 |",
        "| :--- | :--- | ---: | :--- | :--- | ---: | ---: | :--- |",
    ]
    for r in records:
        lines.append(
            f"| `{r['model']}` | `{r['gguf']}` | {r['n']} | "
            f"{'yes' if r['system_role_folded'] else 'no'} | "
            f"{', '.join(f'`{x}`' for x in r.get('normalised') or []) or 'none'} | "
            f"{r['text_identical']}/{r['n']} | {r['ids_identical']}/{r['n']} | "
            f"**{r['verdict']}** |")
    lines.append("")
    for r in records:
        div = r.get("first_divergence")
        if not div:
            continue
        lines += [
            f"#### `{r['model']}` --- where the two tokenisers part",
            "",
            f"Rendered text is identical on {r['text_identical']}/{r['n']} prompts, so the chat",
            "template itself is not at fault. The divergence is in segmentation, first",
            f"at token index {div['index']} of prompt `{div['prompt_id']}` "
            f"(lengths: HuggingFace {div['hf_len']}, llama.cpp {div['cpp_len']}).",
            "",
            "| Source | Token IDs from the divergence | Pieces |",
            "| :--- | :--- | :--- |",
            f"| HuggingFace (training) | `{div['hf_ids']}` | {div['hf_pieces']} |",
            f"| llama.cpp (serving) | `{div['cpp_ids']}` | {div['cpp_pieces']} |",
            "",
            "Both segmentations detokenise to the same string, which is why no error is",
            "raised anywhere in the pipeline.",
            "",
        ]
    failed = [r["model"] for r in records if r["verdict"] == "FAIL"]
    if failed:
        lines += [
            "**Consequence.** " + ", ".join(f"`{m}`" for m in failed) +
            " cannot carry a Surface-B result. A quantised accuracy or latency number for",
            "it would be measured under a tokenisation the adapter was not trained on, and",
            "would be attributed to quantisation. The reference-precision (Surface A)",
            "results are unaffected: they are produced by the same HuggingFace tokeniser",
            "the adapter was trained with.",
            "",
        ]
    dates = sorted(r["checked"] for r in records)
    lines.append(f"Runs recorded between {dates[0]} and {dates[-1]}.")
    return "\n".join(lines) + "\n"


def check(model: str, gguf: Path, port: int = 8891,
          report: bool = False) -> int:
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
    divergence = None
    applied: set[str] = set()
    try:
        _wait(port, process)
        # What the recorded first token stands for, asked of the server rather than
        # assumed from the model name. Empty unless it really is a BOS-like special.
        first = records[0]["token_ids"][0]
        bos = _piece(port, first)
        if not (bos.startswith("<") and bos.endswith(">")):
            bos = ""
        for record in records:
            if folded:
                messages = [{"role": "user",
                             "content": f"{system_prompt}\n\n{record['user_text']}"}]
            else:
                messages = [{"role": "system", "content": system_prompt},
                            {"role": "user", "content": record["user_text"]}]
            rendered = _post(port, "/apply-template", {"messages": messages})["prompt"]
            rendered, notes = _align(record["formatted"], rendered, bos)
            applied.update(notes)
            # BOS now lives in the prompt string on both sides, so it must not be
            # added a second time at tokenisation.
            tokens = _post(port, "/tokenize",
                           {"content": rendered, "add_special": False})["tokens"]
            if rendered != record["formatted"]:
                text_bad.append(record["id"])
            if tokens != record["token_ids"]:
                ids_bad.append((record["id"], record["token_ids"], tokens))
        if ids_bad:
            # Localise and name the divergence while the server is still up: only it
            # can say what a token id stands for, and "IDs differ" is not actionable.
            prompt_id, hf_ids, cpp_ids = ids_bad[0]
            index = next((i for i, (a, b) in enumerate(zip(hf_ids, cpp_ids)) if a != b),
                         min(len(hf_ids), len(cpp_ids)))
            hf_slice, cpp_slice = hf_ids[index:index + 3], cpp_ids[index:index + 3]
            divergence = {
                "prompt_id": prompt_id,
                "index": index,
                "hf_len": len(hf_ids), "cpp_len": len(cpp_ids),
                "hf_ids": hf_slice, "cpp_ids": cpp_slice,
                "hf_pieces": " + ".join(repr(_piece(port, t)) for t in hf_slice),
                "cpp_pieces": " + ".join(repr(_piece(port, t)) for t in cpp_slice),
            }
    finally:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()

    n = len(records)
    print(f"\nformatted text : {n - len(text_bad)}/{n} identical")
    print(f"token IDs      : {n - len(ids_bad)}/{n} identical")

    if divergence and not text_bad:
        # The interesting case: same string, different segmentation.
        print("\nText renders identically; the tokenisers segment it differently.")
        print(f"  first divergence at token index {divergence['index']} "
              f"of prompt {divergence['prompt_id']}")
        print(f"  lengths: hf={divergence['hf_len']} cpp={divergence['cpp_len']}")
        print(f"  hf  {divergence['hf_ids']}  {divergence['hf_pieces']}")
        print(f"  cpp {divergence['cpp_ids']}  {divergence['cpp_pieces']}")

    ok = not text_bad and not ids_bad
    print("\nGATE 3 (llama.cpp side):", "PASS" if ok else "FAIL")
    if not ok:
        print("A Surface-B number for this model would be measured under a tokenisation")
        print("the model was not trained on. Do not run Surface B until this is resolved.")

    if report:
        _save({
            "model": model,
            "gguf": gguf.name,
            "gguf_sha256": _sha256(gguf),
            "n": n,
            "system_role_folded": folded,
            "text_identical": n - len(text_bad),
            "ids_identical": n - len(ids_bad),
            "first_divergence": divergence,
            "normalised": sorted(applied),
            "verdict": "PASS" if ok else "FAIL",
            "checked": datetime.date.today().isoformat(),
        })
        print(f"\nwrote {REPORT_JSON.relative_to(REPO)} and {REPORT_MD.relative_to(REPO)}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model", help="model name as it appears in parity_hf.json")
    ap.add_argument("gguf", type=Path, help="path to the GGUF to check")
    ap.add_argument("--port", type=int, default=8891)
    ap.add_argument("--report", action="store_true",
                    help=f"record the verdict in {REPORT_JSON.name} and re-render "
                         f"{REPORT_MD.name}")
    args = ap.parse_args()
    return check(args.model, args.gguf, args.port, args.report)


if __name__ == "__main__":
    sys.exit(main())
