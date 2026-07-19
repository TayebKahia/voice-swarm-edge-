# Dataset card — voice-to-JSON swarm commands v1.0

Fill each `TBD` from the spike or day named beside it. This file is committed;
the audio corpora it describes largely are not, so **this card is the only
record of where the bytes came from.** A `TBD` left in place at the D5 freeze
means the dataset is not reproducible.

---

## 1. Capture hardware and audio paths

| Field | Value | Source |
|---|---|---|
| Microphone | TBD | fixed at **S0** |
| USB interface | TBD | fixed at **S0** |
| ALSA card / device | TBD | `arecord -l` at **S0** |
| Corpus sample rate | 48 kHz, `S16_LE`, mono | fixed |
| Corpus resampling | offline 3:1 `soxr` VHQ to 16 kHz — **never ALSA `plug`** | fixed |
| Live-path resampling | TBD (16 kHz direct, or named online polyphase) | decided at **S0** |
| **Noise floor, silence** | -64.47 dBFS | measured at **S0** (meets <= -50 dBFS) |
| Normal speech peak | -36.06 dBFS | measured at **S0** |
| Capture + buffering latency | 120 ms (nominal ALSA 3-period buffer @ 48 kHz) | measured at **S0** |

Pass condition at S0: noise floor **≤ −50 dBFS** with speech peaking near
−20 dBFS. A floor above −40 dBFS triggers the R-2 escalation ladder, because it
would contaminate every nominal SNR level below.

---

## 2. Speaker

**One speaker: the author.** A fluent L2 English speaker, single accent.

This is an internal-validity choice, not an oversight. Holding the speaker fixed
makes noise the only varying factor in Exp-3, which is what licenses the causal
statement about SNR. It is **never** presented as speaker independence. External
validity at the acoustic model — the only speaker-sensitive stage — is measured
separately by Exp-0 on Mozilla Common Voice.

---

## 3. Recording sessions — 320 files

| Folder | Files | Condition | Day |
|---|---|---|---|
| `audio/s1/` | 200 | Quiet room. All ten intents, every slot combination in the required-slot matrix. | D4 |
| `audio/s2/` | 60 | A 60-item subset in a different room with real background: corridor noise, fan, distant conversation. | D5 |
| `audio/s3/` | 60 | The same 60 items on a different day — day-to-day voice variation and microphone placement. | D5 |

| Field | Value |
|---|---|
| Room 1 (s1) | TBD — dimensions, surfaces, time of day |
| Room 2 (s2) | TBD |
| s3 recorded | TBD — date, and days after s1 |
| Mic distance | TBD cm, consistent within a session |

**Filenames are join keys.** `0042.wav` is the same utterance in `s1/`, `s2/`,
and `s3/`, and `0042` is its line number in `test_golden.jsonl`.

---

## 4. Splits — assigned by template family

Every paraphrase descended from one label lands in the **same** split. Row-wise
splitting puts near-duplicates on both sides of the boundary and inflates every
accuracy figure. `check_leakage.py` enforces this and is a gate, not a report.

| Split | Size | Source | Role |
|---|---|---|---|
| `train_synth` | ~1,900 pairs | Label-first generation + round-trip augmentation | LoRA fine-tuning |
| `val_synth` | ~250 pairs | Held-out template families | Checkpoint selection on exact match |
| `test_synth` | ~250 pairs | Held-out template families | Exp-1; the McNemar paired sample |
| `test_golden` | 320 audio / 200 transcripts | The author, three sessions | Headline accuracy and all of Exp-3 |
| `test_ood` | ~150 items | Out-of-domain and adversarial phrasings | NFR-18; the real test of `unknown` |
| `wake_pos` | ~1,500 clips per class | Piper TTS via openWakeWord's pipeline | Branch A training |
| `wake_neg` | ≥ 3 h | Ambient speech, podcasts, room noise | NFR-15 false accepts per hour |
| `commonvoice` | 300 clips | Common Voice English, validated | Exp-0 baseline |

**Conformance assert.** Every label in every split must be accepted by
`schema/cmd.gbnf`. A label the grammar cannot produce is an unreachable target
that silently caps accuracy. Part of the D1 gate, re-run after any regeneration.

---

## 5. Generation — label first

Write the target JSON, then request eight natural phrasings of it. The reverse
order reintroduces the annotation cost that generation was meant to remove and
produces label noise.

Diversity axes are enumerated, not left to sampling temperature: imperative and
polite forms, unit variants (metres, m), numeric forms (five, 5, 5.0), drone
subsetting (all, drone two, drones one and three), synonym sets per intent,
filler words, self-corrections, truncated utterances.

