# Step 1 — Technical & Feasibility Audit

**Scope:** reconciliation of Prof. Khaldi's registration form (`Voice-Control for Drone Swarm.doc`)
against the expanded PRD (`Voice_Control for Drone Swarms.pdf`), plus an engineering audit of the
edge-deployment claims against a hard 4-week deadline.

**Verdict up front:** the architecture is sound and the contribution is real, but the PDF is scoped
for ~16 weeks and carries three latency assumptions that do not survive arithmetic. Cutting MARL
(as directed) removes ~35% of the work. Cutting the items in §D removes another ~30% and is what
makes 4 weeks possible. One finding (§C-1, prompt prefill) is a genuine architectural fix, not a cut —
it is the difference between hitting and missing the p95 target.

---

## A. Contradictions & ambiguities between the two documents

| # | Item | Prof. Khaldi (`.doc`) | Your PRD (`.pdf`) | Resolution |
|---|---|---|---|---|
| A-1 | **Timeline** | 6 months (1.5+1.5+1+1+1) | 16 weeks | **1 month.** A 6× compression from the supervisor's own plan. See §E-0 — get the reduced scope acknowledged in writing before Day 3. |
| A-2 | **Model candidates** | GPT-4o mini, LLaMA-3.2-3B, TinyBERT, MiniLM, ALBERT, TinyLlama | Qwen2.5-0.5B, TinyBERT, MiniLM-L6 | Neither list is coherent. See A-3, A-4. New list in `03_model_pipeline.md` §1. |
| A-3 | **GPT-4o mini** | Named as a candidate "designed for mobile/edge computing" | Absent | **Hard contradiction.** GPT-4o mini is closed-weight and cloud-only. It cannot run on a Pi and directly violates the *"100% offline / local execution on resource-constrained hardware"* requirement that is the project's stated core claim. Must be dropped, and the drop justified in one paragraph of the thesis (it is a defensible correction, not an omission). |
| A-4 | **Task formulation** | Encoders (TinyBERT/MiniLM/ALBERT) → *intent classification*, metrics = F1/Accuracy | Generative SLM → *GBNF-constrained JSON*, but retains TinyBERT/MiniLM in the same benchmark table | **Apples-to-oranges.** Encoders cannot emit slot-filled JSON without a separate token-classification head; the PDF's own Exp-2 note admits the asymmetry and then reports both under one F1 column. Two different tasks cannot share a metric. Your new requirement (≥3 generative SLMs) *fixes* this: SLM-vs-SLM on an identical task is a controlled comparison. Keep **one** encoder (joint intent+slot DistilBERT) as an explicitly-labelled non-generative reference point, not as a row in the main table. |
| A-5 | **Simulator** | "PyFlyt **or** AirSim" | PyFlyt (pinned) | PyFlyt. AirSim is archived upstream and requires Unreal — a multi-day install risk with zero thesis value. Document the choice. |
| A-6 | **Hardware** | Unspecified; "TinyLlama (tested on Raspberry Pi 5)" | Pi 5, 8 GB, mains-powered | **RESOLVED: Raspberry Pi 5 confirmed** (27 W official USB-C PSU, active cooler, USB SSD). **RAM tier still to be recorded** for the thesis hardware table (§E, S0). Plan does not fork on the answer — the ~1.0 GB budget in §C-3 fits a 4 GB unit. |
| A-7 | **Microphone** | Not mentioned | "USB Mic Array" in Fig. 1; absent from the hardware table and from the student's stated baseline | **RESOLVED: 3.5 mm analog microphone acquired.** The Pi 5 has no analog input, so capture requires a **USB audio adapter** (~\$3–8, CM108-class, driver-free). Match the dongle to the plug type (2 rings = TRS → 2-jack dongle; 3 rings = TRRS → combined jack). Full bring-up, sample-rate discipline, and noise-floor protocol in §C-6. No AGC on these dongles, so the earlier "optimistic WER" limitation is removed. |
| A-8 | **Intent class count** | Not specified | "15 distinct classes" | 15 classes × a 3-4 day dataset build gives ~100 train examples/class and unstable per-class F1. Reduced to **10 classes** (`02_dataset_plan.md` §2), each mapping 1:1 onto a controller action. Fewer, cleaner classes is a stronger result than 15 noisy ones. |
| A-9 | **Drone addressing** | Not mentioned | Schema has **no `drone_ids` field** | Your brief explicitly requires *"drone IDs"* as a dataset parameter dimension. The PDF schema cannot represent "drone 3, hold position" — the model would have nowhere legal to put it and would hallucinate. Added as `ids` in schema v1.0. |
| A-10 | **Out-of-domain handling** | Not mentioned | No `unknown` intent | Same class of bug: with GBNF forcing a legal command, "what's the weather" is *guaranteed* to produce a flight command. An explicit `unknown` intent is a safety requirement, not a nicety. Added. |
| A-11 | **Language** | Not specified | Whisper `tiny.en` (English-only) + "Multi-language" as a Tier 3 criterion | Self-contradictory. Drop multi-language entirely. |
| A-12 | **MARL** | Not mentioned anywhere in the supervisor's form | Full Phase 2: MAPPO, GATv2, PettingZoo, curriculum, reward shaping, Exp-5 | Cut per your directive. Worth noting it was **never** in the supervisor's brief — it was pure scope inflation, and removing it moves the project *toward* the approved subject, not away from it. Useful framing for the defence. |

