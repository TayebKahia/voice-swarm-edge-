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
| **Noise floor, silence** | TBD dBFS | measured at **S0** |
| Normal speech peak | TBD dBFS | measured at **S0** |
| Capture + buffering latency | TBD ms, loopback | measured once at **S0** |

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

## 6. Noise corpora — licences

| Corpus | Use | Licence | URL |
|---|---|---|---|
| ESC-50 | Environmental classes | TBD | TBD |
| DREGON | UAV-embedded rotor noise | TBD | TBD |
| Common Voice (English, validated) | Exp-0 | CC0 | TBD |
| Wake-word negatives | NFR-15 denominator | TBD | TBD |

SNR levels for Exp-3 are mixed **digitally** from session 1's clean audio, so no
level requires re-recording. Mixing is level-matched on the **speech-active
region only** — leading silence would otherwise set the level and make nominal
SNR depend on how promptly the speaker started.

Levels: clean, 20, 15, 10, 5 dB.

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
