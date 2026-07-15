# STATE
Session: 02A (Wed 9 Sep, PRD D2)
Last updated: 2026-09-09T16:15:00+01:00

## Gates
Gate 1 schema        : GREEN (pytest schema/ → 83 passed in 0.20s, tag schema-v1.1)
Gate 2 leakage       : READY (check_leakage.py --strict → exit 0, 0 near-duplicates; Session 02B formal gate)
Gate 3 parity        : PENDING (Session 05B)
Gate 4 fsm           : PENDING (Session 08; Table 9 legality & grounded rejection verified in swarm/test_fsm.py)
Gate 5 dataset frozen: PENDING (Session 03)
D1 Environment Gate  : GREEN (requirements.txt pinned, environment.yml exported)

## Artefacts
schema/                     : FROZEN (cmd.gbnf, schema.py, validate.py, canon.py, logger.py, test_grammar.py, test_canon.py)
                              - cmd.gbnf: verbatim from §2.3
                              - schema.py: 10 intent Pydantic models, declaration order fixes key order, nulls omitted
                              - validate.py: Layer 2 validator, slot matrix, clamp-and-log, pos.z ceiling/floor & norm clamp, yaw periodic wrapping, non-finite (NaN/Inf) rejection to HOVER, structured logging
                              - canon.py: canonicaliser rule 1-5, single comparator helper canon_equal(), non-finite protection, total id handling
                              - logger.py: structured JSON lines logging with LogRecord extra field preservation
                              - test_grammar.py: 72 tests (adversarial corpus, Layer 2 overflow/non-finite handling, all clamp boundaries from both sides, yaw wrapping)
                              - test_canon.py: 8 tests (rules 1-5, banker's rounding on dyadic fractions, canon_equal equivalence)
swarm/                      : fsm.py (Table 9 legality, grounded no-op on rejection in LANDED, airborne HOVER fallback), test_fsm.py (19 tests passing)
docs/adr/                   : 0001_physical_envelope_analogies.md, 0002_fsm_grounded_rejection_and_canon_helpers.md, 0003_surface_form_conventions.md
data/template_families.json : SYNCHRONIZED (120 families: 96 train [80%], 12 val [10%], 12 test_synth [10%]; enum coverage verified in train; formation size slot constraints verified per Table 14)
data/template_families.py   : AUTHORED (dataclass, split assignments, schema validation)
data/harvest_asr_garbage.py : AUTHORED & HARVESTED (20 stimuli synthesized: silence, tone, rotorwash, gusts, rumbles; processed with whisper.cpp tiny.en; 12 distinct hallucinations)
data/asr_garbage.json       : HARVESTED (20 stimuli records from whisper-cli on noise/silence)
data/surface_forms.py       : AUTHORED (realisation engine with all 7 diversity axes: register, number forms, addressing modes, disfluency, politeness, ellipsis, synonyms)
data/hard_negatives.py      : AUTHORED (155 contrast rows across 20 groups; negation -> hover, abort exempt)
data/ood.py                 : AUTHORED (150 eval-only OOD rows across 4 quarters: MASSIVE, drone-adjacent unsupported, whisper ASR garbage, truncated fragments)
data/generate.py            : AUTHORED (seed 42 deterministic generator, cross-split Jaccard filtering < 0.85, non-singleton paraphrase grouping)
data/raw_pairs.jsonl        : GENERATED (2,421 rows: 1,941 train [80.2%], 240 val [9.9%], 240 test_synth [9.9%])
data/test_ood.jsonl         : GENERATED (150 rows)
data/test_golden.jsonl      : GENERATED (200 held-out rows across all 10 intents)
data/test_golden_transcripts.txt: GENERATED (200 sequential `<id>\t<transcript>` lines for Session 03 audio recording)
data/check_grammar.py       : AUTHORED & VERIFIED (2,771 labels accepted by cmd.gbnf, 0 rejected)
data/check_leakage.py       : AUTHORED & VERIFIED (template family integrity & cross-split surface-form near-duplicate lexical leakage check)
data/test_generate.py       : AUTHORED (110 tests passing)
data/test_template_families.py: AUTHORED (6 tests passing)
spikes/s0..s7 scripts       : 8 scripts authored in spikes/
spikes/reports/S0..S7.md    : 8 spike reports in spikes/reports/
requirements.txt            : PINNED (all dependencies pinned with ==, conda header updated)
environment.yml             : EXPORTED (conda env pfe_swarm)
.scratch/sprint-pfe/spec.md : AUTHORED (16-day sprint plan, cut ladder, milestones)
.scratch/sprint-pfe/issues/ : Issue 01, 02, 03 resolved; 23 pending human.

## Decisions this session
- Session 02A synthetic data generation implementation:
  1. Fixed slot patterns for F002, F007, F012, F016: restored required `radius` on `circle` and `spacing` on `line`, `grid`, `column` per PRD Table 14 and Layer 2 validation matrix, removing unrepresentable `speed` slot without dropping required geometric size slots.
  2. Implemented automated harvesting of real ASR noise hallucinations using local `whisper-cli` and `ggml-tiny.en.bin` over 20 synthesized acoustic stimuli (silence, room tone, rotorwash, gusts, rumbles).
  3. Aligned `generate.py` leakage checking with `check_leakage.py`'s 2-gram and token Jaccard similarity metrics (max(token, 2-gram) < 0.85), ensuring zero cross-split near-duplicate leakage.
  4. Resolved global transcript uniqueness by seeding generator's `seen` set with authored contrast and unknown rows.
  5. Prevented singleton paraphrase samples when partitioning family budgets.
  6. Generated 2,421 `raw_pairs.jsonl`, 150 `test_ood.jsonl`, 200 `test_golden.jsonl`, 200 `test_golden_transcripts.txt`.
  7. Authored ADR-0003 (`docs/adr/0003_surface_form_conventions.md`) documenting semantic conventions (CCW yaw, diameter phrasing, hover negation, ellipsis).
  8. All 235 pytest tests pass; Gate FR-1 and Gate 2 strict checks pass cleanly.

## Blocked / needs human
- Autorisation de soutenance: Requested Sep 6, pending formal receipt (tracked in Issue 24).

## Next session starts with
Session 02B Task 1. Audio pipeline: author `data/mix_noise.py`, TTS synthesis (`piper` / `kokoro`), SNR mixing with rotorwash / room noise, audio augmentation, and round-trips.


