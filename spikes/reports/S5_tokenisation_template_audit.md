# Spike S5 Report: Tokenisation & Chat-Template Audit

- **Date:** 2026-09-07
- **Owner:** Agent
- **Target Models:**
  1. `Qwen/Qwen2.5-0.5B-Instruct`
  2. `HuggingFaceTB/SmolLM2-360M-Instruct`
  3. `meta-llama/Llama-3.2-1B-Instruct`
- **Status:** PRE-REGISTERED / DEFERRED TO GATE 3 (§2.8a)

## Audit Objectives
1. Prevent **Chat-Template Drift (Project Trap #1)**: Mismatch between fine-tuning prompt formatting (`tokenizer.apply_chat_template`) and `llama.cpp` inference flags (`--chat-template`).
2. Adhere to **Hardware & Environment Constraint (§0.5 / §2.8a)**: `torch`/`transformers` are kept off workstation and execute on Kaggle.

## Fixed Audit Prompt Suite ($N=10$)
Defined in `eval/fixed_audit_prompts.json`:
1. `terse_takeoff` ("takeoff")
2. `formation_circle` ("form a circle with radius five meters")
3. `move_relative` ("move north ten meters at speed one point five")
4. `move_cartesian` ("navigate to position ten zero three")
5. `single_drone_altitude` ("drone one climb to altitude four meters")
6. `rotate_heading` ("rotate heading by ninety degrees")
7. `set_param_speed` ("set maximum speed to one point two meters per second")
8. `disfluency_correction` ("move south no wait move west five meters")
9. `emergency_abort` ("abort flight immediately")
10. `out_of_domain` ("what is the weather today")

## Pinned Message Formatting for Gate 3 Parity
To guarantee exact token-ID identity between fine-tuning and runtime, all training and evaluation prompts use the canonical two-turn message structure:
- **System Prompt:** `"You are a drone swarm command parser. Output only JSON matching schema."`
- **User Prompt:** The raw spoken/text command.

## Chat-Template Findings & Mappings
| Model | HF Chat Format | `llama.cpp` CLI Flag | Stop / EOS Token | Status |
|---|---|---|---|---|
| **Qwen2.5-0.5B** | ChatML (`<\|im_start\|>`) | `--chat-template chatml` | `<\|im_end\|>` | Verified (`<\|im_start\|>system\n...`) |
| **SmolLM2-360M** | SmolLM Chat (`<\|im_start\|>`) | `--chat-template chatml` | `<\|im_end\|>` | **Hypothesis** (Gate 3 to verify system token handling) |
| **Llama-3.2-1B** | Llama-3 (`<\|start_header_id\|>`) | `--chat-template llama3` | `<\|eot_id\|>` | Verified |

## Parity Verification Procedure (Gate 3)
1. **Kaggle Execution (Session 04):** `eval/dump_parity_hf_kaggle.py` runs alongside LoRA training, formatting with both system and user prompts, dumping exact token IDs to `eval/parity_hf.json`.
2. **Local Verification (Session 05B / Gate 3):** `eval/test_template_parity.py` asserts byte-for-byte token ID identity between `parity_hf.json` and local `llama-cli` tokenisation on the 10 fixed prompts.
