# ADR-0004: Round-Trip Augmentation Substitutes Surface Forms, and the Noise Corpus is Partitioned

**Status:** Accepted (Session 02B)
**Supersedes:** nothing. **Amended by:** nothing.

## Context

Session 02B implements `02_dataset_plan.md` §4, the ASR round-trip augmentation.
Seven things needed deciding before `data/build_splits.py` could write a row, and
none of them is settled verbatim by `prd.md`. Each is a commitment that shows up in
a reported number, so each is recorded here rather than left in a commit message.
The last two were found by reading the guard output rather than by reasoning about
it, which is the argument for §4's "eyeball the rejects once" being a step and not
a nicety.

---

## Decision 1 --- Augmentation replaces a row's surface form; it does not add a row

`02_dataset_plan.md` §4 gives the composition of the final training set:

| Variant | Share |
|---|---|
| Clean transcript | 50% |
| ASR round-trip @ 20 dB | 20% |
| @ 10 dB | 15% |
| @ 5 dB | 10% |
| Hand-injected perturbation | 5% |

`prd.md` Table 13 gives the size: `train_synth`, **$\approx$1,900 pairs**, source
"label-first synthetic generation **plus round-trip augmentation**".

Two readings fit the composition table and only one fits both documents.

**Inflation** — keep all 1,941 clean rows from Session 02A and append a round-trip
row beside each, weighted to the table. The split becomes ~3,900 rows. That
contradicts Table 13 by a factor of two.

**Substitution** — each of the 1,941 rows is assigned one variant, and a row
assigned `asr_10db` has its *transcript* replaced by what `whisper.cpp` heard at
10 dB while keeping its original `target`. The split stays at 1,941 $\approx$ 1,900,
and it is 50% clean.

**We adopt substitution.** Beyond the arithmetic, three things point the same way:

- §4's instruction is "pair the **noisy** transcript with the **original**
  `gold_json`" — one pair, not two.
- §4's own de-duplication guard reads as written for substitution and as a
  contradiction under inflation: "round-tripping often returns the clean string, and
  near-duplicates inflate your effective epoch count". Under inflation that is the
  *designed* behaviour, not a hazard to guard against.
- Under inflation the same label appears two to five times with near-identical text.
  Three epochs (Table 14) over that corpus is closer to nine epochs over the labels,
  and the LoRA would overfit the surface forms the augmentation was meant to
  diversify.

**Cost.** The model never sees a clean/noisy minimal pair for one label, so it
cannot learn the correspondence contrastively. We accept that: the model is not
being asked to denoise, it is being asked to parse whatever text arrives.

**Trace.** `data/composition.py`; `data/build_splits.py:apply_augmentation`.

---

## Decision 2 --- The clean half exists because Exp-1 is measured on reference text

Deployment always feeds `whisper.cpp` output to the parser, so a purely
round-tripped training set would match deployment more closely than a 50/50 mix
does. Keeping 50% clean is therefore worth justifying rather than inheriting.

**Exp-1 measures exact match on reference text** (`IMPLEMENTATION_ROADMAP.md` §2.6,
and the reason is stated there: feeding Exp-1 audio would impose a WER ceiling on
all three models at once and make any remaining difference unattributable). So the
headline accuracy number is measured on human-authored transcripts, and the
deployed CRR number is measured on ASR output. The model has to hold both
distributions, and EM − CRR is only interpretable as "the cost of the
speech-recognition stage" if the model is not disadvantaged on one side of it.

50/50 is what covers both. This is not a tuning choice and should not be re-tuned
against a validation score.

---

## Decision 3 --- The noise corpus is partitioned: augmentation and Exp-3 share no bytes

Round-trip augmentation and the Exp-3 SNR sweep both need noise. If they draw from
the same excerpts, the fine-tuned model has been tuned against transcripts whose
error pattern was produced by the very seconds of audio it is then evaluated
against, and the reported robustness does not generalise past them. Nothing in the
PRD forbids sharing — but nothing licenses the claim that would follow from it.

**Partition.** ESC-50 folds 1–4 augment, fold 5 evaluates. ESC-50's fold assignment
keeps clips originating from one source recording together, which is exactly the
property needed. DREGON is a single flight, so it is split by position: the first
70% augments, the last 30% evaluates.

**Cost.** Exp-3 draws from 17 recordings rather than 81. Acceptable — Exp-3's noise
condition is *propeller-type noise*, and it runs `--sources dregon` anyway, where
the partition costs a fraction of one continuous flight.

**Trace.** `data/mix_noise.py:NoiseBank`; `data/roundtrip.py:AUG_PARTITION`.

