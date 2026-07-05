# Issue 01: spikes-s0-s7

Status: ready-for-human
Blocked by: —
Session: 01A
Closes: 8 spike reports

## Summary
Execute and script the eight engineering spikes (S0–S7) per PRD Table 22 to establish hardware baselines, audio quality, and architectural feasibility before building downstream components.

## Deliverables & Status
1. **S0 (Audio Bring-up):** Script `spikes/s0_audio_bringup.py` and report template `spikes/reports/S0_audio_bringup.md` created. Human hands on mic required. Target: Noise floor $\le -50$ dBFS, speech $\sim -20$ dBFS.
2. **S1 (llama.cpp Throughput + Thermals):** Script `spikes/s1_llama_bench_pi.sh` and report template `spikes/reports/S1_llama_throughput_thermals.md` created. Run on Pi 5 when powered on.
3. **S2 (whisper.cpp Timing):** Script `spikes/s2_whisper_timing_pi.sh` and report template `spikes/reports/S2_whisper_timing.md` created. Evaluates `tiny.en` Q5 on 3s clip over 20 runs (-t 3) vs 1200 ms budget on Pi 5.
4. **S3 (GBNF Smoke):** Tested end-to-end via `spikes/s3_gbnf_smoke.py`. 20 valid accepted, 20 structurally adversarial rejected. **PASS** (`spikes/reports/S3_gbnf_smoke.md`).
5. **S4 (PyFlyt Swarm Simulation):** Tested end-to-end via `spikes/s4_pyflyt_hover.py`. 5 quadx drones at 50 Hz control / 250 Hz physics achieved **4.72x real-time factor**. **PASS** (`spikes/reports/S4_pyflyt_simulation.md`).
6. **S5 (Tokenisation & Template Audit):** 10 fixed prompts defined in `eval/fixed_audit_prompts.json`. Kaggle export script generated (`eval/dump_parity_hf_kaggle.py`). Pre-registered for Gate 3 (§2.8a). **PASS / PRE-REGISTERED** (`spikes/reports/S5_tokenisation_template_audit.md`).
7. **S6 (ASR Accent Check):** Script `spikes/s6_asr_accent_check.py` and report template `spikes/reports/S6_asr_accent_check.md` created. Human hands on mic required.
8. **S7 (Preemption Capability):** Evaluated via `spikes/s7_preemption.py`. In-process abort caught in 2.27 ms; fallback subprocess termination in 0.58 ms + respawn in 10.68 ms (total 11.26 ms vs 300 ms NFR-17 budget). **PASS** (`spikes/reports/S7_preemption_capability.md`).

## Comments
- 2026-09-07 (Session 01A): S3, S4, S5, S7 completed by agent. S0, S1, S2, S6 scripted with templates ready for human execution (S0/S6 with microphone, S1/S2 on Pi 5 when powered on).