| Field | Value |
|---|---|
| Generator | TBD — model and version |
| Prompt file | TBD |
| Seed | TBD |
| Unique labels | TBD |
| Duplicates removed | TBD |

---

## 6. Downloaded corpora and models — licences

Fetched and hash-verified by `python data/fetch_assets.py`. The table below is
**rewritten from `data/asset_manifest.json` on every run** — do not hand-edit it.

<!-- corpora:begin -->

| Corpus | Files | Size | Licence | URL |
|---|---:|---:|---|---|
| DREGON | 1 | 63.3 MB | Free to use for academic and educational purpose (dregon.inria.fr, verbatim from the dataset homepage). Cite Strauss et al., IROS 2018. | <https://dregon.inria.fr/> |
| ESC-50 | 80 | 35.3 MB | CC BY-NC 3.0 (non-commercial; this is a non-commercial thesis) | <https://github.com/karoldvl/ESC-50> |
| piper-voices | 6 | 189.6 MB | MIT (piper-voices repository); underlying corpora per voice MODEL_CARD | <https://huggingface.co/rhasspy/piper-voices> |

Retrieved 2026-09-13. Fetched and verified by `python data/fetch_assets.py`; per-file SHA-256 in `data/asset_manifest.json`.

<!-- corpora:end -->

| Corpus | Role here |
|---|---|
| DREGON | UAV-embedded rotor noise, recorded on a flying quadrotor. The `hovering_nosource_room2` flight: ego-noise with no source playing, so the file is pure propeller wash. This is the *right* citation for propeller noise (`02_dataset_plan.md` §5) and it was available, so no approximation was needed. |
| ESC-50 | `helicopter` and `engine` classes, as environmental backing beside DREGON. CC-BY-**NC**: acceptable for a non-commercial thesis, recorded rather than glossed. |
| Common Voice (English, validated) | Exp-0 speaker-sensitivity baseline. Fetched at D6 — see §8. |
| Wake-word negatives | NFR-15 denominator. Fetched at D5 — see §8. |

### Mixing policy

`data/mix_noise.py` is the **only** path by which noisy audio is produced. It is
committed and seeded (`--seed 42`, `prd.md` Table 14), so the corpus reproduces
byte-for-byte.

- **Digital mixing from session 1's clean audio only.** No level requires
  re-recording. Recording a second acoustic condition instead would move room,
  distance, mic placement and voice together with the noise and destroy Exp-3's
  causal claim (`IMPLEMENTATION_ROADMAP.md` §0.2, conflict 4).
- **SNR is defined on the active-speech level** against noise RMS, not full-file
  RMS. The active level is the RMS over 20 ms frames within 30 dB of the loudest
  frame. Leading silence would otherwise set the level and make nominal SNR depend
  on how promptly the speaker started.
- **The speech is never scaled; only the noise is.** Where the sum would clip, the
  whole mixture is attenuated by one factor, which leaves the ratio exact. The
  attenuation is recorded per file.
- **One noise excerpt per utterance, shared across all its SNR levels.** Drawing a
  fresh excerpt per level would confound level with excerpt in Exp-3's ANOVA.
- **Corpus-balanced draws.** The corpus is chosen before the recording, so DREGON
  (one long flight) and ESC-50 (80 short clips) are equally represented.
- **Augmentation and evaluation share no noise bytes.** ESC-50 folds 1–4 and the
  first 70% of the DREGON flight augment; fold 5 and the last 30% are held back for
  Exp-3. See ADR-0004, Decision 3.

Levels: clean, 20, 15, 10, 5 dB. Round-trip augmentation uses 20, 10 and 5.

---

## 6a. Round-trip augmentation — the training-set composition

`gold_json` → clean transcript → Piper TTS → noise mix @ SNR → `whisper.cpp` →
noisy transcript, **paired with the original `gold_json`**. This is the fix for the
train/test distribution shift that otherwise costs 10–20 points of exact match
(`02_dataset_plan.md` §4).

| Field | Value |
|---|---|
| TTS | Piper, three voices: `en_US-lessac-medium`, `en_US-ryan-medium`, `en_GB-alba-medium` |
| Voice + speaking rate | assigned per row from `(seed, id)`; `length_scale` ∈ [0.88, 1.12] |
| ASR | `whisper.cpp` `tiny.en`, greedy, `-nt`, with the S6 domain prompt — **identical to the deployed runtime** (`data/asr.py`) |
| Rate | 16 kHz mono throughout; resampling is `soxr` VHQ |
| Applied to | the **train** split only. `val` and `test_synth` stay clean — both are measured on reference text (§2.6) |
| Augmentation is | **substitution**, not inflation: a row's surface form is replaced, its label is not, and no row is added. See ADR-0004, Decision 1 |

