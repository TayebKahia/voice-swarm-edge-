# Spike S2 Report: whisper.cpp Timing on Raspberry Pi 5

- **Date:** 2026-09-07
- **Target Platform:** Raspberry Pi 5 (Cortex-A76, 4 cores)
- **Status:** Pending Execution (Pi is powered off; user will execute `spikes/s2_whisper_timing_pi.sh`)

## Configuration
- `whisper.cpp` commit SHA: `[ENTER SHA]`
- Model: `tiny.en` Q5 quantization (`ggml-tiny.en-q5_1.bin`)
- Test stimulus: 3.0-second speech audio @ 16 kHz mono
- Threads: 3 cores pinned (`-t 3`)
- Sample count: $N = 20$ timed repetitions

## Timing Measurements
- **p50 (Median):** `[ENTER VALUE]` ms (Budget: $\le 1200$ ms)
- **p95:** `[ENTER VALUE]` ms
- **Min:** `[ENTER VALUE]` ms
- **Max:** `[ENTER VALUE]` ms
- **Mean $\pm$ Std:** `[ENTER VALUE]` ms

## Observations vs Table 6 Budget
- Does p50 meet the 1200 ms budget? `[Yes / No]`
- Peak RSS during inference: `[ENTER VALUE]` MB (Budget: $\le 300$ MB)
- Thermal impact over 20 runs:
