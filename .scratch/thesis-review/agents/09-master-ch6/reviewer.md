# Issue 09 -- Master Ch6 (Conclusion and future work) -- reviewer report

Chapter: `thesis/master/ch6_conclusion.tex` (107 lines, no `\cite`), as committed at `602447e`.
Dimensions: D1, D2, D4, D5c, D6, D8, D10, D11, D12 (D3, D5a/b/d/e/f, D7, D9 are the script's).
Script re-run: `tools/review/master_ch6.py`: 0 FAIL, 0 WARN, 54 PASS (baseline unchanged).
Ch5 was compared as committed (`1bd566e` and earlier).

## 1. Verdict

**Ready after fixes.** The chapter has the frozen outline. It opens by saying what it does, and it
keeps both of Ch5's hand-off promises: it decides RQ1, and it gives the three steps in Ch5's
order. Every number is right. There are no BLOCKERs. The RQ1 verdict matches Ch4 §4.7 on every
point the issue lists.

The six MAJOR findings share one pattern. The chapter removes a qualifier that Ch4 or Ch5 attached
to a claim, and so makes the claim stronger than the evidence supports. This is exactly the
failure that "unhedged means no hedging words, not stronger claims" warns about. The instances
are:
- the frontier generalised beyond the three Q4\_K\_M points;
- 0.935 quoted without "reference text";
- the abstention "tendency" stated as a rule;
- the family difference stated causally, without the declared differences Ch5 says must go with it;
- the untested training-data hypothesis stated as the effect of step 2.

One MAJOR is structural: the C2 paragraph does not report on C2 as Ch1 states it. Every fix is a
wording change that adds no number.

## 2. Scorecard

| Dim | Result |
|---|---|
| D1 Structure | ISSUES (1 NIT): the outline matches prd §3.1 item 6 exactly; the opening states what the chapter does; the document ends on a list sub-point |
| D2 Argument coherence | ISSUES (4): MAJOR-4 (C2 mismatch), MINOR-1 (ordering criterion), MINOR-7 (paragraph with no anchor), NIT-5 (term drift) |
| D4 Claims and hedging | ISSUES (9): MAJOR-1, 2, 3, 5, 6; MINOR-4, 5, 6; NIT-6. No hedging words; no unearned absolutes (the reachability claim at l.53-54 is earned by construction, ch3 l.110-117) |
| D5c Uncited factual claims | PASS: no claim about literature or a tool needs a `\cite`. The reachability property restates Ch3/Ch4, and Ch1 l.108 cites `llamacpp` for GBNF |
| D6 Cross-document ownership | ISSUES (1 MINOR): no acoustic-robustness experiment, no TTFT or preemption, no voice-UAV literature, no hardcoded chapter number. The *M\'emoire d'Ing\'enieur* is never named, so it cannot be misnamed. But the 3,122 ms figure it owns is quoted without its owner (MINOR-3) |
| D8 Language and style | ISSUES (2 NIT): acronyms are correct (`\gls{slm}`, `\glspl{slm}`, `\gls{em}`; nothing hand-expanded); British spelling; ASCII only; tense is consistent. Some long sentences (NIT-4) |
| D10 Examiner view | ISSUES: see §5; one of the three hardest questions is not answered in Ch6 |
| D11 Self-containment | PASS: RQ1 and C1-C3 are defined in Ch1 (l.93, l.107-125); "failure clause", "reference/deployed surface", "multi-model benchmark" and "exploratory family" are all defined upstream; no project-internal words |
| D12 Headings and register | ISSUES (1 NIT): the three headings are short noun phrases in sentence case, consistent with the document; two mild metaphors |

## 3. Findings (BLOCKER -> NIT)

| # | Sev | Dim | file:line | Quoted text | Problem | Evidence | Proposed fix |
|---|---|---|---|---|---|---|---|
| MAJOR-1 | MAJOR | D4b | ch6_conclusion.tex:20-21 | "Across fine-tuned \glspl{slm} of 0.36--1.2~B parameters quantised for a Raspberry~Pi~5, the accuracy--efficiency trade-off reduces to two non-dominated configurations" | (a) The frontier has only three Q4\_K\_M points, and six configurations exist. SmolLM2-360M Q8\_0 scores 0.790 > 0.760 on golden, and its latency was never measured, so "reduces to two" across the configurations is not established. (b) Stated for the parameter class, although Ch5 twice limits the reading to the models measured | ch5:87-91 ("the frontier is strictly a Q4\_K\_M frontier"); ch4:334 (Q8\_0 not plotted); `results/surface_b.csv` smollm2 Q8\_0 golden 0.79; ch5:50, ch5:328-329 ("statements about these models and not about parameter classes"); ch5:34-35 | "Across the three fine-tuned \glspl{slm} measured on the Raspberry~Pi~5, spanning the 0.36--1.2~B range, the accuracy--efficiency trade-off at Q4\_K\_M reduces to two non-dominated configurations, SmolLM2-360M and Qwen2.5-0.5B, ..." |
| MAJOR-2 | MAJOR | D4b | ch6_conclusion.tex:22-23 | "the selection rule deploys Qwen2.5-0.5B at Q4\_K\_M, at 0.935 \gls{em} on the golden split" | Drops the qualification Ch4 attaches to this selection: accuracy is on reference transcripts, not on speech. The golden split is also 200 audio files (ch3 l.160), so "on the golden split" alone reads as deployed accuracy. This is the sentence STATE.md marks for the abstract | ch4:388-389 ("The selection is made against reference-text accuracy"); ch4:14-16; ch5:286-289; ch3:160 | "... at 0.935 \gls{em} on the reference transcripts of the golden split." (Do not add the speech-input figure: Table 3 keeps it in Ch5) |
| MAJOR-3 | MAJOR | D4b/d | ch6_conclusion.tex:39-40 | "when wrong or out of domain, the parser emits a well-formed command rather than \texttt{unknown}" | Ch4's qualifier "one tendency" is dropped, which turns a tendency into a rule. Read literally, the rule is refuted by the figures it follows: a false-command rate of 0.1867-0.3933 means 60.7-81.3% of out-of-domain items do get `unknown`. It borders on BLOCKER ("claim the evidence refutes"); rated MAJOR because the intended reading is Ch4's | ch4:149-150 ("Both reflect one tendency: ..."); ch5:124-127 ("The parser does abstain ... on 60.7\% to 81.3\% of items") | "... against $\leq$~0.05. Both misses reflect one tendency: when a configuration is wrong or out of domain, it emits a well-formed command rather than \texttt{unknown}." |
| MAJOR-4 | MAJOR | D2a/b | ch6_conclusion.tex:58 | "None of the accuracy the comparison reports is available from the pretrained models as prompted (Contribution~C2)." | Ch1's C2 is the label-first dataset pipeline: family-level splits, round-trip augmentation, dataset card, frozen and checksummed. The paragraph labelled C2 reports the zero-shot baseline, which is not what C2 promises. Its own last sentence says the baseline does not attribute the gain to the fine-tune, the only route by which the corpus acts. So the paragraph establishes nothing about C2, and nothing of what C2 does promise is summarised | ch1:112-117; ch3:174-190 (family splits 96/12/12, leakage gate clean on all four axes, conformance check on every label); ch6:62-63 | Open the paragraph on C2 as Ch1 states it, then keep the baseline: "Every accuracy figure the comparison reports is measured on template families held out from training (Contribution~C2): the label-first pipeline assigns splits by family, and its leakage gate and conformance check pass on every split (Section~\ref{sec:dataset}). None of that accuracy is available from the pretrained models as prompted. Prompted zero-shot ..." (rest unchanged) |
| MAJOR-5 | MAJOR | D4b | ch6_conclusion.tex:75 | "At matched size, model family moves \gls{em} by 6.5~pp" | Causal wording ("family moves EM"). Ch4 reports "the family difference is 6.5 pp". Ch5 says two declared differences (the system prompt folded into the user turn, and a separate training session) could contribute, and that the difference "should be quoted with them". Ch5 also says it is a difference between single trained adapters (one seed). Ch6 quotes it without any of these, and without "reference surface" | ch4:171; ch5:206-213; ch5:221-223; ch4:188-193 | "At matched size, the family difference on the reference surface is 6.5~pp: ... (exact $p = 0.0023$, an exploratory test), between single trained adapters that also differ in chat-template handling and training session, under the identical three-epoch budget at which no model is shown to have converged (Sections~\ref{sec:iso-parameter} and~\ref{sec:threats-internal})." (Split into two sentences; see NIT-4) |
| MAJOR-6 | MAJOR | D4b | ch6_conclusion.tex:99-101 | "Pairs of that kind change what the model treats as an available answer on in-domain input, where the gate changes only what is dispatched" | States as a fact the effect of an intervention that was never run. It also assumes the premise of Ch5's common-cause hypothesis (abstention learned from the kind of training pair), which Ch5 labels "a hypothesis rather than a finding" that "cannot be tested on the present data". Ch5 offers these pairs as what would *test* that hypothesis | ch5:157-158, ch5:170-177 | "Pairs of that kind target what the model treats as an available answer on in-domain input, where the gate acts only on what is dispatched, so the two steps are complementary, and this one also tests the common-cause hypothesis of Section~\ref{sec:failure-modes}." |
| MINOR-1 | MINOR | D2b | ch6_conclusion.tex:85 | "Three steps follow from these results, ordered by the requirement each addresses." | The chapter opening (l.8) and Ch5's hand-off (ch5:335) promise an order "of priority". This criterion does not order anything: steps 1 and 2 address the same two requirements. The actual priority reasoning (no retraining; retraining; selection-independent) is left implicit | ch6:8; ch5:334-336; ch6:90, 101, 105-106 | "Three steps follow from these results, in order of priority: the first two address the abstention requirements the selected configuration misses, the first without retraining, and the third completes a measurement on which the selection does not depend." |
| MINOR-2 | MINOR | D2f / Ch5 | ch6_conclusion.tex:103-104 | "and no configuration's full-stack memory was measured. Measuring both for SmolLM2-360M ..." | (a) Adds full-stack memory to step 3. Ch5's hand-off names only "the end-to-end measurement of SmolLM2-360M", and Ch5 never discusses the memory shortfall, although Ch4 l.390-395 hands "these shortfalls" to Ch5. **Against Ch5:** the limitation is stated in Ch4 (l.342-344) but never taken up in Ch5. (b) Logical gap: if no configuration's full-stack memory was measured, the selected one's matters most, yet the step measures it only for SmolLM2-360M | ch5:87-100, ch5:337-338; ch4:342-344, ch4:390-395 | **Ch5 §5.1 "Unmeasured points and axes"** (after l.100): add "A third gap is memory: peak resident memory was measured for the language-model process only, and no configuration's full-stack memory was measured (Section~\ref{sec:selection})." Change "Two gaps" at l.87 to "Three gaps". Ch5 hand-off l.337: "... the end-to-end measurement of SmolLM2-360M, of latency and full-stack memory, that Section~\ref{sec:tradeoff} notes was not made." **Ch6 l.104:** "Measuring both for SmolLM2-360M, and full-stack memory for Qwen2.5-0.5B, completes ..." (or drop the memory clause, to match Ch5's hand-off as written) |
| MINOR-3 | MINOR | D6a / D4c | ch6_conclusion.tex:32 | "the budget is re-baselined to its measured p95 of 3{,}122~ms" | The figure belongs to the latency experiment of the *M\'emoire d'Ing\'enieur* (Table 3; Ch4 l.348-349 names the owner). Ch6 quotes it with neither the owner nor n = 226 (the issue's RQ1 focus line lists n = 226) | ch4:346-350; `results/exp2_latency_budget.md` n = 226 | "... re-baselined to its p95 of 3{,}122~ms over 226 segments, measured end to end by the latency experiment of the \emph{M\'emoire d'Ing\'enieur}." |
| MINOR-4 | MINOR | D4c | ch6_conclusion.tex:25, 27 | "a gap significant at the corrected $\alpha$" / "a difference ... that the test does not establish" | The test is never named in Ch6 ("the test" has no antecedent), and neither is n | ch4:271-275, 282-290 | l.25: "... significant under McNemar's test at the corrected $\alpha$ on the 200 golden items (Section~\ref{sec:statistics})"; l.27: "... that the same test does not establish" |
| MINOR-5 | MINOR | D4b | ch6_conclusion.tex:93-94 | "the parser dispatches them as executable commands instead of declining" | Drops Ch5's "nearly": 3 of the 282 in-domain errors (1.1%) resolve to a safe action | ch5:141-144 ("Nearly every ... 98.9\% dispatch an executable command") | "... the parser dispatches nearly all of them as executable commands instead of declining." |
| MINOR-6 | MINOR | D4b / D2d | ch6_conclusion.tex:71 | "The latency results hold for a cooled board" | Reads as holding for cooled boards in general, but Ch5 limits them to one board, one cooler and one `llama.cpp` build. The sentence also puts a latency assertion at the end of the C3 accuracy-cost paragraph, whose Impact is the sentence before it | ch5:84-85; ch5:301-307 | "The latency results are those of one cooled Raspberry~Pi~5 under one \texttt{llama.cpp} build: without active cooling, ..." (optionally open its own short paragraph) |
| MINOR-7 | MINOR | D2a/b | ch6_conclusion.tex:75-80 | "At matched size, model family moves ..." | The section is promised as "for each contribution" (l.6-7). This paragraph is not a contribution (Ch1 announces the control only in the outline, l.136-138), so it has no anchor. It serves RQ1: it qualifies the size reading of the trade-off | ch6:6-7; ch1:107-125, 136-138 | Add the anchor to the opening: "For RQ1, the size axis of the trade-off is confounded with family among the deployed models, and at matched size the family difference on the reference surface is 6.5~pp: ..." (combine with the MAJOR-5 fix) |
| NIT-1 | NIT | D1 | ch6_conclusion.tex:106 | "The selection does not depend on the outcome." | The last sentence of the document is a sub-point of step 3. No closing sentence returns to RQ1 | -- | Optional one-sentence close after `\end{enumerate}` that adds no claim, e.g. "The answer to RQ1 above holds at the strength stated; these steps address the requirements it leaves unmet." |
| NIT-2 | NIT | D12c | ch6_conclusion.tex:23, 26 | "the trade-off has a measured price" / "the largest model buys no established accuracy" | Mild metaphors; the plain wording carries the same claim | SKILL §2 Register | "Between the two, the trade-off is measured." / "On the split the rule ranks on, the largest model has no established accuracy advantage." |
| NIT-3 | NIT | D2e | ch6_conclusion.tex:32-33 | "The memory ceiling is confirmed for the language-model process only" | The ceiling is not what is confirmed; the configuration's memory is (Ch4's wording) | ch4:391 | "Its memory is confirmed against the ceiling for the language-model process only, at 0.68~GiB against 2.5~GiB." |
| NIT-4 | NIT | D8g | ch6_conclusion.tex:75-78, 66-69 | "At matched size, ... (Section~\ref{sec:iso-parameter})." | About 51 and 49 words; split each at the colon or semicolon | -- | Split after "discordant items (..., an exploratory test)." and after "moves by $-$1.5 to $+$1.5~pp." |
| NIT-5 | NIT | D2e | ch6_conclusion.tex:97 | "Training pairs for unreadable commands." | Ch6 follows Ch3's corrected wording ("made unreadable by recognition error"). Ch5's hand-off says "degraded commands", and ch5:176 says "degraded or truncated". The drift is on Ch5's side | ch3:178-180; ch5:163-164, 176, 337 | No Ch6 change; optionally align Ch5 l.176 and l.337 with "supported commands made unreadable" |
| NIT-6 | NIT | D4 | ch6_conclusion.tex:37-38 | "Across the six configurations, the safe-failure rate is 0.0000--0.1579" | The range is over configuration x split rows (18), not over six per-configuration rates. Ch4 l.144 does not say "configurations" | `results/nfr9_nfr18_abstention.csv` (per-split rows) | "Across the six configurations and three splits, the safe-failure rate is ..." |

