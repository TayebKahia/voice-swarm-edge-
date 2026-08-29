# Issue 04: master-ch4

Status: resolved
Blocked by: 03
Chapter: thesis/master/ch4_results.tex
Script: tools/review/master_ch4.py
Report: .scratch/thesis-review/reports/master_ch4.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_ch4.py
```

## Agents

- **Argument / statistics agent** -- D2, D4, D6, D10. Focus: register (Results reports, Ch5
  interprets); "upper bound" (l.14); interpretations with no computed figure behind them
  ("predominantly parameter errors", "two-fifths"); the two McNemar cautions.
- **Citation agent** -- D5 (11 citations).
- **Presentation agent** -- D7, D8, D9, D11, D12: the six `\input{generated/...}` tables and Figure 2
  (vector, caption self-contained), clean build.
- **Verifier.**

## What the script establishes (baseline: 7 FAIL, 17 WARN, 155 PASS; all 7 FAILs are D11, every number is right)

155 claims recomputed from `surface_b*.csv`, `surface_a.csv`, the per-trial rows of
`exp1_cooled.csv` / `exp1.csv` (nearest-rank, half-up rounding), `mcnemar.csv`,
`nfr9_nfr18_abstention.csv` and table16/33 -- every one matches. The selection rule was
re-applied: exactly one configuration (Qwen2.5-0.5B Q4_K_M) meets all six constraints.

## Seeded findings

- "GB" is MiB / 1024 (GiB): Llama's peak RSS is 1,670 MB = 1.67 GB decimal, written 1.63 GB.
  State the unit once or write GiB -- the same convention runs through Table 17.
- fig:pareto is first `\ref`'d in this chapter at l.328, after the float (l.310).

- **D11**: Exp-0/1/2/3 undefined; "the hardware specification", "the project specification",
  "the escalation rule" (l.97, l.141).
- **D12**: 9 lead-in headings are sentences or claims ("NFR-2 has not been measured, and cannot be
  decided here.", "Schema validity is 1.0000 everywhere, ...").

## Comments
### 2026-09-23 -- review round 1 (argument/statistics + citation + presentation + verifier)

Script: 7 FAIL, 16 WARN, 156 PASS. The issue's baseline said 17 WARN / 155 PASS; the uncommitted
issue-02 changes to `lib.py` were in the working tree when this ran. **All 7 FAILs are chapter
errors** (D11): Exp-0/1/2/3 never defined, and "hardware specification" (l.97), "escalation rule"
and "project specification" (l.141). The verifier confirmed none is a false positive.

Script error fixed: the `units` WARN in `master_ch4.py` divided MiB by 1000 and called the result
decimal GB. `peak_rss_mb` is bytes/1024² (`eval/bench.py:334`), so Llama's 1,669.86 MiB is
1.63 GiB = **1.75 GB decimal**, not 1.67. **The seeded finding above has the conversion backwards.**
No expected value changed. Self-test passes.

**Issue 03 is not resolved**, although this issue is blocked by it. About a third of the fixes
below need Ch3 to define something first (marked **[Ch3]**).

Verdict: needs rework in §4.2 and §4.7, fixes elsewhere. Every recomputed number is right. The
defects are in the arguments built on those numbers:
- the selection rule is applied as if the end-to-end latency were unmeasured, yet it has been
  measured and it misses;
- the statistics do not test the quantisation deltas they are said to test;
- the size and family claims go beyond the data;
- the chapter drifts into interpretation in about eight places.

Citations: 11 keys, 10 SUPPORTS, 1 PARTIAL (tam2024), 0 DOES NOT SUPPORT.

Verified BLOCKER/MAJOR (verifier: 22 confirmed, 10 partly, 0 refuted). Severities shown are
after the verifier's correction.

| # | Sev | Line | Finding | Verifier | Proposed fix |
|---|---|---|---|---|---|
| A1 | BLOCKER | 317-328, 291 | "NFR-2 has not been measured": it has been. For the selected Qwen Q4_K_M, cooled, with the shipped parser: E2E p95 **3,122 ms** (n=226) against 2,500, MISSES (`exp2_latency_budget.md`; STATE l.1497-1501 leaves re-baselining to author/supervisor). l.321 "on the Exp-1 evidence alone" silently swaps "satisfying" for "not ruled out". SmolLM2 was never measured end to end | CONFIRMED | One sentence + cross-ref to the Ingénieur: measured 3,122 ms, so no measured configuration satisfies both constraints; rule applied with the latency constraint re-baselined, reported as missed. **Re-baseline is your decision** |
| A2 | MAJOR | 209-210, 273-275 | "§4.6 tests that reading": `mcnemar.csv` tests Q4_K_M vs Q8_0; Table 18 (FP16 vs quantised) is never tested. Verifier reproduced FP16-vs-quantised: 3-0, 2-0, 0-0, 1-0, 12-9, 0-3; all p ≥ 0.25, so the conclusion survives | PARTLY (↓ BLOCKER) | Reword to "tests the related Q4_K_M vs Q8_0 comparison; the FP16-to-quantised differences (one to three items) are not tested", or add an exploratory family to `eval/mcnemar.py` |
| A3 | MAJOR | 150, 76-77, 162-163 | "established that parameter count does not order the results": only on golden, where Qwen>Llama is not significant (l.267 says so). On synth and ood the order follows parameter count (Table 17) | PARTLY (↓ BLOCKER) | Rest the claim on Qwen vs H2O-Danube3 (larger, worse on all splits; golden 15-2 p=.0024, synth 17-1 p=1.4e-4); drop "established" |
| A4 | MAJOR | 106-108 | "The cost of the missing cooler was ... 35.2% to 68.5% of throughput": that is the cooler's gain on the uncooled base. As a cost, the throughput loss is 26.0-40.7% | PARTLY (↓ BLOCKER) | "Fitting the cooler reduced decode p95 by 25.1-41.3% and raised throughput by 35.2-68.5%". The script matched the digits without checking the base |
| A5 | MAJOR | 10-11 vs ch3:327-328 | Ch3 says the Surface-B artefacts run "on the target Pi"; Ch4 and `eval/surface_b.py` say accuracy is scored on the workstation. Ch3 also contradicts itself (ch3:391). No number changes (Pi/workstation parity 0/200) | PARTLY (↓ BLOCKER) | **[Ch3]** fix ch3:327-328; Ch4 is correct |
| A6 | MAJOR | 14, 57-59 | "upper bound on what the deployed pipeline achieves": not a bound. Item 0113 is wrong from text and right from audio; the covered sections include FP16 and grammar-off figures; synth/ood have no audio | CONFIRMED | "measured on reference text, and expected to overstate what the pipeline achieves from audio"; drop "ceilings ... floor", "in flight" |
| A7 | MAJOR | 263-268 | 5 discordant pairs: the smallest two-sided exact p is 0.0625 > α=0.0167, so the test could never reject. It needs ≥ 7 pairs all one way. The caution at l.278 covers only the 1-pair case | CONFIRMED | Add: "with five discordant pairs the smallest attainable p is 0.0625, so no split could reach the corrected α" |
| A8 | MAJOR | 158-166, 151 | "two-fifths of what the full size range buys": the size range (SmolLM2 vs Llama) also crosses families, and no family appears at two sizes, so the ratio is meaningless | CONFIRMED | Keep the matched-size family result (with its McNemar); drop the ratio and "separates them"; move "first-order decision" to Ch5 |
| A9 | MAJOR | 322-326 | Llama eliminated because the STT *budget* is 1,200 ms, but a budget is not a lower bound | CONFIRMED | Use the measured STT minimum from the latency experiment, **1,063 ms** (`exp2_preds/clean.jsonl`), once, with cross-ref. Not the 870 ms from the acoustic experiment (Table 3: Exp-3 is referenced once, in Ch5) |
| A10 | MAJOR | 334 | Qwen "meeting ... NFR-9a": ch3:477-480 says the LM-process RSS can only rule out, never confirm | CONFIRMED | "is not ruled out by the memory ceiling" |
| A11 | MAJOR | 123-131, 333 | Prefill timed with prompt cache ON (`eval/exp1.py:31`); the shipped parser has it OFF (`runtime/parser.py:252`). Shipped prefill+decode p95 is 1,658 ms against the 1,350 ms allowance, so "278 ms to spare" and "meeting the 1,350 ms allowance" hold only for the cached condition | CONFIRMED | Say the timing condition, cite the uncached figure once via the Ingénieur, and restate l.131/l.333 as "under cached prefill" |
| A12 | MAJOR | 6-7, 291 | "fixed in writing before any result existed": the rule appears only in Ch4; Ch3 never states it, and nothing dated shows it predates results | CONFIRMED (merged with P11) | **[Ch3]** state the rule in the protocol; soften "in writing" unless you can point to a dated artefact |
| C1 | MINOR (arguable MAJOR) | 255 | McNemar named, uncited here and in Ch3; no bib entry. SKILL.md:162 ("author names need a key") literally covers it | PARTLY | You verify and add McNemar 1947, *Psychometrika* 12(2):153-157, doi:10.1007/BF02295996; cite at first use (Ch3) |
| P1 | MAJOR | table16 note | "Table 16 positions the author": the PDF numbers it Table 4.1; the note also contains NFR-11 | PARTLY (fix location) | Fix in `eval/exp0.py:249` (not tables.py): "this table" |
| P2 | MAJOR | Figure 4.1 | The in-plot title says "Figure 2 —" and a line label says "Table 6 SLM budget" (they are Figure 4.1 and Table 3.5) | CONFIRMED | `eval/plots.py`: drop `set_title`; label "SLM stage allowance 1,350 ms" |
| P3 | MAJOR | Figure 4.1 | Inset "(Exp-1 scoped to Q4_K_M, Sat-19 triage)"; the figure also shows Exp-1, NFR-2, NFR-4, Surface B | CONFIRMED | `plots.py:213`: "Not measured on the Raspberry Pi 5"; rename the criteria |
| P4 | MAJOR | Figure 4.1 | Rotated line labels overlap the Qwen and Llama annotations and the NFR-4 text; literal backticks on the y-axis | CONFIRMED | Move the labels to the top margin or offset the annotations |
| P5 | MAJOR | table33:19, thermal:21 | `\#\#\#\#` markdown heading and " - " bullets printed literally | CONFIRMED | `eval/tables.py:438`: convert to prose |
| P6 | MAJOR | 120, 314; Table 17; fig; ch3:501; ch5:24,27 | "GB" is GiB everywhere. Llama 1.63 GiB = 1.75 GB. Against a decimal 2.5 GB ceiling, the "35% clear" is 30.0% | CONFIRMED | **Your decision: is the ceiling GB or GiB?** Then either write GiB everywhere (tables, plots, Ch3, Ch4, Ch5), or convert to 0.73/0.59/1.75 GB and 30% |
| P7 | MAJOR | 18-19 | "rendered ... from the measurement CSVs named in its caption": Tables 4.1 and 4.5 name no CSV; 4.6 names only `exp1_cooled.csv`; 4.4 names a train/ file | CONFIRMED | Add the source CSVs in the generators |
| P8 | MAJOR | 97; thermal caption | "the active cooler that the hardware specification declares" (the caption repeats it: `eval/tables.py:505`) | CONFIRMED | "An initial run without active cooling throttled on all 180 scored trials ..."; same in the caption |
| P9 | MAJOR | 99 | "a configuration this project never declared ... not the run of record": Ch3 never describes the board setup (cooler, governor) | CONFIRMED | **[Ch3]** describe the board configuration; then "Because the target configuration includes active cooling, that run is not used for selection" |
| P10 | MAJOR | 141 | "Per the escalation rule fixed in the project specification": ch3:472-473 and the tab:requirements caption say the same, and the rule is never stated in the thesis | CONFIRMED | **[Ch3]** state the re-baselining rule with tab:requirements; Ch4 then points there |
| P12 | MAJOR | ~57 sites | Codes per issue 00: ~38 in prose, ~14 in generated tables, 5 in the figure (Exp-N, NFR-N, Surface A/B). A per-occurrence replacement table exists (presentation report) | CONFIRMED | Apply the issue-00 names. NFR names **[Ch3]**: Ch3's requirements table must carry the named criteria first, and it has no row for the 20 tok/s floor Ch4:334 uses |

