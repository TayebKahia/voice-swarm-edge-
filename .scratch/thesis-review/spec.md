# Thesis chapter review -- plan

Review every written chapter of both theses, one chapter at a time, in reading order: Master Ch1
to Ch5, then Ingénieur Ch1 and Ch2, then one whole-document pass per thesis. Each chapter gets a
deterministic script first, then review agents on what the script cannot judge, then a verifier.

Issues: `issues/00` (a decision) then `issues/01` ... `issues/08`, one per chapter, each blocked by the one before so the order
holds. Reports: `reports/<script>.md`, regenerated on every run.

## Why this order

- **Master first, whole.** Ch1 makes promises (C1-C3, "Chapter 4 reports ..."); reviewing Ch1-Ch5 in
  sequence means each later review can check the earlier chapter's promises against what it finds,
  with the Master's numbers still in context.
- **Ingénieur second.** Its Ch1 depends on the Master only through Table 3 (who owns what), and its
  Ch2 has no prose yet -- its script exits 2 ("not reviewable") until it does.
- **Whole-document passes last** (Template B in `docs/agents/thesis-chapter-review.md`): they check
  what no single-chapter review can see, and they are only worth running on chapters already clean.

## The loop, per chapter

1. **Script.** `~/miniconda3/envs/pfe_swarm/bin/python tools/review/<script>.py`. It writes
   `reports/<script>.md`: FAIL (the chapter disagrees with its sources), WARN (someone must judge),
   PASS, then the MANUAL sheets the agents work from (citation sheet, number trace, section map,
   requirement wording).
2. **Triage the FAILs.** Each is either a chapter error (goes to the findings) or a script error.
   A script error is fixed in the script -- **never by changing an expected value to match the
   prose**; the expected value comes from `results/`, and the prose is what is under test.
3. **Review agents**, split by dimension as the issue says (Template A, restricted to the listed
   dimensions, with the report as input). The script has already done D3 (numbers) and most of
   D9 (LaTeX), so no agent re-does arithmetic the script did -- they read the UNTRACED rows only.
4. **Verifier.** One agent, given only the BLOCKER and MAJOR findings, tries to disprove each.
   Only what survives reaches you.
5. **You decide** each surviving finding: fix, or keep with a reason recorded in the issue's
   Comments. The prose is yours; the agents propose, they do not edit `thesis/`.
6. **Re-run the script** after the fixes: zero FAIL, and every WARN either fixed or justified in
   the issue.
7. **Commit**, separately for `thesis/` and for `tools/review/` if a script changed (CLAUDE.md:
   separate subsystems, separate commits); set the issue `Status: resolved`.

## What the scripts check, and what they cannot

Every script runs the common checks in `tools/review/lib.py`: `tools/check_tex.py`, `\ref`
resolution across the document (pending chapters are WARN, grouped per label), leftover
`\TODO`/`\CHECK`/`\figtodo`, citation keys and identifiers, hand-typed `Table 19`-style numbers,
`~` before `\cite`/`\ref`, the SKILL §2 word lists, companion-document naming, acronyms typed by
hand, float referencing order, `\texttt{}` paths that must exist, and a trace of every significant
number to a source file.

On top of that, each chapter script recomputes its chapter's own claims from the artefacts:
Ch1 against `thermal_headroom.md` and `prd.md` §2; Ch3 against `schema/cmd.gbnf`,
`train/configs/*.yaml`, `data/*.jsonl` and the annotation seal; Ch4 against the per-trial CSVs with
the project's nearest-rank percentile (155 claims); Ch5 against the same, plus "no number Ch1-Ch4
did not report"; Ingénieur Ch1 against `prd.md` Tables 11-12.

They cannot judge argument, register, or whether a paper supports its sentence. Those are the
agents' job, and the report's MANUAL sheets are their worklists.

**Trust in the scripts** comes from `tools/review/selftest.py`: it plants one realistic error per
chapter in an in-memory copy and requires the matching FAIL. Run it after any change to `lib.py`.
A claim anchors on the words around its number, so when a number in the chapter changes, the
script reports the new value against the source rather than "anchor not found".

## Agent budget

| Issue | Chapter | Agents | Why |
|---|---|---|---|
| 01 | Master Ch1 (112 lines, 3 cites) | 1 reviewer + verifier | fits one agent's attention |
| 02 | Master Ch2 (192, 34 cites) | citation + argument + verifier | 34 papers to open |
| 03 | Master Ch3 (540, 18 cites) | reproducibility + argument + citation + presentation + verifier | too long for one |
| 04 | Master Ch4 (349, 11 cites) | argument/statistics + citation + presentation + verifier | numbers done by script |
| 05 | Master Ch5 (§5.1 only) | 1 reviewer + verifier | short; re-run when §5.2-5.3 exist |
| 06 | Ingénieur Ch1 (374, 12 cites) | argument + citation/presentation + verifier | requirement-heavy |
| 07 | Ingénieur Ch2 | script only until prose exists | scaffold |
| 08 | Whole-document, both | 1 reviewer + verifier per document | must see every chapter at once |

## Self-containment and headings (D11, D12)

Two dimensions added to Template A, with rules in SKILL §2 and checks in `lib.py`:
- **D11 self-containment**: no project-internal references (prd, specification, spike, triage,
  build schedule -- FAIL), and every code (Exp-N, NFR-N, RQN, CN, Surface/Branch A/B) defined in
  this document before its first use (FAIL if never defined, WARN if defined later).
- **D12 headings and register**: headings are short noun phrases with no claims, codes or
  numbers; one capitalisation style for chapter titles; no rhetorical flourishes.

They go to the presentation agent where a chapter has one, otherwise to the single reviewer.
The biggest single decision they raise is **`issues/00-codes-decision.md`**: whether the experiment and
requirement codes stay (defined once) or go (descriptive names). Decide it before issue 01.

## Known cross-chapter items (seen by more than one script)

- **Acronyms are typed by hand in every chapter except Master Ch1 and Ch4.** Write `\gls` at every
  use: the first `\gls` in document order expands itself. `\acrfull` does not mark the entry used
  (it caused a double expansion in Ch4), and the scripts now FAIL on it.
- **`FA` means two things**: Formation accuracy (Master Ch3 metrics table) and False Acceptance
  (`shared/acronyms.tex`). Master Ch3 FAILs on it.
- **Three models or four**: Ch1 "three candidate models", Ch2 "four candidate models", Ch3 fine-tunes
  four and quantises three. Consistent in fact; the reader needs to see it as one story.