---

## B. Internal errors and overclaims in the PDF (things a jury will catch)

These are not scope problems. They are statements that are wrong or unfalsifiable as written, and each
is cheap to fix.

1. **"Collisions: Zero (APF-guaranteed)"** — Artificial Potential Fields provide *no* collision
   guarantee. With discrete timesteps and bounded actuation, penetration is always possible; APF is a
   reactive heuristic with known failure modes (local minima, oscillation, the very failures your own
   §4.2 escape rule concedes). **Fix:** claim *"zero collisions observed across N = 150 trials"* and add
   a hard geometric separation clamp at the integrator so the claim has a mechanism behind it. Never
   write "guaranteed" about a potential field.

2. **"Two-way ANOVA (formation × trial)"** — `trial` is the replication unit, not a factor. A two-way
   ANOVA over it is a statistical error. **Fix:** one-way ANOVA across the three formations, trials as
   replicates.

3. **"CT = ∞ if convergence not achieved. Recorded, not discarded"** + **"95% CIs on CT"** — mutually
   exclusive. You cannot compute a confidence interval on a sample containing ∞. **Fix:** report
   *convergence rate* (%) and *CT over converged trials only* (median + IQR) as two separate numbers.
   This is also the honest presentation.

4. **"FA ≥ 90%"** — Formation Accuracy is defined in Table 5 as *mean positional error* (a distance),
   then thresholded as a percentage. Undefined without a tolerance. **Fix:** `FA = fraction of drones
   within τ = 0.5 m of assigned slot, averaged over the final 5 s of the trial`. State τ everywhere.

5. **"Valid JSON %" as a contribution vs. Lim et al.** — under GBNF, syntactic validity is **100% by
   construction**. Reporting it as a beaten metric is circular: you are not outperforming Lim et al.'s
   100%, you are making the metric vacuous. **Fix:** state this explicitly and move the claim to where
   it is real — *semantic* accuracy (correct intent + correct slots) and *latency under grammar
   constraint*. Add one honest sentence: "GBNF removes syntactic failure as a failure mode; it does not
   constrain semantics, which is what we measure." That sentence will earn marks.

6. **Cohen's κ with two annotators** — requires a second human for 50+ samples. If you are working
   alone this is not a schedule risk, it is an impossibility. **Fix:** the synthetic set needs no
   annotation at all under label-first generation (`02_dataset_plan.md` §3), so κ applies only to the
   ~200-utterance golden set. Recruit one classmate for 90 minutes, or replace with a documented
   single-annotator adjudication protocol + second-pass spot check on a 50-sample subsample. Either is
   defensible; silently dropping κ after specifying it is not.