Raised by the verifier, not independently verified (I spot-checked N1 and N2):

| # | Sev | Line | Finding | Proposed fix |
|---|---|---|---|---|
| N1 | MAJOR | 315 | "confirming [memory] against the full stack is Exp-2's measurement": `eval/exp2.py` records no memory, and no results file or Ingénieur chapter reports full-stack RSS | "The ceiling is not confirmed on the full stack" (or measure it) |
| N2 | MAJOR | 199; ch3:325-326 | FP16 (Surface A) figures "on the workstation": they were produced on Kaggle (`train/make_kaggle_notebook.py:680-687`; ch3:319-320 keeps torch/peft off the workstation) | "the FP16 model (fine-tuning environment)"; **[Ch3]** same |
| N3 | MAJOR (Ch3) | ch3:386 | "under the grammar for every accuracy figure either document reports": FP16, ablation and zero-shot figures are not | For issue 03 |
| N4 | MINOR→MAJOR? | 83, 89, 133, 313, 317, 330, 341 | Headings as claims; SKILL.md quotes l.317 as its ❌ example | Heading table below |
| N5 | MAJOR (borderline) | 187-193 | Zero-shot EM 0.000 over 590 items: no table and no named source (`train/kaggle_out/surface_a.csv` `A_fp16_zeroshot`), which breaks l.18-20 | Name the source, or add the rows to Table 4.4 |

