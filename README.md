# Voice-Controlled Drone Swarm on the Edge

Offline natural-language control of a drone swarm, running entirely on a
**Raspberry Pi 5 (8 GB)** with no network connection. Spoken English commands
become validated JSON swarm primitives; the swarm executes them in simulation.

Final-year project (PFE), **École Supérieure en Informatique — Sidi Bel Abbès**,
specialty **IASD**. Supervisor: Prof. Belkacem Khaldi.
Two theses from one system: *Mémoire de Master* (research) and
*Mémoire d'Ingénieur d'État* (engineering).

**The specification is [`docs/PRD.tex`](docs/PRD.tex).** It is the contract —
requirements, gates, dated schedule, experiments, statistics. This README only
tells you where things live and how to run them.

---

## How it works

Two paths, deliberately separated by latency:

**Branch B — the language path** (2,500 ms p95 from end of speech)
Silero VAD endpointing → `whisper.cpp tiny.en` → fine-tuned SLM with GBNF-constrained
decoding → Pydantic validator → command bus.

**Branch A — the reflex path** (≤150 ms from keyword offset)
A two-class spotter for `swarm hold` and `swarm abort` only. Bypasses speech
recognition and the language model entirely, and preempts Branch B by sequence
number. Only two intents qualify: both make the swarm do *less*, so a false
accept is always fail-safe.

Three validation layers guard the output: **GBNF** (structure) → **Pydantic**
(meaning; clamps and logs, never rejects) → **flight state machine** (legality).

---

## Layout

One folder per stage of the journey a spoken command takes.

| Path | Contents |
|---|---|
| `docs/` | The PRD, feasibility audit, dataset plan, model pipeline note |
| `schema/` | `schema.py`, `cmd.gbnf`, `validate.py`, `canon.py`, `test_grammar.py`, `test_canon.py` |
| `data/` | `raw_pairs.jsonl`, the five splits, `audio/`, `wake/`, `mix_noise.py`, `check_leakage.py`, `dataset_card.md` |
| `train/` | LoRA scripts, one config per model, training logs |
| `gguf/` | Six quantised artefacts plus `LICENSE_MODELS.md` |
| `runtime/` | `audio.py`, `vad.py`, `stt.py`, `branch_a.py`, `parser.py`, `bus.py`, entry point |
| `swarm/` | `fsm.py`, `control.py`, `env_numpy.py`, `env_pyflyt.py`, `test_fsm.py` |
| `eval/` | `bench.py`, `norm.py`, `stats.py`, `plots.py`, `test_template_parity.py` |
| `results/` | `exp0.csv` … `exp4.csv` — every raw trial, committed |
| `thesis/` | `master/` and `ingenieur/`, each with its own cover page and bibliography |
| `tools/` | `check_tex.py`, `build_pdf.py` — LaTeX pre-flight and compile driver |
| `build/` | Compiled PDFs. Overwritten every compile; never edit anything here |

`schema/` is imported by `data/`, `train/`, `runtime/`, and `eval/`. It is the
one place a valid command is defined. Duplicating any part of it elsewhere
produces a silent accuracy collapse with no error message.

### Where `data/` goes

```
data/
  raw_pairs.jsonl        label-first generated pairs
  train_synth.jsonl      ~1,900   LoRA fine-tuning
  val_synth.jsonl        ~250     checkpoint selection on exact match
  test_synth.jsonl       ~250     Exp-1, the McNemar paired sample
  test_golden.jsonl      200      headline accuracy + all of Exp-3
  test_ood.jsonl         ~150     NFR-18 false-command rate
  audio/
    s1/                  200 files   quiet room                    (D4)
    s2/                   60 files   different room, real noise     (D5)
    s3/                   60 files   same 60 items, different day   (D5)
    tts/  mixed/  roundtrip/         derived — regenerated, not committed
  wake/                  two positive classes + >=3 h negatives
  noise/  commonvoice/   downloaded; URLs and licences in dataset_card.md
  annot/                 annot_pass1.jsonl (sealed D5), annot_pass2.jsonl (D15)
```

**Filenames are join keys.** `0042.wav` is the same utterance in `s1/`, `s2/`,
and `s3/`, and `0042` is its line in `test_golden.jsonl`. Sessions 2 and 3 hold
a 60-item subset of session 1's IDs.

Splits are assigned **by template family**, never row-wise: every paraphrase
descended from one label lands in the same split. `check_leakage.py` enforces
this and is a gate, not a report.

---

## Running it

Reproduce every table and figure from frozen data:

```bash
./run_all.sh
```

Run the live pipeline on the Pi:

```bash
./run_pipeline.sh
```

Recover from the `ABORTED` state — explicit, manual, and non-vocal by design:

```bash
./run_pipeline.sh --reset
```

Build the PRD (run from the repository root):

```bash
python tools/build_pdf.py
```

Structural check on the LaTeX with no TeX engine needed:

```bash
python tools/check_tex.py docs/PRD.tex
```

---

## Setup

```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

`llama.cpp` and `whisper.cpp` are built from source, not installed with pip.
Their commit SHAs are recorded in the spike S1 and S2 reports.

---

## What is committed

Sources are committed; derivatives are regenerated. The 320 recordings in
`data/audio/s1..s3/` cannot be recreated — losing them costs a full recording
day and the numbers still would not match. The 1.2 GB of SNR mixes can be
rebuilt in minutes by `data/mix_noise.py`, so they are ignored.

Noise is added **digitally** from session 1's clean audio. That is what makes
noise a knob rather than a recording session, and it is what licenses the causal
claim in Exp-3.

Every number in either thesis traces to a CSV in `results/`. No figure is
hand-edited.

---

## Scope

The golden set is **one speaker — the author**. This is an internal-validity
choice: holding the speaker fixed makes noise the only varying factor in Exp-3.
It is never presented as speaker independence. External validity at the acoustic
model is recovered by Exp-0 on Mozilla Common Voice.

Annotation agreement is **intra**-annotator: 50 items labelled at D5, sealed,
then relabelled cold at D15. It measures schema stability, not schema clarity.