7. **Memory table (Table 2) is internally inconsistent.** Rows and RAM figures are misaligned, and
   `Whisper tiny.en → 800 MB` is off by ~4×. Corrected derivation in §C-3.

8. **Model licences unaddressed.** Qwen2.5 = Apache-2.0, SmolLM2 = Apache-2.0, Phi-3.5 = MIT,
   **Llama-3.2 = Meta Community Licence** (attribution + naming obligations, use-policy clause). For a
   public repo + a manuscript this needs one line in the thesis. Verify each before publishing weights.

---

## C. Edge-deployment edge cases

### C-1. The latency budget does not close as written — and the fix is architectural

The PDF budgets `<3 s` p95 for the Cortex path and then states *"48 tokens adds 2.4 s — still within
the <3 s p95 budget"*, leaving ~600 ms for VAD + STT + prefill. That is not enough. Three unbudgeted
costs:

| Stage | PDF treatment | Reality | Note |
|---|---|---|---|
| VAD endpointing | "Silero VAD 30 ms" | **300–700 ms** | 30 ms is per-frame *compute*. The real cost is `min_silence_duration_ms` — the wall-clock wait to confirm end-of-speech. Unbudgeted entirely. |
| Whisper `tiny.en` | listed, not budgeted | **0.6–1.8 s** for a 3 s utterance | And cores 0–2 are pinned to llama.cpp, so STT runs contended. |
| **SLM prefill** | **not budgeted at all** | **potentially 2–6 s** | The killer. See below. |
| SLM decode | 2.4 s @ 48 tok | 0.7–1.7 s after §C-2 fix | |

**The prefill problem.** The PDF's Exp-2 config mandates a system prompt describing the schema *plus*
`N = 5` previous JSON commands as a prompt prefix. That is roughly 150 (system) + 125 (history) + 15
(utterance) ≈ **290 prefill tokens on every single command**. On a Pi 5 CPU, prompt processing for a
0.5B Q4 model is in the low hundreds of tok/s at best — this alone can consume the entire budget, and
it is paid *per utterance*, forever.

**Three fixes, all free:**

- **Drop the `N=5` history prefix.** It exists solely for comparability with Lim et al. Single-turn
  command parsing does not need conversational history. Cost: −125 tokens/call. Keep it as *one
  ablation cell* if you want the comparison.
- **Fine-tuning removes the need to describe the schema in the prompt.** That is the entire point of
  fine-tuning. A fine-tuned model takes the bare transcript as input. Cost: −150 tokens/call.
- **Reuse the static prefix KV cache** (`llama.cpp` prompt cache / persistent server context) so any
  remaining fixed prefix is prefilled **once at startup**, not per command.

After all three, per-call prefill is the ~15-token utterance ⇒ **~0.1–0.3 s**.

**Revised, defensible budget** (to be replaced by measured values in Week 2):

| Stage | Target p95 |
|---|---|
| VAD endpointing | 500 ms |
| Whisper `tiny.en` (whisper.cpp Q5) | 1,200 ms |
| SLM prefill (cached prefix) | 250 ms |
| SLM decode (~22 tok, omit-null schema) | 1,100 ms |
| Validate + dispatch | 50 ms |
| **E2E from end-of-speech** | **~2.4 s** |
| **E2E from start-of-speech** (3 s utterance) | **~5.4 s** |

**Also fix the measurement definition.** The PDF defines T0 precisely for Branch A and leaves it
ambiguous for Branch B. Report **both** anchors (end-of-speech and start-of-speech) with a per-stage
breakdown. Reporting only end-of-speech looks like hiding; reporting only start-of-speech makes a
correct system look slow. Set the headline PRD target as **p95 < 2.5 s from end-of-speech**, with the
full stage table alongside.

### C-2. Malformed / semantically-invalid structured output

GBNF guarantees *shape*, never *meaning*. Enumerated failure modes and mitigations:

