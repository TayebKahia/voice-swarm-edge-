# Step 2 — Dataset Acquisition & Preparation Plan

**Budget: 3–4 days (Week 1, D2–D5), single operator.**

The whole plan rests on one inversion: **generate the label first, then the utterances.** The PDF's
approach — collect utterances, then have two humans annotate them and measure Cohen's κ — is the
standard NLU recipe and it costs ~2 weeks. Inverting it makes labels *correct by construction*, removes
annotation from the critical path entirely, and confines human effort to the one place it actually buys
credibility: the spoken test set.

---

## 1. Target artefacts

| Artefact | Size | Purpose | Cost |
|---|---|---|---|
| `train.jsonl` | ~1,900 pairs | LoRA fine-tuning | automated |
| `val.jsonl` | ~300 pairs | checkpoint selection, early stopping | automated |
| `test_synth.jsonl` | ~300 pairs | held-out synthetic, **unseen templates** | automated |
| `test_golden.jsonl` | **~200 pairs + WAV** | **the reported benchmark** — human speech | ~4 h human |
| `test_ood.jsonl` | ~150 pairs | out-of-domain → `unknown` | automated |
| `audio/` | ~200 human + ~600 TTS WAV × 4 SNR | STT eval, SNR sweep, robustness | ~2 h |
| `wakeword/` | Piper-synthetic positives + public negatives | Branch A reflex | ~2 h |
| `DATASET_CARD.md` | — | provenance, licences, splits, limitations | 1 h |

**Split discipline (non-negotiable):** split by **template family**, not by row. If the same paraphrase
template appears in train and test, your exact-match score is memorisation and a jury will find it in
five minutes. Assign each of the ~120 template families to exactly one split *before* generating.

---

## 2. Intent ontology — 10 classes

Reduced from the PDF's 15 (audit A-8). Each maps 1:1 onto a controller entry point, which is what makes
the ontology defensible: no class exists that the system cannot execute.

| Intent | Slots | Example utterance | Controller action |
|---|---|---|---|
| `formation` | `shape`, `radius?`, `spacing?`, `ids?` | "everyone form a circle five metres wide" | formation slot assignment |
| `move` | `pos?` \| (`dir`+`dist`), `speed?`, `ids?` | "move ten metres north" | migration / point-nav |
| `altitude` | `z`, `ids?` | "climb to four metres" | altitude setpoint |
| `takeoff` | `z?`, `ids?` | "all drones take off" | arm + ascend |
| `land` | `ids?` | "bring them down" | descend + disarm |
| `hover` | `ids?` | "hold position" | zero-velocity hold |
| `abort` | — | "abort" / "emergency stop" | immediate stop (Reflex path) |
| `rotate` | `yaw`, `ids?` | "rotate the formation ninety degrees" | rotate about centroid |
| `set_param` | `speed?`, `spacing?`, `alt?` | "slow down to one metre per second" | parameter update |
| `unknown` | — | "what's the weather" | → `HOVER`, log, no action |

**Canonical units, stated once and never violated:** metres, metres/second, degrees. `ids` absent or
empty ⇒ all drones. `ids` are 0-indexed but *spoken* 1-indexed ("drone one" → `[0]`) — pick one
convention, document it, and encode the mapping in the generator so it is consistent across 2,400 rows.

---

## 3. Synthetic generation — label-first (D2, ~6 h)

### 3.1 The procedure

```
for each intent:
  for each slot-combination valid for that intent:      # from the required-slot matrix
    sample slot VALUES from physical ranges             # programmatic → labels exact
    → gold_json                                         # this IS the label. No annotation.
    ask a frontier model: "give me K=8 distinct ways a
      human operator would say this over a radio"       # → 8 utterances, all sharing gold_json
```

Because the JSON is constructed **before** the text, every label is correct by definition. There is
nothing to annotate and nothing to disagree about. Cohen's κ becomes irrelevant for this 2,400-row bulk
— which is exactly why the golden set (§6) still matters.

### 3.2 Diversity axes to sweep explicitly

Do not let the frontier model choose diversity for you — enumerate it, or you get 2,400 rows of the same
three sentence shapes:

