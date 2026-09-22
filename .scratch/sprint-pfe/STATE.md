# STATE
Session: 04 (Fri 18 -> Sat 19 Sep) -- COMPRESSED. Depot moved to **Thu 24 Sep**.
Last updated: 2026-09-21T00:00:00+01:00

## THE CALENDAR, as of Sat 19 Sep
Build days left: Sat 19, Sun 20, Mon 21, Tue 22, Wed 23. Depot Thu 24 (buffer morning only).
Five days, thirteen roadmap sessions. The roadmap does NOT fit and is not being followed
session-by-session; see "Triage" below for what was cut and why.
**The binding constraint is writing, not experiments.** thesis/master and thesis/ingenieur
contain a .gitkeep each. Zero words. An experiment with no chapter scores zero; a chapter about
a smaller experiment scores most of the marks. Writing days are protected; experiments fit
around them.

## Triage (decided Sat 19, deviations from IMPLEMENTATION_ROADMAP Part 3)
Cut, each declared as a Limitation rather than silently dropped:
  - golden sessions s2 and s3        -> single recording session; no day-to-day variation claim
  - Exp-1 200 -> 60 timed runs, Q4_K_M configs only   -> wider CIs, n reported per 2.7
  - Exp-2 200 -> 60 trials/branch (BOTH conditions kept: NFR-1 is meaningless without both)
  - Exp-4 150 -> 60 trials       ** UN-CUT. Ran in full: 150 trials in under a minute. **
  - PyFlyt backend -> smoke only ** UN-CUT. Same controller, same gains, both backends. **
Not cut, because they ARE the contributions: grammar ablation (C1), quantisation delta (C3),
wake-branch membership rule (C4), annotation pass 2.

**The decision that unlocks the schedule: accuracy is hardware-independent, latency is not.**
Every EM / F1 / CRR / schema-validity number runs on the workstation (greedy decode under a
fixed grammar is deterministic). The Pi is used ONLY for p50/p95/p99, peak RSS, thermals and
throttle flags. This makes Tables 17 and 18 -- the Master's core -- reachable without the Pi.

## The five days -- who does what
This division is the plan of record. It existed only in conversation until Sat 19; if context
is lost, THIS is the schedule. Human items are the bottleneck and are listed first each day,
because the agent's work parallelises and the author's does not.

Sat 19  AUTHOR: launch Kaggle (blocked on it all day -- start first) | **write Ch 1-2 of BOTH
                theses**, which depend on no result and are the biggest outstanding debt
        AGENT : Table 9 cell coverage + runtime/bus.py -> Gate 4 | quantise + Gate 3 + Surface-B
                the moment the Kaggle artefacts land
Sun 20  AUTHOR: **annotation pass 2** (~20 min, hard-dated in the PRD, do not move) | Master Ch 3
        AGENT : grammar ablation (C1) | McNemar + Figure 2 | Tables 17/18/19
Mon 21  AUTHOR: Master Ch 4-6 | record the demo video (live mic, networking off camera,
                including the ABORTED recovery path)
        AGENT : runtime pipeline end to end | Exp-2 / Exp-3 analysis
Tue 22  AUTHOR: Ingenieur Ch 4-6 | Table 21 positioning against Lim et al.
        AGENT : regenerate every table and figure by script
Wed 23  AUTHOR: read-through against the write-once rule, cover pages, print, DVDs
        AGENT : run_all.sh from a clean clone -- if a number cannot be traced to a CSV it does
                not go in a thesis
Thu 24  DEPOT. Buffer morning only.

Overnights: Exp-1 on the Pi (Sat), Exp-2 (Sun), Exp-3 (Mon). Exp-4 is already done.

**Master went 5 -> 6 chapters (decided Sat 19 evening, after Ch 1-2 were drafted and reviewed.)**
Discussion and Conclusion were one chapter in the original PRD outline; splitting them lets
Discussion stay hedged (trade-off, failure modes, threats to validity) while Conclusion stays a
clean, unhedged answer to RQ1 -- the two registers were fighting each other in one chapter, and
ch1_introduction.tex's own closing section had already drifted into ending on logistics instead of
a verdict, which is the failure mode a dedicated Conclusion chapter exists to prevent. No new
writing day was added: the 6th chapter is absorbed into the existing Mon 21 slot. prd.md Table 2
and SS3.1 updated to match; thesis-writing SKILL.md's chapter blueprint updated to stop presenting
one generic 6-chapter template for both documents (it previously implied Master was 6 chapters
when the PRD said 5, and misassigned Ingenieur's TTFT metric to Master's Results chapter).

## Gates
Gate 1 schema        : GREEN (pytest schema/ -> 83 passed, tag schema-v1.1)
Gate 2 leakage       : GREEN (check_leakage.py --strict -> exit 0, Sep 14; family, surface-form,
                       eval-independence, wake-corpus and noise-partition isolation all clean)
Gate 3 parity        : **GREEN for the three deployed models, RED for h2o-danube3**
                       (Mon 22 Sep). Both halves now run: HF side dumps on Kaggle
                       (notebook cell), llama.cpp side is `eval/check_parity_gguf.py`
                       against a local llama-server. qwen2.5-0.5b, smollm2-360m and
                       llama-3.2-1b are 10/10 on text AND token IDs; h2o-danube3 is
                       10/10 on text and 0/10 on IDs. Durable record:
                       `results/gate3_parity.{json,md}`, regenerated by the checker
                       with `--report`. See the two sections near the end of this file.
Gate 4 fsm           : **GREEN** (Sun 20 Sep, A3). All 50 Table 9 cells (5 states x 10
                       intents) covered by `swarm/test_fsm.py`; `python -m pytest
                       swarm/test_fsm.py -q` -> 100 passed. Coverage is structural (the
                       parametrisation is generated from the cross product) and the
                       transcription of Table 9 is cross-checked against prd.md at run
                       time. See the Gate 4 RESULT section below for the output and the
                       three mutations used to show the proof can fail.
Gate 5 dataset frozen: GREEN (tag dataset-v1.0, Sep 18). 200/200 masters + 200 resampled;
                       annot_pass1.jsonl sealed 23:41 under SHA-256 f1a1fe6c, verified intact.
D1 Environment Gate  : GREEN
FR-1 grammar         : GREEN (5,191 labels, 0 rejected)

Test suite: 720 passed, 0 skipped, `python -m pytest -q` (Sun 20 Sep, after A3 added 70
tests to swarm/test_fsm.py). The 650 below is the figure before that.
Previously: 650 passed, 0 skipped, `python -m pytest -q` (was 614 passed, 3 skipped as of
the last STATE.md entry recording it; not investigated further here whether the +36 is
exactly this session's new runtime/ tests plus 3 previously-skipped now passing, or
includes other sessions' concurrent commits -- see below for this session's own additions).

## What Session 03 delivered
data/record_session.py   : capture tool. 48 kHz S16_LE mono, device found by NAME, per-take
                           clip/silence/level/margin verification against a room floor measured
                           at session start, resumable, asks for room + mic distance up front.
data/resample.py         : offline 3:1 soxr VHQ + ONE session gain to a -14 dBFS ceiling.
                           Masters are never written to. Same soxr call as mix_noise.load_mono.
data/wake_corpus.py      : Branch A corpus. DONE -- 3,000 positives + 5,040 negatives (3.50 h).
data/commonvoice.py      : Exp-0 corpus. DONE -- 300 clips, 263 speakers, 15 accent buckets.
data/annotate.py         : test-retest. Subset stratified 5-per-intent; SHA-256 seal; pass 2
                           refuses to open before the seal and is shuffled.
data/check_leakage.py    : Gate 2 gained a fourth axis -- wake corpus isolation.
data/fetch_assets.py     : --wake and --commonvoice; four new corpora in asset_manifest.json.
data/dataset_card.md     : SS1/SS3/SS5 TBDs filled; SS7 rewritten with generated markers;
                           SS9 (wake) and SS10 (Exp-0) added.
docs/adr/0005            : 7 decisions.
prd.md + docs/project/PRD.tex : annotation interval 10 -> **2** days AND the agreement rate
                           withheld entirely (SS9.3, Limitations, R-9, Table 25). An earlier
                           line here said '10 -> 6 days'; that was the superseded first pass.

Corpora on disk (gitignored, all reproducible):
  data/wake/pos_swarm_hold/  1,500 clips   data/wake/pos_swarm_abort/ 1,500 clips
  data/wake/neg/             5,040 clips = 3.50 h  (train 3,930 / val 348 / test 762)
  data/commonvoice/clips/      300 clips   manifest + summary ARE tracked (WER references)
  data/wake/_src/  441 MB   data/commonvoice/_src/  684 MB   (SHA-256 in asset_manifest.json)

## Decisions this session (ADR-0005)
1. **48 kHz masters and the 16 kHz corpus are different directories.** `audio/s1/` is never
   written to after capture; `audio/s1_16k/` is derived and rebuilt. One soxr call in the
   project -- resample.py and mix_noise.load_mono are asserted identical.
2. **One normalisation gain per session**, not per file: per-file would erase the level
   variation the golden set carries. No nominal SNR moves (mix_noise levels on active speech).
3. **Wake corpus splits by base rendition** (70/10/20), negatives by speaker, near-misses by
   phrase -- otherwise Exp-2's ROC describes memorisation.
4. **Held-out wake clips hear different rooms and different noise** (RIR 70/30, aug|eval).
   Found while writing the test: DREGON keys cannot show this because it is one flight split by
   position, so each clip now records `noise_partition` from the bank it drew from.
5. **Keyword at a random offset, never centred**; 40 authored near-misses because no public
   corpus contains "swarm" or a phrase starting with "hold".
6. **The annotation claim was rescoped, not just renumbered.** The interval collapsed to 2 days
   (recording slipped to Sep 17-18; depot was Mon 21 Sep, since moved to Thu 24 -- the interval
   is NOT reopened, because pass 1 is already sealed and pass 2 is dated in the PRD),
   and at 2 days an agreement percentage
   measures recall rather than schema clarity. So **no agreement rate is reported at all.** What
   is reported is the list of items the two passes label DIFFERENTLY: recall can push the passes
   together but never apart, so a disagreement is evidence of ambiguity at any interval. The count
   is declared a lower bound, and a zero count is declared not to be a positive result.
   `annotate.py:card_block` renders no rate -- the rates stay in stdout as working numbers.
7. **Common Voice comes from an ungated mirror of release 17.0, recorded as a mirror**, and the
   sample is stratified by accent because a uniform draw is 39% US English.

## Blocked / needs human
1. **Annotation pass 2 -- Sun 20 Sep.** `python data/annotate.py --pass 2`, then
   `python data/annotate.py --compare`. ~20 min. Do NOT open annot_pass1.jsonl first.
   Reports the DISAGREEMENTS only; no agreement rate (see Decisions 6).
2. RESOLVED Sat 19: **autorisation de soutenance requested AND approved.** R-15 closed.
3. RESOLVED Sat 19: llama.cpp built on the workstation at the spike commit 88ada91c
   (build 10863, the same one S1/S3 used, so Gate 3 compares like with like).
   ~/llama.cpp/build/bin: llama-cli, llama-quantize, llama-bench, test-gbnf-validator.
   NOTE the target is `test-gbnf-validator`, not `llama-gbnf-validator`, at this commit.
   cmake lives in the conda env, NOT on the base PATH -- a background build without
   `export PATH=$CONDA_PREFIX/bin:$PATH` fails with "cmake: command not found".
