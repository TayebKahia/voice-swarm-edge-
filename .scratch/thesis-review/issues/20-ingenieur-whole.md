# Issue 20: whole-document pass, Ingénieur (seven chapters, two parts)

Status: resolved
Blocked by: 10 (resolved, on the six-chapter Ingénieur), 18, 19
Documents: thesis/main_ingenieur.tex

## What

Template B of `docs/agents/thesis-chapter-review.md`, repeated on the restructured Ingénieur.
Issue 10 ran it on 2026-09-24 against the six-chapter, 77-page document. Since then (26 Sep):
prd.md §3.1 rewritten to seven chapters in two parts (Part I Background and state of the art;
Part II Contribution; the closing chapter outside the parts), as the Master has had since 26 Sep;
a new Background (Ch2, issue 18); the State of the art rebuilt with four comparison tables and
Research gaps G1-G3 (Ch3, issue 19); the speech-component justification moved from the old Ch2 to
Architecture (Ch4, sec:component-choices); Ch1's structure paragraph rewritten for the parts;
Ch7's ref to the gap re-pointed. The three abstracts are unchanged since 24 Sep. 91 pages.

What this pass must see that the chapter reviews could not: the golden thread now runs
Ch1 (RQ2, RQ3, C4) -> Ch3 §3.5 (G1-G3) -> Ch4 (designed) -> Ch5 (built) -> Ch6 (measured) ->
Ch7 (answered); Background definitions used with one meaning by Ch3-Ch7; the abstracts against the
new chapter set; the List of Acronyms after the Background's new `\gls` uses (JSON, UDP, LoRA,
GGUF, GBNF now first used in Ch2); every printed bibliography entry cited; write-once against the
Master as it stands (Background vs Background especially). Known and left as deposited (STATE.md,
24 Sep): Ch5's "not built" statements about the demonstration chain, which cba9c1e has since built;
the pass reports them but they are the author's decision.

## Agents

One reviewer + verifier, as in issues 10 and 17. Not split by dimension.

## Comments

### 2026-09-26 -- review round 1 (reviewer + verifier)

Reviewed at 398b35a; agent reports `agents/20-ingenieur-whole/{reviewer,verifier}.md`. Clean build
by the reviewer: 91 pages, 0/0/0/0, only the two jury placeholders on the title page and nine
Background \TODOs in the PDF.

Verdict: ready after fixes, no rework. PASS on the golden thread (RQ2, RQ3, C4 -> G1-G3 -> Ch4 ->
Ch5 -> Ch6 -> Ch7), headline numbers identical at every occurrence across abstracts, Ch6, Ch7 and
the generated tables, write-once across documents, scope from Ch1 alone, 22 acronym keys, 46 cited
= 46 printed.

Findings (verifier: 18 confirmed, 0 refuted, 0 new):