## 4. Focus lines (issue 09)

- **Unhedged means no hedging words, not stronger claims.** FINDINGS: MAJOR-1, 2, 3, 5, 6; MINOR-5, 6. The four named qualifiers are otherwise kept:
  - "significant": l.25, 35;
  - "established": l.26-27, 35-36;
  - "exploratory": l.69, 77;
  - "not distinguishable": the Q8/Q4 comparison is not restated in Ch6;
  - "not separated from zero": l.66, never "no cost".

  The script found no hedging words.
- **No new caveat.** PASS for Ch6, with one Ch5 finding (MINOR-2). The full-stack memory gap used in step 3 is in Ch4 l.342-344 but never taken up in Ch5. It belongs in Ch5 §5.1 "Unmeasured points and axes" and in the Ch5 hand-off. The calibration-set prescription (l.95) is a method for the future step, not a limitation.
- **RQ1 verdict matches Ch4 §4.7 and Ch5 §5.1.**
  - Selected on EM against re-baselined constraints: PASS (l.30).
  - Misses 2,500 ms as specified by 622 ms (25%): PASS (l.31-32).
  - Re-baselined to 3,122 ms: PASS; n = 226 and the owner are missing (MINOR-3).
  - Memory confirmed for the language-model process only: PASS (l.32-33; wording NIT-3).
  - The rule is not restated, and "not ruled out" appears nowhere in Ch6: PASS.
  - Selection independent of SmolLM2's end-to-end latency, never "of the re-baselining": PASS (l.33-35).
  - The accuracy on which the selection rests loses Ch4's reference-text qualifier: MAJOR-2.
