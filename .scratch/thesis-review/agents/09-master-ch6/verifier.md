# Issue 09 -- Master Ch6 -- verifier report

Chapter: `thesis/master/ch6_conclusion.tex` (107 lines) as in the working tree (= `602447e`).
Checked against Ch1 l.88-125, Ch3 §3.2 (l.123-245), Ch4 l.9-16, 120-206, 266-396, Ch5 in full (as
committed, `1bd566e`), `results/surface_b.csv`, `results/mcnemar.csv`,
`results/nfr9_nfr18_abstention.csv`, `data/check_leakage.py`, `data/check_grammar.py`,
`tools/review/master_ch6.py`, issue 05 (C6 and the author's decisions), and the Master abstracts.
Nothing edited except this file; no build run.

## 1. Summary

| ID | Sev (reviewer) | Verdict | Sev (verified) | Evidence | Fix judgement / corrected fix |
|---|---|---|---|---|---|
| MAJOR-1 | MAJOR | CONFIRMED | MAJOR | (a) ch4:334 "the benchmark timed only Q4\_K\_M on the board"; ch5:90-91 "strictly a Q4\_K\_M frontier"; `surface_b.csv` smollm2 Q8\_0 golden 0.79 > Q4\_K\_M 0.76, so an untimed Q8\_0 point can be non-dominated. (b) ch5:50 and ch5:328-329 "statements about these models and not about parameter classes". RQ1's own range (ch1:94) is not a defence: the answer can name the range without asserting the class | Fix correct in substance. Use "timed" rather than "measured" (the Q8\_0 accuracy *was* measured; only the timing is Q4-only), and avoid "at Q4\_K\_M" twice in one sentence. Danube (fine-tuned, not quantised) is correctly excluded by "three". See §3 |
| MAJOR-2 | MAJOR | CONFIRMED | MAJOR | ch4:14-16 (all benchmark EM is on reference text, "expected to overstate" audio); ch4:388-389 lists it first among the qualifications to the selection; ch3:160 golden = "200 audio files"; ch5:286-289. Ch6 l.30-42 reproduces every other §4.7 qualification and omits this one; "reference text" appears nowhere in Ch6 | Fix correct but breaks the anchor `at 0.935 \gls{em} on the golden split`. Anchor-preserving alternative: append ", scored on reference text" (Ch4's term; "reference transcripts" sits next to Ch6 l.66's "reference surface", a different concept) |
| MAJOR-3 | MAJOR | CONFIRMED | MAJOR (bordering BLOCKER) | ch4:149-150 "Both reflect one tendency"; `nfr9_nfr18_abstention.csv` false-command 0.1867-0.3933, so 60.7-81.3% of OOD items do get `unknown` (ch5:124-127). Read literally, "when ... out of domain, the parser emits a well-formed command" is false for the majority of OOD items | Fix correct: it is Ch4's sentence verbatim. "tendency" is not on the script's hedge list. Scope agrees with Ch5 R1 (in-domain abstention "almost absent", ch5:135-136; OOD abstention is the majority). No anchor affected |
| MAJOR-4 | MAJOR | CONFIRMED | MAJOR | ch1:112-117 C2 = the dataset pipeline; ch4:200-206 places the zero-shot baseline under the family control, with no link to C2; ch6:62-63 itself says the baseline attributes nothing to the fine-tune, the only route by which the corpus acts | **Fix introduces two errors.** (1) "Every accuracy figure ... on template families held out from training": false for `test_ood` (150 authored/harvested transcripts, ch3:161, not template families), which enters Ch6's own figures (the 590 zero-shot items, l.60; the 3,540-decode ablation, l.49; EM on `test_ood` in `surface_b.csv`). (2) "leakage gate ... pass on every split": the gate checks train against val/test\_synth/golden, those three against each other, noise and wake partitions (ch3:184-188; `check_leakage.py` never reads `test_ood`). Ch3 says "all four axes are clean", not "every split". Corrected: "every in-domain accuracy figure", "clean on all four axes it checks". `sec:dataset` exists (ch3:124). See §3 |
| MAJOR-5 | MAJOR | CONFIRMED | MAJOR | ch4:171 "the family difference ... is 6.5 pp"; ch4:176 "measure a family difference"; ch5:206-213 two declared differences "could contribute" and it "should be quoted with them"; ch5:221-223 single adapters, one seed. Ch6 keeps "exploratory" (l.77) and the convergence caveat (l.77-78), and l.79 says "measures a family difference", but the lead verb "family moves EM" is causal | Fix correct and not a new caveat (Ch4:188-193 and Ch5:201-223 carry both). Tighten "chat-template handling" to Ch4's fact ("how the system prompt is rendered") and split at the parenthesis (NIT-4). Changes the anchor `moves \gls{em} by 6.5~pp`; the two newline anchors survive only if the line breaks are kept |
| MAJOR-6 | MAJOR | PARTLY | MINOR | ch5:157-158, 170-177 (hypothesis, untested). Mitigated by ch6:85-86 "None of them is implemented or measured", which frames the whole list as untaken steps; the gate half ("changes only what is dispatched") is true by construction. What remains is one outcome verb ("change") for an unrun retraining | Fix's verb change is right. **Drop the added clause** "this one also tests the common-cause hypothesis": Ch5 as committed says *both* interventions would test it (ch5:173-176; issue 05 C6, which proposed limiting that to the pairs, was kept as written by the author), so "this one also" either duplicates Ch5 or implies the gate does not, contradicting it. See §3 |
| MINOR-2 | MINOR | CONFIRMED (Ch5 finding) | MINOR | Ch5 contains no "full-stack" and treats memory only as a frontier coordinate (ch5:19, 27, 30, 33, 54); ch4:342-344 states the gap and ch4:395-396 hands "these shortfalls" to Ch5; Ch5's hand-off (ch5:337-338) names only SmolLM2's end-to-end measurement. Ch6's memory clause is not new to the document (ch4:342-344; ch6:32-33), so the defect is on Ch5's side. The logical gap (the selected configuration's full-stack memory matters more) is real | Reviewer's fix correct |
| NEW-1 | -- | NEW | MAJOR (frontmatter; issue 08 scope) | `thesis/master/frontmatter/abstract.tex` l.17-28 (and the FR/AR translations, `0e1421f`) carry MAJOR-1, 2 and 3 verbatim: "The trade-off reduces to two non-dominated configurations"; "0.935 exact match on the golden set" two sentences after "a golden test set of 200 recorded commands", which reads as speech accuracy; "emitting a well-formed command rather than declining". STATE.md l.1606-1608 tells B12 to copy 6.1 at its strength | Whatever wording lands in Ch6 for MAJOR-1/2/3 must be carried into all three abstracts in the same change, or logged against issue 08 |

## 2. Reasoning per finding

### MAJOR-1 -- CONFIRMED, MAJOR

Attempted disproof 1: RQ1 is phrased "across small language models of 0.36--1.2 B parameters"
(ch1:93-96), so an answer phrased in RQ1's terms is legitimate. This fails. The answer can *cite*
the range, but l.20-21 makes the class the subject of "reduces to two", and Ch5 limits this twice:
ch5:50 ("a statement about a model that was measured, not about a parameter class") and
ch5:328-329. Ch5's own R6 revision (issue 05) removed exactly this size-class wording from Ch5, so
reinstating it in Ch6 undoes a verified fix.

Attempted disproof 2: Ch4 l.373-375 says the Q8\_0 exclusion "does not change the ranking". True,
but that is about the *selection* (no Q8\_0 exceeds 0.935), not about the *frontier*. SmolLM2-360M
Q8\_0 scores 0.790 on golden against Q4\_K\_M's 0.760 (`surface_b.csv`). If its latency falls below
Qwen2.5-0.5B Q4's 1,072 ms, it is a third non-dominated point; its latency was never measured
(ch4:334). So "reduces to two" holds only over the three timed points, which is what ch5:91 says.

Four models were fine-tuned; three were quantised and timed on the board (ch1:118-119, ch4:197-198).
"quantised for a Raspberry Pi 5" already excludes Danube, and "three" in the fix is correct.

### MAJOR-2 -- CONFIRMED, MAJOR

Attempted disproof: Ch4 l.14-16 declares chapter-wide that every benchmark EM is on reference text,
so a reader who has read Ch4 knows. This fails for two reasons. Ch6 l.30-42 restates the §4.7
"Qualifications to the selection" item by item (re-baselined constraints, 622 ms, memory for the
LM process only, abstention miss, "not every requirement") and leaves out exactly the first of
them (ch4:388-389). Selective restatement of a qualification list is a stronger claim. And this is
the sentence STATE.md marks for the abstract, where the omission has already propagated (NEW-1).
Ch3 defines `test_golden` as "200 audio files, 200 transcripts" (ch3:160), so "on the golden split"
alone does not settle which input.

On the fix: Ch4 and Ch5 say "reference text" (ch4:15, 388; ch5:108, 274, 281, 286). Ch6 already uses
"reference surface" (l.66) for the fp16 PyTorch path, so "reference transcripts" next to it invites
confusion; use Ch4's term. Do not add the 0.690 CRR (Table 3 keeps the speech figure in Ch5).

### MAJOR-3 -- CONFIRMED, MAJOR

No disproof holds. The claim is literally false for out-of-domain input: the complement of
0.1867-0.3933 is 0.6067-0.8133 abstention (ch5:125-127). "when wrong" is near-true (98.9% of
in-domain errors dispatch, ch5:143-144), but the conjunction with "or out of domain" makes the
sentence a rule the same sentence's numbers refute. Ch4's "one tendency" is the qualifier that
keeps it true. "tendency" is not in the script's hedge regex. Ch4's own sentence is loose about OOD,
since most OOD items do get `unknown`. It is the Ch4 qualifier, so inheriting it verbatim satisfies
"same value, same qualifier". A more exact rewording would need a new percentage form, which the
script would flag.

### MAJOR-4 -- CONFIRMED, MAJOR; the proposed fix is wrong in two places

Attempted disproof: the zero-shot baseline could belong to C2, because Ch3 l.125-127 says the
dataset "trains and evaluates every model in Chapter 4 ... which is the labour Contribution C2
names". This fails. The paragraph's own last sentence (l.62-63, matching ch5:230-234) says the
baseline does not attribute the gain to the fine-tune. Fine-tuning is the only route by which the
corpus acts, so the paragraph concludes nothing about C2. Ch4 presents the baseline under the family
control (ch4:200-206) and never ties it to any contribution. It does not belong to C3 either: C3 is
the harness over three of four models at two quantisation levels (ch1:118-124), and the baseline is
four models at fp16. The paragraph is correct content under the wrong label, and the section's
promise "for each contribution" (l.6-7) is unmet for C2.

The fix, checked against primary sources:
- `\label{sec:dataset}` exists (ch3:124).
- Held out: `val_synth` and `test_synth` are held-out families (ch3:158-159, 180-182). The golden
  transcripts come from the 12 `test_synth` families, held out from training (ch3:202-204). Ch5:264-269
  (golden and test\_synth share families) does not contradict "held out from training". So the claim
  is true for the **in-domain** splits.
- It is **false for `test_ood`**: 150 authored and harvested transcripts, not template families
  (ch3:161). Ch6's own figures include it: the 590 zero-shot items (l.60 = 240+200+150) and the
  3,540 ablation decodes (l.49). `surface_b.csv` also reports EM on `test_ood`. "Every accuracy
  figure" therefore overclaims.
- The leakage gate does not run "on every split". Ch3:184-188 lists its four axes: train against
  val/test\_synth/golden, those three against one another, the noise partition, and the wake corpus.
  `data/check_leakage.py` loads no `test_ood`. The conformance check does cover every split
  (`check_grammar.py` DEFAULT\_FILES includes `test_ood.jsonl`; ch3:188-189). The combined wording
  "leakage gate and conformance check pass on every split" is wrong for the gate.
- Nothing here is a caveat, so the no-new-caveat rule is not engaged. Do not add anything about the
  sealed annotation pass as evidence of label quality: ch5:259-263 calls its null result
  uninformative.

### MAJOR-5 -- CONFIRMED, MAJOR

Attempted disproof: Ch6 already carries "an exploratory test" (l.77), the convergence caveat
(l.77-78) and "measures a family difference" (l.79-80), so the paragraph as a whole is not causal.
This is partly right: most of the paragraph is at Ch4's strength. But the lead clause "model family
moves EM by 6.5 pp" makes family the cause, and ch5:211-212 says the difference "should be quoted
with" the two declared differences (the system prompt folded into the user turn, and the separate
training session), which Ch6 omits. Both are stated in Ch4 (l.188-193) and Ch5 (l.201-213, 221-223),
so restating them imports no new caveat. The minimal fix is the non-causal verb plus one clause
naming them. "reference surface" is worth one word: Danube exists only there (ch4:193), and the
0.935 here is the fp16 figure, which happens to equal the deployed one (ch4:219).

### MAJOR-6 -- PARTLY, downgraded to MINOR

The reviewer is right that "change what the model treats as an available answer" states the
outcome of a retraining that was not run, and that it leans on the premise of Ch5's untested
hypothesis (ch5:157-158, 170-177). Two things lower the severity:
- l.85-86 says just above that none of the three steps "is implemented or measured in this
  document", so no reader takes l.99 as a result.
- The contrast half ("the gate changes only what is dispatched") is true by construction.

What is left is one verb. Step 1 already uses "targets" (l.93), so "target"/"act on" is consistent.

The added clause is not safe. Ch5 as committed says "Two interventions would test it and would also
address the failure" (ch5:173-176), naming both the gate and the pairs. Issue 05's C6 proposed
limiting the test to the pairs, and the author kept the text as written (issue 05, "Kept as
written: C5-C14"). "this one also tests the common-cause hypothesis" either repeats Ch5 or, through
"this one", implies the gate does not, which disagrees with Ch5 as written. Present-tense "tests"
for a step not taken is also stronger than Ch5's "would test". Drop the clause. If the hypothesis
link is wanted, attribute it: "Section~\ref{sec:failure-modes} names both steps as tests of its
common-cause hypothesis."

### MINOR-2 -- correct (a Ch5 finding)

Ch5 never mentions full-stack memory. Ch4 hands the shortfalls to Ch5 (ch4:395-396), and Ch5's
hand-off (ch5:337-338) omits memory. Ch6's clause is grounded in Ch4 l.342-344, so it is not new to
the document, but it is new relative to Ch5's hand-off. The reviewer's Ch5 edits are right. So is
the logical point: the selected configuration's full-stack memory is the one that matters.

### NEW-1 -- MAJOR, frontmatter (issue 08)

`abstract.tex` l.17-28, committed in `0e1421f`, copies 6.1 at the strength this review is removing:
- "The trade-off reduces to two non-dominated configurations", with no range and no Q4\_K\_M scope
  (MAJOR-1);
- "0.935 exact match on the golden set", two sentences after "a golden test set of 200 recorded
  commands". That juxtaposition makes the speech reading more likely than in Ch6 (MAJOR-2);
- "emitting a well-formed command rather than declining" (MAJOR-3).

`frabstract.tex` l.25 and `arabstract.tex` l.26 are translations of it. STATE.md l.1606-1608
instructs B12 to match 6.1, so the abstracts must be re-derived after the Ch6 fixes land.

## 3. Corrected wording for each surviving finding

**MAJOR-1 + MAJOR-2 (l.20-23), one sentence:**

```
Across the three fine-tuned \glspl{slm} timed on the Raspberry~Pi~5, which span RQ1's
0.36--1.2~B range, the accuracy--efficiency trade-off among their Q4\_K\_M artefacts reduces to two
non-dominated configurations, SmolLM2-360M and Qwen2.5-0.5B, and the selection rule deploys
Qwen2.5-0.5B at Q4\_K\_M, at 0.935 \gls{em} on the golden split, scored on reference text.
```

(If the reviewer's shorter form is preferred: "Across the three fine-tuned \glspl{slm} timed on the
Raspberry~Pi~5, spanning the 0.36--1.2~B range, the accuracy--efficiency trade-off at Q4\_K\_M reduces
to ..." Either is correct. "timed" is the load-bearing word.)

**MAJOR-3 (l.38-40):**

```
... and the false-command rate on out-of-domain input is 0.1867--0.3933 against $\leq$~0.05. Both
misses reflect one tendency: when a configuration is wrong or out of domain, it emits a well-formed
command rather than \texttt{unknown}.
```

**MAJOR-4 (l.58), replacing the first sentence only; l.59-63 unchanged:**

```
The dataset that trains and evaluates every model of the comparison is the label-first corpus of
Contribution~C2. Its splits are assigned by template family, so every in-domain accuracy figure is
measured on families held out from training, and its leakage gate is clean on all four axes it
checks (Section~\ref{sec:dataset}). None of the accuracy the comparison reports is available from
the pretrained models as prompted. Prompted zero-shot at fp16, ...
```

**MAJOR-5 (l.75-78); keep the two line breaks shown, which the script's anchors contain:**

```
At matched size, the family difference in \gls{em} on the reference surface is 6.5~pp: at about
0.5~B parameters, Qwen2.5-0.5B scores 0.935 against
H2O-Danube3-500M's 0.870, on 15 against 2 discordant items (exact
$p = 0.0023$, an exploratory test). It is a difference between single trained adapters that also
differ in how the system prompt is rendered and in training session, under the identical
three-epoch budget at which no model is shown to have converged (Sections~\ref{sec:iso-parameter}
and~\ref{sec:threats-internal}).
```

**MAJOR-6 -> MINOR (l.99-101):**

```
Pairs of that kind act on what the model is trained to output for input that reads as a supported
command, where the gate acts only on what is dispatched, so the two steps are complementary.
```

(Optional, and only in this form: "Section~\ref{sec:failure-modes} names both steps as tests of its
common-cause hypothesis." Not "this one also tests".)

**MINOR-2:** the reviewer's Ch5 wording as proposed (§5.1 "Three gaps", memory as the third; hand-off
"of latency and full-stack memory").

**NEW-1:** re-derive `abstract.tex` l.24-28 (and FR/AR) from the final 6.1 sentence. Minimum: "Among
the three models timed on the board, the trade-off at Q4\_K\_M reduces to ..."; "0.935 exact match on
the golden set's reference text"; "tending to emit a well-formed command rather than decline".

All proposed wording was checked against the script's hedge regex (may, might, could, perhaps,
possibly, likely, suggest(s), appear(s), seem(s)) and the banned phrases. It contains none of them
and adds no number absent from Ch1-Ch5.

## 4. Script-anchor impact (`tools/review/master_ch6.py`)

| Fix | Anchor affected | Action |
|---|---|---|
| MAJOR-1 | none. `r.expect("rq1", ...)` requires "trade-off" and "Qwen2.5-0.5B at Q4\_K\_M" in the first paragraph of 6.1; both are kept | none |
| MAJOR-2 (my form) | `at 0.935 \gls{em} on the golden split` (l.59) kept, text appended after it | none. The reviewer's form ("on the reference transcripts of the golden split") breaks it; if that form is taken, change the anchor to `at 0.935 \gls{em} on the reference`, with the same expected value |
| MAJOR-3 | `input is 0.1867--0.3933 against` (l.81-82) kept | none |
| MAJOR-4 | none (no anchor in the first sentence of that paragraph; `four models match none of the 590 items` kept) | none |
| MAJOR-5 | `moves \gls{em} by 6.5~pp` (l.116) removed; `scores 0.935 against\nH2O-Danube3-500M's` (l.118) and `(exact\n$p = 0.0023$` (l.123) contain newlines and break on any rewrap; `H2O-Danube3-500M's 0.870` and `on 15 against 2 discordant` kept | change l.116's anchor to `on the reference surface is 6.5~pp`, with the same expected value and places=1. Either keep the line breaks as in §3, or make l.118 and l.123's anchors whitespace-tolerant (for example `scores 0.935 against`); never change the expected values |
| MAJOR-6 | none | none |
| MINOR-2 | Ch5 edit: `master_ch5.py` has no "Two gaps"/"gaps" anchor (checked by grep), so none breaks | none |
