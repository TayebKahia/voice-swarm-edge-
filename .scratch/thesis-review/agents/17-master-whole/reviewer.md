# Issue 17 -- whole-document review of the Master (Template B, seven chapters), reviewer report

## 0. Header

- Reviewed: `thesis/main_master.tex` as a whole at HEAD `2f23827` (working tree: only
  `.scratch/` files modified; no `thesis/` file touched by this review) -- title page, dedication,
  acknowledgements, the three abstracts, `shared/acronyms.tex`, Ch1-Ch7
  (`ch1_introduction`, `ch2_background`, `ch3_state_of_the_art`, `ch3_method` = Ch4,
  `ch4_results` = Ch5, `ch5_discussion` = Ch6, `ch6_conclusion` = Ch7), the seven generated tables
  Ch5 `\input`s, `references.bib`, and the built PDF (80 pages) via `pdftotext`.
- Against: SKILL.md; prd.md §2, §3.1, §3.2 + Table 3, Table 31; the seven pre-review reports
  (`master_ch1`, `master_bg`, `master_ch2` [= state of the art], `master_ch3`..`master_ch6`;
  every PASS number taken as recomputed, not redone); the Comments of issues 08, 15 and 16
  (author's decisions not re-raised: smollm2 "and others", the 1,100 ms cell in Table 3.4, ATIS
  not added, issue 08's NIT-2..NIT-5 and MIN items, the latency-budget table staying in Method,
  the jury placeholders); `results/nfr9_nfr18_abstention.csv`, `results/limitation_abstention.md`,
  `results/exp2_latency_budget.md`, `results/mcnemar.md`.
- Write-once (item 7) compared against `thesis/ingenieur/ch1..ch6*.tex` as on disk (all six
  written), by targeted grep of every Master-owned topic plus reading of the passages that name
  the Master (Ing. Ch1 l.268-280, Ch2 l.185-200 and 320-345, Ch3 l.45-60, 285-305, 400-460,
  Ch5 l.295-310, Ch6 l.405-415).
- Build: run by this review from a clean tree (no other latexmk/xelatex was running).

## 1. Verdict

