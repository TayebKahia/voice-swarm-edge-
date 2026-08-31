# Issue 09: master-ch6

Status: resolved
Blocked by: 05
Chapter: thesis/master/ch6_conclusion.tex (107 lines, no \cite; chapter `602447e`, STATE.md record `c2da438`)
Script: tools/review/master_ch6.py
Report: .scratch/thesis-review/reports/master_ch6.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_ch6.py
```

## Agents

- **Reviewer** -- D1, D2, D4, D6, D8, D10, D11, D12, and D5c only: there are no citations, so look
  for literature or tool claims that need one. D3 is the script's job. Focus:
  - **Unhedged means no hedging words, not stronger claims.** No Ch4 figure may carry a stronger
    qualifier in Ch6 than Ch4 gave it. The qualifiers are "significant" and "established"
    (Ch4 §4.6 l.290, §4.7 l.372), "exploratory" (the family control, Ch4 l.173) and "not
    distinguishable" (Ch4 l.296).
  - **No new caveat** (SKILL.md, Ch6). A limitation that first appears here belongs in Ch5, so
    report it as a Ch5 finding.
  - **The RQ1 verdict must match Ch4 §4.7** (l.349-392) **and Ch5 §5.1** (l.52-64):
    - Qwen2.5-0.5B Q4\_K\_M is selected on EM against re-baselined constraints.
    - It misses 2,500 ms as specified by 622 ms (25%).
    - The budget is re-baselined to 3,122 ms (n = 226).
    - Memory is confirmed for the language-model process only.
    - If the rule is restated, it says "satisfying", never "not ruled out" (issue 04, option B).
      Ch4 l.378 uses "not ruled out by the memory ceiling" for memory (issue 04 A10). That use is
      correct and is not a restatement of the rule.
  - **The three next steps must match** Ch5's closing hand-off (`ch5_discussion.tex`, final
    paragraph) and §5.2 (l.174-177):
    1. the confidence gate;
    2. training pairs mapping degraded commands to `unknown`;
    3. the end-to-end measurement of SmolLM2-360M (the hand-off places it in §5.1).
  - **The 81 unknown training pairs.** Ch6 must agree with Ch3 l.174-180 as corrected in `644c8fb`:
    20 assistant queries, 21 unsupported capabilities and 40 lexical near-misses, none of them a
    supported command made unreadable.
  - **"What the comparison establishes"** must cover each contribution C1-C3 exactly as Ch1 states
    it (`ch1_introduction.tex` l.107-125), and claim nothing Ch1 did not promise.
  - **Carried from STATE.md** (the Ch6 entry; this is a check, not a finding). Ch6 was checked against
    a working-tree Ch5 before issue 05's edits were committed (`f1f7732`, `c985c13`, `535352c`,
    `1bd566e`). Re-read 6.2 P2 and 6.3 against Ch5 as committed, in particular the 5.2 taxonomy
    paragraph and the 5.3.1 untuned-baseline paragraph.
- **Verifier.**

## What the script establishes (baseline: 0 FAIL, 0 WARN, 54 PASS)

- Every Ch6 figure is recomputed from the file Ch4 draws it from: `surface_b.csv`,
  `surface_b_nogrammar.csv`, `surface_a.csv`, `exp1_cooled.csv` / `exp1.csv` (nearest-rank p95),
  `exp2_latency_budget.md`, `mcnemar.csv`, the abstention CSV and `data/train.jsonl` (81 `unknown`
  rows).
- Any significant number that appears in no earlier chapter is a FAIL.
- Hedging words FAIL.
- Five banned phrasings are absent: "budget met", "oversampling", "only instance",
  acoustic-robustness/Exp-N, and "guarantee".
- The prd.md §3.1 outline maps to the three sections, and the first paragraph of 6.1 answers RQ1.

## Seeded findings

None.

## Comments
### 2026-09-24 -- review round 1 (1 reviewer + verifier)

**Script.** 0 FAIL, 0 WARN, 54 PASS, the same as the baseline. There were no FAILs to triage and no
script change. Agent reports: `agents/09-master-ch6/reviewer.md`, `agents/09-master-ch6/verifier.md`.

**Verdict.** Ready after fixes; no rework needed. These pass:
- the outline (D1: three sections, as in prd §3.1);
- the RQ1 verdict against Ch4 §4.7 (622 ms / 25%, re-baselined to 3,122 ms, memory for the language-model process only, "satisfying");
- the 81-pairs sentence against Ch3 as corrected (`644c8fb`);
- the order of the next steps against Ch5's hand-off;
- D6: no mention of the acoustic-robustness experiment, and the Mémoire d'Ingénieur is named exactly;
- the carried re-read of 6.2 P2 and 6.3 against the committed Ch5.

None of the number-trace rows that were only "measured:" hits is wrong in context.

**The pattern.** Four of the five surviving MAJORs are the same failure. Ch6 is unhedged, which is
right, but in four places it also drops a qualifier Ch4 or Ch5 attached, so the claim reads stronger
than the evidence. The focus line "unhedged means no hedging words, not stronger claims" is what
catches them. The fifth (M4) is a contribution mislabelled.

**Verified BLOCKER/MAJOR.** There were no BLOCKERs. The reviewer raised 6 MAJOR. The verifier confirmed 5, found 1
real but narrower (downgraded to MINOR), corrected two of the proposed fixes, and added 1 (NEW-1,
outside this chapter).

| # | Sev | Line | Finding | Verifier | Fix (verifier's corrected wording) |
|---|---|---|---|---|---|
| M1 | MAJOR | 20-21 | "Across fine-tuned SLMs of 0.36--1.2 B parameters ... the trade-off reduces to two non-dominated configurations". (a) The frontier is strictly a Q4\_K\_M frontier: Q8\_0 was never timed (ch4:334, ch5:90-91), and SmolLM2 Q8\_0 scores 0.790 against 0.760 at Q4\_K\_M on golden, so "reduces to two" is not established over all configurations. (b) It is a size-class claim, which Ch5 disowns twice (ch5:50, 328-329) and removed from itself in issue 05 R6. RQ1's own range (ch1:94) does not excuse it | CONFIRMED | "Across the three fine-tuned \glspl{slm} timed on the Raspberry~Pi~5, which span RQ1's 0.36--1.2~B range, the accuracy--efficiency trade-off among their Q4\_K\_M artefacts reduces to two non-dominated configurations, SmolLM2-360M and Qwen2.5-0.5B, …" ("timed", not "measured": Q8\_0 accuracy was measured) |
| M2 | MAJOR | 22-23 | "at 0.935 \gls{em} on the golden split". Ch4 lists "the selection is made against reference-text accuracy" first among the selection's qualifications (ch4:388-389, also ch4:14-16). Ch6 restates every other §4.7 qualification but not this one, and "reference text" appears nowhere in Ch6. The golden split is "200 audio files" (ch3:160), so the sentence reads as accuracy on speech. STATE.md names this as the sentence the abstract carries | CONFIRMED | Append ", scored on reference text" after "the golden split". This keeps the script anchor, and it is Ch4's term. Avoid "reference transcripts" (too close to l.66's "reference surface", a different concept) |
| M3 | MAJOR (near BLOCKER) | 39-40 | "when wrong or out of domain, the parser emits a well-formed command rather than \texttt{unknown}". This drops Ch4's "one tendency" (ch4:149-150). Read literally, it is refuted by the false-command rate just before it: 0.1867-0.3933 means 60.7-81.3% of out-of-domain items do get `unknown` (ch5:124-127) | CONFIRMED | "… against $\leq$~0.05. Both misses reflect one tendency: when a configuration is wrong or out of domain, it emits a well-formed command rather than \texttt{unknown}." This is Ch4's sentence verbatim. "Tendency" is not on the script's hedge list |
| M4 | MAJOR | 58 | "None of the accuracy the comparison reports is available from the pretrained models as prompted (Contribution~C2)." Ch1's C2 is the label-first dataset pipeline (ch1:112-117). The zero-shot baseline is not C2, and Ch4 ties it to no contribution (ch4:200-206). So 6.2 concludes nothing about C2 as Ch1 states it | CONFIRMED; **reviewer's fix corrected**. The reviewer's fix said "every accuracy figure" is on held-out families, which is false for `test_ood` (authored/harvested, ch3:161, and part of l.49/l.60's totals). It also said the leakage gate "passes on every split", but its four axes exclude `test_ood` (ch3:182-186) | Replace l.58's first sentence: "The dataset that trains and evaluates every model of the comparison is the label-first corpus of Contribution~C2. Its splits are assigned by template family, so every in-domain accuracy figure is measured on families held out from training, and its leakage gate is clean on all four axes it checks (Section~\ref{sec:dataset}). None of the accuracy the comparison reports is available from the pretrained models as prompted." l.59-63 unchanged |
| M5 | MAJOR | 75 | "At matched size, model family moves \gls{em} by 6.5~pp" is causal wording. Ch4 says "the family difference … is 6.5 pp" (ch4:171). Ch5 says it "should be quoted with" the system-prompt fold and the separate training session (ch5:211-212), and that it is a difference between single trained adapters (ch5:221-223). Ch6 keeps "exploratory" (l.77) but drops these and "reference surface". Restating Ch5's caveats adds no new one | CONFIRMED | "At matched size, the family difference in \gls{em} on the reference surface is 6.5~pp: at about 0.5~B parameters, Qwen2.5-0.5B scores 0.935 against⏎H2O-Danube3-500M's 0.870, on 15 against 2 discordant items (exact⏎$p = 0.0023$, an exploratory test). It is a difference between single trained adapters that also differ in how the system prompt is rendered and in training session, under the identical three-epoch budget at which no model is shown to have converged (Sections~\ref{sec:iso-parameter} and~\ref{sec:threats-internal})." (⏎ = keep that line break, since two script anchors contain it) |
| M6 | MINOR (↓MAJOR) | 99-101 | "Pairs of that kind change what the model treats as an available answer on in-domain input" states the outcome of a retraining that was never run. It is weakened by l.85-86, which frames every step as "not implemented or measured". The residue is the one verb | PARTLY; **reviewer's fix corrected**. Its added "this one also tests the common-cause hypothesis" contradicts Ch5 as committed, which says *both* interventions would test it (ch5:173-176; issue 05 C6 was left as written) | "Pairs of that kind act on what the model is trained to output for input that reads as a supported command, where the gate acts only on what is dispatched, so the two steps are complementary." |

**Script anchors the fixes touch.** An anchor is updated in the same change, never the expected value:
- M5: `master_ch6.py` anchor `moves \gls{em} by 6.5~pp` becomes `on the reference surface is 6.5~pp`.
- Two anchors contain newlines: `scores 0.935 against\nH2O-Danube3-500M's` and `(exact\n$p = 0.0023$`. Keep those breaks when rewrapping.
- M1-M4 and M6 touch no anchor. The `rq1` check still finds "trade-off" and "Qwen2.5-0.5B at Q4\_K\_M" in 6.1's first paragraph.

