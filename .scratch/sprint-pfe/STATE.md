# STATE
Session: 01A (Mon 7 Sep, PRD D1)
Last updated: 2026-09-07T16:25:00+01:00

## Gates
Gate 1 schema        : PENDING (Session 01B)
Gate 2 leakage       : PENDING (Session 02B)
Gate 3 parity        : PENDING (Session 05B)
Gate 4 fsm           : PENDING (Session 08)
Gate 5 dataset frozen: PENDING (Session 03)
D1 Environment Gate  : GREEN (requirements.txt pinned, environment.yml exported)

## Artefacts
spikes/s0..s7 scripts       : 8 scripts authored in spikes/
spikes/reports/S0..S7.md    : 8 spike reports authored in spikes/reports/
                              - S3 GBNF Smoke: PASS (zero structural invalid emissions accepted)
                              - S4 PyFlyt Hover: PASS (5 drones, 50 Hz, RTF = 4.72x >= 1.0)
                              - S5 Template Audit: PRE-REGISTERED (10 fixed prompts locked, Kaggle script authored)
                              - S7 Preemption: PASS (abort 2.27 ms, fallback 11.26 ms vs 300 ms NFR-17 budget)
                              - S0, S1, S2, S6: Templates ready for human execution
requirements.txt            : PINNED (all dependencies pinned with ==, conda header updated)
environment.yml             : EXPORTED (conda env pfe_swarm)
.scratch/sprint-pfe/spec.md : AUTHORED (16-day sprint plan, cut ladder, milestones)
.scratch/sprint-pfe/issues/ : AUTHORED (26 issues filed, Issue 24 filed first)

## Decisions this session
- Python Environment: Conda env `pfe_swarm` (Python 3.11.15) at `/home/kahia-tayeb/miniconda3/envs/pfe_swarm` is active and pinned. No `.venv` created.
- Local GPU: `nvidia-smi` confirmed cannot communicate with driver; all LoRA fine-tuning and Surface-A eval will run on Kaggle in fp16 per roadmap §2.8a.
- PyTorch/Transformers policy: Zero local PyTorch/Transformers dependencies installed in `pfe_swarm`, adhering strictly to §0.5 and §2.8a.
- Preemption Architecture: In-process abort callback validated (2.27 ms); separate-process fallback validated (11.26 ms). Both comfortably beat NFR-17 (300 ms).
- Untracked contract files: `prd.md`, `docs/project/`, `IMPLEMENTATION_ROADMAP.md`, `START_SESSION.md` remain untracked per `.gitignore`. Author confirmed off-repo backup completed.
- Kaggle verification: Author confirmed account is phone-verified, securing notebook internet for Session 04 training.
- Duplicate PRD removal: Confirmed `docs/project/prd.md` is removed; root `prd.md` is sole contract.

## Blocked / needs human
- Autorisation de soutenance: Requested Sep 6, pending formal receipt (tracked in Issue 24).
- Hands-on microphone: Author to execute `spikes/s0_audio_bringup.py` and `spikes/s6_asr_accent_check.py`.
- Raspberry Pi: Pi 5 is currently off. When powered on, author to run `spikes/s1_llama_bench_pi.sh` and `spikes/s2_whisper_timing_pi.sh`.

## Next session starts with
Session 01B Task 1. Freeze `schema/` — inspect and salvage prior work in `schema/canon.py`, `schema/cmd.gbnf`, `schema/schema.py`, implement validators and adversarial tests, and run Gate 1 (`pytest schema/ -v`).
