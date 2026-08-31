# Issue 08: whole-documents (Master)

Status: ready-for-agent
Blocked by: 01, 02, 03, 04, 05, 09
Documents: thesis/main_master.tex

## What

Template B of `docs/agents/thesis-chapter-review.md`, for the Master: RQ traceability through
every chapter, headline numbers identical across the three abstracts and all chapters, definitions
consistent, forward references true, write-once across the two documents, front matter, clean build.

The write-once check (Template B item 7) compares against the Ingénieur chapters as they stand
now. Issue 10 repeats it once the Ingénieur is complete.

Split 2026-09-24: this issue covered both documents, so the unwritten Ingénieur Ch2 (issue 07)
blocked the finished Master. The Ingénieur pass is now `issues/10-whole-document-ingenieur.md`.

## Agents

One reviewer + verifier. Not split by dimension: this pass exists to see every chapter at once.

## Before running

Re-run every chapter script (all must be 0 FAIL) and `tools/review/selftest.py`.

## Comments

- Added 2026-09-23 (from issue 01): **scope check.** Could a reader who has only this document
  state the system end to end, what is simulated, the language, the command vocabulary, what is
  out of scope, and how the work divides between the two theses? A per-chapter review against
  the section list does not ask this.
