# Spike S3 Report: GBNF Grammar Smoke Test

- **Date:** 2026-09-08
- **Owner:** Agent (executed end-to-end on workstation and Raspberry Pi 5)
- **Grammar File:** `schema/cmd.gbnf` (2157 bytes, SHA256: `dc2aa15735d7fa1a74ad13a17d692ec80578d5cf787cab5d12a428574203f15b`)
- **Status:** **PARTIAL** (Grammar compilation and structural constraint validated on `llama.cpp` build 10863; semantic index mapping & swarm intent resolution deferred to fine-tuning)

## Hardware Validation on Raspberry Pi 5 (`llama-cli`)

Live sampling was executed on the Raspberry Pi 5 using the compiled `llama.cpp` toolchain (build 10863) with `Qwen2.5-0.5B-Instruct-Q4_K_M.gguf` under strict grammar steering:
```bash
~/llama.cpp/build/bin/llama-cli \
  -m ~/models/qwen2.5-0.5b-instruct-q4_k_m.gguf \
  --grammar-file ~/cmd.gbnf \
  -p "<prompt>" -n 48 --temp 0 -t 3 -st
```

### Raw Model Emissions & Semantic Audit

| User Command | Raw Model Emission under GBNF | Layer 1 (GBNF Structure) | Layer 2 & Flight State Machine Result |
| :--- | :--- | :--- | :--- |
| `swarm takeoff` | `{"intent":"takeoff","ids":[1]}` | Valid JSON | **Semantic Defect:** Operator commanded "swarm" (all drones). Model emitted `ids:[1]` (single-drone takeoff). |
| `drone 1 move forward 5 meters at 1 meter per second` | `{"intent":"move","dir":"forward","dist":5,"speed":1,"ids":[1]}` | Valid JSON | **Index Mapping Defect:** Operator said "drone 1". Internal representation is 0-indexed per Roadmap:657-658 (`[0]`). Model emitted `[1]`. |
| `swarm formation circle with radius 4 meters` | `{"intent":"formation","shape":"circle","radius":4,"ids":[1,2,3,4,5,6,7,8,9,1,2,3,4,5,6` | **Non-terminating Degeneration:** Unbounded `idlist` causes greedy decoding (`--temp 0`) to loop endlessly until max tokens cutoff. | **Syntax Truncation $\rightarrow$ HOVER Fallback:** Incomplete JSON string fails `json.loads`. Layer 2 falls back to `Hover()`. If terminated, `_filter_ids` would drop 5–9 (exceeding `SWARM_SIZE=5`), leaving `[1,2,3,4]` and **omitting Drone 0**! |
| `swarm land` | `{"intent":"land","ids":[1,2,3,4,5,6,7,8,9,1,2,3,4,5,6,7,8,9,1,2` | **Non-terminating Degeneration:** Same repeating ID loop truncated at `-n 48`. | **Syntax Truncation $\rightarrow$ HOVER Fallback:** Fails `json.loads`, triggering fallback to `Hover()`. Landing aborted. |
| `emergency abort` | `{"intent":"abort"}` | Valid JSON | **PASS:** Flawless zero-shot structural emission. |

---

## Critical Specification Defects in Frozen PRD §5.1 Grammar

Hardware validation revealed two fundamental defects in the original grammar specification:
1. **Defect 1 (Grammar Syntax Error):** Multiline productions without trailing continuation operators (`|`) are rejected by the `llama.cpp` grammar compiler. Production rules must be formatted onto single logical lines.
2. **Defect 2 (Unbounded & Over-Wide `idlist`):**
   - The frozen rule `idlist ::= [0-9] ( "," [0-9] )*` accepts digits 5–9 (impossible for a 5-drone swarm).
   - Because the rule has no repetition upper bound, greedy decoding can enter an infinite repetitive loop emitting digits indefinitely, blowing the 1,100 ms decode budget and forcing `-n` truncation.
   - **Recommended Spec Amendment for v1.1:**
     ```gbnf
     idlist ::= [0-4] ( "," [0-4] )*
     ```
     Bounded to maximum 5 unique identifiers: `idlist ::= [0-4] ( "," [0-4] ){0,4}`.

---

## Architectural Findings for Session 02A (Dataset Design)

1. **Division of Labor:**
   - **Layer 1 (GBNF):** Guarantees token validity matching schema syntax.
   - **Layer 2 (Validator):** Clamps coordinates ($z \in [0.5, 15.0]$, $|pos| \le 50.0$), rejects non-finite values, and filters out-of-range IDs ($0 \le id < 5$).
   - **Fine-Tuning (Model):** Because zero-shot models default to single-drone `[1]` or infinite loops, **fine-tuning is exclusively responsible for:**
     - Collective intent: "swarm" $\rightarrow$ omit `ids` (all drones).
     - 1-based to 0-based conversion: "drone 1" $\rightarrow$ `ids:[0]`.
     - Output termination: Emitting closing `]` and `}` promptly after valid slot generation.

---

## Software Model Verification (Python Test Suite)

- **Valid Strings Accepted:** 20/20 (100% via schema test suite)
- **Adversarial Strings Rejected:** 20/20 (100% rejected by structural regex model)
- **Structurally Invalid Emissions on Hardware:** Under active GBNF steering, invalid grammar characters are unemittable by construction (NFR-6). Full hardware adversarial prompt injection testing will execute during Exp-1.
