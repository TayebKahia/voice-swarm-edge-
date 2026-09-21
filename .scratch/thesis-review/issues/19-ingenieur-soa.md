# Issue 19: ingenieur-soa (State of the art, Chapter 3 since 26 Sep)

Status: resolved
Blocked by: 07 (resolved); runs beside 18 (Background)
Chapter: thesis/ingenieur/ch3_state_of_the_art.tex (512 lines, 30 keys, 89 citation sites; rebuilt 26 Sep, committed `c3fe8d5`)
Script: tools/review/ingenieur_ch2.py (the file name keeps the chapter's old number; rewritten for the new shape in `3e109c1`)
Report: .scratch/thesis-review/reports/ingenieur_ch2.md

Issue 07 reviewed the old Chapter 2 (resolved 24 Sep). The chapter was rebuilt on 26 Sep in the
Master's form (issue 16 is the model): four themes -- voice-controlled UAV systems, fast-path and
dual-path architectures (new section), swarm control, offline speech components -- each a taxonomy
with one comparison table ending in a "This work" row and a "Critical comparison." paragraph; then
Research gaps (Synthesis, Conceded prior art, G1-G3, the baseline Lim et al. with
tab:lim-positioning, comparison by design). The component justification moved to Architecture
(sec:component-choices). No bibliography entry was added: every cell restates a fact the reviewed
prose already carried, and a dash marks the rest. Issue 07's citation verdicts still apply to the
sentences that survived; the citation agent re-checks the changed sentences and every table cell.

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/ingenieur_ch2.py
```

## Agents

- **Citation agent** -- D5 only. Worklist: the report's citation sheet (89 sites, 30 keys) and
  "Numbers quoted from papers" (32 anchors). Every cell of tab:voice-uav-survey, tab:soa-dual-path,
  tab:soa-swarm, tab:soa-speech and the Lim et al. column of tab:lim-positioning is a claim about its
  source: a wrong cell is a BLOCKER, a dash is never a finding. Reuse issue 07's verdicts where the
  sentence is unchanged, and say so.
- **Argument agent** -- D1, D2, D4, D6, D8, D10, D11, D12. Focus: (a) each critical comparison reads
  its table column by column and compares the studies to each other; comparison to this work only in
  Research gaps; (b) every silence claim scoped to the studies reviewed; (c) G1-G3 follow from the
  tables and are closed by what they name, without promising what Chapter 6 does not report (the
  reflex budget is missed under load); (d) nothing conceded in issue 07 is now claimed; (e) the
  "This work" rows agree with Chapters 4-6.
- **Verifier.**

## What the script establishes (baseline: 0 FAIL, 3 WARN, 70 PASS)

- Four theme sections, each with one table, a Critical comparison and a This-work row; Research gaps
  with Synthesis, Conceded prior art, G1-G3 and tab:lim-positioning; no source introduced in the
  gaps; each gap points at what closes it; no Master-owned literature; 32 paper-number anchors.
- WARN: 9 numbers untraced (paper numbers inside table rows); `UAV`/`LLM` typed in a heading and
  a model name.

## Comments
### 2026-09-26 -- review round 1 (citation + argument + verifier)

Agent reports: `agents/19-ingenieur-soa/{citation,reviewer,verifier}.md`.

Verdict (both agents): ready after fixes. D1 PASS (four themes, one table each with a This-work
row, a Critical comparison each; Research gaps complete), D6 PASS, D11 PASS; issue 07's fixed
overclaims all still fixed. Citations: ~139 table cells and 89 sites checked, most in full text;
all 32 paper numbers found at the stated value; bib metadata agrees.

Verified BLOCKER/MAJOR (verifier: 12 of 12 confirmed, two raised, one NEW):

| # | Sev | Line | Finding | Verifier |
|---|---|---|---|---|
| B1=B-5 | BLOCKER | 365-366 | "CommandSwarm, the most recent system that accepts speech" -- Henry (Jun 2026) and MIRA (Sep 2026) are later speech rows | CONFIRMED |
| B-1 | BLOCKER | 425-427 + MIRA latency cell | "this review established no latency" for MIRA's stop -- MIRA Table 3: 466 ms median, speech onset to abort, after a 450 ms confirmation threshold; no target stated | CONFIRMED; G2 narrowed |
| M4+B-2 | BLOCKER (raised) | 151-152, 421-423 | "none reports a stopping command handled separately" -- Silva and Burke's out-of-band radio kill; Lim's operator switch | CONFIRMED; scoped to spoken/typed stops, human stops named |
| B-3 | BLOCKER | 439-441 | Torkamani's edge tier "presumes the network" -- the paper: it "enables operation without internet connectivity"; the cloud-preferring routing presumes it | CONFIRMED |
| B-4 | BLOCKER | 283 | CommandSwarm cell: the classifier screens the command before generation; only the parser gates the tree | CONFIRMED |
| M1 | BLOCKER (raised) | 285 | swarm This-work row "physics simulator ... 50 Hz" with the clamp -- Ch5: physics backend 24 Hz effective, tests only, no clamp | CONFIRMED |
| M2 | MAJOR | 358 | speech This-work "Offline: Yes" -- Ch7 marks offline operation "Not yet run" -> "By design; not yet tested" | CONFIRMED |
| M3 | MAJOR | 144, 434-435 | "no system in the table runs its full chain on an SBC without a GPU" includes This-work and three dash hosts -> "no prior row" (Sikorski: desktop RTX A4000; Torkamani: Jetson GPU) | CONFIRMED |
| M5 | MAJOR | 231-233, 384-386 | "one to two orders of magnitude" without the hardware of each figure | CONFIRMED |
| M6 | MAJOR | 299-305 | concession + G2 restated in the swarm critical comparison (issue 16 M1 pattern) -> reading of the Evaluation column | CONFIRMED |
| M-1 | MAJOR | 364-365 + tab:soa-speech | Torkamani missing from the speech table; offline 8-bit tiny faster-whisper on a Jetson Xavier NX | CONFIRMED; row added |
| M-2 | MAJOR | 383-384, 149-151 | Iannoli's "runtime guardrails" are prompt fragments, not deterministic checks | CONFIRMED |
| NEW-1 | MAJOR | 374-375 | "none states a latency budget" -- Henry set 7 ms against a 100 ms teleoperation limit -> "none allocates a budget" | NEW |

G2 still follows once narrowed (no reviewed stop is a spoken command on its own path held to a
budget of its own; MIRA's reacts to any sustained speech with no target; the preemption is conceded
to MIRA) and promises only that Chapter 6 measures the reflex, not that it meets the budget. G3
holds scoped to prior rows and to the speech-and-language chain, naming Torkamani (nearest chain,
Jetson GPU) and Strobel et al.'s TinyLlama speed test on a Pi 5 (added to the swarm section too).

MINORs: 24 applied in the tested set (verifier §4). Flagged unsafe: n5 ("6.7--14~B" breaks an
anchor), m14 (moving "Open components" to Ch4 removes four anchors -- defer to issue 20), m16
(retitling "Voice-controlled UAV systems" needs the script's TOPICS map changed). m15 (a \TODO for
the search method behind the silence claims) is an author action. Tested set: script 0 FAIL,
3 WARN, 70 PASS; all anchors survive; build rc=0, no overfull.

Examiner questions: (1) G2 closed while the reflex misses its budget -- answered after the fix
(G2 promises measurement, Chapter 6 reports the miss); (2) how were the studies selected -- not
answered (m15); (3) are 7-21 ms fast-path figures comparable with the keyword-offset anchor --
partly (hardware and anchors now named).

Awaiting the author's decisions.

### 2026-09-26 -- fixes applied (author's decision: the verifier's tested set, all BLOCKER/MAJOR plus 24 safe MINORs; section 1 retitled)

Committed `84e04be` (chapter, Ch1 structure sentence, SKILL.md) and `8386de4` (script topic map,
selftest target). The tested set was installed as the verifier produced it, prose then reflowed;
one theme-section pointer reworded ("returns to it as the baseline") to clear a positioning WARN.
Section 1 is now "Language interfaces to robots" (label sec:voice-uav kept); prd 3.1 follows.
Not applied: n5 (anchor), m14 (four anchors; deferred to issue 20), m15 (search-method \TODO:
needs the author's facts). Script after: 0 FAIL, 3 WARN (10 untraced paper numbers in table rows;
UAV/LLM in a heading and a model name), 70 PASS; SELF-TEST PASSED; clean build 0/0/0/0, 91 pages.
Open for the author: examiner question 2 (how the studies were selected) -- one sentence on the
search method would scope every silence claim.

Status: resolved.