4. **No active cooler is fitted on the Pi** (confirmed with the author Sun 20 -- not yet
   purchased). Spike S1 flagged mounting one as mandatory before Exp-1; it still wasn't
   done, and tonight's Exp-1 ran, and measured, 100% throttled (see RESULT below).
   Recommendation: buy it before Sun-night's Exp-2 run if at all possible -- Exp-2's
   Branch A budget (NFR-1, p95 <=150 ms) is far tighter than Exp-1's decode budget and
   would be hurt more by the same throttling. A cooled Exp-1 re-run is optional, not
   required (tonight's uncooled numbers are being kept, not discarded) -- see the
   projection in the RESULT section for which configs a cooler would most likely help.

## Session 04 delivered (night of Fri 18 -> Sat 19)
eval/norm.py     : the fixed SS2.7 normalisation. Imports data/numwords.py (ADR-0004 D6).
                   Expansion runs BEFORE punctuation stripping or "17.3" becomes "17 3"; a
                   leading minus is protected or "minus two point five" and "two point five"
                   both normalise to 2.5 and a sign error on an altitude reads as correct.
eval/stats.py    : nearest-rank percentiles (numpy's default interpolates and would report a
                   p95 no trial achieved) and a bootstrap that resamples UTTERANCES, not rates.
eval/exp0.py     : Table 16, POPULATED -> results/exp0.csv + table16_*.md.
eval/bench.py    : the shared harness. --dry-run green on experiments 0-4 (Session 04 gate).
train/           : three Table 14 configs, make_kaggle_bundle.py, kaggle_finetune.ipynb.
data/asr.py      : sidecars removed before AND after each batch -- a stale .txt from an earlier
                   run was being returned as a fresh transcript when whisper declined a file.
pytest.ini       : eval/ added to testpaths; it had been silently uncollected.

## Exp-0 RESULT (Table 16)
Author WER 23.1% [20.3, 25.9] on 200 golden utterances, unprompted.
Lower than 7 of the 15 accent buckets -- 53rd percentile. Corpus 22.4%.
Range: New Zealand 6.2% -> Hong Kong 49.5%. No pass/fail claimed; NFR-11 asks for a position.
**A confound was found and measured rather than argued about.** Exp-0 had been transcribed with
data/asr.py's DOMAIN_PROMPT, which names the command vocabulary. Those words are present in the
author's commands and absent from Common Voice sentences, so the prompt could only inflate the
native speakers' WER while leaving the author's alone -- flattering exactly the comparison the
table exists to make honestly. Both conditions are now run: +0.5 pp on Common Voice, -0.1 pp on
the author's. Real, small, reported. Table 16 positions the author on the MATCHED (unprompted)
pass. One confound remains and cannot be removed: the author read drone commands, the Common
Voice speakers read general English. Stated in the table. Upgrade path: the author reads ~20
Common Voice sentences (about 10 minutes) and the comparison becomes matched.

## Exp-4 RESULT (done, night of Fri 18 -> Sat 19)
Full pre-registered protocol: 50 trials x circle/line/wedge, 60 s, 50 Hz, seed = index x 42.
  FA 1.000 +/- 0.000 on all 150 trials; 150/150 meet NFR-13. **NFR-13 PASS.**
  **Collisions: 0 observed. NFR-12 PASS.** Closest approach 0.800 m vs a 0.8 m clamp.
  The clamp resolved 432 pair violations -- reported beside the zero, because that is the
  number of times APF alone was not enough, and it is what makes "zero observed, backed by
  a clamp" an honest sentence rather than "guaranteed by APF", which is unprovable.
  Convergence 100%; median 4.06 s circle / 3.26 s line / 2.30 s wedge.
  One-way ANOVA on convergence time: F(2,147) = 3500.7, p = 1e-124; all three Tukey pairs
  separated. ANOVA on FA: NOT APPLICABLE and said so in words -- zero variance, nothing to
  partition. **FA is saturated**: Table 15's N(0, 0.5 m) spawn is small against a multi-metre
  formation and 60 s leaves ~55 s of settled flight. Reported as pre-registered rather than
  made harder afterwards to manufacture variance. Convergence time is the discriminating metric.
PyFlyt: FA 1.00 on all three shapes, mean slot error 0.135 m, stable over 20 s.

## Surface-B RESULT (Tables 17/18, Sat 19 Sep 16:18)

Six artefacts x three splits, 590 items each, llama.cpp b10863 (88ada91c), GBNF grammar
on, one slot, greedy, workstation. Raw: `results/surface_b.csv`; per-item predictions in
`results/surface_b_preds/` (Session 07's McNemar test needs those, not the summary).
Tables rendered by `python eval/tables.py` -> `results/table17_model_comparison.md`,
`results/table18_quantisation_delta.md`, `results/nfr18_false_command.md`.

Exact match, Surface B (quantised + grammar):

| model | quant | test_synth | test_golden | test_ood |
| :--- | :--- | ---: | ---: | ---: |
| llama-3.2-1b | Q4_K_M | 0.9583 | 0.9100 | 0.8133 |
| llama-3.2-1b | Q8_0   | 0.9625 | 0.9150 | 0.8000 |
| qwen2.5-0.5b | Q4_K_M | 0.9542 | 0.9350 | 0.7467 |
| qwen2.5-0.5b | Q8_0   | 0.9583 | 0.9300 | 0.7333 |
| smollm2-360m | Q4_K_M | 0.8125 | 0.7600 | 0.6600 |
| smollm2-360m | Q8_0   | 0.8125 | 0.7900 | 0.6067 |

Schema validity is 1.0000 in all eighteen rows.

Three things the chapters must carry:

1. **Quantisation is nearly free.** test_golden delta vs FP16 runs -1.5 to +1.5 pp, with no
   consistent Q8_0 > Q4_K_M ordering (smollm2 is +1.5 at Q8_0 and -1.5 at Q4_K_M). At
   n=200 that is noise, not precision. Q4_K_M is therefore defensible as the deployed
   artefact on accuracy grounds alone, before the memory argument.

2. **NFR-18 is MISSED by every configuration.** False-command rate on test_ood is 0.187 to
   0.393 against a <=0.05 budget. The grammar guarantees structure, not abstention: an
   out-of-domain utterance still decodes to a well-formed command. Report as measured.
   Do NOT reconcile. This is a genuine limitation and the honest discussion is that
   abstention needs a mechanism the grammar cannot provide (a confidence gate or an
   `unknown`-biased decoding rule), which is future work.

3. **On test_ood, Surface B beats its own FP16 parent** (llama 0.7333 -> 0.8133). That is
   the GBNF constraint, not the quantisation -- contribution C1 appearing inside the C3
   measurement. Say so explicitly or a reader will read it as quantisation improving
   weights, which would be absurd.

Still to run on this harness: `python eval/surface_b.py --no-grammar` -> Table 19, C1
measured directly rather than inferred.

## Table 19 -- GRAMMAR ABLATION RESULT (Sat 19 Sep)

`python eval/surface_b.py --no-grammar`, then `python eval/tables.py`.
Raw: `results/surface_b_nogrammar.csv`, preds in `results/surface_b_preds/*_nogrammar_*`.

| Condition | Items | Schema validity | Malformed | EM (pooled) |
| :--- | ---: | ---: | ---: | ---: |
| Grammar on | 3540 | 1.0000 | 0 | 0.8508 |
| Grammar off | 3540 | 0.9997 | 1 | 0.8492 |

**The effect is one item in 3540.** Do not oversell C1. Three epochs of supervised
fine-tuning on nothing but canonical JSON taught the format so thoroughly that the
unconstrained model almost never leaves it. Writing the ablation up as "the grammar
rescues broken output" would be contradicted by our own table.

The defensible C1 claim is narrower and stronger:

  Fine-tuning makes valid output *overwhelmingly likely*; the grammar makes it
  *certain*. On a flight-control path the difference between 0.9997 and 1.0000 is
  not a rounding error -- it is whether a malformed command can reach the vehicle
  at all. The guarantee is structural and holds under distribution shift; the
  tendency is statistical and was learned on a distribution the aircraft will leave.

The single failure is the whole argument in one line. llama-3.2-1b Q4_K_M, test_ood:

  transcript   : "what does lidar stand for"
  gold         : {"intent":"unknown"}
  grammar OFF  : "Lidar" stands for Light Detection and Ranging.
  grammar ON   : {"intent":"unknown"}

Unconstrained, the model stopped being a command parser and became a chatbot -- and it
did so on out-of-domain input, exactly where the training distribution ends. The grammar
did not tidy up malformed JSON; it made that failure mode unreachable. Use this example
verbatim in Master Ch4; it is worth more than the aggregate row.

Caveat to state honestly: the ablation cannot separate "the grammar constrains" from
"the fine-tune already complies", because both surfaces use the fine-tuned weights. A
base-model ablation would separate them, and is not being run (no time, and the zero-shot
Surface-A baseline of 0.0000 EM already shows base models do not produce the format).

Decode p95 for Table 19's last column comes from Exp-1 on the Pi, not from the
workstation.

## Writing progress -- Master Ch 2 (Sun 20 Sep, Block B session)
thesis/master/ch2_related_work.tex is now fully drafted, all five sections, no NOTE markers left:
  2.1 Edge LLM inference / SBC benchmarking -- positions this work against \cite{sbc2025} as
      narrower (one task, one device) and deeper (task accuracy measured, not throughput alone).
  2.2 Quantisation (\label{sec:quantisation}) -- Q8_0/Q4_K_M mechanics via \cite{llamacpp}; the
      gap named is "accuracy cost reported as generic perplexity, not task accuracy" -- C3 closes it.
  2.3 Constrained decoding (\label{sec:constrained-decoding}) -- the GBNF argument: structural
      validity moves from a measured rate to a decoder property. Deliberately does NOT preview
      the Table 19 number (0.9997 vs 1.0000, the one-item delta) -- that stays in Ch 4's register
      per rule 10; Ch 2 only sets up the conceptual distinction Table 19 will demonstrate.
      Closes with the write-once exclusivity note for the Ingenieur (Table 3).
  2.4 SLU for robotics (\label{sec:slu-robotics}) -- \cite{massive} for the solved task shape;
      the gap is the resource envelope (offline, sub-1B, Pi-5 budget, no human in the loop), not
      the task shape itself.
  2.5 Positioning (\label{sec:positioning}) -- Synthesis / Gap / Delta shape per the skill;
      Delta ties directly to C1/C2/C3. No voice-UAV literature discussed (Table 3 reserves that
      for Ingenieur Ch 2).

No numbers are hand-typed anywhere in this chapter -- it is entirely conceptual/positioning prose,
so there was nothing to trace to a CSV and no \TODO{} was needed.
`python tools/check_tex.py thesis/master/ch2_related_work.tex` run: 5 problems reported, all
expected cross-file false positives (refs to chap:method / chap:results, not yet written; cites
to llamacpp/massive/sbc2025, bibliography is the sibling file) -- conclusive only once main.tex
exists. No in-file dangling refs, no table/ASCII issues.

Stopped here: Master Ch 2 done in full. Not started: Master Ch 3 (Sun 20 AUTHOR slot per the
five-day plan above), Ingenieur Ch 2 (B7, also owed a State-of-the-Art draft but for the DISTINCT
voice-UAV literature -- do not reuse any of the above prose there, per write-once).

## Writing progress -- Master Ch 3 (Sun 20 Sep, Block B session, B2)
thesis/master/ch3_method.tex is now fully drafted, all five sections, no NOTE markers left:
  3.1 Command schema and grammar design (\label{sec:schema}) -- the ten intents, the JSON wire
      format with the 40->18 token latency argument, the full cmd.gbnf grammar, and the num rule's
      digit-count-vs-range distinction (sets up sec:definitions-of-record's one-decimal rounding).
      Validator/FSM layers handed to the Mémoire d'Ingénieur in one paragraph, per Table 3.
  3.2 Label-first dataset construction (\label{sec:dataset}) -- Table~\ref{tab:dataset} (all 8
      Table 13 rows). test_golden corrected to 200 files/200 transcripts (NOT the prd.md 9.2
      three-session 320-file design) to match the actual Sat 19 triage cut (sessions s2/s3 dropped);
      the cut and its consequence are handed to the Ingénieur's Ch6 Limitations, not re-argued here.
      Annotation pass 2's disagreement count is \TODO{} -- not yet in STATE.md as of this session.
      Wake corpus (wake_pos/wake_neg) and commonvoice construction included here per Table 3
      ("dataset construction" ownership is Master's in full; Ingénieur Ch4 gets one naming paragraph).
  3.3 The LoRA recipe (\label{sec:lora}) -- Table~\ref{tab:lora}, full Table 14 recipe. **The
      fp16-for-bf16 deviation is declared here, once, and explicitly says it is not repeated in
      Ch4**: Table 14 specifies bf16, Kaggle's T4 is sm_7.5 (Turing, no hardware bf16 -- that needs
      Ampere sm_8.0+), so all three models trained in fp16 identically, which is why the RQ1 ranking
      is not confounded by precision. Verified against train/make_kaggle_notebook.py's own header
      comment and the fp16=True training call before writing this -- not asserted from memory.
  3.4 Quantisation procedure (\label{sec:quantisation-procedure}) -- merge/GGUF conversion on
      Kaggle (needs torch+peft, kept off the workstation by the environment gate), llama-quantize
      locally (pure C++). Surface A (fp16, reference) vs Surface B (quantised, what ships) kept
      strictly apart. Chat-template parity gate (test_template_parity.py) described as a mandatory
      per-conversion gate; deliberately does NOT assert Gate 3's current pass/fail status, since
      STATE.md still shows it PENDING as of Sep 19 even though Surface-B results already exist --
      contradiction not resolved here, left to whoever next touches Gate 3.
  3.5 Evaluation protocol and the definitions of record (\label{sec:definitions-of-record},
      prd.md S6) -- greedy/deterministic decoding, accuracy-on-workstation vs latency-on-Pi split,
      n_accuracy vs n_latency distinction, the canon() comparator, the EM-minus-CRR-is-a-result
      argument, and Table~\ref{tab:metrics} (full Table 10). Noted explicitly which rows this
      document's own Ch4 draws on (EM, F1 x2, schema validity, safe-failure, false-command,
      throughput) vs which the Ingénieur reports (latency, FA, convergence) -- this section has no
      Table 3 ownership row of its own, but the task and prd.md S6 both point here, so it is treated
      as the one place both documents' metric definitions are derived, with the Ingénieur expected
      to cite rather than re-derive.

No fabricated bibitems: all cites (qwen25, smollm2, llama32, lora, llamacpp, piper, oww,
commonvoice, esc50, dregon) verified present in thesis/bibliography.tex before use. No
"Table 3"/"write-once" project-process language leaked into the prose (caught and fixed twice
during drafting -- once in the dataset table caption, once in the golden-set paragraph). One
speculative claim (that fp16 training showed no divergence/needed no loss-scaling) was drafted,
found unverifiable against train/ and STATE.md, and removed rather than kept as a plausible-sounding
detail.

`python tools/check_tex.py thesis/master/ch3_method.tex`: 0 in-file problems on every pass; the
final pass reports 14 problems, all confirmed cross-file (ch2's sec:constrained-decoding, ch4's
chap:results -- not yet written, bibliography.tex's 10 cited keys).

Stopped here: Master Ch 3 done in full, one \TODO{} outstanding (annotation pass 2 disagreement
count -- run `python data/annotate.py --pass 2` then `--compare` when ready, then fill the TODO).
Not started: Master Ch 4 (Mon 21 AUTHOR slot per the five-day plan), Ingenieur Ch 2 (B7, still
owed, distinct voice-UAV literature only).

## runtime/bus.py and the pipeline wiring (Sun 20 Sep, Block A session, A2)

Task: build runtime/bus.py and wire wake -> ASR -> LLM -> validator -> FSM so Exp-2 and
Exp-3 can run. `runtime/` held only `__init__.py` before this session.

Five new modules, each wiring an existing or newly-built stage rather than reimplementing
one -- schema/validate.py and swarm/fsm.py are untouched:

  runtime/bus.py      : Table 4's Command Bus. Real UDP/JSON, one CommandBus instance per
                        process holds ONE monotonic sequence counter shared by both branches
                        (`publish`), plus `next_seq()` to *reserve* a slot ahead of a slow
                        Branch B decode -- see the correctness note below, this is the one
                        design point that took a wrong first pass to get right.
  runtime/branch_a.py : Table 5 / contribution C4's membership rule, encoded as
                        KEYWORD_TO_INTENT = {"swarm_hold": "hover", "swarm_abort": "abort"}
                        and asserted at import time to be exactly these two -- no third
                        intent can be added without editing and re-justifying this file.
                        No trained openWakeWord model exists yet (data/wake_corpus.py built
                        the 3,000+5,040-clip corpus, not the classifier) -- BranchA depends
                        on a WakeDetector Protocol instead, tested against a fake. Training
                        that model is separate work, NOT done this session (rule 10).
  runtime/stt.py      : one function, transcribe_utterance(), wrapping data/asr.py's
                        existing single-file transcribe() -- no whisper.cpp invocation is
                        re-derived here, per that module's own docstring on why not to.
  runtime/parser.py   : CommandParser + LlamaServerProcess. Same request shape as
                        eval/surface_b.py (Gate-3-proven): /apply-template -> /tokenize
                        (add_special=false) -> /completion under schema/cmd.gbnf, against a
                        persistent llama-server per PRD Sec. 4's "schema out of the prompt,
                        static prefix KV-cached" decision. abort() closes the in-flight
                        request's socket from another thread (Sec. 4.3's "optimisation,
                        desirable" half) -- Spike S7's in-process-callback-with-
                        signalable-worker-process architecture, applied to the server
                        process llama-server already is.
  runtime/pipeline.py : Dispatcher (owns Sec. 4.3's correctness rule + the FSM) and
                        PipelineRuntime (the two publish paths). Table 4 assigns the
                        bus-staleness discard to "the state machine", not the bus, so it
                        lives in Dispatcher rather than inside swarm/fsm.py or runtime/bus.py.

**The one real bug this session found, in itself, before it shipped.** First pass assigned
a Branch B message's sequence number in `publish()`, i.e. at *decode completion*. That is
wrong: Sec. 4.3 needs a slow, in-flight decode that finishes *after* a later Branch A
trigger to still compare as *older*, and a sequence number assigned at completion time
would instead make it compare as *newer*, silently defeating the rule it exists to
implement -- a stale move could have overwritten an abort. Fixed by adding
`CommandBus.next_seq()`, reserved by `PipelineRuntime.on_utterance` before transcription
even starts, carried through to `publish(..., seq=reserved)` regardless of how long the
decode takes. `runtime/test_pipeline.py::test_stale_branch_b_message_is_discarded_after_a_later_branch_a_trigger`
is the regression test -- it fails without the fix (verified) and is the closest thing
this repo has to a proof of Sec. 4.3's mandatory correctness clause.

A second, smaller bug: `Dispatcher.drain()`'s zero-timeout read for a queued burst raised
`BlockingIOError` (Errno 11) instead of returning None on a tight race against the kernel's
UDP receive queue -- caught in `CommandBus.recv()` now, and `drain()` uses a 50 ms grace
period after the first message instead of a hard 0.0.

Every module above is exercised against the REAL binding it wraps, not only against fakes:
`runtime/test_parser.py::test_real_llama_server_produces_a_grammar_valid_command` runs the
real `llama-server` against `gguf/smollm2-360m-instruct-Q4_K_M.gguf`;
`runtime/test_stt.py::test_transcribe_utterance_runs_the_real_binary` runs the real
`whisper-cli` against `data/audio/s1_16k/0001.wav`; `runtime/test_end_to_end.py` chains
both of those plus schema/validate.py, the real UDP bus, and swarm/fsm.py in one pass,
Branch A only (no trained model). All three are marked `slow` (subprocess/model-load cost)
and skip cleanly, not fail, on a checkout without the binaries/GGUFs -- they ran and passed
here. `abort()`'s causal effect (a 2 s fake decode cut to well under 1.5 s) is tested
separately against a fake HTTP server so that assertion does not depend on how fast a real
model happens to decode on this machine.

```
$ python -m pytest runtime/ -v
...
======================= 33 tests: 30 passed + 3 slow marker-deselected on the -m "not slow" run =====
$ python -m pytest runtime/ -v -m slow
runtime/test_end_to_end.py::test_golden_clip_reaches_the_fsm_through_the_real_chain PASSED
runtime/test_parser.py::test_real_llama_server_produces_a_grammar_valid_command PASSED
runtime/test_stt.py::test_transcribe_utterance_runs_the_real_binary PASSED
======================= 3 passed, 30 deselected in 3.37s =======================
$ python -m pytest -q          # whole repo, both env vars unset, pfe_swarm active
650 passed in 59.21s
```

`pytest.ini` testpaths gained `runtime` (was missing it entirely -- the directory had no
tests to collect before this session).

**Named, not started (rule 10 -- one task):** `runtime/audio.py` (capture) and
`runtime/vad.py` (endpointing) are Table 4 rows this task's own scope did not include --
the task was named as wake -> ASR -> LLM -> validator -> FSM, which is exactly what got
built; Branch B's entry point is therefore an already-segmented utterance (a WAV path), not
a live audio stream. Training the Branch A keyword-spotter model (openWakeWord, on the
already-built corpus) is also not done. Table 9 cell-coverage proof for Gate 4 (A3) was not
touched, though `swarm/fsm.py` was read closely while wiring `Dispatcher` and looked
consistent with Table 9 on inspection -- that is not the coverage proof A3 asks for.

Stopped here: runtime/bus.py and the wake->ASR->LLM->validator->FSM wiring are done and
tested against real llama.cpp/whisper.cpp bindings on this workstation. Exp-2 and Exp-3 are
unblocked on the runtime side; Exp-1's Pi triage is a separate, hardware-side blocker this
session did not touch. Next: either A3 (Table 9 coverage, closes Gate 4) or A6/A7 (Exp-2 /
Exp-3 themselves, both now runnable against this pipeline) -- and, out of session scope
entirely, training the Branch A keyword-spotter model, without which Branch A's real
detector never runs, only its wiring.

## Writing progress -- Ingenieur Ch 1 (Sun 20 Sep, Block B session)
thesis/ingenieur/ch1_introduction.tex is now fully drafted, all six sections, no NOTE markers left:
  1.1 Operational context -- one operator, five aircraft, outdoor site, no infrastructure. Offline
      argued as THREE independently sufficient reasons (availability / an uncontrolled latency tail
      inside a p95 budget / a stop channel that must survive what else fails), because one reason
      reads as a preference. States the simulation boundary at the outset -- aircraft simulated,
      audio path not -- rather than leaving it for Ch 6 to concede. Master's edge-inference
      exposition NOT repeated: one fresh sentence handing model selection to the Master (Table 3).
  1.2 Engineering requirements (\label{sec:engineering-requirements}) -- Tables 1.1/1.2 carry 17 of
      the project's 33 requirement rows. **Selection rule is traceability, not judgement: this
      document answers RQ2+RQ3, so it carries the union of those two rows of prd.md Table 31**, and
      says so in the prose. NFR-11 is the one Table 31 row deliberately dropped (listed under RQ3
      there, but its exposition is Exp-0 in the Master's Ch 4) -- cross-referenced, not tabulated.
      The argued point is the NFR-1/NFR-2 ratio (150 ms vs 2,500 ms) forcing the dual path.
      A first draft justified that with "the transcription stage alone exceeds 150 ms" -- plausible,
      but NOT measured anywhere in this repo, so it was cut per rule 6 and replaced with the
      anchor-point argument (NFR-1 runs from keyword offset, NFR-2 from end-of-speech; the reflex
      must answer mid-utterance), which needs no measurement and is the stronger claim.
      NFR-15/16 given a paragraph committing this document to always quoting them as one operating
      point on one ROC.
  1.3 The safety problem (\label{sec:safety-problem}) -- the chapter's argumentative centre, built
      as one chain: errors are asymmetric -> accuracy is silent about direction -> three layers,
      one exit (every rejection resolves to a hold) -> layers cannot fix a LATE stop -> so the stop
      gets its own path -> which is only safe under a closed membership rule (C4, cost-of-a-false-
      accept argument: a path skipping validation may carry only commands that remove energy from
      the system) -> and correct commands still need a bound at the integrator.
      **NFR-12 phrasing fixed here at first mention and used 3x in the chapter** (Table 1.2 target
      cell + twice in 1.3). "guaranteed" appears twice, both inside an explicit denial of the
      stronger claim. 1.3 also argues why the weaker sentence is MORE informative (it names the
      mechanism the result rests on), so Ch 5 inherits a claim it does not have to apologise for.
      Forward-promises the STRUCTURE of the Exp-4 report -- collision count reported beside
      clamp-intervention count -- without quoting either figure.
  1.4 Objectives (\label{sec:objectives}) -- RQ2 and RQ3 verbatim from prd.md:114-115 in quote
      blocks; VAD/STT/SLM defined in the lead-in so the quotes stay unedited. Commentary picks out
      the clause a reader skips in each: RQ2's per-stage distribution (why NFR-3 exists) and RQ3's
      "safely rather than wrongly". Names the Exp-3/Exp-4 separation as confound avoidance.
  1.5 Contributions (\label{sec:contributions}) -- C4 only, verbatim from prd.md:124. Second
      paragraph draws the claim boundary explicitly: pipeline, bus, FSM, controller, both backends
      and the demo are the document's substance but are NOT claimed as novel. A one-bullet section
      invites "is that all?", so the boundary is defended in the text rather than padded.
  1.6 Structure (\label{sec:structure}) -- five-chapter map, closing on the document's thesis rather
      than on logistics (the failure mode flagged against Master Ch 1 above).

**No measured number and no \TODO{} anywhere in this chapter.** 1.2 promises in its own prose that
results arrive in Ch 5, so the Exp-4 figures already in STATE.md (150 trials / 0 collisions / 432
clamp interventions) were deliberately not used, and 1.3 was written to forward-promise their
structure instead. Whoever writes Ingenieur Ch 5 should quote NFR-12 in 1.3's exact words.

Write-once held against Master Ch 1, which was re-read before drafting: the Master owns the
structured-output argument (controller reads JSON, spike S3's mis-addressed collective command), so
1.3 gives Layer 1 one sentence with ownership named and argues error DIRECTION and stop-path
LATENCY instead. The sentence handing C1-C3 back to the Master is freshly worded, as is 1.6's
closing thesis statement.

Label convention for this document fixed in a header comment so Ch 2-6 resolve against it:
chap:introduction / chap:state-of-the-art / chap:architecture / chap:implementation /
chap:validation / chap:demonstration. **ch2_state_of_the_art.tex still has no \label on its
\chapter -- whoever drafts B7 should add \label{chap:state-of-the-art}**; not touched here (one
task per session).

`python tools/check_tex.py thesis/ingenieur/ch1_introduction.tex`: 10 problems, all confirmed
cross-file false positives (5 refs to chapters not yet written; 5 cites -- lim2025, llamacpp,
pyflyt, reynolds1987, whisper -- all verified present in thesis/bibliography.tex before use). No
in-file dangling refs, no cell-count or column-width findings on either tabularx, ASCII clean.
Both tables need tabularx + booktabs in a preamble that does not exist yet; Master Ch 3 carries
the same outstanding dependency, and neither thesis has a main.tex.

Stopped here: Ingenieur Ch 1 done in full, nothing waiting on a measurement. Not started:
Ingenieur Ch 2 (B7, still owed, distinct voice-UAV literature only -- do not reuse Master Ch 2
prose), Master Ch 4-6 (Mon 21 AUTHOR slot), Ingenieur Ch 3-6 (Tue 22 AUTHOR slot).

## Next session starts with
1. **Kaggle.** `python train/make_kaggle_bundle.py` -> upload train/pfe_kaggle_data.zip as a
   Dataset named `pfe-swarm-data`; upload train/kaggle_finetune.ipynb; GPU T4, Internet ON;
   HF_TOKEN secret for the gated Llama-3.2. Run All, ~2 h unattended.
   It produces: adapters, zero-shot AND fine-tuned Surface-A EM, parity_hf.json, GGUF f16.
   **Merging and GGUF conversion moved onto Kaggle** -- both need torch+peft and SS0.5 keeps
   those off this workstation. Only llama-quantize (pure C++) runs locally.
2. Power the Pi. Nothing needs it until the quantised artefacts exist, i.e. Saturday afternoon.
3. Then locally: llama-quantize -> Q8_0 + Q4_K_M (six artefacts), Gate 3, Surface-B, ablation.
For Exp-3 later: `python data/mix_noise.py --input data/audio/s1_16k --output data/audio/mixed
--sources dregon --partition eval`  (note: s1_16k, the normalised corpus, not the masters).
Do NOT re-run Gate 1 or Gate 2.

## Exp-1 RESULT (Sun 20 Sep, Block A session, A1)

Task: 60 timed runs, Q4_K_M only, on the Pi (Sat-19 triage). Raw: `results/exp1.csv`
(1,647 trial rows: 180 scored + 1,467 warm-up, tagged `<artefact>-warmup` and excluded
from percentiles by name, not discarded -- every request the Pi answered is still in
the CSV). New: `eval/exp1.py` (the Pi runner). `eval/bench.py` gained
`tokens_predicted`/`tokens_evaluated` columns and a `tokens_per_second` aggregate --
Table 17's tok/s column had nothing to read before this session. `eval/tables.py` now
actually reads `results/exp1.csv` to fill Table 17's p50/p95/tok-s/Peak-RSS columns and
Table 19's Decode p95, instead of hard-coding `--`. `python -m pytest -q`: 650 passed
(unchanged), `python -m pytest eval/ -q`: 122 passed.

Protocol: llama.cpp b10863 (88ada91c, the Gate-3/Surface-B commit) built fresh on the
Pi -- only llama-cli/llama-quantize/test-gbnf-validator existed there before, not
llama-server. `taskset -c 1-3 -t 3` per Table 7; governor forced to `performance`
(the script refuses to run otherwise -- spike S1's own numbers were confounded by an
`ondemand` governor mid-throttle, and this run does not repeat that mistake); swap
disabled for the duration, restored after; page cache dropped between configs;
ten-minute warm-up per config before anything is scored; `cache_prompt=true`
(deliberately unlike Surface-B's accuracy sweep, which disables the cache for
single-slot determinism -- Table 6's "cached prefix" prefill budget is a claim about
the deployed runtime, which does cache the prefix across requests).

**No active cooler is fitted on the Pi (confirmed with the author -- not yet
purchased).** All 180 scored trials, across all three configs, ran under active
thermal throttling: `throttled_now` = 1 on every single trial, core clock capped at
1.5 GHz (down from the pinned 2.4 GHz "performance" target), steady-state temperature
90.6-91.1C. This is not a harness bug -- it is exactly what spike S1 flagged and
recommended fixing ("Mount the Raspberry Pi Active Cooler... prior to Exp-1"), and
what still hadn't been done before tonight's run. **NFR-10 (throttled trials <=5%) is
missed by the widest possible margin: 100% vs a 5% budget.** Reported as measured, not
reconciled.

| Config (Q4_K_M) | n | Prefill p50/p95 (ms) | Decode p50/p95 (ms) | tok/s | Peak RSS | Decode budget (<=1,100 ms p95) | NFR-9a (<=2.5 GB) |
| :--- | ---: | :--- | :--- | ---: | :--- | :--- | :--- |
| llama-3.2-1b-instruct | 60 | 430.8/787.4 | 1504.6/2458.9 | 10.75 | 1.63 GB | **MISS** (+123%) | MEETS |
| qwen2.5-0.5b-instruct | 60 | 74.7/614.2 | 922.5/1518.9 | 18.13 | 0.68 GB | **MISS** (+38%) | MEETS |
| smollm2-360m-instruct | 60 | 51.6/516.7 | 701.1/1338.9 | 24.11 | 0.55 GB | **MISS** (+22%) | MEETS |

**NFR-9a (peak RSS <=2.5 GB) is MET by every configuration, comfortably** --
consistent with Table 8's worst-case estimate, and now a real measurement rather
than the Table 8 arithmetic bound. This closes NFR-9a for the model selection rule.

**The decode budget (Table 6, <=1,100 ms p95) is MISSED by all three Q4_K_M
configurations under present (uncooled) conditions**, including qwen2.5-0.5b, which
spike S1 had projected as the one configuration meeting it (by a 51 ms margin -- and
that margin was itself measured under an already-throttled 1.5 GHz clock per S1's own
report, so the two measurements are on comparable footing, not apples-to-oranges).
Per prd.md SS10.2 this is reported as a genuine miss, not reconciled: **if Exp-2's
NFR-2 (E2E p95 <=2,500 ms) is measured under the same uncooled conditions, it is very
unlikely to be met by llama-3.2-1b** -- its decode p95 alone (2,458.9 ms) consumes
essentially the entire E2E budget before VAD, STT, prefill, validate or dispatch are
even added.

**Llama-3.2-1B's elimination, previously extrapolated from spike S1, is now CONFIRMED
by direct measurement.** S1 scaled qwen's throttled 20.97 tok/s baseline by parameter
count to project ~10.7 tok/s for llama-3.2-1b Q4_K_M; tonight's real measurement is
10.75 tok/s -- within 0.5% of the extrapolation. It is also the worst of the three
configs against the decode budget by a wide margin (+123% vs +22-38% for the other
two).

**The Q8_0 elimination remains UNMEASURED, still an extrapolation from S1.** This
triage explicitly scoped Exp-1 to Q4_K_M only (STATE.md, Sat 19); no Q8_0 artefact ran
on the Pi tonight. Table 17's Q8_0 rows keep `--` in the latency/RSS columns for that
reason, not because the join failed. S1's claim that "Q8_0 variants are physically
incapable of closing the decode latency budget" is therefore **still an inference from
measured Q4_K_M numbers and architecture scaling, not a direct Pi measurement** --
flagged here rather than silently treated as closed.

**Rough, unverified projection if a cooler removes the throttle:** decode time should
scale close to linearly with clock for this compute-bound workload. At the full
2.4 GHz pinned clock (1.6x the throttled 1.5 GHz), a naive linear rescale of tonight's
p95s gives ~1,536 ms (llama, still a MISS), ~949 ms (qwen, would MEET), ~837 ms
(smollm2, would MEET). This is NOT a measurement and must not be quoted as one in
either thesis -- it is only grounds for prioritising a cooled re-run of qwen/smollm2
over llama-3.2-1b if the cooler arrives before Exp-2.

**Two bugs found on the Pi's actual configuration while running this, fixed in
`eval/exp1.py` before being reported as data:**
1. `swapon -a` (meant to restore swap after the run) silently does nothing on this
   Pi: it manages its swapfile via `dphys-swapfile`, not an `/etc/fstab` entry, so
   `-a` had nothing to reactivate. Found by checking `free -h` after the run showed
   0B swap where 511 MiB was expected. Fixed by recording the actual device path
   from `swapon --show` before turning swap off, and swapping back on by that exact
   path afterward -- verified restored (511 MiB) before moving on.
2. `swapon`/`swapoff` are not on PATH under a bare `ssh host cmd` (no login shell) --
   hardcoded to `/sbin/swapon`, `/sbin/swapoff`.

Governor is left at `performance` intentionally, not reverted to `ondemand` --
Exp-2 needs the same setting (Table 7: "verified during Exp-1 and Exp-2").

Stopped here: Exp-1 done for all three Q4_K_M configs; `results/exp1.csv` written;
Tables 17 and 19 regenerated (`python eval/tables.py`) and now carry real p50/p95,
tok/s, Peak RSS and Decode-p95 numbers instead of `--`. Not done, named per rule 10:
a cooled re-run (blocked on the cooler purchase, see "Blocked / needs human" above),
Q8_0 on the Pi (out of this triage's scope), and Exp-2/Exp-3 themselves (A6/A7,
runtime side already unblocked per the A2 entry above).

## Gate 4 RESULT -- Table 9 cell coverage (Sun 20 Sep, Block A session, A3)

Task: prove every flight-state x command cell of prd.md Table 9 is covered by a test, and
that rejections resolve to HOVER with a log entry. `swarm/fsm.py` already existed and was
not changed by this session -- the gap was the proof, and the proof is what was built.

**Gate 4 is GREEN.** `swarm/test_fsm.py` grew from 30 to 100 tests; whole repo 650 -> 720.

```
$ python -m pytest swarm/test_fsm.py -q
100 passed in 0.22s

$ python -m pytest swarm/test_fsm.py -v -k "table_9_cell"
collected 100 items / 50 deselected / 50 selected
swarm/test_fsm.py::test_table_9_cell[LANDED-formation] PASSED            [  2%]
swarm/test_fsm.py::test_table_9_cell[LANDED-move] PASSED                 [  4%]
...  (50 cells: LANDED / TAKING_OFF / FLYING / LANDING / ABORTED x the ten intents)
swarm/test_fsm.py::test_table_9_cell[ABORTED-unknown] PASSED             [100%]
====================== 50 passed, 50 deselected in 0.15s =======================

$ python -m pytest -q            # whole repo, pfe_swarm active
720 passed in 52.78s
```

**What makes this a proof rather than 50 more passing tests.** Three things are separated,
because each can be wrong independently:

1. `TABLE_9_AS_SPECIFIED` -- Table 9 transcribed by hand into the test file, keyed on plain
   strings. It deliberately does NOT import `TABLE_9_LEGALITY`; a test that derives its
   expectations from the code under test agrees with it by construction and proves nothing.
   `test_fsm_table_matches_the_specification` then compares the two encodings.
2. `test_transcription_matches_prd_table_9` parses Table 9 out of `prd.md` at run time and
   compares it to the hand transcription -- so a typo in the test file fails the suite rather
   than silently redefining the gate. prd.md is untracked by design (roadmap 0.4a), so this
   one **skips** rather than fails when the file is absent; on this workstation it ran and
   passed, and the parse was inspected by hand (all ten intents, including the two prose
   cells -- set_param's "Every state except `ABORTED`" and unknown's bare em dash).
3. The 50 cells are a **generated** cross product, `[(s, i) for s in FlightState for i in
   INTENTS]`, with `test_the_cell_matrix_is_the_complete_cross_product` asserting
   5 x 10 = 50. A cell cannot be omitted without the generator changing; there is no
   hand-maintained list of cells to fall out of date.

Each cell drives `handle_command` with a real payload and asserts three things: what is
dispatched, the state afterwards, and the log entry. `test_every_cell_payload_survives_
layer_2` asserts all ten payloads pass `validate()` unchanged -- without it, a payload that
fell back to Hover inside Layer 2 would make its cell pass for the wrong reason.

**The proof was mutation-tested before being called green** (each mutation applied to
`swarm/fsm.py`, run, then `git checkout`):

  - hover made legal in LANDING (fsm.py drifts from Table 9)  -> 17 failed, 83 passed
  - airborne rejection returns None instead of Hover          ->  9 failed, 91 passed
  - the hover-illegal rejection log silenced                  -> 24 failed, 76 passed

**On "rejections resolve to HOVER with a log entry".** Table 9's caption says exactly that,
and it cannot be literally true in all five states: Table 9's own rows declare `hover`
illegal in LANDED, LANDING and ABORTED, so resolving a rejection there to HOVER would
dispatch a command the same table rejects -- and that rejection would resolve to HOVER
again. ADR-0002 already settled this (it predates this session): rejections resolve to
HOVER where Table 9 permits hovering (TAKING_OFF, FLYING) and to a logged no-op where it
does not, because dispatching HOVER would otherwise spin up a grounded swarm, arrest a
descent at altitude, or fly out of an abort. The gate is therefore recorded as green
against **that** reading, not against the caption's literal wording, and the tests assert
the property the caption is actually about:
`test_no_rejection_is_ever_silent` asserts, for all five states, that every illegal intent
produces a structured log record and resolves to either HOVER or a no-op -- never to a
movement command. The whole-thesis version of this sentence is one an examiner may ask
about, so it is stated here in full rather than left implicit in a passing test.

FR-11's second half -- "the explicit non-vocal recovery path out of `ABORTED`" -- is covered
by `test_recovery_out_of_aborted_is_reachable_only_off_the_voice_path`: all ten intents are
fed to an ABORTED machine and none of them escapes, then `manual_reset()` does. That is the
one-directional reflex Ingenieur Ch 1 Sec. 1.3 argues for, now asserted rather than asserted-in-prose.

**Named, not started (rule 10 -- one task):**
  - ADR-0002 documents the rejection log as carrying `"action": "fallback_hover"`; the code
    actually emits `"fallback": "HOVER"` on that branch (the no-op branch does use `action`).
    The new tests do not depend on either key, so nothing is blocked, but ADR and code
    disagree on a field name and one of them should be corrected.
  - `swarm/fsm.py:141` annotates `handle_command`'s parameter as `Command | Mapping | str`
    without importing `Command`. Harmless at run time (`from __future__ import annotations`),
    but it would fail a type-checker or any `get_type_hints()` call.
  - Gate 3 parity is still PENDING in this file while Surface-B results already exist --
    the contradiction Master Ch 3.4 flagged and declined to resolve. Still unresolved; not
    this task.

Stopped here: Gate 4 closed and recorded. `swarm/fsm.py` unmodified (verified with
`git status` after each mutation revert) -- this session added tests only. Not started:
A6/A7 (Exp-2, Exp-3), A4 (McNemar), A5 (the NFR-9/NFR-18 limitation).

## NFR-9 / NFR-18 LIMITATION (Sun 20 Sep, Block A session, A5)

Task: write the Limitations entry for NFR-9 and NFR-18 together, once, citable by both
theses. New: `eval/abstention.py` (+ `eval/test_abstention.py`, 7 tests),
`results/limitation_abstention.md` (the entry), `results/nfr9_nfr18_abstention.csv`
(per-configuration counts), `docs/adr/0006`. The entry is GENERATED from
`results/surface_b_preds/*.jsonl` -- rule 5, no figure in it is typed by hand. Master Ch 5
and Ingenieur Ch 6 both cite it; neither re-derives it.

**Both budgets missed by every artefact, reported as measured per prd.md SS10.2:**
NFR-9 safe-failure 0.0000-0.1579, pooled **0.0530** (28 of 528 errors) vs a >=0.70 budget;
NFR-18 false-command 0.1867-0.3933 vs <=0.05. Re-baselined against the measured figures
and the re-baselining reported (ADR-0006 D4), explicitly as descriptive baselines, not as
targets lowered until they could be met. prd.md Table 12's rows are NOT edited.

**Two corrections to the task brief's own numbers, both in the direction of the brief
being wrong, not the data.**

1. **The brief gave NFR-9 as "0.00 to 0.23". The deployed surface measures 0.0000 to
   0.1579.** The 0.2308 figure is real but belongs to `qwen2.5-0.5b Q4_K_M test_ood`
   **with the grammar OFF** (`results/surface_b_nogrammar.csv`) -- the ablation surface,
   which is not what ships. Quoting it as Surface B would have overstated the system's
   safe-failure rate, i.e. flattered it on the safety metric. The entry quotes the
   grammar-on range and says in SS6 why the ablation figure is excluded.
2. The brief's NFR-18 range (0.187-0.393) and its Qwen claim (13 errors on `test_golden`,
   none resolving to `unknown` or HOVER) both CONFIRMED exactly against the per-item files.

**Two findings sharper than the brief's framing, both from the per-item files rather than
the summary CSV:**

  a. **Almost nothing the safe-failure metric counts is an abstention.** Of the 28 safe
     failures: **24 are the model emitting `hover`** (a command to hold -- safe, but
     indistinguishable from the model believing the operator said "hold"), **3 are the
     validator falling back to HOVER** (each a `formation` missing a slot its shape
     requires), and **1 is the model emitting `unknown`** -- one instance in 3,540 items
     of the model declining to answer. The metric cannot make this split by construction
     (it is defined over the dispatched action), which is why the entry reports the origin
     breakdown beside the rate.
     **Got this wrong first and caught it before it shipped:** the initial `_origin`
     classified EVERY `hover` as a validator fallback, which would have reported "27
     validator catches, 1 abstention" -- a system that checks itself -- instead of "24
     confident commands, 3 catches, 1 abstention". The headline claim survives either way;
     the mechanism it names does not, and the wrong version credits `schema/validate.py`
     with work it never did. `eval/test_abstention.py` regression-tests exactly that.
  b. **Abstention is topic-triggered, not confidence-triggered.** On `test_ood` (all 150
     references `unknown`) the models DO abstain, 60.7%-81.3% of the time -- the
     capability is present and reachable under the grammar. On the in-domain splits it
     vanishes: 282 errors, and `unknown` volunteered on a real-command item exactly **once
     in 2,640** -- and that once was itself an error (smollm2 declined a valid `hover`,
     item 0178, "freeze, units fo-- four through five"). The system can tell "this is not
     about drones"; it cannot tell "this is about drones and I did not catch it". This
     selects the future work: a confidence gate addresses it, more OOD training data does
     not.

**In-domain error taxonomy (new, Master Ch 5's material).** Pooled over six artefacts on
`test_synth`+`test_golden`, 282 errors: 240 (85.1%) right intent / wrong parameters, 39
(13.8%) wrong intent but still actionable, 3 (1.1%) safe. **98.9% of in-domain errors
dispatch an executable command.** Largest single family: the **yaw sign flip**, 114 of 282
(40.4%) -- the swarm turns through the correct angle the wrong way. Structurally invisible
to all three validation layers (schema-valid, in-envelope, internally consistent); no
consistency check distinguishes clockwise from anticlockwise. Quotable example on real
recorded speech is in the entry (qwen Q4_K_M `test_golden` item 0036).

Future work named as future work, not as done: a confidence gate on decoder
log-probabilities, and oversampling `unknown` in training. Neither implemented, measured
or claimed.

**Caveat carried into both theses (entry SS6, ADR-0006 D4):** NFR-9 is sourced to Exp-1
**and Exp-3** (prd.md Table 12), and Exp-3 has not run. This baseline rests on Exp-1
evidence only and must be revisited when A7 lands -- Exp-3 puts real ASR error into the
input, which can only move the figure.

```
$ python eval/abstention.py
wrote results/nfr9_nfr18_abstention.csv
wrote results/limitation_abstention.md
$ python -m pytest eval/test_abstention.py -q
7 passed in 0.11s
$ python -m pytest -q
727 passed in 53.31s
```

Note on that 727 (was 650 at the Exp-1 entry): +63 is A3's Gate 4 cell coverage, already
committed (8ac396c, 68511d9); +7 is this session; the remainder is A4's McNemar work
**uncommitted in the working tree** (`eval/mcnemar.py`, `eval/plots.py`, modified
`eval/stats.py`/`eval/test_stats.py`, `results/mcnemar.*`, `results/figure2_pareto.*`).
Those files are NOT part of this session's commit -- a concurrent Block A session owns them.

Stopped here: the limitation entry is written, generated, tested and reported in ADR-0006.
Nothing in this task touched `thesis/`, `schema/`, or prd.md. Named, not started (rule 10):
whoever drafts Master Ch 5 / Ingenieur Ch 6 (B4 / B11) should cite
`results/limitation_abstention.md` rather than re-derive it, and must carry the Exp-3
caveat above. A4's McNemar work needs its own commit from its own session.

## McNEMAR + FIGURE 2 (Sun 20 Sep, Block A session, A4)

Task: run the paired tests that answer RQ1 and produce Figure 2, from the per-item
predictions already on disk. No model re-run, no server started. New: `eval/mcnemar.py`
(the runner), `eval/plots.py` (Figure 2 -- the file `eval/__init__.py` has promised since
Session 04 and that `run_all.sh` already required), `mcnemar()` + `bonferroni_alpha()` in
`eval/stats.py`, `eval/test_mcnemar.py` (12), `eval/test_plots.py` (9), 13 added to
`eval/test_stats.py`. Outputs: `results/mcnemar.csv`, `results/mcnemar.md`,
`results/figure2_pareto.pdf` + `.png`.

**Provenance first: the per-item files reproduce Table 17 exactly.** Exact match
re-derived from `results/surface_b_preds/*.jsonl` through `eval/metrics.py` matches all
eighteen `grammar=on` rows of `results/surface_b.csv` to four decimals. This is asserted
on every run, not checked once by hand -- `check_against_surface_b()` returns a non-empty
problem list and `eval/mcnemar.py` exits 1 if the two ever drift. Without it the McNemar
tables would be a second, independently-computed set of numbers sitting beside Table 17
with nothing tying them together.

### Family 1 -- model against model, `test_golden`, Q4_K_M (confirmatory, alpha = 0.0167)

| A vs B | EM A | EM B | a | b | c | d | b+c | test | p | signif. |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | ---: | :--- |
| llama-3.2-1b vs qwen2.5-0.5b | 0.9100 | 0.9350 | 182 | 0 | 5 | 13 | 5 | exact | 0.0625 | **no** |
| llama-3.2-1b vs smollm2-360m | 0.9100 | 0.7600 | 148 | 34 | 4 | 14 | 38 | chi2_cc | 2.5e-06 | **yes** |
| qwen2.5-0.5b vs smollm2-360m | 0.9350 | 0.7600 | 149 | 38 | 3 | 10 | 41 | chi2_cc | 1.1e-07 | **yes** |

### Family 2 -- Q4_K_M against Q8_0 within each model, `test_golden` (confirmatory, alpha = 0.0167)

| A vs B | EM A | EM B | a | b | c | d | b+c | test | p | signif. |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | ---: | :--- |
| llama-3.2-1b Q4_K_M vs Q8_0 | 0.9100 | 0.9150 | 182 | 0 | 1 | 17 | 1 | exact | 1.0 | **no** |
| qwen2.5-0.5b Q4_K_M vs Q8_0 | 0.9350 | 0.9300 | 186 | 1 | 0 | 13 | 1 | exact | 1.0 | **no** |
| smollm2-360m Q4_K_M vs Q8_0 | 0.7600 | 0.7900 | 144 | 8 | 14 | 34 | 22 | exact | 0.286 | **no** |

Secondary rows (not corrected, not evidence in their own right): the model comparison
repeated at Q8_0 reproduces the same verdicts (llama vs qwen p = 0.375 n.s.; both vs
smollm2 significant), and the quantisation pairs on `test_synth`/`test_ood` are all
non-significant (p = 0.0768 to 1.0). Full table in `results/mcnemar.md`.

**The RQ1 answer, stated at the strength the evidence supports.** The 360M model is
separated from both larger models decisively, on both quantisations. **llama-3.2-1b and
qwen2.5-0.5b are NOT separated** (p = 0.0625 against alpha = 0.0167): qwen's 2.5 pp EM
lead on `test_golden` rests on five items. Note the shape of that table -- **b = 0**:
there is no `test_golden` item llama gets right that qwen gets wrong, so the disagreement
is entirely one-directional and qwen's predictions are a strict superset of llama's on
this split. One-directional and still not significant at a corrected alpha, because five
items is five items. Ch 4 should say the two are indistinguishable on accuracy and let
Figure 2's other two axes break the tie; it must not say they are equal.

**Two statements the write-up must not make, both of which the contingency counts refuse.**

1. **Non-significant is not equivalent.** Where `b+c = 1` (llama and qwen, each against
   its own Q8_0) the smallest attainable exact p-value is 1.0 -- the test cannot reject
   whatever the truth is. What those rows report is a *bound*: the two quantisations of
   one model disagreed on exactly one item in 200. That is a stronger and more honest
   sentence than "no significant difference", and it is the one to use.
2. **An identical EM is not an identical model.** smollm2-360m scores 0.8125 at both
   quantisations on `test_synth` -- a delta of exactly zero. The pairing shows 24
   disagreements split 12/12. Comparing the summary column alone would have reported
   agreement where there are two dozen differences that happen to cancel.

Together these put a test under the Sat-19 claim that "quantisation is nearly free", which
until now was an eyeballed comparison of point estimates: six paired comparisons, none
significant, discordance 1 to 24 items. **Q4_K_M's selection is now defensible on measured
paired evidence, not on the absence of a visible gap.**

**Test choice, stated because it changes two p-values.** Exact binomial below 25 discordant
pairs, continuity-corrected chi-square above (`EXACT_BELOW_DISCORDANT`). Only the two
comparisons against smollm2-360m (b+c = 38 and 41) take the chi-square branch. Both
p-values are carried in `results/mcnemar.csv` for every row and the verdict is identical
under either test throughout -- so the threshold is documented rather than load-bearing.
Bonferroni is applied **per family of three**, not once across all fifteen rows: the two
confirmatory families answer different questions, and pooling them would penalise each for
the other's existence.

### Figure 2 -- `results/figure2_pareto.pdf`

Spec (prd.md 8.2 / roadmap Session 07): EM vs p95 latency, marker area proportional to peak
RSS, one point per model x quantisation, 2.5 s target as a vertical line. Three deviations,
each drawn on the figure's own face rather than left to a caption:

1. **Three of the six specified points do not exist.** Exp-1 was scoped to Q4_K_M by the
   Sat-19 triage, so no Q8_0 artefact has a Pi latency or RSS. They are named in a box on
   the axes with their EM, not dropped and not plotted at a guessed x.
2. **The x-axis is not the quantity the 2.5 s line bounds.** NFR-2 runs end-to-end from
   end-of-speech; Exp-1 measured the SLM stages only (Table 6's prefill + decode, summed,
   nearest-rank p95 of the per-trial sums -- not the sum of the two p95s). Every plotted x
   is a **lower bound** on E2E, so a point left of the line has not met NFR-2, only failed
   to rule itself out. Exp-2 (A6) measures the real thing. A second, solid line at 1,350 ms
   (Table 6's own SLM allowance, 250 + 1,100) is the budget actually comparable to the axis
   -- and **every config clears 2,500 ms on SLM stages alone except llama-3.2-1b, which
   does not: 3,238.6 ms before VAD, STT, validate, FSM or bus are added.**
3. **Every trial was thermally throttled** (100%, 1.5 GHz cap, no cooler). Said in the
   subtitle, because a Pareto plot invites the reader to read the x-axis as a property of
   the model when here it is partly a property of the enclosure.

**llama-3.2-1b Q4_K_M is Pareto-dominated** -- slower *and* less accurate than
qwen2.5-0.5b Q4_K_M (3,238.6 ms / 0.9100 against 1,771.5 ms / 0.9350) and 2.4x its peak
RSS. The frontier is {smollm2-360m, qwen2.5-0.5b}, and smollm2 is on it only because it is
cheaper, not because it is adequate: at EM 0.7600 it is under NFR-4's 0.85 floor, drawn as
a dotted horizontal line so the frontier cannot be misread as a menu of deployable options.
`pareto_frontier()` is tested against these exact three points.

**`run_all.sh` stage_report was broken and is fixed.** It called
`python eval/stats.py --in results/ --out thesis/`, but `eval/stats.py` is a library with
no `__main__` and no argparse: that invocation ran no analysis, ignored both flags and
exited 0 -- the silent partial run the file's own header warns produces stale thesis
numbers. `require eval/stats.py` also could not fail, since the file existed. The stage now
requires and runs `eval/mcnemar.py` and `eval/plots.py` with no invented flags, and the
`DUE` map tracks `eval/mcnemar.py` instead. Verified: `bash run_all.sh report` regenerates
all four artefacts from `results/*.csv` alone.

```
$ python eval/mcnemar.py
  ... 15 comparisons ...
wrote results/mcnemar.csv and results/mcnemar.md
provenance: recomputed exact match matches results/surface_b.csv on all 18 rows

$ python eval/plots.py
wrote results/figure2_pareto.pdf
wrote results/figure2_pareto.png
  frontier  smollm2-360m-instruct    Q4_K_M  EM 0.7600  p95  1610.21 ms  RSS 0.55 GB
  frontier  qwen2.5-0.5b-instruct    Q4_K_M  EM 0.9350  p95  1771.54 ms  RSS 0.68 GB
  dominated llama-3.2-1b-instruct    Q4_K_M  EM 0.9100  p95  3238.57 ms  RSS 1.63 GB
  UNMEASURED (x3, Q8_0) -- Exp-1 covers Q4_K_M only

$ python -m pytest eval/ -q
163 passed in 12.25s
$ python -m pytest -q
761 passed in 55.94s
```

Correction to the A5 entry's test-count arithmetic above: its 727 was measured **without**
this session's files, not partly with them. Baseline at HEAD (this session's work stashed
and its new files ignored) collects 727; A4 adds 34 (13 in `test_stats.py`, 12 in
`test_mcnemar.py`, 9 in `test_plots.py`) for 761. A5's +7 and A3's +63 are correct.

One bug found in this session's own code before it shipped: `load_correct()` reported a
missing prediction file with `path.relative_to(REPO)`, which raises its own `ValueError`
for any path outside the repo -- the error message's construction crashing in place of the
error it was written to report. Caught by the test that asserts the message names
`surface_b.py`. Fixed with a `_display()` helper in both new modules.

**Named, not started (rule 10 -- one task):**
  - **The 2.9 model selection rule is NOT applied.** Session 07's item 2, and it needs
    Exp-2's E2E p95, not Exp-1's SLM-only figure: NFR-2 bounds a quantity nothing has yet
    measured. Figure 2 shows where the candidates sit; it does not select one, and nothing
    in this session records a deployment decision. A6 unblocks that.
  - `run_all.sh` has no stage running `eval/tables.py` at all, so Tables 16-19 are not on
    the one-command reproduction path even though every figure in them is script-generated.
    One line, but a different subsystem's omission than the one this task owns.
  - Figure 2's Q8_0 points stay absent until Q8_0 runs on the Pi -- out of the Sat-19
    triage's scope, still flagged at the Exp-1 entry above.

Stopped here: McNemar and Figure 2 done, both regenerating from `results/*.csv` through
`bash run_all.sh report`. Nothing in this task touched `thesis/`, `schema/`, `prd.md` or
any existing result CSV. Master Ch 4 SS4.5 (B3) can now cite `results/mcnemar.md` and
`results/figure2_pareto.pdf` rather than ranking Table 17's point estimates.

## BIBLIOGRAPHY AUDIT + .bib MIGRATION (Tue 22 Sep)

Three commits: 72a02e1 (verify), 59ae943 (migrate), and an untracked PRD sync recorded
here because git cannot see it.

**What was wrong.** The 18 entries were lifted verbatim from `docs/project/PRD.tex` in
689ec6e and never checked. Checking all of them against primary sources found `sbc2025`
attributed to an author who did not write the paper -- "J. Gou et al., Benchmarking 25
LLMs on Single-Board Computers" does not exist; the real work is arXiv:2511.07425,
Nguyen and Nguyen. `pyflyt` credited "J. Jet" (Jun Jet Tai). `esc50` gave the dataset's
name as the paper's title. `smollm2` and `llama32` pointed at blog posts, and `llamacpp`
bundled two projects under a URL whose org had moved.

**The part that was not a bibliography problem.** Three passages in Master Ch 1 and Ch 2
described `sbc2025` as finding a ceiling "independent of which model" and throughput that
"does not vary meaningfully with the choice of board." The real paper reports
architecture-specific bottlenecks and a runtime effect (Llamafile 4x over Ollama) plus a
~1.5B parameter ceiling -- close to the opposite. Prose was rewritten to what the source
supports, which reads as a stronger warrant for this project's design, not a weaker one:
the thesis picks a runtime and sub-1.5B models, the exact lever the survey says dominates.

**Format.** `thesis/bibliography.tex` is gone; `thesis/references.bib` replaces it,
biblatex + biber, matching `thesis/sample_thesis`. The old `thebibliography` printed every
entry regardless of citation, so each thesis would have listed references it never cites
(the Ingenieur: 12 of 19). All 19 keys carried over unchanged -- no chapter text needed
editing. `tools/check_tex.py` now resolves citations against the `.bib`, so a standalone
chapter check is conclusive about `\cite` for the first time; `\ref` still needs a
`main.tex`.

**PRD sync (untracked, invisible to git).** `docs/project/PRD.tex`'s own
`thebibliography` held the pre-verification copy, so a future session extracting from it
would have reintroduced "J. Gou". All six corrected entries are synced there, `whispercpp`
added, the L205 runtime row now cites both, and the block carries a header naming
`thesis/references.bib` as authoritative. PRD and `.bib` hold the same 19 keys.

**Not verified:** no TeX toolchain in the environment. The `.bib` was checked structurally
(19 entries, no duplicate keys, balanced braces, ASCII-clean) but never run through biber.
First compile is the real test.

**Open:** `speechcmd` is still cited by nothing -- expected, Master Ch 4-6 are unwritten.
Neither thesis has a `main.tex`; the biblatex wiring for one is recorded in the
thesis-writing skill.

## Master Ch 3 corrections (Tue 22 Sep, Block B session)

Task: analyse four fixes another agent proposed against `thesis/master/ch3_method.tex`, verify
each against current repo state (a lot moved since the chapter was drafted Sun 20: Exp-1 ran,
Gate 4 closed, McNemar/Figure 2 landed, the bibliography was audited and migrated to
`references.bib`), and apply what survived verification. Nothing in `schema/`, `data/`, `train/`,
`eval/`, `swarm/`, `runtime/` or `prd.md` touched -- Block B scope, thesis text only.

1. **`idlist` grammar listing was stale, confirmed against `schema/cmd.gbnf` on disk.** The
   chapter reproduced `idlist ::= [0-9] ( "," [0-9] )*` (transcribed from `prd.md` S5.1 at
   drafting time); the live file reads `[0-4] ( "," [0-4] ){0,4}`, matching `N = 5` (prd.md
   Table 1). This is not cosmetic: ch1_introduction.tex already narrates the unbounded form's
   spike-era failure ("since fixed to a bounded form") without saying what the fix was --
   ch3 was the one place that should have shown it, and as drafted it silently reproduced the
   *pre-fix* grammar, contradicting ch1. Fixed against the real file, tied to N=5 and Layer 2's
   `ids ⊆ {0...N-1}` rule, and cross-referenced to the ch1 anecdote.
   **Flagging, not fixing:** `prd.md` S5.1's own printed grammar still shows the old unbounded
   form -- `schema/cmd.gbnf`'s header comment says "if these two disagree, the PRD wins and this
   file is the bug," but here the file is right and the PRD transcription is stale. A future
   Block A / PRD-sync session should correct S5.1 to match the artefact that actually ships and
   passed FR-1 (5,191 labels, 0 rejected) -- same shape of problem as the Gate-3-pending-vs-
   Surface-B-results contradiction flagged at the original Ch3 drafting session, still open.
2. **n_latency=200 was wrong for two of three latency experiments.** STATE.md's own Sat-19
   triage (already read once, missed on the first pass) and the Exp-1 RESULT entry both show
   Exp-1 executed at 60 reps/Q4_K_M-only, and Exp-2 is triaged to 60/branch. Corrected S3.5's
   protocol paragraph to state the design target (200, prd.md Table 15) against what was
   actually run/triaged per experiment, rather than one uniform figure.
3. **Table~\ref{tab:metrics} (Table 10 reproduction) was missing three rows the harness
   actually computes.** Verified against source rather than trusting the other agent's
   wording: `eval/metrics.py::schema_validity` (NFR-6, 1.0 by construction under the grammar)
   and `eval/bench.py`'s throughput aggregate (tokens summed over decode-seconds summed, not
   mean-of-ratios, on the `taskset -c 1-3 -t 3` cores Table 7 pins to inference) were absent
   entirely; the Latency row's "Used in: Exp-2" was also wrong -- Exp-1 reports its own SLM
   decode/prefill p50/p95 (Table 17), which is this document's own material, not only the
   Ingenieur's. Added Schema validity and Throughput rows, expanded Latency, updated the
   lead-in sentence on which rows Ch4 draws on, and flagged in the table's own caption that
   these three are grounded in the harness rather than in prd.md's printed Table 10, which
   does not list them -- another prd.md-staleness instance, not silently smoothed over.
4. **"The companion document" (2x) and "the companion runtime" (1x) → "the \emph{M\'emoire
   d'Ing\'enieur}".** Direct violation of the thesis-writing skill's naming rule, caught
   correctly by the other agent for two instances; found and fixed a third the diff missed.

One thing NOT applied from the proposed diffs: nothing else in the other agent's four snippets
was taken verbatim -- Fix 1's idlist rule matched the real file exactly so it was reused, but
its added prose was rewritten to cite N=5/Layer 2/the ch1 cross-reference instead; Fix 3's
metric definitions were re-derived from `eval/metrics.py`/`eval/bench.py` source rather than
trusted as written, since a Method chapter defining a metric wrong is worse than not defining it.

`python tools/check_tex.py thesis/master/ch3_method.tex`: citations now resolve against
`references.bib` directly (STATE.md's bib-migration entry above notes this became possible for
the first time) -- 11 cites, 0 unresolved. 4 remaining flags are the same cross-file `\ref`s as
before (chap:related-work, chap:results, sec:constrained-decoding, sec:quantisation).

Stopped here: the four corrections are applied and committed. Not started: nothing else in Ch3
touched. Still outstanding from the original drafting session: the annotation pass-2 `\TODO{}`
(unchanged), and Master Ch 4 itself.

## FOURTH MODEL -- h2o-danube3-500m, Surface A (Mon 22 Sep)

Added as the **iso-parameter control** for RQ1, after the supervisor objected that
comparing 1.2B / 0.5B / 360M models is not a fair comparison. The objection as stated
cannot hold -- RQ1 asks for the trade-off *across* 0.36-1.2B, so size is the independent
variable, and the measured data already refused the premise (qwen-0.5B beat llama-1.2B,
and McNemar could not separate them). But its residue is real and was unanswerable with
three models: they sit at three sizes in three *different families*, so size and family
were perfectly aliased and every pairwise comparison changed two things at once.

`h2oai/h2o-danube3-500m-chat` -- 514M measured against qwen2.5-0.5b's 494M, a fourth
family (H2O.ai), Apache-2.0, technical report arXiv 2407.09276. Llama-2-derived, so all
seven Table 14 target modules exist and the recipe applied unchanged (asserted: the
lora/optim/train/precision/checkpoint_selection blocks are byte-identical across all four
configs).

### RESULT -- Surface A, FP16, fine-tuned (results/table33_iso_parameter.md)

| model | params | family | test_synth | test_golden | test_ood |
| :--- | ---: | :--- | ---: | ---: | ---: |
| smollm2-360m  |   362 M | HuggingFace | 0.8250 | 0.7750 | 0.6200 |
| qwen2.5-0.5b  |   494 M | Alibaba     | 0.9542 | 0.9350 | 0.7267 |
| h2o-danube3   |   514 M | H2O.ai      | 0.8875 | 0.8700 | 0.7200 |
| llama-3.2-1b  | 1,236 M | Meta        | 0.9583 | 0.9250 | 0.7333 |

**The 1.24B model is bracketed by the two 0.5B models on test_golden**: 0.8700 (danube)
< 0.9250 (llama) < 0.9350 (qwen). Parameter count does not order the table.
  - Family, at matched size (494M vs 514M, 4.0% apart): **6.5 pp**.
  - Size, across 3.4x (362M -> 1,236M): **+15.0 pp**.
  - Within the 0.5-1.2B band size is worth **-1.0 pp** (qwen 0.9350 vs llama 0.9250).

This is the point of the control: with only qwen at 0.5B you conclude "size does not
help"; with only danube at 0.5B you conclude "size helps by 5.5 pp". Same 1B model,
opposite conclusions, depending which 0.5B you happened to pick. That IS the aliasing,
demonstrated rather than argued.

**Caveat that must travel with the 6.5 pp.** The recipe is frozen at three epochs for
every model. Per-epoch val EM: danube 0.7667 -> 0.8333 -> 0.8708 (+3.75 pp on the last
epoch) and smollm2 0.650 -> 0.750 -> 0.775 (+2.5) are both STILL CLIMBING, while qwen
(+0.83) and llama (0.00) have converged. The two still improving are exactly the two
lowest scorers, so part of any gap is convergence under a fixed budget, not capability.
The defensible claim is "under an identical three-epoch budget", never "in capability".

**test_ood 0.7200 -> false-command rate 0.2800**, inside the existing 0.187-0.393 range.
A fourth independent model from a fourth family missing NFR-18 the same way strengthens
the abstention argument considerably: it is systemic, not a property of one model.

### Two deviations, both declared

1. **No system role.** Danube's chat template raises `TemplateError: System role not
   supported` -- the same construct Gemma uses, whose vendor guidance is exactly this
   fold. First Kaggle attempt died on it. Resolved by folding the system prompt into the
   user turn for models whose template refuses one. PROBED, not keyed off a model name,
   so the three already-trained models provably keep their byte-identical system-turn
   rendering. One helper (`build_messages`) serves training, Surface-A eval and the Gate
   3 parity dump so they cannot drift. Recorded per model in training_history.json
   (`system_role_supported`) and parity_hf.json (`system_role_folded`).
   State it at its real strength: per-model template variation is ALREADY the protocol
   (ChatML vs Llama-3 vs SmolLM2), so this is that rule applied one step further, not a
   new confound. It matters most for the zero-shot rows; three epochs of completion-only
   training make the scaffolding a learned fixed prefix for the fine-tuned rows.
2. **Separate Kaggle session.** Trained alone via the notebook's ONLY hatch. fp16 GPU
   training is not bit-reproducible, so this artefact is not from the same session/image
   as the other three. The alternative -- retraining all four -- would have produced new
   adapters for the existing three and invalidated Surface B, Tables 17/18/19, McNemar
   and the abstention entry. A declared session caveat is far the cheaper cost.

### Scope: Surface A ONLY

No Surface B, no Pi latency run, no grammar ablation for this model. The Pi is a serial
resource and Exp-2/Exp-3 have never run; spending Pi time on a fourth model's latency
while a whole research question (RQ2) has no data is the wrong trade. Consequences:
  - Table 33 is separate from Table 17 by necessity -- Table 17 is Surface B, and a model
    with no Surface B would be a row of blanks in the table that answers RQ1.
  - **McNemar's Bonferroni alpha is UNCHANGED at 0.0167.** Table 33 is a separately
    declared comparison, not an expansion of Family 1, so no existing verdict moves.
  - `gguf/h2o-danube3-500m-chat-f16.gguf` (1.03 GB, sha256 19ae0dbc7a86...) is kept so
    promotion to Surface B never needs another Kaggle session. If it is ever promoted,
    `llama-server` will likely need `--jinja` for Danube's non-standard template, and
    that flag must then be added for ALL FOUR with test_template_parity.py re-run against
    the existing three to prove no token IDs moved.

### Provenance and merge

`surface_a.csv`'s three Danube rows re-derive exactly from
`train/kaggle_out/preds_h2o-danube3-500m-chat_*.jsonl` through `schema/canon.py`
(0.8875 / 0.8700 / 0.7200, zero malformed predictions even ungrammared at FP16 --
independent support for Table 19's finding that the fine-tune teaches the format).

`train/merge_kaggle_out.py` is new, because the notebook's own closing instruction
(`unzip -o pfe_outputs.zip -d train/kaggle_out/`) is correct for a full run and
DESTRUCTIVE for a partial one: surface_a.csv and parity_hf.json are per-session
aggregates and `-o` would have replaced the versions describing the other three models.
The script unions them, is idempotent, refuses if a merge would drop a model, and
refuses if the system prompt ever differs between runs. The notebook now prints the
correct command for each case.

Test suite: 768 passed (was 761; +7 is eval/test_tables.py, new -- Table 33 is the one
table nothing else cross-checks, since 17/18/19 are guarded by eval/mcnemar.py's
provenance assertion against Surface B).

**Named, not started:** Exp-2 and Exp-3 still have no runners and no data. That remains
the largest hole in the project and is the next thing to do.

### GATE 3 RESULT for h2o-danube3 -- FAIL, and the gate earned its keep (Mon 22 Sep)

Run after the Surface-A merge, to test whether the Surface-A-only scope could be lifted.
New: `eval/check_parity_gguf.py` (the llama.cpp half of Gate 3; `eval/test_template_parity.py`
only ever checked the HuggingFace half, because the other half needs a running server).

```
$ python eval/check_parity_gguf.py qwen2.5-0.5b-instruct gguf/qwen2.5-0.5b-instruct-Q4_K_M.gguf
formatted text : 10/10 identical
token IDs      : 10/10 identical
GATE 3 (llama.cpp side): PASS          <- control; the harness is sound

$ python eval/check_parity_gguf.py h2o-danube3-500m-chat gguf/h2o-danube3-500m-chat-f16.gguf
formatted text : 10/10 identical
token IDs      :  0/10 identical
GATE 3 (llama.cpp side): FAIL
```

**The predicted risk did not happen; a different one did.** The config warned that
llama-server might need `--jinja` for Danube's non-standard template. It does not --
llama.cpp renders `<|prompt|>...</s><|answer|>` correctly with no flag, and the formatted
text matches HuggingFace byte for byte on all ten audit prompts.

**The tokenisers segment that identical text differently.** Same length (32 tokens),
same detokenised string, divergence at index 9:

    HF (training)   1605, 538  ->  [' dr', 'one']
    llama.cpp       3483, 485  ->  [' dro', 'ne']

SentencePiece merge ranking is not unique and the two implementations resolve " drone"
differently. It hits all ten prompts because "drone" is in the system prompt, which the
fold puts into every one.

**Consequence: Danube CANNOT have a Surface B.** The model was trained on one
segmentation and would be served on another -- accuracy degrades with no error, which is
exactly what prd.md Sec. 10.1 names as this project's highest-cost silent failure. Any
Surface-B number for this model would be uninterpretable as "the same model as Surface A".
The Surface-A-only scope is therefore now a *hard* constraint, not a time-triage choice.

**This is a reportable methodology result, not just an obstacle.** Gate 3 is declared in
prd.md Sec. 10.1 as a mandatory gate after every conversion rather than a diagnostic run
when something looks wrong. Here it was run on a new model and caught a real
train/serve tokenisation mismatch that no amount of reading the rendered prompt would
have revealed -- the text was byte-identical. Master Ch3 Sec. 3.4 already describes the
gate; Ch4 or Ch5 can now cite an instance of it firing. The existing three pass 10/10, so
their Surface-B numbers are unaffected and this casts no doubt on Tables 17/18/19.

Not attempted (would each need its own justification and none is cheap): rebuilding the
GGUF with a different tokeniser conversion path, retraining under llama.cpp's
segmentation, or declaring the mismatch and reporting Surface B anyway.


### GATE 3 CORRECTION -- the checker had two false failures, and one of them was llama-3.2 (Mon 22 Sep)

The section above reported Danube FAIL against qwen as the only control, and asserted
"the existing three pass 10/10" without having measured smollm2 or llama-3.2. Running
all four to build a durable artefact is what exposed the problem:

    llama-3.2-1b-instruct    formatted text 0/10, token IDs 0/10   -> FAIL

llama-3.2-1b has a complete, published Surface B. A checker that condemns it is wrong
about the checker, not about the model, so the verdict was not written up until the
cause was found. It is two harness artefacts, neither a property of any model:

1. **BOS convention.** `/apply-template` omits the leading `<|begin_of_text|>` because
   llama.cpp inserts the BOS at tokenisation time, not into the prompt string. The HF
   dump has it inline. Lengths 51 vs 50.
2. **`strftime_now` in Llama-3.2's template.** Its system turn carries
   `Today Date: <today>`. The Kaggle dump recorded `19 Sep 2026`; the check ran on
   `22 Sep 2026`. One token differs: `'19'` (777) against `'22'` (1313). This one is
   time-dependent -- the same check would have passed on 19 September and failed every
   day after, which is exactly the kind of result that gets believed once and never
   reproduced.

Fixed in `eval/check_parity_gguf.py` by `_align()`, which re-aligns both conventions
**all-or-nothing**: the rules are applied in sequence and kept only if together they make
the two renderings identical; otherwise they are discarded and the raw strings compared.
A first attempt guarded each rule with its own equality test, which failed on exactly the
model that needs both at once -- each rule was blocked by the other's difference. The
all-or-nothing form cannot mask a real divergence, because a normalisation that merely
narrows a mismatch is thrown away. Every normalisation actually applied is named in the
`Normalised` column of `results/gate3_parity.md`.

**Result after the fix, all four measured under the same harness:**

    qwen2.5-0.5b-instruct    text 10/10   ids 10/10   PASS   normalised: none
    smollm2-360m-instruct    text 10/10   ids 10/10   PASS   normalised: none
    llama-3.2-1b-instruct    text 10/10   ids 10/10   PASS   normalised: bos-prefix, today-date
    h2o-danube3-500m-chat    text 10/10   ids  0/10   FAIL   normalised: none

The Danube verdict is unchanged and is now considerably better supported: the same
harness passes three models whose Surface B is already published, and Danube's failure
needs no normalisation to appear -- it is a mid-prompt segmentation split in the word
"drone", at index 9, with both sequences 32 tokens long.

**What this buys beyond Danube.** Tables 17/18/19 previously rested on an unmeasured
assumption that the three deployed GGUFs tokenise the way training did. That is now a
measured fact with a regenerable artefact behind it, which is a stronger claim than the
chapter was making before.

**Still true, and now the only open question here:** promoting Danube to Surface B needs
the tokeniser disagreement resolved (a different GGUF conversion path, or retraining under
llama.cpp's segmentation). It is not blocked on hardware time. `train/configs/
h2o-danube3-500m.yaml`'s `scope_note` said it was; that note has been corrected, since
accuracy runs on the workstation and Surface B would never have cost Pi time at all.

## BRANCH A KEYWORD SPOTTER -- trained (Wed 23 Sep, 01:00-01:30)

Calendar correction: depot is **Thu 24 Sep 23:59**, not the morning.

Annotation pass 2 committed (f716c57): 50 items, 4.04-day interval, 0 disagreements, seal intact.

`python train/train_wake.py` -> `runtime/models/wake/{swarm_hold,swarm_abort}.onnx` (gitignored,
hashes in `wake_heads.json`), report `results/wake_training.{md,json}`. Loaded by
`runtime.branch_a.load_trained()`. Two openWakeWord heads (sklearn MLP -> hand-built ONNX) over
the frozen v0.5.1 front end. Operating point 0.999, selected on val.

| held-out | result | requirement |
| :--- | :--- | :--- |
| FRR test, hold / abort | 0.027 / 0.007 (n=300 each, Piper voices only) | NFR-16 <= 0.10 |
| ambient speech FA | 1 in 0.429 h = 2.33/h, CI [0.06, 12.98] | NFR-15 <= 1/h -- NOT demonstrated |
| golden set (author) FA | 0 in 0.304 h | -- |
| authored near-miss FA | 34 in 0.100 h (31 hold head) | stress figure only |
| algorithmic delay p95 from keyword offset | hold 188 ms, abort 131 ms (workstation) | NFR-1 is Exp-2 on the Pi |

Caveats that must travel: all positives synthetic (3 Piper voices); test seen twice (round 1
rejected on val diagnostics); threshold saturated at grid top; ambient stream too short for
NFR-15. **Cheapest improvement: the author records ~20 real "swarm hold" + ~20 "swarm abort"**
(5 min) -> real-voice FRR.

Still open for Exp-2: BranchA has no debounce (fires every frame above threshold);
`runtime/audio.py` and `runtime/vad.py` still not built; Exp-2/Exp-3 runners not written.

START_SESSION.md BLOCK B rule 8 corrected (references.bib, count with grep). Ingenieur Ch2
voice-UAV candidates under verification (background agent) -- Ch2 waits on it; Ch3 does not.

## Debounce + VAD built (Wed 23 Sep, ~02:00)

- `runtime/branch_a.py`: per-class 1.0 s debounce, same rule as `train_wake.py:count_events`
  (asserted by test). One keyword -> one command.
- `runtime/vad.py`: Silero ONNX on onnxruntime (no torch), `Endpointer.feed()` -> `Utterance`
  with T0. Default min_silence 450 ms, derived from Table 6's 500 ms, not tuned.
- **DECISION FOR THE AUTHOR (RESOLVED Thu 24 Sep: keep 450 ms, see end of file):** at Table 6's 500 ms, 10.5% of golden utterances split into >1
  segment (17.5% @400, 2.5% @700, 0% @1000). Keep 450 ms and report the split rate, or raise
  the VAD budget line. Affects Exp-2 E2E latency and Branch B accuracy on disfluent speech.
- `data/wake_real_transcripts.txt`: 40 prompts for the author's real-voice Branch A takes.
- Still not built: `runtime/audio.py` (live mic) and the stream loop driving both branches;
  Exp-2 / Exp-3 runners.

## Exp-1 OF RECORD is the COOLED run (Wed 23 Sep, recorded here late)

365d2f5 made `results/exp1_cooled.csv` Exp-1 of record; `results/exp1.csv` (uncooled, 100%
throttled at 1.5 GHz) is kept as the thermal-headroom result. Cooled, 0/180 throttled,
67.5-74.1 C. Decode p95 vs the 1,100 ms allowance: **smollm2 785 MEETS, qwen 1,033 MEETS,
llama 1,842 MISSES.** SLM combined p95 vs 1,350: qwen 1,072 (278 spare), smollm2 894, llama 2,282.
Selection rule applied in Master Ch4: **Qwen2.5-0.5B Q4_K_M.** Earlier sections of this file
saying "all three Q4_K_M configs miss the decode budget" describe the uncooled run only.

Master Ch4 drafted (d70c4e7) and audited: 6 numeric errors and 3 structural gaps fixed (see the
commit before this one). Ch3 now carries Tables 3.4 (requirements of record) and 3.5 (latency
budget as deployment constraint) -- Ch4 and later chapters \ref them instead of PRD numbers.
Master Ch5 inherits from Ch4: the grammar-ablation / abstention reading (fine-tune made the
grammar nearly redundant AND removed abstention -- a hypothesis, not a measurement), and the
clock-ratio overshoot (SmolLM2 1.69x > 1.6x: remaining term unidentified).

## Exp-3 RESULT -- accuracy half, workstation (A7a, Wed 23 Sep, 03:50-04:25)

`python data/mix_noise.py --input data/audio/s1_16k --output data/audio/mixed --sources dregon
--partition eval` -> 800 files. Realised SNR was checked on every file (worst 19.997 dB at 20),
and none needed attenuation. Session 1 only, as declared. Then `python eval/exp3.py` (new, e7844c3)
followed by `python eval/tables.py`. Raw: `results/exp3_preds/{text,clean,20,15,10,5}.jsonl`
(per segment: transcript, raw, canonical, dispatched, host timings). Summary: `results/exp3.csv`.
Tests and envelope: `results/exp3_analysis.md`. Table: `results/table20_end_to_end.md`,
`thesis/generated/table20_end_to_end.tex`.

| SNR | CRR [95% CI] | WER % | EM | EM - CRR [95% CI] | safe-failure |
| :--- | :--- | ---: | ---: | :--- | :--- |
| clean | 0.690 [0.625, 0.750] | 23.4 | 0.935 | +0.245 [0.185, 0.310] | 2/62 |
| 20 dB | 0.675 [0.610, 0.740] | 24.3 | 0.935 | +0.260 | 1/65 |
| 15 dB | 0.650 [0.585, 0.715] | 26.1 | 0.935 | +0.285 | 1/70 |
| 10 dB | 0.590 [0.520, 0.660] | 28.8 | 0.935 | +0.345 [0.280, 0.410] | 4/82 |
| 5 dB  | 0.495 [0.425, 0.565] | 36.2 | 0.935 | +0.440 | 4/101 |

**NFR-7 MISSED (0.690 vs 0.80). NFR-8 MISSED (0.590 vs 0.65). NFR-9 MISSED at every level
(0.014-0.049 vs 0.70).** Reported as measured. Not reconciled.

- **Provenance:** the `text` condition (reference text through the runtime parser) equals
  Surface B's raw output on 200/200 items. EM here IS Table 17's EM, and EM - CRR is the
  ASR-stage cost on identical items (prd.md 6.1).
- **The VAD split is a measured CRR cost, not only a latency trade-off.** 23 of the 200 clean
  items split under the 450 ms endpoint (11.5%), and **all 23 failed**. That is 23 of the
  62 clean failures. The canonical example is golden 0003: the fragment "proceed." dispatched
  a `takeoff` before the real move arrived. This feeds the open DECISION FOR THE AUTHOR
  (keep 450 ms or raise the VAD budget line) with a number it did not have before. Do NOT
  project "CRR without splits": that configuration was not run.
- **Scoring rule of record:** a split item is correct only if every dispatched command is
  correct. The last-segment-only CRR is 0.730 clean, and it misses NFR-7 too. So the miss
  does not depend on this rule.
- **Pre-registered test run as specified:** arcsine + one-way ANOVA F(4,995)=5.47, p=2.3e-4.
  Tukey separates only 5 dB from clean/20/15. Its weaknesses are stated in the analysis: on
  0/1 outcomes the arcsine is a rescaling, and the same items appear at every SNR, so the
  groups are not independent. Reported beside it: Cochran's Q=56.65, p=1.5e-11, and exact/cc
  McNemar (Bonferroni over 10 pairs). Those separate clean from 10 dB and 5 dB, and 20 and
  15 dB from 5 dB.
- **Operational envelope:** CRR >= 0.65 holds down to 15 dB on the point estimate, and at no
  level on the 95% lower bound. CRR >= 0.80 holds at no level.
- **Safe failure is ~0, so the NFR-9 limitation now rests on Exp-3 too.** This closes the
  caveat in the A5 entry above: the Exp-1-only baseline of 0.053 was not an artefact of text
  input. With real ASR error it drops further, to 1.4-4.9%. `results/limitation_abstention.md`
  is NOT regenerated here (different subsystem, rule 10), and it should now cite Exp-3.
- Cross-check: clean WER 23.4% vs Exp-0's prompted 23.0%. Segmenting before whisper did not
  move the ASR error rate. The CRR loss is parser-visible ASR error plus splits.

Tests: `eval/test_exp3.py` 9 passed; `python -m pytest -q` -> 803 passed.

**Named, not started (rule 10):**
  - A7b: the same runner on the Pi (`--preds results/exp3_pi_preds` writes `exp3_pi.csv`, so it
    cannot overwrite this run). It must fill Table 20's E2E p50/p95 from real-time replay and
    diff the Pi's raw outputs against `results/exp3_preds/`. The workstation's per-segment
    `stt_ms/prefill_ms/decode_ms` are NOT of record. The E2E columns in exp3.csv are empty by
    design. The runner needs a real-time replay mode (it currently feeds as fast as it can);
    that is A7b's to add.
  - `results/limitation_abstention.md` / ADR-0006: add the Exp-3 evidence (above).
  - The rationale for the author's 450 ms decision now has a CRR figure to cite (all splits fail).

Stopped here: A7a done, accuracy columns final, Table 20 rendered with E2E pending.

## Writing progress -- Master Ch 5 (B4, Wed 23 -> Thu 24 Sep) -- DONE
thesis/master/ch5_discussion.tex complete, no \TODO. Commits ca1ed8c (5.1-5.3), 8a3980d (lead-in),
1efbf29 (Ch3 sentence Ch5 depends on), 87ebad1 (review scripts). Every section reviewed and approved
by the author one at a time. Review script: 0 FAIL, 4 WARN (chap:conclusion; negated "guaranteed";
163.0 x2 = quoted item value), 91 PASS -- every 5.2/5.3.2 figure recomputed, not just traced. Clean
build (build/master/): 0 errors, only chap:conclusion undefined.

What each section settles (Ch6 may rely on these readings; none is a verdict):
  5.1 trade-off -- frontier is two points {SmolLM2, Qwen}; knee is Qwen2.5-0.5B specifically, not
      "0.5B" (Danube 6.5 pp below at FP16 = >1/3 of the 16.0 pp FP16 frontier distance; both terms
      FP16 -- the seeded l.40 surface-mixing finding is fixed). The rule ranks on EM with latency
      only as constraint/tie-break, so the trade-off never reaches the decision; SmolLM2 loses the
      EM RANKING (0.935 vs 0.760), the 0.85 miss is "a second fact". Qwen remains only against the
      re-baselined budget (misses 2,500 ms as specified by 622 ms, 25%). Stage allowances are budget
      lines, not rule constraints. Enclosure reads as a term in the latency budget.
  5.2 failure modes -- safe-failure 28/528 = 24 model hover + 3 validator + 1 unknown; abstention by
      REQUEST TYPE (supported vs unsupported), not by uncertainty (OOD abstain 60.7-81.3%, in-domain
      unknown once in 2,640, and wrong); 98.9% of in-domain errors executable, yaw sign flip 114/282;
      HYPOTHESIS (labelled): one training effect gives both the near-redundant grammar and the
      missing abstention; untestable on these data.
  5.3.1 internal -- controlled by design: greedy, parity 10/10 prompts, checkpoints on val_synth.
      Six threats: Danube's fold + separate session (reference-surface-only is a scope limit, not a
      confound); three-epoch budget, none converged; zero-shot changes fine-tune AND grammar at
      once, preds not retained; thermal gain attributable to thermal state, not clock (1.69x vs
      >=1.6x); 200 items / 12 patterns, p optimistic (Qwen>SmolLM2 survives; Qwen~Llama is power,
      not equivalence; 60-rep p95 makes the 67 ms margin fragile); labels generated not annotated,
      test_synth and test_golden share the 12 families (not independent confirmations).
  5.3.2 external -- the ONE reference to the acoustic-robustness experiment (Table 3), Ingenieur
      named as owner: parser bit-identical board vs workstation 200/200 (Qwen Q4_K_M, one build);
      CRR 0.690 clean / 0.590 at 10 dB vs EM 0.935 -> loss is at the speech stage; EM = the parser's
      accuracy given a correct transcript. Then other speakers (6.2-49.5% WER spread), other
      hardware/runtimes (sbc2025 4x), small schema (grammar cost/benefit may differ at scale),
      four models / two quant schemes.

Also changed this session: Ch4 sec:exp0 / sec:exp1 alias labels deleted (issue 04 hand-off;
nothing else referenced them). Ch3 3.2 gained one sentence: unknown is taught by 81 of 1,940
training pairs (35 assistant-style, 46 unsupported drone requests like "follow me"), none of them a
supported command made unreadable. **[Corrected Thu 24 Sep: that split was by source_variant and
mislabelled. By family it is 20 assistant queries (F115), 21 unsupported capabilities (F116, e.g.
"follow me") and 40 lexical near-misses (F117, e.g. "hold that thought"); Ch3 now says so -- see
the Ch3 follow-up below.]**

**Named, not started -- Block A (rule 1: not a B-session's to touch):**
  - results/limitation_abstention.md s3 says the single model `unknown` is "the only instance, in
    3,540 items, of the model declining to answer" -- false, it declines on 60.7-81.3% of test_ood;
    it contradicts its own s4. s2/s7 "valid commands almost exclusively" is also loose (81 unknown
    training rows). Generated by eval/abstention.py; fix there and regenerate. Ingenieur Ch6 (B11)
    cites this file -- do not copy either sentence.
  - 103 of the 114 yaw sign flips are reference-negative / model-positive (a dropped minus sign).
    Supports 5.2's untested explanation, but is in no generated artefact, so it is NOT in the
    thesis. Adding it to eval/abstention.py's taxonomy would make it citable.
  - Ch3's false-command definition ("...that also survives the validator") vs eval/abstention.py
    (dispatched != unknown, so a validator HOVER fallback counts as a false command): differs on
    the one smollm2 OOD fallback per quant. Not reconciled; noticed while writing 5.2.

Stopped here: Master Ch 5 done. Next brief: B5, Master Ch 6 (unhedged RQ1 answer). Ch6 must not
add caveats -- a new limitation belongs in Ch5.

## Branch A real voice + Exp-3 error analysis (Wed 23 Sep, afternoon)

**Branch A on the author's voice (129fb28).** The 40 takes (`data/audio/wake_real/`, now committed
as irreplaceable recordings) were resampled by `data/resample.py --glob "w*.wav"` and scored by
`python eval/wake_real.py` -> `results/wake_real_voice.{md,json}`, using train_wake.py's own
scoring and the unchanged 0.999 threshold. hold 1/20 missed (FRR 0.050, exact CI [0.001, 0.249]);
abort 0/20 (FRR 0.000, CI [0.000, 0.168]); **0 cross-triggers in 40**. The synthetic-voice caveat
is closed. **NFR-16 is NOT proven:** at n=20 even zero misses leaves the upper bound at 0.168 > 0.10.
The one miss (w03) peaked at 0.9977 against 0.999, which is the saturated threshold already named.
Delay p50/p95 is 230/550 ms (hold) and 160/430 ms (abort) against TTS's 188/131 ms p95. It is
**indicative only**, measured from the capture tool's energy-based end of speech rather than a
forced alignment. Exp-2's NFR-1 measurement should use these real takes as its keyword audio and
watch whether the gap is real.

**Exp-3 error analysis of record.** `eval/exp3.py:failure_cause` gives one cause per failed item,
in a fixed order, in `results/exp3_analysis.md`. Clean, 62 failures: ASR right intent / wrong slot
23, endpointer split 22, parser wrong on text 12, ASR wrong intent 5, perfect transcript + parser
wrong 0. At 5 dB the slot errors grow to 52 (of 101). exp3.csv is unchanged.

**Decided with the author:** there is no legitimate way to raise CRR before depot. Every candidate
fix (700 ms VAD, base.en, a new prompt) would be chosen on the golden set, which is the test set,
because s2/s3 were cut. base.en also breaks STT latency (spike S6: ~3.8 s on the Pi vs 1.2 s).
They go to Limitations / future work, not into the results. The 700 ms run is dropped.

Test suite: 807 passed.

Stopped here. Next: **A6, Exp-2 on the Pi** (runtime/stream.py first, tests first). That is the
only remaining gap that leaves an RQ (RQ2) unanswered. A7b only if Pi time remains.

## Exp-2 RESULT -- dual-path latency on the Pi (Wed 23 Sep, A6)

302d6a8 `runtime/stream.py` (one 80 ms frame loop, Branch A + endpointer on core 0,
Branch B worker on cores 1-3, swappable frame source for A11). 19119f0 `eval/exp2.py` + the
run of record: `results/exp2.csv`, `results/exp2_analysis.md`, `results/exp2_raw/`,
Table `thesis/generated/exp2_latency_budget.tex` (`tab:latency-budget`). Pi cooled,
governor performance, 0/360 trials throttled, 50-78 C, affinity verified per thread.
Pi setup: whisper.cpp rebuilt at the workstation's commit 52a939a in `~/whisper.cpp-52a939a`
(run with `WHISPER_CPP_DIR`), same ggml-tiny.en.bin (sha256 921e4cf8...); venv `~/pfe_venv`
pinned to the workstation's versions.

| requirement | measured p95 | target | verdict |
| :--- | ---: | ---: | :--- |
| NFR-2 E2E from T0 (n=226 segments) | 3,122 ms | 2,500 | **MISSES** |
| -- STT / prefill / decode / VAD wait / validate+FSM | 1,449 / 751 / 915 / 480 / <1 | 1,200 / 250 / 1,100 / 500 / 50 | miss / miss / meet / meet / meet |
| NFR-1 Branch A from offset, idle / loaded (n=78) | 545 / 547 ms | 150 | **MISSES** |
| -- of which spotter + quantisation / Pi compute | 540 / 6 (idle), 18 (loaded) | -- | -- |
| NFR-17 recovery (n=78) | 1,195 ms | 300 | **MISSES** |

- **Where the misses are.** NFR-1: the spotter's own delay (hardware-independent), not the Pi;
  load adds ~12 ms, so Table 7's isolation works. NFR-2: STT and uncached prefill. NFR-17:
  llama-server only notices a closed connection once per second (HTTP_POLLING_SECONDS=1).
- **Selection rule (prd line 633): Qwen2.5-0.5B Q4_K_M does NOT satisfy NFR-2 end to end.**
  It was the only configuration measured end to end; smollm2's SLM stages are ~180 ms
  faster (Exp-1), not enough to close a 622 ms gap, but that is inference, not measurement.
  The prd's own clause applies: the rule "fails loudly" and NFR-2 is re-baselined against
  the measured figure, with the re-baselining reported. **DECISION FOR THE AUTHOR (RESOLVED Thu 24 Sep: re-baseline accepted, see end of file) (and
  supervisor): accept the re-baseline to the measured 3.1 s, stated as such.**
- FR-6: 78/78 triggers hit an in-flight decode, 78 aborted, 0 late results.
- Cross-trigger 0/160. Hold misses 2/80 (w03 twice). One Branch A false accept on the
  golden set (0158, "hover", fail-safe).
- VAD split rate on the Pi: 23/200 = 11.5% (the workstation diagnostic said 10.5%).
- **For A7b:** Pi clean CRR 138/200 = 0.690, the same as A7a, but 4 transcripts and 5 raw
  outputs differ (`results/exp2_preds/clean.jsonl` vs `results/exp3_preds/clean.jsonl`).
  Accuracy is therefore not bit-identical across hardware; A7b owns that finding.
- Not measured: Wi-Fi hop (prd 4.7), live capture latency (A11). Prefill ran with the
  prompt cache off, as deployed; Table 6's line assumes it on.

Stopped here. Next: A7b (Exp-3 on the Pi), if Pi time remains before Thu 12:00; else B10.

## Exp-3 on the Pi (A7b, Wed 23 Sep, 17:05-17:50) -- parity not exact; the Pi is of record

`eval/exp3.py` ran unchanged on drone-pi (same code md5, GGUF sha256 ee914fa8..., whisper.cpp
52a939a, governor performance) into `results/exp3_pi_preds/`; analysed on the workstation
against A7a's per-item files. Commit d4f2ae8.

- **Parity** (`results/exp3_pi_parity.csv`, items; transcript / raw / outcome flips):
  text 0/0/0 -- the parser is bit-identical across x86 and ARM. clean 4/5/0, 20 dB 2/2/0,
  15 dB 5/5/0, 10 dB 6/9/2 (+1/-1), 5 dB 6/6/2 (0/-2). The differences enter at whisper
  and carry through. **The Pi is the result of record**; Table 20 now reads `exp3_pi.csv`.
- **CRR of record (Pi):** clean 0.690, 20 dB 0.675, 15 dB 0.650, 10 dB 0.590, 5 dB **0.485**
  (A7a: 0.495). The rest are the same as A7a. NFR-7, NFR-8 and NFR-9 still MISS. The
  significant pairs are the same (Tukey and Bonferroni McNemar: 5 dB against clean, 20 and
  15 dB). **Write with care:** 10 dB vs 5 dB McNemar is p = 0.0051 against alpha = 0.0050,
  not significant by a hair.
- **Latency per SNR (Table 20's last column, renamed "Stage sum"):** STT + prefill + decode
  + validate per segment, nearest rank, p50/p95 in ms: clean 2156/2869 (n=226), 20 dB
  2132/2871, 15 dB 2167/2867, 10 dB 2181/2906, 5 dB 2198/2977 (n=218). Noise barely moves
  latency: +108 ms at p95 from clean to 5 dB. This is NOT the NFR-2 figure. The replay isn't
  real time, so there's no queue; HTTP and the FSM aren't timed; and STT runs -t 4
  unpinned. NFR-2 stays Exp-2's 3,122 ms.
- **Thermal:** peak 80.1 C; the sticky soft-limit bit (0x80000) is set from ~17:44, during
  5 dB only. No measurable effect: 5 dB per-segment medians track 10 dB, which ran with the
  flag clear, by item position. Accuracy can't be affected. Record it as a caveat and state
  that it was checked. Log: `results/exp3_pi_preds/soc.log`.

Stopped here. Block A experiments are done except the declared cuts (A11 live capture, H2,
A9). Next: writing sessions (B-blocks); A8 freeze at Thu 12:00.

## Author decisions (Thu 24 Sep) -- the two open DECISION FOR THE AUTHOR items, closed
Decided by the author as project owner ("you have my approval, it's my project"). Supervisor
sign-off is not recorded here; the author took the decision in their own name.
1. **VAD endpoint stays at 450 ms**; the 500 ms budget line is not raised. The split rate is
   reported as measured -- 23/200 = 11.5% on the Pi, and all 23 split items fail CRR -- as a
   limitation, not tuned away. Consistent with the earlier call that no fix may be chosen on the
   golden set, which is the test set (the 700 ms run stays dropped).
2. **End-to-end budget re-baselined to the measured 3,122 ms p95** (n = 226), under the selection
   rule's failure clause. Reported as a re-baseline, never as the 2,500 ms requirement met: Qwen
   misses 2,500 ms as specified by 622 ms (25%). Master Ch4 4.7 and Ch5 5.1 already say this;
   the Ingenieur's validation chapter (B10) must state it the same way.


## Writing progress -- Master Ch 6 (B5, Thu 24 Sep) -- DONE
thesis/master/ch6_conclusion.tex complete, no \TODO; its \input is live in main_master.tex, so
chap:conclusion now resolves and the Master has all six chapters. Commits 602447e (chapter),
0b128d1 (tools/review/master_ch6.py: 0 FAIL, 0 WARN, 54 PASS). Clean build (build/master/): 0 errors,
no undefined refs or citations, no Float too large. Every section approved by the author one at a time.

What each section says (B12's abstract and B13's read-through should match these, not paraphrase
them more strongly):
  6.1 answer -- the quotable sentence: across 0.36-1.2 B the trade-off reduces to two
      non-dominated configurations {SmolLM2-360M, Qwen2.5-0.5B}; the rule deploys Qwen2.5-0.5B
      Q4_K_M at 0.935 EM golden. Price between them: 894 vs 1,072 ms SLM p95 (cooled), 0.760 vs
      0.935, 17.5 pp, significant. Llama 0.910 / 2,282 ms, dominated on latency, accuracy gap not
      established -- scoped to the golden split (synth/ood follow parameter count). Standing:
      selected on accuracy against re-baselined constraints; 2,500 ms missed by 622 ms (25%),
      re-baselined to 3,122 ms; memory confirmed for the LM process only (0.68 GiB); selection
      independent of SmolLM2's unmeasured E2E latency (NOT "independent of the re-baselining" --
      that is false). Abstention miss stated here (ranges 0.0000-0.1579 / 0.1867-0.3933).
  6.2 established -- C1: validity is a decoder property; measurable contribution 1 decode in
      3,540, 0.17 pp in the grammar's favour; reachability is not measured by a rate. C2: none of
      the accuracy is available zero-shot; the baseline does not attribute the gain to fine-tune
      or grammar (Ch5 5.3.1 wording). C3: pipeline delta -1.5..+1.5 pp, not separated from zero
      (never "no cost"); latency holds for a cooled board. Family control 6.5 pp, exploratory,
      its own paragraph (reference surface, not the C3 harness).
  6.3 next steps -- 1 confidence gate (threshold on a calibration set, not golden); 2 training
      pairs of supported commands made unreadable -> unknown (not "oversampling"); 3 SmolLM2 E2E +
      full-stack memory (selection does not depend on it). None implemented.

Concurrent-session note: at commit time the working tree held another session's uncommitted edits
to ch5_discussion.tex, master_ch5.py, its report and issues/05-master-ch5.md (issue-05 revision:
heading renames, 5.1 knee wording, 5.2 abstention wording). Not committed here, not touched. Ch6 was
re-run against that working-tree Ch5 and still passes; 6.3 step 1 cites 5.2's "98.9% dispatch an
executable command", which that edit kept. If the Ch5 revision changes 5.2's taxonomy paragraph or
5.3.1's untuned-baseline paragraph, re-run tools/review/master_ch6.py and re-read 6.2 P2 / 6.3.

Stopped here: Master Ch 6 done; all six Master chapters written. Remaining Master briefs: B12
(frontmatter, both documents -- the abstract must carry the 6.1 verdict at its strength) and B13
(write-once read-through). Ingenieur B9-B11 are not this session's.

**[Revised Thu 24 Sep, issue 09 review: the 6.1 wording above is superseded.]** The frontier claim
is scoped to the three models timed on the board, at Q4_K_M, because Q8_0 was never timed and
SmolLM2 Q8_0 golden EM is 0.790 against 0.760 at Q4_K_M. The 0.935 is "scored on reference text".
The abstention misses are "one tendency", not a rule, since 60.7-81.3% of OOD items do get unknown.
6.2 now ties C2 to the corpus, not to the zero-shot baseline. The family difference is 6.5 pp "on the
reference surface", between single adapters that also differ in system-prompt rendering and training
session. All three Master abstracts were re-derived from the new 6.1. B13 should read 6.1 as it now
stands, not this entry's summary of it.

## Ch3 follow-up from the Ch5 review (Thu 24 Sep) -- the unknown training pairs, and the ellipsis axis
Two Ch3 errors found by issue 05's verifier and checked against data/ before fixing:
- The 81 unknown training pairs were described by source_variant (35 authored / 46 hard-negative) and
  labelled "assistant-style" / "drone near-miss requests". By template family (data/ood.py,
  data/hard_negatives.py) they are 20 assistant queries (F115), 21 requests for unsupported
  capabilities (F116: 15 authored + 6 from the hard-negative set, e.g. "follow me") and 40 lexical
  near-misses (F117: a command word without a command, e.g. "hold that thought", "the swarm of bees
  is back"). The counts were right; the kinds were wrong, and the Ch3 script only checked counts.
- Ch3 listed "truncated utterances" as a training axis. The axis is ellipsis (data/surface_forms.py
  axis 5): the verb is dropped and every slot kept, 268 training rows. Content-losing truncation
  (F119, "form a") is in val_synth only, plus the OOD truncated_fragment source. Mattered because
  Ch5 5.2 and Ch6 rely on "no training pair maps an unreadable supported command to unknown".
- Ch4's prefill percentiles (38.5 / 328.8 ms, 8/60) were reported as having no generated artefact:
  false alarm -- they come from results/exp1_cooled.csv, which the same section's table caption
  names, and master_ch4.py recomputes them.
Done (author-approved, same day): Ch5 l.161 called all 81 pairs "a request the schema does not support"; the 40
F117 near-misses are not requests; it now says "an utterance the schema does not support as a command". Ch6 only says "81 pairs, none a supported command made
unreadable", which stays true.

## Writing progress -- Master frontmatter (B12, Master half, Thu 24 Sep) -- DONE
B12 is blocked on B11 for the Ingenieur only; the Master half needed only Ch6. Page order kept
as it was by the author (dedication, acknowledgements, abstracts), not the sample's.
  - Abstracts EN/FR/AR (0e1421f; later aligned to the issue-09 Ch6 fixes by that session,
    cfe5b32): three paragraphs + 8 keywords, drafted from Ch6. No \gls in the abstracts on
    purpose (they precede Ch1 and would consume first-use expansions). FR uses decimal commas;
    AR keeps Latin digits (numerals=maghrib), model names \mbox'ed against bidi line breaks.
    The Arabic still wants a native reader's check.
  - Title pages (1dc2667, 067fc85): heading "MASTER THESIS" (the one point both versions of the
    sample agree on); specialty kept "IASD" and the Arabic ministry line kept, both by the author;
    no co-supervisor, line deleted in BOTH title pages; jury "[President Name]" / "[Examiner
    Name]" in both -- plain text now, nothing flags them: grep "Name]" before the depot.
  - Acknowledgements + dedication (067fc85): thesis/shared/frontmatter/, printed by BOTH
    documents, so written document-neutral; jury thanked without names (the two defences need
    not share a jury). Content is the author's (Alhamdulillah, Prof. Khaldi, mother first,
    sister, Yacine, Zineddine, Salah, Mohammed).
  - Acronyms (ce9ea4a, 5d9bec2): all Master keys defined, no \acrfull; Ch4 now uses \gls{em};
    LoRA cell points to 3.3; GGML listed via \glsadd in Master Ch1. Nothing pruned: PID, FR,
    NFR, ROC are the Ingenieur's.
thesis/sample_thesis/ is back in place (gitignored; source ~/Downloads/thesos/). Not done, the
author's call: \setotherlanguage{french} in the shared preamble (the resume hyphenates with
English patterns; no bad break today).

Stopped here: Master is complete except the jury names. Remaining: Ingenieur B9 (Ch4) and B10
(Ch5) unwritten; then the Ingenieur half of B12; then B13 over both documents.

## Writing progress -- Ingenieur Ch 3 (B8, Thu 24 Sep) -- DRAFTED, awaiting review
thesis/ingenieur/ch3_architecture.tex, \label{chap:architecture}, all five sections drafted; no
\TODO{}, no \noautobreak left. Commits: b954b36 (scaffold, lead-in, 3.1, 3.2), da5f625 (3.3),
61eb810 (3.4), 113723a (3.5); other sessions' commits in between renamed Branch A/B to the reflex /
parse path (cca879e) and rewrote 3.1's dual-path reason (a46a8d0).
  3.1 sec:dual-path -- fig:architecture (TikZ), placement, policy-free bus, cached-prefix prompt,
      preemption = ordering rule (correctness) + cancellation (optimisation).
  3.2 sec:membership-rule -- tab:membership. Argued from what the reflex path skips (interpretation,
      not validation): a false accept is well-formed and legal, so no layer can catch it.
  3.3 sec:validation-layers -- tab:legality. Layer 1 one paragraph (write-once, Master owns it);
      layer 2 envelope from schema/schema.py; layer 3 rejection per ADR-0002; both uncaught classes.
  3.4 sec:latency-budget -- tab:stage-budget, row names identical to the generated Exp-2 table.
      States that the four ceilings after T0 sum to 2,600 ms > 2,500. 5,500 ms left underived
      (author's call: 3,000 + 500 + 2,500 = 6,000 is a known question, not fixed).
  3.5 sec:resource-allocation -- tab:core-allocation. Memory WITHOUT the prd 4.6 arithmetic: it is
      not a bound (Master measured 0.68 / 1.63 GiB for the LM process alone, above it).
No measured figure anywhere in the chapter; every result is forwarded to Ch 5 by label.
Build: clean from scratch (latexmk -xelatex main_ingenieur.tex), 0 errors, no Float too large.

Waiting on other chapters, not on measurements:
  - Ch 4 sec:runtime must give the cache_prompt=false reason 3.1 promises.
  - Ch 5 must say where its parse-path span ends: eval/exp2.py:355 stops at the FSM having applied
    the command (loopback on the Pi); Ch 1 and Ch 3 define the span as ending at the bus.
Next: review issue + tools/review/ingenieur_ch3.py (Template A), then the review loop.

Stopped here: B8 draft complete; nothing in the chapter waits on a measurement.

## Master REVIEW closed (Thu 24 Sep) -- issues 00-05, 08, 09 all resolved
The review loop of .scratch/thesis-review/spec.md has run over the whole Master: one Template A pass
per chapter (issues 01-05, 09), then the Template B whole-document pass (issue 08, split from the
Ingenieur on 24 Sep so the finished Master did not wait on Ingenieur Ch2). Every Master script is at
0 FAIL (Ch1 0/2/40, Ch2 0/1/46, Ch3 0/4/132, Ch4 0/1/208, Ch5 0/1/96, Ch6 0/0/54; FAIL/WARN/PASS), the
self-test passes, and the clean build from scratch is 0 errors, 0 undefined, 0 overfull, 63 pages.
The remaining WARNs are each justified in their issue (hand-typed CPU/LoRA/JSON inside quoted or
verbatim text, the negated cited "not guaranteed", the 1,350 ms sum row, Ch2's three-plus-control note).

Issue 08 (round 1: 02294b3; fixes 33f95d8, c688bd6; scripts bcda927, caa1c9b; closed 34171d5).
What the pass established: RQ1 and C1-C3 traced through all six chapters with no empty cell; the 13
headline numbers identical at every occurrence; all 44 \ref targets do what the text says; write-once
clean against the Ingenieur as it stood at 5ed20ba; acronym list complete, 45 printed bib entries =
45 cited keys. 0 BLOCKER, 1 MAJOR, 5 MINOR, 5 NIT.
  - The MAJOR (M-1) was the same failure as issue 09's NEW-1: the abstracts' METHOD paragraph still
    said the control "separates model family from size" (dropped from Ch1 under issue 03 V20;
    negated by Ch3/Ch4/Ch6) because issue 09 re-derived only the verdict sentences. Now Ch1's
    "measures a model-family difference at fixed size" in EN/FR/AR. Lesson, for the Ingenieur
    abstracts (B12, Ingenieur half): check EVERY paragraph of an abstract against the chapter it
    derives from, not only the verdict paragraph against Ch6.
  - Applied: MIN-1 the three Ingenieur-sourced timing figures in Ch4 (751 / 3,122 / 1,063 ms) now say
    "on the cooled board" (Ch1 promises a thermal state for every timing figure; exp2_latency_budget.md
    header says cooled); MIN-2 Ch1's scope paragraph says the controller runs with the simulation on a
    workstation linked to the board; MIN-3 p50/p95 defined in tab:metrics; MIN-4 golden set =
    test_golden = "golden split" tied in one parenthesis (ch3 l.201); MIN-5 the Intent-F1 threshold
    (>= 0.90) added to §4.7's list of thresholds only Qwen meets (all three clear it; master_ch4.py's
    check now counts seven criteria from data); NIT-1 the unused `sha` acronym key deleted from
    shared/acronyms.tex (used in neither thesis; SHA-256 stays hand-typed on purpose).
  - Kept as written: NIT-2 (safe-failure rate in the C3 metric lists), NIT-3 (full checkpoint name at
    first mention, short after -- deliberate), NIT-4 (FR/AR "référence" twice in one sentence; the
    proposed fix would add "not on speech", which the English does not say), NIT-5 (build warnings:
    Amiri small caps, biblatex arabic, xltabular duplicate anchor -- no action).
  - Script error found on the way, fixed in tools/review (bcda927): 4d8d701 renamed the rows of
    results/exp2_latency_budget.md ("SLM prefill" -> "Language-model prefill"); master_ch4/ch5.py
    looked the row up by the old prefix and died with StopIteration on HEAD. Lookup now matches on
    "prefill". Rule held: no expected value changed. If eval/ renames rows again, re-run the Master
    scripts, not just the Ingenieur ones.

Left on the Master -- none of it review work:
  - Jury names: [President Name] / [Examiner Name] on the title page (grep "Name]" before the depot).
  - Artefact location (repository / dataset / GGUF URLs) appears nowhere in the document; the GGUF
    converter commit is unpinned and the control's training image unrecorded (ch3 ~l.502). Issue 03
    "revisit before submission"; the reproducibility question a jury asks first.
  - Arabic abstract: native-speaker read (numbers and qualifiers match the English).
  - Waits on the Ingenieur (issue 10): Master cross-references into Ingenieur Ch5/Ch6 prose not yet
    written (ch3 l.212-213, l.528; ch4 l.140, 348; ch5 l.281-282); the second write-once pass, which may
    hand small Master edits back (issue 08 found Ingenieur Ch1 l.182 repeating tab:metrics' formation-
    accuracy definition verbatim, and l.119-121 saying the Master "states" five FRs it carries as method).
  - Optional polish only: the kept-as-written lists in issues 05, 08, 09 ("knee" undefined, "of record",
    long sentences, metaphors).

Stopped here: Master review closed. Ingenieur track: issue 07 (Ch2) ready-for-human, issue 11 (Ch3)
ready-for-agent, issue 10 blocked on both.

## Master LAYOUT pass (Thu 24 Sep) -- page breaks tuned by hand, 63 -> 62 pages
Done after the review closed, at the author's request, on the built PDF page by page (pdftotext
line counts per page). Five commits: 5304a4b, 08fb8bf, 6413fdd, 6294b54, 9409812. No number or claim
changed; one prose cut (below). Every chapter script at its review counts; clean build 0 errors,
0 overfull, 62 pages.

What was wrong and what fixed it (printed page numbers):
  - End of Ch3: the stage-allowance table sat alone on the chapter's last page. LaTeX places floats
    of one kind in SOURCE order and the full-page requirements table was queued first, so the small
    table could not take the free third of the page before. Its source now precedes the requirements
    table (it is Table 3.4, requirements 3.5; no prose hardcodes either number).
  - End of Ch4: four lines of the closing paragraph on a page of their own. Pareto figure at
    0.8\textwidth absorbs them. Its in-plot labels are ~7pt in the source figure, so ~5pt on the page;
    if too small in print, fix the font in eval/plots.py, not the width.
  - 1.3, 1.4, 4.6 each started a fresh page under the keep-a-section-on-one-page rule (preamble,
    23 Sep), leaving pages a third to a half empty. \noautobreak before each: they flow. 1.5 stays
    whole (letting it flow would leave a 4-line orphan page).
  - Two stranded lines above a heading (end of 3.2 -> 3.3, end of 3.3 -> 3.4, end of 2.1 -> 2.2):
    pulled back by \enlargethispage{\baselineskip} on the page before (ONE line max: footskip is
    30pt, two lines would run into the page number) plus \looseness=-1 on that page's paragraphs,
    one of which sets a line shorter. In Ch2 no paragraph had slack, so the second line came from a
    cut approved by the author: "on the target hardware" and "in particular" dropped from the
    llama.cpp sentence at the end of 2.1. Meaning unchanged.
  - 3.5, 5.3.2 and 6.3 start on a new page (\clearpage before the heading), author's request.
    Cost accepted by the author (option 2): p.29 ends 14 lines short and Ch3's closing 9-line
    paragraph sits alone on p.35 after the full-page requirements table. Tightening every paragraph
    of 3.5 (\everypar{\looseness=-1} + 3 x \enlargethispage) recovered only 2 of the 9 lines and was
    reverted; only cutting ~9 lines of 3.5 or shrinking the table would remove that page.
  - The section rule does NOT act on \subsection (5.3.2 needed the explicit \clearpage).

Fragility, for whoever edits the Master next: the markers (\enlargethispage, \looseness=-1,
\noautobreak, \clearpage) in Ch1-Ch6 are tied to the current text. After editing a paragraph in
2.1, 3.2, 3.3 or 3.5, rebuild FROM SCRATCH (rm -rf thesis/build/master; the rule measures section
heights on one pass and applies them on the next) and re-check the tops of pp. 16, 26, 28, 30 and
the last pages of Ch3 and Ch4. Quick check: per-page line counts via
  for i in $(seq 1 N); do pdftotext -f $i -l $i -layout build/master/main_master.pdf - | grep -c '[^[:space:]]'; done
Remaining short pages are chapter ends (Ch1 p.14, Ch2 p.19, Ch5 p.54, Ch6 p.57) plus the two
accepted above. Front matter: the contents spilled 5 lines onto a second page; now one page (commit after
cbd844f): entries set \small via \addtocontents and the class's 1em gap before each chapter entry
patched to 0.3em inside a group around \tableofcontents (main_master.tex), so the lists of figures
and tables keep the defaults. tocdepth 1 alone would have saved only the 2 subsection lines. The
list of figures (one entry) and list of tables now share a page: \clearpage relaxed in a group
around the two list commands, with an explicit \clearpage before the group (without it the contents'
Bibliography entry drifts onto the lists' page). Master: 60 pages.

Stopped here: Master layout done to the author's satisfaction; nothing open on the Master beyond
the pre-submission items listed in the previous entry.

## Writing progress -- Ingenieur Ch 5 (B10) (Thu 24 Sep) -- DRAFTED, awaiting review
thesis/ingenieur/ch5_validation.tex, \label{chap:validation}, lead-in and all five sections drafted;
no \TODO{} left; the one \figtodo (fig:keyword-curve) since replaced by the generated figure. Commits: 1ed40d8 (lead-in, 5.1, 5.2), 29fa92d
(5.3), 6da10fa (5.4, 5.5, notes removed). Written in parallel with the Ch4 4.3-4.6 session; no file
outside ch5 was touched. Every figure was read from results/ at drafting time.
  lead-in -- criteria from Ch1's two tables and tab:stage-budget, verdict vocabulary (point estimate;
      interval rule for the two keyword criteria). Thermal: latency experiment cooled, 50.5-77.9 C,
      flag clear 0/360 (exp2_analysis.md); acoustic run's state deferred to 5.3. Records: JSON lines
      per trial (exp2_raw/, exp3_pi_preds/), CSV rows per trial (exp4.csv); pinned whisper.cpp
      commit, SHA-256 model files, pinned venv, fixed seeds, greedy decoding. Rerun: "holds per
      experiment rather than for the chapter as a whole" (see run_all.sh below).
  5.1 sec:latency-experiment -- \input tab:latency-budget. Reflex latency MISSED 545/547 (540 spotter
      + 6/18 board); core 0 never over 80 ms. Preemption 78/78 cancelled, 0 late; class matrix 38/40
      hold (one take, w03, twice), 40/40 abort, 0 cross. Recovery MISSED 1,195 (client 6 ms; server's
      once-per-second closed-connection check). E2E MISSED 3,122 (+622, 25%), located in STT and
      uncached prefill; re-baseline stated as re-baseline, verdict stays missed. Per-stage MET (five
      stages; queue 73 and request overhead 8 reported unbudgeted). Keyword false rejects NOT
      DEMONSTRATED, 0.050 [0.001, 0.249] / 0.000 [0.000, 0.168] (wake_real_voice.md). Parse-path span
      stated to end at the FSM applied (exp2.py), bounded by the validation row -- closes the Ch3
      entry's open item. Not measured: live capture, Wi-Fi hop -> sec:limitations.
  5.2 sec:keyword-spotter-evaluation -- wake_training.{md,json}. Keyword false accepts NOT
      DEMONSTRATED, 2.33/h [0.06, 12.98]; the one test false accept survives every threshold
      0.88-0.999 (roc key). Synthetic FRR 0.027/0.007; delay 188/131 synthetic vs 550/430 author.
  5.3 sec:acoustic-robustness -- \input tab:end-to-end; exp3_pi_analysis.md, exp3_pi.csv,
      exp3_pi_parity.csv, soc.log. Clean MISSED 0.690, noise MISSED 0.590, with the one-cause
      error table; ANOVA + its two caveats, Cochran + McNemar (10 vs 5 dB p = 0.0051 vs 0.0050).
      Safe-failure MISSED at every level (0.014-0.039), below even the Master's 0.053 baseline.
      Parity, stage-sum column (+108 ms at p95, not E2E), thermal flag from 17:45:13 in 5 dB.
  5.4 sec:formation-control -- exp4_formation.md, exp4.csv. Collisions MET in the locked phrasing,
      432 clamp interventions (0-14 per trial, needed in 144/150); FA MET but saturated; convergence
      ANOVA + Tukey; scope -> sec:limitations.
  5.5 sec:requirements-summary -- \input tab:requirements-summary; 7 met, 5 missed, 2 not
      demonstrated, 2 not yet run, 1 planned; one sentence per miss with its cause.

Deliberately left out, and why:
  - A "target realistic?" paragraph: none written; Ch6 may take one.
  - The combined language-model row and the start-of-speech row of tab:stage-budget: no measured
    counterpart in the generated table; 5.1 says why neither has a verdict (no hand-summed p95).
  - PyFlyt formation figures (STATE.md Exp-4 entry): not in results/; the smoke test is Ch4's.
  - The Master's WER number: cited in words only, per the promise.

Requests (not made here -- other subsystems):
  - RESOLVED Thu 24 Sep (author lifted the eval/ restriction for this session): fig:keyword-curve
    is results/figure_keyword_curve.{pdf,png}, drawn by eval/plots.py figure_keyword_curve() from
    wake_training.json (test split; 6 tests in eval/test_plots.py; suite 845 passed), commit
    0dab2eb; included in 5.2 with the caption rewritten against the drawing. Ch5 now has no
    \figtodo. The figure floats to a page of its own -- B13's layout pass.
  - eval/tables.py (optional): a combined LM-stage row (prefill + decode per segment) in
    exp2_latency_budget, if the author wants tab:stage-budget's 1,350 ms row judged here.
  - run_all.sh: stages exp2/exp3/exp4 call `eval/bench.py --experiment N`, which without --dry-run
    exits "nothing to do". The real runners are eval/exp2.py (Pi), eval/exp3.py (--preds for the
    Pi), eval/exp4.py, then eval/tables.py. Until fixed, Ch5 says the rerun is per experiment.
  - results/exp2_analysis.md rounds the validation row to 0/1/3 ms, the generated table to 0/0/4
    (exp2.csv: 0.3/0.5/3.5 -- half-to-even vs half-up). Harmless; Ch5 quotes "under 1 ms".
  - references.bib: Tukey's HSD, Cochran's Q and the exact (Clopper-Pearson) interval are named in
    5.3/5.4/5.1 without citation (only mcnemar1947 and dunn1961 exist). Author's call whether to add.
  - RESOLVED Thu 24 Sep: the author confirmed the active cooler was fitted for the acoustic Pi run
    (17:05-17:50). Not recorded in results/ (soc.log has no cooler field) -- this line and the ch5
    commit are the record. Lead-in and 5.3 now say "cooled".

What Ch6 inherits: every verdict via tab:requirements-summary and the section labels; the misses
with causes as 5.5 words them; the safe-failure direction result (5.3, "Direction of the errors");
the limitations 5.1 and 5.4 point at (live capture, Wi-Fi hop, kinematic scope, clamp rewrites only
there); remedies named in 5.3 "No tuning" for sec:future-work; the golden-set reflex trigger on
item 0158 (Pi) vs none on the workstation, unexplained.
What the Ch4 session inherits: RESOLVED -- 5.4 re-matched to 4.5/4.6 after they landed ("kinematic
backend", "vehicles"; 0.35 m and the clamp mechanics now referenced to sec:swarm-controller, not
restated; spawn sentence corrected to swarm/env.py; physics backend: no clamp, no collision claim). 5.1 relies on Ch4 4.2
for the prompt-cache reason and on 4.3 for loopback transport. The Ch4 commit f33e5a1 (4.4, the
state machine) is titled "docs(review): Ch2 report regenerated..." -- its subject is wrong.

Next: after both chapters are committed, the review issue and tools/review/ingenieur_ch5.py.
Stopped here: B10 draft complete; nothing in the chapter waits on a measurement or a figure.

## Writing progress -- Ingenieur Ch 4 (B9, Thu 24 Sep) -- DRAFTED, every section read by the author
thesis/ingenieur/ch4_implementation.tex, \label{chap:implementation}, lead-in + six sections, no
\TODO{}, no measured figure (every number is a parameter of the code). Commits: e0f1674 (lead-in,
4.1), 2be5441 (4.2), ee4f18b (4.3), 2e2116d (4.4), 084a227 (4.5), 11500b4 (4.6). Several commits,
not one: three of this session's --amend calls swallowed concurrent sessions' commits; history
was rebuilt the same day (d0fcf7d explains) and later sections were new commits.
Build: clean from scratch, 0 errors; check_tex over all six chapters concatenated: no unresolved \ref.

Not built, each stated once in its own section (author's decision): live capture (4.1), an entry
point (4.2 -- only eval/exp2.py assembles the runtime), the state machine -> controller link (4.4).
4.5 adds that the controller takes only a formation (no intent is mapped onto it) and implements 3
of the schema's 6 shapes (grid, column, flock have no slot generator).

Handed on -- the chapters that inherit these must carry them:
  - Ch5 keyword-spotter section: the test split was scored twice (4.1; results/wake_training.md).
  - Ch5 latency experiment: prefill cost of cache_prompt=false (4.2 promises Ch5 reports it); the
    server's stop latency bounds preemption recovery (4.2).
  - Ch5 formation section: reports interventions and collisions (4.5 promises both).
  - Ch6 sec:limitations -- 4.3/4.4/4.6 point there by \ref, so these three are PROMISED:
      (a) the Wi-Fi hop never carried a command (bus ran on the Pi's loopback only);
      (b) the raw-intent defect: fsm.handle_command judges legality on the pre-validation intent;
          FlightStateMachine(LANDING).handle_command({'intent':'set_param'}) -> Hover (probed).
          Unreachable on the deployed route; the code fix is Block A's;
      (c) no clamp on PyFlyt (only APF separates there; no collision claim for that backend).
  - Ch6 demonstration: if PyFlyt is chosen for the visual, it flies without the clamp. No fix for
    the prompt cache is promised anywhere (author's decision).
  - Ch1 l.69 says the simulation runs "at 50 Hz"; PyFlyt's control rate is 48 Hz (4.6). True of
    the kinematic backend the results use; left for B13's read-through, not edited here.

Stopped here: Ingenieur Ch 4 drafted in full. No section waits on a measurement.

## Ingenieur Ch 4 review closed (Thu 24 Sep) -- issue 12 resolved
The review loop of .scratch/thesis-review/spec.md has run over Ingenieur Ch 4 (issue 12).
All 14 verified findings (V1-V14) were decided and applied (commits 0cd26b1, 8582f81, 90f3375,
fdf333d, 8f2b360, 7046bf2, 0696a08).
The PyFlyt 24 Hz tick finding was resolved by prose honesty in Section 4.6 (code unchanged, 10
physics steps / 41.67 ms per tick, 600 ticks = 25 s flight; transfer at 50 Hz noted as unestablished
pointing to sec:limitations). Chapter polish applied (\gls{udp}, 'Cross-backend verification' heading,
'demonstrate little about transfer', all five vehicles for N=5, docstring timing observations removed).
Review script tools/review/ingenieur_ch4.py at 0 FAIL, 5 WARN (all cross-chapter), 226 PASS; selftest
passes; clean build 0 errors, 59 pages. Issue 12 closed.

## Ingenieur Ch 5 review closed (Thu 24 Sep) -- issue 13 resolved
The review loop of .scratch/thesis-review/spec.md has run over Ingenieur Ch 5 (issue 13).
All 14 verified findings (V1-V14) were decided, verified, and applied to thesis/ingenieur/ch5_validation.tex:
- V1: energy-based keyword offset imprecision stated with counts of early detections (idle 6/78, earliest -234.7 ms; loaded 4/78, earliest -234.0 ms); algorithmic/quantisation/anchor error separated from board; both anchor definitions named ($|x| > 10^{-4}$ synthetic vs 20 ms frame at 5% peak RMS real); board reflex computation stated as 18 ms at p95.
- V2: llama-server HTTP polling interval (1 s) cited (\texttt{llamacpp}), median 601 ms noted as ~half period, p95 1,195 ms and max 1,505 ms quoted with 10 of 78 recoveries exceeding 1,000 ms; slot release time located as cause in 5.5.
- V3: McNemar pre-registered rule stated (exact binomial below 25 discordant pairs, Edwards' continuity correction \cite{edwards1948} from 25 up); both boundary pairs decided by chi-square form with exact binomial p = 0.0046. Added edwards1948 to references.bib.
- V4: golden-set grouping into 12 command patterns explicitly disclosed, with non-independence and narrower intervals/p-values acknowledged.
- V5: experiment's own reference-text condition (13 failures, 0 safe) quoted, comparing with audio (1-4 safe); clarified audio errors do not make failures less safe than the parser's own.
- V6: keyword criteria paired wherever either appears (2.33/h [0.06, 12.98] ambient FA in 5.1; 0.050 and 0.000 real-voice FR in 5.2); operating point on curve clarified.
- V7: dropped "declared before they were scored" for interval rule; point estimate exceeding budget (FA) vs lying within budget (FR) distinguished.
- V8: reproduction script experiment stages noted as not invoking runners, stating single-command rerun is not provided and listing per-experiment runners.
- V9: combined language-model row noted as having no counterpart in measured table and assuming cached prefix deployed parser does not use; lead-in notes reasons for two unjudged rows.
- V10: load reached reflex path through shared SoC resources noted, raising board share from 6 to 18 ms at p95; load clarified as LM stages only; golden-set max frame 74.2 ms quoted.
- V11: circle radius 5 m, line/wedge 2 m spacing specified; recovery operationalised as moment server reports slot idle; recogniser noted running on 4 unpinned threads.
- V12 & V13: added kramer1956 and cochran1950 to references.bib and cited in 5.3.
- V14: Master selection rule failure clause accurately stated as failing openly when no configuration satisfies both constraints.
Review script tools/review/ingenieur_ch5.py: 0 FAIL, 1 WARN (seeded rerun note), 266 PASS; selftest passes; clean XeLaTeX build (60 pages, 0 errors, 0 undefined citations/references). Issue 13 closed.

## Writing progress -- Ingenieur Ch 6 (B11) (Thu 24 Sep) -- DRAFTED, awaiting review
thesis/ingenieur/ch6_conclusion.tex, \label{chap:conclusion}, lead-in and all four sections drafted (390 lines, 0 \TODO{} left). Commits: bd2ba37 (sections 6.2-6.4 drafted, refined, and verified).
  lead-in -- maps the four sections against prd.md §3.1 and Chapter 1 contributions; establishes that Chapter 6 inherits every measured figure strictly from Chapter 5 (tab:requirements-summary) with no new measurement introduced.
  6.1 sec:demonstration-protocol -- sets the demonstration protocol before the defence; defines Part A (offline smoke test across recorded audio) and Part B (live tethered speech demonstration); references Table~\ref{tab:demo-script}; fixes four explicit success criteria for Part A (zero collisions under clamp, formation accuracy 1.000, 78/78 in-flight decodes preempted, zero late dispatches) and live interactive tethered verification for Part B.
  6.2 sec:limitations -- candid accounting across simulation, safety, acoustic robustness, and requirements:
      - Simulation scope: PyFlyt rigid-body vs kinematic backend; PyFlyt advances 10 physics steps at 240 Hz per control tick (41.67 ms), yielding an effective 24 Hz control rate rather than nominal 48/50 Hz; evaluated across 600 ticks (25 s flight); exercised only by smoke tests on seed 42 for 12 s checking terminal position within 0.5 m, without collision logging or separation clamp.
      - Separation clamp: intervened 432 times across 144 of the 150 trials at 0.800 m (collision threshold 0.50 m); commanded velocity ceiling 2.0 m/s vs backend ceiling 3.0 m/s; clamp is an external geometric override in the kinematic simulator, not a distributed collision avoidance algorithm.
      - Acoustic degradation & safety: safe-failure rate is 0.032 clean (2 of 62 failures) and remains between 0.014 and 0.039 across noise levels down to 5 dB, missing the >= 0.70 target; speech recognition errors distort parameters into executable commands rather than unknown; on the reference-text golden set, the parser yields 13 failures with zero safe failures (showing failure pattern originates in fine-tuning, not acoustic noise).
      - Raw-intent state machine defect: FlightStateMachine.handle_command evaluates transitions against raw rather than validated intent, replacing invalid set_param during landing with hover.
      - Criteria summary: inherits Table~\ref{tab:requirements-summary} strictly: 7 met, 5 missed with confirmed causes (reflex latency, e2e latency, preemption recovery, clean CRR, noise CRR), 2 not demonstrated (KWS FA, KWS FR), 2 not yet run (offline STT, offline operation), 1 planned for defence (live demo).
  6.3 sec:future-work -- three prioritized directions with concrete remedies:
      1. Dynamic artificial potential fields / real-time distributed collision avoidance (\cite{koren1991}) to replace static geometric clamp.
      2. Prompt prefix caching in llama.cpp to drop prefill latency from 751 ms to within 250 ms allowance.
      3. Socket-level cancellation / signal handling in llama-server to replace 1 s HTTP polling and achieve client's 6 ms cancellation latency; acoustic front-end retraining and multi-microphone beamforming.
  6.4 sec:conclusion -- direct, unhedged answers to RQ2 and RQ3; RQ1 cited from Mémoire de Master in one sentence without reopening evidence:
      - RQ2: offline pipeline does not meet 2,500 ms p95 budget (3,122 ms measured, missed by 622 ms / 25%); reflex path misses 150 ms (545/547 ms, located in spotter decision delay 540 ms + 80 ms quantisation); preemption recovery misses 300 ms (1,195 ms). Stage attribution: 3 meet (VAD wait 480 ms, decode 915 ms, validate <1 ms), 2 miss (STT 1,449 ms, prefill 751 ms).
      - RQ3: acoustic degradation falls from 0.690 clean to 0.485 at 5 dB (WER 23.3% to 36.0%); clean and noise CRR miss requirements; loss located in speech stage (costs 0.245 to 0.450 accuracy); safe-failure rate 0.032 to 0.039 fails >= 0.70; formation accuracy 1.000 (>= 0.85 requirement met); locked collision phrasing: zero collisions observed, backed by hard geometric separation clamp; preemption: 78 of 78 cancelled, 0 late dispatches, 0 cross-triggers.
      - Register strictly unhedged (no may/might/could/perhaps/possibly/likely/suggests/appears/seems).

Verification and tooling:
  - Clean XeLaTeX build (rm -rf thesis/build/ingenieur && cd thesis && latexmk main_ingenieur.tex): 65 pages, 0 errors (^!), 0 undefined citations, 0 undefined references, 0 dropped floats.
  - Review script tools/review/ingenieur_ch6.py: 0 FAIL, 0 WARN, 81 PASS; 0 untraced numbers.
  - tools/review/selftest.py: passes all checks including planted mutations for ingenieur_ch6 (latency claim and conclusion hedge).
  - Issue 14 scaffolded (.scratch/thesis-review/issues/14-ingenieur-ch6.md, commit c2e60e7); Issue 10 updated.

Stopped here: Ingenieur Ch 6 drafted in full; all six chapters of both theses are now drafted. Next: Chapter 6 review loop (Issue 14).


## Writing progress -- Ingenieur Ch 2 (Thu 24 Sep) -- DRAFTED, awaiting the author's read
thesis/ingenieur/ch2_state_of_the_art.tex, \label{chap:state-of-the-art}, lead-in + five sections
(voice-UAV survey with tab:voice-uav-survey; Lim positioning with tab:lim-positioning; swarm
control; offline speech components; gap). Commit 7ad9bc4. Script 0 FAIL / 3 WARN (justified),
clean build 0 errors. Every Ingenieur chapter now has prose.
- The scaffold's "Table 21 in Ch5" does not exist and is not added: the Lim comparison is by
  design point, in Ch2 only.
- Gap: (i) spoken swarm commands with deterministic checking -> conceded to CommandSwarm;
  (ii) planner over control-rate safety layer -> conceded to SkySim; (iii) preemption under a
  derived membership rule -> claimed against RelayS2S / dual-attention / MIRA; (iv) offline on one
  SBC -> the setting, not a contribution.
- OPEN for the author: the MIRA contrast rests on its abstract; read the paper before the defence.
- Build note: two sessions building thesis/build/ingenieur at once corrupt the .aux. Build to a
  private -outdir when another session is active.
Issue 07 -> ready-for-agent.

## Ingenieur Ch 6 review closed (Thu 24 Sep) -- issue 14 resolved
The review loop of .scratch/thesis-review/spec.md has run over Ingenieur Ch 6 (issue 14).
All 5 verified findings (MINOR-1, NIT-1 to NIT-4) were decided, verified, and applied to thesis/ingenieur/ch6_conclusion.tex:
- MINOR-1 (D8g): l.138-141: split 58-word run-on sentence joining controller input mapping with state feedback reporting into two clear sentences.
- NIT-1 (D8d): l.162: corrected American spelling `idealized kinematics` to British `idealised kinematics`.
- NIT-2 (D8d): l.196: corrected American spelling `formation maneuvers` to British `formation manoeuvres`.
- NIT-3 (D8d): l.294: corrected American spelling `attitude stabilization` to British `attitude stabilisation`.
- NIT-4 (D8d): l.301: corrected American spelling `optimized acoustic model` to British `optimised acoustic model`.
Review script tools/review/ingenieur_ch6.py: 0 FAIL, 0 WARN, 81 PASS; selftest passes; clean XeLaTeX build from scratch (0 errors, 0 undefined citations/references, 0 dropped floats). Issue 14 closed.


## Ingenieur whole-document pass closed (Thu 24 Sep, ~20:30) -- issue 10
Abstracts EN/FR/AR written (ee80c2b, f9cbb67); Ch2 scoped citation check applied (feb7371, issue 07
closed); whole-document pass applied (87ca9f1 thesis, 1395103 scripts). One BLOCKER found and fixed:
Ch6 said collisions were counted at 0.50 m; the code and Ch4 say 0.35 m, and the Ch6 script had
checked against the same wrong literal -- it now reads swarm/control.py. Every Ingenieur chapter
script 0 FAIL; clean build 78 pages, 0 errors.
LEFT FOR THE AUTHOR BEFORE THE DEPOT: jury names ("Name]" on both title pages); read the Arabic
abstract; print / DVDs.

## Demonstration chain built (Thu 24 Sep, ~22:20) -- cba9c1e; hardware run NOT yet made
The three Ch6 prerequisites Ch4 records as not built now exist, as new files only (no measured
module edited; the deposited Ch4/Ch6 text still says "not built" and is left as deposited):
runtime/audio.py (live capture, golden-set chain), runtime/main.py (Pi entry point),
swarm/link.py (FSM -> controller mapping + vehicle feedback + raw-intent guard),
demo/workstation.py (consumer, Part A numpy + clamp / Part B PyFlyt, 3D display, [r] reset),
demo/rehearse.py (publishes tab:demo-script in place of the Pi). Runs log to demo_runs/ (ignored).
Verified on the workstation only: 853 fast tests; loopback rehearsals of Part A (all 8 steps end
in their State after, step-4 line discarded behind the reflex hold) and Part B; runtime/main.py
replaying audio through real whisper/llama/spotter/VAD: take off -> circle -> hold -> abort.
Part B rehearsal (no criterion, recorded not tuned): circle settles at r ~4.73 m, line spacing ~2.8 m.
OPEN FOR THE AUTHOR:
- RISK, steps 1 and 7: the parser maps "take off to 5 meters" (whisper's form under DOMAIN_PROMPT,
  all three piper voices) to altitude z=5 -> illegal in LANDED -> no motion. Rehearse step 1 by voice
  on the Pi before the defence; the protocol and parser are fixed, so do not reword on the day.
- Hardware steps (Pi, BOYA, Wi-Fi link, recording) are the author's; commands in the session.
- Operating rules: restart Pi and workstation together (bus seq restarts at 0); speak only after
  the workstation prints "listening".

## First live hardware run (Fri 25 Sep, 11:00-12:13) -- Part A voice tests and full script PASS, unrecorded
Pi 5 + BOYA (USB adapter hw:2,0) -> Wi-Fi -> workstation demo/workstation.py (numpy + clamp).
Logs: demo_runs/pi-20260925-*.jsonl (copied from the Pi) and demo_runs/20260925-*-numpy/ (ignored).
- Pi setup gap: whisper must be selected with `export WHISPER_CPP_DIR=~/whisper.cpp-52a939a`
  (~/whisper.cpp is a newer build with only tiny.en-q5_1; first run crashed branch-b on it).
- Mic hum: Pi-hosted floor -38..-42 dBFS raw, mains share 0.75-0.93 (50/100/200 Hz); same mic on
  the laptop on battery -60.4 dBFS, share 0.00 (S1 was -69.6; room ~9 dB louder today). Official
  27 W PSU in use. Finger on a Pi port shell -> -57.0 dBFS, share 0.28: floating ground (charger
  leakage), not the mic. Author has no power bank / earthed HDMI / USB isolator. Left as is: ~97%
  of that energy is below 300 Hz, and it produced no false triggers in ~70 s of silence and no
  misparse attributable to it. Capture chain unchanged (no high-pass).
- Step-1 risk CONFIRMED live: whisper wrote "take off to 5 meters" -> altitude -> not dispatched in
  LANDED. "take off and climb to five metres" -> takeoff z 5 every time (4/4). Parser-side check of
  whisper-style variants: altitude for "take off to 5 meters", "takeoff to 5 meters", "... altitude";
  takeoff for "Take off to 5 meters." and "take off to five meters". Whether the recorded run keeps
  the thesis wording (step 1 refused on camera) or uses the substitute (same parse target, stated at
  the defence) is the AUTHOR'S DECISION, still open.
- Voice tests 3a-3g all pass; step-3d preemption live: hold 1.6 s after endpoint, line decode
  stopped (seq 3/4), nothing published. Parse path ~2.2 s endpoint -> publish; reflex 2.2-2.4 s
  ahead of the parse copy. Full tab:demo-script (substitute wording in 1/7): all 8 steps end in
  their State after. One miss: step 7 "swarm abort" was NOT caught by the spotter (no REFLEX line);
  the parse path delivered the abort 1.8 s after endpoint. Spotter scores are not logged, so the
  miss cannot be diagnosed from the log; the Pi JSON log also lacks transcripts (runtime/main.py
  change offered, not made).
- Ctrl-C in the workstation was swallowed by Tk mid-redraw -> fixed in 0d39a7b.
- Still to do: Part B by voice (optional), recorded run on the Pi hotspot (step 7 of the plan).
- Spotter check (12:20, landed): 10/10 "swarm abort", 10/10 "swarm hold" caught, each 0.2-0.6 s
  before the endpoint; the step-7 miss was a one-off (spoken fast, before FLYING).
- FINDING, not in the thesis: the parse path's copy of a reflex phrase is numbered after the reflex,
  so the ordering rule lets it through; "swarm hold" copies were hover x6, unknown x1, abort x1,
  wedge x2. Mitigated for the demo only by ReflexGate in runtime/main.py (7eec6fd): no parse for
  an utterance a reflex fired during or after, before its parse began. Present it at the defence
  as a mitigation added after live testing. Not yet verified live on the Pi (Pi unreachable at
  commit time): copy runtime/main.py + runtime/test_main.py, then 10x "swarm hold" while FLYING.

## Master RESTRUCTURE (Fri 25 Sep, afternoon) -- Background chapter written; SoA rebuild pending
Trigger: supervisor meeting with Prof. Khaldi, 25 Sep. Three notes on the Master: (1) the state of
the art is the chapter that counts and must compare the previous studies TO EACH OTHER (comparison
tables + critical comparison, as in Bensalah 2023 SS3.3.4.1 and Boufafa 2026 SS5.2.4/SS6.5 -- the
latter co-supervised by Khaldi, so it is the template of record); (2) structure must follow the ESI
skeleton: Part I Background, Part II State of the art; (3) a Background chapter must precede the
state of the art. Deposit extended: author can deliver in two days (Sun 27 Sep).
Decision: experimental chapters STAY in the Master. Both reference Masters are literature-only
(their experiments live in the PFE), but moving Method/Results across would undo Table 3, take RQ1
out of the document that states it, and does not fit two days. Front of the document adopts the
skeleton; the spine is untouched:
  1 Introduction | Part I: 2 Background | Part II: 3 State of the art |
  Part III Contribution: 4 Method, 5 Results, 6 Discussion | 7 Conclusion (outside the parts).
Done today:
- prd.md SS3.1 rewritten (seven chapters, three parts, rationale); Table 2 chapter count; Table 3
  renumbered (+ a Background-foundations ownership row: Master owns LM/LoRA/quantisation/GBNF/SLU/
  metrics foundations; the Ingenieur's background, when written, owns speech pipeline/UAV/swarm/RT).
- thesis/master/ch2_background.tex NEW (~4.4k words, 8 sections, one table, two equations). About
  half is moved text: the Q8_0/Q4_K_M construction and the GBNF mechanism from the old Ch2, the
  LoRA/QLoRA description from the old Ch3 "Adaptation method"; each origin now points at the
  Background section instead. Two visible markers for the author: \TODO (Vaswani 2017 not in
  references.bib -- add + verify, then cite in sec:bg-lm) and \CHECK (Raspberry Pi 5 SoC/memory
  designations -- verify against the product brief, add a bib entry).
- ch2_related_work.tex -> git mv -> ch3_state_of_the_art.tex; \chapter{State of the art};
  label chap:related-work -> chap:state-of-the-art everywhere. CONTENT NOT YET REBUILT (Day 2).
- main_master.tex: \part{Background} / \part{State of the art} / \part{Contribution}; file names
  keep their historical numbers (ch3_method.tex is Chapter 4, etc.), never hardcode a number.
- ch1 "Structure of this document" rewritten for the three parts. ch6 comment numbers fixed.
- thesis-writing SKILL.md blueprint rewritten to match prd.md SS3.1.
- Clean build: 0 errors, 0 undefined refs/cites, 0 overfull, 75 pages (was 62). TOC now spills to
  a second page; the \small + chapter-gap patch in main_master.tex was tuned for one page and can be
  dropped in the layout pass.
Day 2 (SoA rebuild), in order: one comparison table per section from the 19 already-cited sources
(columns: study, models/size range, hardware, runtime or method, metrics reported, downstream task
scored, grammar used); a critical-comparison paragraph under each table; \section{Positioning} ->
\section{Research gaps} with G1-G3 mapped to C1-C3 (the Synthesis/Gap/Delta prose becomes that
section); at most 3-5 author-verified new bib entries. Other constrained-decoding tools may appear
as REVIEWED rows, never as used (SKILL.md exception recorded). Then tools/review/master_ch2.py
must be re-pointed at the new chapter/index (see below), and the whole-document read-through.

## Master state of the art REBUILT (Fri 25 Sep, evening) -- comparison tables + research gaps; Day 2 item done early
thesis/master/ch3_state_of_the_art.tex rewritten in the ESI form Khaldi asked for, from the 19
sources already cited (no new bib entries; closed set kept):
- Each of the four sections opens with a taxonomy of its studies (kinds), carries ONE comparison
  table (tab:soa-edge, tab:soa-quantisation, tab:soa-constrained, tab:soa-slu; every table ends in a
  "This work" row, dashes for properties the review did not establish -- same convention as the
  Ingenieur's tab:voice-uav-survey), and closes with a \paragraph{Critical comparison.} that walks
  the table's axes and compares the studies TO EACH OTHER (Bensalah SS3.3.4.1 pattern).
- \section{Positioning} -> \section{Research gaps}: Synthesis paragraph kept, then Gap G1
  (structural validity after fine-tuning -> C1), G2 (the command corpus -> C2), G3 (deployment cost
  on a task at sub-billion scale -> C3). Studies are compared to this thesis only there.
- Section labels renamed sec:soa-*; Method's three refs repointed. Old prose kept where it held.
- Table cells state only what the chapter prose or .scratch/thesis-bibliography/*-candidates.md
  establish about each source. Tables 3.1 (2 studies) and 3.4 (2 works) are thin: the candidate
  files hold page-verified additions the author can make in an hour each -- XGrammar, PICARD,
  Beurer-Kellner 2024 (constrained decoding); Jin 2024, Li 2024, Dettmers & Zettlemoyer 2023
  (quantisation evaluations); ATIS, SNIPS, SLURP (SLU corpora). Each needs the author to open the
  primary page and add a verified entry; then one table row + one sentence each.
- tools/review/master_ch2.py shape checks rewritten: last section "Research gaps"; Synthesis +
  Gap G1..G3 paragraphs; each sec:soa-* has a table, a Critical comparison and a This-work row;
  each gap paragraph names its contribution. 0 FAIL, 2 WARN (paper numbers on the citation
  worklist; the pre-existing Ch1/Ch2 coherence note).
- Clean build: 0 errors, 0 undefined, 0 Float too large, 0 overfull, 79 pages. Tables 3.2 and 3.3
  float to their own pages (white space on 29 and 31): layout pass (B13) territory, not fixed now.
Remaining for the author before deposit: the two markers in Background (Vaswani 2017; Pi 5 brief),
the optional table rows above, jury names on the title page, and the final layout pass.

## Master Background REVIEW closed (Fri 25 Sep, evening) -- issue 15
Loop as for issues 01-14: new script tools/review/master_bg.py (registered in selftest.py with
three planted errors; check_tex.py taught to skip display math), citation + argument + verifier.
No BLOCKER; 5 MAJOR all confirmed and applied (SwiGLU description was wrong; a protocol decision
had leaked in; edwards1948 bib title wrong since 4445be5; one model card cited for four models;
AWQ cited for a CPU claim it makes for a GPU); 26 minors/nits applied, 2 rejected by the verifier.
Script 0 FAIL after fixes; clean build 0/0/0/0. Outstanding for the author: add + verify two bib
entries (Raspberry Pi 5 product brief RP-008348-DS-6 -> resolves the \CHECK and cites the throttle
flag; Vaswani et al. 2017 -> resolves the \TODO). Details: .scratch/thesis-review/issues/15-master-bg.md.

## Master State of the art REVIEW closed (Fri 25 Sep, night) -- issue 16
Loop as for issues 01-15 on the rebuilt Chapter 3 (7830694): script master_ch2.py (re-pointed
in 4bb8138/7830694; stale agent note rewritten; two paper-number anchors added), citation +
argument + verifier. Citations 53/57 SUPPORTS, 4 PARTIAL, 0 DOES NOT SUPPORT; all 19 paper
numbers found; bib metadata all agree. 3 BLOCKER (G3's "8 B and above" refuted by the chapter's
own table -- issue 02 #11 crept back; Kurtic's 1.5 B model is a DeepSeek-R1 Qwen distillation,
not Llama-3.1; sbc2025 ran every model at Q4_K_M, not "formats as distributed"), 8 MAJOR + 1 NEW
(positioning inside two critical comparisons against prd §3.1 "to this thesis only in the gaps";
This-work rows implying accuracy and timing on the Pi at both levels and an fp16 reference in
llama.cpp; F1 promised for the ablation that Table 19 does not report; "no existing corpus" scoped
to the world; uncited "no SBC serves 8 B"; Park misread twice; a false citation-graph claim). All
confirmed by the verifier and applied with its anchor-safe wording, plus the factual MINORs (27
edits), then the style items in a second pass (one name for the throughput constraint, one metric
list per This-work row with safe-failure added to Ch1's C3, no sentence over 40 words, shorter Gap
lead-ins, two figurative phrases removed). Later the same night: Table 3.4 gained SLURP and Snips
rows (primary pages verified by an agent at the author's delegation; ATIS rejected -- no intents or
slots in the 1990 paper), and Method names the repository (private, to be opened). Examiner gap still open: why Table 3.1 holds one SBC benchmark
(a scoping sentence, or an author-verified second row). Script 0 FAIL, 2 WARN justified; self-test
PASSED; clean build 0/0/0/0, 79 pages. Details: .scratch/thesis-review/issues/16-master-soa.md.

## Master WHOLE-DOCUMENT pass repeated (Fri 25 Sep, late night) -- issue 17
Template B on the seven-chapter Master (issue 08 had run it on the six-chapter one). Reviewer +
verifier. PASS on the golden thread (RQ1/C1-C3 -> G1-G3 -> Ch4 -> Ch5 -> Ch6 -> Ch7), headline
numbers identical everywhere, three abstracts agree, write-once against the finished Ingénieur,
scope from Ch1 alone, acronyms, bibliography. 2 MAJOR (Background defined the safe-failure rate over
in-domain errors while the definition of record pools all splits; the contents entry for the
Bibliography pointed at the wrong page and anchor -- same defect fixed in the Ingénieur main file),
4 MINOR, 2 NIT applied; 1 MINOR refuted (issue 15 had ruled). Both documents build clean: Master 80
pages, Ingénieur 78. Master is review-complete. Remaining for the author: jury names; the layout
pass (B13); optional Table 3.1 scoping sentence; converter commit if the logs have it.
Details: .scratch/thesis-review/issues/17-master-whole.md.

## Master LAYOUT pass (B13, Master half; Fri 25 Sep, late night) -- DONE
Survey by per-page text-line counts plus renders. Four defects, four causes, all fixed at the
cause: (1) the contents' \small + chapter-gap patch, tuned to fit six chapters on one page, now
gave two pages of shrunken entries -> dropped, contents at body size on two pages; (2) the
keep-section-whole rule (preamble, 23 Sep) left half-empty pages before Background §2.2 and §2.5
(sections of nearly a page each) and its page break flushed Tables 3.2 and 3.3 onto float pages ->
the rule's own \noautobreak override before those four sections, with a comment each; (3) class
float defaults (\topfraction 0.7, \floatpagefraction 0.5) put any table over 70% of the text height
alone on a float page -> preamble now \topfraction 0.9, \floatpagefraction 0.88 (just under, since
the output routine tries a float page before a top float), \textfraction 0.08, \bottomfraction 0.5;
Tables 3.2, 3.3, 3.4 and 4.1 now sit at the top of a page with text beneath; (4) the hand-placed
\clearpage before Method §4.5 (left 40% of a page blank) was no longer needed -> removed; the two
other hand-placed breaks (Discussion §6.3.2, Conclusion §7.3) cost nothing and stay. Master 80 -> 78
pages, still 0/0/0/0, all scripts unchanged. The shared preamble change also rebuilt the Ingénieur
clean at 77 pages (was 78); its own layout pass is not done (sparse pages at 22-23, 33, 43, 48
noted, not examined). Remaining Master layout: nothing found; part pages and chapter ends are by
design.

## Master parts: three -> two (Sat 26 Sep, morning)
Prof. Khaldi asked for the Background and the State of the art to share one part. Master now:
Introduction | Part I "Background and state of the art" (Ch2, Ch3) | Part II "Contribution" (Ch4-6)
| Conclusion. Chapter numbers, files and contents unchanged. Updated: main_master.tex, Ch1's
structure paragraph, prd.md §3.1 and Table 2 (dated rationale), SKILL.md's Master blueprint, a
lib.py comment, and the saved Ingénieur prompt (.scratch/sprint-pfe/ingenieur-restructure-prompt.md),
which now targets the same two-part shape. Build clean, 79 pages (the author's c4a11f1 hard page
breaks added one page back after the layout pass; its sparse pages -- 14, 25, 35, 58 -- are the
author's choice and were not touched). The Ingénieur restructure is to run in a new session from
that prompt.

## Master captions shortened (Sat 26 Sep)
Author's request. Generated tables: qualifications moved from the caption to a note under the rule
in eval/tables.py and eval/exp0.py, outputs regenerated (no cell changed; test_tables.py passes).
Hand-written: Pareto figure legend only (interpretation is in the prose), the dash convention stated
once in the state-of-the-art introduction, dataset caption trimmed. Longest now: figure 78 words;
every table at or under 43. Build 0/0/0/0, 79 pages; scripts 0 FAIL.

## Ingénieur RESTRUCTURE (Sat 26 Sep) -- seven chapters in two parts; Background written; SoA rebuilt; issues 18-19 closed
Author's request, mirroring the Master (Khaldi's notes of 25-26 Sep). Structure confirmed with the
author: 1 Introduction | Part I "Background and state of the art": 2 Background (NEW), 3 State of
the art (rebuilt) | Part II "Contribution" (not the template's "Design & Implementation"): 4
Architecture, 5 Implementation, 6 Validation | 7 Demonstration, limitations and conclusion (outside).
No Project Management chapter (supervisor did not ask). Files keep historical numbers
(ch3_architecture.tex is Chapter 4); prose uses \ref only.
- prd.md §3.1 (Ingénieur, dated rationale), Table 2 chapter count, Table 3 Ingénieur chapter numbers
  + a new foundations row; SKILL.md Ingénieur blueprint rewritten. (prd untracked by design.)
- b8ee6db restructure + Background (speech pipelines; multirotors, PID, double integrator; swarm
  control, slot assignment, potential fields; real-time/latency budgets; the Pi as a shared host;
  FSMs and command buses; the Master's foundations one sentence each in sec:bg-master).
- c3fe8d5 SoA rebuilt: four themes with one table each (tab:voice-uav-survey, tab:soa-dual-path NEW,
  tab:soa-swarm, tab:soa-speech) + Critical comparison; Research gaps = Synthesis, Conceded prior art
  (CommandSwarm, SkySim, MIRA), G1 fast-path membership -> C4 clause 2; G2 a budgeted stop -> C4 clause
  1 via dual-path + latency budget; G3 one-board execution -> core allocation; Lim et al. baseline and
  tab:lim-positioning moved into the gaps. Component justification moved to Ch4 sec:component-choices.
- 3e109c1 tools/review re-pointed (INGENIEUR list, indices), ingenieur_ch2 rewritten for the new shape,
  ingenieur_bg.py NEW; selftest +3 planted errors, PASSED.
- Issue 18 (6d40ad4): 1 BLOCKER -- squared-distance assignment does NOT stop paths crossing (it gives a
  minimum-separation property under synchronised straight-line motion, CAPT); fixed in Ch2, Ch1
  ("crossing paths by construction") and Ch5; 6 MAJOR (direct pipeline + endpointing wait; WER owned
  by the Master; percentiles owned here; flight-stack cites; Reynolds' central force; Ch6's "end of
  speech" for the keyword end), 23 MINOR. Issue 19 (84e04be, 8386de4): 7 BLOCKER, all wrong facts
  about sources (MIRA reports a 466 ms stop; Silva/Burke out-of-band kill; Torkamani's edge tier runs
  offline; CommandSwarm's classifier precedes generation and it is not the latest speech system; the
  swarm This-work row claimed 50 Hz + clamp on the physics backend), 6 MAJOR, 24 MINOR; section 1
  retitled "Language interfaces to robots". G2 now promises measurement, never that 150 ms is met.
- Build: 0 errors, 0 undefined, 0 Float too large, 0 overfull; 91 pages (was 77). A keep-section-whole
  oscillation on Ch5 "Command bus" (p61 <-> p62, latexmk never converged) is held by \noautobreak --
  revisit in the layout pass. No hardcoded Ingénieur chapter number found in the Master.
OPEN FOR THE AUTHOR:
- [RESOLVED Sat 26 Sep] Nine \TODO sources in the Background added and verified with publisher DOIs/URLs (mahony2012, px4userguide, astrom2008, turpin2014, khatib1986, buttazzo2011, love2010, harel1987, eugster2003). All bib house rules met; ingenieur_bg.py 0 FAIL.
- One sentence on how the SoA studies were selected (scopes every silence claim; issue 19 m15).
- Examiner question with no answer anywhere: why processor affinity alone, not a real-time
  scheduling policy or core isolation.
- Ch5's "not built" statements about the demo chain (known since 24 Sep, left as deposited).

## Ingénieur WHOLE-DOCUMENT pass repeated (Sat 26 Sep) -- issue 20 closed
Template B on the seven-chapter Ingénieur (issue 10 had run it on the six-chapter one). Reviewer +
verifier. PASS on the golden thread (RQ2, RQ3, C4 -> G1-G3 -> Ch4 -> Ch5 -> Ch6 -> Ch7), headline
numbers identical everywhere, three abstracts agree, scope from Ch1 alone, 22 acronym keys (GGML
added via \glsadd{ggml}), 46 cited = 46 printed.
- 1 MAJOR (Gap G2 latency claim vs conceded MIRA: rephrased "held to" to "specified and measured against";
  MIRA 466 ms median compared directly with 965 ms keyword onset median in Ch7, clarifying the reflex adds
  a derived membership rule and localized diagnosis rather than raw speed over MIRA).
- 10 MINOR on Ingénieur: component duplication replaced with Section 3.4 cross-references in Ch4; abstracts
  refined across EN, FR, AR for rejection (no-op on ground, hold in flight) and latency attribution (decision
  delay + quantisation + anchor error); consumer unit test cited for ordering rule in Ch6 and Table 6.3;
  allowances phrasing corrected in Ch7; RQ3 synthesis sentence added to Ch3; Master canonical comparison
  cross-referenced in Ch6; controller terms convergence attribution corrected in Ch7; collision avoidance
  future work aligned with soft-mechanism arguments; 10 dB failure breakdown completed to 82.
- 6 NITs applied (emph on Mémoire de Master, gap closer ordering, an SLM, end of speech, deployment constraints,
  explicit out-of-scope sentence in Ch1).
- 1 MINOR on Master deferred (speech pipeline text, Master review completed in Issue 17).
- Background \TODOs: all nine placeholders resolved with publisher-verified primary citations in references.bib
  (mahony2012, px4userguide, astrom2008, turpin2014, khatib1986, buttazzo2011, love2010, harel1987, eugster2003).
Clean build: 0 errors, 0 undefined citations or references, 0 overfull, 92 pages.

## Ingénieur LAYOUT pass (B13, Ingénieur half; Sat 26 Sep) -- DONE
Per-page text-line survey and visual check on main_ingenieur.pdf. Three causes of whitespace resolved:
1. Chapter 2 cascade: sections 2.5, 2.6, and 2.7 were each moved to new pages by the keep-section-whole
   rule, leaving three consecutive half-empty pages (pp. 30-32). Applying \noautobreak before Section 2.5,
   2.6, and 2.7 allows natural flow, consolidating Chapter 2 from 9 sparse pages to 8 balanced pages.
2. Chapter 1 hand-placed \clearpage before Section 1.3 (The safety problem) removed: Section 1.3 now
   flows directly onto page 17, eliminating the ~40% white space and balancing the chapter.
3. Chapter 7 hand-placed \clearpage before Section 7.4 (Conclusion) removed: Conclusion now starts
   directly below Future Work, eliminating the half-empty page 84.
4. Ch5 Command bus \noautobreak confirmed and retained to stabilize section start at the top of the page.
Ingénieur build: 92 -> 90 pages total (PDF p. 90, arabic 89), 0 errors, 0 undefined citations or references,
0 overfull boxes. All chapter scripts pass with 0 FAIL.
REMAINING DEPOSIT ITEMS FOR AUTHOR:
- [RESOLVED Sat 26 Sep] One sentence on how the SoA studies were selected added to Ch3 introduction (searches of IEEE Xplore, ACM DL, arXiv 2017-2026; empirical latency/check/edge deployment inclusion criteria; issue 19 m15 closed).
- Examiner question with no answer anywhere: why processor affinity alone, not a real-time
  scheduling policy or core isolation (oral defense answer prepared: userspace feasibility, memory/cache interference mechanism, Exp-2 empirical evidence).
- Ch5's "not built" statements about the demo chain (known since 24 Sep, left as deposited).
