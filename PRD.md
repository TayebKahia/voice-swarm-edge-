# Voice-Control for Drone Swarms via Small Language Models
## Product Requirements Document — Lean 4-Week Edition (v2.0)

| | |
|---|---|
| **Student** | Tayeb Kahia |
| **Supervisor** | Prof. Belkacem Khaldi |
| **Institution** | École Supérieure en Informatique — Sidi Bel Abbès · Second Cycle · IASD |
| **Year** | 2025/2026 |
| **Version** | 2.0 — supersedes the 16-week "Reflex-Cortex" PRD v1.0 |
| **Execution window** | **4 weeks** |
| **Status** | Pending supervisor acknowledgement of reduced scope (see §12, R-0) |

**Change summary vs. v1.0.** MARL Phase 2 removed in full (MAPPO, GATv2, PettingZoo, curriculum, reward
ablation, Exp-5). Model set changed from `Qwen2.5-0.5B + TinyBERT + MiniLM` to **three generative SLMs**
at 0.36 B / 0.5 B / 1.2 B, making the central comparison task-identical and therefore valid. Timeline
16 weeks → 4 weeks. Zenoh deferred to a swappable command-bus abstraction. Physics simulation moved
off-device from Day 1. Wake-word scope reduced from 5 hand-recorded keyword classes to 1 synthetically
trained keyword. GPT-4o mini dropped as incompatible with the offline requirement. Command schema
extended with `ids` (per-drone addressing) and `unknown` (out-of-domain), both of which were unsatisfiable
gaps in v1.0. Full rationale in [`docs/01_feasibility_audit.md`](docs/01_feasibility_audit.md).

---

## 1. Objective and contribution claim

**One sentence.** Demonstrate that a fine-tuned, grammar-constrained Small Language Model can run
entirely offline on a Raspberry Pi 5 CPU, convert spoken natural-language commands into validated
structured swarm primitives in under 2.5 s, and drive a coordinated 5-drone simulated formation — and
quantify the accuracy/latency/memory trade-off across three model scales.

**Four contributions, each measurable within the window:**

| # | Contribution | Evidence |
|---|---|---|
| C1 | **Controlled multi-scale SLM benchmark on ARM64.** Three generative SLMs (0.36 B / 0.5 B / 1.2 B) × two quantisations, identical data and recipe, evaluated on the deployed quantised artefact. | Table 1, Figure 1 (Pareto) |
| C2 | **Grammar-constrained structured decoding as a safety mechanism.** GBNF removes syntactic failure by construction; a two-layer grammar + semantic validator removes physically-invalid commands. Quantified against grammar-off. | Table 3 |
| C3 | **Quantisation cost at sub-1B scale.** Q8_0 vs Q4_K_M accuracy delta — the finding that the Q4 memory saving does not buy meaningful latency at this scale. | Table 2 |
| C4 | **Full offline voice→swarm pipeline with a measured sub-150 ms safety reflex** and a published, reproducible dataset. | Table 4, `DATASET_CARD.md` |

**What this is not.** No physical flight. No battery or airborne power integration. No reinforcement
learning. No vision. English only. These are stated as scope, not discovered as failures (§11).

---

## 2. Research questions

Narrowed from v1.0 so that each is fully answerable by a named experiment.

- **RQ1 — Model feasibility.** How do intent accuracy, slot accuracy, exact-match, inference latency, and
  memory footprint trade off across generative SLMs of 0.36 B–1.2 B parameters, fine-tuned for drone-swarm
  command parsing and quantised for CPU-only execution on a Raspberry Pi 5? → **Exp-1**
- **RQ2 — Pipeline latency.** Can a fully offline pipeline (wake-word + VAD + STT + grammar-constrained
  SLM + validator + controller) meet a p95 budget compatible with interactive swarm control, and how is
  that budget distributed across stages? → **Exp-2, Exp-3**