---

## Decision 4 --- One noise excerpt per utterance, shared across all its SNR levels

`prd.md` §9.3 fixes that SNR is measured on the active-speech level rather than
full-file RMS, and that mixing is digital. It does not say whether the 20 dB and the
5 dB version of utterance `0042` use the same noise.

**They do.** The excerpt is drawn from `(seed, item_id)` and deliberately not from
the SNR. Drawing per level would confound level with excerpt, and Exp-3's one-way
ANOVA across SNR would be measuring both at once — with *n* = 200 items and five
levels, excerpt variance is not small enough to ignore.

For the same reason the speech is never scaled: only the noise is. Where the sum
would clip, the whole mixture is attenuated by one factor, which leaves the ratio
exact and is reported per file.

**Trace.** `data/mix_noise.py:rng_for_item`, `mix_at_snr`;
`data/test_mix_noise.py::test_one_excerpt_serves_every_snr_level`.

---

## Decision 5 --- `variant` means the augmentation variant; 02A's value moves to `source_variant`

`02_dataset_plan.md` §7.4 fixes the training record format and its `variant` field
holds `"asr_10db"`. Session 02A had already written the *generation* variant
(`paraphrase_2`, `hard_negative`, `authored_unknown`) into the same key.

§7.4 wins, because the trainer and every downstream table read it. 02A's value is
preserved under `source_variant`, so the hard-negative and authored-unknown
provenance that Session 02A built is still queryable — it is needed for the
per-slice accuracy breakdown in Exp-1.

**Trace.** `data/build_splits.py:to_record`.

---

## Decision 6 --- A destroyed utterance is relabelled `unknown` and kept, not dropped

§4 guard (ii) says to relabel rather than keep a corrupt→command pair. It does not
say whether to keep the row at all.

**Kept.** A transcript too damaged for a person to read *should* produce `unknown`
— that is the safe-failure behaviour NFR-9 measures, and these rows are the only
naturally-occurring training signal for it. Dropping them would remove the evidence
and shrink the split silently.

The threshold is character similarity against the clean form, below
`DESTROYED_SIMILARITY = 0.55`. It is set to sit clear of ordinary degradation —
"form a circle, radius five" → "4m a circle, radius 5." scores ≈ 0.8 and is still
readable — while catching whisper's silence artefacts ("Thanks for watching!",
"[BLANK_AUDIO]"). Every row the guards touched is written to
`data/roundtrip_rejects.jsonl` for the one-time eyeball pass §4 asks for.

**The eyeball pass earned its place immediately.** The first build relabelled 17
rows, and reading them showed that 15 were *correct transcriptions*. Whisper writes
"128.4" where the speaker said "one hundred and twenty-eight point four", and on
raw characters that scores 0.54 — under the threshold. Training on those rows would
have taught the model to answer `unknown` to perfectly readable commands: a safety
regression, and one no aggregate statistic would have shown. `data/numwords.py`
now rewrites spelled-out numbers as digits and the guard scores both forms, taking
the better. The count fell from 17 to 1, and the one that remains ("call mohamed"
→ "call, no, high, mid,") was already labelled `unknown`.

`eval/norm.py` (Session 04) must import the same mapping: §2.7 defines WER as edit
distance after "expand digits via the mapping in `eval/norm.py`", and two digit
mappings in one repo means the WER figure and this guard disagree about what the
same utterance says.

**Trace.** `data/build_splits.py:apply_augmentation`, `similarity`,
`DESTROYED_SIMILARITY`; `data/numwords.py`.

---

## Decision 7 — The perturbation slice may not change a slot *value*

Guard (ii) polices what the recogniser does. Nothing policed what the hand-injected
perturbation does, and the first build shipped `"circle, 1.5 radius, all units"` as
`"circle 15 radius all units"` against a label still reading `radius: 1.5` —
`strip_punctuation` had removed the decimal separator.

The distinction that matters: a perturbation may make an utterance *harder to read*
(`"drone two"` → `"drone to"`, `"forty-eight"` → `"forty-ate"` — 21 rows do exactly
that, and they are the point of the slice) but it may not silently make the label
wrong. No recogniser writes "15" for "one point five", so that row was not a hard
example, it was a mislabelled one.

`strip_punctuation` now spares a period with a digit on each side, and
`digitise_number` delegates to `numwords` so it reads a compound number whole
rather than one word at a time ("1 point five" was the other symptom).

**Trace.** `data/perturb.py:_NON_DECIMAL_PERIOD`, `digitise_number`;
`data/test_perturb.py::test_strip_punctuation_never_eats_a_decimal_separator`.
