# Issue 03: synthetic-generation

Status: closed
Blocked by: 02
Session: 02A
Closes: raw_pairs.jsonl, all labels grammar-accepted

## Summary
Label-first synthetic dataset generation covering 7 diversity axes, hard negatives, and OOD sources. Author 200 golden transcripts.

## Deliverables
- `data/generate.py`: Deterministic label-first synthetic generator under seed 42.
- `data/surface_forms.py`: Realisation engine covering all 7 diversity axes (register, number form, addressing, disfluency, politeness, ellipsis, synonyms).
- `data/hard_negatives.py`: 155 decisive-token contrast rows across 34 group lists / 38 distinct group labels (`_NEGATION` is one list carrying five labels) (negations -> hover, abort exempt).
- `data/ood.py`: 150 eval-only OOD rows across 4 quarters (MASSIVE assistant queries, drone-adjacent unsupported, whisper ASR garbage, truncated fragments).
- `data/harvest_asr_garbage.py`: Stimuli synthesis and automated whisper.cpp tiny.en harvesting.
- `data/asr_garbage.json`: 20 stimuli harvested from whisper-cli on noise/silence.
- `data/raw_pairs.jsonl`: 2,421 rows (1,941 train [80.2%], 240 val [9.9%], 240 test_synth [9.9%]).
- `data/test_ood.jsonl`: 150 rows.
- `data/test_golden.jsonl`: 200 held-out rows covering all 10 intents.
- `data/test_golden_transcripts.txt`: 200 sequential lines (`<id>\t<transcript>`) for human recording in Session 03.
- `data/check_grammar.py`: Grammar gate runner cross-checking all datasets against `schema/cmd.gbnf`.
- `docs/adr/0003_surface_form_conventions.md`: Surface-form semantic conventions (CCW yaw, diameter phrasing, hover negation, ellipsis).

## Verification & Gates

### Gate FR-1: cmd.gbnf Acceptance (`python data/check_grammar.py`)
```
grammar: /home/kahia-tayeb/PFE/schema/cmd.gbnf
  raw_pairs.jsonl               2421 labels  all accepted
  test_golden.jsonl              200 labels  all accepted
  test_ood.jsonl                 150 labels  all accepted

data/gbnf.py: 2771 labels checked, 441 distinct, 0 rejected

llama-gbnf-validator: NOT FOUND --- the gate rests on data/gbnf.py alone.
  Build llama.cpp (or set LLAMA_CPP_DIR) and re-run to cross-check against
  the parser that constrains decoding at inference time.

GATE PASS --- 2771 labels accepted by: data/gbnf.py
```

### Gate 2 Split Leakage & Integrity (`python data/check_leakage.py --strict`)
```
Running Gate 2 split leakage verification...
[+] Template family integrity: PASS (120 families: 96 train, 12 val, 12 test_synth)
[*] Inspecting raw_pairs.jsonl for leakage...
    2421 rows: 1941 train, 240 val, 240 test_synth
[+] Split isolation (train vs val): PASS (240 rows, 0 overlaps, 0 near-duplicates)
[+] Split isolation (train vs test_synth): PASS (240 rows, 0 overlaps, 0 near-duplicates)
[+] Split isolation (train vs test_golden): PASS (200 rows, 0 overlaps, 0 near-duplicates)
[+] Eval independence (val vs test_synth): PASS (240 rows, 0 exact matches, 0 near-duplicates)
[+] Eval independence (val vs test_golden): PASS (200 rows, 0 exact matches, 0 near-duplicates)
[+] Eval independence (test_synth vs test_golden): PASS (200 rows, 0 exact matches, 0 near-duplicates)

[+] Gate 2 verification SUCCESSFUL: No leakage detected.
```

### Test Suite (`pytest -v`)
```
============================= 237 passed in 0.97s ==============================
```

## Comments
- 2026-09-07 (Session 01A): Tracker initialized.
- 2026-09-09 (Session 02A): Reviewed and resolved Session 02A blockers:
  1. Fixed slot patterns for F002, F007, F012, F016: restored required `radius` on `circle` and `spacing` on `line`, `grid`, `column` (omitting unrepresentable `speed` per Layer 2 required-slot matrix). Re-synchronized `data/template_families.json`.
  2. Harvested actual whisper.cpp output on 20 synthesised noise/silence stimuli into `data/asr_garbage.json`.
  3. Resolved transcript collision in `generate.py` by sharing `seen` transcripts across authored, OOD, raw_pairs, and golden sets.
  4. Implemented full parity with `data/check_leakage.py` in `generate.py` (word token and 2-gram Jaccard similarity), ensuring 0 cross-split near-duplicate lexical leakage (Jaccard < 0.85).
  5. Prevented singleton paraphrase samples when family budget leaves remainder 1.
  6. Generated all deliverables: `data/raw_pairs.jsonl` (2,421 rows), `data/test_ood.jsonl` (150 rows), `data/test_golden.jsonl` (200 rows), `data/test_golden_transcripts.txt` (200 lines). All gates green. Closed.

