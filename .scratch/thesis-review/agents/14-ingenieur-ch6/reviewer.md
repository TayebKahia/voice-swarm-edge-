# Issue 14 -- Ingenieur Ch6 (Demonstration, limitations, and conclusion) -- reviewer report

Chapter: `thesis/ingenieur/ch6_conclusion.tex` (390 lines, 2 cites: `pyflyt`, `koren1991`), as committed at `bd2ba37`.
Dimensions: D1, D2, D4, D5c, D6, D8, D10, D11, D12 (D3, D5a/b/d/e/f, D7, D9 are checked by `tools/review/ingenieur_ch6.py`).
Script re-run: `tools/review/ingenieur_ch6.py`: 0 FAIL, 0 WARN, 81 PASS.

## 1. Verdict

**Ready after minor fixes.** The chapter strictly implements the frozen outline from `prd.md` §3.1 item 6 (Demonstration protocol, Limitations, Future work, Conclusion). It opens by defining its scope and establishing that every number is inherited from Chapter 5 (`tab:requirements-summary`) with zero new measurements introduced.

The demonstration protocol (Section 6.1) fixes Part A and Part B in advance of the defence, establishing four unambiguous success criteria without prematurely claiming results. Section 6.2 candidly accounts for all limitations across simulation fidelity, the separation clamp at the integrator, acoustic degradation, the raw-intent state machine defect, and criteria verdicts. Section 6.3 establishes six direct, prioritised future work mappings. Section 6.4 answers RQ2 and RQ3 directly and unhedged against measured data, citing RQ1 in one sentence from the *Mémoire de Master*.

There are zero BLOCKERs and zero MAJORs. Five minor/nit items were identified: one long run-on sentence in Section 6.1 (MINOR-1) and four American spelling instances that should be converted to British English per project conventions (NIT-1 to NIT-4).

## 2. Scorecard

| Dim | Result |
|---|---|
| D1 Structure | PASS: Four sections match `prd.md` §3.1 item 6 exactly; lead-in establishes inheritance and scope; closing cleanly hands off to the defence demonstration. |
| D2 Argument coherence | PASS: Every section serves RQ2, RQ3, or the engineering demonstration of the dual-path runtime. Paragraphs follow Assertion -> Evidence -> Impact. |
| D3 Numerical accuracy | PASS: Verified by `tools/review/ingenieur_ch6.py` (81 PASS). Every figure traces to `results/` or Chapter 5. |
| D4 Claims and hedging | PASS: Section 6.4 concludes without hedging (0 prohibited modals). No unearned absolutes ("guarantee" absent, locked phrasing used for zero collisions backed by clamp). |
| D5c Uncited factual claims | PASS: Both external citations (`\cite{pyflyt}`, `\cite{koren1991}`) exist in `references.bib` and support their claims. |
| D6 Cross-document ownership | PASS: *Mémoire de Master* is named explicitly; RQ1 and speaker sensitivity are cited in single sentences without reopening Master-owned evidence. |
| D8 Language and style | ISSUES (1 MINOR, 4 NIT): Minor run-on sentence in 6.1 (MINOR-1); four `-ize`/`-er` American spellings (NIT-1 to NIT-4: *idealized*, *maneuvers*, *stabilization*, *optimized*). Acronyms are properly managed via `\gls{}`. |
| D10 Examiner view | PASS: Key examiner questions anticipated and answered: why the demo is planned for the defence, why safe-failure rate failed, why the clamp is needed, and why preemption recovery missed. |
| D11 Self-containment | PASS: No project-internal terminology (no `prd`, `spike`, `gate`, `session`). Codes (RQ2, RQ3, Part A/B) are defined in context. |
| D12 Headings and register | PASS: Headings are short noun phrases in sentence case; register is formal, technical, and objective. |

## 3. Findings

| # | Sev | Dim | file:line | Quoted text | Problem | Evidence | Proposed fix |
|---|---|---|---|---|---|---|---|
| MINOR-1 | MINOR | D8g | ch6_conclusion.tex:138-141 | "The controller accepts only a formation (Section~\ref{sec:swarm-controller}), while the script also commands a take-off, a movement, a hold, a landing and an abort, so each of these needs a mapping onto the controller; and the state machine's transitions at the take-off height and on ground contact, like the reset, need the vehicles' state reported back to it." | 58-word sentence with a semicolon combines two separate architectural requirements (controller input mapping vs state feedback reporting). | SKILL.md D8g (sentences over ~40 words should be split) | Split at semicolon: "The controller accepts only a formation (Section~\ref{sec:swarm-controller}), while the script also commands a take-off, a movement, a hold, a landing and an abort, so each of these needs a mapping onto the controller. In addition, the state machine's transitions at the take-off height and on ground contact, like the reset, require the vehicles' state reported back to it." |
| NIT-1 | NIT | D8d | ch6_conclusion.tex:162 | "under idealized kinematics rather than the flight envelope of physical aircraft." | American spelling `idealized`. | SKILL.md D8d (British spelling throughout: quantisation, behaviour, etc.) | Change `idealized` to `idealised`. |
| NIT-2 | NIT | D8d | ch6_conclusion.tex:196 | "velocities during formation maneuvers exceed the commanded flight envelope." | American spelling `maneuvers`. | SKILL.md D8d | Change `maneuvers` to `manoeuvres`. |
| NIT-3 | NIT | D8d | ch6_conclusion.tex:294 | "quadrotor airframes equipped with onboard attitude stabilization." | American spelling `stabilization`. | SKILL.md D8d | Change `stabilization` to `stabilisation`. |
| NIT-4 | NIT | D8d | ch6_conclusion.tex:301 | "deploying an optimized acoustic model or streaming encoder" | American spelling `optimized`. | SKILL.md D8d | Change `optimized` to `optimised`. |
