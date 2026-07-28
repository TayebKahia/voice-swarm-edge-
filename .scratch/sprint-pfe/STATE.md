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

## Gates
Gate 1 schema        : GREEN (pytest schema/ -> 83 passed, tag schema-v1.1)
Gate 2 leakage       : GREEN (check_leakage.py --strict -> exit 0, Sep 14; family, surface-form,
                       eval-independence, wake-corpus and noise-partition isolation all clean)
Gate 3 parity        : PENDING. HF side dumps on Kaggle (notebook cell); llama.cpp side
                       local. llama.cpp NOW BUILT on the workstation -- see below.
Gate 4 fsm           : PENDING (Session 08). swarm/ controller, both backends and Exp-4
                       are DONE; what remains for Gate 4 is Table 9 cell coverage + runtime/bus.py.
Gate 5 dataset frozen: GREEN (tag dataset-v1.0, Sep 18). 200/200 masters + 200 resampled;
                       annot_pass1.jsonl sealed 23:41 under SHA-256 f1a1fe6c, verified intact.
D1 Environment Gate  : GREEN
FR-1 grammar         : GREEN (5,191 labels, 0 rejected)

Test suite: 584 passed (was 451 at the end of Session 03).

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
prd.md + docs/project/PRD.tex : annotation interval 10 -> 6 days (SS9.3, Limitations, R-9, Table 25).

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
   (recording slipped to Sep 17-18; depot is Mon 21 Sep), and at 2 days an agreement percentage
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