- **The three next steps match Ch5's hand-off and §5.2.** PASS on order and identity: the gate, then the training pairs, then SmolLM2-360M end to end. Ch6 adds full-stack memory to step 3 (MINOR-2). Step 2's justification states as fact what Ch5 calls an untested hypothesis (MAJOR-6). The ordering criterion given is not a priority (MINOR-1).
- **The 81 unknown training pairs.** PASS: l.97-99 "81 pairs, none of them a supported command made unreadable by recognition error" agrees with ch3:174-180 as corrected (20 / 21 / 40; every one `unknown` in its clean form). No "oversampling".
- **"What the comparison establishes" covers C1-C3 as Ch1 states them.**
  - C1: PASS (l.47-56 match ch1:107-111 and ch4:246-262).
  - C2: FINDING (MAJOR-4).
  - C3: PASS (l.65-71 match ch1:117-124, including "the pipeline as a whole, not quantisation").
  - Family-control paragraph: unpromised under "for each contribution" (MINOR-7), and overclaimed (MAJOR-5).
- **Carried check against the committed Ch5.** PASS, with one wording finding:
  - §6.2 P2 matches the 5.3.1 untuned-baseline paragraph ("does not attribute that accuracy to either intervention", ch5:232-234).
  - §6.2 P1 l.50-52 is an observation ("the fine-tuned models depart from the format once"), consistent with R2; nothing attributes structural validity to the fine-tune.
  - §6.3 step 1 against the 5.2 taxonomy: consistent except for the dropped "nearly" (MINOR-5).