| # | Sev | Where | Finding | Verifier | Fix |
|---|---|---|---|---|---|
| MAJOR-1 | MAJOR | ch3:448-452; ch7:397-406 | Gap G2 overclaims a stop "held to a latency budget of its own" over conceded MIRA; reflex misses 150 ms budget (545/547 ms p95, 965 ms median from onset vs MIRA's 466 ms) | CONFIRMED | Soften "held to" to "specified and measured against"; clarify what reflex adds over MIRA is a restricted two-command trigger by a derived rule and a localized budget miss, not raw speed |
| MINOR-1 | MINOR | ch3:337-343; ch4:543-568 | Verbatim duplication of open component descriptions (openWakeWord, Silero, Whisper) | CONFIRMED | Fix A: keep Ch3 descriptions and script anchors; replace Ch4 restatements with cross-references to Section 3.4 |
| MINOR-2 | MINOR | abstracts EN/FR/AR; ch6:420-421 | 540 ms reflex miss attributed solely to spotter delay rather than decision delay + quantisation + anchor error | CONFIRMED | Refine attribution across all three abstracts and Ch6 summary |
| MINOR-3 | MINOR | abstracts EN/FR/AR | "a rejection becomes a hold"; on the ground, in landing, or after abort it is a logged no-op | CONFIRMED | "and a rejection never becomes motion: in flight it becomes a hold" (FR/AR updated) |
| MINOR-4 | MINOR | ch1:139; ch6:119-120; tab 6.3 | Preemption verified in Ch6 only by 78/78 cancellations; ordering rule never needed in trials and verified only by Ch5 unit tests | CONFIRMED | Add note citing consumer unit tests in Ch6; update eval/tables.py and Table 6.3 cell |
| MINOR-5 | MINOR | ch7:361-366 | Stage allowances called "allocations" that "account for" 622 ms shortfall (treating percentiles as additive) | CONFIRMED | "three stages meet their allowances"; "The shortfall lies in two stages: ..." |
| MINOR-6 | MINOR | ch3:395-408 | RQ3 (noise robustness, safe degradation, formation quality) lacks literature motivation in Synthesis | CONFIRMED | Add synthesis sentence citing Contreras et al. distortion evaluation; anchor-safe |
| MINOR-7 | MINOR | ch2:348-350 | GGML undefined in List of Acronyms | CONFIRMED | Add `\glsadd{ggml}` in Ch2 l.348 |
| MINOR-8 | MINOR | ch6:259-261 | CRR comparator never defines "correct" or cites Master's canonical comparator | CONFIRMED | Add sentence citing Master's canonical comparison |
| MINOR-9 | MINOR | ch7:160-162 | Convergence attributed to potential field rather than PID formation control law | CONFIRMED | Rephrase to controller terms (formation law, potential field, flocking) |
| MINOR-10 | MINOR | ch7:286-291 | Proposing repulsive potential field as clamp replacement reverses thesis argument on soft mechanisms | CONFIRMED | Rephrase: kinematic feasibility constraints, noting potential field is a soft mechanism whose failure modes are known (koren1991) |
| MINOR-11 | MINOR | master ch2:339-346 | Master restates speech pipeline details | CONFIRMED (Master side) | Left to author; not touched during Ingénieur pass |
| MINOR-12 | MINOR | ch6:284-286 | 10 dB error breakdown sum is 81/82, missing 1 misparsed perfect transcript | CONFIRMED | Append: ", and one utterance transcribed perfectly was misparsed." |
| NIT-1 | NIT | ch2:340; ch5:216 | Missing `\emph{...}` around Mémoire de Master in headings | CONFIRMED | Apply `\emph{M\'emoire de Master}` |
| NIT-2 | NIT | ch3:406-407 | Gaps order claim does not match closer section order | CONFIRMED | "stated below, each with the part of the design of Chapter~\ref{chap:architecture} that closes it," |
| NIT-3 | NIT | ch2:345 | "a SLM" -> "an \gls{slm}" | CONFIRMED | "an \gls{slm}" |
| NIT-4 | NIT | ch1:183, 201 | "from end-of-speech" -> "from the end of speech" | CONFIRMED | Apply |
| NIT-5 | NIT | ch4:458-460 | "the deployment constraint" -> "deployment constraints" | CONFIRMED | Apply |
| NIT-6 | NIT | ch1:66-91 | Explicit out-of-scope sentence in Ch1 | CONFIRMED | Add sentence after line 91 |

### 2026-09-26 -- fixes applied (author's decision: all confirmed Ingénieur items applied)

Applied:
- MAJOR-1: Gap G2 latency claim rephrased; MIRA latency comparison added to Ch7.
- MINOR-1: Component duplication replaced with Section 3.4 cross-references in Ch4.
- MINOR-2 & MINOR-3: Abstracts updated across EN, FR, AR for rejection and latency attribution.
- MINOR-4: Consumer unit test note added to Ch6; eval/tables.py and Table 6.3 cell updated.
- MINOR-5: Budget allowances phrasing corrected in Ch7.
- MINOR-6: RQ3 synthesis sentence added to Ch3.
- MINOR-7: `\glsadd{ggml}` added to Ch2.
- MINOR-8: Master canonical comparison cross-reference added to Ch6.
- MINOR-9: Controller terms convergence attribution corrected in Ch7.
- MINOR-10: Collision avoidance future work aligned with thesis arguments in Ch7.
- MINOR-12: 10 dB error breakdown sum corrected to 82 in Ch6.
- NIT-1 through NIT-6: all applied.

Final build: `main_ingenieur.pdf` 91 pages, 0 errors, 0 warnings, 0 undefined refs/cites, 0 overfull. List of Acronyms includes GGML. Ready for Ingénieur layout pass.
