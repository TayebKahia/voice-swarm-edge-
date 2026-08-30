# Issue 05: master-ch5

Status: resolved
Blocked by: 04
Chapter: thesis/master/ch5_discussion.tex (§5.1 written; §5.2, §5.3.1, §5.3.2 and the lead-in are \TODO)
Script: tools/review/master_ch5.py
Report: .scratch/thesis-review/reports/master_ch5.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_ch5.py
```

## Agents

- **Reviewer** -- D2, D4, D5, D6, D8, D10, D11, D12 on §5.1. Focus: Ch5 may not quote a Ch4 figure with a
  stronger qualifier than Ch4 gave it; no RQ1 verdict (Ch6's); "modest" margin at n = 60 on one board.
- **Verifier.**
- Re-run this issue when §5.2-5.3 are drafted, adding claims to the script first.

## What the script establishes (baseline: 0 FAIL, 19 WARN, 37 PASS)

- Every §5.1 figure recomputed (178 ms, 0.13 GB, 17.5 pp, 1,210 ms, 0.95 GB, 1,771.5 and 1,610.2 ms
  uncooled, the 67 ms / 6% decode margin). No number appears that Ch1-Ch4 did not report.

## Seeded findings

- l.40 "more than a third of the distance": 6.5 pp is a Surface-A (FP16) gap and 17.5 pp a
  Surface-B (Q4_K_M) gap -- the ratio mixes surfaces without saying so.

- **D12**: three lead-ins are claims ("The knee belongs to a model, not to a size.", ...).

## Comments
### 2026-09-24 -- review round 1 (1 reviewer + verifier), whole chapter

**Scope.** The issue was written when only §5.1 existed. Since then §5.2 and §5.3 and the lead-in have been
drafted (`ca1ed8c`, `8a3980d`), and the script was extended to cover them (`87ebad1`). This round
therefore reviews the **whole chapter**, on the issue's dimensions: D2, D4, D5, D6, D8, D10, D11, D12.

**Script.** 0 FAIL, 4 WARN, 91 PASS. There were no FAILs to triage. **One script error was fixed**:
the item-0036 claim checked −163.0/+163.0 against
`surface_b_preds/qwen…Q4_K_M_test_golden.jsonl` but was anchored on l.144. The two values on l.145
therefore WARNed as "new numbers". It is now split into a transcript claim (l.144) and a value claim
(l.145). No expected value changed. After the fix: **0 FAIL, 2 WARN, 94 PASS**, and the self-test passes. The
2 WARNs left are justified:
- `chap:conclusion` (Ch6 unwritten; it must carry this label).
- l.201 "not guaranteed" (negated; see C3 for its missing cite).

**Verdict.** Ready after fixes; no rework needed. Every issue-04 hand-off item is honoured:
- GiB;
- `sec:benchmark`;
- "satisfying";
- SmolLM2 loses the EM ranking and the 0.85 miss is a second fact;
- stage allowances are not rule constraints;
- the 622 ms (25%) miss and the re-baseline;
- the cached-prefill qualifier on 278 ms;
- no model is shown to have converged.

D6 is clean: the acoustic-robustness experiment is named once and the owner is named correctly. The three
STATE.md flags are honoured:
- 1 − FCR is exact under Ch3's current definition;
- the false "only instance of declining" sentence was not copied;
- the 103/114 dropped-minus figure is absent.

Seeded findings:
- (a) the FP16/Q4_K_M ratio mixing is **fixed**;
- (b) claim lead-ins are **partly fixed**: 5 remain (M13).

Citations: 3 keys, **3 SUPPORTS**. Issue 04's PARTIAL on tam2024 concerned Ch4's sentence. Ch5's
sentence reports the finding and hedges its own inference.

**Verified BLOCKER/MAJOR.** There were no BLOCKERs. The reviewer raised 7 MAJOR; the verifier confirmed 3, found 4
real but narrower (all downgraded to MINOR, one of them mostly refuted), and added 1 (folded into R3).

| # | Sev | Line | Finding | Verifier | Proposed fix |
|---|---|---|---|---|---|
| R2 | MAJOR | 157-159 | "supervised fine-tuning had made structurally valid output close to certain before any constraint was applied": a causal attribution the chapter disowns at l.168-170 and l.222-227 (zero-shot predictions not retained, so untuned validity is unknown). It is the *premise* of the labelled hypothesis, stated as fact, so the hypothesis is partly circular | CONFIRMED | "so the fine-tuned models already produced structurally valid output almost without exception when no constraint was applied" (no new number; matches Ch4 l.254-255 wording) |
| R3 | MAJOR | 196, 190-191 | Each model was trained **once, from seed 42** (ch3:311); "seed" appears nowhere in Ch4/Ch5. McNemar covers item sampling, not training-run variance, and this is not among the six threats. Related overclaim at l.190-191: "no difference between configurations is run-to-run noise" is true of *decoding* only. Scope: it cannot touch the Q8_0/Q4_K_M or grammar contrasts (one adapter per model); it can touch the model and family (6.5 pp, exploratory) contrasts | CONFIRMED (+N1 folded in) | l.191 → "…is decoding noise". Add to "Fixed training budget": "Each model was also trained once, from one seed. The paired tests account for the sampling of items, not for variation between training runs, which was not measured, so a model or family difference is a difference between single trained adapters." No claim about typical seed spread (no source in the bib). Fold into the existing paragraph so "Six threats remain" stays true |
| R4 | MAJOR | 89-90 | "A Q8\_0 point could join the frontier only by matching or beating its Q4\_K\_M counterpart on latency": false on the point estimates the frontier is drawn on (Ch4 l.382-383, "dominated on the point estimates"). SmolLM2 Q8_0 golden EM 0.790 > Q4_K_M 0.760 (McNemar 8 vs 14, p = 0.286), so it would be non-dominated at any latency below Qwen's 1,072 ms. The sentence silently assumes ties it does not grant Llama | CONFIRMED | "Where a Q8\_0 point would sit depends on its latency, which was not measured, so the frontier is strictly a Q4\_K\_M frontier." |
| R1 | MINOR (↓MAJOR) | 130-134 | Claimed: the OOD split's 38 truncated fragments contradict "abstention by request type". Verifier recounted by `ood_source` (counts right: fragments 16-19/38, drone-unsupported 17-29/37, assistant 35-38/38, garbage 23-36/37), but 14 of the 38 fragments carry no command ("no wait", "scratch that"). On the 24 command-bearing fragments abstention is only 5-10/24, which **supports** l.131-134. The l.173 sub-claim is refuted: `test_ood` is the untrained baseline such an intervention would be measured against. Residue: drone-unsupported 46-78% shows the boundary is graded, and "abstention is absent" should be tied to the in-domain splits | PARTLY (mostly refuted) | l.131: "They separate off-topic requests from supported ones more reliably than they separate commands they parsed correctly from commands they did not." l.134: "…where, on the in-domain splits, abstention is almost absent." Do **not** quote per-source numbers unless `eval/abstention.py` first generates them (Block A) |
| R5 | MINOR (↓MAJOR) | 75-78 | (a) Real: it gives the combined and decode margins but omits the one stage allowance Qwen misses, prefill 250 ms (ch3 tab:latency-budget; Ch4 l.129-131: cached p95 328.8 ms, 8/60 over). Selective rather than wrong, since stage allowances are not rule constraints (l.78-79). (b) Refuted: "modest" hedges downward, and l.249-250 already flags n = 60 | PARTLY | "Cooled, the selected configuration fits the combined and decode allowances, with modest margins, but not the 250~ms prefill allowance (Section~\ref{sec:benchmark})." Do not quote 328.8 ms in Ch5 (no generated artefact carries prefill percentiles; see hand-off) |
| R6 | MINOR (↓MAJOR) | 31-35 | "useful part of the range ends at or below half a billion parameters … parameters appear to purchase latency and memory and little else": a size-class wording one paragraph before l.37-50 retracts the size reading. This is set-up-then-qualify, not a contradiction (l.34-35 caps it). Residue: register, "purchase latency" inverts the sense, and "little else" is generous (Llama 0.910 < 0.935, n.s.) | PARTLY | "…the two directions suggest that, among the models measured, accuracy stops rising at Qwen2.5-0.5B: the one smaller model loses 17.5~pp, and the one larger costs latency and memory for no difference these tests can detect." |
| R7 | MINOR (↓MAJOR) | 139-143 | The error taxonomy (240/39/3, 114 yaw flips of 282) has no source pointer. Numbers reproduce exactly from `eval/abstention.py:taxonomy()`. The flip rule is `gold.yaw == -pred.yaw` (equal magnitude; no zero-yaw edge case; all 114 have every other slot right). Ch4 names artefacts for prose-only figures (l.86, l.173); Ch5 does not. Traceable, so not a reproducibility gap | PARTLY | After the 282 sentence: "(\texttt{results/limitation\_abstention.md})"; optionally "the predicted yaw being the exact negation of the reference" |

**MINOR/NIT (reviewer only, not verified).** Proposed wording is in the round-1 reviewer report; the key
items are listed here so you can decide them:
- **C1** l.207-208 "established by an exploratory test": stronger than Ch4. → "detected by an exploratory exact McNemar test (15 against 2 discordant items, $p = 0.0023$)".
- **C2** l.18-21 "The answer turns out to have less of the shape of a trade-off than the question anticipated": answers RQ1 ahead of Ch6, and is a flourish. → "Figure~\ref{fig:pareto} places the measured configurations for this task and this board; this section examines how much of the trade-off the figure shows reaches the selection."
- **C3** l.201 GPU non-reproducibility uncited. Ch3 l.363 and Ch4 l.193 cite `pytorchrepro`. → append `~\cite{pytorchrepro}`.
- **C4** l.296 "a survey": sbc2025 is a benchmark (Ch2 l.12 says so). → "a benchmark of language-model inference on single-board computers".
- **C5** l.190-191: the reference surface decodes in batches (ch3:397), and its determinism was not checked. The deployed surface is greedy, one sequence at a time.
- **C6** l.170-173 "Two interventions would test it and would also address the failure": the confidence gate addresses the failure but does not test the hypothesis. → "could address the failure, and the second would also test the hypothesis".
- **C7** l.279-280 "lost at the speech stage, not at the parser": the attribution belongs to the Ingénieur (endpointing and recognition together, ch3:524-527). → "The parser is unchanged between the two conditions, so the loss originates in its input, in endpointing and recognition, as analysed in the \emph{Mémoire d'Ingénieur}."
- **C8** l.286-288 drops Ch4's caveat ("different text, indicative"). The distribution is over accent buckets, not speakers.
- **C9** l.37, 47 "knee" is never defined, and a two-point frontier has no geometric knee. → define it at first use, or say "the frontier's upper point".
- **C10** l.214-216 "identical three-epoch allowance … fixed fine-tuning budget": equal passes are not equal compute.
- **C11** l.254-256 "bounds the ambiguity … its null result is uninformative": "bounds" contradicts "uninformative". → "can reveal ambiguity in the schema but not errors in the targets".
- **C12** l.242-245 "five orders of magnitude below the corrected threshold": p-value magnitude is the wrong robustness measure. The reviewer's design-effect arithmetic (χ² 28.2 vs 5.73, which survives a design effect up to about 4.9) is unverified and computed ad hoc. **Rewording is safer than quoting it.**
- **C13** l.164-167 "fell where the training distribution ends": lidar is an assistant-style query, and that type is in training. → "fell on an out-of-domain query".
- **C14** l.266-269: the abstention figures depend on the author-written 150-item OOD mix; this is not acknowledged.
- **M13** Lead-ins that state findings: l.23, 111, 123, 139, 155. → "Composition of the frontier." / "Composition of the safe failures." / "Abstention on in-domain and out-of-domain input." / "Taxonomy of in-domain errors." / "A common-cause hypothesis."
- **M14** Aphorisms: l.25 "a pair defines a direction, not a curve"; l.37-38 "It would be tempting…"; l.111-112 "bounds what an output can look like; it does not bound whether an output is given"; l.161.
- **M15** "of record" (l.195, 238, 252, 275) is never defined in the thesis. → "reported", or define it once in Ch3.
- **M16** l.63-64, 77, 80: the Ingénieur's latency figures (622, 751) are given without the `\ref{sec:selection}` / `\ref{sec:benchmark}` that Ch4 gives them.
- NITs:
  - l.24 → "dominated on the point estimates";
  - 14 sentences over 40 words, worst l.191 (62) and l.309 (58);
  - FP16 vs fp16 (l.217; Ch3 and Ch4 use lowercase);
  - l.60 "exact-match" hand-typed, → `\gls{em}`;
  - l.74 "language-model stages" vs `\gls{slm}` stages;
  - "does not show", "very large", "considerably worse";
  - the framing is repeated four times (l.9-11, 179-182, 187-189, 266-268);
  - l.52 the rule is stated in `sec:definitions-of-record`;
  - l.294 "every timing figure … active cooler" ignores the uncooled run;
  - l.284 "one recording session" was held over two days.

**Outside the assigned dimensions (D1):** the chapter ends on "Models and quantisation levels" and never
hands off to Chapter 6. Template D1 asks for a closing hand-off.

**For other issues (not Ch5), verified by the verifier:**
- ch3:174-175: of the "35 authored assistant-style queries", 15 are unsupported drone requests (F116, e.g. "deploy the parachute"). Only 20 are assistant queries.
- ch3:172-173 lists "truncated utterances" as a training axis. F119 (truncated) is in `val_synth` only.
- Ch4 l.129-131 prefill percentiles (328.8 ms, 8/60) come from no generated artefact. They are reproducible only by re-aggregating `results/exp1_cooled.csv`.

**Decisions only you can make:**
- Each of R2, R3, R4 (MAJOR) and R1, R5, R6, R7.
- Whether R3 becomes a new threat paragraph or folds into "Fixed training budget". The recommendation is to fold it in, keeping "Six threats remain" true.
- Which MINOR/NIT items to take. C2, C3 and M13 are the cheapest and highest-value.
- Whether to add a closing hand-off to Ch6.

### 2026-09-24 -- author's decisions, and what was applied

The author approved the recommendations. That meant fixing all the verified findings
(R1-R7) and five cheap MINORs (C1-C4, M13); the rest were left as written. Applied to
`thesis/master/ch5_discussion.tex`:
- **R2:** the premise of the common-cause hypothesis is now an observation ("the fine-tuned models
  already produced structurally valid output almost without exception when no constraint was
  applied"). It no longer attributes validity to fine-tuning.
- **R3:** l.191 now reads "decoding noise". "Fixed training budget" states the single seed
  (`Table~\ref{tab:lora}`) and that training-run variation was not measured. It is folded into the
  existing paragraph, so "Six threats remain" is still true. The text makes no claim about how large
  seed spread typically is.
- **R4:** the Q8_0 sentence now says only that its position depends on an unmeasured latency.
- **R1:** "separate off-topic requests from supported ones more reliably than…", with "abstention is
  almost absent" tied to the in-domain splits. No per-`ood_source` number is quoted, because no
  artefact generates one.
- **R5:** the selected configuration fits the combined and decode allowances "but not the 250~ms
  prefill allowance" (`\ref{sec:benchmark}`). The 328.8 ms figure is not quoted, because no artefact
  generates it.
- **R6:** "among the models measured, accuracy stops rising at Qwen2.5-0.5B …". The size-class
  wording is gone.
- **R7:** the taxonomy now points to `results/limitation_abstention.md`.
- **C1:** "detected by an exploratory exact McNemar test (15 against 2 discordant items)" replaces
  "established". This is Ch4's wording.
- **C2:** the RQ1-answering flourish in the §5.1 opening is replaced by a statement of what the
  section examines.
- **C3:** l.201 now cites `pytorchrepro`, as Ch3 and Ch4 do.
- **C4:** sbc2025 is described as "a benchmark of language-model inference on \glspl{sbc}", not a
  survey.
- **M13:** five lead-ins are retitled as topics: "Composition of the frontier", "Composition of the
  safe failures", "In-domain and out-of-domain abstention", "Taxonomy of in-domain errors", "A
  common-cause hypothesis".

**Kept as written, by the author's choice:**
- C5-C14, M14-M16 and the NITs: the recommendation was to leave them unless a fuller polish pass is
  wanted.
- **The closing hand-off to Ch6 (D1): done** (see the follow-up below).

**Final state.** Script: 0 FAIL, 1 WARN, 96 PASS.
- The remaining WARN is l.203 "not guaranteed", which is negated and now cited.
- The `chap:conclusion` WARN cleared because the untracked Ch6 draft now carries that label.
- Two WARNs introduced by the edits were fixed before this point: the weak verb "shows" in the new
  §5.1 opening, and the hand-typed "single-board computers".
- The self-test passes, and `check_tex` is clean.
- The build (`latexmk main_master.tex`, run incrementally because the build folder is shared with
  the Ch6 session) gave 0 errors, no undefined references or citations, and no overfull boxes.

**Still open for other issues** (listed in round 1): the ch3:174-175 split of the 35 pairs (20 of
them assistant queries, 15 F116 drone requests); ch3:172-173 "truncated utterances" appear only in
`val_synth`; the Ch4 prefill percentiles have no generated artefact.

### 2026-09-24 -- follow-up: closing hand-off to Ch6 (D1)

Ch6 was committed by the other session (`c2da438`), so the hand-off was written against its actual
opening and its "Prioritised next steps". It is one closing paragraph after §5.3.2's last paragraph.
It says the chapter's readings set the strength at which the Ch4 results can be stated, and that Ch6
"decides RQ1 at that strength". The wording echoes the lead-in's l.12 and gives no verdict. It names
the three steps Ch6 lists, in Ch5's own wording: the confidence gate, training pairs mapping degraded
commands to `unknown`, and SmolLM2-360M's end-to-end measurement. It adds no claim or number.

The paragraph avoids the phrase "answers RQ1", because the script's register check reserves it for
Ch6.

Script: 0 FAIL, 1 WARN (l.203, justified), 96 PASS. The Master builds with 0 errors. The one Amiri
font-shape warning comes from the Arabic front matter and is unrelated to this change.

### 2026-09-24 -- the three hand-offs to other chapters, closed

- The two Ch3 items are fixed. See issue 03's follow-up comment: the 81 pairs by family are
  20 / 21 / 40, and "truncated utterances" became the ellipsis axis.
- The Ch4 prefill percentiles were a **false alarm**. They come from `results/exp1_cooled.csv`, which
  the section's model-comparison table caption names, and `master_ch4.py` l.193-197 recomputes them.
- **New, left for the author:** Ch5 l.161 says all 81 pairs are "a request the schema does not
  support". The 40 F117 lexical near-misses ("we landed that contract") are not requests. Proposed:
  "…through 81 pairs, every one an utterance the schema does not support as a command, and through
  none in which a supported command was made unreadable". Ch6 l.97 stays true.