- **D1.** PASS on the opening and on the outline. Ch5's promises are kept:
  - "decides RQ1 at that strength" is delivered (§6.1), though MAJOR-1/2/3 state parts above that strength;
  - "in order of priority, three steps" is delivered with the same three steps, though the stated order criterion is off (MINOR-1).

  The ending is NIT-1.
- **D6.** PASS on the name: the *M\'emoire d'Ing\'enieur* is not named anywhere in Ch6, so it is not misnamed. PASS on the acoustic-robustness experiment: it is absent, and the script checks this too. The one D6 point is the unattributed 3,122 ms (MINOR-3).

### Number trace rows judged in context ("measured:" hits only)

None is wrong in context:
- l.20 0.36 / 1.2: RQ1's own range (ch1:94). The script's hits in `wake_training.json` and the S1 spike are coincidental; ch5:18 uses the same range.
- l.31 2,500: the budget as specified (ch3:621, ch4:314).
- l.51 3,540: the pooled grammar-off decodes (ch4:246), the same figure as l.49.
- l.61 0.935: Qwen2.5-0.5B Q4\_K\_M golden on the deployed surface (`surface_b.csv`). It equals the fp16 reference figure, since the delta is 0 (ch4:219).
- l.65 200: the golden-split n (ch4:221). The script's `exp2_latency_budget.md` hit is coincidental.