**Decisions only you can make** (the fixes wait on these): A1 (re-baseline the latency constraint,
and how to word it); P6 (whether the ceiling is GB or GiB); A2 (reword, or add the FP16-vs-quantised test); C1
(add McNemar/Bonferroni entries after checking them); A12 (whether a dated artefact exists for the
pre-registration claim); whether to do issue 03 first (recommended, because A5, A12, P9, P10, P12 and N2
all need Ch3 to define something that Ch4 then points to).

Proposed headings (D12): l.57 "Reference-text ceiling" → better "Reference-text input";
l.83 "Schema validity"; l.89 "Slot-F1 on the abstention split"; l.96 "Thermal state";
l.133 "Abstention"; l.187 "Zero-shot baseline"; l.277 "Interpreting the tests";
l.313 "Memory constraint"; l.317 "End-to-end latency constraint"; l.330 "Ranking and selection";
l.341 "Qualifications to the selection".

MINOR/NIT (not verified, ~60 items; full lists in the three agent reports of this round):
- Citations: tam2024 PARTIAL. It tests JSON-mode and format instructions, not a task grammar, and
  finds that classification is not harmed. Reword l.243-245 to say so. Cite `whisper` alongside
  `whispercpp` (l.27). Bonferroni and the 25-pair threshold are uncited. "fp16 not bit-reproducible"
  (l.180) is uncited. The 514 M count sits next to `\cite{danube3}` but comes from the checkpoint.
  whispercpp has no `version`.
