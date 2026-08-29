# Thesis chapter review -- prompt template

Paste the block below into a fresh session, filling the three `{{...}}` slots. One chapter per
session: a review that has to hold two chapters' numbers in context at once starts guessing.
Run the whole-document pass (bottom of this file) only after every chapter has had its own review.

---

## Template A -- single chapter

```text
Review one thesis chapter. This is a REVIEW ONLY: do not edit any file under thesis/.

DOCUMENT:   {{master | ingenieur}}
CHAPTER:    thesis/{{master|ingenieur}}/{{chN_name}}.tex
FOCUS:      {{optional -- e.g. "Section 4.3 only", or "none"}}

## 0. Load context before reading the chapter

First run the chapter's pre-review script and read its report in full:
    ~/miniconda3/envs/pfe_swarm/bin/python tools/review/{{master|ingenieur}}_chN.py
    -> .scratch/thesis-review/reports/{{master|ingenieur}}_chN.md
Every number the report marks PASS under "claim" has been recomputed from its source: do not
redo that arithmetic. Work from its MANUAL sheets instead (citation sheet, UNTRACED numbers,
requirement wording). Its FAIL/WARN rows are leads, not findings -- verify each like any other.

Then read, in this order, and do not skip any:
1. .agents/skills/thesis-writing/SKILL.md          -- the standard you are reviewing against
2. prd.md §2 (RQs and contributions), §3.1 (frozen chapter outline for this document),
   Table 3 (ownership of shared material / write-once rule), Table 31 (RQ -> requirement ->
   experiment -> output). prd.md wins over SKILL.md where they disagree.
3. The chapter itself, in full.
4. The chapter immediately before and after it in the same document (only to check that
   forward/backward references and definitions agree -- do not review them).
5. thesis/references.bib (the closed citation set).
6. The sources of truth for numbers: results/*.csv and results/*.md, thesis/generated/*.tex,
   spikes/reports/*.md, .scratch/sprint-pfe/STATE.md, docs/adr/*.md.

## 1. Review dimensions -- check every one, in order (D10 last)

D1  Structure. Section list matches prd.md §3.1 for this chapter exactly (no added, merged,
    missing or reordered sections). The chapter opens by stating what it does and closes by
    handing off to the next chapter.

D2  Argument coherence.
    a. Every section serves a named RQ or contribution (C1-C3 for Master); name which, or
       report the section as unanchored.
    b. What the chapter introduction promises is delivered, and nothing is delivered that was
       not promised.
    c. No chronological/diary narration ("first we tried...").
    d. Paragraphs follow Assertion -> Evidence -> Impact; list paragraphs that assert without
       evidence or stop at evidence without stating the consequence.
    e. Terms are defined before use and used with one meaning throughout; a term defined
       differently in the neighbouring chapter is a finding.
    f. Logical gaps: a conclusion that does not follow from the evidence given, a step skipped,
       an alternative explanation not ruled out.

D3  Numerical accuracy. For EVERY number in the chapter (prose, tables, captions):
    a. Trace it to a specific file and row/field. Record the source as `path:row` or
       `path#field`.
    b. Recompute every derived value (percentages, deltas, margins, ratios, "X% above the
       floor") from the source values. Show the arithmetic.
    c. Check units, rounding and significant figures are consistent with the source and with
       the rest of the chapter (same metric -> same precision everywhere).
    d. Check the number matches the same number wherever else it appears in this chapter and
       the neighbouring chapters.
    e. A table that has a generator (eval/tables.py, thesis/generated/*) but is hand-typed
       is a finding.
    If a number has no traceable source, report it as UNTRACEABLE -- never assume it is right.

D4  Claims and hedging.
    a. Unearned absolutes (guarantees, proves, ensures, always, never, impossible) outside a
       mathematical proof.
    b. Claims stronger than the evidence: generalising beyond the tested models, hardware,
       dataset, speakers or conditions; causal language for a correlational result.
    c. Statistical claims name the test, n, and the effect/interval; "significant" is used only
       with a test behind it (see results/mcnemar.*).
    d. Register fits the chapter: Discussion hedged, Conclusion unhedged, Results descriptive
       (no interpretation that belongs to Discussion).
    e. Limitations that the chapter's own evidence implies but the text does not acknowledge.

D5  References.
    a. Every \cite key exists in thesis/references.bib (run tools/check_tex.py for this).
    b. For EVERY citation, open the entry's doi/eprint/url and confirm the cited source actually
       supports the specific sentence it is attached to (the claim, the number, the attribution).
       Report per citation: SUPPORTS / PARTIAL / DOES NOT SUPPORT / COULD NOT ACCESS.
       Do not rely on your memory of a paper; if you cannot open it, say so.
    c. Factual claims about the literature, a tool or a prior result with no citation.
    d. Author names, tools or methods mentioned without a \cite, or tools this project never
       used (e.g. Outlines) being presented as part of the stack.
    e. Bib entries this chapter cites that lack a doi, eprint or url, or whose title/authors/
       year disagree with the primary page.
    f. Citation placement: attached to the claim it supports, not dumped at paragraph end.
    .scratch/thesis-bibliography/*.md holds UNVERIFIED candidate notes -- useful leads, never
    evidence.

D6  Cross-document ownership (write-once, prd.md Table 3).
    a. Material owned by the other document is explained here instead of stated in one
       sentence with a cross-reference.
    b. The other document is named exactly "the \emph{Mémoire d'Ingénieur}" /
       "\emph{Mémoire de Master}".
    c. Any hardcoded chapter number of the other document is checked against its current
       prd.md §3.1 outline.
    d. Master only: no TTFT/preemption latency or voice-UAV literature. Ingénieur only: voice-UAV
       literature lives in Ch2.

D7  Figures and tables.
    a. Each is \ref'd in the text BEFORE it appears, and the text interprets it (not just
       "see Table X").
    b. Captions are self-contained: what is plotted, axes/columns, units, n, the takeaway.
    c. Vector format for plots and diagrams; no raster architecture diagrams.
    d. Any table longer than ~half a page is xltabular, and its last row is present in the
       built PDF.
    e. Table/figure values agree with the prose.

D8  Language and style.
    a. Marketing adjectives and vague qualifiers ("high", "significant" without a test,
       "seamless", "state-of-the-art").
    b. Weak verbs from the SKILL.md avoid-list.
    c. Tense consistency (method/results in past, established facts and the document's own
       structure in present).
    d. One spelling convention (British: quantisation, behaviour) throughout.
    e. Acronyms: \gls{} at every use, first included (\acrfull does not mark the entry used, so
       the next \gls expands again); key from shared/acronyms.tex; acronyms
       spelled out by hand are a finding.
    f. Non-ASCII characters in the chapter body.
    g. Grammar, run-on sentences, sentences over ~40 words that should be split.

D9  LaTeX and build hygiene.
    a. Run `python tools/check_tex.py <chapter>` (without --xelatex for a chapter body).
       Discount cross-chapter \ref findings as expected false positives; \cite findings are real.
    b. Remaining \TODO{}, \CHECK{}, \figtodo{} -- list each with its line.
    c. Labels follow the chap:/sec:/fig:/tab: pattern and match what other chapters \ref.
    d. `~` before \cite, \ref and units.
    e. Clean build: `rm -rf thesis/build/{{document}} && cd thesis && latexmk main_{{document}}.tex`
       (each thesis has its own folder, so this never touches the other one's build), then grep
       thesis/build/{{document}}/main_{{document}}.log for `^!`, `Citation.*undefined`,
       `Float too large`.

D11 Self-containment (SKILL §2 "A Self-Contained Document"). The reader holds only the thesis.
    a. Project-internal references (prd, project/hardware specification, spike, gate, D-numbers,
       escalation rule) -- the script FAILs on these; propose the thesis-facing wording for each.
    b. Project-management vocabulary (triaged, build schedule, sprint, "this project executed").
    c. Every code (Exp-N, NFR-N, FR-N, RQN, CN, Surface A/B, Branch A/B) defined once before first
       use in THIS document; the report's "Codes used" table lists them. For each, recommend keep
       (and where to define it) or replace with a descriptive name.
    d. Material owned by the other document named in words, never by its internal code.

D12 Headings and register (SKILL §2 "Headings", "Register").
    a. Every heading is a short noun phrase: no sentence, claim, code, number or result. For each
       WARN heading in the report, propose a replacement title.
    b. One capitalisation convention for chapter and section titles across the document.
    c. Formal, impersonal register: list rhetorical flourishes, aphorisms, conversational asides
       and history-of-the-project narration, each with a plain rewording.

D10 Examiner view.
    a. Reproducibility: could an outside researcher rerun the work from this chapter alone
       (hyperparameters, versions, seeds, hardware, protocol)? List what is missing.
    b. The three hardest questions a jury member would ask about this chapter, and whether the
       text already answers each (with the line that does, or "not answered").

## 2. Rules for findings

- Verify before reporting. Every finding cites the chapter line (`file:line`), quotes the
  offending text (<= 1 sentence), and cites the evidence (source file/row, recomputed
  arithmetic, or the primary-source passage).
- If you cannot verify a suspicion, report it under UNVERIFIED, not as a finding.
- Do not report a style preference as an error. Do not invent a rule not in SKILL.md, prd.md
  or standard academic practice.
- Propose a concrete fix for each finding (replacement wording or the action needed), but do
  not apply it.

Severity:
- BLOCKER  factually wrong number; citation that does not support its claim; contradiction with
           another chapter or with results/; claim the evidence refutes; missing outline section.
- MAJOR    untraceable number; overclaim; uncited literature claim; write-once violation;
           figure/table not discussed; reproducibility gap.
- MINOR    hedging/register, acronym usage, caption incompleteness, terminology drift.
- NIT      wording, typography, spacing.

## 3. Output format

1. Verdict (2-3 sentences): is the chapter ready, ready after fixes, or needs rework -- and why.
2. Scorecard: one line per D1-D12 -- PASS / ISSUES (count) / FAIL.
3. Findings table, sorted BLOCKER -> NIT:
   | # | Sev | Dim | file:line | Quoted text | Problem | Evidence | Proposed fix |
4. Number trace table (D3): | Value as written | file:line | Source path:row | Source value | OK? |
5. Citation table (D5b): | Key | file:line | Claim it carries | Verdict | Note |
6. UNVERIFIED list.
7. Examiner questions (D10b).
```

---

## Template B -- whole-document pass (after every chapter passed Template A)

```text
Review thesis/main_{{master|ingenieur}}.tex as a whole. REVIEW ONLY. Load
.agents/skills/thesis-writing/SKILL.md and prd.md §2, §3.1, Table 3, Table 31 first, then every
\input chapter and the front matter (English, French and Arabic abstracts).

Check only what a single-chapter review cannot see:
1. Golden thread: each RQ stated in Ch1 is operationalised in Method, measured in Results,
   interpreted in Discussion, and answered in Conclusion. Build a table RQ/Ci -> section per
   chapter; any empty cell is a finding.
2. Contributions claimed in Ch1 and the abstract are each demonstrated; nothing is demonstrated
   that is never claimed.
3. The same number (headline results especially) is identical everywhere it appears: abstracts,
   Ch1, Results, Discussion, Conclusion. List every occurrence of each headline value.
4. The three abstracts say the same thing: same numbers, same claims, same scope; none claims
   more than the chapters show.
5. Definitions and notation are consistent across chapters (same symbol, same meaning).
6. Every forward/backward reference ("as shown in Chapter 4", "Section 3.2 defines") points at
   the section that actually does it.
7. Write-once across documents (Table 3): grep both documents for duplicated paragraphs or
   near-duplicate explanations.
8. Front/back matter: List of Acronyms is non-empty and complete; list of figures/tables
   titles are short forms; every bibliography entry printed is cited in this document; title
   page fields.
9. Scope: from Ch1 alone, can a reader state the system end to end (with one example
   command), what is real and what is simulated, the language and command vocabulary, what is
   out of scope, and how the work divides between the two documents? Each "no" is a finding.
10. Clean build from scratch with zero errors, no undefined citations, no dropped floats, and no
   \TODO / \CHECK / \figtodo left in the PDF.

Output: verdict, the RQ traceability table, the headline-number occurrence table, then findings
in the Template A format.
```