## 5. UNVERIFIED

- "The two abstention requirements are the ones the selected configuration misses by the widest margin" (l.89-90) is a comparative that Ch4 does not state ("by a wide margin"). On ratios it holds for Qwen2.5-0.5B Q4\_K\_M:
  - pooled safe-failure 6/62 = 0.097 against $\geq$ 0.70;
  - false-command rate 0.2533 against $\leq$ 0.05, about 5x;
  - end-to-end latency 25% over;
  - uncached prefill 751 ms against the 250 ms allowance, 3x.

  The claim depends on counting the prefill allowance as a budget line rather than a requirement. Not reported.
- Step 1's mechanism ("token-level log-probabilities over the emitted command", l.91) assumes the deployed `llama.cpp` server exposes per-token log-probabilities under grammar constraint. This is plausible but was not checked against the runtime build. No claim needs a `\cite`, because nothing is attributed to the literature.

## 6. Examiner questions (D10b)

1. *"You re-baselined the end-to-end budget to your selected model's own p95. What did the latency constraint actually decide?"* Partly answered. l.34-36 say the selection holds when SmolLM2-360M is admitted and that the choice over Llama-3.2-1B rests on latency. Ch6 does not say that the re-baselined budget cannot test Qwen2.5-0.5B, which Ch4 says at l.362-363. Consider one clause at l.32: "... re-baselined to its own measured p95 of 3{,}122~ms, which Qwen2.5-0.5B satisfies by construction".
2. *"Is 0.935 what an operator speaking to the drones gets?"* Not answered in Ch6. After MAJOR-2 the chapter says what 0.935 is (reference transcripts). The rest is answered in Ch5 §5.3.2 (l.278-289), which is where Table 3 keeps it.
3. *"98.9% of in-domain errors dispatch a command and the parser almost never declines. Is the selected configuration deployable?"* Answered at the strength the data allow: l.37-42 ("it does not meet every requirement placed on the system"), with the remedies in §6.3 steps 1-2.

D10a: not applicable to a conclusion. Nothing in Ch6 is needed to rerun the work; step 1's calibration set is undefined, which is acceptable for a step not taken.
