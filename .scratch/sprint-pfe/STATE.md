# STATE
Session: 04 (Fri 18 -> Sat 19 Sep) -- COMPRESSED. Depot moved to **Thu 24 Sep**.
Last updated: 2026-09-19T02:05:00+01:00

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
Gate 4 fsm           : PENDING. swarm/ controller, both backends, Exp-4, and now
                       runtime/bus.py + the full pipeline wiring are DONE (see below);
                       what remains for Gate 4 is Table 9 cell-coverage proof (A3, not run
                       this session -- rule 10, one task).
Gate 5 dataset frozen: GREEN (tag dataset-v1.0, Sep 18). 200/200 masters + 200 resampled;
                       annot_pass1.jsonl sealed 23:41 under SHA-256 f1a1fe6c, verified intact.
D1 Environment Gate  : GREEN
FR-1 grammar         : GREEN (5,191 labels, 0 rejected)

Test suite: 650 passed, 0 skipped (was 614 passed, 3 skipped before this session's
runtime/ work; the 3 previously-skipped are not these -- see below).

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
