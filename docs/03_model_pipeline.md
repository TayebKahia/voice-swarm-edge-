# Step 3 — Multi-Model Fine-Tuning & Evaluation Pipeline

**Window: Week 2 (D8–D14).** One recipe, three models, two quantisations, two evaluation surfaces.

The design principle: **hold everything constant except the model.** Same data, same LoRA config, same
seed, same grammar, same eval harness, same thermal protocol. Then every difference in the results table
is attributable to model scale and architecture — which is the whole point of RQ1. Any per-model
hyperparameter tuning destroys the comparison, so it is prohibited (with one documented exception, §3.4).

---

## 1. Model selection

Your brief requires Qwen2.5-0.5B plus ≥2 other lightweight SLMs. Recommended set:

| # | Model | Params | Licence | Q4_K_M (est.) | Why this one |
|---|---|---|---|---|---|
| **M1** | `Qwen2.5-0.5B-Instruct` | 0.5 B | Apache-2.0 | ~400 MB | Required. Strong small-model instruction following; efficient tokeniser. **Expected winner / deployment default.** |
| **M2** | `SmolLM2-360M-Instruct` | 0.36 B | Apache-2.0 | ~270 MB | The **latency floor**. Smallest credible instruct model; if it holds accuracy, it is the better edge answer and that is a genuine finding. Llama-architecture ⇒ same tooling. |
| **M3** | `Llama-3.2-1B-Instruct` | 1.2 B | **Meta Community** | ~800 MB | The **accuracy ceiling** at the edge, and the practical upper bound on a Pi 5. Continues Prof. Khaldi's Llama-3.2 lineage (his doc names the 3B; the 1B is its viable edge sibling). |

Three points at 0.36 B → 0.5 B → 1.2 B give a clean Pareto curve over ~3.3× of scale. That curve *is*
the answer to RQ1.

**Deliberate exclusions:**
- **Phi-3.5-mini (3.8 B)** — ~2.2 GB at Q4 and single-digit tok/s on a Pi 5; it cannot meet the latency
  target. Include only as a Week-4 stretch "why bigger is not viable at the edge" data point. Its value
  is as a *negative* result, and negative results are cheap to obtain last.
- **GPT-4o mini** — closed-weight, cloud-only, contradicts the offline requirement (audit A-3).
- **TinyBERT / MiniLM / ALBERT as main-table rows** — different task, non-comparable metric (audit A-4).

**Optional M4 — encoder reference (stretch, ~4 h).** A joint intent+slot `DistilBERT` (BIO tagging head
for slots, classification head for intent). It cannot emit JSON; it emits an intent label plus tagged
spans that you assemble into JSON in Python. Report it in a **separate table**, explicitly labelled
non-generative, as a latency/accuracy reference floor. This is the honest way to honour the supervisor's
original encoder interest, and it usually produces a nice result: much faster, slightly worse on
compositional commands, and unable to handle anything the tag scheme did not anticipate.

**Licence action:** Llama-3.2 requires attribution and carries naming obligations for derivatives. Before
publishing merged weights, add a `LICENSE_MODELS.md` recording each base model's terms. One hour, avoids
a real problem.

---

## 2. Compute

| Stage | Where | Notes |
|---|---|---|
| Fine-tuning | Colab T4/L4 free or Pro, or any ≥8 GB local GPU | 0.36–1.2 B with LoRA fits easily |
| FP16 accuracy eval | Same GPU | fast, used for config selection |
| GGUF conversion | Same machine | `llama.cpp/convert_hf_to_gguf.py` + `llama-quantize` |
| **Quantised accuracy eval** | **Pi 5** | must be measured on the deployed artefact, §5.2 |
| **Latency / RAM / thermal** | **Pi 5, exclusively** | §5.3 |

