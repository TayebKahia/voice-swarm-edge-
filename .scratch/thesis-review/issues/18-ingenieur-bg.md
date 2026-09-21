# Issue 18: ingenieur-bg (Background, Chapter 2 since 26 Sep)

Status: resolved
Blocked by: 06 (resolved); runs beside 19 (State of the art), as 15 ran beside 16
Chapter: thesis/ingenieur/ch2_background.tex (344 lines, 7 keys, 10 citation sites; written 26 Sep, committed `b8ee6db`)
Script: tools/review/ingenieur_bg.py (new, `3e109c1`; model: master_bg.py)
Report: .scratch/thesis-review/reports/ingenieur_bg.md

Numbered 18 because it was drafted after 00-17 existed (spec.md: issues are never renumbered).
The Ingénieur was restructured on 26 Sep to the Master's two-part shape (prd.md §3.1): a new
Background chapter owns the foundations prd Table 3 gives this document (speech pipelines,
multirotors and flight control, swarm control, real-time systems and latency budgets, the
single-board computer as a shared host, state machines and command buses) and names the Master's
foundations in one sentence each. Two passages moved in from the old Ch2 (Reynolds' three rules;
keyword spotting as a distinct task). Seven visible \TODO markers name textbook sources absent from
references.bib; the closed-set rule reserves those additions for the author.

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/ingenieur_bg.py
```

## Agents

- **Citation agent** -- D5 only. Worklist: the report's citation sheet (10 sites, 7 keys:
  speechcmd, whisper, reynolds1987, koren1991, pyflyt, vaswani2017, lora, llamacpp, mcnemar1947)
  and the paper numbers (Whisper 680,000 hours; 39 M smallest). Also D5c: list every factual claim
  about a tool or the literature that carries no citation and would need one beyond the seven TODOs.
- **Argument agent** -- D1, D2, D4, D6, D8, D10, D11, D12, plus textbook correctness of every
  definition in the report's "Definitions to verify" sheet. Focus: (a) foundations only -- any
  sentence that states what this system chose, or what the literature measured; (b) consistency of
  vocabulary with Chapters 3-7 (operating point, end of speech, refractory interval, setpoint, clamp
  as hard, allowances as ceilings, affinity, sequence numbers); (c) write-once against the Master's
  Background (thesis/master/ch2_background.tex), especially sec:bg-master and sec:bg-sbc.
- **Verifier.**

## What the script establishes (baseline: 0 FAIL, 14 WARN, 48 PASS)

- Six foundation sections in prd §3.1 order, sec:bg-master, a Conclusion; labels in order.
- No latency figure, chosen component, design decision or code in the prose; the Master's
  foundations appear only in sec:bg-master; the moved passages are stated once.
- Arithmetic: 10 dB = x10 power; -dU/dd of eq:apf; critical damping at kd = 2 sqrt(kp).
- WARN: seven \TODO markers (known); three headings spell out an acronym (VAD, SNR, SBC); two
  negated "guarantee(s)"; three numbers untraced (16,000 samples/s, 680,000, 39 million).

## Comments
### 2026-09-26 -- review round 1 (citation + argument + verifier)

Agent reports: `agents/18-ingenieur-bg/{citation,reviewer,verifier}.md`.

Verdict (both agents): ready after fixes. Shape PASS (D1), write-once mostly PASS, register sober.
Citations (10 sites): 8 SUPPORTS, 2 PARTIAL (reynolds1987 "central force"; vaswani2017 does not
define a language model), 0 DOES NOT SUPPORT; Whisper figures verbatim in the PMLR paper; bib
metadata agrees (NIT: vaswani2017 booktitle NeurIPS vs NIPS; koren1991 volume unconfirmed).

Verified BLOCKER/MAJOR (verifier: 7 confirmed or partly, 1 MINOR raised):

| # | Sev | Line | Finding | Verifier |
|---|---|---|---|---|
| F1+C-2 | BLOCKER | 177-180 | "minimising the total squared distance ... avoids" crossing paths -- false (counterexample 113 < 127, paths cross at (0.5,0), reproduced with swarm.control.assign_slots); what it gives is a minimum-separation property under synchronised straight-line motion (CAPT); contradicts Ch1 l.338 "crossing paths by construction"; Ch5 (ch4_implementation l.355-357) implies the same claim; uncited | CONFIRMED; fix in all three chapters + CAPT \TODO |
| F2 | MAJOR | 99-101 | "a direct pipeline ... avoids the endpointing wait" -- only one that decides per frame | CONFIRMED |
| F3 | MAJOR->MINOR here | 69-71 | "end of speech" = endpointer declaration is the meaning of record (Ch1, Ch4, Ch5, Ch7); drop "natural". Cross-chapter MAJOR: Ch6 (ch5_validation l.85-86, l.94-95) uses it for the keyword's acoustic end | PARTLY |
| F4 | MAJOR | 79-82 | WER definition near-verbatim the Master's l.404-406; the Master owns metrics (Table 3) -> one sentence in sec:bg-master | CONFIRMED |
| F5 | MAJOR | 227-233 | p50/p95 explanation repeats the Master's l.282-285; ownership reversed from the reviewer's proposal: prd 3.1 item 2 and Table 3 give percentiles/latency to the Ingénieur, so the Ingénieur keeps a reworded exposition without "the definition the Master gives" | PARTLY |
| C-1 | MAJOR | 124-131 | flight-controller loop rates and setpoint interfaces uncited -> cite pyflyt for the simulator half, \TODO naming the PX4 guide | CONFIRMED |
| C-3 | MINOR->MAJOR | 167-171 | Reynolds' "central force model" is a pull on the centroid only, called "more simplistic", not "simpler to compute"; no velocity matching | CONFIRMED, raised |

MINOR/NIT: 23 wordings tested together by the verifier (verifier.md §3.8), script 0 FAIL, build
rc=0. Two proposals rejected as anchor-breaking or against the script's intent (F29 drop of the
Whisper figures -> use C-5; F28's \ref to the Implementation chapter -> "from Chapter 4 onwards").
Script defects noted: the \ref foundations pattern is vacuous (prose() strips \ref); the
memory-bound pattern does not span lines. F5's Master-side cross-reference is a Master edit, out of
scope under the restructure's rule (thesis/master/ only for a hardcoded Ingénieur chapter number).

Examiner questions: (1) what squared-distance assignment guarantees -- answered after F1;
(2) what removes the endpointing wait -- answered after F2; (3) why processor affinity alone rather
than a real-time scheduling policy or core isolation -- not answered in any chapter.

Awaiting the author's decisions.

### 2026-09-26 -- fixes applied (author's decision: verified findings plus all tested MINORs, and the cross-chapter fixes)

Committed `6d40ad4`. Applied with the verifier's §3 wording: F1+C-2 in Ch2, Ch1 l.338 and Ch5
(ch4_implementation l.355-359, anchor kept); F2; F3 in Ch2 (MINOR) and Ch6 (ch5_validation l.85-95);
F4 (WER to sec:bg-master); F5 (ownership kept, "the definition the Master gives" dropped; the Master
cross-reference NOT applied -- Master edits are out of scope for the restructure); C-1 (pyflyt +
PX4 \TODO); C-3 (Reynolds' central force; Ch5 l.374 follows). All 23 MINOR wordings of verifier
§3.8, a dangling "Its parser" -> "The parser", Koren/Khatib TODO year widened, prose reflowed.
Script after: 0 FAIL, 16 WARN (9 \TODO, 3 acronym long forms in headings -- correct as written,
2 negated "guarantee", 2 untraced textbook numbers). Clean build 0/0/0/0, 91 pages.
Open for the author: nine \TODO sources to add and verify (multirotor dynamics, PX4 guide, feedback
control, CAPT, Khatib, real-time text, sched(7)/sched_setaffinity(2), Harel, publish/subscribe
survey); examiner question 3 (affinity vs real-time scheduling policy) unanswered anywhere.

Status: resolved.