| Failure mode | Example | Mitigation |
|---|---|---|
| Syntactically valid, semantically impossible | `{"intent":"formation","shape":"circle"}` with no radius | **Per-intent required-slot matrix** in a Pydantic validator downstream of the grammar. Grammar makes shape legal; validator makes meaning legal. Two layers, both mandatory. |
| Out-of-range numbers | `radius: 400.0`, `z: -50.0` | GBNF cannot express ranges — only digit counts. Bound digit count in the grammar (`num ::= "-"? [0-9]{1,3} ("." [0-9])?`), then **clamp** in the validator against a physical envelope (radius 1–10 m, z 0.5–15 m, speed ≤ 2 m/s). Clamp-and-log, do not reject: a clamped command is safer than a dropped one. |
| Degenerate float tokens | `2.`, `-`, `1e999`, 18-digit integers | Prevented by the tight `num` rule above. **Unit-test the grammar against an adversarial corpus** — this is a 30-line test and it is the single highest-value test in the repo. |
| `max_tokens` truncation mid-object | `{"intent":"move","pos":[1.0,` | Grammar guarantees structure *only if generation terminates*. Set `max_tokens` above the measured worst case (Week 2 tokenisation audit), and treat truncation as a parse failure → `HOVER`. |
| Unit ambiguity | "go up 5" — metres? feet? | Canonical unit contract (metres, m/s, degrees) stated in the schema doc and in every training example. Never mix units in the dataset. |
| Unaddressable reference | "drone 3 hold position" with no `ids` field | Fixed by A-9. Also validate `ids ⊆ {0..N-1}` and drop unknown IDs with a log line. |
| Out-of-domain speech | "what's the weather" | Fixed by A-10 (`unknown` intent) + ~150 OOD training examples. Without this, GBNF *forces* a flight command out of arbitrary noise. |
| **STT→NLU distribution shift** | Whisper renders "wedge" as "which", "echelon" as "a shell on" | **The most important one.** Training on clean text and inferring on ASR output is a train/test mismatch that will silently cost you 10–20 points of exact-match. Fix = TTS→noise→ASR round-trip augmentation (`02_dataset_plan.md` §4). Fully automated. |
| Failure fallback | — | Every unrecoverable path resolves to `HOVER` + structured log. Never to a movement command. |

### C-3. Memory pressure — corrected derivation

| Component | Basis | Resident (est.) |
|---|---|---|
| Qwen2.5-0.5B `Q4_K_M` weights | GGUF on disk, `mlock`ed | ~400 MB |
| KV cache | 24 layers × 2 KV heads × 64 dim × 2 (K,V) × 2 B ≈ 24 KB/tok × 2048 ctx | ~50 MB |
| `whisper.cpp tiny.en` Q5 + buffers | 40 MB weights + scratch | ~250 MB |
| openWakeWord (melspec + embedding + head, ONNX) | | ~100 MB |
| Python 3 + NumPy + Pydantic + audio stack | | ~150 MB |
| Controller + command bus | NumPy, N=5 | ~30 MB |
| **Total** | | **~1.0 GB** |

Fits comfortably on 8 GB and adequately on 4 GB — *provided* PyFlyt/PyBullet (+300–500 MB and a
saturated core) runs **off-device**. Practical edge cases:

- **Never load two SLMs concurrently.** Benchmark sequentially, one process per model, fresh process
  per configuration, with page cache dropped between runs — otherwise you are measuring warm cache.
- **`mlock` + `mmap` interaction:** with `mlock` enabled, pass `--no-mmap` in llama.cpp or the model is
  mapped *and* locked and peak RSS roughly doubles during load.
- **Disable swap and zram** for all benchmark runs (`swapoff -a`), and state it in the methodology. A
  single swap-in invalidates a p99 latency figure.
- **Measure `VmHWM`** (peak RSS) from `/proc/<pid>/status`, not instantaneous RSS. Report llama.cpp's
  own model + KV figures alongside it as a cross-check.

### C-4. Thermal

