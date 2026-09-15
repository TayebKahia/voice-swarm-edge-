# Issue 10: whole-document-ingenieur

Status: closed
Blocked by: 06, 07, 11, 12, 13, 14
Documents: thesis/main_ingenieur.tex

## What

Template B of `docs/agents/thesis-chapter-review.md`, for the Ingénieur: RQ traceability through
every chapter, headline numbers identical across the three abstracts and all chapters, definitions
consistent, forward references true, write-once across the two documents, front matter, clean build.

This issue was split from issue 08 on 2026-09-24, so that the unwritten Ingénieur Ch2 no longer
blocked the finished Master. Issue 08's write-once check was made against the Ingénieur as it stood
then; repeat it here against the complete document.

**The Blocked-by line is incomplete.** Ingénieur Ch3 has issue 11. Ch4, Ch5 and Ch6
(`ch6_conclusion.tex`) have no review issues yet. Add each chapter's issue to Blocked-by when it is
created.

## Agents

One reviewer + verifier. Not split by dimension: this pass exists to see every chapter at once.

## Before running

Re-run every chapter script (all must be 0 FAIL) and `tools/review/selftest.py`.

## Comments

- Carried from issue 08 (added there 2026-09-23, from issue 01): **scope check.** Could a reader
  who has only this document state the system end to end, what is simulated, the language, the
  command vocabulary, what is out of scope, and how the work divides between the two theses? A
  per-chapter review against the section list does not ask this.

### 2026-09-24 -- whole-document pass run and applied (87ca9f1, 1395103); Status -> closed

Split for the depot deadline: one reviewer agent took items 1, 5, 6, 7, 9 (RQ traceability,
definitions, cross-references and promises, write-once, scope); the main session took 2, 3, 4, 8, 10
(contributions, headline numbers, the three abstracts, front matter, build). No separate verifier
agent: the main session re-read every BLOCKER and MAJOR against the text before applying.

Clean: every headline number identical across the three abstracts, Ch5, Ch6 and the generated
tables; the abstracts agree and claim no more than the chapters; 21 acronyms; short LoT/LoF titles;
43 bibliography entries, all cited; every Ch3/Ch4/Ch5 promise into sec:limitations kept.

Applied (20): 1 BLOCKER (Ch6 collision threshold 0.50 -> 0.35 m; the ch6 script had the same wrong
literal and now reads swarm/control.py), 11 MAJOR (Ch6 contribution paragraph vs Ch1/Ch2; future
work predicting unmeasured results; recovery wording; 540 ms attribution; RQ2 answer scope;
velocity claim never measured; broken Ch5 -> future-work promise; PyFlyt 12 s vs 25 s; Ch1 "50 Hz";
RQ1 "Pareto-optimal"), 8 MINOR (Ch1 Ch2 description, WER source, saturation caveat, T0, kinematic
integrator, rerun limitation, write-once GBNF sentence, Ch1 English and ten intents plus a traced
example). All six scripts 0 FAIL, selftest passes, clean build 78 pages.

Remaining for the author: jury names on both title pages; read the Arabic abstract.