- Argument: "predominantly parameter errors" (l.78-81): the number is 133/152 = 87.5%, range
  79-100%, so state it. Interpretation to cut or move to Ch5: l.40, 111-113, 129-130, 164-166,
  172-173, 215-216, 285-286. Prefill-tail mechanism asserted (the same long items are slow for
  every model). 1.5 GHz is a cap, not a held clock. l.15 "measures the size of the gap" vs l.59.
  EM−CRR also includes segmentation. C3 means three things across Ch1/Ch3/Ch4. The confirmatory
  families vs ch3:137. "a bound worth quoting" (Clopper-Pearson 2.8%). "drawn from the training
  distribution" (l.239). l.206-208 frames the change as precision only. "dominated on both axes"
  rests on a non-significant difference. l.35-38 "unremarkable" comes before its caveat. The
  paired prompt effect is judged against marginal CIs. The Q8_0 exclusion from the rule is
  silent. The hardware-independence claim is uncited (the parity csv exists). Exp-3/Exp-2 are
  described more times than Table 3 allows. l.5-7 overstates what §4.7 answers. "decisively";
  "measurement noise" for deterministic decoding. Exp-2 shows STT also missing its budget (l.123).
- Presentation: `\acrshort` in prose; SNR, GPU and FP16 hand-typed; pp/p95 never defined; rss
  acronym. Three spellings of each model name across the tables. EM appears as a fraction in some
  places and a percentage in others. FCR is in no table. Table 4.1 caption says "matched", the note
  says "not matched". "Items 3540" should be decodes. Codes in the List of Tables. Figure has no
  short caption, and the markers are unexplained. "decisively", "properly", "actually",
  "quietly". "shows" ×3. Five sentences over 45 words (l.180-185 is 75). "template-parity gate",
  "of record", "Pi-side". `sec:exp0` and `sec:exp1` labels. Minus signs, ×, and → in the table
  notes. Type 3 fonts in the figure. About 18 register flourishes (e.g. l.134, 137, 143, 235,
  281, 305, 328, 344, 349).
