# Issue 17 -- verifier report on the whole-document review of the Master

Reviewed: `agents/17-master-whole/reviewer.md` (all nine findings) against the working tree at
HEAD `2f23827` (no `thesis/` file touched; the one build made by this verification was a scratch
copy under the session scratchpad, not `thesis/build/`). Rules: `docs/agents/thesis-chapter-review.md`
§2 severities. Author decisions checked: issues 08 ("Kept as written"), 15 (round 1, fixes, markers)
and 16 (round 1, fixes, style pass, Table 3.4 widening).

## 1. Summary table

| ID | Sev reported | Verdict | Sev verified | Evidence | Fix judgement / corrected fix |
|---|---|---|---|---|---|
| MAJOR-1 | MAJOR | CONFIRMED | MAJOR (at the BLOCKER boundary: a definition that contradicts the definition of record; kept MAJOR because no printed number is wrong and the Background itself hands operational definitions to `sec:definitions-of-record`, ch2:373) | ch2_background.tex:392-396 vs ch3_method.tex:574 and prd.md:509 ("Denominator is failed items only", no in-domain restriction); `results/nfr9_nfr18_abstention.csv` recomputed: 528 errors / 28 safe = 0.0530, max 0.1579 on `qwen2.5-0.5b Q4_K_M test_ood`; in-domain only: 282 errors / 3 safe = 0.0106, max 0.0417; ch5_discussion.tex:116-117, 130-132; ch6_conclusion.tex:39; Ingénieur ch1:240 uses the pooled form. No `master_bg.py` anchor on l.389-396 (l.132 is a manual-sheet note only); no recorded author decision (issue 15's argument agent wrote "agrees with ch3_method.tex:569" without seeing the in-domain clause, present since 1109a91) | Reviewer's direction correct; wording tightened in §3 (avoids "split", a Ch4/Ch5 term the Background does not use). Anchor-safe |
| MAJOR-2 | MAJOR | CONFIRMED | MAJOR | `build/master/main_master.toc:157` `{Bibliography}{79}{Item.3}`; PDF: heading on printed p.75 (pdf p.76), Ch7 ends p.74, entries [49]-[51] on p.79; main_master.tex:96-98. Scratch build with the thesis preamble (titlesec l.125 + fncychap l.205) and `\nocite{*}`: current construct reproduces `{9}{Item.3}`; `heading=bibintoc` gives `{3}{Item.3}` (page right, link still to Ch7's last list item); `\clearpage\phantomsection\addcontentsline` before `\printbibliography` gives `{3}{section*.1}` (page and anchor right, no blank page, 9 pp in all three) | Reviewer's FIRST option is insufficient under this preamble (titlesec suppresses the starred chapter's hyperref anchor); apply the SECOND option only. Same construct at main_ingenieur.tex:77-78 -- note for issue 10's successor, not widened here |
| MINOR-1 | MINOR | CONFIRMED | MINOR | main_master.tex:88-93 (Part III = ch3_method, ch4_results, ch5_discussion; ch6_conclusion after, no part); `.toc:74` part III before chapter 4, `.toc:153` chapter 7 with no part; SKILL.md:115 "Introduction and Conclusion sit outside the parts"; master_ch1.py:25 anchors `has six chapters` (kept by the fix), l.22-24 checks `\ref` order (unchanged) | Correct as written |
| MINOR-2 | MINOR | CONFIRMED (both defects) | MINOR | ch2:102-104, 113; ch3_method.tex:287-288 gives only 514 M and 494 M; generated/table33:12-15 gives 362 / 494 / 514 / 1,236 M; 1,236 M -> "1.24 B" is rounding to ten million, not to the million the caption promises. Caption clause added in b4333a0 (issue 15 fixes) without a corresponding finding -- no recorded decision. master_bg.py:90 anchors `Meta & 1.24~B` (must be updated), l.94 anchors `the released checkpoints, rounded to the nearest million` (must be kept), l.48-49 forbid `\ref{chap:results}` and `\ref{tab:...}` of another chapter | Row fix correct. Caption: drop the `(Chapter~\ref{chap:method})` pointer rather than redirect it (Ch4 does not give the four counts; the only place that does is Table 5.5, which the Background may not `\ref`). Script line 90 updated in §3 |
| MINOR-3 | MINOR | CONFIRMED | MINOR | ch3_state_of_the_art.tex:354; Llama-3.2-1B = 1,236 M (table33:15), This-work rows l.52, 137, 277 say 0.36--1.2 B, RQ1 ch1:95-96 the same; "sub-billion" is used literally for the literature at soa l.64, 111, 135, 150, 308, 348 and generically at ch2:142. Sentence dates from 7830694 (SOA rebuild); issue 16's B1 fix touched l.347-348, not l.354; no `master_ch2.py` anchor on l.353-355 | Correct as written ("at the 0.36--1.2~B scale") |
| MINOR-4 | MINOR | REFUTED | none (author's choice at most, for l.205 and l.227) | Issue 15 verifier.md:58-59 ruled "naming *what* is compared is allowed"; its argument agent listed the design-decision sentences (l.84-85, 151-155, 344-345, 386-388) and none of these four. l.338-340 was decided explicitly: A-16 (delete the whisper.cpp clause) rejected, C-7 (cite it) applied (issue 15 Comments, "Not applied, per the verifier: A-16"). l.428-429 is a generic property of a pre-specified rule; ch3_method.tex:651-653 applies it to this work. `master_bg.py` foundations regexes pass | Do not apply. The proposed l.338 wording ("is the usual choice for this stage") would add an uncited literature claim (MAJOR under D5c) and reverse an issue-15 decision |
| MINOR-5 | MINOR | CONFIRMED | MINOR (D8d, one convention) | grep: `FP16` only at ch5_discussion.tex:40, 42, 140; `fp16` 21 times in chapter prose (soa 5, method 10, results 3, discussion 1, conclusion 2) + 2 in generated tables; expanded at soa:50 as "(fp16)". master_ch5.py: no anchor contains the token (l.33, 66, 69-71, 115 are comments/variables); the l.140 anchors `abstain on 62.0\% to` / `to 73.3\% of\nthe out-of-domain` do not include it | Correct as written |
| NIT-1 | NIT | CONFIRMED | NIT | table19:12-13 cells 0.8508 / 0.8492 subtract to 0.16 pp; counts: 3012/3540 = 0.85085, 3006/3540 = 0.84915, 6/3540 = 0.1695 pp -> 0.17 (master_ch4.py:280-283 PASS on counts). Reviewer's first fix breaks anchors l.282 `a difference of 0.17~pp` and l.283 `or six decodes in 3{,}540`; the generator fix would change results/table19 and force the l.280 prose anchor to change too | Corrected fix in §3: add "on the unrounded counts" after the anchored phrase; both anchors survive, no new number |
| NIT-2 | NIT | CONFIRMED, lines and count corrected | NIT | main_master.tex:13-15 (not 14-15) and l.60 (not 47-48). `build/master/main_master.lot` has 17 `\contentsline` entries (2.1; 3.1-3.4; 4.1-4.5; 5.1-5.7 = 1+4+5+7), `.lof` 1; the reviewer's "twelve tables" is wrong (his own list sums to 17). Both lists still share printed p.8 (pdf p.9) | Fix as comments, with "seventeen", in §3 |

No BLOCKER. Six of nine findings confirmed at the reported severity, two confirmed with a corrected
fix (MAJOR-2, NIT-1), one refuted (MINOR-4). The reviewer's UNVERIFIED item on `master_bg.py` is
resolved: no anchor on the safe-failure sentences; `Meta & 1.24~B` is anchored at l.90.

## 2. Reasoning per finding

### MAJOR-1 -- safe-failure denominator (CONFIRMED, MAJOR)

Attempted disproof 1: the Background's "on in-domain input" is a defensible simplification for a
jury member outside the sub-field. It fails. The Background presents the sentence as the
definition ("is the fraction of ...") and follows it with an explicit denominator contrast
(l.394-396: "the first has out-of-domain items as its denominator, the second the erroneous items
only"), so a reader takes the in-domain restriction as part of the definition. Under that
definition the CSV gives 3 safe events among 282 in-domain errors (SmolLM2 Q4_K_M: 1 on
`test_synth`, 2 on `test_golden`), a pooled rate of 0.0106 and a range 0.0000--0.0417; the
document reports 0.0530 over 528 errors and 0.0000--0.1579 (ch4_results.tex:144-145,
ch5_discussion.tex:116-117, ch6_conclusion.tex:39). The maximum 0.1579 is an out-of-domain row
(6 hovers among Qwen Q4_K_M's 38 non-declines on `test_ood`), and 24 of the 28 pooled safe events
are out-of-domain hovers (ch5_discussion.tex:117-119). The two definitions are numerically
incompatible.

Attempted disproof 2: `tab:metrics` is the one that should change. It fails. `tab:metrics`
(ch3_method.tex:574) matches prd.md l.509 word for word ("Among items where EM is 0 ... denominator
is failed items only"), `eval/abstention.py` computes it per split including `test_ood`
(CSV rows), `results/limitation_abstention.md` §1 pools "all 3,540 items", the Discussion's
whole failure-mode analysis (l.115-125) is built on the 28-of-528 breakdown, and the Ingénieur
(ch1_introduction.tex:240) states the pooled form. The Background's own charter (l.12-14) and its
l.373 hand-off to `sec:definitions-of-record` make Ch4 the definition of record.

Attempted disproof 3: issue 15 accepted the sentence. It fails. The argument agent's list of
"definitions checked and found correct" says "safe-failure denominator (l.379-381; agrees with
ch3_method.tex:569)" -- it checked that the denominator is errors, not items, and did not see
the in-domain clause. The clause has been there since the chapter was written (1109a91); no
Comments entry of issue 15 mentions it. Not an author decision.

Severity: the rules table puts "contradiction with another chapter" at BLOCKER and
"terminology drift" at MINOR. This is a definitional contradiction with no wrong printed number,
the same shape as issue 15's A-1 which the verifier there held at MAJOR for the same reason.
MAJOR stands; it must be fixed before deposit either way.

Fix: the reviewer's direction (drop the in-domain restriction) is right. The wording in §3 says
"on in-domain and out-of-domain input alike" rather than "on any input" (which could be read as
including non-speech), and "whatever their input" rather than "of every split" ("split" is Ch4
vocabulary the Background does not otherwise use). The out-of-domain corner -- a hold on an
out-of-domain item counts as both a false command and a safe failure -- belongs to the definition
of record and is already read by the Discussion (l.117-119, 129-131); the Background need not
resolve it. No `master_bg.py` anchor is touched (the only "safe" string in the script, l.132, is
the manual-sheet note), no foundations regex fires (no number, no code, no `\ref`), and the
sentence stays under 40 words.

### MAJOR-2 -- contents page entry for the Bibliography (CONFIRMED, MAJOR; fix corrected)

Confirmed from the build: `.toc:157` records page 79 and anchor `Item.3`; `pdftotext` shows the
"Bibliography" heading on printed page 75 (pdf page 76; Ch7's last text on printed 74) and the
last entries on printed 79. The two proposed fixes were tested in a scratch copy
(`scratchpad/bibtest2`) that `\input`s the real `shared/preamble.tex` under `extreport`, with
`\nocite{*}` so the 82 entries span seven pages and an `enumerate` before the bibliography as in
Ch7:

| construct | `.toc` line | correct page? | correct anchor? |
|---|---|---|---|
| current (`\printbibliography` then `\addcontentsline`) | `{Bibliography}{9}{Item.3}` | no (last page) | no |
| `\printbibliography[heading=bibintoc]` | `{Bibliography}{3}{Item.3}` | yes | no -- link lands on the last enumerate item of the preceding chapter |
| `\clearpage\phantomsection\addcontentsline{toc}{chapter}{Bibliography}` then `\printbibliography` | `{Bibliography}{3}{section*.1}` | yes | yes |

Why `bibintoc` is not enough here: for report classes biblatex 3.19 defines it as `\chapter*{#1}`
followed by `\addcontentsline` with no `\phantomsection` (biblatex.def:1926-1929); under a plain
class hyperref anchors `\chapter*` itself (my first mini-test gave `chapter*.2` for both
constructs), but this preamble loads `titlesec` (preamble.tex:125), which reimplements the
sectioning commands and drops that anchor, so `\@currentHref` stays at the last `\item` of Ch7.
The page number would read 75 but the hyperlink would target page 74. The reviewer's second
option puts its own anchor on the bibliography's first page; TeX does not ship a page that holds
only the anchor whatsit and the `\write`, so no blank page appears (9 pages in every variant, 0
errors in every log). `\clearpage` in place of the current `\newpage` also flushes any pending
float, which `\newpage` does not.

Ingénieur: `thesis/main_ingenieur.tex:77-78` is the identical construct and will show the same
page/anchor defect once its bibliography exceeds one page (and the anchor defect already). For
issue 10's successor; not widened here.

### MINOR-1 -- "six chapters in three parts" (CONFIRMED, MINOR)

`main_master.tex:82-93` places Ch2 in Part I, Ch3 in Part II, Ch4-Ch6 in Part III, Ch7 after
Part III with no `\part`; the built `.toc` agrees (part III at l.74 before chapter 4; chapter 7 at
l.153 has no part line above it). SKILL.md:115 prescribes exactly this. The sentence promises six
chapters in the parts; five are. The reviewer's wording keeps the `has six chapters` anchor
(master_ch1.py:25, which counts `main_order` minus one = 6) and the `\ref` sequence checked at
l.22-24. Correct as written.

### MINOR-2 -- Table 2.1 caption and the 1.24 B cell (CONFIRMED, MINOR)

(a) Pointer: `ch3_method.tex:287-288` states "514~M parameters against 494~M ... counted from the
released checkpoints" for the control pair only; SmolLM2's 362 M and Llama's 1,236 M appear only
in Table 5.5 (`generated/table33_iso_parameter.tex:12, 15`, Ch5). So "(Chapter~\ref{chap:method})"
does not land where the four counts are. The Background may not point at Table 5.5:
`master_bg.py:48-49` FAIL on `\ref{chap:results}` and on any `\ref{tab:...}` outside `bg-`.
(b) Rounding: 1,236 M to the nearest million is 1,236 M; "1.24 B" is the nearest ten million.
The caption's "rounded to the nearest million" is anchored (`master_bg.py:94`, a `text_claim`
that all table33 counts are whole millions) and must stay verbatim. History: the current caption
was written in b4333a0 (issue 15's fix commit) replacing "with the parameter count reported by
each developer. Parameter counts are counted from the released checkpoints (Chapter~\ref{chap:method})";
no issue-15 finding asked for "nearest million", so there is no author decision to respect.

Fix: row "1{,}236~M" (agrees cell-for-cell with Table 5.5, satisfies check 3); caption drops the
parenthetical pointer. The reviewer's "counted as in Section~\ref{sec:lora}" is allowed by the
script but points at a passage that counts two models, so it is not better than no pointer. The
prose "1.24~B" at ch4_results.tex:80, 161 and ch6_conclusion.tex:28 is a prose rounding of the
same value and stays (as ch2:91-92 "one and a quarter billion" does). Script: `master_bg.py:90`
must become an anchor on the new cell (exact line in §3); l.92 is unaffected (it computes from
`params`, not from the cell).

### MINOR-3 -- G3 "sub-billion scale" (CONFIRMED, MINOR)

Llama-3.2-1B, one of the three quantised models C3 measures, has 1,236 M parameters, so the set
is not sub-billion. Every other "sub-billion" in the chapter is literal and about the literature
(Wang et al. l.111, 135, 150; the scale gap at l.64, 308, 348), which is what makes the reader
take l.354 literally. The This-work rows (l.52, 137, 277), RQ1 (ch1:95-96) and ch2:91-92 all
give the range as 0.36--1.2 B. The sentence was written in 7830694 and not touched by any issue-16
fix (B1 rewrote l.347-348, the previous sentence; MINOR-7 rewrote the metric list at l.351-352),
so no decision is reversed. `master_ch2.py` has no anchor on l.353-355 (its paper-number anchors
l.77-81 sit on other sentences). Reviewer's wording correct.

### MINOR-4 -- four "in this work" sentences in the Background (REFUTED)

The reviewer already marks this "for the author's judgement, not a re-raise". Checked against
issue 15: (i) its verifier's ruling on A-2 (verifier.md:58-59) is that "naming *what* is
compared is allowed"; l.205 (which two GGUF formats) and l.227 (which board) are exactly that,
the same kind as l.36 and l.84 which issue 15 passed; (ii) l.338-340 was decided: the argument
agent's A-16 asked to delete the whisper.cpp clause, the verifier rejected it and C-7 (cite it)
was applied, recorded in the Comments as "Not applied, per the verifier: A-16 (whisper.cpp clause
kept, cited instead)"; the reviewer's replacement ("is the usual choice for this stage") would
add a literature claim with no citation, which is a MAJOR under D5c, so it must not be applied;
(iii) l.428-429 states a property of any pre-specified selection rule, not a choice of this work;
`ch3_method.tex:651-653` is where the choice is made ("The rule was fixed in writing before any
result existed"), and removing the clause from the Background would leave the Pareto paragraph
defining a rule without saying why fixing it in advance matters. `master_bg.py`'s foundations
checks (deployment vocabulary, results formats, codes, forward `\ref`s) pass. Not a finding; at
most the author may prefer other wording for l.205 and l.227.

### MINOR-5 -- FP16 vs fp16 (CONFIRMED, MINOR)

Three upper-case sites, all in ch5_discussion.tex (l.40, 42, 140); 21 lower-case sites across
the five other chapters plus the two generated tables, with the expansion at
ch3_state_of_the_art.tex:50 "(fp16)". One convention (D8d). No `master_ch5.py` anchor contains
the token; the two anchors on the l.140 sentence begin after it. Fix correct as written.

### NIT-1 -- 0.17 pp vs the rounded cells (CONFIRMED, NIT; fix corrected)

Counts: the only integers that round to the printed cells are 3012/3540 = 0.85085 -> 0.8508 and
3006/3540 = 0.84915 -> 0.8492; their difference 6/3540 = 0.1695 pp prints as 0.17 pp, while the
cells subtract to 0.16 pp. `master_ch4.py:280-283` computes from counts and PASSes. The
reviewer's first fix reorders the phrase and breaks two anchors (l.282 `a difference of 0.17~pp`,
l.283 `or six decodes in 3{,}540`); the generator fix rewrites `results/table19_grammar_ablation.md`
and the table for a presentation nit and would force the prose 0.8508/0.8492 (anchored at l.280)
to five decimals as well. Corrected fix: insert "on the unrounded counts" after the anchored
phrase (§3). The other four sites (res:261, dis:163, con:52, 57) state 0.17 pp without the cells
beside them and need nothing.

### NIT-2 -- stale comments in main_master.tex (CONFIRMED, NIT; lines and count corrected)

l.13-15: "Chapter structure is prd.md 3.1 verbatim (seven chapters in three parts). Chapters not
yet written are listed commented-out below ..." -- every chapter is `\input` (l.80-93). l.60:
"One figure and seven tables: the two lists share a page" -- `main_master.lot` has 17 entries
and `main_master.lof` 1. The reviewer wrote "twelve tables" while listing 2.1, 3.1-3.4, 4.1-4.5,
5.1-5.7, which is seventeen. The `\let\clearpage\relax` trick still holds: LoF and LoT share
printed page 8. Comment-only; nothing prints.

### Consistency with recorded decisions

- Issue 08 "Kept as written" NIT-2 (safe-failure absent from Ch1's C3 list) was superseded by
  issue 16 MINOR-7 (C3 now names it; `master_ch1.py:38-40` anchors `safe-failure rate`). MAJOR-1's
  fix touches ch2 only; no conflict.
- Issue 15: A-9's false-command sentence (ch2:390-392) is left verbatim by the MAJOR-1 fix; A-2's
  `\ref{sec:definitions-of-record}` at l.373 remains, so `master_bg.py`'s foundations check holds.
  A-16/C-7 (whisper.cpp clause) is respected by refusing MINOR-4's l.338 rewrite.
- Issue 16: B1 (l.347-348) and MINOR-7 (l.351-352) are untouched by MINOR-3's l.354 edit; the
  smollm2 "and others" and the 1,100 ms cell are not raised.

## 3. Corrected fixes ready to apply

### MAJOR-1 -- thesis/master/ch2_background.tex l.392-396

Old (l.392-396, from "The \emph{safe-failure" to "poorly on both."):
```
vehicle still acts on input that was not a command. The \emph{safe-failure
rate} is the fraction of the system's errors on in-domain input that resolve to a harmless
action, such as declining or holding position, rather than to a wrong command. The first has
out-of-domain items as its denominator, the second the erroneous items only; neither is a
function of \gls{em}, and a system can score well on \gls{em} and poorly on both.
```
New:
```
vehicle still acts on input that was not a command. The \emph{safe-failure
rate} is the fraction of the system's errors, on in-domain and out-of-domain input alike, that
resolve to a harmless action, such as declining or holding position, rather than to a wrong
command. The first has out-of-domain items as its denominator, the second erroneous items only,
whatever their input; neither is a function of \gls{em}, and a system can score well on \gls{em}
and poorly on both.
```
Anchors: none in `master_bg.py` on these lines; foundations regexes unaffected. Re-run
`master_bg.py` (expect 0 FAIL / 6 WARN / 67 PASS unchanged).

### MAJOR-2 -- thesis/main_master.tex l.95-98

Old:
```
% -- Bibliography -------------------------------------------------------------
\newpage
\printbibliography
\addcontentsline{toc}{chapter}{Bibliography}
```
New:
```
% -- Bibliography -------------------------------------------------------------
%  The contents entry and its hyperref anchor go BEFORE \printbibliography: placed after it,
%  \addcontentsline records the bibliography's last page and the last \item of Chapter 7, and
%  heading=bibintoc does not help because titlesec drops the anchor of \chapter*.
\clearpage
\phantomsection
\addcontentsline{toc}{chapter}{Bibliography}
\printbibliography
```
Do NOT use `\printbibliography[heading=bibintoc]` alone (page right, link wrong under this
preamble; tested). Rebuild from clean and confirm `.toc` reads `{Bibliography}{75}{section*.N}`
and the PDF stays at 80 pages. No review-script anchor involved (`main_master.tex` is read only
by `main_order`, which counts `\input` lines).

### MINOR-1 -- thesis/master/ch1_introduction.tex l.136

Old: `The rest of this document has six chapters in three parts. Part~I holds`
New: `The rest of this document has six chapters: five in three parts, and a conclusion outside them. Part~I holds`
Anchor `has six chapters` (master_ch1.py:25) intact; `\ref` order (l.22-24) intact.

### MINOR-2 -- thesis/master/ch2_background.tex l.102-104 and l.113, plus tools/review/master_bg.py l.90

Caption, old (l.102-104):
```
\caption[Small language models compared in this work]{The four small language models compared in
this work. Parameter counts are those of the released checkpoints, rounded to the nearest million
(Chapter~\ref{chap:method}); the developer's report is cited for each model.}
```
New:
```
\caption[Small language models compared in this work]{The four small language models compared in
this work. Parameter counts are those of the released checkpoints, rounded to the nearest million;
the developer's report is cited for each model.}
```
Row, old (l.113): `Llama-3.2-1B-Instruct & Meta & 1.24~B & \cite{llama32} \\`
New: `Llama-3.2-1B-Instruct & Meta & 1{,}236~M & \cite{llama32} \\`

Script, old (master_bg.py:90):
```
r.number("Meta & 1.24~B", params["llama-3.2-1b-instruct"] / 1000, "results/table33_iso_parameter.md Params, in B")
```
New:
```
r.number("Meta & 1{,}236~M", params["llama-3.2-1b-instruct"], "results/table33_iso_parameter.md Params")
```
Anchor l.94 (`the released checkpoints, rounded to the nearest million`) is kept verbatim by the
new caption; l.92 unaffected. The `{,}` form is what `lib.py` strips before parsing (l.152) and
what ch4_results uses for 3{,}540. Re-run `master_bg.py` and `selftest.py`.

### MINOR-3 -- thesis/master/ch3_state_of_the_art.tex l.354

Old: `the whole deployment pipeline on this task at sub-billion scale, next to the throughput that`
New: `the whole deployment pipeline on this task at the 0.36--1.2~B scale, next to the throughput that`
No `master_ch2.py` anchor on l.353-355.

### MINOR-4 -- no change

Not a finding (issue 15's rulings on l.36/84 and A-16/C-7 cover these sentences; l.428-429 is
generic). If the author still prefers, l.205 "Two are used in this work." and l.227 "The
Raspberry~Pi~5 used in this work carries" may be reworded, but l.338-340 must keep its
`\cite{whisper}` / `\cite{whispercpp}` and must not acquire "the usual choice".

### MINOR-5 -- thesis/master/ch5_discussion.tex l.40, 42, 140

`FP16` -> `fp16` at the three sites (l.40 "at FP16. It has no latency", l.42 "At FP16", l.140
"At FP16 the three models"). No `master_ch5.py` anchor contains the token.

### NIT-1 -- thesis/master/ch4_results.tex l.247-248

Old:
```
malformed. \Gls{em} moves from 0.8508 to 0.8492, a difference of 0.17~pp, or six decodes in
3{,}540. On this test set, under these models, the grammar's measurable contribution to output
```
New:
```
malformed. \Gls{em} moves from 0.8508 to 0.8492, a difference of 0.17~pp on the unrounded counts,
or six decodes in 3{,}540. On this test set, under these models, the grammar's measurable contribution to output
```
Anchors `moves from 0.8508` (l.280), `a difference of 0.17~pp` (l.282) and
`or six decodes in 3{,}540` (l.283) all survive; no new number. Reflow the paragraph as the
author likes; the anchors are whitespace-tolerant (l.283 already matches across a line break).

### NIT-2 -- thesis/main_master.tex l.13-15 and l.60 (comments only)

l.13-15, old:
```
%  Chapter structure is prd.md 3.1 verbatim (seven chapters in three parts). Chapters not yet
%  written are listed commented-out below with their prd.md titles, so the
%  outline stays visible and the document still compiles.
```
New:
```
%  Chapter structure is prd.md 3.1 verbatim (seven chapters in three parts); every chapter is
%  written and \input below.
```
l.60, old: `% One figure and seven tables: the two lists share a page. Each \chapter* starts with`
New: `% One figure and seventeen tables: the two lists share a page. Each \chapter* starts with`

## 4. New findings

None at BLOCKER level. Two corrections to the reviewer's report itself, recorded above: the
`heading=bibintoc` option of MAJOR-2 does not fix the hyperlink under this preamble, and NIT-2's
table count is seventeen, not twelve.

## 5. Suggested order of application and re-checks

1. MAJOR-1 (ch2), MINOR-2 (ch2 + script), MINOR-3 (soa), MINOR-1 (ch1), MINOR-5 (dis), NIT-1 (res):
   one chapter-edit commit; re-run `master_bg.py`, `master_ch1.py`, `master_ch2.py`,
   `master_ch4.py`, `master_ch5.py`, `selftest.py` (expect FAIL counts unchanged at 0).
2. MAJOR-2 + NIT-2 (main_master.tex): clean build; confirm `.toc` Bibliography page 75 with a
   `section*` anchor, 80 pages, 0 errors / 0 undefined / 0 dropped floats.
3. Record in issue 10's successor: `main_ingenieur.tex:76-78` needs the same bibliography fix.