**MINOR/NIT (reviewer only, not verified except MINOR-2).**
- **MINOR-1** l.85 "ordered by the requirement each addresses" is not a priority order, and steps 1 and 2 address the same requirements. l.8 and Ch5's hand-off promise "order of priority".
- **MINOR-2 (a Ch5 finding; verifier CONFIRMED)** l.103-104: step 3 adds full-stack memory, which Ch5's hand-off does not name. Ch4 hands the memory shortfall to Ch5 (ch4:342-344, 395-396), and Ch5 never takes it up. The fix belongs in Ch5 (§5.1 "Unmeasured points and axes", and the hand-off). The step also measures memory for SmolLM2 only, not for the selected model.
- **MINOR-3** l.32: 3,122 ms is quoted without its owner (the Mémoire d'Ingénieur's latency experiment) or n = 226.
- **MINOR-4** l.25, 27: the test and n are never named; "the test" has no antecedent.
- **MINOR-5** l.93-94 "the parser dispatches them" drops Ch5's "nearly" (98.9%).
- **MINOR-6** l.71 "hold for a cooled board" generalises beyond one board and one llama.cpp build (ch5:301-307). The latency sentence also sits oddly in the paragraph on accuracy cost.
- **MINOR-7** l.75-80: the family-control paragraph is not among the contributions 6.2 promises (l.6-7). It should be tied to RQ1.
- **NIT-1** l.106: the document ends on a sub-point of step 3; a one-sentence close is optional.
- **NIT-2** l.23 and l.26: two metaphors, "has a measured price" and "buys no established accuracy".
- **NIT-3** l.32-33 "The memory ceiling is confirmed": it is the model's memory that is confirmed, as Ch4 says.
- **NIT-4** l.66-69 and l.75-78 are sentences of about 49 and 51 words.
- **NIT-5** l.97 "unreadable" matches Ch3; the drift is Ch5's "degraded".
- **NIT-6** l.37-38: the range covers all 18 configuration-and-split rows, not six configurations.