- Build: clean. XeLaTeX, 0 errors, no undefined citations, no overfull boxes in Ch4, every table's
  last row present. The only undefined ref is `chap:conclusion` (expected). A duplicate hyperref
  anchor on Ch3's Table 3.3 (for issue 03). `tab:latency-budget` is defined both in ch3:525 and
  in `generated/exp2_latency_budget.tex` (for issue 03).

For issue 03: A5, A12, N2, N3, P9, P10, P12 (requirements table names, the 20 tok/s row);
ch3:105 "Table~19" and ch3:331 "Table~18" are hard-coded (4.6 and 4.5 in the PDF); ch3:137 "the
McNemar sample" vs golden.

### 2026-09-24 -- hand-off from issue 03's second pass, and what the new Ch3 changes here

Issue 03 is resolved (`cc27192`, then second pass `d9aeb76`). Its "For issue 04" section adds
four items. Each was verified in issue 03's verifier pass. I confirmed that the Ch4 lines say
what the hand-off quotes. IDs are H-numbered.

| # | Sev | Line | Finding | Maps to | Proposed fix |
|---|---|---|---|---|---|
| H1 | MAJOR | 9-12 | "accuracy is hardware-independent under greedy decoding with a fixed grammar": stated as a principle, for every configuration. Ch3 now establishes it empirically, for the selected configuration on text input only (Pi/workstation parity 0/200; CRR is *not* hardware-independent, ch3 V5) | was MINOR #31 (argument), raised | "accuracy is scored on the workstation: for the selected configuration, the deployed surface produced identical outputs on the workstation and the Pi for all 200 golden transcripts (Section~\ref{sec:definitions-of-record}); every timing figure is measured on the Pi". Use Ch3's surface names |
| H2 | BLOCKER | 291-322 | "has not been measured": the latency experiment measured p95 3,122 ms for the selected configuration (misses 2,500), and no chapter reports it | = A1 | see the reframed decision below |
| H3 | BLOCKER | 169-170 | "while Qwen2.5-0.5B and Llama-3.2-1B have converged": contradicts ch3:323-325 ("No model is shown to have converged"). Only validation EM is logged, and Qwen still rose 0.9042 -> 0.9125 at epoch 3; only Llama was flat (0.900) | new (the verifier had flagged a related issue) | "...shows every model except Llama-3.2-1B (unchanged at 0.900) still improving at epoch 3, from 0.008 for Qwen2.5-0.5B to 0.038 for H2O-Danube3-500M, so no model is shown to have converged. The two lower-scoring models improve most, so part of both gaps may be convergence under a fixed budget rather than capability." |
| H4 | MAJOR | 126 | "the prompt-cache behaviour the protocol deliberately enables": true of the benchmark, false of the deployed parser (`cache_prompt=false`) | = A11 (+ MINOR #15) | Ch3's new "Timing protocol" paragraph states the difference; Ch4 points there and scopes "278 ms to spare" (l.131) and l.333 to cached prefill |

**Earlier findings that the new Ch3 changes:**
- **C1 no longer needs a decision.** `mcnemar1947` is in the bib and cited in Ch3's statistical plan.
  Ch4 l.255 can leave it uncited, since the plan is one section back. Bonferroni is still uncited
  in both chapters (MINOR).
- **A12 now has an anchor.** Ch3 states the rule ("Selection rule and statistical plan",
  sec:definitions-of-record), so l.6 and l.291 become a `\ref`. The claim "before any result existed"
  is now Ch3's as well.
- **P9 now has an anchor.** Ch3's "Timing protocol" states the cooler and the governor, so l.96-99
  can say "the run of record described in Section~\ref{...}" and drop "never declared".
- **P10 changes.** Ch3 re-baselines only under the selection rule (fail-openly clause). For every
  other requirement the tab:requirements caption says "reported as missed, not adjusted". So l.141
  drops re-baselining: safe failure and false commands are reported as missed, and nothing more is said.
- **A10 / N1** match Ch3 ("met for the language-model process only"). **A5 / N2** are fixed in Ch3;
  Ch4 l.198-199 follows (fp16 base + adapter, transformers, Kaggle T4).
- **P12:** the script now shows **16 FAIL** (7 + 9 codes Ch3 no longer defines). Names come from
  Ch3's table: End-to-end latency, Exact-match threshold, Schema validity, Safe failure, Memory
  ceiling, Throttling, Speaker sensitivity, False commands; the reference surface and the deployed surface.
- **Also from the first hand-off:** l.212-214 add the decoding settings (64 vs 96 cap, batched vs one
  sequence) and Llama's epoch-3 vs epoch-2 checkpoint (V4). l.198 "reports C3" becomes "what the
  harness of C3 measures" (V19). l.180 becomes "GPU training is not guaranteed to be bit-reproducible across
  sessions" (V32). The captions of generated/exp2_latency_budget.tex ("prd 4.7", "Table 7 pinning",
  "Table 6's line") are fixed in `eval/tables.py`.
