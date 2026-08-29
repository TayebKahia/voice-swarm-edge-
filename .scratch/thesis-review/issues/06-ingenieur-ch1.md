# Issue 06: ingenieur-ch1

Status: resolved
Blocked by: 05
Chapter: thesis/ingenieur/ch1_introduction.tex
Script: tools/review/ingenieur_ch1.py
Report: .scratch/thesis-review/reports/ingenieur_ch1.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/ingenieur_ch1.py
```

## Agents

- **Argument agent** -- D1, D2, D4, D6, D10. Focus: every design promise the safety argument makes
  (membership rule, clamp placement, three layers) listed with the chapter that must deliver it,
  for the Ch3-Ch6 reviews; the locked NFR-12 phrasing at each occurrence; requirement paraphrases
  that narrow or widen scope (report's wording table).
- **Citation / presentation agent** -- D5 (12 citations: stpa, avizienis2004, koren1991, relays2s,
  mira, ...), D7, D8, D9, D11, D12.
- **Verifier.**

## What the script establishes (baseline: 5 FAIL, 29 WARN, 52 PASS; the 5 FAILs are D11)

- RQ2, RQ3 and C4 are prd.md §2 verbatim; C1-C3 not claimed.
- Every NFR target matches prd.md Table 12; counts (12 FR, 21 NFR rows, 6 remaining, "more than
  sixteenfold") are right; no measured result is quoted, as the chapter promises.

## Seeded findings

- Both requirement tables are first `\ref`'d after the float (l.87 vs l.72; l.126 vs l.106).
- FR-11 verification reworded ("every state x command cell" vs prd's "`test_fsm.py` covering every
  cell of Table 9") -- equivalent?
- Labels the unwritten chapters must carry: chap:architecture, chap:implementation,
  chap:validation, chap:demonstration.

- **D11**: Exp-2/3/4 and Branch A/B used in Ch1 but defined nowhere yet -- define them here,
  at first use, even though Ch3 and Ch5 will describe them. RQ1/RQ2, NFR-14/15/16 are used a few
  lines before their table rows.
- **D12**: flourishes to judge -- "FR-6 is worth reading twice", "The vocabulary of failure has one
  word in it."

## Comments

### 2026-09-24 -- review, verified findings (awaiting the author's decisions)

**Order.** Issue 05 (the blocker) is still `ready-for-agent`; this review was run on request ahead
of it. Nothing here depends on Master Ch5.

**Script triage.** Baseline reproduced: 5 FAIL, 29 WARN, 52 PASS. All 5 FAILs are chapter errors
(D11: Branch A/B, Exp-2/3/4 never defined; fixes V9, V12). Two script errors, fixed in
`tools/review/lib.py` (no expected value touched):
- `_codes` took any `(` after a code as a definition, so "RQ2 and RQ3 (Section~\ref{...})" (l.60)
  and "contribution C4 (Section~\ref{...})" (l.221) counted as defining RQ3 and C4 and hid two
  use-before-definition WARNs. A parenthesis opening with Section/Chapter/Table/Figure/Appendix is
  now a use.
- The citation sheet bounded a sentence by `. ` or a blank line only, so a `\cite` inside a tabular
  row showed the caption or the row above (rows 2-4 here; rows 2-5, 19-20 in Master Ch3). Rows now
  also end at `\\`.
After both: **5 FAIL, 31 WARN, 52 PASS**; selftest passes; Master Ch1-Ch3 and Ingenieur Ch2 counts
unchanged (Master Ch4/Ch5 not re-run: uncommitted work in flight on them).
Tooling note for step 5: renaming Exp-N in the Source column (V12) turns the
`requirement_table_check` source comparisons into WARNs; the check must map the issue-00 names to
the prd codes, not the other way round.

**Agents:** argument (D1, D2, D4, D6, D10; 28 findings), citation/presentation (D5, D7-D9, D11, D12;
26 findings; clean build to a scratch outdir: 0 errors, 0 undefined citations, 0 overfull boxes,
15 undefined refs all to the unwritten Ch4-Ch6). 12 BLOCKER/MAJOR went to the verifier:
10 CONFIRMED, 1 PARTLY, 0 REFUTED; 1 raised to BLOCKER, 3 lowered to MINOR; 7 proposed fixes
corrected. Full reports, including the verifier's corrected replacement text and the promise
table (P1-P31) for the Ch3-Ch6 reviews: `.scratch/thesis-review/agents/06-ingenieur-ch1/`.

| # | Sev | Line | Finding | Verifier | Proposed fix (verifier-corrected) |
|---|---|---|---|---|---|
| V1 | BLOCKER | 224-235, 332 | Reflex-path phrases "reach the swarm without passing through any of the three validation layers": false. Branch A commands go through `validate()` and the state machine (pipeline.py:79 -> fsm.py:165); only transcription and parsing are skipped. Contradicts ch3:157-160 | CONFIRMED (traced the code path) | The hazard is that a false accept is well-formed, in range and, while in flight, legal, so no check can tell it from speech. Rewrite l.224-235 per verifier.md A1 ("skip interpretation", not "skip validation"); l.332 "A fast path that skips interpretation" |
| V2 | BLOCKER (up) | 196-201 | "every rejection at every layer resolves to a hold ... the same state in each": in LANDED/LANDING/ABORTED a rejection is a logged no-op (ADR-0002, fsm.py:212-243); the grammar has no rejection exit. Contradicts ch3:222-223 | CONFIRMED (ran fsm.py) | Hold where the flight state admits one, logged no-op otherwise; conclusion "no rejection path produces motion" kept. Merged with V7 text in verifier.md A3. Delete l.201 |
| V3 | MAJOR | 126-133 | "sixteenfold ... no single path can satisfy both ... no amount of tuning": non sequitur (a path meeting 150 ms meets 2,500 ms); the real obstacle, the endpointer's silence wait, is unnamed | CONFIRMED; reviewer's fix had a false fact (validate/FSM stage is 50 ms, under 150) | Keep the anchor argument; name the endpointing wait as the reason (verifier.md A2). Ch3:37-40 repeats the claim |
| V4 | MAJOR | 218, 324-325 | "The reflex is bounded at 150~ms at p95" states an achieved property; measured p95 is 545/547 ms, NFR-1 misses (exp2_analysis.md:21,26). C4 "a bounded safety reflex" same | CONFIRMED | "is budgeted at 150~ms at p95 from the keyword offset (NFR-1)"; C4 "a safety reflex with its own latency budget" -- but C4 is prd §2.1 verbatim (script PASS), so changing it means changing the contribution text |
| V5 | MAJOR | 32-35 | "a command channel that can be partitioned away from the aircraft is not a fail-safe": the stop commands themselves cross a Wi-Fi hop (ch3:80,103); "offline" never defined | CONFIRMED | Define "offline" in prose by the l.24-25 criterion (site infrastructure vs the system's own link); l.33-34 "depends on infrastructure the site may not provide". Leave the NFR-14 row as prd Table 12 |
| V6 | MAJOR | 274-275 | "Chapter architecture builds the three mechanisms": Ch3 l.17-19 designs two, the clamp is Ch4's (matches prd §3.1) | CONFIRMED | "designs the first two mechanisms and Chapter~\ref{chap:implementation} realises all three, the third as part of the swarm controller" |
| V7 | MAJOR | 197-198 | avizienis2004 credited with "resolving every detected fault to a single safe state is the fail-safe behaviour": the taxonomy defines fail-safe by severity ("failures ... all minor ones", §3.3.1) | CONFIRMED (primary text read) | Merged into V2 text: fail-controlled for the mode, fail-safe for the severity, cite on the definition |
| V8 | MAJOR | 179-181 | stpa cited for consequence-over-rate as "standing practice ... rather than a departure": the Handbook presents exactly that as its departure from probabilistic analysis (ch.1; p.133) | CONFIRMED | Cite each for what it says: avizienis2004 grades failures by severity; STPA is a worst-case, not likelihood, method |
| V9 | MAJOR | 78, 111-115, 134, 224, 235, 359 | Branch A (8x) / Branch B (5x) never defined (script FAIL) | CONFIRMED | Issue 00: define "reflex path" / "parse path" (incl. the VAD) after l.43, replace every use; Ch3 (~30 uses, heading ch3:155) must follow |
| V10 | MINOR (down) | 305-308 | RQ3's "degrade safely" clause points to no metric | PARTLY: NFR-9 is RQ1's (Table 31); l.161-165 already names the safe-failure rate | One back-reference clause at l.307-308. Do not tabulate NFR-9 (breaks l.60-62 subset rule; its target was re-baselined, ADR-0006) |
| V11 | MINOR (down) | 46-48 | \cite{pyflyt} on a sentence about this system's SIL that never names PyFlyt | CONFIRMED-DOWNGRADE (placement only; l.80 correct) | "... two interchangeable backends, the PyFlyt simulator~\cite{pyflyt} and a kinematic simulator." |
| V12 | MINOR (down) | 78-79, 111-120 | Exp-2 (7x), Exp-3 (2x), Exp-4 (3x) never defined (script FAIL); table cells only | CONFIRMED-DOWNGRADE | Issue 00 names; Source column -> "Experiment" with "Latency" / "Acoustic robustness" / "Formation control" and a caption line; forward-reference sentence before the floats (P9) |

**MINOR / NIT, not verified (spec step 4), listed for decision** -- row numbers in the agent reports
(A = argument.md, P = citation-presentation.md):
- Undefined or early codes/terms: RQ1-3 at l.60-62 (P15), NFR-14 at l.35 (P16), C4 at l.221 (P17),
  "golden set" (P11, A20), p95 undefined (P11), "the budget" (A27), "canonicaliser" (P24),
  "fail-safe" three meanings (A18), hold/hover drift (A19).
- Acronyms typed by hand, ~20 sites; no `apf` key; `pid` long form prints "(controller) (PID)" (P12, P13).
- Floats referenced after the table in source (P9); NFR-7/8 never discussed (P10).
- Citation placement: koren1991 covers an unsourced one-step-crossing clause (P6); relays2s/mira
  lead clause "bypasses validation" (P7, overlaps V1).
- Bib: `lim2025` and `whispercpp` `note` fields print in the bibliography (P8, P21).
- Eight sentences of 59-136 words (P14). Ten flourishes incl. l.93, l.201, l.232-233, l.253-254,
  l.370-374 (P19). Project vocabulary at six sites (P18).
- Argument: NFR-11 missing from the accounting (A10); caption vs text on FR-10 (A11); two-class
  derivation skips the test that excludes `land` (A12); "closed" vs "a third could be admitted"
  (A13); "harmless" for `abort` (A14); formation results are from the kinematic backend (A17);
  clamp count is pair-events, not timesteps (A26); FR-6 drops the sequence-number rule, FR-7 drops
  the three formation shapes (A23, A24); no opening statement of what the chapter does (A8).
- Outside this chapter: FSM `takeoff` with `z = NaN` in LANDED goes to TAKING_OFF and dispatches
  HOVER (legality checked on the raw intent after layer-2 fallback); unreachable on the live path,
  which validates before publishing, but untested (verifier.md A3).

**Decisions (author, 2026-09-24):** fix V1-V12 as verified; apply every MINOR/NIT.

### 2026-09-24 -- fixes applied; script at 0 FAIL, 5 WARN, 57 PASS

**Applied in `thesis/ingenieur/ch1_introduction.tex`:** V1-V12 with the verifier's corrected text,
and every MINOR/NIT row of both agent reports (A8-A28, P6-P25), with these exceptions and
adjustments:
- **V4, C4 half not applied.** The C4 bullet ("a bounded safety reflex") is prd §2.1 verbatim and
  the script requires it to stay so; changing it means changing the contribution itself, which is
  the author's call in prd first. l.218 now reads "budgeted at", which carries the correction.
- **A9:** prd §3.1 item 1 amended (outside git by design) to list objectives, contribution and
  structure; `ingenieur_ch1.py` now checks those three sections too.
- **A12:** the added sentence names no number ("the time the reflex saves"), so no untraced
  2,350 ms enters the chapter.
- **A21 / A25 / D4:** l.146-150 and l.259 were reworded so that no negated absolute remains
  ("not as a property of every reachable state"; "no collision could occur"; "the potential field
  alone maintains separation"); the locked NFR-12 wording is intact at l.144 and l.296-297.
- **P13, P8, P21, P26** touched shared files: `pid` long form is now "proportional-integral-
  derivative"; the `note` fields of `lim2025` and `whispercpp` are deleted (they printed in the
  bibliography); Ingenieur Ch2/Ch3 chapter titles are sentence case like the Master's. P21's
  optional retitle of `whispercpp` was not done.
- **P20** (labels of the unwritten Ch4-Ch6) needs no edit now; see the WARN justification below.
- **Found while building:** a first-use `\gls` inside `tabularx` prints only the short form,
  because tabularx typesets its body in trial passes that consume the first use. In this chapter
  only PID was affected (CRR and SNR are spelled out by the NFR caption before the table): the
  FR-7 cell now prints `\acrlong{pid} (\acrshort{pid})` and `\glsunset{pid}`. Document-wide this is
  a preamble matter (both theses) and is left for issue 08. Both tables gained short captions so
  the List of Tables carries no glossary command.

**Script changes (`tools/review/`), no expected value changed:**
- `lib.py` `norm` compares `\gls`/`\glspl`/`\acrshort`/`\acrlong` as they print, so the RQ2/RQ3
  verbatim checks see the `\gls` quote blocks as prd §2's text.
- `lib.py` `_codes` accepts "name (CODE)" as a definition ("pipeline latency (RQ2)").
- `lib.py` requirement `gist` ignores prd's own "Table N" pointer, which is not a target (this was
  the FR-11 WARN).
- `ingenieur_ch1.py`: Source column mapped back to prd codes (`source_names`); the three count
  claims re-anchored on the new wording; the "more than sixteenfold" claim removed because V3
  removed the sentence; outline topics added (A9).
- Selftest passes, and Master Ch1-Ch3/Ch5 and Ingenieur Ch2 counts are identical under the old and
  new `lib.py` (checked in a HEAD worktree, since uncommitted results/ changes from another session
  currently break `master_ch1.py` in the live tree -- a KeyError on the regenerated
  `thermal_headroom.md` labels, not caused here).

**Build** (`latexmk -outdir=<scratch>`): 0 errors, 0 undefined citations, 0 overfull boxes;
19 undefined references, all to chap:implementation / chap:validation / chap:demonstration.

**Remaining WARNs, justified:**
- `ref` x3 (l.68, l.69, l.314): chap:validation, chap:demonstration, chap:implementation do not
  exist yet. The labels are fixed in the chapter's header comment; Ch4-Ch6 must carry them
  (main_ingenieur.tex names the last file `ch6_conclusion`; its label must be chap:demonstration).
- `acronym` x2 (l.89, l.123): "Functional/Non-functional requirements driving this document"
  opens each caption. A glossary command there reaches the List of Tables and can take the first
  use, so the long form stays as caption prose (presentation agent, P12).

**Carried to other reviews:**
- Ingenieur Ch3: rename Branch A/B (about 30 uses and the heading at ch3:155) to the reflex/parse
  path; repair ch3:37-40, which repeats the V3 non sequitur; the promise table P1-P31 in
  `agents/06-ingenieur-ch1/argument.md`.
- Issue 08: the glossaries/tabularx first-use problem above; re-check l.390-393 (Master C3
  paraphrase, A22) once Master Ch1 is final.
- Code, not thesis: FSM `takeoff` with `z = NaN` in LANDED (verifier.md, A3).

### 2026-09-24 -- author's reading of the PDF: three codes still undefined for a reader

1. The experiments were named but never described. They are now described in one sentence each in
   Section 1.2 at first mention, from what `results/exp2_analysis.md`, `exp3_pi_analysis.md` and
   `exp4_formation.md` record, with no trial counts. The Measured-by column carries the full names.
2. The FR/NFR IDs were defined only by table rows, and in print the prose reached them first
   (Table 1.1 floats to p.12, after "FR-5 and FR-9 determine..." on p.11). Both tables now use named
   criteria, like the Master. The shared ones reuse the Master's names, so one requirement has one
   name across both documents. Every prose use of an ID is now its name, including Ch3's three.
3. C4 was defined only by its bullet, and the number meant nothing without C1-C3. The bullet is now
   a `\textbf{Contribution.}` quote block, with its text still prd C4 verbatim. "C4" is gone from
   the prose of Ch1 and Ch3.

Issue 00 is amended to match. The script maps names back to prd IDs (`row_ids`, as `master_ch3.py`
does), and it now checks that every shared criterion has the Master's name.
Result: **0 FAIL, 5 WARN, 60 PASS**. The WARNs are the same five, justified above. The selftest
passes, and the build has 0 errors.

Ch3's 41 Branch A/B uses have been renamed to the reflex/parse path of Section 1.1, on the author's
request, including the heading "Reflex-path membership rule", the figure tags and the membership
table. The ch3 l.37-40 repeat of the V3 non sequitur is fixed as well: the reason is now the
endpointing wait, with pointers to 3.4 and Ch1 1.2.
