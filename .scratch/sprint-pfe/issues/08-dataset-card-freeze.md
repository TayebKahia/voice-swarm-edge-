# Issue 08: dataset-card-freeze

Status: done
Blocked by: 04,05,06,07
Session: 03
Closes: Gate 5 (tag dataset-v1.0)

## Summary
Document noise floor, capture device, noise corpora, split policy, and single-speaker framing in data/dataset_card.md. Freeze and tag dataset-v1.0.

## Deliverables
- Planned for Session 03.
- Closes requirement: Gate 5 (tag dataset-v1.0).

## Comments
- 2026-09-07 (Session 01A): Tracker initialized.
- 2026-09-14 (Session 03): card SS1/SS3/SS5 TBDs filled, SS7 rewritten with generated markers, SS9 (wake corpus) and SS10 (Exp-0) added. Remaining TBDs are the three that cannot be filled before the human runs: agreement, disagreements, and the freeze commit SHA. **Blocked on 05 and 06.**
- 2026-09-18 (Session 03): **DONE.** Every TBD that could be filled is filled; SS7's generated block waits on pass 2 (Sun 20 Sep) and SS8's commit SHA is self-describing via `git rev-parse dataset-v1.0^{commit}`. Gate 5 tagged.
