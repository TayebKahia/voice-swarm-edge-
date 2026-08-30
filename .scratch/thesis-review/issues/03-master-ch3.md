# Issue 03: master-ch3

Status: resolved
Blocked by: 02
Chapter: thesis/master/ch3_method.tex
Script: tools/review/master_ch3.py
Report: .scratch/thesis-review/reports/master_ch3.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_ch3.py
```

## Agents

- **Reproducibility agent** -- D3 (UNTRACED rows only) and D10a: could an outsider rerun Method from
  this chapter alone? Every named script is checked for existence by the script; this agent checks
  it is the one that actually ran.
- **Argument agent** -- D1, D2, D4, D6. Focus: l.330 calls A - B "Contribution C3" while Ch1 defines
  C3 as the harness; the three-layer "guarantee" (l.40); the Table 3 hand-offs to the Ingénieur.
- **Citation agent** -- D5 (18 citations).
- **Presentation agent** -- D7, D8, D9, D11, D12, including the clean build (tab:metrics is an xltabular:
  grep the PDF for its last row, "Convergence").
- **Verifier.**

## What the script establishes (baseline: 16 FAIL, 43 WARN, 98 PASS; 15 of the FAILs are D11)

- The grammar listing is `schema/cmd.gbnf` verbatim; the ten intents are the grammar's ten.
- Every LoRA setting matches all four `train/configs/*.yaml`.
- Dataset sizes within 5% of `data/*.jsonl`; the 4.0-day interval and zero disagreements
  recomputed from the annotation seal and pass-2 timestamps; 514 / 494 = 4.0%.
- NFR targets in tab:requirements match prd.md Table 12 on numbers and bound direction.

## Seeded findings

- **FAIL**: `FA` = Formation accuracy (l.466) but `\gls{fa}` = False Acceptance in
  `shared/acronyms.tex`. One of them needs a new abbreviation.
- `Table~19` (l.105) and `Table~18` (l.331) hand-typed -- use `\ref{tab:grammar-ablation}`,
  `\ref{tab:quantisation-delta}`.
- NFR-9a "Measured by: Exp-1, Exp-2" vs prd.md "Exp-1" -- the chapter text justifies Exp-2; decide
  whether prd.md or the table changes.
- "close to a full second" (l.36): 22 tokens is 0.79 s at the measured 27.93 tok/s, 1.10 s at the floor.
- **D11**: Exp-0 to Exp-4 used ~50x, never defined; "triaged" x5, "spike-era", "the build
  schedule this project executed against", "the project specification", "escalation rule".
- Outside the chapter: `data/dataset_card.md` says "a two-day interval" beside its own 4.0-day table.

## Comments

### 2026-09-23 -- review, verified findings (awaiting the author's decisions)

**Script triage.** Baseline run: 16 FAIL, 43 WARN, 99 PASS. Every FAIL is a chapter error (13 D11
words/codes, the FA clash). Two script errors were found and fixed in the script (expected values
untouched):
- `lib.py` INTERNAL matched multi-word terms on a single space only, so "project specification"
  broken across l.485-486 was missed. Now `\s+`; the matched text is whitespace-collapsed so the
  report row does not break. No other chapter's counts change.
- `master_ch3.py` passed "taskset pinning is in the harness" whenever the word `taskset` appeared in
  eval/exp1.py, so the invalid command at l.462 could never FAIL. It now reads CORES/THREADS from the
  harness and requires the prose's `\texttt{taskset ...}` to carry only `-c <cores>`.
After both: **18 FAIL, 43 WARN, 98 PASS**; selftest passes. `master_ch1.py:54` also anchors on the
l.462 string and will need its anchor moved when l.462 is fixed.

**Agents:** reproducibility (D3 trace rows, D10a), argument (D1, D2, D4, D6), citation (D5, 18 rows),
presentation (D7-D9, D11, D12; clean build, 0 errors, 0 overfull boxes, "Convergence" row present on
p.30 inside Table 3.3). 36 BLOCKER/MAJOR findings after de-duplication went to the verifier:
29 CONFIRMED, 7 PARTLY, 0 REFUTED.

| # | Sev | Line | Finding | Verifier | Proposed fix |
|---|---|---|---|---|---|
| V1 | BLOCKER | 105, 331 | "Table~19" / "Table~18" are prd numbers; compiled they are 4.6 and 4.5 | CONFIRMED (aux) | `Table~\ref{tab:grammar-ablation}`, `Table~\ref{tab:quantisation-delta}` |
| V2 | BLOCKER | 327-330 | Surface B "run on the target Raspberry Pi 5" and the source of "every headline accuracy figure": it is scored on the workstation (surface_b.py:9-12; l.389-392 says so), and the family comparison + zero-shot rows come from Surface A | CONFIRMED | Deployed surface = quantised GGUF under llama.cpp + GBNF; accuracy scored on the workstation, timing on the Pi; family comparison from the reference surface |
| V3 | BLOCKER | 325-326 | Surface A "fp16 merged model run on the workstation": it ran on the Kaggle T4, unmerged PEFT model in memory (notebook l.661-700); contradicts l.319-320 | CONFIRMED | "fine-tuned fp16 model (base + adapter) decoded under transformers on the Kaggle T4, without a grammar"; same fix at Ch4 l.198-199 |
| V4 | BLOCKER | 325, 333-335 | "Three things change": for Llama-3.2-1B also the checkpoint (A = epoch 3 in memory, B = epoch-2 adapter saved on strict improvement; val EM tied 0.900); cap 64 vs 96 and batch-32 vs one slot also differ | CONFIRMED (cap inconsequential for gold) | Declare the Llama checkpoint difference and the decoding differences (or re-score A from the saved adapter); Ch4 l.212-214 too |
| V5 | BLOCKER | 389-392 | CRR listed as hardware-independent and run on the workstation: whisper.cpp differs x86/ARM (2-6 items per noisy condition, 5 dB 0.485 vs 0.495); the Pi run is of record | CONFIRMED | Restrict to text-input metrics (bit-identical 200/200); CRR measured on the board |
| V6 | BLOCKER | 174, 423 | Promise Ch4 reports the SNR sweep and the EM-CRR gap; both are the Ingénieur's (Ch4 l.16, 59-62) | CONFIRMED | Point both at the \emph{Mémoire d'Ingénieur} |
| V7 | BLOCKER | 265-267 | "sufficient on its own to bring a 0.36-1.2 B model to convergence" + \cite{lora}: SmolLM2 and Danube3 still improving at epoch 3 (Ch4 l.168-171) | CONFIRMED | Keep the cite on the mechanism; state two of four had not converged under the fixed 3-epoch budget; l.224 "attributable to the model under an identical budget" |
| V8 | BLOCKER | 47-49 | Grammar "generated directly from the schema so the two cannot drift apart": hand-transcribed (cmd.gbnf:4), drift recorded | CONFIRMED | "written from the schema and held to it by the grammar test suite and the conformance assert, which parses this file itself" |
| V9 | BLOCKER | 429-430, 442-443 | "one absent from this table does not appear in either": peak RSS, throttle proportion, WER percentile/bootstrap CI (Ch4), false accepts/h, false rejects, recovery latency, collisions (Ingénieur) are absent | CONFIRMED | Add rows for RSS, throttle proportion, WER position; rescope the sentence to "every metric this document reports and every accuracy metric the Ingénieur reuses" |
| V10 | BLOCKER | 141, 142, 205 | "passed through openWakeWord's own training pipeline" and wake_neg "Ambient speech, podcasts, room noise" are prd design text: corpus built in-house (wake_corpus.py), sklearn head over openWakeWord's frozen front end; negatives LibriSpeech 1,936 + Speech Commands 2,384 + 720 near-miss, no podcasts | CONFIRMED | Describe what the manifest records; cite LibriSpeech (new entry) and `speechcmd` (in bib, uncited) |
| V11 | BLOCKER | 294-295 | Ampere "two generations later" than Turing: it is the next one | CONFIRMED | "the following architecture"; cite NVIDIA's compute-capability table |
| V12 | BLOCKER | 462 | `taskset -c 1-3 -t 3`: taskset has no `-t`; that is llama-server's thread flag (script FAIL) | CONFIRMED | "`taskset -c 1-3`, llama-server `-t 3`" |
| V13 | BLOCKER | 162-164 | "training and validation audio ... four signal-to-noise levels": only 872/1,940 train rows round-tripped, at 20/10/5 dB; val and test_synth are clean text, no audio; four levels are Exp-3's sweep | CONFIRMED (recounted) | "Half the training rows keep the clean transcript; 872 are replaced by the whisper.cpp transcript of Piper audio at 20, 10 or 5 dB, 88 carry injected perturbations; validation and test_synth are clean" |
| V14 | BLOCKER | 137-138 | test_synth "the McNemar sample": confirmatory families run on test_golden (mcnemar.csv); test_golden's Role omits its role as the benchmark's split of record | CONFIRMED | test_golden: benchmark exact match of record + confirmatory McNemar; test_synth: descriptive second split (240 items) |
| V16 | BLOCKER (up) | 353-365 | test_template_parity.py named as the gate that renders both templates and re-aligns; that is check_parity_gguf.py, added 22 Sep after the 19 Sep Surface B run, Q4_K_M only | CONFIRMED | Name both halves; replace "after every GGUF conversion" with what ran and when (template half added after the first sweep, re-confirmed all three) |
| V15 | MAJOR | 32-38 | 40/18 tokens is a prd estimate; "close to a full second", "single-digit margin" (Qwen only; SmolLM2 40.63, Llama 14.53) and "second-largest saving" unsupported | PARTLY (result depends on what "every field present" means: 19.6 vs 16.0 intent-nulls, 53.3 vs 16.0 all-schema-nulls) | Measure one stated case over the 200 golden labels and report it; delete "second-largest" |
| V17 | MAJOR | 114-116 | "phrasings are then elicited": they come from deterministic expansion of a frame bank/lexicon authored by the AI coding agent (surface_forms.py:8-12), seed 42; "eight per label" is right | PARTLY | Disclose the mechanism and the authorship of the lexicon |
| V18 | MAJOR | whole | Absent from the document: software versions (llama.cpp b10863, PEFT 0.19.1, whisper.cpp 52a939a, converter unpinned, transformers/torch), system prompt, n_predict 96 / ctx 1024 / one slot, Piper voices, noise seed, true val/test sizes 240, code/data release | PARTLY (Pi hardware, cooler, governor, warm-up, 60 trials are stated elsewhere) | An "Environment and artefacts" paragraph or table; pin the converter commit |
| V19 | MAJOR | 330 | "A - B is Contribution C3": Ch1 l.117-124 defines C3 as the harness that measures it | CONFIRMED | "the accuracy cost ... that the harness of C3 measures"; Ch4 l.198 too |
| V20 | MAJOR | 238-240 | "separable in this one": one pair estimates family at ~0.5 B; the size span's endpoints are two other families; control unconverged, system prompt folded, reference surface only | CONFIRMED | Rescope (argument agent's wording #8); soften Ch1 l.137 and Ch4 l.150-166 |
| V21 | MAJOR | 9-11, 382-384 | "frozen ... on the project's first development day" / "before any data existed": idlist amended after the template families (63df858, tag schema-v1.1); three metric rows defined from the harness | PARTLY ("before bulk generation" holds) | "fixed before the synthetic corpus was generated and amended once, to bound the identifier list"; l.382 "before any result existed" |
| V22 | MAJOR | 166-169 | Golden set "different in kind": its transcripts are generator output from the test_synth families; only the audio differs | CONFIRMED | Say so, and that only test_ood probes phrasings outside the generator |
| V23 | MAJOR | 421-423 | EM-CRR gap "attributable to a single cause -- the speech-recognition stage": endpointing splits 22 of 62 clean failures; CRR 0.690/0.730 by scoring rule | CONFIRMED (same items: holds) | "the audio front end -- endpointing and ASR -- under the stated scoring rule" |
| V24 | MAJOR | 177-180 | "speaker generalisation is recovered ... by Exp-0": it characterises WER spread (Ch4: "indicative", no pass/fail) | CONFIRMED | "characterised"; state the parser is text-only; no end-to-end transfer claim |
| V25 | MAJOR | 477-480, 501 | NFR-9a "Measured by: Exp-1, Exp-2" / "only the full-stack measurement can confirm one": no full-stack memory measurement exists (exp2.csv has no RSS); Ch4 l.315 same error | CONFIRMED | **Change the table, not prd.md**: LM-process lower bound only; say the full-stack figure was not measured, so the ceiling is not confirmed; fix Ch4 l.315 |
| V26 | MAJOR | §3.5 | Selection rule, the two McNemar families (Bonferroni alpha = 0.0167, exact below 25 discordant pairs) and the zero-shot baseline are treated as pre-declared by Ch4 l.6, 255, 291 but stated nowhere before | CONFIRMED | New paragraph "Selection rule and statistical plan" in §3.5 |
| V27 | MAJOR | 102-104 | "holds by construction on any input" needs the cap condition Ch2 hands to this section: longest grammar string 90 chars < 96-token cap | CONFIRMED | Add the two-sentence bound after l.100 |
| V28 | MAJOR | 96, 129, 172, 399-401, 472, 485, 487; + 9, 320, 258 | Project-internal words (script FAILs) plus "first development day", "environment gate", "the bf16 specification" | PARTLY (l.245, 291, 327, 341, 389 are permitted patterns) | Presentation agent's rewordings #6-#14 |
| V29 | MAJOR | ~90 uses | Exp-N / NFR IDs / Surface A/B / Branch A/B per issue 00; also Ch4 (Exp 13, NFR 22), Ch5 (NFR 5), generated/*.tex captions (Exp 8, NFR 12) | CONFIRMED | Names per issue 00; tab:requirements without ID column (named criteria); tab:metrics "Used in" -> "Reported in" sections; captions via eval/tables.py. Spans Ch3-Ch5 |
| V31 | MAJOR | 371-373 | "because SentencePiece merge ranking is not unique across implementations": uncited and never isolated (the unpinned converter is an open alternative) | CONFIRMED | Report the observation; "the cause was not isolated" |
| V32 | MAJOR | 306 | "Training in fp16 on a GPU is not bit-reproducible" implies precision is the cause; uncited (Ch4 l.180 repeats) | PARTLY | "GPU training is not bit-reproducible across session instances" + PyTorch reproducibility notes |
| V33 | MAJOR | 319-320, 326, 347 | transformers, PEFT, PyTorch named, not in the bib, cited nowhere | CONFIRMED | Add Wolf et al. 2020, PEFT (Mangrulkar et al. 2022), PyTorch |
| V34 | MAJOR | 218-219 | "a uniform draw over the corpus is 39% US English": it is 959/2,448 accent-labelled rows of the 17.0 English test split | CONFIRMED | Rescope the sentence; keep \cite{commonvoice}, add the 17.0 release and mirror as a dataset reference |
| V35 | MAJOR | 141, 211 | RIR corpus (MIT survey, CC BY 4.0 per the card) used, uncited | CONFIRMED | Add Traer & McDermott 2016 |
| V30 | MINOR (down) | 466-467 | "Formation accuracy (FA)" vs \newacronym{fa}{FA}{false acceptance}; no \gls{fa} anywhere | CONFIRMED | No abbreviation: "formation accuracy" in both rows |
| V36 | MINOR (down) | bib | `piper` url is the archived rhasspy repo; installed piper-tts 1.8.0 is OHF-Voice/piper1-gpl | CONFIRMED | url + version |
| V37 | lead | tab:lora | "effective batch 16": notebook says "GPU T4 x2"; two visible GPUs would give 32 under DataParallel | UNDETERMINED | Check the Kaggle session log (steps/epoch 122 vs 61) before touching the table |

**Verifier's new leads** (not yet reviewed): generated captions carry project-internal wording
(thermal_headroom.tex "the hardware specification declares", exp2_latency_budget.tex "prd 4.7",
"Table 7 pinning"); l.315-317 says three adapters were merged and converted, but
danube3 f16 GGUF exists (all four converted, only Danube's quantisation withheld); Ch2 working copy
l.106 "a grammar compiled from the same schema" (same issue as V8 if it describes this system).

**MINOR/NIT, not verified** (from the agents; applied with the fixes unless you say otherwise):
\gls at every acronym (JSON, GBNF, GGUF, LoRA, TTS, UAV, SNR, RMS, GPU, SLM, EM, CRR, WER; drop "GGML
BNF"); the headings (#45 of the presentation agent: "The decoding grammar.", "The parameter-matched
control.", "Adaptation method.", "Training precision.", "Training sessions.", "Reference and deployed
surfaces.", "Exclusion of the control model.", "Stage latency allowances."); rhetorical set-ups
(l.32, 92, 196-200, 342-344, 363-365, 382-384); "guarantee" (l.40), "impossible" (l.426), "always
reported" (l.502); 45 sentences over 40 words (worst l.95, 170, 208, 285, 430); tense (past for
executed steps); no chapter introduction and no hand-off (D1); "full precision" is fp16 (l.269);
"compiled once" is per request (l.48); ESC-50 is split by fold, not 70/30 (l.212); "91.0 is a
legal yaw" -- yaw wraps at +-180, use an altitude (l.88); "four axes" lists five (l.155-157);
test_ood is 150 text items, no audio (l.139); Danube's folded system prompt belongs in the recipe
(l.238); the date re-alignment hides a one-token train/serve difference (l.360-363); "perplexity
delta" vs Ch2's perplexity + zero-shot (l.344); NFR-13/NFR-15 rows duplicate the Ingénieur's
table and NFR-15 drops "aggregate over both classes"; the latency-budget table sits in Ch3 where prd
Table 3 says Ch4; " -- " vs " --- ", fp16/f16/FP16, "HuggingFace"; bib: add years/versions to the
tool entries, qlora -> @inproceedings NeurIPS 2023; licences inline (l.183).

**Decisions needed from the author**
1. Each row above: fix, or keep with a reason.
2. Scope: V2-V4, V19, V20, V25, V29, V32 require the same change in Ch4 (and V29 in Ch5 and
   eval/tables.py). Fix them in this issue, or open an issue-04 note?
3. V25 / seeded NFR-9a: the recommendation is to change the table, not prd.md.
4. V37: can you check the Kaggle session log for the number of GPUs / steps per epoch?
5. Outside the chapter: `data/dataset_card.md:328` "a two-day interval" -> 4.0 days (and the
   openWakeWord / podcasts wording at dataset_card.md:98).
6. Order: issue 02 is still uncommitted (Ch2, references.bib, lib.py, master_ch2.py, selftest.py).
   This review's lib.py change sits on top of it in the same file, so issue 02 should be approved
   and committed before this one's tools/review/ commit.

### 2026-09-23 -- author's decisions and resolution

The author chose: fix everything as proposed (BLOCKER/MAJOR and the MINOR/NIT list), with these
answers to the open questions:
- (a) V37: Kaggle ran "GPU T4 x2". The notebook `.cuda()`s the model to device 0 with no
  device_map and runs Trainer in one process, so with two visible GPUs Trainer wraps it in
  DataParallel: 4 per device x 2 x accumulation 4 = **effective batch 32**, not 16. tab:lora and
  the precision paragraph now say two T4s and 32. (Inferred from the code path plus the
  accelerator; a Kaggle log showing ~61 optimizer steps per epoch would confirm it directly.)
- (b) V17: do not mention AI assistance. The chapter now describes the mechanism only --
  phrasings "produced by deterministic expansion of a committed frame bank and lexicon
  (data/surface_forms.py) under a fixed seed" -- and says nothing about who wrote the lexicon.
- (c) V4: declare the Llama checkpoint difference (reference surface epoch 3, deployed epoch 2).
- (d) Ch4 is under review in another session: **Ch4, Ch5 and eval/tables.py were not edited
  here.** The matching changes are handed to issue 04 below.
- (e) V25: the table changes, not prd.md (memory ceiling met for the language-model process only).
- (f) data/dataset_card.md fixed: "two-day" -> 4.0-day; the component table (design-era sizes,
  "three sessions", openWakeWord pipeline, podcasts) now matches what was built.

Beyond the listed fixes:
- V15 needed a measurement, not a rewording: new `eval/wire_format_tokens.py` ->
  `results/wire_format_tokens.md` (golden labels, each deployed tokeniser). Qwen2.5: 16.0 tokens
  in the wire format, 19.6 with intent nulls, 53.3 with all schema nulls; 0.13 s / 1.33 s at
  27.93 tok/s. The chapter reports both counterfactuals; "second-largest saving" is gone.
- Ch1 l.136-137 "a parameter-matched control that separates model family from model size" ->
  "measures a model-family difference at fixed size" (V20 consistency; no other session on Ch1).
- tab:requirements has no ID column (issue 00): named criteria; NFR-13 and NFR-15 rows dropped
  (the Ingénieur's; NFR-15 had also lost "aggregate over both classes"); NFR-9b added.
- tab:metrics: "Used in" -> "Reported in" (Ch4 sections, dagger for the Ingénieur); rows added
  for peak resident memory, throttle proportion and speaker position (V9).
- New paragraphs: chapter introduction and hand-off (D1), software environment (V18), selection
  rule and statistical plan (V26), the 90-char / 96-token bound (V27).
- references.bib: +transformers, peft, pytorch, pytorchrepro, nvidiacc, nvidiaampere,
  llama32card, commonvoice17, librispeech, traer2016 (DOIs checked on Crossref); piper -> the
  piper1-gpl codebase actually installed (1.8.0); oww/whispercpp versions; qlora -> NeurIPS 2023.
- Kept, with reason: the latency-budget table stays in Ch3 (prd Table 3 says Ch4; moving it
  touches Ch4, which the other session owns -- issue 04 may move it).
- Not done, by the author's decision: no code/data release location in the chapter. The
  repository URL stays out for now; revisit before submission (an examiner will ask where the
  code and data are).

**Scripts** (script errors only; no expected value changed to match prose):
- lib.py: INTERNAL across line breaks (above); `requirement_table_check` gains `row_ids` /
  `source_names` so a table of named criteria is still compared to the same prd rows; `gist`
  ignores codes, so "an RQ1 result" no longer reads as the number 1.
- master_ch3.py: taskset check against the harness (above); the longest grammar string is
  computed from schema/cmd.gbnf and checked against MAX_TOKENS; the wire-format numbers, split
  sizes (exact now), 872/88 round-trip variants and SNR levels, and the wake_neg sources are
  recomputed from results/, data/*.jsonl and the wake manifest; anchors follow the new wording.
- master_ch1.py: its cross-check of Ch3's pinning string reads CORES from eval/exp1.py.
- selftest passes.

**Final state: 0 FAIL, 3 WARN, 118 PASS.** WARNs justified:
- `budget` "Language-model stages combined 1,350 ms" is not a prd Table 6 row: it is the sum of
  two rows, recomputed by the claim check (PASS).
- `acronym` LoRA l.250: the section title "The LoRA recipe" is the prd §3.1 outline title; headings
  stay plain text (no \gls in the TOC).
- `acronym` JSON l.462: inside the verbatim system prompt, which must be quoted exactly.
Clean build of the Master: 0 errors, no undefined citations, 0 overfull boxes; only the pending
chap:conclusion. "Convergence" is the last row of Table 3.3 in the PDF.

### For issue 04 (Ch4) -- matching changes Ch3 now depends on

Ch3 no longer defines NFR IDs, Exp codes or Surface A/B, so Ch4/Ch5's uses of them are now
undefined (the Ch4/Ch5 scripts' code checks will say so). Names to use, as in Ch3:
- Experiments: speaker-sensitivity experiment (Exp-0), multi-model benchmark (Exp-1), latency
  experiment (Exp-2), acoustic-robustness experiment (Exp-3), formation-control experiment (Exp-4).
- Criteria (tab:requirements first column): End-to-end latency (NFR-2), Exact-match threshold
  (NFR-4), Intent F1 (NFR-5), Schema validity (NFR-6), Clean-audio recognition (NFR-7),
  Recognition in noise (NFR-8), Safe failure (NFR-9), Memory ceiling (NFR-9a), Memory per
  configuration (NFR-9b), Throttling (NFR-10), Speaker sensitivity (NFR-11), False commands (NFR-18).
- Surfaces: reference surface (A), deployed surface (B); reflex path / parse path (Branch A/B).
Ch4 lines that repeat errors fixed in Ch3:
- l.198-199: Surface A is "FP16 model on the workstation" -> fp16 base + adapter (unmerged) under
  transformers on a Kaggle T4 (V3); l.198 makes the difference "C3" -> what C3's harness measures (V19).
- l.212-214: "three things change" -> add the decoding settings (64 vs 96 cap, batched vs one
  sequence) and Llama's epoch-3 vs epoch-2 checkpoint (V4).
- l.150-166: family/size "separates them" -> family difference at ~0.5 B only; the size span's
  endpoints are two other families (V20).
- l.315: full-stack memory "is Exp-2's measurement" -> no full-stack measurement exists (V25).
- l.180: "half-precision GPU training is not bit-reproducible" -> GPU training is not
  bit-reproducible across sessions, whatever the precision (V32).
- l.97 and generated/thermal_headroom.tex: "the active cooler the hardware specification
  declares", "a configuration this project never declared" (D11); generated/exp2_latency_budget.tex
  "prd 4.7", "Table 7 pinning", "Table 6's line"; captions carry Exp-N / NFR / "Surface A/B" --
  fix in eval/tables.py, not by hand.
- Anything quoting the recipe's batch size: it is 32, not 16.
- Ch5 uses NFR IDs 5x (issue 05).

### 2026-09-24 -- second pass on the rewritten chapter (awaiting the author's decisions)

Why: the first pass reviewed the pre-rewrite text; 1ea2dae changed 860 lines, so the new sentences
had never been checked against source. Run: script (unchanged, 0 FAIL / 3 WARN / 118 PASS), one
reviewer (D1-D12 on the diff `369403f..1ea2dae` first, then the whole chapter), one citation agent
(the 10 added and 4 changed bib entries, and old keys attached to new sentences), one verifier on
BLOCKER/MAJOR. IDs are W-numbered so they do not collide with V1-V37.

Confirmed by the reviewer against source (no finding): the 20 ms / 30 dB SNR gate, the random
keyword offset, the speaker/phrase splits, 720 near-misses, 70/10/20 positives, the Q8_0 tokeniser
and template (all `tokenizer.*` GGUF keys hash identically to Q4_K_M -- the text may say so), the
statistical plan's families and tests, the software versions, the system prompt, seed 42, the 90-char
bound, the Common Voice 39% (959/2,448), every tab:metrics "Reported in" ref, "amended once", the
leakage gate. Citations: 0 BLOCKER; `pytorch` and `commonvoice17` (2024) written from memory are
correct; ESC-50 CC BY-NC 3.0 and DREGON "personal, educational and academic use only" are correct.

#### Verified BLOCKER / MAJOR

| # | Sev | Line | Text | Verdict | Problem | Proposed fix |
|---|---|---|---|---|---|---|
| W1 | BLOCKER | 187 | "every slot combination the schema admits" | CONFIRMED | Golden (= test_synth) covers 12 (intent, slot-set) combinations from 12 held-out families; the generator produces 34, the grammar admits 38; `set_param{alt,spacing}` (22 golden items) never occurs in training. Also `data/dataset_card.md:63`. | "...drawn from the 12 template families held out for test_synth: all ten intents, but 12 of the 34 (intent, slot-set) combinations the generator produces, one family per combination; one (set_param with altitude and spacing) never occurs in training." Same in the card. |
| W2 | BLOCKER | 451-452 | "used 60 trials per path" | CONFIRMED | 60 is the planned minimum; the run timed 226 endpointed segments (parse path) and 78 triggers per condition (reflex). The paragraph itself warns against quoting design figures. **Script error:** `master_ch3.py:183` PASSed it against the plan line in STATE.md. | "...timed 226 endpointed segments from the 200 golden utterances on the parse path, and 78 reflex triggers in each of its idle and loaded conditions." Re-anchor the script check on `results/exp2_analysis.md`. |
| W3 | BLOCKER | 523 | false-command: "any intent other than unknown that also survives the validator" | CONFIRMED | `eval/metrics.py:92-94,154-165`: an output the validator rejects falls back to hover, and hover counts. Under the chapter's wording two reported SmolLM2 figures would not reproduce. | "...whose dispatched action -- the output after the validator, where an invalid output falls back to hover -- is anything other than `unknown`; hover counts as a false command." |
| W4 | BLOCKER | 573-575 | selection rule "among those meeting" both constraints | PARTLY (mostly real) | On Ch3's own terms nothing can be shown to meet them (memory ceiling unconfirmable, l.541-544; end-to-end p95 3,122 ms misses). The failure clause is missing; Ch4 applies a rule-out reading. | "...among configurations not ruled out by the end-to-end latency budget or the memory ceiling (on the evidence available each can only rule a configuration out); if none satisfies both, the rule fails openly: the constraint is re-baselined against the measured figure and the re-baselining is reported." |
| W5 | BLOCKER (low impact) | 233-234 | "no public corpus contains the word 'swarm' or a phrase beginning with 'hold'" | CONFIRMED | Common Voice 17.0 test.tsv has "swarm" once and three "Hold..." sentences; LibriSpeech dev-clean has one "HOLD ON TO ME". | "...since neither LibriSpeech nor Speech Commands supplies the confusions that matter to this spotter: short phrases beginning with 'swarm' or 'hold'." |
| W6 | MAJOR | 304-305 | "Qwen2.5-0.5B-Instruct and Llama-3.2-1B-Instruct converged" | CONFIRMED | Only validation EM is logged (no loss). Qwen .8667/.9042/.9125 (still rising, 2 items); only Llama flat (.900/.900). Ch4 l.169-170 repeats it. | "Only Llama-3.2-1B-Instruct's validation EM was unchanged between epochs two and three (0.900); Qwen2.5 still rose by 0.008 (two of 240 items), SmolLM2 by 0.025, H2O-Danube3 by 0.038. No model is shown to have converged." |
| W7 | MAJOR | 203-207 | RIRs "...all of it is mixed by one seeded path, data/mix_noise.py" | PARTLY | Noise part true; mix_noise.py has no RIR code. RIRs are applied only to the wake corpus (`data/wake_corpus.py`); parser audio is not reverberated. | "All noise is mixed by one seeded path, data/mix_noise.py: DREGON and ESC-50 (augmentation partition) for the training round trip, DREGON (evaluation partition) for the SNR sweep. Room impulse responses from the MIT survey are applied only to the wake corpus, by data/wake_corpus.py; the parser's audio is not reverberated." |
| W8 | MAJOR | tab:requirements | "lists every requirement this document uses" | CONFIRMED | The 20 tok/s floor (Ch1 l.27, Ch2 l.30, Ch4 l.334) is not in the table; the 22-token decode it derives from is never stated, and Ch3 states a 16.0-token mean. | Add a row "Throughput floor: >= 20 tok/s on the three inference cores, from a ~22-token decode allowance within 1,100 ms; multi-model benchmark", and one clause: 22 is a design allowance above the measured 16.0 mean. |
| W9 | MAJOR | 434-466 | (absent) | CONFIRMED | The Pi timing protocol is not stated anywhere: `eval/exp1.py` pins cores, enforces the performance governor, swap off, page cache dropped per config, 600 s warm-up (excluded), `cache_prompt=true`; accuracy sweeps and the deployed parser run `cache_prompt=false` (latency experiment: 300 s warm-up); active cooler. | One "Timing protocol" paragraph listing those settings. |
| W10 | MAJOR | 456-466 | (absent) | CONFIRMED | whisper.cpp runs with a fixed 25-word domain prompt (`data/asr.py:33-37`) in the runtime and in building the 872 round-trip rows; Ch4 l.48-55 measures its effect. | "...tiny.en, prompted with a fixed 25-word command vocabulary (data/asr.py), both for the round-trip corpus and at run time." |
| W11 | MINOR (merged) | 183-189 | limitation not sized | PARTLY, duplicate of W1 | W1's wording sizes it. What W1 does not say: the 200 golden items are 12 clusters, while the CIs and McNemar tests treat them as independent. | Optional: one sentence of clustering caveat next to the statistical plan. |

#### MINOR / NIT (reviewer and citation agent; not verifier-checked, per the loop)

| # | Line | Problem | Proposed fix |
|---|---|---|---|
| W12 | 169-171 | Leakage parenthetical overstates: held-out splits are checked against each other for surface form only; test_ood not checked | "family and surface-form isolation of train against validation, test_synth and the golden set, and surface-form isolation of those three against one another" |
| W13 | 142,152,184,213 | Golden recording spanned two days (115 + 85 takes, 17-18 Sep) | "one session over two consecutive days"; "sealed on the day recording was completed" |
| W14 | 442 | "two to six ... per noisy condition" omits clean (4 items) | "two to six of the 200 items per condition, clean audio included" |
| W15 | 463 | 1,024 context is the benchmark; runtime uses 512 (`runtime/parser.py:70`) | add "; the runtime uses a 512-token context" |
| W16 | 529 | prefill/decode are llama-server's reported timings, not wall-clock | "server-reported prefill and decode time" |
| W17 | 527 | WER defined as a distance, aggregation unstated | "word edits summed over utterances divided by total reference words (corpus WER)" |
| W18 | 156 | wake_neg also trains the spotter (3,930/5,040 in train) | "Keyword-spotter training and false-accept measurement" |
| W19 | 141,226,529 | reflex / parse path never defined in the Master | define at l.141 in one clause |
| W20 | 384-386 | attribution assumption ignores the cap/batching/checkpoint differences just listed | "...and that the cap, batching and checkpoint differences contribute nothing" |
| W21 | 334-335, 302-303 | uncited: bf16 pretraining and fp16 range; "narrower adapter would under-fit" | cite `qlora` at l.302; soften or cite l.334 |
| W22 | 285, 575-579 | AdamW, McNemar, Bonferroni named without citation | add Loshchilov & Hutter 2019 and McNemar 1947 to the bib |
| W23 | 379-380 | "this document does not do that anywhere" -- Ch4's section is titled "The quantisation delta" | delete the clause |
| W24 | §3.2 | Ch1's C2 promises a version tag and dataset card; Ch3 never names them | one sentence: frozen at tag dataset-v1.0, documented in the dataset card (no URL) |
| W25 | 491-493 | tab:metrics also defines Ingénieur-only latency/formation/convergence rows | "...reuses, together with its latency, formation-accuracy and convergence definitions" |
| W26 | 575 | McNemar surface unnamed | "Paired deployed-surface predictions (grammar on)" |
| W27 | 350-351 | Danube "stays at fp16 on the reference surface" conflates its fp16 GGUF | "was converted to fp16 GGUF but not quantised, and is reported on the reference surface only" |
| W28 | 153 | test_ood: 12 of 150 are harvested recogniser outputs | "...authored, and recogniser output on noise and silence (12 harvested)" |
| W29 | bib | `commonvoice17` URL now a data-less placeholder | point at the mirror used (fsicoli/common_voice_17_0) |
| W30 | 326 / bib | `nvidiacc` does not say Turing | also cite the T4 product page, or move the cite to after "7.5" |
| W31 | 327-328 | "no bf16 path" -- emulation exists | "no native bf16 path" |
| W32 | bib | `qlora` stale comment, missing pages/doi; `traer2016` missing pages; `whispercpp` missing year | add `pages = {10088--10115}`, `doi = {10.52202/075280-0441}`; `pages = {E7856--E7865}`; `year = {2026}` |
| W33 | 204 / bib | ESC-50 and DREGON licences cited to papers that do not state them | add the repo / dataset-page `url` to `esc50` and `dregon`; "CC BY-NC 3.0" |
| W34 | 340 | pytorchrepro says "not guaranteed", text says "is not" | "is not guaranteed to be bit-reproducible" |
| W35 | 407 | llama.cpp BOS-drop is a code claim cited to the repo root | pin `common/chat.cpp` at 88ada91c in the note, or leave |
| W36 | 22 sentences | over 40 words (list in the reviewer output: l.4-8, 14-17, 19-22, 101-104, 104-106, 114-116, 126-129, 161-165, 171-174, 212-215, 245-248, 252-257, 261-264, 268-271, 301-304, 372-375, 392-395, 450-452, 458-461, 475-477, 496-499, 583-586) | split each as proposed |
| W37 | NITs | "bootstrap 95% CI" by hand (567); "fixes" x3 (257,471,491); "one session against two is the smaller cost" (342); determinism credited to the grammar (436, should be greedy + one slot); "(p95 targets, measured from end of speech)" only true of the e2e row (596); "never evaluated"/"No corpus existed" (240,123); "below 25 ... above it" leaves 25 (578); wire-format: say 19.6 is the relevant counterfactual under a per-intent grammar (40-44); m16: Ch2 l.110 "compiled from the same schema" (issue 02 is closed -- a one-word fix) | as listed |

#### For issue 04 -- additions to the hand-off above
- Ch4 l.9-12: hardware independence stated as a consequence of greedy decoding + grammar, and
  "surfaces" used for workstation vs Pi -> Ch3 establishes it empirically, for the selected
  configuration, on text input only (W-verifier B6).
- Ch4 l.291-322: says end-to-end latency "has not been measured"; the latency experiment measured
  p95 3,122 ms (misses 2,500) and no chapter reports it (W4).
- Ch4 l.169-170: "converged" (W6).
- Ch4 l.126: attributes the prefill distribution to a prompt cache "the protocol deliberately
  enables" -- true of the benchmark, false of the deployed parser (`cache_prompt=false`) (W9).

#### Questions for the author
1. W8: add a throughput row to tab:requirements, or annotate the decode row of the latency-budget
   table?
2. W11: add the clustering caveat (200 items = 12 families) to the statistical plan?
3. W22/W21: add new bib entries (AdamW, McNemar), or cut the uncited sentences?
4. W37-m16: touch Ch2 (closed issue 02) for the one-word "compiled" -> "written" fix?

### 2026-09-24 -- second pass: author's decisions and resolution

Decisions: fix everything as proposed; (1) W8 add the throughput row; (2) W11 add the clustering
caveat; (3) W21/W22 add the bib entries; (4) W37-m16 fix Ch2 l.110.

Applied (W1-W37), with what was checked while fixing:
- W1: 12 of 34 combinations recomputed from the jsonl files; the 96/12/12 family split is now in
  the text. The dataset card's §3 also still described s2/s3 as recorded (320 files); both folders
  are empty, so the card now says 200 files, s2/s3 planned and not recorded.
- W9: the timing protocol is scoped to what the harnesses enforce. Swap off, one model resident
  and page-cache drop are the multi-model benchmark's only (`eval/exp1.py`); `eval/exp2.py`
  enforces the governor but not those. The cooler is stated for the benchmark's run of record
  only (`results/thermal_headroom.md`); nothing records whether it was fitted for the latency
  experiment. The Pi's RAM variant and OS are recorded nowhere, so they are not stated.
- W21: all four base checkpoints are distributed in bf16 (`torch_dtype` in each model's
  config.json; Llama read through an ungated mirror). l.302 now cites `qlora` for all-linear
  adapters.
- W22: `adamw` (Loshchilov & Hutter, ICLR 2019) and `mcnemar1947` (Psychometrika 12(2):153-157,
  Crossref) added. W30: `nvidiat4` (T4 product page, "Based on the new NVIDIA Turing
  architecture"). W35: `llamacppchat` pins `common/chat.cpp` at 88ada91c.
- Q8_0 sentence now states the check that was made: all `tokenizer.*` GGUF fields hash identically
  to Q4_K_M for the three models (gguf-py, re-run while fixing).
- W36: every flagged sentence split; three new ones over 40 words written during the fixes were
  split too.

Script (`tools/review/`): the "60 trials per path" check now reads the executed n from
`results/exp2_analysis.md` (226 parse-path segments, 78 reflex triggers per condition), not
STATE.md's plan line. `requirement_table_check` accepts a criterion mapped to None -- a
requirement derived from another prd table -- and `master_ch3.py` checks the throughput floor's
derivation itself (prd Table 6 decode row: 22 tokens / 1.1 s = 20 tok/s).

Final: 0 FAIL, 4 WARN, 125 PASS; selftest passed; Ch1 and Ch2 scripts unchanged (0 FAIL); clean
Master build in a scratch copy, 0 errors, biber 0 warnings, only `chap:conclusion` undefined.
WARNs: the three justified above (budget sum row, LoRA in the section heading, JSON in the verbatim
system prompt) plus `guaranteed` at the pytorchrepro sentence, which is the hedge W34 asked for
("is not guaranteed to be"), not an absolute.

Not fixed here, for the author:
- Ch1 C2 (l.113-114) says the dataset's "gold labels are sealed under a SHA-256 checksum". What is
  sealed is annotation pass 1 (`annot/annot_pass1.seal.json`, 50 items); the golden labels are
  generator targets frozen under the `dataset-v1.0` tag. Issue 01 is closed -- the wording is the
  author's call.
- The effective batch of 32 is still inferred, not read from a Kaggle log.

### 2026-09-24 -- follow-ups closed

- Batch 32 confirmed: on Kaggle "GPU T4 x2" under transformers 5.0.0 (the version the training
  session logged), `TrainingArguments(per_device_train_batch_size=4)` gives device_count 2,
  n_gpu 2, train_batch_size 8, so 8 x 4 accumulation = 32. Ch3 stands; the stale "effective
  batch 16" comments in train/configs/*.yaml were corrected.
- Training versions: the session that trained the first three models logged transformers 5.0.0,
  torch 2.10.0+cu128, peft 0.19.1; Ch3 now states them. The control's session is still
  unlogged.
- Ch1 C2 "gold labels are sealed" corrected to the annotation pass (author's decision).

### 2026-09-24 -- follow-up from issue 05 (Ch5 review): two Ch3 descriptions corrected

Issue 05's verifier found these two while checking Ch5. Each was checked against `data/` before fixing.
- **ch3:173-176, the 81 `unknown` training pairs.** They were described as "35 authored
  assistant-style queries, and 46 near-miss requests …". Those counts are by `source_variant`, and the
  script checked only the counts, not the kinds. By template family the pairs are:
  - 20 assistant queries (F115);
  - 21 requests for capabilities the schema lacks (F116: 15 authored plus 6 from the hard-negative
    set, e.g. "follow me");
  - 40 lexical near-misses (F117: a command word without a command, e.g. "hold that thought").

  Ch3 now says 20 / 21 / 40.
- **ch3:172-173, "truncated utterances" as a training axis.** The axis is ellipsis
  (`data/surface_forms.py` axis 5, 268 training rows): the verb is dropped and the slots are kept.
  Content-losing fragments (F119) are in `val_synth` only. Ch3 now says "elliptical commands that drop
  the verb and keep the slots (``grid, 3.7 spacing'')".
  - The first example chosen, "ring, ten across", was rejected by the new quote check. Its training
    row carries the round-trip transcript ", bring 10 across,", not the clean text, so it was
    replaced by an example that appears in `train.jsonl` as written.

Script `master_ch3.py`:
- The 35/46 checks by `source_variant` are replaced by per-family checks (20/21/40), plus a check
  that no other family teaches `unknown`.
- A check that every quoted example on these lines is a `data/train.jsonl` transcript.

No expected value was changed to match the prose. Final state: 0 FAIL, 4 WARN (the same four as
before), 132 PASS. The self-test passes. The build has 0 errors.