The PDF's *"10-min warm-up; cold-boot testing is explicitly prohibited"* is right in spirit and wrong
in framing — a real deployment **is** a cold start. **Fix:** log `vcgencmd measure_temp` and
`vcgencmd get_throttled` alongside *every* latency sample, and report steady-state as the headline with
a cold-start figure in an appendix. Any trial with a non-zero throttle flag is reported, flagged, and
not silently dropped. Sustained 3-core llama.cpp load on a Pi 5 with an active cooler should stay under
throttle, but this is a measurement, not an assumption — it is Spike S1.

### C-5. Concurrency

The PDF pins cores 0–2 to llama.cpp and reserves core 3 for a 50 Hz controller + Zenoh + STT +
wakeword. Core 3 is oversubscribed. With the controller moved off-device (§D-3), the Pi runs
wakeword (continuous, cheap) + VAD + STT + SLM, which are *sequential* per command, not concurrent —
so contention largely dissolves. Keep 3 threads for llama.cpp (`-t 3`) and leave core 3 for the audio
callback, which must never miss a buffer. Confirm no dropped audio frames under load.

### C-6. Audio capture — no microphone currently owned

**Hardware constraint:** the **Pi 5 has no 3.5 mm audio jack** (removed relative to the Pi 4) and no
analog audio input of any kind. Capture must arrive over **USB** or an **I2S HAT**.

**Current status: a 3.5 mm analog microphone has been acquired.** It is usable via a **USB audio adapter**
(USB sound-card dongle with a microphone input, ~\$3–8, CM108/CM109-class). These are USB Audio Class 1.0
compliant and require no drivers on Raspberry Pi OS. Match the dongle to the plug type:

| Insulating rings on plug | Type | Required dongle |
|---|---|---|
| **2** | TRS, 3-pole — classic PC mic (usually pink) | **Two separate jacks** (pink mic + green headphone). Supplies the bias / plug-in power an electret capsule needs. |
| **3** | TRRS, 4-pole — phone/headset style | **Single combined headset jack**, or a TRRS→dual-TRS splitter into a 2-jack dongle |

Mismatching these is the usual failure mode: the microphone is either not enumerated or is barely audible.

**Bring-up sequence:**

```bash
lsusb && arecord -l && arecord -L        # confirm enumeration; note the card index
alsamixer -c 1                            # F4 = capture; raise "Mic" and "Mic Boost"
arecord -D plughw:1,0 -f S16_LE -c 1 -r 48000 -d 5 /tmp/test.wav && aplay /tmp/test.wav
```

