# Dataset card — voice-to-JSON swarm commands v1.0

Fill each `TBD` from the spike or day named beside it. This file is committed;
the audio corpora it describes largely are not, so **this card is the only
record of where the bytes came from.** A `TBD` left in place at the D5 freeze
means the dataset is not reproducible.

---

## 1. Capture hardware and audio paths

| Field | Value | Source |
|---|---|---|
| Microphone | BOYA BY-M1, omnidirectional lavalier, 3.5 mm analog | fixed at **S0** |
| USB interface | GeneralPlus USB Audio Device (3.5 mm → USB adapter) | fixed at **S0** |
| ALSA card / device | `USB Audio Device` — enumerated by **name**, not index | `arecord -l` at **S0** |
| Capture gain | ALSA `Capture 28 [100%] [30.00 dB]`, AGC and noise suppression **off** | fixed at **S0** |
| Power | battery, never AC | **S0**: the wall charger raised the floor 22 dB with 50/100 Hz hum |
| Corpus sample rate | 48 kHz, `S16_LE`, mono | fixed |
| Corpus resampling | offline 3:1 `soxr` VHQ to 16 kHz — **never ALSA `plug`** | `data/resample.py` |
| Corpus level normalisation | **one gain per session**, loudest file to −14 dBFS | `data/resample.py`, decision at **S0** |
| Live-path resampling | native 16 kHz capture, direct — no online resampler in the loop | decided at **S0** |
| **Noise floor, silence** | −64.47 dBFS | measured at **S0** (meets ≤ −50 dBFS, 14.5 dB margin) |
| Normal speech peak | −36.06 dBFS | measured at **S0** |
| Capture + buffering latency | 120 ms (nominal ALSA 3-period buffer @ 48 kHz) | measured at **S0** |

The speech peak sits 16 dB under Table 22's −20 dBFS target and the ALSA capture
gain was already at maximum, so the shortfall is the capsule, not the setting. It
is corrected offline by a **single per-session gain** rather than per file: a
per-file ceiling would make a shouted command and a trailing-off one equally loud
and erase the level variation the golden set carries. **No nominal SNR moves:**
`data/mix_noise.py` levels noise against each file's active-speech RMS, so a
common gain on the speech cancels in the ratio.

The 48 kHz masters in `audio/s1..s3/` are never written to. The 16 kHz corpus
every consumer reads is derived in `audio/s1_16k/` and is regenerated, not
repaired. `data/resample.py` makes the identical `soxr` VHQ call as
`mix_noise.load_mono`, so a file carries the same samples whichever module opens
it — asserted in `data/test_resample.py`, not assumed.

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
| Room 1 (s1) | recorded in `audio/s1/session_meta.json` at capture time |
| Room 2 (s2) | recorded in `audio/s2/session_meta.json` at capture time |
| s3 recorded | recorded in `audio/s3/session_meta.json` at capture time |
| Mic distance | recorded per session; held constant within a session |

`data/record_session.py` asks for the room and the mic distance before the first
take and measures the room floor itself, so §3 is answered while the author is
standing in the room rather than reconstructed at write-up. Each session also
carries a per-take record — duration, peak, active-speech level, SNR against that
session's floor — in the same file.

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
| Generator | `data/generate.py` — deterministic templates, **no language model** |
| Surface forms | `data/surface_forms.py`, 120 template families |
| Seed | 42 (`prd.md` Table 14, identical everywhere in the project) |
| Rows | 2,421 in `raw_pairs.jsonl`; 200 golden; 150 OOD |
| Unique labels | 298 distinct canonical commands |
| Duplicates removed | near-duplicate surface forms rejected at Jaccard >= 0.85 by `check_leakage.py` |

There is **no prompt file and no generator model**, which is the point: the label
is constructed first and the text derived from it, so no row can carry a label
that disagrees with its transcript. A language model in this position would
introduce label noise that no downstream assertion could detect, and would make
`run_all.sh` irreproducible from a clean clone.

---

## 6. Downloaded corpora and models — licences

Fetched and hash-verified by `python data/fetch_assets.py`. The table below is
**rewritten from `data/asset_manifest.json` on every run** — do not hand-edit it.

<!-- corpora:begin -->

