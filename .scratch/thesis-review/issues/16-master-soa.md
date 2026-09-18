# Issue 16: master-soa (State of the art, Chapter 3 since 25 Sep)

Status: resolved
Blocked by: 02 (resolved); runs beside 15 (Background), as 13 ran beside 12
Chapter: thesis/master/ch3_state_of_the_art.tex (341 lines, 19 keys, 57 citation sites; rebuilt 25 Sep, committed `7830694`)
Script: tools/review/master_ch2.py (the file name keeps the chapter's old number; the script was re-pointed at the new file and shape in `4bb8138` and `7830694`)
Report: .scratch/thesis-review/reports/master_ch2.md

Numbered 16 because it was drafted after 00-15 existed (spec.md: issues are never renumbered).
Issue 02 reviewed the old Chapter 2 (Related work) and was resolved on 2026-09-23. The chapter was
then rebuilt for the supervisor's request of 25 Sep: the same four themes, each now a taxonomy of
the reviewed studies, one comparison table per section along fixed axes with this work as the last
row, a "Critical comparison" paragraph reading each table, and the former Positioning replaced by
"Research gaps" (Synthesis, then G1-G3 mapped one to one onto C1-C3). Its foundations moved to the
new Background (issue 15). No bibliography entry was added: every table cell states only what the
prose or the verified candidate notes establish, and a dash marks the rest.

Issue 02's citation verdicts (24 rows) still apply to the sentences that survived the rewrite; the
citation agent re-checks the changed sentences and every table cell.

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_ch2.py
```

## Agents

- **Citation agent** -- D5 only. Worklist: the report's citation sheet (57 sites, 19 keys) and
  "Numbers quoted from papers" (25 models / 3 SBCs / 2 runtimes / 1.5 B / 4x; AWQ's one percent;
  SpQR's under one percent; 8 B and above; Kurtic's smallest 1.5 B; MASSIVE's 1 M / 51 / 60 / 55 /
  258-580 M / 85.1-86.1 / 73.6-76.8 / 63.7-66.6). Open each identifier; verdict per row SUPPORTS /
  PARTIAL / DOES NOT SUPPORT / COULD NOT ACCESS. Every cell of the four tables is a claim about the
  cited source (a wrong cell is a BLOCKER; a dash is never a finding). Issue 02's Comments hold the
  earlier verdicts for the same keys; reuse them where the sentence is unchanged, say so.
- **Argument agent** -- D1, D2, D4, D6, D8, D10, D11, D12. Focus: (a) each critical comparison
  compares the studies to each other and reads its table column by column, and compares to this
  thesis only in Research gaps (the chapter's own promise, l.10-11); (b) every "silence" claim
  ("none of these studies", "no work in the table", "not reported anywhere") is scoped to the
  studies reviewed, not to the literature; (c) the "This work" rows and the G1-G3 paragraphs promise
  nothing Chapters 4-6 do not deliver, with the C3 wording of Ch1 (three of four models, two levels,
  accuracy on the workstation, timing on the Pi at Q4_K_M) as the reference; (d) examiner view of the
  two thin tables (3.1 and 3.4 hold two prior works each).
- **Verifier.**

## What the script establishes (baseline: 0 FAIL, 2 WARN, 57 PASS)

- Four theme sections in prd.md §3.1 order, each with a table ending in a "This work" row and a
  Critical comparison paragraph; one closing Research gaps section with Synthesis and G1-G3, each
  gap closed by its contribution.
- Research gaps cites nothing the theme sections did not review; no Outlines; no voice-UAV
  literature; the Ingénieur named correctly; all four models cited where first named.
- All 19 paper-number anchors present (four of them now in Background l.167-199).
- WARN: six numbers in the tab:soa-slu MASSIVE row are UNTRACED by the number trace (they are the
  same figures the prose quotes at l.245-246 with a citation; the trace does not look inside table
  rows). WARN: l.51 "three fine-tuned models, plus a control" against Ch1's "three deployment
  candidates" plus a control.

## Seeded findings (leads, to be verified like any other)

- l.266 tab:soa-slu "This work" row states a "1{,}100~ms decode allowance". The figure is Ch1 l.27
  and Ch3(method) l.588-631, so it is in scope, but it is the only latency-budget number in this
  chapter and Table 3 gives the latency budget to the Ingénieur -- judge whether the row should
  carry the 20 tok/s floor instead, as l.70 does.
- l.51 tab:soa-edge "Three fine-tuned models ... plus a control" vs l.67 "four fine-tuned models" vs
  l.135 tab:soa-quantisation "Three fine-tuned models" -- one story?
- l.108 and l.131 "smallest 1.5~B" for kurtic2025: verify in the paper (issue 02 #11 recorded a
  1.5 B model there; confirm which).
- l.130 and l.212 llama.cpp rows: "Optional" grammar, "cost depends on rule shape" -- is the
  README the source for both?
- l.71-73: the control "reported at fp16 only, because llama.cpp segments its prompt differently
  from the tokeniser it was trained under" -- Ch3(method) l.377, l.445 give the reason; agree?
- Stale text in the script's "For the argument agent" block (Gap l.162-176, Delta): it describes
  the old chapter. Tooling fix, not a chapter finding.

## Comments
### 2026-09-25 -- review round 1 (citation + argument + verifier)

Script baseline: 0 FAIL, 2 WARN, 57 PASS (report regenerated after the stale "For the argument
agent" block in master_ch2.py was rewritten for the new chapter shape).

Agent reports: `agents/16-master-soa/{citation,reviewer,verifier}.md`.

Verdict (both agents): ready after fixes. The chapter has the frozen shape (four themes, one table
each ending in a This-work row, a Critical comparison under each, Research gaps with Synthesis and
G1-G3 mapped onto C1-C3); D1 PASS, D6 PASS, acronyms all `\gls`, ASCII, British spelling. Twelve of
fourteen silence claims are scoped to the reviewed studies. Of issue 02's twenty-four fixed
overclaims, one crept back (#11, the "8 B and above" scale claim).

Citations (57 sites): 53 SUPPORTS, 4 PARTIAL, 0 DOES NOT SUPPORT, 0 COULD NOT ACCESS; all 19 quoted
paper numbers found at the stated value; all 19 bib entries agree with their primary pages (spqr
and awq fixes from issue 02 are in).

Verified BLOCKER/MAJOR (verifier: 11 of 11 confirmed, two PARTLY on literal wording, one raised,
one NEW):

| # | Sev | Line | Finding | Verifier | Fix (verifier §3 has the exact wording) |
|---|---|---|---|---|---|
| B1 | BLOCKER | 329-331, 147-149 | "those that score tasks at all work at eight billion parameters and above" -- refuted by the chapter's own Table 3.2 (Kurtic 1.5 B; Wang sub-billion) and Synthesis l.296 | CONFIRMED | "the two that score tasks at scale work at 1.5 B and above, and the one sub-billion evaluation scores generic suites too"; l.147-149 "two of the three evaluations ... the third, the one study of sub-billion models" |
| B2 | BLOCKER | 131 | Kurtic cell "Llama-3.1 family; smallest 1.5 B" -- the 1.5 B model is DeepSeek-R1-Distill-Qwen-1.5B (Table 4, reasoning suites); Llama-3.1 is 8/70/405 B | CONFIRMED | cell "Llama-3.1-Instruct at 8, 70 and 405 B; DeepSeek-R1 distillations from 1.5 B, on reasoning suites"; add paper-number anchor ("8, 70 and 405~B", kurtic2025) to the script; keep the l.108 anchor "has 1.5~billion parameters" and append the qualifier after it |
| B3 | BLOCKER (raised from MAJOR) | 48 | sbc2025 cell "formats as distributed" -- source: "All models were quantized using the q4_k_m quantization scheme" | CONFIRMED | cell "Ollama and Llamafile; Q4\_K\_M throughout" |
| M1 | MAJOR | 66-77, 279-285 | Positioning and design rationale inside two critical comparisons (model list, the control's fp16 reason, the runtime; G2 restated) breaks prd §3.1 "to this thesis only in the gaps" and the chapter's own l.10-11 | CONFIRMED; ruling: a one-sentence hand-off reading the last row is fine (l.233-234 is the model), a gap statement or design rationale is not | l.66-77 -> three sentences that keep the anchor "Three of those models are carried through to quantised artefacts" (text_claim, script l.72-74) and the four model cites; l.279-285 -> one hand-off sentence |
| M2 | MAJOR | 51, 135 | This-work rows imply accuracy on the Pi at both levels and timing at both levels; Ch5: accuracy on the workstation, timing on the Pi at Q4_K_M only | CONFIRMED | l.51 row rewritten (Hardware "Pi 5, three cores (timing); workstation, same runtime (accuracy)"; metrics "... throughput, latency, memory at Q4\_K\_M"); l.135 "throughput on the board at Q4\_K\_M" |
| NEW-1 | MAJOR (bordering BLOCKER) | 51 | Same row: "llama.cpp; Q8_0 and Q4_K_M against fp16" beside "Raspberry Pi 5" says the fp16 reference was a llama.cpp run on the Pi; Method l.386-389: transformers on a Kaggle T4, no grammar | NEW | folded into the M2 row rewrite: "against an fp16 reference decoded under \texttt{transformers}" |
| M3 | MAJOR | 214 | Ablation cell promises F1; Table 19 reports schema validity and EM only (the CSV has the F1 columns, unreported) | CONFIRMED | "Yes: \gls{em} and schema validity with and without the grammar" (or add F1 to Table 19 via eval/tables.py -- out of scope here) |
| M4 | MAJOR | 282, 320 | "No existing corpus covers this command vocabulary" scoped to the world; Method l.127 says "No public corpus covering this vocabulary was found" | CONFIRMED | "no public corpus covering this command vocabulary was found" at l.320 (l.282 disappears under M1) |
| M5 | MAJOR | 63-64 | "an 8-billion-parameter model that no SBC serves at interactive speed" -- uncited; sbc2025 ran up to 7 B, >= 3 B below 5 tok/s on the one board that could run them; "interactive" undefined | CONFIRMED | "an 8-billion-parameter model, larger than any the hardware benchmark ran, whose models of three billion parameters and above decoded below five tokens per second on the one board that could run them~\cite{sbc2025}" |
| M6 | MAJOR | 228-230 | Park misread: it does state task cost (correct solutions, GCD vs its aligned sampler ASAp, 38% geomean), never against unconstrained decoding | CONFIRMED | "... departs from the model's own grammar-conditioned distribution, and counts what that departure costs in correct solutions only against an aligned sampler, never against decoding without a grammar" |
| M7 | MAJOR | 210 | Park cell "divergence from the unconstrained distribution": KL is to the grammar-conditioned distribution (differs by a constant, which the paper states); correctness also counted | PARTLY (incompleteness, not falsity) | cell "Yes: Kullback--Leibler divergence from the model's grammar-conditioned distribution, and solution correctness on program-synthesis tasks, against an aligned sampler only" |
| M8 | MAJOR | 222-223 | "the three kinds do not cite one another's measurements ... on different models and tasks" -- Park cites Willard/Louf and Geng, extends Geng's implementation, reuses Geng's CP tasks; Tam cites Willard/Louf | PARTLY on the literal wording | "the cost studies measure the mask's effect in experiments of their own, so the literature establishes correctness and cost separately" |

MINOR/NIT (not verified; reviewer.md §3 and citation.md §4 have the wording): Kind taxonomy says
three kinds, table has four plus this work (MINOR-1); floor/budget/allowance/"this budget" for one
constraint, 1,100 ms at l.266 permitted under Table 3 but the fourth name (MINOR-2, verifier ruling
ii); structural vs schema validity never distinguished, l.234 crosses them (MINOR-3); Park's
Fine-tuned cell is a dash while l.223-224 says "no work" -- set to "No", verified (MINOR-4); l.60-61
"the two agree the engine is a variable of the same order as the model" does not follow from Kurt
(MINOR-5); golden set, template family, fp16 used before definition (MINOR-6); five metric lists
disagree, safe-failure only at l.266 (MINOR-7); two "show" (MINOR-8); l.51 "three ... plus a
control" vs l.67 "four fine-tuned" (MINOR-9, resolves the script WARN); "up to a few billion" ->
"135 M to 7 B" (cit-8); "parsed per request" -> "supplied per request" (cit-9); "shift ... is
recent" uncited and contradicted by the GPTQ row (cit-10 = NIT-5); "joint model as the modern
default" needs \cite{qin2021} (cit-11); "no calibration" -> "no calibration required" (cit-12);
smollm2 bib "and others" (cit-13); fourteen sentences over 40 words (NIT-1); two Gap lead-ins over
five words (NIT-2); l.339-340 names only Ch5 as answering RQ1 (NIT-3); two figurative phrases
(NIT-4).

Examiner questions: (1) why one SBC benchmark in Table 3.1 -- not answered (recommendation: a
one-sentence scoping statement, or an author-verified second row); (2) where is the robotics in
§3.4 -- half answered, M4's wording completes it; (3) why not compare the quantisation delta with
Kurt's -- answered at l.143-157.

Awaiting the author's decisions.

### 2026-09-25 -- fixes applied (author's decision: verified findings plus the factual MINORs)

Applied to thesis/master/ch3_state_of_the_art.tex, 27 edits, every one with the verifier's §3
wording where it gave one: B1 (G3 and the §3.2 critical comparison), B2 (Kurtic cell and the
l.108 qualifier, anchor `has 1.5~billion parameters` kept), B3 (Q4_K_M throughout; range 135 M to
7 B), M1 (l.66-77 reduced to the three-sentence hand-off that keeps the text_claim anchor; l.279-285
reduced to one hand-off sentence, so l.282's corpus claim is gone), M2 + NEW-1 (l.51 row: timing on
the Pi, accuracy on the workstation, fp16 reference under transformers, throughput/latency/memory
at Q4_K_M; l.135 "at Q4_K_M"), M3 (F1 dropped from the ablation cell), M4 (l.320 "no public corpus
... was found"), M5 (8 B sentence rewritten in words with \cite{sbc2025}), M6 and M7 (Park prose
and cell; Park's Fine-tuned cell set to "No", MINOR-4), M8 (citation-graph claim dropped; "show"
-> "find", MINOR-8). Factual MINORs: MINOR-1 (four kinds in §3.3; the runtime as a third kind in
§3.2), MINOR-3 (structural validity glossed against schema validity at first use; l.234 "schema
validity"), MINOR-5 (runtime inference restated), MINOR-6 (fp16 expanded at first use; golden set
and template family pointed at sec:dataset), MINOR-9 (l.51 "three fine-tuned candidates ... and a
fine-tuned, parameter-matched control"), cit-9, cit-10/NIT-5, cit-11, cit-12, NIT-3.

Left to the author's own pass (style, not applied): MINOR-2 (floor/budget/allowance; the 1,100 ms
cell at l.266 stays, permitted under Table 3 by the verifier's ruling ii), MINOR-7 (one metric list
in every This-work row; needs a one-word Ch1 change to add safe-failure to C3), NIT-1 (fourteen
sentences over 40 words), NIT-2 (two Gap lead-ins over five words), NIT-4 (two figurative phrases),
cit-13 (smollm2 "and others"). Examiner question 1 (why one SBC benchmark) remains a
recommendation: a scoping sentence or an author-verified second row.

Script: two paper-number anchors added to master_ch2.py ("135~M to 7~B" -> sbc2025, "8, 70 and
405~B" -> kurtic2025; expected values from the papers, not the prose), and the stale "For the
argument agent" block rewritten for the new chapter shape.

Final state: `master_ch2.py` 0 FAIL, 2 WARN, 59 PASS. WARN 1 (six UNTRACED numbers at l.266): the
MASSIVE figures repeated in the table row; the same figures are traced to the paper at l.245-246
and the trace does not look inside table rows -- justified. WARN 2 (coherence, "three quantised +
one fp16 control"): a warn=True claim by design; MINOR-9 makes the l.51 row and l.67 read as one
story -- justified. Self-test PASSED. Clean build: 0 errors, 0 undefined citations, 0 dropped
floats, 0 overfull, 79 pages.

### 2026-09-25 -- style items applied (author's decision: all remaining)

MINOR-2: the l.266 cell now names the constraint as the 20 tok/s throughput floor derived from
the 1,100 ms decode allowance; "throughput budget" no longer appears. MINOR-7: one metric list
("false-command and safe-failure rates") in both This-work rows and in G3; Chapter 1's C3 gains
"safe-failure rate" (written "false-command rate and safe-failure rate" so master_ch1.py's anchor
survives; a matching text_claim against nfr9_nfr18_abstention.csv added to that script). NIT-1:
every sentence over 40 words split, mostly at a colon or semicolon; none over 40 remains. NIT-2:
"Gap G1, validity after fine-tuning." and "Gap G3, deployment cost.". NIT-4: "without scoring the
output"; "fixes the constraint this thesis works under". Not applied: cit-13 (smollm2 "and
others" in references.bib -- the file has uncommitted edits from the Background review session,
so it is left for that session or the author); examiner question 1 (a scoping sentence for
Table 3.1 is a claim about the field, the author's to make).

Final state: master_ch2.py 0 FAIL, 2 WARN (justified above), 59 PASS; master_ch1.py 0 FAIL,
3 WARN (pre-existing acronym warns, unchanged), 42 PASS; clean build 0/0/0/0, 79 pages.
