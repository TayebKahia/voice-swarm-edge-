"""GATE 3 --- token-ID identity between HF and `llama.cpp`.

`prd.md`: "a mandatory gate after every conversion, not a diagnostic run when
something looks wrong." The failure it catches has no error message. If the chat
template tokenises differently in the two runtimes, the fine-tuned model is served a
prompt it was never trained on; it still answers, the JSON is still grammatical
because the GBNF guarantees that, and the accuracy is merely worse. It looks exactly
like a bad fine-tune or a quantisation problem, and both of those are expensive things
to go and investigate.

The two halves come from different machines by necessity. `transformers` is not
installed here and stays that way (§0.5), so the HF side is dumped on Kaggle into
`eval/parity_hf.json` --- formatted prompt text and token IDs for the ten fixed audit
prompts --- and committed. This test runs the `llama.cpp` side live and compares.

Two settings have to match the HF call or the comparison is meaningless:

* **no BOS.** The Kaggle side calls the tokenizer with `add_special_tokens=False`,
  because `apply_chat_template` has already emitted whatever special tokens the
  template wants. `llama.cpp` adds one from model metadata unless told otherwise, so
  `add_bos_token` is overridden to false. Without this every model mismatches by
  exactly one leading token, which looks like a catastrophic failure and is an
  artefact of the harness.
* **no escape processing.** Templated text contains real newlines. `llama-tokenize`
  interprets backslash escapes by default, which would rewrite the prompt before
  tokenising it.
"""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PARITY_JSON = REPO / "eval" / "parity_hf.json"
GGUF_DIR = REPO / "gguf"
LLAMA_TOKENIZE = Path.home() / "llama.cpp" / "build" / "bin" / "llama-tokenize"


def _load_parity() -> dict:
    if not PARITY_JSON.is_file():
        pytest.skip(f"{PARITY_JSON.relative_to(REPO)} not present --- "
                    "it is produced by train/kaggle_finetune.ipynb and committed")
    return json.loads(PARITY_JSON.read_text())


def _find_gguf(model: str) -> Path | None:
    """Any quantisation of `model`. Tokenisation does not depend on the weights."""
    candidates = sorted(GGUF_DIR.glob(f"{model}*.gguf"))
    return candidates[0] if candidates else None


def llama_cpp_token_ids(gguf: Path, text: str, tmp_path: Path) -> list[int]:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text(text, encoding="utf-8")
    completed = subprocess.run(
        [str(LLAMA_TOKENIZE), "-m", str(gguf), "-f", str(prompt_file),
         "--ids", "--no-escape",
         # Match transformers' add_special_tokens=False -- see the module docstring.
         # `--no-bos`, not `--override-kv tokenizer.ggml.add_bos_token=bool:false`:
         # the override is accepted silently and does NOT suppress the BOS, which
         # showed up as Llama-3.2 -- the one model whose template emits
         # <|begin_of_text|> itself -- mismatching on all ten prompts by exactly one
         # leading 128000, while Qwen and SmolLM2 passed.
         "--no-bos"],
        capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"llama-tokenize failed: {completed.stderr[-500:]}")
    for line in reversed(completed.stdout.splitlines()):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            return list(ast.literal_eval(stripped))
    raise RuntimeError(f"no token id list in output:\n{completed.stdout[-500:]}")


@pytest.fixture(scope="module")
def parity():
    return _load_parity()


def test_parity_file_covers_the_ten_fixed_prompts(parity):
    audit = json.loads((REPO / "eval" / "fixed_audit_prompts.json").read_text())
    expected = {p["id"] for p in audit["prompts"]}
    for model, records in parity["models"].items():
        assert {r["id"] for r in records} == expected, f"{model} is missing prompts"


def test_system_prompt_matches_the_committed_one(parity):
    # If Kaggle trained against a different system prompt than the one the runtime
    # will send, parity can pass on template mechanics and still be wrong.
    audit = json.loads((REPO / "eval" / "fixed_audit_prompts.json").read_text())
    assert parity["system_prompt"] == audit["system_prompt"]


@pytest.mark.slow
def test_token_ids_are_identical(parity, tmp_path):
    """GATE 3. Paste the failing IDs --- a diff of two token lists localises it."""
    if not LLAMA_TOKENIZE.is_file():
        pytest.skip(f"llama-tokenize not built at {LLAMA_TOKENIZE}")

    checked, mismatches, skipped = 0, [], []
    for model, records in parity["models"].items():
        gguf = _find_gguf(model)
        if gguf is None:
            skipped.append(model)
            continue
        for record in records:
            actual = llama_cpp_token_ids(gguf, record["formatted"], tmp_path)
            expected = record["token_ids"]
            checked += 1
            if actual != expected:
                mismatches.append(
                    f"\n{model} / prompt {record['id']} ({record['name']}):"
                    f"\n  hf        n={len(expected):3d}  {expected}"
                    f"\n  llama.cpp n={len(actual):3d}  {actual}")

    if skipped and not checked:
        pytest.skip(f"no GGUF found for {skipped} in {GGUF_DIR.relative_to(REPO)}")
    assert not mismatches, (
        f"GATE 3 RED --- {len(mismatches)}/{checked} prompts tokenise differently."
        + "".join(mismatches))
    assert checked, "no prompts were compared"
