# Issue 04: audio-augmentation-splits

Status: resolved
Blocked by: 03 (resolved)
Session: 02B
Closes: Gate 2 (data/check_leakage.py)

## Summary
Audio augmentation via Piper TTS, digital noise mixing across 4 SNR levels, round-trip filtering, split assembly by template family, and leakage verification.

## Deliverables

| Artefact | What it is |
|---|---|
| `data/fetch_assets.py` | Fetches and SHA-256 verifies DREGON + ESC-50 noise and three Piper voices; rewrites `dataset_card.md` §6 from the manifest |
| `data/asset_manifest.json` | Per-file URL, SHA-256, size, licence. Committed; the bytes are not |
| `data/mix_noise.py` | The only path producing noisy audio. 4 SNR levels, active-speech-level SNR, seeded, aug/eval-partitioned noise bank |
| `data/tts_synth.py` | Piper, three voices, per-row voice and speaking rate from `(seed, id)` |
| `data/asr.py` | The deployed `whisper.cpp` config in one place — `tiny.en` + S6 domain prompt, shared with the runtime |
| `data/roundtrip.py` | TTS → mix → whisper.cpp over the 873 assigned train rows → `roundtrip.jsonl` |
| `data/composition.py` | Intent-stratified variant assignment, largest-remainder quotas |
| `data/perturb.py` | The 5% hand-injected slice |
| `data/numwords.py` | Spelled-out numbers → digits. Session 04's `eval/norm.py` must import this |
| `data/build_splits.py` | Both guards, split assembly, `dataset_card.md` §6a |
| `data/train.jsonl` / `val.jsonl` / `test_synth.jsonl` | 1,940 / 240 / 240 rows in the §7.4 record format |
| `data/roundtrip.jsonl` | 873-row audit trail: voice, noise excerpt, SNR, similarity |
| `data/roundtrip_rejects.jsonl` | 2 rows, for the §4 eyeball pass |
| `docs/adr/0004_*.md` | Seven decisions, including the two the eyeball pass found |

## Composition realised (intended → realised)

| Variant | Intended | Realised | Rows |
|---|---:|---:|---:|
| `clean` | 50% | 50.5% | 979 |
| `asr_20db` | 20% | 19.9% | 387 |
| `asr_10db` | 15% | 15.0% | 291 |
| `asr_5db` | 10% | 10.0% | 194 |
| `perturb` | 5% | 4.6% | 89 |

206 round-trip rows came back with the clean wording. They are flagged, not
re-rolled: an identity round-trip is a true sample from the ASR output
distribution. Counting text rather than provenance the corpus is 61.1% clean, and
the card says so.

## Two bugs the eyeball pass caught

1. **Guard (ii) relabelled 15 correct transcriptions as `unknown`.** Whisper writes
   "128.4" for "one hundred and twenty-eight point four"; on raw characters that
   scores 0.54, under the 0.55 threshold. Training on those rows teaches the model
   to refuse valid commands. Fixed by `data/numwords.py`; count fell 17 → 1.
2. **`strip_punctuation` ate decimal separators.** `"circle, 1.5 radius"` shipped as
   `"circle 15 radius"` against a label still reading `radius: 1.5`. No recogniser
   produces that, so it was a mislabelled row, not a hard one. Fixed; regression
   test added.

Both are recorded in ADR-0004 (Decisions 6 and 7).

## Gate 2 — `python data/check_leakage.py --strict`

```
Running Gate 2 split leakage verification...
[+] Template family integrity: PASS (120 families: 96 train, 12 val, 12 test_synth)
[*] Inspecting pre-split files for leakage...
[+] Split isolation (train vs val): PASS (240 rows, 0 overlaps, 0 near-duplicates)
[+] Split isolation (train vs test_synth): PASS (240 rows, 0 overlaps, 0 near-duplicates)
[+] Split isolation (train vs test_golden): PASS (200 rows, 0 overlaps, 0 near-duplicates)
[+] Eval independence (val vs test_synth): PASS (240 rows, 0 exact matches, 0 near-duplicates)
[+] Eval independence (val vs test_golden): PASS (200 rows, 0 exact matches, 0 near-duplicates)
[+] Eval independence (test_synth vs test_golden): PASS (200 rows, 0 exact matches, 0 near-duplicates)
[+] Noise partition isolation: PASS (round-trip audio drew only from the augmentation partition)

[+] Gate 2 verification SUCCESSFUL: No leakage detected.
EXIT=0
```

## FR-1 — `python data/check_grammar.py`

```
grammar: /home/kahia-tayeb/PFE/schema/cmd.gbnf
  raw_pairs.jsonl               2421 labels  all accepted
  test_golden.jsonl              200 labels  all accepted
  test_ood.jsonl                 150 labels  all accepted
  train.jsonl                   1940 labels  all accepted
  val.jsonl                      240 labels  all accepted
  test_synth.jsonl               240 labels  all accepted

data/gbnf.py: 5191 labels checked, 441 distinct, 0 rejected

llama-gbnf-validator: NOT FOUND --- the gate rests on data/gbnf.py alone.
GATE PASS --- 5191 labels accepted by: data/gbnf.py
```

## Test suite

```
346 passed in 2.40s
```

## Comments
- 2026-09-07 (Session 01A): Tracker initialized.
- 2026-09-13 (Session 02B): Resolved. DREGON turned out to be directly downloadable
  (free for academic use), so the *right* propeller-noise citation is in the corpus
  and no fan-recording approximation was needed. Round-trip ran 873 rows in ~13 min
  (synth+mix 43 s, whisper.cpp 517 s). Gate 2 green, FR-1 green, 346 tests pass.
  `llama-gbnf-validator` is still absent on the workstation, so FR-1 rests on
  `data/gbnf.py` alone — unchanged from 02A, tracked for Session 05B.
