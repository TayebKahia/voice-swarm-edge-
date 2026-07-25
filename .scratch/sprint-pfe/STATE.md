# STATE
Session: 03 (Mon 14 Sep, PRD D4 + D5a)
Last updated: 2026-09-14T23:15:00+01:00

## Gates
Gate 1 schema        : GREEN (pytest schema/ -> 83 passed, tag schema-v1.1)
Gate 2 leakage       : GREEN (check_leakage.py --strict -> exit 0, Sep 14; family, surface-form,
                       eval-independence, wake-corpus and noise-partition isolation all clean)
Gate 3 parity        : PENDING (Session 05B)
Gate 4 fsm           : PENDING (Session 08)
Gate 5 dataset frozen: GREEN (tag dataset-v1.0, Sep 18). 200/200 masters + 200 resampled;
                       annot_pass1.jsonl sealed 23:41 under SHA-256 f1a1fe6c, verified intact.
D1 Environment Gate  : GREEN
FR-1 grammar         : GREEN (5,191 labels, 0 rejected)

Test suite: 420 passed (was 346; +74 this session).

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
2. Autorisation de soutenance: requested Sep 6, still pending (Issue 24). **Depot is Mon 21 Sep --
   this is now the project's top risk.**
3. `llama-gbnf-validator` still not built; needed before Session 05B (Gate 3).

## Next session starts with
Session 04 Task 2 (`eval/norm.py`) -- and it MUST import `data/numwords.py` rather than define a
second digit mapping (SS2.7 defines WER against that mapping; ADR-0004 D6).
Overnight tonight -- Pi: Exp-0, the 300 clips in `data/commonvoice/clips/` through `tiny.en`.
For Exp-3 later: `python data/mix_noise.py --input data/audio/s1_16k --output data/audio/mixed
--sources dregon --partition eval`  (note: s1_16k, the normalised corpus, not the masters).
Do NOT re-run Gate 1 or Gate 2.