Composition of the final training set (`02_dataset_plan.md` §4), and what was
actually realised — the difference is guard activity, reported rather than hidden:

<!-- composition:begin -->

| Variant | Intended | Realised | Rows |
|---|---:|---:|---:|
| `clean` | 50% | 50.5% | 980 |
| `asr_20db` | 20% | 19.9% | 387 |
| `asr_10db` | 15% | 15.0% | 291 |
| `asr_5db` | 10% | 10.0% | 194 |
| `perturb` | 5% | 4.5% | 88 |
| **total** | 100% | 100% | **1940** |

Of the 206 round-trip rows the recogniser returned unchanged, none is re-rolled: an identity round-trip is a true sample from the ASR output distribution, and re-drawing until it degraded would keep only the utterances whisper fails on. Counting text rather than provenance, the corpus is 61.1% clean.

Guard and fall-back activity:

| Action | Rows | Meaning |
|---|---:|---|
| `roundtrip_identical` | 206 | recogniser returned the clean wording; row keeps its variant |
| `relabelled_unknown` | 1 | guard (ii): transcript destroyed, target -> `unknown` |
| `perturb_noop_to_clean` | 9 | nothing in the sentence was perturbable |
| `asr_missing_to_clean` | 0 | no transcript came back; fell back to clean |
| `dropped_duplicate` | 1 | guard (i): same text, same target |
| `reverted_conflict_to_clean` | 0 | guard (i): same text, different target |
| `dropped_conflict` | 0 | guard (i): unresolvable, both clean |

Split sizes as written: `train` 1940, `val` 240, `test_synth` 240.

<!-- composition:end -->

**Guard (i), de-duplication.** Identical post-augmentation transcripts carrying the
same target collapse to one row. Carrying *different* targets, the later row is
reverted to its clean form rather than dropped, so the label survives.

**Guard (ii), destroyed utterances.** Below 0.55 character similarity to the clean
form, the row keeps its degraded transcript and its target becomes
`{"intent":"unknown"}` — a transcript too damaged to read *should* produce
`unknown`, and these rows are the only naturally-occurring training signal for the
safe-failure rate NFR-9 measures.

Every row either guard touched is written to `data/roundtrip_rejects.jsonl`, and
the full per-row audit trail — voice, noise excerpt, SNR, similarity — is in
`data/roundtrip.jsonl`.

---

## 6b. Reproducing the corpus

Ordered, and each step is idempotent — re-running skips what is already on disk.
Steps 2–4 are CPU-bound and unattended.

```bash
python data/fetch_assets.py      # noise corpora + Piper voices, SHA-256 verified
python data/generate.py          # D2: label-first generation -> raw_pairs.jsonl
python data/roundtrip.py         # D3: TTS -> mix -> whisper.cpp -> roundtrip.jsonl
python data/build_splits.py      # D3: composition + guards -> train/val/test_synth.jsonl
python data/check_grammar.py     # FR-1: every label accepted by schema/cmd.gbnf
python data/check_leakage.py --strict   # Gate 2
```

Everything is seeded at 42 (`prd.md` Table 14) and every random choice is drawn
from a stable hash of `(seed, row id)` rather than from stream position, so the
corpus reproduces byte-for-byte and adding a row does not re-roll the rest of it.

---

## 7. Annotation agreement — intra-annotator

Measured on **50 golden-set utterances** by test–retest with a single annotator:
labelled at D5, that pass sealed, the same items relabelled cold at D15 — a gap
of ten days.

| Field | Value |
|---|---|
| Pass 1 | `annot/annot_pass1.jsonl` — D5, sealed |
| Pass 2 | `annot/annot_pass2.jsonl` — D15, cold |
| Agreement | TBD |
| Disagreements | TBD — each one localises a schema ambiguity |

Reported as **intra**-annotator agreement and never as inter-annotator. It
establishes that the schema is applied *stably*; it does not establish that a
second reader would apply it the same way, and that stronger claim is not made
anywhere.

**Pass 1 remains the authoritative gold label.** The dataset freezes at D5, so
the D15 pass is a measurement of consistency, not a revision. A schema gap found
after the freeze is recorded as future work; it does not trigger regeneration.

Synthetic labels need no annotation at all — they are generated label-first, so
the label is the source rather than a judgement. These 50 items are the only
place in the project where annotation occurs.

---

## 8. Freeze

| Field | Value |
|---|---|
| Tag | `dataset-v1.0` |
| Frozen | D5 |
| Commit SHA | TBD |