**Unverified.** l.89-90 "widest margin" holds on ratios, but whether it holds depends on whether the prefill allowance counts as a requirement.

**For other issues.**
- **NEW-1 (verifier, MAJOR; for issue 08 / B12).** `frontmatter/abstract.tex` l.17-28 (committed `0e1421f`) repeats M1-M3 almost word for word. There, "0.935 exact match on the golden set" follows "200 recorded commands", which makes the speech reading more likely than in Ch6. The French and Arabic abstracts are translated from it. Whatever 6.1 becomes, re-derive all three abstracts from it.
- **MINOR-2** above is a Ch5 edit.

**Decisions only you can make:**
- Each of M1-M5 (MAJOR) and M6. The recommendation is to take all six, with the verifier's corrected wording.
- Whether to take MINOR-2 in Ch5, and with it whether step 3 keeps "full-stack memory".
- Which other MINOR/NIT items to take. MINOR-1 (priority order, promised by Ch5's hand-off) and MINOR-5 ("nearly") are the cheapest.
- Whether NEW-1 is fixed with Ch6, which is recommended because the abstract carries 6.1 at its strength, or is logged against issue 08.

### 2026-09-24 -- author's decisions, and what was applied

The author approved **M1-M6 with the verifier's corrected wording**, and **NEW-1** (fix the
abstracts in the same change). Applied to `thesis/master/ch6_conclusion.tex`:
- **M1 + M2:** 6.1 now opens "Across the three fine-tuned \glspl{slm} timed on the Raspberry~Pi~5,
  which span RQ1's 0.36--1.2~B range, the accuracy--efficiency trade-off among their Q4\_K\_M
  artefacts reduces to two non-dominated configurations …". It ends "at 0.935 \gls{em} on the golden
  split, scored on reference text".
