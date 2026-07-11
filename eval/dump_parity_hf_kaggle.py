"""Dump HF token IDs for Gate 3 parity check (Session 05B).

Reads the SINGLE SOURCE OF TRUTH for audit prompts and system prompt from
eval/fixed_audit_prompts.json.  Writes eval/parity_hf.json containing the
formatted prompt text and token IDs for each model × prompt combination.

Runs ON KAGGLE where torch + transformers are available.  The workstation
side of Gate 3 (test_template_parity.py) compares this JSON against live
llama.cpp output — no torch needed locally.
"""

from __future__ import annotations

import json
from pathlib import Path
from transformers import AutoTokenizer

# ── Single source of truth ──────────────────────────────────────────────
PROMPTS_PATH = Path(__file__).parent / "fixed_audit_prompts.json"

with open(PROMPTS_PATH) as f:
    audit_data = json.load(f)

# System prompt lives in the same JSON so there is exactly one definition
SYSTEM_PROMPT: str = audit_data["system_prompt"]
PROMPTS: list[dict] = audit_data["prompts"]

# ── Models ──────────────────────────────────────────────────────────────
MODELS = [
    ("Qwen2.5-0.5B-Instruct", "Qwen/Qwen2.5-0.5B-Instruct"),
    ("SmolLM2-360M-Instruct", "HuggingFaceTB/SmolLM2-360M-Instruct"),
    ("Llama-3.2-1B-Instruct", "meta-llama/Llama-3.2-1B-Instruct"),
]

parity_data: dict[str, list[dict]] = {}

for model_name, hf_id in MODELS:
    print(f"Tokenizing for {model_name} ({hf_id})...")
    tokenizer = AutoTokenizer.from_pretrained(hf_id)
    model_entries = []
    for item in PROMPTS:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": item["user_text"]},
        ]
        formatted_prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
        token_ids = tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True,
        )
        model_entries.append({
            "id": item["id"],
            "name": item["name"],
            "user_text": item["user_text"],
            "formatted_prompt": formatted_prompt,
            "token_ids": token_ids,
        })
    parity_data[model_name] = model_entries

# Write to eval/ so S5:41's path expectation is met
OUTPUT_PATH = Path(__file__).parent / "parity_hf.json"
with open(OUTPUT_PATH, "w") as f:
    json.dump(parity_data, f, indent=2)
print(f"Saved {OUTPUT_PATH} successfully!")