# Sprint Specification: Voice Swarm Edge (16-Day Plan)

## Overview
- **Project:** Edge-deployed voice-driven multi-UAV autonomous swarm interface (Dual Master + Ingénieur thesis).
- **Execution Window:** Monday 7 September 2026 to Monday 21 September 2026 (Dépôt).
- **Contract:** `prd.md` (root).

## Schedule & Sessions
| Session | Date | Focus | Major Gates / Deliverables |
|---|---|---|---|
| **01A** | Mon 7 Sep | Env, Spikes S0–S7, Tracker | Pinned env, 8 spike reports, tracker initialized |
| **01B** | Mon 7 Sep | Freeze `schema/` | **Gate 1** (`pytest schema/`), tag `schema-v1.0` |
| **02A** | Mon 7 Sep | Label-first Generation | `raw_pairs.jsonl`, 200 golden transcripts |
| **02B** | Tue 8 Sep | Augmentation & Splits | **Gate 2** (`data/check_leakage.py --strict`) |
| **03**  | Tue 8 Sep | Golden s1, Wake Corpus, Pass 1 | 200 s1 audio files, `annot_pass1.jsonl` sealed (**10-day fuse starts**), **Gate 5** |
| **04**  | Wed 9 Sep | s2, Harness, Kaggle LoRA | `results/exp0.csv`, `eval/bench.py`, launch LoRA x 3 on Kaggle |
| **05A** | Thu 10 Sep | Quantise 6 GGUF Artefacts | Q8_0 and Q4_K_M for 3 models, deploy to Pi |
| **05B** | Thu 10 Sep | Template Parity & Surface B | **Gate 3** (`test_template_parity.py`), launch Exp-1 |
| **06**  | Fri 11 Sep | s3, Grammar Ablation, Swarm Core | Table 19 ablation, NumPy vectorised Boids + APF clamp |
| **07**  | Sat 12 Sep | Statistics & Master Lock | McNemar tests, Figure 2, Tables 17–19, **Master results locked** |
| **08**  | Sun 13 Sep | PyFlyt, FSM, Bus | **Gate 4** (`pytest swarm/`), start Exp-4 (150 SIL trials) |
| **09**  | Mon 14 Sep | End-to-End Pipeline | Full pipeline with push-to-talk/live-mic, non-vocal reset, chase autorisation |
| **10**  | Tue 15 Sep | Branch A Preemption | 2-class wake word, sequence number preemption, start Exp-2 |
| **11**  | Wed 16 Sep | Exp-2 Analysis & Robustness | ROC operating points, latency breakdown, start Exp-3 |
| **12**  | Thu 17 Sep | Ingénieur Lock | Arcsine ANOVA on CRR, Exp-4 stats, **Ingénieur results locked** |
| **13**  | Fri 18 Sep | Annotation Pass 2 & Master Drafting | Pass 2 relabeling (**10-day fuse ends**), Master thesis Ch 4–5 |
| **14**  | Sat 19 Sep | Ingénieur Drafting & Demo Video | Table 21, record live demo video (offline, mic) |
| **15**  | Sun 20 Sep | Thesis Polish & Clean Clone Check | Full verification from clean clone, build PDFs |
| **16**  | Mon 21 Sep | Dépôt | Final submission with signed autorisation |

## Invariable Constraints & Precedence
1. `prd.md` is the canonical contract.
2. Single speaker (author) for golden set; noise mixed digitally from clean audio.
3. 48 kHz recording with offline 3:1 soxr VHQ resample to 16 kHz (never ALSA plug).
4. Completion-only loss for training; fp16 on Kaggle (T4/P100 hardware constraint documented in §2.8a).
5. Nearest-rank percentiles without interpolation; n_accuracy != n_latency (n_latency = 200).
6. Hard geometric clamp at integrator for swarm separation; zero collisions observed.

## Cut Ladder (Applied strictly in order if time/resource budget is breached)
1. Golden session 3 (60 files, Sep 11) dropped.
2. Exp-1 timed runs reduced from 200 to 120 per config.
3. PyFlyt simulation downgraded to NumPy-only SIL for Exp-4.
4. Table 21 replaced with prose paragraph.
*Never cut:* Grammar ablation (Table 19 / C1), Exp-0, Spikes S0–S7, either 10-day fuse or autorisation.
