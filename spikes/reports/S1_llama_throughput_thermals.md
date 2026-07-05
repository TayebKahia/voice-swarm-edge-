# Spike S1 Report: llama.cpp Throughput & Thermals on Raspberry Pi 5

- **Date:** 2026-09-07
- **Target Platform:** Raspberry Pi 5 (Cortex-A76, 4 cores, 8GB RAM)
- **Status:** Pending Execution (Pi is powered off; user will execute `spikes/s1_llama_bench_pi.sh`)

## Configuration
- `llama.cpp` commit SHA: `[ENTER SHA]`
- Compiler flags: `cmake -B build -DGGML_NATIVE=ON -DGGML_FAST=ON`
- Thread pinning: 4 threads (`-t 4`)

## Results: 6 Configurations (Tokens/sec)
Prompt eval (pp=64) and text generation (tg=32):

| Model | Quantization | Prompt Eval (tok/s) | Eval Decode (tok/s) | Peak RSS |
|---|---|---|---|---|
| Qwen2.5-0.5B | Q8_0 | `[VALUE]` | `[VALUE]` | `[VALUE]` |
| Qwen2.5-0.5B | Q4_K_M | `[VALUE]` | `[VALUE]` | `[VALUE]` |
| SmolLM2-360M | Q8_0 | `[VALUE]` | `[VALUE]` | `[VALUE]` |
| SmolLM2-360M | Q4_K_M | `[VALUE]` | `[VALUE]` | `[VALUE]` |
| Llama-3.2-1B | Q8_0 | `[VALUE]` | `[VALUE]` | `[VALUE]` |
| Llama-3.2-1B | Q4_K_M | `[VALUE]` | `[VALUE]` | `[VALUE]` |

## Thermal Soak (10 Minutes)
- Baseline Idle Temp: `[ENTER VALUE]` °C
- Peak Load Temp: `[ENTER VALUE]` °C
- `vcgencmd get_throttled` code: `[ENTER VALUE]` (Target: `0x0` - no thermal throttling)
- Available RAM headroom (`free -h`): `[ENTER VALUE]`

## Verdict
- Throughput feasibility vs NFR-2 (decode latency budget):
- Thermal stability without active fan / with active fan:
