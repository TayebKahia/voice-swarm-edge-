import json
import torch
from transformers import AutoTokenizer

models = [
    ("Qwen2.5-0.5B-Instruct", "Qwen/Qwen2.5-0.5B-Instruct"),
    ("SmolLM2-360M-Instruct", "HuggingFaceTB/SmolLM2-360M-Instruct"),
    ("Llama-3.2-1B-Instruct", "meta-llama/Llama-3.2-1B-Instruct")
]

prompts = [
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

parity_data = {}

SYSTEM_PROMPT = "You are a drone swarm command parser. Output only JSON matching schema."

for model_name, hf_id in models:
    print(f"Tokenizing for {model_name} ({hf_id})...")
    tokenizer = AutoTokenizer.from_pretrained(hf_id)
    model_entries = []
    for item in prompts:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": item["user_text"]},
        ]
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