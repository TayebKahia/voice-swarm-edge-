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
Gate 3 parity        : PENDING. HF side dumps on Kaggle (notebook cell); llama.cpp side
                       local. llama.cpp NOW BUILT on the workstation -- see below.
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
