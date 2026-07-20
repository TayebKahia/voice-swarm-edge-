# ADR-0005: Golden-Set Capture, the Wake Corpus, and the Annotation Interval

**Status:** Accepted (Session 03)
**Supersedes:** nothing. **Amends:** `prd.md` §9.3, the Limitations table, and R-9
— the annotation interval only (Decision 6). **Amended by:** nothing.

## Context

Session 03 produces the three corpora nothing downstream can be rebuilt without:
the 200 golden recordings, the Branch A wake corpus, and Exp-0's Common Voice
sample. It also starts the annotation clock.

Seven things needed deciding. Two of them (1 and 2) are irreversible at capture
time, three (3, 4, 5) decide whether an Exp-2 number means what it says, one (6)
amends the contract, and one (7) is a provenance question that must be answered
in the open rather than glossed.

---

## Decision 1 — The 48 kHz masters and the 16 kHz corpus are different directories

`prd.md` D4: capture at 48 kHz, resample offline with soxr VHQ, never ALSA
`plug`. It does not say where the resampled corpus lives, and the obvious answer
— resample in place — is the wrong one.

**`audio/s1/` holds the masters and is never written to after capture.**
`audio/s1_16k/` is derived, gitignored, and rebuilt by `data/resample.py`. If the
derived corpus is ever wrong it is thrown away; if a master is wrong there is
nothing to do, because these 320 files cannot be re-recorded.

`test_golden.jsonl`'s `audio_path` points at the master, which is the provenance
pointer and the join key. Consumers read the derived corpus.

**One resampling call, not two.** `data/resample.py:resample` and
`mix_noise.load_mono` make the identical `soxr.resample(..., quality="VHQ")`
call, so a file carries the same samples whichever module opens it. Two correct
but different resamplers would put different bytes in front of `whisper.cpp`
depending on which door a consumer used, and the WER difference would read as a
model effect. `test_resample.py` asserts the equality rather than trusting it.

**Trace.** `data/resample.py`; `data/test_resample.py::test_resample_matches_mix_noise_exactly`.

---

## Decision 2 — One normalisation gain per session, not one per file

S0 measured the BOYA peaking at −36.06 dBFS against Table 22's −20 dBFS, with the
ALSA capture gain already at maximum: the shortfall is the capsule, not a
setting. The S0 report recorded the decision to normalise offline but not the
granularity, and the granularity is the whole question.

**One scalar for the session**, lifting its loudest file to −14 dBFS. Per-file
normalisation would make a shouted command and a trailing-off one equally loud,
erasing the level variation the golden set exists to carry. A single scalar
preserves every relative level and is one multiplication away from being undone;
it is written to `resample_manifest.json`.

**No nominal SNR moves.** `mix_noise` levels noise against each file's
*active-speech* RMS, so a gain common to speech and nothing else cancels in the
ratio. This is the same property that made active-speech levelling the right
choice in ADR-0004 D4, used a second time.

A gain above 24 dB aborts rather than applying: that would mean the session was
recorded ~20 dB under the chain S0 characterised, which is a capture fault and
not a level to correct.

**Trace.** `data/resample.py:PEAK_CEILING_DBFS`, `MAX_GAIN_DB`;
`data/test_resample.py::test_one_gain_for_the_session_preserves_relative_levels`.

---

## Decision 3 — The wake corpus is split, and the split is by base rendition

Nothing in the PRD says the wake corpus has a held-out portion. Exp-2 nonetheless
reports a per-class ROC with a declared operating point (NFR-15, NFR-16), and a
ROC measured on clips the model trained on is a statement about memorisation.

**Split 70/10/20, and the unit is the base Piper rendition.** All 25 augmented
variants of one rendition land in one split. Negatives split by **speaker**
(LibriSpeech, Speech Commands) and near-misses by **phrase** — otherwise the
held-out false-accept rate is measured on a phrase the model was trained to
reject, which is the same error one level down.

This is `build_splits.py`'s template-family rule applied to audio, and for the
same reason.

**Trace.** `data/wake_corpus.py:assign_splits`;
`data/test_wake_corpus.py::test_no_base_rendition_straddles_two_splits`.

---

## Decision 4 — Train and test hear different rooms and different noise

Having split the clips, the augmentation could still leak the room: 3,000
positives convolved with the same 271 impulse responses means the held-out clips
were recorded, acoustically, in rooms the model trained in.

**RIRs split 70/30 by index. Background noise comes from the `aug` partition for
train and val, and the `eval` partition for test** — the same two partitions
`mix_noise.py` defines and `check_leakage.py` already gates. Every clip's
`noise_key` is recorded in `wake_manifest.json`, so the partition is checkable
against what the pipeline *did*, not against what the source intends.

**Cost.** Training sees 189 rooms rather than 271. Accepted: a robustness figure
measured across rooms the model has heard is not a robustness figure.

**One thing the keys could not say, found by the test that checks them.** ESC-50
keys carry the partition in the filename, so disjointness is provable from the
manifest. DREGON does not: it is one continuous flight split by *position*, and
both partitions legitimately report the same filename. The first version of
`test_the_held_out_split_hears_noise_...` asserted key-disjointness over both and
failed on correct behaviour. The bytes were always disjoint --- `NoiseBank._load`
slices them and `test_mix_noise.py::test_partitions_are_disjoint` asserts it ---
but the *provenance record* could not express it. Each clip now records
`noise_partition` from the bank it actually drew from, so the manifest states
which half of the flight was used instead of leaving a reader to infer it.

