# Issue 07: wake-word-corpus

Status: done
Blocked by: 02
Session: 03
Closes: 2 classes + >=3 h negatives

## Summary
Synthesize two-class wake-word corpus (swarm hold, swarm abort) with openWakeWord/Piper pipeline and collect >=3 h negatives.

## Deliverables
- Planned for Session 03.
- Closes requirement: 2 classes + >=3 h negatives.

## Comments
- 2026-09-07 (Session 01A): Tracker initialized.
- 2026-09-14 (Session 03): DONE. 3,000 positives (1,500 per class, 3 Piper voices x 20 prosody renditions x 25 augmentations) + 5,040 negatives = **3.50 h** (floor is 3 h). Negatives: LibriSpeech dev-clean, Speech Commands v0.02 test set, and 720 authored near-misses (`swarm`, `hold on`, `storm`, `sworn`) because no public corpus contains them. Split 70/10/20 by BASE RENDITION, negatives by speaker, near-misses by phrase; rooms 70/30 and noise aug|eval so the held-out ROC is not measured on rooms or excerpts the model trained in. Gate 2 now checks all of it. ADR-0005 D3-D5.