- **M3:** "Both misses reflect one tendency: when a configuration is wrong or out of domain, it emits
  a well-formed command rather than \texttt{unknown}." This is Ch4's sentence.
- **M4:** 6.2's C2 paragraph now opens on the corpus. The splits are assigned by family, so every
  in-domain figure is on held-out families, and the leakage gate is clean on all four axes it checks.
  The zero-shot sentences follow, unchanged.
- **M5:** "the family difference in \gls{em} on the reference surface is 6.5~pp". A second sentence
  says it is a difference between single trained adapters that also differ in how the system prompt
  is rendered and in training session, and adds the `sec:threats-internal` pointer.
- **M6:** "Pairs of that kind act on what the model is trained to output for input that reads as a
  supported command". The verifier's corrected fix does not say that only this step tests the
  hypothesis.

**Abstracts (NEW-1).** M1-M3 are carried into `frontmatter/abstract.tex`, `frabstract.tex` and
`arabstract.tex`:
- "Among the three models timed on the board, the trade-off at Q4\_K\_M reduces to two …";
- "…, scored on reference text";
- "both misses reflect one tendency …".

The method paragraph's "three are quantised at two levels and measured on the board" had the same
M1 overclaim. It now reads "…, their Q4\_K\_M artefacts are timed on the board" in all three
languages.

