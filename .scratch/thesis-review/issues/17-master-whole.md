# Issue 17: whole-document pass, Master (seven chapters)

Status: resolved
Blocked by: 08 (resolved, on the six-chapter Master), 15, 16 (resolved)
Documents: thesis/main_master.tex

## What

Template B of `docs/agents/thesis-chapter-review.md`, repeated on the restructured Master. Issue 08
ran it on 2026-09-24 against the six-chapter, 63-page document. Since then: the supervisor meeting
of 25 Sep; prd.md §3.1 rewritten to seven chapters in three parts (Background; State of the art;
Contribution); a new Background (Ch2, issue 15) and a rebuilt State of the art with comparison
tables and Research gaps G1-G3 (Ch3, issue 16); Ch1's structure paragraph rewritten for the parts;
C3 in Ch1 gains the safe-failure rate; Table 3.4 gains SLURP and Snips; Method names the
repository; five bibliography entries added (vaswani2017, rpi5brief, edwards1948 corrected,
snips2018, slurp2020). The three abstracts are unchanged since 24 Sep. 80 pages.

What this pass must see that the chapter reviews could not: the golden thread now runs
Ch1 (RQ1, C1-C3) -> Ch3 §3.5 (G1-G3, one per contribution) -> Ch4 (built) -> Ch5 (measured) ->
Ch6 (interpreted) -> Ch7 (answered); Background definitions used with one meaning by Ch3-Ch7;
abstracts against the new chapter set and the C3 metric list; List of Acronyms after the
Background's new `\gls` uses; every printed bibliography entry cited; the write-once check
against the Ingénieur as it stands (all six chapters written, issues 11-14 closed).

## Agents

One reviewer + verifier, as in issue 08. Not split by dimension.

## Before running

Every Master chapter script 0 FAIL and `selftest.py` passing (recorded in Comments).

## Comments

### 2026-09-25 -- before running

Every Master chapter script re-run at 2f23827, all 0 FAIL: Ch1 0 FAIL / 3 WARN / 41 PASS;
Background 0 / 6 / 67; State of the art 0 / 2 / 67; Method 0 / 4 / 132; Results 0 / 1 / 208;
Discussion 0 / 1 / 96; Conclusion 0 / 0 / 54. Self-test PASSED. Every WARN is one justified in
its own issue. Reviewer launched (one agent, Template B); verifier follows on its BLOCKER/MAJOR.

### 2026-09-25 -- review round 1 (reviewer + verifier)

Reviewed at 2f23827; agent reports `agents/17-master-whole/{reviewer,verifier}.md`. Clean build
by the reviewer: 80 pages, 0/0/0/0, only the two jury placeholders in the PDF.

Verdict: ready after fixes, no rework. PASS on the golden thread (RQ1/C1-C3 -> G1-G3 -> Ch4 ->
Ch5 -> Ch6 -> Ch7, no empty cell), headline numbers identical at every occurrence, the three
abstracts agree (Arabic read sentence by sentence) and claim nothing beyond the chapters, write-once
against the finished Ingénieur, scope from Ch1 alone, 20/20 acronym keys, 51 cited = 51 printed.

Findings (verifier: 8 confirmed, 1 refuted, 0 new):

| # | Sev | Where | Finding | Verifier | Fix |
|---|---|---|---|---|---|
| M1 | MAJOR | ch2_background l.392-396 | Safe-failure rate defined over "errors on in-domain input"; the definition of record (tab:metrics, prd, the CSV) pools all splits: 28/528 = 0.0530, max 0.1579 is a test_ood row; in-domain would give 3/282 | CONFIRMED (issue 15's argument agent missed the clause) | one clause: on in-domain and out-of-domain input alike |
| M2 | MAJOR | main_master.tex l.96-98 | TOC prints "Bibliography 79" with a link to Ch7's last item; the bibliography starts on 75 (five pages now) | CONFIRMED; fix corrected: `heading=bibintoc` fixes the page but not the anchor under titlesec | `\clearpage\phantomsection\addcontentsline` before `\printbibliography`; same defect in main_ingenieur.tex l.77-78 (for the Ingénieur pass) |
| m1 | MINOR | ch1 l.136 | "six chapters in three parts" -- Ch7 sits outside the parts | CONFIRMED | reword; master_ch1.py counts chapters, anchor checked |
| m2 | MINOR | ch2_background l.102-104, 113 | tab:bg-models caption points at Chapter 4 for counts it does not give; "1.24 B" against "nearest million" | CONFIRMED | drop the pointer; row 1{,}236~M; master_bg.py:90 anchor updated |
| m3 | MINOR | ch3_state_of_the_art G3 | "at sub-billion scale" while Llama-3.2-1B has 1.24 B | CONFIRMED | consistent wording with RQ1's 0.36--1.2 B |
| m4 | MINOR | ch2_background four sites | "in this work" sentences in the Background | REFUTED: issue 15 ruled naming what is compared allowed; l.338 already decided there | none |
| m5 | MINOR | ch5_discussion l.40, 42, 140 | "FP16" against "fp16" everywhere else | CONFIRMED | fp16 |
| n1 | NIT | ch4_results l.247 | 0.17 pp from counts, 0.16 from the printed cells | CONFIRMED | "on the unrounded counts" (anchors kept) |
| n2 | NIT | main_master.tex l.13-15, 60 | stale comments (chapters "not yet written"; "seven tables") | CONFIRMED (LoT holds seventeen) | update |

Awaiting the author's decisions.

### 2026-09-25 -- fixes applied (author's decision: all eight confirmed items, and the Ingénieur's main file)

Applied with the verifier's §3 wording: M1 (safe-failure rate defined over errors on in-domain and
out-of-domain input alike), M2 (`\clearpage\phantomsection\addcontentsline` before
`\printbibliography`; `.toc` now `{Bibliography}{75}{section*.20}`; the same fix in
main_ingenieur.tex, `.toc` `{Bibliography}{74}{section*.17}`), m1 ("six chapters: five in three
parts, and a conclusion outside them"), m2 (caption pointer dropped; row 1{,}236~M; master_bg.py
anchor updated), m3 ("at the 0.36--1.2~B scale"), m5 (fp16 x3), n1 ("on the unrounded counts"),
n2 (two comments). m4 not applied (refuted).

Final state: all seven Master scripts 0 FAIL (Ch1 0/3/41; Background 0/6/67; State of the art
0/2/67; Method 0/4/132; Results 0/1/208; Discussion 0/1/96; Conclusion 0/0/54); self-test PASSED;
clean builds: Master 80 pages, Ingénieur 78 pages, each 0 errors / 0 undefined citations or
references / 0 dropped floats / 0 overfull; no TODO, CHECK or figtodo in the Master PDF; the two
jury placeholders remain by the author's choice.
