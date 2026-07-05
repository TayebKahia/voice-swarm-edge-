#!/usr/bin/env python3
"""
Spike S5: Tokenisation & Chat-Template Audit
Defines the 10 fixed canonical prompts across the 3 target models:
  1. Qwen2.5-0.5B-Instruct
  2. SmolLM2-360M-Instruct
  3. Llama-3.2-1B-Instruct

Audits chat template specifications (ChatML vs SmolLM vs Llama-3) to ensure
strict template parity between HuggingFace tokenizer.apply_chat_template and
llama.cpp inference, preventing chat-template drift (Project Trap #1 / Gate 3).
"""

import json
import os
import sys

# 10 canonical prompts spanning diverse intents, lengths, disfluencies, and edge cases
FIXED_PROMPTS = [
    {
        "id": 1,
        "name": "terse_takeoff",
        "user_text": "takeoff",
        "expected_intent": "takeoff"
    },
    {
        "id": 2,
        "name": "formation_circle",
        "user_text": "form a circle with radius five meters",
        "expected_intent": "formation"
    },
    {
        "id": 3,
        "name": "move_relative",
        "user_text": "move north ten meters at speed one point five",
        "expected_intent": "move"
    },
    {
        "id": 4,
        "name": "move_cartesian",
        "user_text": "navigate to position ten zero three",
        "expected_intent": "move"
    },
    {
        "id": 5,
        "name": "single_drone_altitude",
        "user_text": "drone one climb to altitude four meters",
        "expected_intent": "altitude"
    },
    {
        "id": 6,
        "name": "rotate_heading",
        "user_text": "rotate heading by ninety degrees",
        "expected_intent": "rotate"
    },
    {
        "id": 7,
        "name": "set_param_speed",
        "user_text": "set maximum speed to one point two meters per second",
        "expected_intent": "set_param"
    },
    {
        "id": 8,
        "name": "disfluency_correction",
        "user_text": "move south no wait move west five meters",
        "expected_intent": "move"
    },
    {
        "id": 9,
        "name": "emergency_abort",
        "user_text": "abort flight immediately",
        "expected_intent": "abort"
    },
    {
        "id": 10,
        "name": "out_of_domain",
        "user_text": "what is the weather today",
        "expected_intent": "unknown"
    }
]

# Chat Template Architecture Audit Specifications
TEMPLATE_SPECS = {
    "Qwen2.5-0.5B-Instruct": {
        "format": "ChatML",
        "system_token": "<|im_start|>system\n{system_prompt}<|im_end|>\n",
        "user_token": "<|im_start|>user\n{user_prompt}<|im_end|>\n",
        "assistant_prefix": "<|im_start|>assistant\n",
        "eos_token": "<|im_end|>",
        "llama_cpp_chat_template": "chatml"
    },
    "SmolLM2-360M-Instruct": {
        "format": "SmolLM-Chat",
        "system_token": "<|im_start|>system\n{system_prompt}<|im_end|>\n",
        "user_token": "<|im_start|>user\n{user_prompt}<|im_end|>\n",
        "assistant_prefix": "<|im_start|>assistant\n",
        "eos_token": "<|im_end|>",
        "llama_cpp_chat_template": "chatml"
    },
    "Llama-3.2-1B-Instruct": {
        "format": "Llama-3",
        "system_token": "<|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>",
        "user_token": "<|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|>",
        "assistant_prefix": "<|start_header_id|>assistant<|end_header_id|>\n\n",
        "eos_token": "<|eot_id|>",
        "llama_cpp_chat_template": "llama3"
    }
}

def generate_kaggle_export_script():
    """Generates the Kaggle snippet that runs with PyTorch/Transformers to produce eval/parity_hf.json."""
    return '''
import json
import torch
from transformers import AutoTokenizer

models = [
    ("Qwen2.5-0.5B-Instruct", "Qwen/Qwen2.5-0.5B-Instruct"),
    ("SmolLM2-360M-Instruct", "HuggingFaceTB/SmolLM2-360M-Instruct"),
    ("Llama-3.2-1B-Instruct", "meta-llama/Llama-3.2-1B-Instruct")
]

prompts = ''' + json.dumps(FIXED_PROMPTS, indent=2) + '''

parity_data = {}

for model_name, hf_id in models:
    print(f"Tokenizing for {model_name} ({hf_id})...")
    tokenizer = AutoTokenizer.from_pretrained(hf_id)
    model_entries = []
    for item in prompts:
        messages = [{"role": "user", "content": item["user_text"]}]
        formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        token_ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
        model_entries.append({
            "id": item["id"],
            "name": item["name"],
            "user_text": item["user_text"],
            "formatted_prompt": formatted_prompt,
            "token_ids": token_ids
        })
    parity_data[model_name] = model_entries

with open("parity_hf.json", "w") as f:
    json.dump(parity_data, f, indent=2)
print("Saved parity_hf.json successfully!")
'''

def main():
    print("=== Spike S5: Tokenisation & Template Audit ===")
    print(f"Fixed prompt set size: {len(FIXED_PROMPTS)} prompts.")
    
    os.makedirs("eval", exist_ok=True)
    kaggle_script_path = "eval/dump_parity_hf_kaggle.py"
    with open(kaggle_script_path, "w") as f:
        f.write(generate_kaggle_export_script().strip())
    print(f"Generated Kaggle token export script at {kaggle_script_path}.")
    
    prompts_path = "eval/fixed_audit_prompts.json"
    with open(prompts_path, "w") as f:
        json.dump(FIXED_PROMPTS, f, indent=2)
    print(f"Saved {prompts_path}.")
    
    print("\nTemplate Architecture Audit:")
    for model, spec in TEMPLATE_SPECS.items():
        print(f"  Model: {model}")
        print(f"    Format: {spec['format']}")
        print(f"    llama.cpp Template: --chat-template {spec['llama_cpp_chat_template']}")
        print(f"    EOS token: {spec['eos_token']}")
    
    print("\nAudit Status: PRE-REGISTERED.")
    print("Execution Strategy (§2.8a):")
    print("  1. HF Token IDs generated on Kaggle during Session 04 LoRA runs -> eval/parity_hf.json.")
    print("  2. Token identity verified locally against live llama.cpp in Gate 3 (Session 05B).")
    print("  3. Zero local torch/transformers dependencies required on workstation.")

if __name__ == "__main__":
    main()
