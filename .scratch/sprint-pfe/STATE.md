# STATE
Session: 02B (Sun 13 Sep, PRD D3)
Last updated: 2026-09-13T22:40:00+01:00

## Gates
Gate 1 schema        : GREEN (pytest schema/ -> 83 passed, tag schema-v1.1)
Gate 2 leakage       : GREEN (check_leakage.py --strict -> exit 0, Sep 13; family, surface-form, eval-independence and noise-partition isolation all clean)
Gate 3 parity        : PENDING (Session 05B)
Gate 4 fsm           : PENDING (Session 08; Table 9 legality verified in swarm/test_fsm.py)
Gate 5 dataset frozen: PENDING (Session 03)
D1 Environment Gate  : GREEN (requirements.txt pinned, environment.yml exported)
FR-1 grammar         : GREEN (5,191 labels across six files, 0 rejected)

## Artefacts
schema/                      : FROZEN (cmd.gbnf, schema.py, validate.py, canon.py, logger.py + tests). NOT touched in 02B.
swarm/                       : fsm.py, test_fsm.py (19 tests)
docs/adr/                    : 0001..0003 (02A) + 0004 augmentation substitution & noise partitioning (02B, 7 decisions)

data/raw_pairs.jsonl         : 2,421 rows (1,941 train / 240 val / 240 test_synth) -- 02A, unchanged
data/test_golden.jsonl       : 200 rows; data/test_golden_transcripts.txt: 200 lines -- ready for Session 03 recording
data/test_ood.jsonl          : 150 rows
data/train.jsonl             : 1,940 rows, §7.4 record format, augmented
data/val.jsonl               : 240 rows, clean (never augmented -- checkpoint selection is on reference text)
data/test_synth.jsonl        : 240 rows, clean (the McNemar paired sample)
data/roundtrip.jsonl         : 873 records -- per-row voice, length_scale, noise excerpt, SNR, ASR transcript
data/roundtrip_rejects.jsonl : 2 rows, eyeballed (see Decisions below)
data/asset_manifest.json     : DREGON 1 file + ESC-50 80 clips + 3 Piper voices, each with URL, SHA-256, licence
data/dataset_card.md         : §6 (corpora) and §6a (composition) are GENERATED from the manifest and the build -- do not hand-edit

data/fetch_assets.py         : asset fetch + verify + card §6
data/mix_noise.py            : THE only path producing noisy audio. 4 SNR levels (20/15/10/5), active-speech-level SNR, seeded, aug|eval noise partitions
data/tts_synth.py            : Piper, 3 voices, per-row voice + speaking rate
data/asr.py                  : deployed whisper.cpp config (tiny.en + S6 domain prompt) -- the runtime must import this, not copy it
data/roundtrip.py            : TTS -> mix -> whisper.cpp orchestration, resumable
data/composition.py          : intent-stratified variant assignment, largest-remainder quotas
data/perturb.py              : the 5% hand-injected slice
data/numwords.py             : spelled-out numbers -> digits
data/build_splits.py         : the two guards + split assembly + card §6a
data/check_leakage.py        : Gate 2, now with noise-partition isolation
data/check_grammar.py        : FR-1, now also over train/val/test_synth

Noise corpora on disk (gitignored, reproducible via fetch_assets.py):
  data/noise/dregon/  63 MB  DREGON_hovering_nosource_room2.wav -- pure UAV ego-noise
  data/noise/esc50/   35 MB  80 clips, helicopter + engine
  data/tts_voices/   190 MB  3 Piper voices
Derived audio (gitignored): data/audio/tts/ 873, data/audio/roundtrip/ 873

Test suite: 346 passed.

## Decisions this session
1. **Augmentation is substitution, not inflation** (ADR-0004 D1). A row's surface
   form is replaced; no row is added. This is the only reading that fits both
   `02_dataset_plan.md` §4's composition table and `prd.md` Table 13's ~1,900 size.
2. **Noise corpus partitioned** (D3): ESC-50 folds 1-4 + first 70% of the DREGON
   flight augment; fold 5 + last 30% are held back for Exp-3. Enforced by Gate 2.
3. **One noise excerpt per utterance across all its SNR levels** (D4), so Exp-3's
   ANOVA measures level and not excerpt.
4. **DREGON is available and was used.** It downloads directly ("free to use for
   academic and educational purpose"), so the *right* propeller-noise citation is in
   the corpus -- no ESC-50-only fallback and no fan-recording approximation. Both
   corpora are in the card with licence and SHA-256.
5. **`variant` now means the augmentation variant** (D5, per §7.4); 02A's generation
   variant moved to `source_variant`. Nothing lost.
6. **Identity round-trips are flagged, not re-rolled** (206 of 873). Re-drawing until
   a row degraded would keep only the utterances whisper fails on and bias the corpus
   away from the distribution the augmentation exists to reproduce. The card reports
   both provenance (50.5% clean) and text (61.1% clean).
7. **Two bugs found by the §4 eyeball pass, both label-corrupting:**
   - guard (ii) relabelled 15 *correct* transcriptions `unknown` because character
     similarity punishes "one hundred and twenty-eight point four" -> "128.4".
     Fixed by `data/numwords.py`; 17 -> 1 relabels.
   - `strip_punctuation` turned "1.5" into "15" against a label still reading 1.5.
     Fixed; regression test added.
   ADR-0004 D6/D7.
8. `.gitignore` gained one line, `data/tts_voices/` (190 MB of ONNX). The spec-file
   block at lines 119-125 was not touched.

## Blocked / needs human
- Autorisation de soutenance: requested Sep 6, still pending (Issue 24). Chase Sep 17.
- `llama-gbnf-validator` is not built on the workstation, so FR-1 rests on
  `data/gbnf.py` alone. S3 validated the grammar against real llama.cpp on the Pi.
  Build it before Session 05B, where Gate 3 needs the live parser.
- Session 03 needs the human for ~90 min of recording (200 utterances, quiet room,
  48 kHz S16_LE mono, AGC/noise-suppression off). Transcripts are ready at
  `data/test_golden_transcripts.txt`.

## Next session starts with
Session 03 Task 1 (`data/record_session.py`). Preconditions are met: Gate 1 green,
S0 noise floor -64.47 dBFS (<= -50 required), 200 golden transcripts authored.
**The ten-day annotation fuse starts the day s1 is recorded** -- pass 1 that day,
pass 2 ten days later. Do NOT re-run Gate 1 or Gate 2.
For Exp-3 later: `python data/mix_noise.py --input data/audio/s1 --output data/audio/mixed --sources dregon --partition eval`.