- **RQ3 — Acoustic robustness.** How do command recognition rate and word error rate degrade as SNR falls
  from clean to 5 dB under propeller-type noise, and does the system degrade *safely* (toward `unknown`)
  rather than *wrongly*? → **Exp-3**

RQ3 in v1.0 also covered formation accuracy under noise; that coupling is removed. Formation quality is
now measured independently (**Exp-4**) because confounding controller performance with acoustic
degradation makes neither interpretable.

---

## 3. System architecture

```
 ┌────────────────────── RASPBERRY PI 5 (offline, mains-powered) ──────────────────────┐
 │                                                                                     │
 │  USB mic ──► ring buffer (16 kHz mono PCM)                                          │
 │                  │                                                                  │
 │     ┌────────────┴────────────┐                                                     │
 │     │                         │                                                     │
 │  BRANCH A: REFLEX          BRANCH B: CORTEX                                         │
 │  target p95 < 150 ms       target p95 < 2.5 s (from end-of-speech)                   │
 │     │                         │                                                     │
 │  openWakeWord             Silero VAD ──► whisper.cpp tiny.en Q5                     │
 │  "abort" (1 kw)            (endpointing)         │                                  │
 │     │                                            ▼                                  │
 │     │                                   Fine-tuned SLM (GGUF, llama.cpp, -t 3)      │
 │     │                                   + GBNF grammar  + cached prompt prefix      │
 │     │                                            │                                  │
 │     │                                            ▼                                  │
 │     │                                   Pydantic semantic validator                 │
 │     │                                   (required slots · clamp · ids · → HOVER)     │
 │     │                                            │                                  │
 │     └──────────► PREEMPT ──────────────────► Command Bus (UDP/JSON, swappable) ◄─────┤
 │                                                  │                                  │
 └──────────────────────────────────────────────────┼──────────────────────────────────┘
                                                    │  (Networked-SIL, Wi-Fi)
 ┌──────────────────────── WORKSTATION ─────────────┼──────────────────────────────────┐
 │                                                  ▼                                  │
 │   State machine ──► Swarm controller @ 50 Hz ──► SwarmEnv (PyFlyt │ NumPy)           │
 │                     Boids · formation slots · APF separation · PID nav               │
 │                     N = 5 drones                                                    │
 └─────────────────────────────────────────────────────────────────────────────────────┘
```

**Three architectural decisions that differ from v1.0 and why:**

1. **Physics runs off-device from Day 1.** The claim under test is *"perception and language understanding
   fit on the edge device"* — not *"a PyBullet physics engine fits on the edge device."* Co-locating them
   contends for cores and makes latency measurements irreproducible. v1.0 already defined Networked-SIL;
   it is promoted from a Week-10 activity to the primary configuration.
2. **Command Bus, not Zenoh.** A ~40-line UDP/JSON transport behind an abstract interface. Zenoh's
   peer-to-peer mesh is the right *eventual* answer and remains a one-file swap; adopting a distributed
   middleware inside a 4-week window buys a whole failure class for no measurable result.
3. **The prompt prefix is cached and the schema is not in the prompt.** Fine-tuning is what removes the
   need to describe the schema at inference time. Combined with KV-cache reuse of any static prefix, this
   cuts per-command prefill from ~290 tokens to ~15 — the difference between meeting and missing the
   latency target (audit §C-1).

**Latency budget (targets; replaced by measured p95 in Week 2):**

| Stage | Target p95 |
|---|---|
| VAD endpointing | 500 ms |
| STT (`whisper.cpp tiny.en` Q5) | 1,200 ms |
| SLM prefill (cached prefix) | 250 ms |
| SLM decode (~22 tok, null-omitting schema) | 1,100 ms |
| Validate + dispatch | 50 ms |
| **E2E from end-of-speech (headline)** | **≤ 2,500 ms** |
| E2E from start-of-speech (3 s utterance) | ≤ 5,500 ms |
| **Branch A reflex (`abort`)** | **≤ 150 ms** |

