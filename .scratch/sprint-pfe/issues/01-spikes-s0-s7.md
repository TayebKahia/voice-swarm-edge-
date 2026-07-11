# Issue 01: spikes-s0-s7

Status: resolved
Blocked by: —
Claimed-by: antigravity
Closed-by: antigravity
Session: 01A
Closes: 8 spike reports

## Summary
Execute and script the eight engineering spikes (S0–S7) per PRD Table 22 to establish hardware baselines, audio quality, and architectural feasibility before building downstream components.

## Deliverables & Status
1. **S0 (Audio Bring-up):** Verified and completed by author. Silence RMS noise floor: -64.47 dBFS (optimal, well below -50 dBFS pass threshold); speech peak: -36.06 dBFS; SNR: 28.4 dB. Offline 3:1 soxr VHQ resample confirmed. **PASS** (`spikes/reports/S0_audio_bringup.md`).
2. **S1 (llama.cpp Throughput + Thermals):** Executed on Raspberry Pi 5. At allocated `-t 3`: Qwen2.5-0.5B Q4_K_M achieved 20.97 tok/s (meets >= 20 tok/s target); Q5_K_M achieved 18.16 tok/s (**FAILS** >= 20 tok/s). Peak compile temp 85.1 °C with soft throttle confirms need for Active Cooler. **PROVISIONAL PASS** (Q4_K_M only) (`spikes/reports/S1_llama_throughput_thermals.md`).
3. **S2 (whisper.cpp Timing):** Executed on Raspberry Pi 5 with ggml-tiny.en-q5_1.bin. Under allocated `-t 3` budget, p50 was 1959.57 ms, p95 was 2014.28 ms (**FAILS** <= 1200 ms budget). Estimated E2E pipeline at 2.4 GHz is 2,591–2,984 ms, which fails NFR-2 (<= 2500 ms). **PROVISIONAL / GATED** (`spikes/reports/S2_whisper_timing.md`).
4. **S3 (GBNF Smoke):** Tested end-to-end via `spikes/s3_gbnf_smoke.py` and live on Pi 5 with `llama-cli --grammar-file`. Structural constraints compiled, but live sampling revealed unbounded `idlist` looping on hardware. **PARTIAL** (`spikes/reports/S3_gbnf_smoke.md`).
5. **S4 (PyFlyt Swarm Simulation):** Tested end-to-end via `spikes/s4_pyflyt_hover.py`. 5 quadx drones at 50 Hz control / 250 Hz physics achieved **4.72x real-time factor**. **PASS** (`spikes/reports/S4_pyflyt_simulation.md`).
6. **S5 (Tokenisation & Template Audit):** 10 fixed prompts defined in `eval/fixed_audit_prompts.json`. Kaggle export script generated (`eval/dump_parity_hf_kaggle.py`). **DEFERRED / PRE-REGISTERED FOR GATE 3** (`spikes/reports/S5_tokenisation_template_audit.md`).
   - *Risk logged*: HF transformers vs llama.cpp tokenization/chat-template discrepancy could silently corrupt JSON generation if unconstrained.
   - *Mitigation*: Layer 1 GBNF grammar constraints guarantee structural compliance at decode time; full cross-runtime parity audit runs at Gate 3 upon GGUF export.
7. **S6 (ASR Accent Check):** Executed by human author on 20 typical drone-swarm commands. Micro WER: **8.89%** (macro 14.00%) with tiny.en (passing <= 20% target); zero deletions (D=0); base.en + domain prompt achieved 9.00% WER. Architectural decision: deploy tiny.en with domain-primed prompt / GBNF constraints. **PASS** (`spikes/reports/S6_asr_accent_check.md`).
8. **S7 (Preemption Capability):** Evaluated via `spikes/s7_preemption.py`. In-process abort caught in 2.27 ms; fallback subprocess termination in 0.58 ms + respawn in 10.68 ms (total 11.26 ms vs 300 ms NFR-17 budget). Live in-flight C++ preemption deferred to Exp-2. **DEFERRED / ARCHITECTURE ONLY** (`spikes/reports/S7_preemption_capability.md`).

## Comments
- 2026-09-07 (Session 01A): S3, S4, S5, S7 completed by agent. S0, S1, S2, S6 scripted with templates ready for human execution.
- 2026-09-08 (Session 01A/01B): S0 audio bring-up verified (-64.47 dBFS noise floor). S6 completed (8.89% micro WER on tiny.en). S1 (Q4_K_M pass, Q5_K_M fail at -t 3) and S2 (2,014 ms p95 at -t 3 fails 1,200 ms budget) recorded. S3 GBNF unbounded idlist defect recorded. S5 and S7 deferred. Issue 01 reconciled with STATE.md.