| Corpus | Files | Size | Licence | URL |
|---|---:|---:|---|---|
| Common Voice 17.0 en (test) | 2 | 716.0 MB | CC0 1.0 (Mozilla Common Voice Corpus 17.0) | <https://commonvoice.mozilla.org/en/datasets> |
| DREGON | 1 | 63.3 MB | Free to use for academic and educational purpose (dregon.inria.fr, verbatim from the dataset homepage). Cite Strauss et al., IROS 2018. | <https://dregon.inria.fr/> |
| ESC-50 | 80 | 35.3 MB | CC BY-NC 3.0 (non-commercial; this is a non-commercial thesis) | <https://github.com/karoldvl/ESC-50> |
| LibriSpeech dev-clean | 1 | 337.9 MB | CC BY 4.0 | <https://www.openslr.org/12> |
| MIT Acoustical Reverberation Survey | 1 | 11.7 MB | CC BY 4.0 (Traer & McDermott, PNAS 2016) | <https://mcdermottlab.mit.edu/Reverb/IR_Survey.html> |
| Speech Commands v0.02 (test set) | 1 | 112.6 MB | CC BY 4.0 | <https://arxiv.org/abs/1804.03209> |
| piper-voices | 6 | 189.6 MB | MIT (piper-voices repository); underlying corpora per voice MODEL_CARD | <https://huggingface.co/rhasspy/piper-voices> |

Retrieved 2026-09-14. Fetched and verified by `python data/fetch_assets.py`; per-file SHA-256 in `data/asset_manifest.json`.

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