- **Unchanged:** A2 (Ch3's plan still declares Q8_0 vs Q4_K_M), P6 (Ch3 still says "2.5 GB").

**A1 / H2 reframed.** My own reading of the new rule; the verifier did not check this. Ch3's rule
is now "highest EM among configurations *not ruled out*" by the two constraints, and "if no
configuration satisfies both, the rule fails openly: the constraint is re-baselined". Applied
literally to what was measured:
- Qwen's measured 3,122 ms exceeds 2,500, so Qwen is ruled out.
- SmolLM2 was never measured end to end. Its lower bound is 894 + 1,063 (the minimum measured STT)
  = ~1,957 ms, so it is not ruled out.
- Read literally, "not ruled out" therefore selects **SmolLM2** (EM 0.760, below the 0.85
  threshold, which the rule does not name). Measuring the model penalised it.
- The fail-openly clause triggers anyway, because no configuration is shown to *satisfy* both:
  memory is unconfirmable for all of them. Re-baselining the latency budget to the measured 3,122 ms
  keeps Llama ruled out (>= 2,282 + 1,063 = ~3,345 ms) and selects **Qwen**.
The two clauses give different answers. Whichever you choose, Ch3's rule needs one clause saying
which applies when a constraint is measured for one configuration only.

### 2026-09-24 -- author's decisions and resolution

Decisions: **A1 fail-openly** (select Qwen2.5-0.5B, end-to-end budget re-baselined to the measured
3,122 ms and reported as missed); **P6 GiB** (the ceiling is 2.5 GiB; every figure relabelled,
no value or margin changes); **A2 add the test**; **approve all** (BLOCKER/MAJOR, N1-N5, H1-H4 and
the MINOR/NIT list).

**Evaluation code** (`eval/`, `results/`, `thesis/generated/`; every generated file re-rendered):
- A2: `eval/mcnemar.py` gains two exploratory families, labelled as added after the results:
  - fp16 reference against each quantised artefact on `test_golden`: 6 pairs, Bonferroni
    alpha 0.0083. Counts 3-0, 2-0, 0-0, 1-0, 12-9, 0-3; smallest p 0.25; none significant.
    These now appear as b / c / p columns in Table 4.6.
  - The family control, Qwen2.5-0.5B against H2O-Danube3-500M fp16: 15-2, p = 0.0023.
  - The reference predictions are re-scored from `train/kaggle_out/preds_*.jsonl` and checked
    against `surface_a.csv`, the same way the Surface-B predictions are checked.
- #13: new `eval/error_intents.py` writes `results/golden_error_intents.md`. 133 of 152 golden errors
  (87.5%) keep the reference intent, from 0.792 (SmolLM2 Q4_K_M) to 1.000 (Qwen).
- `eval/tables.py`:
  - Captions: no codes, and no project-internal or hard-coded float numbers. Cross-references are
    written `[Table](#tab:x)` and rendered as `\ref`; acronyms are written `[X](#acr:k)` and
    rendered as `\acrshort`. Unicode minus, times, degree and arrow signs are converted for LaTeX.
  - One display name per model; fractions at three places everywhere (pooled Table 4.7 keeps
    four); memory in GiB.
  - Table 4.2's caption now computes its 0/180 and 67.5-74.1 °C from the trial rows (they were
    typed in before).
  - Table 4.7 drops its Decode p95 column, and "Items" becomes "Decodes".
  - The Table 4.5 note is prose, not markdown. It drops "two-fifths" and the "largest model"
    claim, reports the family control with its test, and reads convergence from the training logs.
  - The Table 4.3 note says which run is the base; the clock is described as a cap, with the
    1.42 GHz condition.
  - The latency-budget table loses "prd 4.7", "Table 7 pinning" and "Table 6's line".