Ready after fixes; no rework. The golden thread runs unbroken from RQ1 and C1-C3 in Ch1 through
G1-G3 in Ch3 §3.5 to Ch4, Ch5, Ch6 and Ch7 with no empty cell, every headline number is
identical at every occurrence (the abstracts, Ch1, the Background's model table, the State of the
art's This-work rows, Ch5-Ch7 and the generated tables), the three abstracts say the same thing
and claim nothing the chapters do not show, and the build is clean. Two MAJORs: the Background
defines the safe-failure rate over in-domain errors while the definition of record, the results
and the Discussion pool all splits including the out-of-domain set (the quoted maximum 0.1579 is
an out-of-domain row); and the contents page lists the Bibliography at page 79 when it starts on
page 75, because the `\addcontentsline` follows a five-page `\printbibliography`. Five MINORs and
two NITs, all one-line fixes.

## 2. RQ / contribution traceability (check 1)

Section numbers as printed; file:line of the anchoring text.

| Thread | Stated (Ch1) | Gap (Ch3 §3.5) | Built (Ch4) | Measured (Ch5) | Interpreted (Ch6) | Answered (Ch7) |
|---|---|---|---|---|---|---|
| RQ1 | §1.3 quote block, ch1:94-98 (prd §2 verbatim; script PASS) | Synthesis l.302-319 ("No study reviewed here combines all four"); l.357-358 names RQ1 | §4.3 the candidates l.278-283; §4.5 selection rule and statistical plan l.651-674 | §5.2 l.69-72 (central measurement); §5.7 l.314-385 (rule applied) | §6.1 l.18-68 (frontier read as RQ1's trade-off) | §7.1 l.20-44 (direct answer) |
| C1 schema + bounded GBNF grammar | l.110-114 | G1 l.321-329 -> C1 | §4.1 l.10-123 (schema, grammar listing, bounds, 90-char / 96-token argument) | §5.2 l.89-94 (validity 1.000 on 18 rows); §5.5 l.241-264 (ablation) | §6.2 l.160-180 (common-cause hypothesis); §6.3.2 l.317-328 (small schema) | §7.2 l.49-58 |
| C2 label-first dataset | l.115-119 | G2 l.331-339 -> C2 | §4.2 l.125-274 (label first, families 96/12/12, leakage gate, golden set, seal) | §5.2 l.76-81 (three splits); §5.3 l.200-206 (zero-shot baseline the fine-tune is measured from) | §6.3.1 l.262-272 (labels and splits); §6.2 l.164-167 (what the 81 unknown pairs teach) | §7.2 l.60-68 |
| C3 quantised-inference harness | l.120-128 | G3 l.341-355 -> C3 | §4.4 l.385-397 (two surfaces); §4.5 tab:metrics l.556-586, tab:requirements l.623-649 | §5.2 l.69-156 (table 5.2, thermal, latency/throughput/memory, abstention); §5.4 l.211-236 (delta) | §6.1 l.70-103 (thermal axis, unmeasured points); §6.3.1 l.239-260 | §7.2 l.70-78 |

- G1 -> C1, G2 -> C2, G3 -> C3 hold: each Gap paragraph names its contribution once and only
  that one (script `positioning` rows PASS; read confirmed).
- What each Gap says the contribution delivers matches Ch1 and Ch5: G3's metric list "EM,
  intent and slot F1, schema validity, and false-command and safe-failure rates for three of the
  four fine-tuned models at Q8_0 and Q4_K_M ... accuracy under the deployed runtime and grammar
  ... throughput on the Raspberry Pi 5 at Q4_K_M" (ch3_soa:350-353) = Ch1 C3 (ch1:120-125) =
  Table 5.2's columns (Intent-F1, Slot-F1, EM, Safe-fail, Schema-valid, p50/p95, tok/s, Mem., Q4
  only timed) + Table 5.4 (false-command). G1's "grammar ablation, run with the harness of C3,
  decodes the same fine-tuned, quantised models with and without that grammar" = §5.5. G2's
  "recorded golden set on which the deployed configuration is scored" = §5.2's `test_golden`.
- The parameter-matched control (6.5 pp) is not a claimed contribution; Ch1 announces it
  (l.24-25, 145-146), Ch5 §5.3 measures it, Ch7 §7.2 l.80-88 reports it without a C-label. Not
  a finding (issue 08 settled this framing).

## 3. Headline-number occurrence table (check 3)

`abs` = abstract.tex, `fr` = frabstract.tex, `ar` = arabstract.tex, `soa` = ch3_state_of_the_art,
`met` = ch3_method (Ch4), `res` = ch4_results (Ch5), `dis` = ch5_discussion (Ch6),
`con` = ch6_conclusion (Ch7), `gen/` = thesis/generated.

| Value | Every file:line where it appears | Identical? |
|---|---|---|
| 0.935 EM golden (Qwen Q4_K_M) | abs:25; fr:27 (0,935); ar:27; res:78, 172, 373, 376; dis:43, 59, 290; con:23, 66, 81; gen/table17:19; gen/table18:14-15; gen/table33:13,19 | yes, always with "golden"/"reference text" where a qualifier is due |
| Frontier pair SmolLM2-360M / Qwen2.5-0.5B | abs:24; fr:26; ar:25-26; res:384; dis:25; con:22 | yes |
| p95 1,072 / 894 / 2,282 ms | res:122-123, 354, 356; dis:27; con:25, 29; gen/table17:12-14, 18-20, 24-26; gen/thermal:12,14,16 (2282.4 / 1072.4 / 894.2) | yes |
| tok/s 27.93 / 40.63 / 14.53 | ch1:31; met:44; res:122-123; gen/table17; gen/thermal | yes |
| RSS 0.68 / 0.55 / 1.63 GiB | res:126, 342-343; con:34 (0.68); gen/table17 | yes |
| 20 tok/s floor and 1,100 ms allowance | ch1:27-28, 154; soa:74, 277; met:593, 614, 636; res:124, 379-380; dis:79 | yes (floor = 22 tokens / 1.1 s, script PASS) |
| 3,122 ms re-baselined p95 (+622 ms, 25%) | abs:28-29; fr:31-33; ar:32-33; res:351, 363, 393; dis:64; con:33 | yes; 622 and 25% wherever 3,122 is |
| 6.5 pp family difference (0.935 vs 0.870, 15/2, p = 0.0023) | res:171-173; dis:40, 209, 216; con:80-83; gen/table33:14,19 | yes; "exploratory" at res:173, dis:216, con:83 |
| Ablation EM 0.8508 vs 0.8492; validity 1.0000 vs 0.9997; 0.17 pp; 1 in 3,540 | res:246-249, 255, 261; dis:121, 162-163, 325; con:51-53, 57; gen/table19:12-13 | yes (see NIT-1 on 0.17 vs 0.16 from the rounded cells) |
| Safe-failure 0.0000-0.1579, pooled 0.0530 / 528; false-command 0.1867-0.3933 | res:144-146; dis:116-117; con:39-40; gen/nfr18:12-17 | yes (but see MAJOR-1: Ch2's definition would give a different range) |
| Quantisation deltas -1.5 .. +1.5 pp; none significant, smallest p 0.25 | res:218-225; con:73-74; gen/table18:12-17 | yes |
| Model sizes 0.36-1.2 B; 362 / 494 / 514 M; 1.24 B = 1,236 M | ch1:96; abs:11; fr:9-10; ar:11; soa:52, 137, 277; met:280, 287-288; res:79-80, 161, 165-166; dis:18, 39; con:21, 28; ch2 tab:bg-models:110-113; gen/table33:12-15 | yes; 1.24 B (ch2:113, res:80, 161, con:28) and 1,236 M (gen/table33:15) are one value at two roundings (see MINOR-2) |
| 17.5 pp (significant) / 2.5 pp (not established) / 15.0 pp | abs:25-26; fr:28; ar:29; res:79, 174, 290-291; dis:27, 33; con:26 | yes; "significant" attached at every 17.5, "not established/does not establish" at every 2.5 |
| 18.13 tok/s uncooled; 25.1-41.3% / 35.2-68.5% | ch1:33; res:115; con:77-78; gen/thermal:15, 21 | yes |
| 200 golden items; 3,540 decodes; 590 items | abs:14; fr:14; ar:14; met:39, 162, 203; res:11, 202, 242, 246; con:65, 70 | yes |

## 4. Abstract comparison (check 4)

| Claim / number | EN (abstract.tex) | FR (frabstract.tex) | AR (arabstract.tex) | Chapters | Agree? |
|---|---|---|---|---|---|
| 0.36-1.2 B, fine-tuned, quantised, CPU-only Pi 5 | l.10-12 | l.9-11 (0,36 à 1,2) | l.10-13 (0.36 / 1.2) | ch1:95-97 (RQ1) | yes |
| Frozen schema + matched grammar; validity a property of the decoder | l.15-16 | l.13-14 | l.16-17 | ch1:110-114; met §4.1; con §7.2 | yes |
| Label-first pipeline; template-family splits; golden set of 200 recorded commands | l.16-18 | l.14-17 | l.17-19 | met:130-137, 182-186, 203-205 | yes |
| Four models, one recipe; three quantised at two levels, Q4_K_M timed on the board; fourth measures a family difference at fixed size | l.18-20 | l.17-20 | l.19-22 | met:278-283, 375-379; res §5.3 | yes (issue 08 M-1 wording present in all three) |
| Selection rule fixed before any result | l.20 | l.20-21 | l.21-22 | met:651-653 | yes |
| Among the three timed: two non-dominated (SmolLM2-360M, Qwen2.5-0.5B); Qwen at Q4_K_M deployed | l.23-25 | l.25-27 | l.25-27 | res:368-385; con:20-23 | yes |
| 0.935 EM on the golden set, scored on reference text | l.25 | l.27-28 | l.27-28 | res:78; con:23 | yes |
| SmolLM2 faster, 17.5 pp less accurate, significant | l.25 | l.28-29 | l.29 | res:290-291; con:26 | yes |
| Llama slower; lower accuracy not statistically established | l.26 | l.29-30 | l.29-30 | res:283-291; con:27-29 | yes |
| Selection on accuracy against re-baselined constraints; misses 2,500 ms by 622 ms; re-baselined to 3,122 ms | l.27-29 | l.30-33 | l.30-33 | res:359-366, 392-394; con:31-33 | yes |
| Every configuration misses safe-failure and false-command; one tendency (well-formed command instead of declining) | l.29-31 | l.33-35 | l.33-35 | res:143-156; con:38-42 | yes |
| Confidence gate is the first step proposed | l.31-32 | l.35-36 | l.35 | con:100-107 | yes |
| Keywords (8) | l.36-37 | l.38-39 | l.37-39 | -- | same eight in the same order |

Against the new chapter set: the abstracts describe the study (question, method, findings) and
do not enumerate chapters, so the new Background and State of the art change nothing they say;
the C3 metric list is not quoted in any abstract. The Arabic was read sentence by sentence: it
carries the same eleven claims, the same seven numbers and the same qualifiers ("دالّ إحصائيًا" =
significant; "غير مُثبتة إحصائيًا" = not statistically established; "أُعيد ضبطها" = re-baselined;
"محسوبةً على النص المرجعي" = scored on reference text). No abstract claims more than Ch5/Ch7 show.
Nothing in any abstract mentions the 6.5 pp control result or the 0.68 GiB figure, so their
"exploratory" / "language-model process only" qualifiers are not owed there.

## 5. Scorecard

| # | Check | Result |
|---|---|---|
| 1 | Golden thread | PASS |
| 2 | Contributions claimed = demonstrated; Background claims nothing | ISSUES (1): MINOR-4 (four "in this work" sentences in the Background) |
| 3 | Headline numbers identical everywhere | PASS (NIT-1 on a rounding presentation) |
| 4 | Three abstracts agree, claim no more than the chapters | PASS |
| 5 | Definitions and notation consistent | ISSUES (2): MAJOR-1 (safe-failure denominator), MINOR-5 (FP16/fp16) |
| 6 | Every forward/backward reference lands where it says | ISSUES (2): MINOR-1 ("six chapters in three parts"), MINOR-2 (Table 2.1 caption points at Chapter 4 for counts it does not give) |
| 7 | Write-once across documents | PASS (one Ingénieur-side NIT noted for issue 10's successor, not a Master finding) |
| 8 | Front/back matter | ISSUES (1): MAJOR-2 (TOC page and anchor of the Bibliography) |
| 9 | Scope from Ch1 alone | PASS |
| 10 | Clean build | PASS |

## 6. Findings (sorted BLOCKER -> NIT)

| # | Sev | Check | file:line | Quoted text | Problem | Evidence | Proposed fix |
|---|---|---|---|---|---|---|---|
| MAJOR-1 | MAJOR | 5 | thesis/master/ch2_background.tex:392-394 (and 395-396) | "The safe-failure rate is the fraction of the system's errors on in-domain input that resolve to a harmless action" | Definition drift between the Background and the definition of record. tab:metrics (ch3_method.tex:574) and prd Table 10 define it "among items where EM is 0", with no in-domain restriction, and every reported value uses that denominator: the range 0.0000-0.1579 (ch4_results.tex:144-145; ch6_conclusion.tex:39) has its maximum on Qwen Q4_K_M's `test_ood` row, and the pooled 0.0530 = 28/528 (ch4_results.tex:145; ch5_discussion.tex:116-117) counts the 246 out-of-domain errors (24 of the 28 "safe" events are out-of-domain hovers). Under Ch2's definition the range would be 0.0000-0.0417 and the pooled figure 3/282 = 0.0106, so a reader who takes Ch2 at its word cannot reproduce Ch5's numbers | `results/nfr9_nfr18_abstention.csv`: `test_ood` rows carry safe_failure_rate 0.1071 / 0.1000 / 0.1579 / 0.1500 / 0.0588 / 0.0678; in-domain rows max 0.0417; `results/limitation_abstention.md` §1 "0.0000 to 0.1579; pooled 0.0530 (28 of 528 errors)" over "all 3,540 items"; ch5_discussion.tex:130-132 counts 282 in-domain errors separately | l.392-394: "The \emph{safe-failure rate} is the fraction of the system's errors, on any input, that resolve to a harmless action, such as declining or holding position, rather than to a wrong command." l.395-396: "The first has out-of-domain items as its denominator, the second the erroneous items of every split; neither is a function of \gls{em} ...". Check `tools/review/master_bg.py` for an anchor on the sentence before editing (the report lists "false-command and safe-failure denominators" only under definitions to verify) |
| MAJOR-2 | MAJOR | 8 | thesis/main_master.tex:96-98 | `\printbibliography` / `\addcontentsline{toc}{chapter}{Bibliography}` | The contents page prints "Bibliography ... 79" and its hyperlink targets `Item.3` (the last item of Ch7's enumerate), but the bibliography heading is on page 75 (Ch7 ends on 74; the 51 entries fill pages 75-79). The `\addcontentsline` runs after the five-page bibliography, so it records the page where it was executed. Issue 08 did not see this because the 45-entry bibliography of the 63-page build fitted on one page | built PDF: page 75 opens "Bibliography [1] Tung Nguyen ..."; page 79 ends with [51]; `build/master/main_master.toc`: `\contentsline {chapter}{Bibliography}{79}{Item.3}` | Replace the two lines by `\printbibliography[heading=bibintoc]` (biblatex adds the entry at the heading with a correct anchor); or keep `\printbibliography` and put `\clearpage\phantomsection\addcontentsline{toc}{chapter}{Bibliography}` \emph{before} it. Rebuild and confirm the TOC reads 75 |
| MINOR-1 | MINOR | 6 | thesis/master/ch1_introduction.tex:136 | "The rest of this document has six chapters in three parts." | Ch7 sits outside the parts (main_master.tex:77-79; TOC: Part III = Chapters 4-6, Chapter 7 follows unparted). Six chapters follow, but five are in the parts; the sentence promises a structure the TOC does not show. The `master_ch1.py` check counts only "six chapters" | build/master/main_master.toc: `\contentsline {part}{III ... Contribution}` precedes chapter 4; chapter 7 has no part above it; SKILL.md §3 "Introduction and Conclusion sit outside the parts" | "The rest of this document has six chapters: five in three parts, and a conclusion outside them." (the rest of the paragraph already describes Ch7 without a part) |
| MINOR-2 | MINOR | 6 | thesis/master/ch2_background.tex:102-104 and 113 | "Parameter counts are those of the released checkpoints, rounded to the nearest million (Chapter~\ref{chap:method})" / "Llama-3.2-1B-Instruct & Meta & 1.24~B" | Two defects in one caption. (a) Chapter 4 gives only 514 M and 494 M (ch3_method.tex:287-288); 362 M and 1,236 M appear only in Table 5.5 (generated/table33_iso_parameter.tex:12, 15), so the pointer does not land where the counts are. (b) The Llama row is rounded to ten million ("1.24~B") in a table whose caption promises the nearest million; Table 5.5 prints 1,236 M for the same checkpoint | ch3_method.tex:287-288 ("514~M parameters against 494~M ... counted from the released checkpoints"); table33:15 "1,236 M"; master_bg.py claim l.113 anchors on "Meta & 1.24~B" | Row: "1{,}236~M". Caption: "Parameter counts are those of the released checkpoints, rounded to the nearest million, counted as in Section~\ref{sec:lora}; the developer's report is cited for each model." (a `\ref` to Table 5.5 would trip master_bg.py's "no table of another chapter in the Background" check). Update the script's l.113 expectation from 1.24 B to 1,236 M |
| MINOR-3 | MINOR | 1 | thesis/master/ch3_state_of_the_art.tex:354 | "It reports the accuracy cost of the whole deployment pipeline on this task at sub-billion scale" | G3's scope claim is narrower than what C3 measures: one of the three quantised models, Llama-3.2-1B, has 1.24 B parameters (ch6_conclusion.tex:28; table33:15), and the same chapter's This-work rows say "0.36--1.2~B" (l.52, 137, 277). "Sub-billion scale" is used two paragraphs earlier for Wang et al. in its literal sense (l.111, 348), so the reader takes it literally here | ch2_background.tex:91-92 "between a third of a billion and one and a quarter billion"; RQ1 "0.36--1.2~B" | "on this task at the 0.36--1.2~B scale" (or "at sub-billion to 1.2~B scale"); no script anchor on this sentence (master_ch2.py's l.347-348 anchor is the previous sentence) |
| MINOR-4 | MINOR | 2 | thesis/master/ch2_background.tex:204-205, 227-228, 338-340, 426-429 | "Two are used in this work." / "The Raspberry~Pi~5 used in this work carries" / "The \gls{stt} stage in this work is a model of the Whisper family" / "stated before the results exist, it keeps the choice from being made to fit them" | Four sentences state what this work chose or a methodological position, in a chapter whose charter (l.11-14, prd §3.1, SKILL §3) is "no positioning, no results, no design decisions". Issue 15 removed the one such sentence that carried a justification (A-2) and passed the chapter with these four; they are scoping statements rather than arguments, so this is for the author's judgement, not a re-raise | prd §3.1 item 2 "Foundations only ... no positioning"; master_bg.py's `foundations` checks look for numbers, decisions and codes, not for "in this work" | l.204-205 "Two are described here."; l.227 "The Raspberry~Pi~5 carries ..."; l.338 "A model of the Whisper family, an encoder--decoder transformer ..., is the usual choice for this stage; it is served by ..."; l.428-429 drop "stated before the results exist, it keeps the choice from being made to fit them" (Method l.651-653 already makes that point where it belongs) |
| MINOR-5 | MINOR | 5 | thesis/master/ch5_discussion.tex:40, 42, 140 | "scores 6.5~pp lower on the golden split at FP16" | Notation: "FP16" here against "fp16" at its expansion (ch3_state_of_the_art.tex:50 "16-bit floating point (fp16)") and at all 17 other uses (Ch3 x4, Ch4 x7, Ch5 x3, Ch6 l.227, Ch7 x2) | grep: FP16 only at ch5_discussion.tex:40, 42, 140 | "fp16" at the three sites |
| NIT-1 | NIT | 3 | thesis/master/ch4_results.tex:247 | "\Gls{em} moves from 0.8508 to 0.8492, a difference of 0.17~pp, or six decodes in 3{,}540" | 0.8508 - 0.8492 = 0.16 pp from the printed cells; 0.17 pp is 6/3,540 = 0.169 pp from the counts (script PASS on the counts). A reader subtracting Table 5.7's cells gets 0.16 and sees 0.17 stated five times (res:247, 261; dis:163; con:52, 57) | generated/table19_grammar_ablation.tex:12-13 | Either "a difference of six decodes in 3{,}540 (0.17~pp)" at first statement, or have `eval/tables.py` print the ablation EM to five decimals (0.85085 / 0.84915) so the cells subtract to 0.17 |
| NIT-2 | NIT | 10 | thesis/main_master.tex:14-15, 47-48 | "Chapters not yet written are listed commented-out below" / "One figure and seven tables: the two lists share a page" | Stale comments: every chapter is written and `\input`; the lists now hold one figure and twelve tables (they still share page 8, so the `\let\clearpage\relax` trick still holds). Comment-only; nothing prints | LoT in the PDF: 2.1, 3.1-3.4, 4.1-4.5, 5.1-5.7 | Update or delete the two comments |

Ingénieur-side note (not a Master finding; for the Ingénieur's next pass):
`thesis/ingenieur/ch4_implementation.tex:216` "\paragraph{Artefacts from the M\'emoire de
Master.}" is the one occurrence of the Master's name in either document without `\emph`
(SKILL §4.1; D6b).

## 7. Acronym table (check 8)

Keys used in the Master's inputs (`\gls`, `\glspl`, `\Gls`, `\acrshort`, `\Acrlong`, `\glsadd`;
no `\acrfull` anywhere) against `thesis/shared/acronyms.tex` and the printed List of Acronyms
(page 9 of the PDF, 20 entries).

| key | used in | in acronyms.tex? | printed? |
|---|---|---|---|
| bnf | ch2, soa | yes | yes |
| cpu | ch1, ch2, soa | yes | yes |
| crr | met, dis | yes | yes |
| em | ch1, ch2, soa, met, res, dis, con, gen/table17, table18, table19 | yes | yes |
| gbnf | ch1, ch2, soa, met, res, gen/table17, table18 | yes | yes |
| ggml | ch1 (`\glsadd`), ch2 (`\gls`) | yes | yes |
| gguf | ch2, soa, met, res | yes | yes |
| gpu | ch2, soa, met, res, dis | yes | yes |
| json | ch1, ch2, met, res | yes | yes |
| llm | ch2 | yes | yes |
| lora | ch2, met | yes | yes |
| rms | met | yes | yes |
| sbc | ch1, ch2, soa, dis | yes | yes |
| slm | ch1, ch2, res, dis, con, gen/thermal | yes | yes |
| snr | met, dis | yes | yes |
| stt | ch1, ch2 | yes | yes |
| tts | met | yes | yes |
| uav | met | yes | yes |
| vad | met | yes | yes |
| wer | ch2, met, res, dis | yes | yes |

20 keys used, 20 defined-and-printed; the six other keys in `acronyms.tex` (pid, fr, nfr, fa,
roc, udp) are Ingénieur-only and correctly absent from this list. Hand-typed acronyms flagged
by the scripts (CPU, LoRA, JSON, "single-board computer", "small language model") are in
headings, the quoted RQ1 or already-justified sites (issues 01-05, 15); not re-raised.

Other front matter: every `\caption` has a short form, and the LoF (1 entry) and LoT (12
entries) print them (page 8). Bibliography: 51 distinct `\cite` keys across the Master inputs,
none missing from `references.bib` (82 entries), and the PDF prints exactly [1]-[51]. Title page:
diploma, field, specialty (IASD), theme = working title of prd Table 2, author, supervisor,
"September 2026", "Academic Year: 2025/2026" -- all correct; the two jury placeholders are by
the author's choice.

## 8. Scope answers (check 9), from Ch1 alone

- System end to end with one example command: yes -- ch1:76-81, "form a circle with radius five
  metres": STT -> fine-tuned SLM under the grammar -> validator -> swarm controller.
- What is real and what is simulated: yes -- ch1:83-85, speech real through the deployed
  microphone; aircraft simulated (software-in-the-loop, five vehicles, no physical flight);
  controller and simulation on a workstation linked to the board (ch1:80-81).
- Language and command vocabulary: yes -- ch1:76 "spoken English commands"; ch1:81-83 ten
  intents from take-off and landing to formations and parameter changes, plus the two keyword
  phrases.
- Out of scope: yes -- ch1:86 reinforcement learning, vision input, languages other than English.
- Division between the two documents: yes -- ch1:87-89 (research half / engineering half),
  ch1:100-103 (RQ2, RQ3, architecture, runtime, demonstration to the Ingénieur), ch1:113-114 and
  131-133 (validator, state machine, C4 to the Ingénieur).

## 9. Build report (check 10)

`cd thesis && rm -rf build/master && latexmk main_master.tex` (checked first: no latexmk or
xelatex process running). Exit 0. `build/master/main_master.log`: 0 lines matching `^!`, 0
`Citation.*undefined`, 0 `Reference.*undefined`, 0 `Float too large`, 0 `Overfull`. Remaining
warnings are the three issue 08 judged non-findings (Amiri small-caps shape on the Arabic cover,
biblatex "Language 'arabic' not supported", microtype footnote patch) -- no action.
`pdftotext main_master.pdf | grep "TODO\|CHECK\|figtodo\|\[President Name\]"`: only the two
expected jury placeholders (lines 38 and 40 of the text). Page count 80. Contents: two pages
(pp. 6-7), 37 numbered entries (7 chapters, 3 parts, 29 sections/subsections) plus
Bibliography; Parts I "Background", II "State of the art", III "Contribution" are printed in
the TOC, Chapter 1 before Part I and Chapter 7 after Part III's last chapter, as required. LoF +
LoT share page 8; List of Acronyms page 9; Chapter 1 page 10; Bibliography pages 75-79 (TOC says
79: MAJOR-2). `tab:metrics`'s last row ("Convergence") is typeset (page 49-50).

## 10. UNVERIFIED

- The Arabic abstract was read by a non-native reader; the sentence-by-sentence match in §4 is
  a reading, not a certification, and pdftotext does not reproduce shaped Arabic well enough to
  grep the built page.
- Whether `tools/review/master_bg.py` anchors on the safe-failure sentence (MAJOR-1) or only on
  "Meta & 1.24~B" (MINOR-2, confirmed from the report): the scripts were not re-run by this
  review; the reports at HEAD were used as is.
- ch3_method.tex:213-215 "the \emph{Mémoire d'Ingénieur} states the consequence [of the two
  unrecorded sessions] for its runtime validation as a limitation": the Ingénieur's Ch6 l.127
  "Scope of a single run. One run, by one speaker in one room ..." covers the consequence in
  general terms; whether it names the two planned sessions was not checked (the Ingénieur was
  read only for write-once overlap).
- The three Ingénieur-sourced figures the Master quotes (CRR 0.690 / 0.590, ch5_discussion:289;
  "two to six of the 200 items per condition", ch3_method:473; 226 / 78 trials, ch3_method:483-484)
  were matched against `ingenieur/ch5_validation.tex:265, 278` and `results/exp2_latency_budget.md`
  for the first and third; the "two to six" item was not traced.