python data/record_session.py --session s1   # D4: HUMAN, ~90 min
python data/resample.py --session s1         # D4: offline 3:1 soxr VHQ + session gain
python data/wake_corpus.py                   # D4: Branch A, 2 classes + >= 3 h negatives
python data/commonvoice.py                   # D4: Exp-0, 300 clips stratified by accent
python data/annotate.py --pass 1             # D5: HUMAN, then seal
```

Everything is seeded at 42 (`prd.md` Table 14) and every random choice is drawn
from a stable hash of `(seed, row id)` rather than from stream position, so the
corpus reproduces byte-for-byte and adding a row does not re-roll the rest of it.

---

## 7. Annotation agreement — intra-annotator

Measured on **50 golden-set utterances** by test–retest with a single annotator:
labelled on the day session 1 is recorded, that pass **sealed**, the same items
relabelled cold six days later in a **different presentation order**.

The 50 are chosen stratified by intent — five per intent, all ten covered. A
uniform draw from 200 would expect fewer than three `abort` rows and could return
none, and `abort` is the one intent whose misapplication is a safety matter.

The table below is **generated** by `python data/annotate.py --compare`.

<!-- annotation:begin -->

| Field | Value |
|---|---|
| Pass 1 | `annot/annot_pass1.jsonl` — sealed, authoritative |
| Pass 2 | `annot/annot_pass2.jsonl` — cold relabel |
| Gap | TBD — pass 2 not recorded |
| Items | 50 |
| Exact agreement | TBD |
| Intent agreement | TBD |
| Slot F1 between passes | TBD |
| Disagreements | TBD — each one localises a schema ambiguity |

<!-- annotation:end -->

Reported as **intra**-annotator agreement and never as inter-annotator. It
establishes that the schema is applied *stably*; it does not establish that a
second reader would apply it the same way, and that stronger claim is not made
anywhere.

**The gap is six days, not the ten `prd.md` §9.3 originally planned.** Execution
began one day behind the PRD's own D-numbering, pass 1 is gated on the recording,
and the dépôt fixes the far end — so ten days stopped being reachable in either
direction. What makes the second pass a measurement rather than a recital is
forgetting, and six days controls for recall **less well** than ten; the residual
bias runs toward *higher* apparent agreement. Shuffling the presentation order is
a real but partial mitigation, not a substitute for elapsed time. Both are stated
here, in §9.3 and in the Limitations table rather than left for a reader to
notice from the dates.

**Pass 1 remains the authoritative gold label.** The dataset freezes with it, so
the second pass is a measurement of consistency, not a revision. A schema gap
found after the freeze is recorded as future work; it does not trigger
regeneration. The seal is a SHA-256 in `annot/annot_pass1.seal.json`, so an edit
after sealing is detected rather than trusted not to happen.

Synthetic labels need no annotation at all — they are generated label-first, so
the label is the source rather than a judgement. These 50 items are the only
place in the project where annotation occurs.

---

## 8. Freeze

| Field | Value |
|---|---|
| Tag | `dataset-v1.0` |
| Frozen | the day session 1 is recorded (PRD D5) |
| Commit SHA | the commit the tag points at — `git rev-parse dataset-v1.0^{commit}` |

**Freeze means freeze.** If week 3 reveals a schema gap it becomes future work:
regenerating would invalidate every number already measured against the frozen
corpus.

---

## 9. Wake-word corpus — Branch A

Two classes and nothing else: `swarm hold` → `hover`, `swarm abort` → `abort`
(`prd.md` FR-6). **No movement verb may ever be added.** Both qualifying intents
make the swarm do *less*, so a false accept is always fail-safe — that membership
rule is derived from a latency argument, not preference, and it is contribution
**C4**.

Built by `python data/wake_corpus.py`; counts and per-clip provenance in
`data/wake/wake_manifest.json`. Every clip is 2.5 s, 16 kHz, mono.

| Part | Source | Role |
|---|---|---|
| Positives | Piper — 3 voices × 20 prosody renditions per class, each augmented 25× | the two keywords |
| Negatives — natural | LibriSpeech dev-clean | continuous read speech |
| Negatives — command words | Speech Commands v0.02 test set | `stop`, `go`, `up`, `down`, `left`, `right` — false-activation hardening |
| Negatives — near-misses | Piper, 40 authored phrases | `swarm`, `hold`, `abort` alone; `swarm hover`; `hold on`; `storm`, `sworn` |
| Rooms | MIT Acoustical Reverberation Survey | impulse responses |
| Background | ESC-50 + DREGON, the same partitions `mix_noise.py` uses | noise at 3–25 dB SNR |

Four properties, each of which would otherwise cost a number in Exp-2:

- **Split by base rendition, not by clip.** Exp-2 reports a per-class ROC with a
  declared operating point (NFR-15/16). Measured on clips whose un-augmented
  parent was trained on, that ROC describes memorisation. Every augmented variant
  of one Piper rendition lands in one split — the same rule `build_splits.py`
  applies to template families. Negatives split by **speaker**, near-misses by
  **phrase**.
- **Train and test hear different rooms and different noise.** RIRs split 70/30
  by index; background comes from the `aug` partition for train/val and the
  `eval` partition for test. Sharing them would let the held-out figure describe a
  room the model had already heard.
- **The keyword sits at a random offset, never centred.** A model trained on
  centred keywords learns the centring; deployment feeds it a sliding buffer.
- **Near-misses are authored because neither public corpus contains them.**
  Nothing in LibriSpeech or Speech Commands says "swarm", and nothing begins a
  phrase with "hold". Those are the confusions that actually cost false accepts
  on *this* keyword pair.

NFR-15's negative corpus floor is **three hours**, and the false-accept figure is
reported as a count per hour **with a Poisson confidence interval** — "zero false
accepts over three hours" is consistent with a true rate near one per hour.

---

## 10. Exp-0 corpus — Common Voice

300 clips, stratified by accent, built by `python data/commonvoice.py`;
per-clip metadata in `data/commonvoice/exp0_manifest.jsonl`.

Exp-0 exists because §2 of this card holds the speaker fixed on purpose. That
choice is what makes noise the only varying factor in Exp-3, and its cost is that
nothing in the golden set says whether `tiny.en` works for anyone but the author.
Exp-0 recovers external validity at the one stage that is actually
speaker-sensitive — the acoustic model — and reports **WER per accent bucket**
with **the author positioned as a percentile, not pass/fail**.

| Field | Value |
|---|---|
| Release | Mozilla Common Voice 17.0, English, `test` split |
| Retrieved from | `fsicoli/common_voice_17_0` — an **ungated mirror** of that release |
| Licence | CC0 1.0 |
| Selection | accent label present, ≥ 2 up-votes, 0 down-votes, 1.5–12 s |
| Sampling | round robin over accent buckets, smallest bucket first, seed 42 |
| Buckets | accent groups with ≥ 10 source rows; free-text labels pool into one |

Sampling is stratified rather than uniform because a uniform draw from this shard
is 39% United States English and would leave several accent groups at zero —
precisely the sample that would make the author's own WER look unremarkable for
the wrong reason. Bucket sizes are unequal and each is reported **with its *n***;
a bucket of three is never smoothed into a bucket of eighty.

Mozilla's own endpoint requires a browser consent step no script can perform. The
mirror is recorded as a mirror here and in `asset_manifest.json`, with its
SHA-256, rather than cited as the official distribution.