- `eval/exp0.py`: Table 4.1 gets a self-contained caption (CI method, S/D/I, source CSV). It says
  "this table", not "Table 16", and "unprompted decoder", not "matched condition".
- `eval/plots.py` (Figure 4.1):
  - No in-figure title, no codes, no "Sat-19 triage".
  - Line labels moved to the top margin; the point labels sit to the left of their markers.
    Verified by rendering: no overlaps.
  - One marker shape; GiB; TrueType fonts.
- Tests: `test_tables.py` updated, and new tests for the deployment family, the reference provenance
  check, `\ref`/`\acrshort` emission and `error_intents`. 209 pass.

**Thesis:**
- Ch4 is rewritten against every approved finding. Two changes differ from the proposed fixes:
  - #21: no Clopper-Pearson figure. It would be a number with no source file, so the "bound"
    sentence is reworded instead.
  - #26: the paired-CI sentence is dropped, not computed.
  - The Llama end-to-end lower bound is 3,346 ms, not 3,345: 2,282.45 + 1,063.38 = 3,345.8.
  - The slow-prefill items are nested across models (SmolLM2's 3 are among Qwen's 8, which are
    among Llama's 34). The text now states this precisely instead of "the same items".
  - The false-command table (generated, previously not \input) is now Table 4.4, so Ch4's
    later tables are renumbered 4.5-4.7 via \ref.
- Labels: `sec:speaker-sensitivity` and `sec:benchmark` are new. The old `sec:exp0` and
  `sec:exp1` stay as aliases, because Ch5 (being edited in another session) still refs `sec:exp1`.
- Ch3, as these decisions force:
  - 2.5 GB becomes 2.5 GiB (requirements table, selection rule).
  - One sentence on the case the rule did not anticipate, a constraint measured for one
    configuration only, pointing to Ch4. It is stated as a later clarification, not as part of
    the rule as first written.
  - The statistical plan names the two exploratory families.
  - `\ref`s move to the new labels.
- references.bib: `dunn1961` (JASA 56(293):52-64, DOI checked on Crossref), cited for
  Bonferroni in Ch4. Only this hunk is committed; the other session's `note` removals in the
  same file are theirs.

**Scripts** (`tools/review/`; script errors and anchors only, no expected value changed to match the prose):
- `master_ch4.py`:
  - Anchors follow the new wording.
  - New claims recompute every number the rewrite introduced: error-intent share, convergence
    gains, the deployment and family-control tests, 3,122 ms / n = 226 / 751 ms from
    `exp2_latency_budget.md`, the 1,063 ms minimum STT from `exp2_preds/clean.jsonl`, the
    3,346 ms bound, the nested slow items, the 1.42 GHz condition, and the smallest attainable p
    and seven-pair minimum.
  - The GB warning is now a check that the chapter writes GiB.
  - Script error: convergence gains were compared on float differences. 9/240 = 0.0375 came out as
    0.03749999… and failed a correct 0.038; the gains are now rounded to 9 places first.
- `master_ch1.py`: the thermal table now writes "model Q4_K_M"; the key is normalised back to the
  artefact stem.

**Final state: 0 FAIL, 2 WARN, 201 PASS** (baseline 16 FAIL). The WARNs are justified:
- `acronym` "exact match" (l.78): the metric's name is written in words, consistently, throughout
  the chapter, and the tables carry `\acrshort{em}`.
- `absolute` "guaranteed" (l.192): this is the hedge "not guaranteed to be bit-reproducible", the
  same wording Ch3 W34 asked for.

Ch3: 0 FAIL, 4 WARN (unchanged). Selftest passed (10/10). Clean Master build from scratch: 0
errors, 0 overfull boxes, no undefined citations; only the pending `chap:conclusion` is undefined.

Not verified: the 1.5 GHz cap comes from `CLOCK_RATIO` in `eval/tables.py` (STATE.md). No clock
column exists in `exp1.csv`, which is why the text now calls it a cap.

### For issue 05 (Ch5) -- what Ch4 now says that Ch5 must match
- Ch5 l.24 and l.27: "0.13 GB" and "0.95 GB" are GiB differences (0.68 - 0.55 and 1.63 - 0.68);
  write GiB. The ceiling is 2.5 GiB.
- Ch5 l.96 `\ref{sec:exp1}` should become `\ref{sec:benchmark}` (likewise any `sec:exp0` ->
  `sec:speaker-sensitivity`). Then delete the two alias labels in Ch4 (lines 24 and 67).
- Selection: Ch4 §4.7 now reports the end-to-end measurement (Qwen2.5-0.5B p95 3,122 ms, n = 226)
  and applies the rule under its failure clause. The budget is re-baselined, and the selected
  configuration misses 2,500 ms as specified. Any Ch5 sentence treating the latency constraint as
  met, or as unmeasured, contradicts it.
- Ch4 no longer says "decisively" (Ch5 l.26 does), "two-fifths", or that the family choice is
  "first-order". The last two were interpretation, cut from Results; Ch5 may carry that reading,
  hedged. Ch4's family claim is now "a family difference at about 0.5 B, 15-2, p = 0.0023
  (exploratory)".
- Cut from Results as interpretation, available to Ch5: "the enclosure is a term in the latency
  budget"; "a throughput figure quoted without its thermal state is not reproducible"; "the
  condition a practitioner with a fixed fine-tuning allowance faces".
- The prefill margin (278 ms) holds under cached prefill only; the deployed parser's uncached
  prefill p95 is 751 ms.
- No model is shown to have converged (only Llama's validation EM is flat).
- Ch4 has a new Table 4.4 (false-command rate). Refer to it by `\ref{tab:false-command}`, never by
  number.

For the Ingénieur: the generated `exp2_latency_budget.tex` caption changed (the internal
references are gone; "Branch A/B" and the NFR IDs are still there, per issue 00 the Ingénieur's call).