**Trace.** `data/wake_corpus.py:RIRBank`, `_banks`.

---

## Decision 5 — The keyword sits at a random offset, and the near-misses are authored

Two small things, both of which are invisible until Exp-2.

**Random offset.** A keyword always centred in its 2.5 s window teaches the model
where to look. Deployment feeds a sliding buffer that offers no such guarantee,
and the resulting false-reject rate would appear only at NFR-16.

**Authored near-misses.** LibriSpeech gives natural speech and Speech Commands
gives `stop`/`go`/`up`/`down`/`left`/`right`, which is the false-activation
hardening the roadmap names. Neither contains the word "swarm", and neither
begins a phrase with "hold". So the 40 phrases that actually threaten *this*
keyword pair — `swarm` alone, `hold on`, `swarm hover`, `storm`, `sworn`,
`abort the mission` — do not exist in any public corpus and are synthesised
deliberately.

`abort the mission` is a negative, not a positive, and that is not an oversight:
FR-6 fixes Branch A at exactly two phrases and everything else is Branch B's. A
false *reject* there is correct behaviour.

**Trace.** `data/wake_corpus.py:place_in_window`, `ADVERSARIAL_PHRASES`.

---

## Decision 6 — The annotation interval is six days, and the shortfall is reported

`prd.md` §9.3 specified pass 1 → pass 2 as **a gap of ten days** (D5 → D15), and
said so in three places. It is not reachable.

The arithmetic: execution began Mon 7 Sep against a D-numbering that assumed
Thu 27 Aug, so the project runs behind its own calendar while owing the same
deliverables. Pass 1 is gated on the recording, which is today. The dépôt is
Mon 21 Sep. Sealing on Sun 14 Sep and relabelling on Sun 20 Sep is **six days**,
and that is the maximum: the interval cannot extend past the dépôt, and pass 1
cannot move earlier because it depends on audio that did not exist until today.

**We shorten the claim rather than leave a stated ten days the dates refute.**
The roadmap pre-authorises exactly this — Session 03's block reads "Slipping this
day shortens the interval and forces an edit to `prd.md` §9.3 and the Limitations
table." A smaller claim honestly stated costs nothing. A ten-day claim the dépôt
calendar contradicts is a finding against the author.

What the gap is *for* is forgetting: the second pass measures schema stability
only if the annotator has genuinely re-derived each label rather than recalled
it. Six days controls for recall **less well** than ten, and the bias that leaves
runs toward **higher** apparent agreement. That direction is stated in §9.3, in
the Limitations table, in R-9 and in dataset card §7, because a reader who works
out the dates will ask, and the answer should already be on the page.

**One free mitigation, taken.** Pass 2 presents the same 50 items in a different
random order. Order is a strong recall cue and removing it costs nothing. It is a
partial mitigation and is described as one — it does not substitute for elapsed
time.

**Enforced, not trusted.** `data/annotate.py` seals pass 1 with a SHA-256, refuses
to seal an incomplete pass, refuses to open pass 2 before the seal exists,
reports the interval from the seal's own timestamp rather than from the plan, and
never displays pass 1 — or `test_golden.jsonl`'s generated `target` — during
either pass. These rows were built label-first, so showing the target would turn
annotation into proof-reading.

**Trace.** `prd.md` §9.3, Limitations, R-9, Table 25; `docs/project/PRD.tex`
(same four); `data/dataset_card.md` §7; `data/annotate.py`; `data/test_annotate.py`.

---

## Decision 7 — Common Voice comes from a mirror, sampled by accent, and both are said out loud

Exp-0 needs 300 Common Voice clips. Mozilla's own endpoint requires a browser
consent step no script can perform, and `mozilla-foundation/common_voice_*` on
Hugging Face is gated or emptied.

**The bytes come from `fsicoli/common_voice_17_0`, an ungated mirror of the same
17.0 release, and it is recorded as a mirror** — in `asset_manifest.json` with
its SHA-256 and in dataset card §10 — rather than cited as the official
distribution. The corpus, the release and the CC0 licence are Mozilla's; the
retrieval path is not, and a reader is entitled to know which is which.

**The sample is stratified by accent, not uniform.** A uniform draw from this
shard is 39% United States English and leaves several accent groups at zero.
Exp-0's whole purpose is to recover the external validity the single-speaker
golden set gives up, and it reports WER per accent bucket with the author placed
as a percentile. A sample that collapses the accent axis measures nothing about
accent, and would make the author's own WER look unremarkable for the wrong
reason.

Buckets are filled round robin, smallest first, so the small groups — Welsh,
Singaporean, Malaysian — are non-empty before the large ones take the remainder.
Bucket sizes are unequal, each is reported **with its *n***, and accent labels
held by fewer than ten source rows are free text ("ohio", "northern cali") and
pool into one bucket rather than each becoming a stratum of one.

**Trace.** `data/commonvoice.py:stratified_sample`, `populated_buckets`;
`data/fetch_assets.py:fetch_commonvoice`; `data/dataset_card.md` §10.