- **Register:** terse radio ("circle, five metres") · conversational ("could you get everyone into a
  circle") · imperative ("form circle radius five") · hesitant ("uh, make a... a circle I guess")
- **Number surface form:** `5` · `five` · `5.0` · `five metres` · `about five` · `5m`
- **Synonym sets:** circle/ring/round/encircle · wedge/V/arrow/vee · line/row/abreast ·
  hover/hold/stay/freeze · abort/stop/kill it/emergency
- **Drone addressing:** all (implicit) · all (explicit "everyone") · single ("drone two") · subset
  ("drones one and three") · range ("drones one through three")
- **Ellipsis / context-free fragments:** "tighter" · "higher" · "faster" — these must map to
  `set_param`, and if you cannot resolve them, to `unknown`. Include both cases deliberately.
- **Disfluency:** filler words, self-correction ("go north — no, south"), partial words.
- **Politeness / prefix noise:** "okay so", "let's have", "I want you to".

### 3.3 Hard negatives (the highest-value 150 rows in the set)

Near-miss pairs that differ in *one* decisive token. These are what separate a model that has learned
the task from one that has learned keyword co-occurrence:

- "circle" → `formation/circle` **vs.** "circle back" → `move` **vs.** "circle around the tree" →
  `unknown` (no object model exists)
- "drop to two metres" → `altitude` **vs.** "drop the payload" → `unknown`
- "line up" → `formation/line` **vs.** "line of sight" → `unknown`
- "stop forming the circle" → `hover` **vs.** "form the circle" → `formation`
- Negated commands: "don't land yet" → `hover`, not `land`. **A model that gets this wrong lands a
  swarm on a "don't land" command** — worth a dedicated slide at the defence.

### 3.4 Out-of-domain set (~150 rows → `unknown`)

Four sources, roughly equal weight: (a) unrelated smart-assistant queries — mine these from **MASSIVE**
(§5) rather than inventing them; (b) drone-adjacent but unsupported ("take a photo", "follow me",
"return to base" if unimplemented); (c) ASR garbage — actual Whisper output on noise/silence; (d)
truncated fragments ("form a", "move to").

Category (c) matters most: it is the only way the model learns what its *own* front-end produces on
failure. Collect it by running Whisper over silence, propeller noise, and clipped speech.

---

## 4. ASR round-trip augmentation (D3, ~4 h) — the critical step

**This is the fix for audit finding C-2's distribution shift**, and it is the single highest-leverage
item in the dataset plan. Training on clean text and inferring on Whisper output is a train/test
mismatch that silently costs 10–20 points of exact-match.

```
gold_json ──► clean_transcript ──► Piper TTS ──► mix noise @ SNR ──► whisper.cpp ──► noisy_transcript
     └───────────────────────────────────────────────────────────────────────────────────┘
                    pair the NOISY transcript with the ORIGINAL gold_json
```

Fully automated, runs unattended, and produces training text with *the exact error distribution of your
deployed STT model* — not a hand-crafted approximation of it.

**Composition of the final training set:**

| Variant | Share | Rationale |
|---|---|---|
| Clean transcript | 50% | the well-conditioned case |
| ASR round-trip @ 20 dB | 20% | mild degradation |
| ASR round-trip @ 10 dB | 15% | realistic operating point |
| ASR round-trip @ 5 dB | 10% | stress; teaches the model to prefer `unknown` over guessing |
| Hand-injected perturbation | 5% | homophones, dropped articles, lowercase/no-punctuation (Whisper's output style) |

**Two guards.** (i) De-duplicate — round-tripping often returns the clean string, and near-duplicates
inflate your effective epoch count. (ii) If a round-trip destroys the utterance beyond human
recognition, relabel it `unknown` rather than keeping a corrupt→command pair. Automate the check with a
character-level similarity threshold and eyeball the rejects once.

---

## 5. Public datasets to adapt

Use these for the parts that are expensive to create and cheap to borrow — noise, negatives, and
methodological precedent. **Verify each licence before redistribution** (I have not re-checked these
against current terms; treat the licence column as a starting point, not a clearance).

| Dataset | Use here | Licence (verify) |
|---|---|---|
| **MASSIVE** (Amazon, 60 intents, slot-filled, 51 langs) | Primary OOD-negative source; precedent for joint intent+slot JSON formatting | CC-BY-4.0 |
| **SNIPS NLU benchmark** (7 intents, slots) | Methodological baseline to cite for the intent+slot formulation | CC0 / permissive |
| **ATIS** | Classic slot-filling citation; do not use the data, cite the framing | research use |
| **Google Speech Commands v2** | Contains `stop`, `go`, `up`, `down`, `left`, `right`, `on`, `off`, `yes`, `no` — directly useful as **wakeword negatives** and as single-word command sanity checks | CC-BY-4.0 |
| **Fluent Speech Commands** | Closest audio analogue (action–object–location intent triplets) | requires a signed agreement — **check before relying on it** |
| **ESC-50** | Contains `helicopter` and `engine` classes → propeller-noise proxy | CC-BY-NC |
| **MUSAN** / **DEMAND** | Ambient/babble/background noise for the SNR sweep | permissive / CC |
| **DREGON** (Inria) | Actual UAV ego-noise recorded on a flying drone — the *right* citation for propeller noise | research use |
| **MIT RIR** survey | Room impulse responses; this is what openWakeWord's own augmentation pipeline uses | permissive |
| **LibriSpeech** / **Common Voice** | Ambient-speech negatives for the wakeword (false-activation hardening) | CC-BY-4.0 / CC0 |

**On propeller noise specifically.** The PDF correctly insists on *recorded* rather than Gaussian noise
(propeller noise has periodic harmonic structure Gaussian does not reproduce — a good point, keep it in
the thesis). But you own no drone. Order of preference: DREGON → ESC-50 `helicopter` → record any hobby
quadcopter or even a bench fan at 3 distances and document it as an approximation. **State which you
used.** An honest approximation, labelled, is worth more than an unsourced claim of authenticity.

---

## 6. Golden set — the reported benchmark (D4–D5, ~4 h)

Everything above is automated and therefore cheap and therefore *not* fully persuasive. The golden set
is the part that makes the results real.

**Composition:** ~200 utterances covering all 10 intents (≥15 each) and every slot type, spoken by
**3–4 speakers** (you + classmates; mixed accent and gender if possible), recorded on the actual USB mic
at the actual sample rate, in **two conditions**: quiet room and with a noise source running.

**Protocol:**
1. Sample 200 `gold_json` rows from held-out template families. Print the *utterances*, not the JSON.
2. Each speaker reads their subset naturally — no rehearsing to sound like the training data.
3. Record 16 kHz mono WAV, one file per utterance, filename = row ID.
   **Recording device:** any device works — the recorder need not be the Pi, and no experiment requires
   live capture (all use WAV injection). If recording off-device, **disable AGC / noise suppression /
   "voice enhancement"** where the OS allows it, and **name the capture device in the dataset card**:
   consumer laptop processing yields audio cleaner than raw USB PCM, which makes WER and CRR optimistic.
   Prefer a Pi-attached USB mic once acquired, at a natural ~50 cm distance rather than a headset boom.
4. Transcribe with `whisper.cpp tiny.en` and **store the ASR output alongside the human reference.**
   This gives you WER for free and it is what the NLU actually receives.
5. **Agreement (audit B-6):** one classmate independently labels a 50-row subsample from audio alone
   using the published ontology; compute Cohen's κ on the 10-way intent label. Target κ ≥ 0.8. This is
   90 minutes of someone's time and it converts "I made a dataset" into "I validated a dataset."

**Never train on the golden set. Never tune on it. Report it once, at the end.**

---

## 7. Schema v1.0 — the frozen contract

Freeze this on **D1, before any data generation**. Everything — generator, validator, grammar, trainer,
controller, thesis tables — depends on it. Changing it on D6 means regenerating the dataset.

### 7.1 Wire format

Fixed key order, **null fields omitted entirely**. Omitting nulls rather than emitting
`"formation_shape": null` (as the PDF's schema does) cuts a typical command from ~40 tokens to ~18 —
which, at Pi 5 decode rates, is **roughly a full second of latency per command, for free.** This is the
second-largest latency win in the project after the prefill fix.

```json
{"intent":"formation","shape":"circle","radius":5.0}
{"intent":"move","pos":[10.0,0.0,3.0],"speed":1.5}
{"intent":"move","dir":"north","dist":10.0}
{"intent":"altitude","z":4.0,"ids":[1,2]}
{"intent":"rotate","yaw":90.0}
{"intent":"set_param","speed":1.0}
{"intent":"hover"}
{"intent":"abort"}
{"intent":"unknown"}
```

### 7.2 GBNF grammar (llama.cpp)

```gbnf
root      ::= cmd
cmd       ::= c-form | c-move | c-alt | c-takeoff | c-land | c-hover | c-abort | c-rot | c-param | c-unk

c-form    ::= "{\"intent\":\"formation\",\"shape\":" shape o-radius o-spacing o-ids "}"
c-move    ::= "{\"intent\":\"move\","  ( kv-pos | kv-dir ) o-speed o-ids "}"
c-alt     ::= "{\"intent\":\"altitude\",\"z\":" num o-ids "}"
c-takeoff ::= "{\"intent\":\"takeoff\""  o-z o-ids "}"
c-land    ::= "{\"intent\":\"land\""     o-ids "}"
c-hover   ::= "{\"intent\":\"hover\""    o-ids "}"
c-abort   ::= "{\"intent\":\"abort\"}"
c-rot     ::= "{\"intent\":\"rotate\",\"yaw\":" num o-ids "}"
c-param   ::= "{\"intent\":\"set_param\"" o-speed o-spacing o-alt "}"
c-unk     ::= "{\"intent\":\"unknown\"}"

shape     ::= "\"circle\"" | "\"line\"" | "\"wedge\"" | "\"grid\"" | "\"column\"" | "\"flock\""
dir       ::= "\"north\"" | "\"south\"" | "\"east\"" | "\"west\"" | "\"up\"" | "\"down\""
            | "\"forward\"" | "\"back\"" | "\"left\"" | "\"right\""

kv-pos    ::= "\"pos\":[" num "," num "," num "]"
kv-dir    ::= "\"dir\":" dir ",\"dist\":" num

o-radius  ::= ( ",\"radius\":"  num )?
o-spacing ::= ( ",\"spacing\":" num )?
o-speed   ::= ( ",\"speed\":"   num )?
o-alt     ::= ( ",\"alt\":"     num )?
o-z       ::= ( ",\"z\":"       num )?
o-ids     ::= ( ",\"ids\":[" idlist "]" )?
idlist    ::= [0-9] ( "," [0-9] )*

num       ::= "-"? [0-9] [0-9]? [0-9]? ( "." [0-9] )?
```

The `num` rule caps at 3 integer digits + 1 decimal — this is what structurally prevents `1e999`,
20-digit integers, and bare `2.` (audit C-2). **GBNF cannot express numeric ranges**, only digit counts;
range enforcement is the validator's job, below.

### 7.3 Semantic validator (Pydantic) — layer 2

The grammar guarantees shape. This guarantees meaning. Both are mandatory.

- **Required-slot matrix:** `formation` requires `shape`; `circle` requires `radius`; `line`/`grid`/
  `column` require `spacing`; `altitude` requires `z`; `move` requires exactly one of `pos` or
  (`dir`+`dist`); `rotate` requires `yaw`; `set_param` requires ≥1 slot.
- **Physical envelope, clamp-and-log (never reject):** `radius ∈ [1, 10]` m · `spacing ∈ [1, 5]` m ·
  `z ∈ [0.5, 15]` m · `speed ∈ [0.2, 2.0]` m/s · `|pos| ≤ 50` m · `yaw ∈ [-180, 180]` deg.
- **`ids ⊆ {0..N-1}`**; unknown IDs dropped with a log line; empty after filtering ⇒ all drones.
- **Fallback:** any validation failure, parse failure, or `max_tokens` truncation ⇒ `HOVER` + structured
  log entry. Never a movement command.

### 7.4 Training record format

```json
{
  "id": "form_circle_0412",
  "template_family": "F07",
  "split": "train",
  "variant": "asr_10db",
  "transcript": "everyone get into a circle about five meters across",
  "target": "{\"intent\":\"formation\",\"shape\":\"circle\",\"radius\":5.0}",
  "gold_intent": "formation",
  "audio_path": null,
  "snr_db": 10
}
```

At fine-tuning time this is rendered through each model's own chat template with **loss on the
completion only** (`target`), never on the prompt — see `03_model_pipeline.md` §3.

---

## 8. Day-by-day

| Day | Work | Output |
|---|---|---|
| **D1** | Freeze schema v1.0. Write Pydantic validator + GBNF + adversarial grammar unit tests. Assign 120 template families to splits. | `schema.py`, `cmd.gbnf`, `test_grammar.py` green |
| **D2** | Label-first generation: 2,400 pairs across 10 intents. Hard negatives. OOD set. | `raw_pairs.jsonl` |
| **D3** | Piper TTS → noise mix (4 SNR) → whisper.cpp round-trip. De-dup. Assemble train/val/test_synth. | `train/val/test_synth.jsonl` |
| **D4** | Golden set: record 200 utterances × 3–4 speakers, two conditions. Transcribe. | `audio/`, `test_golden.jsonl` |
| **D5** | κ subsample with a classmate. Wakeword set via openWakeWord's Piper pipeline. `DATASET_CARD.md`. **Freeze.** | κ reported, dataset v1.0 tagged |

**Freeze means freeze.** Tag it in git. If Week 3 reveals a schema gap, you note it as future work — you
do not regenerate, because regenerating invalidates every number you have already measured.

---

## 9. Honest limitations to state in the thesis

Write these yourself, before the jury does. Each is a limitation, not a flaw — a labelled limitation
reads as rigour.

1. The bulk training set is **synthetic**; linguistic diversity is bounded by the generating model's
   priors. Mitigated by enumerated diversity axes (§3.2) and by reporting on **human** speech (§6).
2. Bulk audio is **TTS**, which lacks the prosody, breath, and channel variation of live speech. All
   reported CRR/WER figures come from the human golden set; TTS audio is used for development and for
   the SNR sweep only.
3. Propeller noise is a **public-corpus or bench approximation**, not near-field acoustic coupling on a
   flying airframe.
4. The golden set is **~4 speakers** — too few to claim speaker independence. Report per-speaker
   breakdown so the variance is visible rather than hidden in an average.
5. Labels for the synthetic set are correct **by construction**, so κ measures annotator agreement only
   on the golden set. State this explicitly rather than implying κ covers the whole corpus.
6. **English only.**
