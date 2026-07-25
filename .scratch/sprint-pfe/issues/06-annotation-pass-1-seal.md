# Issue 06: annotation-pass-1-seal

Status: done
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
- 2026-09-18 (Session 03): scope changed to **B'** after the interval collapsed to 2 days (depot Mon 21 Sep). **No agreement rate will be reported.** At 2 days a matching pair of labels is as easily recall as schema clarity, so a percentage would measure memory. Only the items the two passes label DIFFERENTLY are reported -- recall can push the passes together but never apart, so a disagreement is evidence of schema ambiguity at any interval. The count is stated as a lower bound, and a zero count is stated as not being a positive result. prd.md SS9.3 / Limitations / R-9 / Table 25, PRD.tex (6 substitutions) and dataset_card.md SS7 all rewritten; `annotate.py card_block` no longer renders a rate (4 new tests pin that). Pass 1 still to be run by the human.
- 2026-09-18 23:41 (Session 03): **PASS 1 DONE AND SEALED.** 50/50 labels, all schema-valid, ids match the stratified subset exactly, no blanks. SHA-256 f1a1fe6c2fd7f6807b456ff9877cc8cef1126f7777dbd0894b48198ae8144e2f, verified intact after sealing. Two envelope clamps fired on real authored utterances (z -7.4 -> 0.5, dist 77 -> 50), which is the clamp-and-log path being exercised by human input rather than only by synthetic tests -- worth citing in the thesis. Pass 2 due Sun 20 Sep.
