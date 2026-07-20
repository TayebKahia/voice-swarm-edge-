# Issue 06: annotation-pass-1-seal

Status: blocked-on-human
Blocked by: 05
Session: 03
Closes: annot_pass1.jsonl sealed (fuse starts)

## Summary
Label 50 golden utterances against schema, produce annot_pass1.jsonl and seal it immediately to start the 10-day test-retest fuse.

## Deliverables
- Planned for Session 03.
- Closes requirement: annot_pass1.jsonl sealed (fuse starts).

## Comments
- 2026-09-07 (Session 01A): Tracker initialized.
- 2026-09-14 (Session 03): `data/annotate.py` written and tested (16 tests). Subset of 50 is stratified 5-per-intent so `abort` cannot be absent. Seal is a SHA-256; an incomplete pass cannot be sealed, pass 2 cannot open before the seal, and neither pass sees the generated target. **Interval shortened 10 -> 6 days** (seal Sun 14 Sep, pass 2 Sun 20 Sep); `prd.md` SS9.3 / Limitations / R-9 / Table 25 and `PRD.tex` edited to match, direction of bias stated. ADR-0005 D6. **Blocked on issue 05.**