**Sample-rate discipline.** Most low-cost dongles support only 44.1/48 kHz natively, while Whisper
requires 16 kHz mono. For development, `-r 16000` is acceptable (ALSA's `plug` layer resamples). **For the
golden set, do not rely on it** — ALSA's plug resampler is low quality and must not sit inside a reported
WER figure. Record at 48 kHz and resample offline: `sox in.wav -r 16000 -c 1 out.wav rate -v`. In Python,
48 kHz → 16 kHz is exactly 3:1, so `scipy.signal.resample_poly(x, 1, 3)` is both cheap and high-quality.

**Noise-floor characterisation (2 minutes, do it once).** Cheap dongles have high self-noise and no
shielding, and the Pi's USB 3.0 bus and SSD radiate directly into a cheap analog front end. Mount the
dongle on a short USB extension away from the board, then record 10 s of silence and report the RMS noise
floor in the dataset card. Check specifically for 50 Hz mains hum, since the Pi is mains-powered.

**Advantage over the laptop-mic fallback:** these dongles apply no AGC and no noise suppression, so the
captured PCM is honest. This removes the "optimistic WER/CRR" limitation that off-device consumer capture
would have introduced.

**Escalation path if the noise floor proves unusable:** an I2S codec HAT with analog input (WM8960-class,
Audio Injector series) offers a substantially better analog front end at the cost of a device-tree overlay
in `/boot/firmware/config.txt`. Only pursue this if the dongle measurably fails.

**Alternative capture devices** (each enumerates as a standard ALSA capture device, should the dongle
route fail): USB webcam (built-in mic) · USB headset · USB conference mic · ReSpeaker 2-Mic HAT for
far-field capture matching the operational use case.

**Why this is not a blocker.** Recording and inference are separable, and the experimental design
already requires them to be:

| Consumer | Needs a live mic? | Why |
|---|---|---|
| Exp-1 (model benchmark) | No | Text input from `test_golden.jsonl` |
| Exp-2 (dual-path latency) | **No** | WAV injection is *mandatory* — a p95 latency figure measured from live speech is not reproducible |
| Exp-3 (SNR sweep) | No | Requires pre-recorded audio by construction (fixed SNR mixing) |
| Exp-4 (formations) | No | Command-level input |
| Golden set recording | No | Record on any device (laptop, phone, USB headset); copy WAVs to the Pi |
| **FR-9 (live demo)** | **Yes** | The only hard dependency |

**Why it should still be resolved in Week 1** — three risks of deferring to D25:

1. **The ALSA / `sounddevice` capture path on ARM64 goes untested.** Audio capture on Linux is the most
   reliably troublesome integration surface in this project (sample-rate negotiation, buffer sizing,
   callback threading, dropped frames). Discovering it on demo day is the bad outcome.
2. **Branch A is inherently a streaming component.** Measure it on injected streams through the same ring
   buffer — that is the correct methodology — but obtain at least one live confirmation that the wake
   word fires on a real human voice.
3. **Laptop microphones inflate the reported numbers.** Consumer laptop capture applies aggressive AGC
   and noise suppression, so a golden set recorded there is *cleaner* than raw USB PCM. WER and CRR come
   out optimistic by an unquantifiable margin. If the golden set is recorded off-device, **state the
   capture device in the dataset card** and treat it as a limitation.

**Acceptable capture devices** — superseded by the analog-mic-plus-adapter path above; see the
"Alternative capture devices" line for fallbacks.

**Fallback if acquisition proves impossible:** run capture on the Ubuntu workstation and stream PCM to the
Pi over the command bus. Defensible — all *inference* remains on the Pi, which is the actual claim — but
weaker. Record it in §11 of the PRD as a stated limitation rather than leaving it for a jury to notice.

---

## D. High-risk assumptions to trim for 4 weeks

Ordered by hours recovered.

| # | Assumption in PDF | Why it fails at 4 weeks | Decision |
|---|---|---|---|
| D-1 | **MARL Phase 2** (MAPPO, GATv2, PettingZoo, 3M-step curriculum, reward ablation, Exp-5) | Weeks of GPU time and tuning; not in the supervisor's brief | **CUT** (directed) |
| D-2 | **openWakeWord: 5 keyword classes, 2,500 hand-recorded positives, 2,000 recorded negatives, 10-min propeller soak** | Hand-recording 2,500 clips is multi-day. And you own no drone, so "recorded propeller noise" has no source. | **REDUCE to 1 keyword** ("abort"), trained via openWakeWord's *official synthetic Piper-TTS pipeline* (~1–2 h on Colab, which is what the tool is designed for). Propeller noise from a public corpus (see `02_dataset_plan.md` §5). Preserves the Reflex contribution at ~1/5 the cost. |
| D-3 | **PyFlyt + 50 Hz controller + full inference stack on the Pi** | PyBullet on ARM64 is a real install risk, and co-locating it destroys latency reproducibility | **MOVE OFF-DEVICE from Day 1.** Networked-SIL becomes the *primary* configuration, not a Week-10 activity. Pi = perception + NLU (the actual claim). Workstation = physics. |
| D-4 | **Eclipse Zenoh** | A whole distributed middleware, its own failure class, for two processes | **DEFER.** Use a 40-line `CommandBus` abstraction over UDP/JSON (or ZeroMQ). Keep the interface swappable and say so in the thesis — the architectural point survives, the dependency does not. |
| D-5 | **500 hand-recorded audio samples + 15 intents** | ~2 days of recording alone | **RESTRUCTURE:** ~2,400 label-first synthetic text pairs (zero annotation) + Piper TTS audio + a **~200-utterance human golden set** which is what you actually report. 10 intents. |
| D-6 | **Cohen's κ, two annotators, 500+ samples** | Needs a second human at scale | **REDUCE** to the 200-item golden set; 90 min of one classmate's time. |
| D-7 | **Full statistical battery** (McNemar+Bonferroni, arcsine+one-way ANOVA+Tukey, two-way ANOVA, η²) | Not all equally cheap | **KEEP the cheap and correct:** McNemar on paired model predictions (5 lines of `scipy`, and it is genuinely the right test for two models on one test set); one-way ANOVA + Tukey on the SNR sweep. **DROP** the two-way ANOVA (it was mis-specified anyway, §B-2) and η². |
| D-8 | **Phi-3.5-mini as a candidate** | 3.8B → ~2.2 GB at Q4 and single-digit tok/s on a Pi 5; blows the latency target | **DROP as a primary.** Optionally include as a documented *"why bigger is not viable at the edge"* ceiling data point if Week 3 has slack. |
| D-9 | **MLflow + FastAPI dashboard** | Infrastructure that produces no thesis result | **DOWNGRADE** to CSV + a plotting script. Add the dashboard in Week 4 only if ahead. |
| D-10 | **AirSim demo, multi-language, manuscript submission** | Tier 3 items behind a gate that no longer exists | **CUT.** Keep "arXiv preprint" as a post-defence option. |
| D-11 | **Week-11 binary gate / 3-tier rubric** | A 16-week governance structure | **REPLACE** with a MUST/SHOULD/COULD ladder (PRD §9) and one checkpoint at end of Week 2. |

**What survives is still a strong thesis:** a fine-tuned, grammar-constrained SLM running fully offline
on ARM64, benchmarked across three model scales and two quantisations on accuracy × latency × memory,
driving a 5-drone simulated swarm through a validated command schema, with a measured sub-150 ms safety
reflex. That is a complete, novel, defensible contribution — and every claim in it is measured.

---

## E. Day 0–1 go/no-go spikes

Nothing else starts until these pass. Each is timeboxed; total ≈ 1 day. If a spike fails, its
contingency is listed — do not improvise on Day 1.

| ID | Spike | Pass criterion | If it fails |
|---|---|---|---|
| **S0** | `cat /proc/device-tree/model; free -h; vcgencmd measure_temp; lsusb; arecord -l` | Pi 5 model string + **RAM tier** recorded in the repo. Mic: **known absent** — `arecord -l` confirms no capture device | Acquire a USB capture device locally this week (§C-6). Proceed meanwhile: all experiments use WAV injection; golden set recorded off-device |
| **S1** | Build `llama.cpp`, run `Qwen2.5-0.5B-Instruct Q4_K_M`, 200-token generation, `-t 3`, 10-min soak, log temp + `get_throttled` | ≥ 12 tok/s sustained, no throttle flag | Drop to SmolLM2-360M as the primary model; re-baseline the latency target |
| **S2** | Build `whisper.cpp`, `tiny.en` Q5, transcribe a 3 s WAV, `-t 4` | < 1.8 s | Try `faster-whisper` (CTranslate2); else shorten the utterance protocol |
| **S3** | Feed the draft GBNF grammar to `llama-cli` on the base (un-tuned) model, 20 prompts | 20/20 parse as valid JSON against the Pydantic validator | Simplify the grammar (drop optional fields), re-test |
| **S4** | `pip install PyFlyt` **on the workstation**; spawn 5 drones; hold hover 30 s | Runs at ≥ 50 Hz | Use the NumPy kinematic sim as primary; PyFlyt becomes a stretch validation env |
| **S5** | Measure end-to-end tokenisation of the 20 worst-case JSON outputs | Worst case ≤ 40 tokens | Compress key names further; re-audit |

**E-0 — the one non-technical action item.** Prof. Khaldi's own échéancier is six months. Before Day 3,
send him a one-page note stating: (a) the 4-week delivery window, (b) that MARL is out of scope, (c)
that GPT-4o mini is dropped as incompatible with the offline requirement, (d) that the model set is now
three generative SLMs, (e) the MUST list you will defend. Get a reply. An acknowledged reduced scope is
a completed project; an unacknowledged one is a contested viva. This is the cheapest risk mitigation in
the entire plan.
