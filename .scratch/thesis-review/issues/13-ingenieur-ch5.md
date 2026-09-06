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
