# Issue 10: whole-document-ingenieur

Status: ready-for-agent
Blocked by: 06, 07
Documents: thesis/main_ingenieur.tex

## What

Template B of `docs/agents/thesis-chapter-review.md`, for the Ingénieur: RQ traceability through
every chapter, headline numbers identical across the three abstracts and all chapters, definitions
consistent, forward references true, write-once across the two documents, front matter, clean build.

This issue was split from issue 08 on 2026-09-24, so that the unwritten Ingénieur Ch2 no longer
blocked the finished Master. Issue 08's write-once check was made against the Ingénieur as it stood
then; repeat it here against the complete document.

**The Blocked-by line is incomplete.** Ingénieur Ch3 (`ch3_architecture.tex`) and Ch6
(`ch6_conclusion.tex`) exist but have no review issues, and Ch4 and Ch5 are unwritten. Add each
chapter's issue to Blocked-by when it is created.

## Agents

One reviewer + verifier. Not split by dimension: this pass exists to see every chapter at once.

## Before running

Re-run every chapter script (all must be 0 FAIL) and `tools/review/selftest.py`.

## Comments

- Carried from issue 08 (added there 2026-09-23, from issue 01): **scope check.** Could a reader
  who has only this document state the system end to end, what is simulated, the language, the
  command vocabulary, what is out of scope, and how the work divides between the two theses? A
  per-chapter review against the section list does not ask this.