Both anchors are reported. Reporting only end-of-speech looks evasive; reporting only start-of-speech
penalises the system for the length of the human's sentence.

---

## 4. Command schema

Frozen as **v1.0 on Day 1**. Full specification, GBNF grammar, and validator rules in
[`docs/02_dataset_plan.md`](docs/02_dataset_plan.md) §7. Summary:

- **10 intents:** `formation`, `move`, `altitude`, `takeoff`, `land`, `hover`, `abort`, `rotate`,
  `set_param`, `unknown`.
- **Wire format:** single-line JSON, fixed key order, **null fields omitted entirely** (~18 tokens
  typical vs ~40 for v1.0's always-emit-nulls schema — roughly one second of decode time per command).
- **Per-drone addressing** via `ids` (absent ⇒ all drones). Required by the brief; absent from v1.0.
- **`unknown` intent** for out-of-domain input. Without it, a grammar that only permits flight commands
  *forces* a flight command out of arbitrary speech — a safety defect, not a gap.
- **Two enforcement layers:** GBNF guarantees structure (and bounds numeric *digit count*); the Pydantic
  validator guarantees meaning (required-slot matrix, physical-envelope clamping, `ids` bounds). Every
  failure path resolves to `HOVER` and a structured log line. Never to a movement command.

---

## 5. Functional requirements

| ID | Requirement | Verification |
|---|---|---|
| **FR-1** | Publish a reproducible dataset: ~2,400 synthetic text–JSON pairs (label-first generation), ~200-utterance human-spoken golden set across 3–4 speakers, ~150 OOD examples, wake-word corpus, and a dataset card. Splits assigned by **template family**, not by row. | `DATASET_CARD.md`; split-leakage check script |
| **FR-2** | Fine-tune **three** SLMs (Qwen2.5-0.5B, SmolLM2-360M, Llama-3.2-1B) with an identical LoRA recipe, data, and seed. Completion-only loss. | 3 adapters + training logs |
| **FR-3** | Export each to GGUF at **Q8_0 and Q4_K_M** (6 artefacts) and verify HF↔llama.cpp output parity on 10 fixed prompts. | `test_template_parity.py` green |
| **FR-4** | Constrain all generative inference with the GBNF grammar; validate all output through the Pydantic semantic validator. | `test_grammar.py` incl. adversarial corpus |
| **FR-5** | Run STT offline on-device via `whisper.cpp tiny.en`; no network access at any point in the pipeline. | airplane-mode E2E run |
| **FR-6** | Implement Branch A: single-keyword (`abort`) wake-word detection that **preempts** an in-flight Branch B inference. | Exp-2 preemption trials |
| **FR-7** | Implement the swarm controller: NumPy-vectorised Boids + formation slot assignment (circle, line, wedge) + APF separation + PID point-navigation, N = 5, 50 Hz, against an abstract `SwarmEnv`. | Exp-4 |
| **FR-8** | Provide two `SwarmEnv` backends: PyFlyt (primary) and a NumPy kinematic sim (fallback / fast iteration). | both pass a hover smoke test |
| **FR-9** | Run the full pipeline end-to-end from live microphone for the demonstration. | demo video |
| **FR-10** | Emit one CSV row per benchmark trial covering accuracy, per-stage latency, peak RSS, temperature, and throttle flags. Every thesis table and figure derives from these CSVs. | `results/*.csv` committed |

---

## 6. Non-functional requirements

| ID | Requirement | Target | Measured by |
|---|---|---|---|
| **NFR-1** | Reflex latency (Branch A) | p95 ≤ 150 ms | Exp-2 |
| **NFR-2** | Cortex latency (Branch B, from end-of-speech) | p95 ≤ 2,500 ms | Exp-2 |
| **NFR-3** | Exact-match on the deployed quantised artefact, best model | **≥ 0.85** | Exp-1 |
| **NFR-4** | Intent macro-F1, best model | **≥ 0.90** | Exp-1 |
| **NFR-5** | Schema validity under GBNF | 100% *by construction* — reported as a structural guarantee, not an achievement | Exp-1 |
| **NFR-6** | CRR on the human golden set, clean audio | ≥ 0.80 | Exp-3 |
| **NFR-7** | CRR at 10 dB SNR | ≥ 0.65 | Exp-3 |
| **NFR-8** | Safe-failure rate — proportion of errors resolving to `unknown`/`HOVER` rather than a wrong action | ≥ 0.70 | Exp-1, Exp-3 |
| **NFR-9** | Peak resident memory, full Pi stack | ≤ 1.5 GB | Exp-1 |
| **NFR-10** | Thermal — proportion of trials with a non-zero throttle flag | ≤ 5%, and always reported | Exp-1 |
| **NFR-11** | Formation accuracy: fraction of drones within **τ = 0.5 m** of assigned slot, averaged over the final 5 s of a 60 s trial | ≥ 0.85 | Exp-4 |
| **NFR-12** | Inter-drone collisions | **zero observed across all trials**, with a hard separation clamp at the integrator | Exp-4 |
| **NFR-13** | Offline operation | 100% — no network dependency | FR-5 |
| **NFR-14** | Reproducibility | all dependencies pinned (PyFlyt version, `llama.cpp` SHA); fixed seeds; one-command rerun | `requirements.txt`, `run_all.sh` |

**On NFR-12:** the claim is *"zero collisions observed"*, backed by a geometric separation clamp — **not**
"zero collisions guaranteed by APF". Potential fields provide no such guarantee, and claiming one invites
a question you cannot answer (audit §B-1).

**NFR-3/4 targets are deliberately below v1.0's F1 ≥ 0.88.** v1.0's figure was set against a 16-week
dataset; these are set against a 4-day dataset and are measured on the *quantised, deployed* model rather
than an FP16 reference. A met target beats an aspirational one.

---

## 7. Experimental plan

Four experiments. Exp-5 (GNN ablation) is deleted with MARL.

| # | Experiment | Method | Metrics | Statistics |
|---|---|---|---|---|
| **Exp-1** | **Multi-model benchmark** (RQ1) | 3 models × 2 quants, on Pi 5, `llama.cpp` + GBNF. 200 trials/config. Inputs from the golden set. 10-min warm-up, one model resident at a time, swap disabled, page cache dropped between runs. Plus 3 zero-shot base-model rows for before/after. | Intent-F1, Slot-F1, **EM**, safe-failure, p50/p95/p99, tok/s, peak RSS, size, throttle % | **McNemar** on paired predictions, 3 pairwise comparisons, Bonferroni α = 0.0167. Pareto plot. |
| **Exp-2** | **Dual-path latency** (RQ2) | 200 trials/branch on Pi 5 at thermal equilibrium, WAV injection for reproducibility. Branch A: T0 = keyword onset in buffer, T1 = bus publish return. Branch B: **both** anchors, per-stage instrumented. Includes preemption trials. | p50/p95/p99 per stage; wake-word TPR/FPR; preemption latency | Distribution plots; explicit budget-vs-measured table |
| **Exp-3** | **Acoustic robustness** (RQ2+RQ3) | Full pipeline, human golden-set audio at 5 SNR levels (clean, 20, 15, 10, 5 dB), propeller-type noise from a public corpus. | CRR, WER, EM, safe-failure, E2E p50/p95 | Arcsine transform on CRR; **one-way ANOVA** + Tukey HSD across SNR; operational envelope |
| **Exp-4** | **Formation validation** (RQ3) | 50 SIL trials × 3 formations (circle, line, wedge). PyFlyt pinned, timestep 0.02 s, `seed = trial_index × 42`, initial positions `N(0, 0.5 m)` about the centroid, 60 s trials. | **FA** (τ = 0.5 m, final 5 s), **convergence rate**, **CT over converged trials** (median + IQR), collision count | **One-way ANOVA** across formations, trials as replicates |

**Three corrections to v1.0's statistical design** (audit §B): the two-way `formation × trial` ANOVA is
mis-specified — `trial` is the replication unit, so Exp-4 is one-way; CT is reported as *convergence rate*
plus *median CT over converged trials* rather than a confidence interval on a sample containing ∞; and the
`N = 5` command-history prompt prefix is dropped from the main configuration (it exists only for
comparability with Lim et al. and costs ~125 prefill tokens on every command) — it survives as one
optional ablation cell.

---

## 8. Four-week execution plan

Assumes ~6–8 focused hours/day, single operator. Days are 1-indexed from project start.

### Week 1 — Foundation, contract, dataset

| Day | Work | Deliverable |
|---|---|---|
| **D1** | **Spikes S0–S5** (audit §E) — Pi model/RAM/mic inventory, `llama.cpp` build + tok/s + 10-min thermal soak, `whisper.cpp` timing, GBNF smoke test, PyFlyt on workstation, tokenisation audit. **Go/no-go.** Then: **freeze schema v1.0** — Pydantic validator, `cmd.gbnf`, adversarial grammar tests, template-family split assignment. Pin all dependencies. | Spike report; `schema/` green; `requirements.txt` |
| **D2** | Label-first synthetic generation: 2,400 pairs, 10 intents, enumerated diversity axes, hard negatives, OOD set. | `raw_pairs.jsonl` |
| **D3** | Piper TTS → noise mix (4 SNR) → `whisper.cpp` **round-trip augmentation**. De-dup. Assemble train/val/test_synth. | `train/val/test_synth.jsonl` |
| **D4** | Golden set: record ~200 utterances × 3–4 speakers × 2 acoustic conditions. Transcribe; store ASR output beside human reference. | `audio/`, `test_golden.jsonl` |
| **D5** | Cohen's κ on a 50-row subsample with one classmate. Wake-word corpus via openWakeWord's Piper pipeline. `DATASET_CARD.md`. **Tag dataset v1.0 — freeze.** | κ reported; dataset frozen |
| **D6–D7** | Zero-shot baseline eval of all 3 base models (free "before" numbers). Latency/RAM harness written and dry-run on Pi. **Start writing Chapters 1–2.** | baseline table; `bench_latency.py` |

*Send the supervisor scope note (R-0) no later than D3.*

### Week 2 — Fine-tune, quantise, benchmark  ⟵ *the core result lands here*

| Day | Work | Deliverable |
|---|---|---|
| **D8–D9** | LoRA fine-tune M1/M2/M3, identical recipe, completion-only loss, best-on-val checkpointing. | 3 adapters + logs |
| **D10** | FP16 eval (surface A). Merge adapters → GGUF f16 → **Q8_0 + Q4_K_M** (6 artefacts). | `gguf/` |
| **D11** | Deploy all 6 to Pi. **Template-parity test** (the failure mode most likely to cost you a day). Accuracy eval on the *quantised deployed artefact* (surface B). | quantisation-delta table |
| **D12–D13** | **Exp-1**: 200 trials × 6 configs. Latency, RAM, thermal. Grammar-on vs grammar-off ablation. | `results/exp1.csv` |
| **D14** | McNemar + Bonferroni. **Table 1, Table 2, Table 3, Figure 1.** **CHECKPOINT** — the contribution is now defensible even if Weeks 3–4 slip. | core results locked |

### Week 3 — Controller, integration, robustness

| Day | Work | Deliverable |
|---|---|---|
| **D15–D16** | `SwarmEnv` abstraction. NumPy Boids, formation slot assignment (circle/line/wedge), APF separation + separation clamp, PID point-nav. NumPy backend first for fast iteration. | `swarm/` |
| **D17** | PyFlyt backend, 5 drones, 50 Hz verified. State machine + command bus. | `env_pyflyt.py` |
| **D18** | Wire full pipeline: mic → VAD → STT → SLM → validator → bus → controller. Push-to-talk plus live-mic paths. | E2E runs |
| **D19** | Branch A: openWakeWord `abort`, synthetic training, preemption logic. **Exp-2.** | `results/exp2.csv` |
| **D20** | **Exp-3** — SNR sweep, ANOVA + Tukey. | `results/exp3.csv` |
| **D21** | **Exp-4** — 150 SIL trials, one-way ANOVA. | `results/exp4.csv` |

### Week 4 — Write-up, hardening, defence

| Day | Work | Deliverable |
|---|---|---|
| **D22–D24** | Thesis Chapters 3–5 from the CSVs. All tables/figures regenerated by script. Baseline positioning vs Lim et al. with an explicit non-comparability column. | full draft |
| **D25** | Demo video (live mic → swarm formation, offline, network disabled on camera). Repo cleanup, dataset + model cards, `run_all.sh`. | demo, repo |
| **D26** | Buffer for reruns. Any SHOULD items still outstanding. | — |
| **D27–D28** | Defence slides, Q&A rehearsal — particularly: why no MARL, why not GPT-4o mini, what GBNF does and does not guarantee, why Q8 over Q4, what the synthetic-data limitations are. | slides |

**Write from Day 1.** The dominant failure mode of a 4-week project is arriving at D26 with good results
and no document. Chapters 1–2 (context, related work, method) do not depend on results — draft them in
Week 1's idle compute time.

---

## 9. Scope ladder (MoSCoW)

If the schedule slips, cut from the bottom. Decide by the **D14 checkpoint**, not on D25.

**MUST — a defensible thesis without anything else**
Schema v1.0 + GBNF + validator + tests · dataset v1.0 (synthetic + human golden) · 3 SLMs fine-tuned,
quantised, deployed · Exp-1 on-device (accuracy × latency × RAM) · E2E voice→JSON→controller working
offline with 3 formations · thesis + demo video.

**SHOULD**
Exp-3 SNR sweep · Branch A reflex + <150 ms measurement · Q8 vs Q4 delta (Table 2) · grammar ablation
(Table 3) · Exp-4 formation statistics · PyFlyt backend (NumPy sim suffices for MUST).

**COULD**
Encoder reference baseline (joint intent+slot DistilBERT) · prompt-cache and history ablations ·
MLflow + dashboard · autonomy "tunnel test" · Phi-3.5-mini as a negative "why bigger fails" data point ·
4th model (Qwen2.5-1.5B) · arXiv preprint.

**WON'T (v2.0 exclusions, stated as scope)**
MARL / MAPPO / GATv2 / PettingZoo / curriculum · Zenoh · AirSim · physical drone, battery, UBEC ·
multi-language · vision / VLM · 5-class hand-recorded wake-word corpus · GPT-4o mini · TinyBERT /
MiniLM / ALBERT as main-table rows.

---

## 10. Deliverables checklist

- [ ] `docs/` — feasibility audit, dataset plan, model pipeline, this PRD
- [ ] `schema/` — Pydantic validator, `cmd.gbnf`, canonicaliser, grammar + parity tests
- [ ] `data/` — train/val/test_synth/test_golden/test_ood, audio, wake-word, `DATASET_CARD.md`
- [ ] `gguf/` — 6 quantised artefacts + `LICENSE_MODELS.md`
- [ ] `eval/`, `results/*.csv` — harnesses and every raw result, committed
- [ ] `runtime/`, `swarm/` — the working pipeline and controller
- [ ] Tables 1–5, Figure 1 (Pareto), all script-regenerable
- [ ] Thesis Chapters 1–5
- [ ] Demo video (offline, live microphone)
- [ ] `run_all.sh` — one-command reproduction

---

## 11. Limitations and future work

Stated deliberately, in the thesis, before the jury raises them.

| Limitation | Status |
|---|---|
| **SIL only** — no physical flight. All dynamics are PyFlyt/PyBullet. | Scope. Airborne validation is future work. |
| **Physics off-device.** The Pi runs perception + NLU; PyFlyt runs on a workstation over Wi-Fi. | Deliberate: the claim under test is edge *inference*, not edge *physics*. Also isolates latency measurement from physics jitter. |
| **Bulk training data is synthetic**; diversity is bounded by the generating model's priors. | Mitigated by enumerated diversity axes and by reporting on human speech only. |
| **Bulk audio is TTS.** | All reported CRR/WER come from the human golden set; TTS is development and SNR-sweep material only. |
| **~4 speakers** in the golden set — insufficient for a speaker-independence claim. | Per-speaker breakdown reported so variance is visible. |
| **Propeller noise is a public-corpus/bench approximation**, not near-field acoustic coupling on a flying airframe. | Source named explicitly in the dataset card. |
| **Single seed** for the model comparison (3 seeds for the winner only). | Stated; not presented as a robustness result. |
| **Airborne electrical integration** (LiPo, UBEC, power budget) out of scope. | Future work. |
| **Audio capture chain.** A 3.5 mm analog mic via a low-cost USB audio adapter; such dongles have measurable self-noise and no shielding against USB 3.0 / SSD interference. | Noise floor measured and reported in the dataset card. No AGC or noise suppression is applied, so captured PCM is unprocessed — an advantage over consumer laptop capture. |
| **Coordinate-frame mismatch** — PX4 uses NED, PyFlyt uses ENU. No transform implemented. | Internally consistent in SIL; required for hardware. |
| **No vision / VLM**; motion blur and imaging artefacts not modelled. | Future work. |
| **Thermal characterisation is at static bench load**; real flight airflow changes cooling. | 10-min warm-up at worst-case static load is a conservative bound. |
| **English only.** | Scope. |
| **GBNF guarantees syntax, not semantics.** | Explicitly stated; motivates the second validator layer and the safe-failure metric. |

---

## 12. Risk register

| ID | Risk | Level | Mitigation | Contingency |
|---|---|---|---|---|
| **R-0** | **Supervisor has not approved the 4-week reduced scope.** His échéancier is 6 months; MARL was never in his brief. | **Critical** | One-page scope note by **D3**: window, MARL removed, GPT-4o mini dropped and why, three-SLM set, MUST list. Get a written reply. | Re-negotiate scope before D7, while the dataset is still cheap to change |
| **R-1** | Pi 5 too slow for the latency target (S1 fails) | High | Day-1 spike; prefill fix (no schema in prompt, no history, cached prefix); null-omitting schema | Demote to SmolLM2-360M as primary; re-baseline NFR-2 with the measured figure and report honestly |
| **R-2** | **Audio capture.** 3.5 mm analog mic acquired; Pi 5 has no analog input, so a USB audio adapter is required. Cheap dongles have high self-noise and are susceptible to USB 3.0 / SSD interference. | Low | USB audio adapter matched to plug type (TRS→2-jack, TRRS→combined). Dongle on a short extension away from the board. Noise floor measured and reported in the dataset card. 48 kHz capture with offline 3:1 resample — never ALSA `plug` resampling for the golden set. | I2S codec HAT (WM8960-class) if the noise floor is unusable; or workstation capture streamed over the command bus (inference stays on the Pi) |
| **R-3** | Chat-template drift between HF training and llama.cpp inference | High | `test_template_parity.py` as a mandatory CI step after every conversion | Manual template application; verify token-by-token |
| **R-4** | Dataset schema gap found in Week 3 | Medium | Freeze on D1 *before* generating; required-slot matrix reviewed against all 10 controller entry points | Note as future work — do **not** regenerate; regeneration invalidates measured results |
| **R-5** | PyFlyt/PyBullet fails to build or runs slow | Medium | S4 on the workstation, D1 | NumPy kinematic backend is already the MUST path; PyFlyt drops to SHOULD |
| **R-6** | Wake-word FPR too high under noise | Medium | Single keyword; openWakeWord's official synthetic pipeline with RIR + noise augmentation | Push-to-talk for the demo; report FPR honestly as a boundary |
| **R-7** | Q4 quantisation destroys structured-output accuracy | Medium | Both Q8_0 and Q4_K_M produced; delta measured | Q8_0 becomes the deployment default — and the delta becomes a finding (C3) |
| **R-8** | Thermal throttling corrupts latency figures | Medium | Active cooler; `-t 3`; 10-min warm-up; per-trial temp + throttle logging | Flag and report affected trials; never silently drop them |
| **R-9** | No second annotator available for κ | Low | 90 min of one classmate's time; synthetic labels need no annotation | Documented single-annotator adjudication protocol + spot check, stated as a limitation |
| **R-10** | GPU/Colab unavailable for fine-tuning | Low | Models are small; LoRA on 0.36–1.2 B fits free-tier | School cluster → Kaggle (30 h/week free) → CPU LoRA on M2 only as a last resort |
| **R-11** | Results exist but the thesis is unwritten at D26 | **High** | Chapters 1–2 drafted in Week 1; all tables script-generated from CSVs | D26 is reserved buffer; cut COULD items first |

---

## 13. Traceability

| RQ | Requirements | Experiments | Outputs |
|---|---|---|---|
| RQ1 | FR-2, FR-3, FR-4; NFR-3, 4, 5, 9, 10 | Exp-1 | Tables 1–3, Figure 1 |
| RQ2 | FR-1, FR-5, FR-6, FR-9; NFR-1, 2, 6, 13 | Exp-2, Exp-3 | Table 4 |
| RQ3 | FR-7, FR-8; NFR-7, 8, 11, 12 | Exp-3, Exp-4 | Table 4, Exp-4 tables |

---

## 14. References

[1] S. K. Lim, M. J. Y. Chong, J. H. Khor, T. Y. Ling, "Taking Flight with Dialogue: Enabling Natural
Language Control for PX4-based Drone Agent," arXiv:2506.07509, 2025. — *primary baseline*
[2] C. W. Reynolds, "Flocks, Herds, and Schools: A Distributed Behavioral Model," SIGGRAPH, 21(4), 1987.
[3] J. Gou et al., "Benchmarking 25 LLMs on Single-Board Computers," arXiv, 2025.
[4] G. Gerganov, "llama.cpp" / "whisper.cpp," github.com/ggerganov.
[5] D. Scripka, "openWakeWord," github.com/dscripka/openWakeWord.
[6] J. Jet, "PyFlyt," jjshoots.github.io/PyFlyt.
[7] Qwen Team, "Qwen2.5 Technical Report," arXiv:2412.15115, 2024.
[8] L. Ben Allal et al., "SmolLM2," Hugging Face, 2024.
[9] Meta AI, "Llama 3.2," 2024.
[10] J. FitzGerald et al., "MASSIVE: A 1M-Example Multilingual NLU Dataset," ACL, 2023.
[11] P. Warden, "Speech Commands: A Dataset for Limited-Vocabulary Speech Recognition," arXiv:1804.03209.
[12] M. Strauss et al., "DREGON: Dataset and Methods for UAV-Embedded Sound Source Localization," IROS, 2018.
[13] K. J. Piczak, "ESC-50: Dataset for Environmental Sound Classification," ACM MM, 2015.
[14] A. Radford et al., "Robust Speech Recognition via Large-Scale Weak Supervision" (Whisper), ICML, 2023.
[15] E. J. Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models," ICLR, 2022.

*Reference details should be verified against current sources before submission; several are cited from
the v1.0 PRD's bibliography.*