**Script.** One anchor changed in `master_ch6.py`: `moves \gls{em} by 6.5~pp` became
`on the reference surface is 6.5~pp`. The expected value is unchanged. The anchors are
whitespace-tolerant (`lib.py` l.94), so the rewrapped lines needed no other change.

**Final state.**
- Script: 0 FAIL, 0 WARN, 54 PASS.
- The self-test passes.
- `check_tex`: clean on Ch6 and the English abstract. On the French and Arabic abstracts it reports
  only non-ASCII notes, and marks them "fine under XeLaTeX".
- Build (`latexmk main_master.tex`, incremental): 0 errors, no undefined references or citations,
  no overfull boxes.

**Not applied.** The author asked for M1-M6 and the abstracts only, so the following are left as
written and stay available:
- MINOR-1 to MINOR-7 and NIT-1 to NIT-6;
- MINOR-2's Ch5 edit, on full-stack memory in Ch5 §5.1 and its hand-off.

### 2026-09-24 -- follow-up: MINOR-1, MINOR-2 (Ch5) and MINOR-5 applied

Each was checked against its source first. The verifier had not checked MINOR-1 or MINOR-5.

- **MINOR-2 (Ch5):** confirmed that nothing in `results/` measures full-stack memory, for any configuration.
  - Ch5 §5.1 "Unmeasured points and axes" now lists three gaps. The third is memory: marker area
    encodes the language-model process, while the 2.5~GiB ceiling applies to the full stack, which was
    not measured (`sec:selection`). The markers therefore show each model's distance from the ceiling
    on its own, not whether the deployed stack fits.
  - The lead-in's "limits what the frontier can be taken to mean" became "the figure", because memory
    is not a frontier axis.
  - Ch5's hand-off now names the third step as SmolLM2-360M "end to end, in latency and in full-stack
    memory". Ch6's step 3 therefore no longer introduces something Ch5 did not raise.
- **MINOR-1 (Ch6 l.85):** l.8, the section title and Ch5's hand-off all say "priority", but the list
  said "ordered by the requirement each addresses". It now says "in order of priority", and gives the
  basis in the steps' own terms:
  - the first two address the requirements missed by the widest margin, with the step that needs no
    retraining first;
  - the third completes the frontier and does not bear on the selection.
- **MINOR-5 (Ch6 l.93):** "the parser dispatches nearly all of them". Ch5 l.141-144 says "nearly
  every" (98.9%), and 1.1% resolve to a safe action.

Not changed: the reviewer's other half of MINOR-2. Step 3 measures memory only for SmolLM2-360M,
although the selected model's full-stack memory is also unmeasured. Widening the step changes its
scope, so it is left for the author.

Scripts: Ch5 0 FAIL, 1 WARN (the justified "not guaranteed", now l.207), 96 PASS; Ch6 0 FAIL, 0 WARN,
54 PASS; `check_tex` clean on both. Build: 0 errors, no undefined references, no overfull boxes.

### 2026-09-24 -- author's decision: step 3 keeps its scope

The remaining half of MINOR-2 (step 3 measures full-stack memory for SmolLM2-360M only, not for
the selected Qwen2.5-0.5B) is **kept as written, by the author's choice**. The Mémoire d'Ingénieur
does not measure full-stack memory either.

A wider step 3 was drafted and discarded without a commit. It would have added Qwen2.5-0.5B's
full-stack memory, scoped "the selection does not depend on the outcome" to the SmolLM2 part, and
reworded the priority sentence and Ch5's hand-off to match.

The reasons for keeping the current scope:
- The gap is stated in Ch4 §4.7, Ch5 §5.1 and Ch6 §6.1 ("confirmed for the language-model process
  only"), so nothing is hidden or overclaimed.
- Step 3 completes the frontier, which is the Master's question. The deployed system's memory is a
  system-validation question.
- Ch5's hand-off and Ch6 agree as committed.

**For the defence.** Expect the question "why measure the rejected model's memory and not the
deployed one's?". The answer: the Master's future work completes the trade-off, and the
language-model process uses 0.68 of the 2.5 GiB ceiling. Do not claim that the rest of the stack
fits, because no figure for it exists.

Nothing is left open in this issue.
