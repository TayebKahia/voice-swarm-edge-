# Issue 13: ingenieur-ch5

Status: ready-for-agent
Blocked by: 11 (Ch3, resolved). Runs alongside 12 (Ch4) -- see "Order" below.
Chapter: thesis/ingenieur/ch5_validation.tex (402 lines, lead-in + 5 sections, 3 distinct cites:
dregon, mcnemar1947, dunn1961; 3 generated tables \input, 1 generated figure; drafted Thu 24 Sep in
1ed40d8 (lead-in, 5.1, 5.2), 29fa92d (5.3), 6da10fa (5.4, 5.5), then e4b34ec (acoustic run cooled,
author's confirmation), 81551fe (5.4 re-matched to Ch4 4.5/4.6), f5126cf (keyword curve in place);
STATE.md record: "Writing progress -- Ingenieur Ch 5 (B10)")
Script: tools/review/ingenieur_ch5.py
Report: .scratch/thesis-review/reports/ingenieur_ch5.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/ingenieur_ch5.py
```

At opening: 0 FAIL, 0 WARN, 252 PASS; 0 significant numbers untraced.

## Order

The spec's order would block this on 12. It is not blocked, by the author's decision (Thu 24 Sep, the
depot day): Ch4 is drafted and committed, and Ch5 refers to it only by label with one clause each. If
issue 12 renames anything Ch5 cites -- "kinematic backend", "separation clamp", "clamp distance",
"physics backend", or a section label -- re-run this script and re-check 5.4's Protocol, Collisions and
Scope paragraphs and 5.1's references to sec:runtime and sec:command-bus.

## Agents

Split like issues 11 and 12:

- **Argument / statistics agent** -- D1, D2, D4, D6, D10. Focus:
  - **Verdicts fixed before measurement, and their wording.** Reflex latency, end-to-end latency,
    preemption recovery, clean-audio recognition and recognition in noise are *missed* with a located
    cause; the two keyword criteria are *not demonstrated* under the declared interval rule; the
    end-to-end re-baseline is stated as a re-baseline, never a pass (STATE.md "Author decisions (Thu 24
    Sep)"). The script checks the words; the agent checks that no sentence around them softens them.
  - **Located cause vs interpretation.** Each miss names a cause. Is each cause what the measurement
    locates, or an interpretation that belongs to Ch6? Hardest cases: 5.1's recovery cause (the
    language-model server's once-per-second check for a closed connection -- no results/ file states it;
    it comes from the llama-server configuration, STATE.md "Exp-2 RESULT"), and 5.3's "Direction of the
    errors" paragraph.
  - **Statistics.** 5.3: the pre-registered arcsine ANOVA with its two stated weaknesses, the paired
    Cochran's Q + McNemar beside it, and "not significant" at p = 0.0051 against alpha = 0.0050. 5.4:
    ANOVA and Tukey on convergence time; formation accuracy saturated and reported as fixed. Are the
    tests named, with n and the interval, wherever "significant" is used (D4c)?
  - **Promises kept** (issue 06, agents/06-ingenieur-ch1/argument.md P1-P31, and Ch1 l.85-235): the
    reflex path idle AND loaded; every stage against tab:stage-budget (two rows have no verdict -- is the
    reason given enough?); clamp interventions beside the zero collisions; formation quality measured on
    its own; the curve's direction (safe-failure rate) separate from the rate; the per-trial record and
    the single-command rerun (the lead-in says the rerun holds per experiment only -- see seeded points);
    the safe-failure rate; the author's-voice WER cited from the Master in one sentence without its number.
  - **Promises Ch4 made to Ch5** (STATE.md, Ch4 entry "Handed on"): test split scored twice (5.2);
    prefill cost of the disabled prompt cache (5.1); server stop latency bounds recovery (5.1);
    interventions and collisions both reported (5.4).
  - **Ch6 inherits** every verdict through tab:requirements-summary: check that 5.5's one-sentence
    causes are the ones the sections give, with no new figure or argument.
- **Citation / presentation agent** -- D5 (3 keys: dregon for the noise, mcnemar1947, dunn1961 for
  Bonferroni), D7, D8, D9, D11, D12. The chapter \inputs three generated tables and includes one
  generated figure: check each is \ref'd before it floats and interpreted in the text, that
  tab:end-to-end's last column is called a stage sum where it is used, and that fig:keyword-curve's
  caption matches the drawn figure (results/figure_keyword_curve.png). Tukey's HSD, Cochran's Q and the
  exact (Clopper-Pearson) interval are named without a citation: references.bib has no entry for them --
  report it, do not add one (adding a bib entry is the author's job, SKILL §4).
- **Verifier**, given only the BLOCKER and MAJOR findings; re-computes from results/ where a finding
  rests on a number.

## What the script establishes

Every figure is recomputed from the results/ file the chapter drew it from, never from STATE.md:
- lead-in: SoC temperatures and throttle words per trial (exp2_raw/*.jsonl, 360 trials);
- 5.1: exp2.csv (every p50/p95), exp2_raw (preemption outcomes, the class matrix idle and loaded, the
  one golden-set trigger), meta.json (warm-up), exp2_analysis.md (core-0 frames), wake_real_voice.json
  (false rejects and exact intervals on the author's takes, the missed take's peak);
- 5.2: wake_training.json (test and val rates, cross-triggers, the flat top of the "roc" grid from 0.88,
  the ambient/near-miss/golden streams and their intervals) and wake_training.md (delays);
- 5.3: exp3_pi.csv, exp3_pi_analysis.md (the one-cause error table, envelope, F, Tukey, Cochran,
  McNemar), exp3_pi_parity.csv, soc.log (peak, first flagged sample); the Master's pooled safe-failure
  rate from nfr9_nfr18_abstention.csv; table16 for the "within a fraction of a point" sentence;
- 5.4: exp4.csv per trial (counts, clamp spread, closest approach, final slot error, convergence),
  ANOVA and Tukey redone with scipy, IQRs from exp4_formation.md;
- 5.5: verdict counts from requirements_summary.md, and each Missed row named as missed in 5.5.
Plus: the three tables are \input and none is retyped; the figure file exists; the fixed verdict words;
Ch4's parameters (0.35 m, 0.80 m, the pass limit) referenced, not restated; the Master's WER not quoted.

Rounding note: exp2.csv holds x.5 values (e2e p95 3,122.5 ms, abort return 6.5 ms). The \input table
prints them half-to-even (3,122); the prose follows the table. The script accepts +/-0.5 on those six
claims with a note -- a reviewer who finds "3,123" in the CSV should read that note before reporting.

Selftest: five planted errors are caught (a reflex p95 454 for 545 -> `claim`; preemption recovery
"met" -> `verdict`; the 0.35 m collision distance restated -> `ownership`; 423 clamp interventions ->
`claim`; the Master's 23.0% WER restated -> `ownership`). Two are wired into selftest.py.

## Seeded points (from the drafting session -- not findings unless the text is wrong)

- **Rerun (lead-in).** run_all.sh's exp2/exp3/exp4 stages call `eval/bench.py --experiment N`, which
  without --dry-run exits "nothing to do"; the real runners are eval/exp2.py, exp3.py, exp4.py. The
  chapter therefore says the single-command rerun "holds per experiment rather than for the chapter as a
  whole". A reproducibility finding for D10a, and a Block A fix -- not a prose fix.
- **Per-trial record (lead-in).** Ch1 says "one CSV row per benchmark trial"; the latency and acoustic
  records are JSON lines per trial (exp2_raw/, exp3_pi_preds/), CSV rows only for formation control.
  The chapter says so. Does Ch1's wording need a Ch1 finding?
- **Parse-path span (5.1).** eval/exp2.py stops the clock at the state machine having applied the
  command, later than Ch3's "handed to the bus"; 5.1 bounds the excess by the validation row (p95 under
  1 ms). Does that satisfy the open item from the Ch3 entry, and does Ch4 4.3 ("the instant at which both
  latency spans end") now contradict 5.1?
- **The golden-set reflex trigger (5.1).** One hover on item 0158 on the Pi; none in the workstation
  evaluation of the same recordings. Reported, cause not claimed.
- **Acoustic run cooled (lead-in, 5.3).** results/ records no cooler for it; the author confirmed it on
  24 Sep (STATE.md, commit e4b34ec). Acceptable as a source?
- **Located cause for preemption recovery** rests on configuration, not on a results/ file (see Agents).
- **No "was the target realistic?" paragraph** anywhere; left to Ch6.
- **Ch1 l.69 says "at 50 Hz"**; 5.4 says "the controller's 50 Hz tick" on the kinematic backend, which is
  true; PyFlyt runs at 48 Hz (Ch4 4.6) and carries no Ch5 result.
- **Float placement**: fig:keyword-curve floats to a page of its own (p. 47 of the build at f5126cf).
  Layout is B13's, not a review finding.

## Comments

### 2026-09-24 -- review, verified findings (awaiting the author's decisions)

**Resumed.** A session stopped after both review agents had written their reports and before the
verifier ran. The Comments were empty. This session picked the work up at step 4.

**Script.** Re-run on the chapter at f2f0384 (407 lines, unchanged since the agents ran; they cite
it as b13c611, same content): 0 FAIL, 0 WARN, 252 PASS, 0 untraced. No FAIL to triage and no
script change. The regenerated report differs from the committed one in one line only: the 5.5
verdict tally, now printed in requirements_summary.md's table order. The committed copy had been
generated before 346a231. Issue 12 (0cd26b1) renamed nothing that Ch5 cites.

**Agents.** Argument (D1, D2, D4, D6, D10): 28 findings, 1 BLOCKER, 11 MAJOR, 12 MINOR, 4 NIT.
Citation/presentation (D5, D7, D8, D9, D11, D12): 26 findings, 4 MAJOR, 12 MINOR, 10 NIT.

- Clean build: 0 errors, 0 undefined, 0 Overfull/Underfull.
- fig:keyword-curve matches its caption element by element.
- All three tables are \ref'd before they float and interpreted.
- tab:end-to-end's last column is called a stage sum.
- mcnemar1947 and dunn1961 SUPPORT their sentences. dregon is PARTIAL (P4 below).
- Verdict wording: every miss opens "The criterion is missed", the re-baseline is a re-baseline,
  and the collision claim keeps the locked form. No verdict is softened in words. The problems lie
  in the located causes and the statistics around them.

**Verifier.** 14 BLOCKER/MAJOR findings were sent (P3 merged into A3, P5 into A4).

- 11 CONFIRMED.
- A1 DOWNGRADED from BLOCKER to MINOR.
- A9 and A12 PARTIAL.
- 0 REFUTED.

No BLOCKER survives. The verifier did three kinds of check:
- It re-computed every number these findings rest on.
- It checked `HTTP_POLLING_SECONDS = 1` at the pinned llama.cpp tag b10863.
- It resolved the proposed DOIs on Crossref.

It corrected eight proposed fixes. Five of them would have put into the prose a figure that no
results/ table holds, so those now need a runner change first (marked **Block A** below). Full
reports: `.scratch/thesis-review/agents/13-ingenieur-ch5/` (argument.md, citation-presentation.md,
verifier.md).

| # | Sev | Line | Finding | Verifier | Proposed fix (verifier-corrected) |
|---|---|---|---|---|---|
| V1 (A2) | MAJOR | 88-93, 205-208, 392-394 | "The miss therefore lies in how long the spotter's score takes to cross the threshold after the keyword ends, a property of the classifier and its operating point, not of the board." The 540 ms is frame end minus the capture tool's energy-based offset, and that anchor is imprecise: some detections come *before* it (idle w06/w28/w29 on both passes, 6 of 78; loaded 4 of 78; earliest -234.7 ms). The synthetic and real delays use different anchors (last sample with \|x\| > 1e-4 vs the last 20 ms frame at >= 5% of peak RMS), so "the synthetic split therefore understates the delay on real speech" is not established. | CONFIRMED (recomputed from exp2_raw). "Not of the board" holds (6/18 ms). | l.88-93: "... That offset is the capture tool's energy-based end of speech, and on some takes the command was published before it, so the anchor itself is imprecise. The 540~ms therefore contains the spotter's decision delay, the quantisation into 80~ms frames and the anchor's error, which this measurement does not separate." Drop "a property of the classifier and its operating point" (Ch6 may argue it). The count and the 235 ms may be quoted only once eval/exp2.py emits them (**Block A**). l.205-208: name both anchors, drop "therefore understates". l.392-394: "18~ms at p95", not "under 20~ms". |
| V2 (A3+P3) | MAJOR | 116-119, 397-398 | "The server accepts a new request only after it has registered the closed connection, which it checks once per second. That check, not the cancellation, sets the recovery time". The claim is true of the deployed build (`server-context.cpp:39` at b10863), but it is uncited and not measured. "Sets" is too strong: p95 1,195 ms and max 1,505 ms exceed the 1 s period (10 of 78 above 1 s, recomputed). | CONFIRMED | "The remainder is the language-model server's. It registers a closed connection by polling once per second (\texttt{llama-server}'s HTTP polling interval~\cite{llamacpp}), and only then releases its single slot. The median recovery, 601~ms, is about half that period, as such a check would give; the p95 of 1{,}195~ms and the maximum of 1{,}505~ms exceed the period, which the check alone does not account for." A file-pinned bib entry like `llamacppchat` would be better than the whole repository (author's call). l.397-398: "Preemption recovery is missed in the time the language-model server takes to release its slot after the connection closes, not in the client's cancellation." |
| V3 (A4+P5) | MAJOR | 281-285 | "The comparison of 10~dB with 5~dB is not significant, at $p = 0.0051$ against $\alpha = 0.0050$, and neither is 20~dB against 10~dB, at $p = 0.0053$." The McNemar variant is not stated. Both boundary pairs are the Edwards continuity-corrected chi-square (b+c >= 25). The exact form gives 0.00460 and 0.00455, below alpha. The variant rule (bfe1b5e) predates the Pi run, so the verdicts stand. The paired family itself was added with the results (ecd4d03). The Master discloses the rule; Ch5 does not. | CONFIRMED (recomputed with scipy) | "McNemar's test~\cite{mcnemar1947} on each of the ten pairs, in the project's form (exact below 25 discordant pairs, with Edwards' continuity correction~\cite{edwards1948} from 25 upwards), at the Bonferroni-corrected level~\cite{dunn1961} ..." Scope "fixed before measurement" to the variant rule, not the paired analysis. The exact p may be quoted only once eval/exp3.py prints `p_exact` (**Block A**); until then, say both pairs are decided by the chi-square form at the boundary. Verdicts unchanged. edwards1948 is Crossref-verified (Psychometrika 13(3):185-187, doi:10.1007/BF02289261); the author adds the entry. |
| V4 (A5) | MAJOR | 233-286 | Every 5.3 interval and test treats the 200 golden utterances as independent. They form 12 template families of 10-22 items (data/test_golden.jsonl `template_family`), as the Master states for the same items (master/ch3_method.tex:664-668). The chapter names two weaknesses of the ANOVA but not this one, which also affects the paired tests and bears on V3's boundary pairs. | CONFIRMED | Reworded so it does not copy the Master's clause: "A third property affects both tests and every interval of this section: the 200 utterances are grouped into 12 command patterns, as the \emph{M\'emoire de Master} sets out, and utterances of one pattern are not independent, so the intervals are narrower and the $p$-values smaller than independent items would give." |
| V5 (A6) | MAJOR | 295-298 | "With recognition errors in the input, the rate measured here is below even that figure at every level." The 0.053 baseline pools six configurations over three splits, and test_ood holds 25 of its 28 safe failures. On the same 200 items as reference text, this experiment's own text condition (exp3_pi_preds/text.jsonl) has 13 failures and none safe. So audio does not make failures safer; the sentence implies the reverse. | CONFIRMED (recomputed) | Take "13 and none safe" from this experiment's text condition, not from the Master's CSV (write-once). First add `text` to the rows eval/exp3.py summarises (**Block A**). Then: "On the same 200 utterances as reference text, the reference-text condition of this experiment has 13 failures and no safe failure; the audio conditions have between one and four. Recognition errors therefore do not make the failures less safe than the parser's own; neither input comes near the bound." Keep the Master's re-baseline to 0.053 as a quoted target; drop "below even that figure". |
| V6 (A7) | MAJOR | 172-173 (also 145-152, 210-222) | "The two keyword criteria are read from this one curve ... and they are quoted together here." This contradicts l.201-203 ("judged on the author's voice") and Ch1's table (false rejects: latency experiment). Ch1:208-209 promises the two numbers "together wherever either appears", but 5.1 and 5.2 each give one without the other. | CONFIRMED | l.172-173: "The two keyword criteria describe one operating point, the threshold marked on this curve, as Table~\ref{tab:nonfunctional-requirements} requires. The false-accept criterion is read from the curve's ambient-speech stream. The false-reject criterion is judged at the same threshold on the author's recorded takes (Section~\ref{sec:latency-experiment}), because the curve's positives are synthetic." Add the false-accept figure (2.33/h [0.06, 12.98]) at l.149-150 and the real-voice false-reject figures (0.050, 0.000) at l.215. All are already in the chapter. |
| V7 (A8) | MAJOR | 26-28, 213-214, 402-404 | "they follow an interval rule declared before they were scored". Git records no rule before scoring. ff6df58 scored the ambient stream and states verdict and result together. "whole interval" first appears in 911b0e8, with the real-voice scores (ancestry, not the rewritten dates). Neither Ch1, prd §8 nor STATE.md "Author decisions" has the rule. The rule turns a point-estimate miss (2.33 > 1/h) into "not demonstrated". | CONFIRMED | If the author holds a dated pre-scoring record, cite it and the finding closes. Otherwise l.26-28: "... they are judged under an interval rule, stated where they are reported, because a point estimate from so few events decides nothing." l.213: "Under that rule ---". l.402-404: add "the false-accept rate, whose point estimate exceeds the budget, ..." / "the false-reject rates, whose point estimates lie within it, ...". Verdict unchanged (review rule). |
| V8 (A9) | MAJOR | 52-55 | "The single-command rerun ... therefore holds per experiment rather than for the chapter as a whole." run_all.sh's experiment stages fail outright: argparse errors for exp2/exp3, "nothing to do" for exp4, and tables.py is never called. "Each experiment is rerun by one command" is false for the keyword-spotter evaluation (train_wake.py, which retrains, plus wake_real.py). | PARTIAL: accurate as a gap, but the sentence does not claim a pass, so it is not "softening". | Preferred: fix run_all.sh (**Block A**), then the sentence can say the requirement holds. Otherwise: "The reproduction script's experiment stages do not invoke these runners, so the single-command rerun that Section~\ref{sec:engineering-requirements} requires is not provided. The latency, acoustic-robustness and formation-control experiments are each rerun by one runner, the first two on the board; the keyword-spotter evaluation by two, one of which retrains the heads; and one further command regenerates every table from the records." |
| V9 (A10) | MAJOR | 18-19, 140-143 | "every stage of both paths is judged against the budget of Table~\ref{tab:stage-budget}", but two rows get no verdict. The reason for the combined language-model row (the Master's cached prefix) does not justify it: the prefill row makes the same assumption and *is* judged. The real reason is that the generated table has no combined row (STATE.md). Ch3 promises "measures the system against each of them". Prefill+decode p95 = 1,657.7 ms against 1,350 (recomputed; keep it out of the prose). | CONFIRMED | Preferred: add the combined row to eval/exp2.py / tables.py (**Block A**) and judge it like the prefill row, noting that its allowance assumes the cached prefix. Otherwise state the true reason and that the deployed parser does not cache the prefix. Lead-in: "... set against the budget ..., and the two rows that receive no verdict are named with the reason". The start-of-speech reason is adequate. |
| V10 (A11) | MAJOR | 94-98 | "The core allocation of Section~\ref{sec:resource-allocation} kept the parse path's load off the reflex path." Under load the board's share rose from 5.5 to 18.0 ms at p95. Ch3's "Limits of core pinning" predicts exactly this residual. The load thread runs only the language-model stages (exp2.py Loader), with no speech recognition. | CONFIRMED. The reviewer's "74.2 ms while the recogniser ran" is not supported: that maximum is for the whole golden-set phase. | "Under the core allocation of Section~\ref{sec:resource-allocation} no frame exceeded its 80~ms period, but the load still reached the reflex path through the resources the cores share, as that section anticipates: it raised the board's share of the reflex latency from 6 to 18~ms at p95. The load in this condition was the language-model stages only; no keyword trial was run while speech recognition was running. In the golden-set phase, where it did run, no frame exceeded the period either, the longest taking 74.2~ms." |
| V11 (A12) | MAJOR (a, c); MINOR (d, e) | 44-55, 114-115, 316-320, 335-344 | Reproducibility gaps. (a) Formation sizes, circle radius 5 m and line/wedge spacing 2 m (swarm/simulate.py:58-59), are stated nowhere. l.360 "several metres across" and the convergence comparison depend on them. (c) "Can accept a new utterance" is operationalised as the server's `/slots` idle, polled every 5 ms, and not said. (d) The acoustic run's recogniser ran at -t 4, unpinned (bears on the stage-sum column only). (e) Seeds are fixed in the repository. | PARTIAL: (b), the llama.cpp commit, is REFUTED. Ch4 l.155 cites `llamacpp` (b10863). | (a) "the circle of radius 5~m, and the line and the wedge at 2~m spacing". Better stated in Ch4 as code parameters and referenced from Ch5 (issue 12's side; not touched here). (c) l.114-115: "... taken as the moment the language-model server reports its slot idle". (d) l.317-318: "... with the recogniser on four unpinned threads rather than the deployed three". (e) optional: "the seeds are fixed in the repository". |
| V12 (P1) | MAJOR | 275, 371 | "Tukey's pairwise comparison separates 5~dB from clean, 20 and 15~dB, and no other pair." An author-named method with no \cite (SKILL §4), next to cited McNemar and Dunn; references.bib has no entry. Anticipated by the issue. | CONFIRMED | The author adds an entry: Kramer 1956, *Biometrics* 12(3):307-310, doi:10.2307/3001469 (the Tukey-Kramer form scipy computes, identical at equal n), or Tukey 1953 via *Collected Works* vol. VIII. Not Tukey 1949. Cite at l.275 only. |
| V13 (P2) | MAJOR | 279-281 | "Cochran's $Q$ rejects equality across the five conditions (...)". Author-named, no \cite, no entry. | CONFIRMED | The author adds `cochran1950`: *Biometrika* 37(3-4):256-266, doi:10.1093/biomet/37.3-4.256 (Crossref-verified). |
| V14 (A1) | MINOR (down from BLOCKER) | 127-130 | "The selection rule of the \emph{M\'emoire de Master} has a failure clause for a constraint that no configuration satisfies". The reviewer read this as contradicting the Master. It does not: the Master defines "satisfies" as measured and within the bound (master/ch3_method.tex:650-651), so the unmeasured SmolLM2 does not satisfy it. Only the trigger (no configuration satisfies *both*) is paraphrased loosely. | DOWNGRADED | "The selection rule of the \emph{M\'emoire de Master} fails openly when no configuration is shown to satisfy both of its constraints, as happened there, and each unmet constraint is then re-baselined against the measured figure; under that clause the end-to-end budget is re-baselined to the measured 3{,}122~ms." Keep l.129-132 from "This is a re-baseline". |

**Block A changes the corrected fixes depend on.** None is in thesis/, and none was made:
- eval/exp2.py: emit the count and minimum of detections before the recorded offset (V1), and the
  number of recoveries above 1 s if wanted (V2).
- eval/exp3.py: print `p_exact` beside `p` (V3), and summarise the text condition's failed/safe
  counts (V5).
- eval/tables.py: the combined language-model row (V9).
- run_all.sh: stages that call exp2.py / exp3.py / exp4.py and tables.py (V8).
- results/exp3_pi_analysis.md:26 heads the paired section "exact McNemar", although 7 of 10 rows
  are chi2_cc. The eval/stats.py:109-111 comment ("every comparison ... falls below") is stale.
  Both come from the verifier and were not second-checked.

**Seeded points, judged.**
- Rerun: V8.
- Per-trial record: MINOR A15 (Ch5 should state the deviation). No Ch1 finding: the requirement
  predates measurement and is not reworded.
- Parse-path span: 5.1 settles the Ch3 open item. Ch4 4.3 describes the defined spans, so there
  is no contradiction. The bound's precision is NIT A26.
- Golden-set trigger 0158: reported correctly, and 5.2's "none" needs a qualifier (A14).
- Acoustic run cooled: acceptable as the author's protocol statement.
- Recovery cause: V2.
- No "was the target realistic?" paragraph: correct, left to Ch6.
- Ch1 "50 Hz": no Ch5 finding.
- Float placement: B13.

**Promises.**
- Kept: offline criteria reported as not run; the curve with its threshold; collisions in the
  locked form; clamp interventions beside zero collisions; curve direction apart from the rate;
  formation quality on its own; the author's-voice WER without its number; Ch4's "test split
  scored twice", "prefill cost" and "interventions and collisions".
- Partial: reflex path idle and loaded (V10); recovery (V2, A20); every stage (V9); per-trial
  record and rerun (A15, V8); "each with its statistical analysis" for the latency experiment (A24).
- Broken: the keyword pair quoted together (V6).
- Ch6 inherits 5.5's causes. 5.5 must be revised with 5.1 (V1, V2, V7, A25).

**MINOR / NIT, not verified (spec step 4), listed for decision.** Row numbers refer to the agent
reports (A = argument.md, P = citation-presentation.md):
- Argument:
  - Tukey and paired-test reporting: no family-wise level or p, and the post-plan test is not
    labelled as such (A13).
  - 5.2's "none in 0.304 h" vs 5.1's one trigger on the board (A14).
  - Per-trial record vs Ch1's "one CSV row" (A15).
  - The test split scored twice: consequence not drawn (A16).
  - "the only real speech available" (A17).
  - "did not change the recogniser's error rate" (A18).
  - Formation sizes confound "convergence time discriminates" (A19, tied to V11a).
  - Recovery measured only for triggers during a decode (A20).
  - "no measurable effect" of the throttle flag (A21).
  - Section order vs prd §3.1 item 5, a prd amendment (A22).
  - No section names its RQ (A23).
  - Latency analysis has no distribution or uncertainty, and 80 trials are 40 takes x 2 (A24).
- Argument NIT: "under 20 ms" in 5.5 (A25); the validation-row bound is 13.5 ms max, not 1 ms
  (A26); "so the figure measured here" does not follow (A27); "five misses" then a sixth (A28).
- Citations:
  - DREGON "evaluation partition" is the project's split, not DREGON's (P4).
  - Clopper-Pearson, Garwood and the bootstrap are unnamed and uncited (P6-P8); the author adds
    entries.
- Generated tables (fixes in eval/tables.py):
  - Latency caption: no units, no "what is tabulated", n = 78 unexplained, no takeaway (P9).
  - End-to-end caption: no subject or takeaway, and an ungrammatical sentence (P10).
  - Keyword false rejects printed to two decimals, so 0.001 becomes 0.00 (P11).
  - The queue and overhead intervals are "recorded beside the stages" but not tabulated (P12).
  - File paths and "Host: drone-pi" in table notes (P13).
  - Hand-typed CRR/EM/WER/SNR instead of \gls, and no `csv` acronym (P14).
- Naming and headings:
  - Criterion-name drift at l.163, 228, 291 (P15).
  - Headings "No tuning." / "Not measured." are not noun phrases (P16).
  - "sticky" flag and "from 17:45" (P17).
- NIT: 15 sentences over 40 words (P18); "show" (P19); conversational phrasing (P20); "upper
  points" in the figure caption (P21); \emph vs \texttt for the keyword phrases (P22); table
  typography (P23); "several metres" (P24); a tense switch (P25); rotor vs propeller-type noise, and
  ROC vs operating curve in Ch1 (P26).
- Verifier NEW (unverified): name the two offset-anchor definitions wherever the synthetic and
  real delays are compared (l.203-208).
- UNVERIFIED:
  - "Decoding is greedy" (l.51-52) for whisper.cpp at 52a939a; the CLI default may be beam search.
  - Why 10 recoveries exceed 1 s (not for the prose).
  - Whether the bibliography prints `version = {b10863}`.
  - The active-speech level definition (data/mix_noise.py, not ITU-T P.56).
  - The soft-temperature-limit flag's "sticky" firmware behaviour.
  - The 2.43 m/s formation speed from issue 12 #10 (Ch6 limitations, if accepted).

No file under thesis/ touched.

### 2026-09-24 -- author: V7 and the Block A route

- **V7: fix.** The author holds no dated record of the interval rule from before scoring, so
  "declared before they were scored" goes. The verdicts are unchanged.
- **Block A: the code route** for V1, V2, V3, V5 and V9, and **rewording** for V8. The rerun
  cannot be proven without a full run on the Pi, so run_all.sh is left as it is and the sentence
  says the single-command rerun is not provided.

Done in 41737eb (eval/ + results/, `--analyse-only`, no rerun on the Pi, every pre-existing row
byte-identical). The corrected fixes can now quote these figures from results/:

| For | Figure | Where |
|---|---|---|
| V1 | detections before the recorded offset: idle 6/78, earliest -234.7 ms (w06, w28, w29); loaded 4/78, earliest -234.0 ms | exp2_analysis.md, both cross-trigger sections |
| V2 | recoveries above 1,000 ms: 10/78 | exp2_analysis.md, Pre-emption |
| V3 | exact p beside the p of record for every chi2_cc pair: 10 vs 5 dB 0.0051 / 0.0046, 20 vs 10 dB 0.0053 / 0.0046 | exp3_pi_analysis.md, second McNemar table |
| V5 | reference text: 13 of 200 failed, 0 safe (rotate 11, move 1, formation 1) | exp3_pi_analysis.md, after "Where the failures come from" |
| V9 | prefill + decode: n 226, p50 1,112, p95 1,658, p99 1,775 ms against 1,350 (MISSES) | exp2.csv `llm`, exp2_analysis.md |

V9's row is in results/ only. Adding it to tab:latency-budget (eval/tables.py `_BUDGET_LINES`)
changes a thesis table, so it waits on the author's decision on V9. When Ch5 quotes any of these,
ingenieur_ch5.py needs a check for each. Checks after the change: ingenieur_ch5 0 FAIL / 252 PASS;
master_ch3 and master_ch5 reports changed only in trace line numbers (refreshed here); selftest
passes; pytest eval/ 218 passed.