**LoRA, not QLoRA.** QLoRA exists to fit models that do not otherwise fit. At 0.36–1.2 B in bf16 on a
16 GB T4, plain LoRA fits with room to spare, trains faster, and avoids NF4 quantisation error during
training. Reaching for QLoRA here is cargo-culting. (If you are restricted to a small local GPU, QLoRA
on M3 only is a reasonable exception — document it, since it then differs from M1/M2's recipe.)

Expected wall-clock per model on a T4 with Unsloth: **20–45 min** for ~1,900 examples × 3 epochs. All
three models train in an afternoon.

---

## 3. Fine-tuning recipe (identical across M1–M3)

### 3.1 Hyperparameters

| Parameter | Value | Reasoning |
|---|---|---|
| Method | LoRA, bf16 | see above |
| `r` | 16 | ample for a narrow structured-output task |
| `lora_alpha` | 32 | 2× r, standard |
| `lora_dropout` | 0.05 | small dataset, mild regularisation |
| Target modules | `q,k,v,o,gate,up,down_proj` | all linear layers; attention-only underperforms on format learning |
| LR | 2e-4 | standard LoRA band |
| Schedule | cosine, 3% warmup | |
| Epochs | 3 | 4–5 if val exact-match still climbing; **select by val, not by epoch count** |
| Batch | 8 × grad_accum 4 = **32 effective** | |
| `max_seq_len` | 512 | transcripts are short; longer wastes compute |
| **Loss masking** | **completion only** | **Critical.** Loss on the prompt teaches the model to generate transcripts. Unsloth: `train_on_responses_only`. TRL: `DataCollatorForCompletionOnlyLM`. |
| Packing | **off** | sequences are short and packing corrupts completion masking |
| Seed | 3407, fixed | |
| Eval | every 50 steps on `val.jsonl`, keep best exact-match | |

### 3.2 Prompt construction

Each model's **own** chat template, applied via `tokenizer.apply_chat_template`. Do not hand-write the
special tokens — Qwen (ChatML), SmolLM2, and Llama-3.2 all differ, and a mismatch produces a model that
trains fine and emits garbage at inference.

```
system:  Convert the operator command to a JSON drone command.     # short & fixed, or omit entirely
user:    {transcript}
assistant: {target}                                                 # ← loss here only
```

Keep the system prompt **short and identical across models**, or drop it entirely. It is prefilled on
every call in production; every token in it is recurring latency (audit C-1). A fine-tuned model does not
need the schema described to it — that is what the fine-tune bought you. Prefer **no system prompt at
all** and verify on val that accuracy is unaffected.

### 3.3 The failure mode that will actually bite you

**Chat-template drift between training and inference.** You train with `apply_chat_template`, then run
`llama-cli` without `--chat-template`, and the model sees a raw string it has never seen. Output is
plausible-looking nonsense and it looks like a quantisation bug or a bad fine-tune.

**Guard:** a `test_template_parity.py` that runs the *same 10 prompts* through HF FP16 and through
`llama.cpp` (post-GGUF) and asserts identical output strings. Run it immediately after every conversion.
Ten minutes to write, saves a day of misdiagnosis. Make it a CI step.

### 3.4 Prohibited

No per-model LR/epoch/r tuning, no per-model prompt engineering, no early stopping on test. Any deviation
must be logged in the results table as a footnote. The comparison's validity rests on this.

---

## 4. Quantisation & export

```bash
# 1. merge adapter → fp16 HF checkpoint
python merge_lora.py --base <model> --adapter out/<model>-lora --out out/<model>-merged

# 2. HF → GGUF f16
python llama.cpp/convert_hf_to_gguf.py out/<model>-merged --outtype f16 \
       --outfile gguf/<model>-f16.gguf

# 3. quantise: BOTH levels
llama.cpp/llama-quantize gguf/<model>-f16.gguf gguf/<model>-Q8_0.gguf   Q8_0
llama.cpp/llama-quantize gguf/<model>-f16.gguf gguf/<model>-Q4_K_M.gguf Q4_K_M
```

**Why both Q8_0 and Q4_K_M** — the PDF specifies Q4_K_M only, and at this scale that is likely the wrong
default:

| | 0.5 B fp16 | Q8_0 | Q4_K_M |
|---|---|---|---|
| Size | ~1.0 GB | ~530 MB | ~400 MB |
| Absolute saving Q8→Q4 | — | — | **~130 MB** |

On an 8 GB Pi with ~1 GB total footprint, 130 MB buys nothing, while Q4 weight error on a
structured-output task can cost real exact-match. Running both costs one extra eval pass through an
already-written harness and yields a genuinely interesting, publishable finding: **"at sub-1B scale the
Q4 memory saving does not buy meaningful latency, so Q8_0 is the better edge operating point."** That is
a contribution the PDF currently leaves on the table.

**Quantisation delta table** (6 cells) — report FP16 exact-match minus quantised exact-match for each
model × quant. The PDF never measures this, and it is exactly the kind of thing a jury asks about.

**Conversion gotchas:** BPE tokeniser conversion occasionally needs an explicit vocab type for
Llama/SmolLM2; verify `special_tokens_map.json` and the EOS token survive conversion (a wrong EOS ⇒ the
model never stops); confirm the GGUF metadata reports the expected architecture and context length.

---

## 5. Evaluation

### 5.1 Metric ladder

The PDF collapses several distinct things into "F1 ≥ 0.88". Separate them — each answers a different
question, and the ladder structure is itself a good thesis figure.

| # | Metric | Definition | Answers |
|---|---|---|---|
| **E1** | **Schema validity** | % parsing as valid JSON *and* passing the Pydantic validator | With GBNF this is **100% by construction** — report it as a *structural guarantee*, not an achievement (audit B-5). Its real use: comparing **grammar-off** vs **grammar-on** to quantify what GBNF buys. |
| **E2** | **Intent accuracy / macro-F1** | 10-way classification over the `intent` field | Directly comparable to Prof. Khaldi's original framing and to encoder baselines. |
| **E3** | **Slot-F1** | micro-F1 over `(key, value)` pairs; floats equal within ±0.05 | Partial credit — right intent, one wrong number. |
| **E4** | **Exact Match (EM)** | full object identical after canonicalisation (key order, float rounding) | **The headline metric.** This is what "the command was understood" means. |
| **E5** | **Safe-failure rate** | % of *wrong* predictions that resolve to `unknown`/`HOVER` rather than a wrong action | A safety metric, and a differentiator no cited work reports. A model that says "I don't know" beats one that confidently lands the swarm. |
| **E6** | **CRR** (end-to-end) | % of spoken utterances producing the correct validated command, audio → JSON | RQ2. Golden set only. |
| **E7** | **WER** | Whisper transcript vs. human reference | Isolates STT error from NLU error — lets you attribute E6 failures correctly. |

Canonicalisation for E4 must be defined in code once (`canon.py`) and used by every consumer: sort keys,
round floats to 2 dp, normalise `ids` order, treat absent and empty `ids` as equal.

**Report E2 and E4 side by side.** The gap between them is the slot-filling difficulty, and it is one of
the more interesting numbers in the thesis.

### 5.2 Accuracy harness — two surfaces, do not conflate

| Surface | Where | Models | Purpose |
|---|---|---|---|
| **A — FP16 reference** | GPU, HF `generate` | merged fp16 | config selection, upper bound |
| **B — deployed artefact** | **Pi 5, `llama.cpp` + GBNF** | Q8_0 & Q4_K_M | **all reported accuracy numbers** |

Accuracy claimed from surface A while latency is measured on surface B is a very common and very
catchable error. Every headline number comes from **B**. Surface A appears only in the quantisation-delta
column.

### 5.3 Latency / RAM / thermal harness (Pi 5 only)

**Protocol:**
- 10-minute warm-up at representative load before any timed run; steady-state is the headline, cold-start
  goes in an appendix (audit C-4).
- Fresh process per model × quant. Drop page cache between runs. **Never two models resident at once.**
- `swapoff -a` for the duration; state it in the methodology.
- `-t 3` threads, core 3 left for the audio callback.
- 200 trials per configuration, inputs drawn from `test_golden.jsonl` (real transcripts, real length
  distribution).

**Recorded per trial:** `prefill_ms`, `decode_ms`, `tok_out`, `tok_per_s`, `vmhwm_kb`,
`temp_c`, `throttled_flags`, `grammar_on`, plus the E1–E5 outcome. One CSV row per trial — every table
and figure in the thesis derives from this one file.

**Reported:** p50 / p95 / p99 per stage, tok/s, peak RSS (`VmHWM`), on-disk size, % trials with a
non-zero throttle flag.

### 5.4 Statistics (kept deliberately small — audit D-7)

- **Model comparison:** **McNemar's test** on paired correct/incorrect vectors over the same test set.
  This is the correct test for two classifiers evaluated on identical items, and it is ~5 lines of
  `scipy.stats`. Three pairwise comparisons ⇒ Bonferroni α = 0.0167.
- **SNR sweep:** one-way ANOVA on CRR across the 5 SNR levels + Tukey HSD. Arcsine-transform CRR
  proportions first (as the PDF correctly specifies).
- **Formations:** one-way ANOVA across the 3 formations, trials as replicates — **not** the PDF's
  mis-specified two-way (audit B-2).
- **Seeds:** 1 seed for all three models to keep the comparison affordable; **3 seeds for the winner
  only**, reported as mean ± sd. State the single-seed limitation plainly rather than implying
  robustness you did not measure.
- **Dropped:** η², the two-way ANOVA, and CIs on a CT sample containing ∞ (audit B-3).

---

## 6. Results tables to produce (these are the thesis)

**Table 1 — Model comparison (the core RQ1 result).** One row per model × quant (6 rows), plus 3 base
zero-shot rows for the before/after contrast.

| Model | Quant | Size | Intent-F1 (E2) | Slot-F1 (E3) | **EM (E4)** | Safe-fail (E5) | p50 / p95 ms | tok/s | Peak RSS |
|---|---|---|---|---|---|---|---|---|---|

**Table 2 — Quantisation delta.** FP16 EM − quantised EM, per model × quant. Answers "what did
quantisation cost?"

**Table 3 — Grammar ablation.** Grammar-on vs grammar-off for the winning model: schema validity (E1),
EM (E4), and decode latency. Quantifies GBNF's benefit *and* its token-time overhead — the honest version
of the PDF's claim.

**Table 4 — E2E on the golden set.** CRR (E6), WER (E7), full stage-wise latency breakdown, per SNR
level. Answers RQ2 and RQ3.

**Figure 1 — Pareto plot.** EM vs p95 latency, marker size = peak RSS, one point per model × quant, with
the ≤2.5 s target as a vertical line. This single figure is the visual answer to RQ1 and belongs on the
defence slide.

**Table 5 — Baseline positioning.** Your results next to Lim et al. [1], with an explicit "not directly
comparable" column noting the differences (fine-tuned vs zero-shot, 5 drones vs 1, Pi CPU vs RTX 3080Ti,
grammar-constrained vs temperature-constrained). Claiming a clean win over a different experimental setup
invites attack; naming the differences yourself pre-empts it and reads as rigour.

---

## 7. Repo layout

```
data/           raw_pairs, train/val/test_synth/test_golden/test_ood .jsonl, audio/, wakeword/
schema/         schema.py (Pydantic), cmd.gbnf, canon.py, test_grammar.py, test_template_parity.py
finetune/       train_lora.py, merge_lora.py, configs/{m1,m2,m3}.yaml
gguf/           <model>-{f16,Q8_0,Q4_K_M}.gguf
eval/           eval_accuracy.py (surface A|B), bench_latency.py (Pi), stats.py, plots.py
runtime/        audio_in.py, vad.py, stt.py, nlu.py, validator.py, bus.py, state_machine.py
swarm/          env.py (abstract), env_numpy.py, env_pyflyt.py, boids.py, formations.py, apf.py
results/        *.csv  ← every table and figure derives from these; commit them
docs/           01_feasibility_audit.md, 02_dataset_plan.md, 03_model_pipeline.md, PRD.md
```

**Two rules that pay for themselves:** commit the results CSVs (so a plot can always be regenerated and
you can prove provenance at the viva), and pin every dependency on D1 (`requirements.txt`, PyFlyt version,
`llama.cpp` commit SHA) — the PDF is right that a mid-project PyFlyt upgrade would invalidate the SIL
trials.
