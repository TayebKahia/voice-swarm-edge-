# Issue 19 -- argument agent report (D1, D2, D4, D6, D8, D10, D11, D12)

Chapter: `thesis/ingenieur/ch3_state_of_the_art.tex` (511 lines): the working tree, i.e. `c3fe8d5` plus six uncommitted one-line style edits (show->exhibits, two G-heading shortenings, "components described below"). All line numbers refer to the working tree.
Script: `tools/review/ingenieur_ch2.py` re-run for this review: 0 FAIL, 3 WARN, 70 PASS (same as the
issue baseline). Read against: `docs/agents/thesis-chapter-review.md` (Template A), issue 19, the
script report, SKILL.md, prd.md §2/§3.1/Table 3, the Master's `ch3_state_of_the_art.tex` and issue 16,
the pre-rebuild chapter (`git show c3fe8d5~1:...`) and issue 07, and the neighbours Ch1
(`ch1_introduction.tex`), Ch2 (`ch2_background.tex`), Ch4 (`ch3_architecture.tex`), Ch5
(`ch4_implementation.tex`), Ch6 (`ch5_validation.tex`), Ch7 (`ch6_conclusion.tex`),
`thesis/generated/requirements_summary.tex`.

## 1. Verdict

Ready after fixes. The rebuild has the frozen shape (four taxonomy sections, one table each ending
in a This-work row, a Critical comparison under each, Research gaps with Synthesis, concessions,
G1-G3 and the Lim et al. positioning), the write-once boundary with the Master holds, and every
issue-07 overclaim I checked stayed fixed. What stops it passing: two This-work rows state more
than Chapters 5-6 deliver (the swarm row's "physics simulator ... at 50 Hz", when Ch5 gives 24 Hz and
tests only; the speech row's "Offline: Yes", when Ch6 marks offline recognition "Not yet run").
Three silence claims that G2 and G3 rest on are stronger than the table as drawn. The
"one to two orders of magnitude" synthesis drops the hardware qualifier that §3.4's own reading
requires. The §3.3 critical comparison restates a concession and G2, which is issue 16's M1
pattern. One factual slip ("CommandSwarm, the most recent system that accepts speech") is refuted
by two later rows of the same table.

## 2. Scorecard

| Dim | Result | Note |
|---|---|---|
| D1 Structure | PASS (1 MINOR) | Sections match prd.md §3.1 item 3 exactly; opens with a scope statement, closes with a hand-off to Ch4/Ch6. The closing conjunction paragraph sits under the "Comparison by design" lead-in (m13). |
| D2 Argument coherence | ISSUES (13) | Taxonomy/row mismatches, axis counts, positioning leak in §3.3, G1 first sentence, G3 closure, dash-to-negative conversions. |
| D3 Numbers | not in scope | Citation agent and verifier. Derived values recomputed in §4 below all hold. |
| D4 Claims and hedging | ISSUES (8) | Two This-work overclaims, the orders-of-magnitude synthesis, stop-path claim vs Lim et al., SBC claim over dash rows, "most recent", "every axis", "measure why". |
| D5 References | not in scope | Citation agent. Leads in §6. |
| D6 Write-once | PASS (1 NIT) | Master-owned literature named in one sentence (l.28-30); Mémoire named exactly; no Master citation keys re-surveyed. One sentence identical to the Master's Synthesis (n4). |
| D7 Figures and tables | not in scope | (Noted in passing: Chat with UAV row never read, n9.) |
| D8 Language and style | ISSUES (7) | Nine sentences over 40 words; IoT hand-typed; "significant" unattributed; weak verbs; unit spacing. British spelling PASS; ASCII PASS; `\gls` PASS apart from the heading WARN (the other UAV/LLM WARN hits are proper names: "Chat with UAV", "DeepSeek-LLM"). |
| D9 LaTeX | not in scope | Script: check_tex clean, refs resolve. |
| D10 Examiner view | ISSUES (1) | Review method (search, inclusion criteria) not stated; three hardest questions in §7. |
| D11 Self-containment | PASS | No project-internal words in the body (prd only in the leading comment). Codes: G1-G3 defined at their paragraph; C4 never coded ("the first/second clause of the contribution"); p95 defined in Ch1 l.32/l.170; p90 appears only in a table cell after "90th-percentile" at l.180. |
| D12 Headings and register | ISSUES (3) | Section title "Voice-controlled UAV systems" inaccurate for half the table; typed UAV in it (script WARN); two aphoristic sentences. Sentence case consistent; all paragraph lead-ins at most five words. |

## 3. Findings

Severity per Template A. "Table" rows = table cells read as drawn.

### BLOCKER

| # | Sev | Dim | file:line | Quoted text | Problem | Evidence | Proposed fix |
|---|---|---|---|---|---|---|---|
| B1 | BLOCKER (low impact, one-clause fix) | D4b | ch3_state_of_the_art.tex:365-366 | "CommandSwarm, the most recent system that accepts speech, does not claim it." | Refuted by two rows of the same table. MIRA (arXiv 2609.24547, Sep 2026) and Henry et al. (arXiv 2606.24910, Jun 2026) both accept speech and are later than CommandSwarm (arXiv 2605.07764, May 2026). The commit message of `c3fe8d5` says a similar recency claim ("the swarm systems are the most recent") was narrowed before commit; this one survived. | `thesis/references.bib` eprints: commandswarm2026 2605.07764; henry2026 2606.24910; mira 2609.24547. tab:soa-speech rows l.353, l.356. | "CommandSwarm, a recent system whose front end is a large multilingual model, does not claim it." (or delete the appositive) |

### MAJOR

| # | Sev | Dim | file:line | Quoted text | Problem | Evidence | Proposed fix |
|---|---|---|---|---|---|---|---|
| M1 | MAJOR | D4b, D2e | ch3_state_of_the_art.tex:285 | "Kinematic and physics simulators; five vehicles at 50~Hz" (and Separation cell "Potential field; geometric clamp at the integrator") | The Evaluation column is "how the control layer was exercised". The cell says both backends exercised the controller at 50 Hz. Ch5: the physics backend's effective control rate is 24 Hz, and it runs five unit/smoke tests from one placement, with no experiment. Every result comes from the kinematic backend. The clamp exists only on the kinematic backend (PyFlyt exposes no integrator). This is the issue 16 M2 pattern: a This-work row promising what later chapters do not deliver. | ch4_implementation.tex:435-441 ("effective control rate is 24~Hz rather than the nominal 48~Hz or 50~Hz"); :446-464 ("The formation-control results come from the kinematic backend alone"; "Its runs apply no separation clamp"); ch5_validation.tex:360-363, 400-403; ch6_conclusion.tex:161-175. Ch1 l.78 itself says "a nominal 50~Hz". | Evaluation: "Kinematic simulator: 150 trials of five vehicles at 50~Hz; physics simulator in tests only, at an effective 24~Hz". Separation: "Potential field; geometric clamp at the integrator (kinematic backend)". |
| M2 | MAJOR | D4b | ch3_state_of_the_art.tex:358 (also :506-507) | "... & Yes & ..." (Offline column, This-work row); "and offline execution on an \gls{sbc}" | The Offline column is "whether recognition runs without a network connection, as the source states it". For this work Ch6 states the opposite status: offline speech recognition and offline operation are "Not yet run" (no run with networking disabled). "Yes" is a design property, not something this document has shown. The closing conjunction repeats it as a property of the system. | generated/requirements_summary.tex rows "Offline speech recognition ... No run with networking disabled ... Not yet run" and "Offline operation ... Not yet run"; ch5_validation.tex:411-413; ch6_conclusion.tex:57, 266, 353. | Cell: "By design; not yet verified with networking disabled (Chapter~\ref{chap:validation})". l.506-507: "and execution on an \gls{sbc} with no network dependency by design". |
| M3 | MAJOR | D2f, D4b | ch3_state_of_the_art.tex:144; :434-435 | "No system in the table runs its full chain on an \gls{sbc} without a \gls{gpu}." / "No system in Table~\ref{tab:voice-uav-survey} executes its full chain on an \gls{sbc} without a \gls{gpu}" | G3 rests on this silence claim, and the table does not establish it. (i) Three rows have a dash for the host (SwarmChat, Iannoli et al., CommandSwarm), and l.138-139 itself says SwarmChat and CommandSwarm do not state their hardware. The review therefore cannot say where those chains run, only that no row records an SBC. (ii) Read literally, "in the table" includes the This-work row, which does run on an SBC. The Master's convention, and this chapter's own l.296/l.373, is "no prior row". | tab:voice-uav-survey l.126, 127, 129 host cells end in "---"; l.138-139. | l.144: "No prior row records a full chain run on an \gls{sbc} without a \gls{gpu}, and three rows state no host at all." l.434-435: "No prior row of Table~\ref{tab:voice-uav-survey} reports executing its speech and language chain on an \gls{sbc} without a \gls{gpu}, and ..." (see also m9 on "full chain"). |
| M4 | MAJOR | D2f, D4b | ch3_state_of_the_art.tex:151-152; :421-423 | "None of the systems in the table reports a stopping command handled separately from the path that interprets commands." | The chapter contradicts this itself. Lim et al. is a row of the same table, and their stop is exactly a mechanism outside the interpreting path: a human operator switches the vehicle to position mode (l.459; tab:lim-positioning l.481 "Stop: Human operator switches to position mode"). A jury member who reads l.459 will raise it. What the gap needs is a *spoken or typed* stop on its own path. | l.458-459; l.481. | l.151-152 and l.421-423: "None of the prior rows reports a spoken or typed stopping command handled separately from the path that interprets commands; the one stop outside that path, in Lim et al., is a human operator's switch to position mode." |
| M5 | MAJOR | D4b | ch3_state_of_the_art.tex:231-233; :384-386 | "removing transcription cuts the latency of a command by one to two orders of magnitude, 21~ms against 1{,}233~ms and 7~ms against 202~ms"; Synthesis: "Transcription-free paths have been measured to cut the latency of a spoken command by one to two orders of magnitude at no cost in accuracy" | This generalises beyond the hardware reported. Henry et al.'s 7 ms is on a GPU; on a CPU the same recogniser takes 106 ms, under twice the cascade's 202 ms (202/106 = 1.9). The chapter's own §3.4 reading (l.370-373) says "a speech latency is a property of the component and of its host together, and most rows state one without the other". The Synthesis then states the effect with no host at all, although this system's fast path runs on a CPU. | l.171-172, l.211, l.353 (7 ms GPU, 106 ms CPU); l.370-373. Arithmetic: 1233/21 = 58.7 (1.8 orders); 202/7 = 28.9 (1.5 orders); 202/106 = 1.9. The hardware of Henry's 202 ms cascade is not stated in the chapter (UNVERIFIED U1). | l.231-233: "... by one to two orders of magnitude on the hardware each reports, 21~ms against 1{,}233~ms, and 7~ms on a \gls{gpu} against 202~ms; Henry et al.'s direct recogniser takes 106~ms on a \gls{cpu}." Synthesis: "Transcription-free paths have been measured to cut the latency of a spoken command by one to two orders of magnitude on the hardware the studies report, with no loss of accuracy on their tasks~\cite{simoes2024,henry2026}." |
| M6 | MAJOR | D2 (chapter promise l.27-28), prd §3.1 | ch3_state_of_the_art.tex:299-305 (secondary: 234-235) | "The layering of a language-model planner above a separate safety layer is therefore published." / "SkySim's planning latency ... exhibits what the separation of layers leaves unsolved: a layered design that routes every command through the planner stops only as fast as the planner answers." | Positioning inside a theme section. The first sentence is a concession (it only has a point relative to this work, and l.398-399 makes it again). It is also a non sequitur: "therefore" follows from SkySim's falling outside Strobel's categories, which does not imply it. The second is the motivation of G2, restated almost word for word at l.423-424. Issue 16 M1 counted "G2 restated" inside a critical comparison as MAJOR and ruled that only a one-sentence neutral reading of the last row is allowed. Secondary: l.234-235 "That result bears on a fast path that must choose among several commands" reads the studies against this work's need (G1). | Issue 16 Comments, M1 and its ruling; this chapter l.27-28 "to this work only in that final section"; l.398-399; l.423-424. | Delete l.299-300. Replace l.302-305 with a reading of SkySim alone: "SkySim's mean planning latency, 34~s for 3 drones and 50~s for 10, is judged unsuitable for time-critical missions by its own authors." l.234-235: "Both studies report the result for alternatives, not for two paths running at once." |

### MINOR

| # | Sev | Dim | file:line | Quoted text | Problem | Evidence | Proposed fix |
|---|---|---|---|---|---|---|---|
| m1 | MINOR | D2e, D12, scoping | :36-38, :83-89, :107, :19-24 | "The published systems are of four kinds: ..." | (i) The taxonomy names four kinds, but the section has five paragraphs. "Where the model runs" (Sikorski, Torkamani) belongs to none of the four (the issue 16 MINOR-1 pattern). (ii) Torkamani and Zarin target IoT devices (smart lights, appliances; candidate note l.137), yet sit in a table captioned "Published language interfaces to robots". (iii) "The published systems" classifies the world, not the review. (iv) SayCan, Code as Policies and Phadke et al. are reviewed in the prose but have no row, so the table's "every system with a language model" readings do not cover them. The same scoping applies to the intro's "the kinds that exist" (l.22). | Paragraph heads l.44, 53, 65, 83, 91; tab rows l.118-129. | l.36-38: "The systems reviewed here are of four kinds ..., and two further studies make the host of the model their subject." Caption: "Published language interfaces to robots and devices". l.22: "sorts its studies into kinds". Either add rows for SayCan/Code as Policies or say in the caption: "systems whose check this review could establish; the general robot-control frameworks of the prose are not rows". |
| m2 | MINOR | D2e | :290 | "Table~\ref{tab:soa-swarm} separates the works on three axes." | Four axes are read: coordination, separation, place of the language model, evaluation (l.290-302). | l.290-302. | "... on four axes." |
| m3 | MINOR | D2e | :309-311 | "The speech front ends ... are of four kinds: recognisers run by a platform or in the cloud, recognisers run offline in a cascade, direct recognisers ..., and gates ..." | CommandSwarm's SeamlessM4T front end (row l.355: "Not claimed" offline, hardware unstated) fits none of the four kinds. | l.320-322, l.355. | Add "and front ends whose host the source does not state". |
| m4 | MINOR | D2f, D8g | :140-144 | "the language model is remote in every system that names a provider, local to a workstation \gls{gpu} in Lim et al., on a control computer in the offline arm of Sikorski et al., ..." | "Every system that names a provider" does not hold: Silva and Burke are "Mostly cloud models" (l.122), and Sikorski names GPT-4-Turbo *and* a local LLaMA. At 58 words, the longest sentence in the chapter. | l.122, l.124. | "On the host, every hosted commercial model in the table is reached remotely. The open models run on a workstation \gls{gpu} in Lim et al.\ and on a control computer in the offline arm of Sikorski et al., and on an edge accelerator in Torkamani and Zarin, which hands work to the cloud when its runtime metrics call for it." |
| m5 | MINOR | D2f (dash semantics) | :146; :293-294; :374-375 | "Every system with a language model constrains or checks its output in some way." / "SkySim is the one language-interface system that states its mechanism." / "none states a latency budget for its speech stage" | Each turns a dash ("this review did not establish") into a positive or negative fact. Sikorski's and Torkamani's check cells (l.124-125) are dashes. The separation cells of Iannoli and CommandSwarm (l.282-283) are dashes. Most latency cells in l.350-356 are dashes. Issue 07 accepted the l.146 wording, so it is not an overclaim creeping back, but it asserts beyond the cells. | Captions l.111-112, 203-204, 271-272, 343. | l.146: "Every system with a language model whose check this review established constrains or checks its output." l.293: "SkySim is the one language-interface row whose separation mechanism is recorded." l.374-375: "... and no prior row records a latency budget for its speech stage." |
| m6 | MINOR | D4b | :149-151 | "The checks that are deterministic and automated appear in the systems of 2026, and Iannoli et al.\ measure why" | (i) "Measure why" is causal. Iannoli et al. measure what guardrails add, not why checks appeared in 2026. (ii) Read as "only in 2026", it is contradicted by SwarmChat (2025), whose check cell is "Rule-based intent keywords". (iii) Whether Iannoli's guardrails are deterministic is not established (U3). | l.126, l.127. | "Deterministic, automated checks appear in the systems of 2026 (Silva and Burke, SkySim, CommandSwarm), and Iannoli et al.\ measure what such support adds: without planning tools and guardrails, general-purpose models do not execute swarm tasks reliably." |
| m7 | MINOR | D2f | :409-411 | "The fast paths of Table~\ref{tab:soa-dual-path} either have one action, as MIRA's abort does, or serve responsiveness or computation rather than safety." | False as drawn for Simoes et al. and Henry et al.: their fast paths decide a full command or intent (not one action), and their Purpose cells are dashes (l.210-211). The next sentence covers them, so the first sentence needs scoping. | l.210-211. | "Of the fast paths in Table~\ref{tab:soa-dual-path} that run beside a slower one, MIRA's has one action, the abort, and the others serve responsiveness or computation rather than safety." |
| m8 | MINOR | D4 (f: concessions) | :427-430; :505-509; :393-402 | "a reflex path with a latency budget of its own ..., which preempts language-model inference"; "the third is claimed against the fast paths of Table~\ref{tab:soa-dual-path}" | Preemption of the slower path is conceded to MIRA at l.401. Yet both the G2 closure and the claimed third conjunct list preemption among what is claimed, without saying which part is new. Issue 07's closing record: "the contribution is the membership rule for a path that CHOOSES between commands; preemption and an uninterpreted stop are conceded to MIRA". Also, the issue-07 version recorded that CommandSwarm lists emergency stop mechanisms only among the safeguards a real deployment should require. That fact is gone, and it is the natural answer to "does CommandSwarm have a stop path?" under G2. | git show c3fe8d5~1 l.374-376, l.409-411, l.413-423; issue 07 last comment. | G2 closure: "... The first clause of the contribution closes this gap. Its preemption is MIRA's; what it adds is a latency budget of its own, 150~ms at p95 from the keyword offset, that must be met while the model decodes." l.507-509: "the third is claimed, for its membership rule and its budget, against the fast paths of Table~\ref{tab:soa-dual-path}, its preemption being conceded to MIRA". Restore in G2: "CommandSwarm lists emergency stop mechanisms only among the safeguards a real deployment should require~\cite{commandswarm2026}." |
| m9 | MINOR | D2f | :434-446 | "an architecture decision closes this gap: the allocation of the four cores" | G3 states two absences: no chain on an SBC, and no per-stage speech latency on the deployment processor. The core allocation addresses the first. The second is closed by the per-stage measurement of Ch6, which G3 does not name. "Full chain" is also inexact for this work: the state machine, controller and simulator run on the workstation (Ch4 "Placement", ch3_architecture.tex:122-133). The pre-rebuild text said "the whole perception and language chain". | ch3_architecture.tex:122-133; ch5_validation.tex:147-157 (per-stage attribution met). | "... closes this gap: the allocation of the four cores of Section~\ref{sec:resource-allocation}, under which Section~\ref{sec:latency-experiment} reports each stage's latency on the board." Use "speech and language chain" at l.144, l.435, l.442. |
| m10 | MINOR | D4b | :500-502; :466-467 | "this system moves every axis of Table~\ref{tab:lim-positioning} towards the deployment"; caption "Every row differs, and each difference changes either the latency or the accuracy a system can reach" | "Every axis" includes Perception ("None") and Reported, which are not moves towards a deployment. The pre-rebuild text listed the five axes that are. The caption's "each difference changes latency or accuracy" is untrue of the Reported row, which is not a design property. | tab:lim-positioning l.480, l.482; git show c3fe8d5~1 l.228-231. | "... this system moves the design axes of Table~\ref{tab:lim-positioning} towards the deployment of Section~\ref{sec:operational-context}: spoken input, an \gls{sbc} without a \gls{gpu}, five vehicles, output checked before it is published, and a stop that does not wait for a human." Caption: "Every design row differs, and each such difference changes ...". |
| m11 | MINOR | D4b (scoping) | :448-449 | "because it is the published system nearest to this one in the part of the design the \emph{M\'emoire de Master} fixes" | A superlative about the whole literature. | Issue 16 M4 precedent (scope to what was found). | "... because, among the systems reviewed, it is the one nearest to this one in the part of the design ..." |
| m12 | MINOR | D4, D2 | :217 | "150~ms; 2{,}500~ms, p95 targets" (column "Latency reported") | This is labelled as targets, so it is not an overclaim. But it puts design targets in a column of reported measurements, beside RelayS2S's 81 ms and Henry's 7 ms, and the anchors differ (this work: from keyword offset / end of speech; the sources: processing time per utterance or first chunk). The measured values miss the targets (545/547 ms; 3,122 ms). A reader who compares down the column is misled in both directions. | ch5_validation.tex:95-120, 137-150; ch3_architecture.tex:432-446 (anchors). | Cell: "Budgets 150~ms (from keyword offset); 2{,}500~ms (from end of speech), p95; measured in Chapter~\ref{chap:validation}". Caption: add "The last row gives design budgets, not measurements, and its anchors differ from the sources'." |
| m13 | MINOR | D1, D2 | :504-511 | "The gap this document fills is therefore narrower than any one of its parts suggests." | The closing paragraph sums up the whole section but sits under the "Comparison by design" lead-in, after the baseline. It frames the gap as four conjuncts (two conceded) without mapping them to G1-G3, so the section carries two gap frameworks side by side. | l.409-446 vs l.504-510. | Give it its own lead-in `\paragraph{Summary.}` and map it: "... the third is claimed as Gaps G1 and G2 ...; the fourth, Gap G3, is the setting ...". Rephrase the opening: "The gap this document fills is therefore a conjunction, narrower than any of its parts." |
| m14 | MINOR | D2a, D2 | :327-334 | "\paragraph{Open components.} Whisper is trained on 680{,}000 hours ... openWakeWord supplies a frozen feature front end ..." | The paragraph describes the components this work deploys. None is a reviewed system or a row of tab:soa-speech (only the This-work row names them), so it compares nothing. Two of its sentences are word-for-word in Ch4 sec:component-choices (openWakeWord: ch3_architecture.tex:543-545; Silero: :555-557), and the 39 M Whisper fact is repeated at :566. | ch3_architecture.tex:529-590. | Keep the Whisper/whisper.cpp facts here (Henry's cascade uses Whisper, which anchors them), and cut the Ch4 repeats to a back-reference. Or move the whole paragraph to Ch4 and leave one sentence: "The open components from which an offline front end of these kinds can be assembled are described with the choices of Section~\ref{sec:component-choices}." (Keep the script's paper-number anchors wherever the sentences land.) |
| m15 | MINOR | D10a | :19-30, :311-313 | (absent) | The review never says how its studies were found (sources searched, period, inclusion criteria). Every silence claim ("no prior row", "among the systems reviewed, none combines") is only as strong as that coverage. | Template D10a; examiner Q2 below. | Add one sentence to the introduction, with facts only the author can supply: `\TODO{author: where and when the search was run, and what admitted a study (e.g. a language or speech interface to a robot, vehicle or device, with a stated check or host)}`. |
| m16 | MINOR | D12a | :32 | "\section{Voice-controlled UAV systems}" | Half the table is typed-text input (Vemprala, TypeFly, Lim, Iannoli, SkySim), and prd.md §3.1 names the theme "voice- and language-controlled UAV systems". The typed "UAV" is the script's acronym WARN. | tab rows l.120-128; prd.md §3.1 item 3. | "Language interfaces to UAVs" or "Voice and language control of UAVs", with `\texorpdfstring{\glspl{uav}}{UAVs}`. Update the script's topic map (`ingenieur_ch2.py` outline check) in the same change. |

### NIT

| # | Sev | Dim | file:line | Quoted text | Problem | Proposed fix |
|---|---|---|---|---|---|---|
| n1 | NIT | D8g | :19-22 (44 w), :77-81 (44), :140-144 (58, see m4), :240-242 (43), :302-305 (42, see M6), :309-311 (43), :398-400 (43), :505-507 (42) | -- | Sentences over 40 words (list sentences mostly). | Split at the colon or the second clause; e.g. l.398-400: "SkySim covers ... at the control rate~\cite{skysim2026}. Its fallback to holding position when a waypoint is rejected is close to the rule ... that a rejection becomes a hold." |
| n2 | NIT | D8a | :86, :437-438 | "the offline model exhibits significant limitations in consistency and reliability" | "Significant" is the source's own word, but it reads as the author's (no test). | "which its authors describe as significant limitations in consistency and reliability". |
| n3 | NIT | D12c | :504; :302-305 | "narrower than any one of its parts suggests"; "stops only as fast as the planner answers" | Aphoristic. | See m13 and M6. |
| n4 | NIT | D6 | :381-382 | "Each of the four literatures reviewed in this chapter answers its own question." | Identical to the Master's Synthesis opening (master/ch3_state_of_the_art.tex:303-304). prd §3.2 forbids shared paragraphs, not sentences, but a jury reading both documents will notice. | "The four bodies of work reviewed above each settle part of the problem." |
| n5 | NIT | D8, SKILL §4.3 | :131, :129 | "Fine-tuned 0.5B model"; "6.7--14B" | Unit spacing. | "0.5~B"; "6.7--14~B". |
| n6 | NIT | D8e | :87, :125 | "IoT devices" | Acronym typed by hand, not in shared/acronyms.tex. | "Internet-of-Things devices" at l.87, or add `\newacronym{iot}` (used twice). |
| n7 | NIT | D8b | :152, :422 ("handled"); :450, :454 ("fixes") | -- | SKILL avoid-list verbs. | "a stopping command carried on a path separate from ..."; "the part of the design the Mémoire de Master determines"; "a prompt that prescribes the format". |
| n8 | NIT | D1 (neighbour) | ch1_introduction.tex:464-466 | "It states three research gaps, concedes the published systems ..., and positions it against its baseline" | The chapter's order is concessions, then gaps, then baseline. | Ch1: "It concedes the published systems that cover parts of this work, states three research gaps, and positions it ...". |
| n9 | NIT | D2, D7a | :215, :222-236 | Chat with UAV row | The critical comparison never reads this row, whose cells are all dashes except the arrangement. | Add: "Chat with UAV, split by function, has no fast path to compare." |
| n10 | NIT | D2e | :156 | "Several systems split the handling of speech between a fast path and a slower" | Chat with UAV takes text; Sahai's "path" is a branch. | "Several systems split the handling of an input between a fast path and a slower, more capable one ...". |
| n11 | NIT | D2e | :217 | "Concurrent; preemption by sequence number" | In Ch4 the sequence-number ordering rule is the correctness mechanism, and preemption is the cancellation (an optimisation). | "Concurrent; decode cancelled, stale results discarded by sequence number". |
| n12 | NIT (outside this chapter) | scoping | ch3_architecture.tex:532-533 | "No published comparison selects among open components ... (Section~\ref{sec:speech-components})" | Cites this chapter but drops its scoping ("No comparative study was found", l.311). | "No comparative study was found that selects ...". |

## 4. Number trace (D3 is the verifier's; derived values I relied on, recomputed)

| Value as written | file:line | Source path:row | Source value | OK? |
|---|---|---|---|---|
| "one to two orders of magnitude", 21 vs 1,233 ms | :231-232 | l.166-167 (0.021 s, 1.233 s) | 1233/21 = 58.7 (10^1.77) | OK on the stated hardware (see M5) |
| 7 vs 202 ms | :232 | l.168-169 | 202/7 = 28.9 (10^1.46) | OK (GPU, see M5) |
| 14 points | :169, :233 | l.168-169 | 93 - 79 = 14 | OK |
| "nearly three orders of magnitude", 7 ms to about 4 s | :369-370 | l.353, l.355 | 4000/7 = 571 (10^2.76) | OK |
| "about fifteen" GPU to CPU | :372 | l.171-172 | 106/7 = 15.1 | OK |
| four systems address a swarm | :139 | tab rows l.126-129 | SwarmChat, Iannoli, SkySim, CommandSwarm | OK |
| speech with a group: two systems | :137-138 | tab rows | SwarmChat, CommandSwarm (This-work row aside) | OK |
| 150 ms; 2,500 ms, p95 | :217, :428 | ch3_architecture.tex tab:stage-budget | 150 ms offset; 2,500 ms end to end | OK as targets (see m12) |
| 50 Hz (This-work swarm row) | :285 | ch4_implementation.tex:332 (nominal 50 Hz), :438 (24 Hz effective, physics) | nominal 50 Hz, kinematic; 24 Hz physics | NOT OK (M1) |
| exactly two classes, five vehicles | :418-419 | ch3_architecture.tex tab:membership | hover, abort | OK |
| RTX 3080 Ti; 0.2; 38%; 40% | :452-458 | lim2025 (citation agent) | -- | citation agent |

## 5. Citation table (D5b)

Not in this agent's scope; see the citation agent's report. Leads for it are in §6.

## 6. UNVERIFIED

- U1 (bears on M5): the hardware of Henry et al.'s 202 ms cascade. If it was timed on the same GPU as
  the 7 ms figure, the GPU comparison is like for like and M5's fix stands as written. If on another
  host, "7 ms against 202 ms" compares hosts as well as shapes.
- U2 (bears on G3, M3): the hardware of Sikorski et al.'s "control computer" (candidate note l.126
  says only that the Pico W is the radio link). If it is a single-board computer without a GPU,
  running VOSK and LLaMA 2-7B offline, then the "no prior row on an SBC without a GPU" silence claim
  fails for that row.
- U3 (bears on m6 and Synthesis l.383-384): whether Iannoli et al.'s runtime guardrails are
  deterministic. The Synthesis cites iannoli2026 for "deterministic, automated checks".
- U4 (bears on G2, M4): whether Silva and Burke's MAVLink interface has an emergency stop, land or
  return command outside the language-model path. If it does, G2's silence claim needs that row
  excepted too.
- U5 (bears on G2 l.426-427): whether MIRA reports a latency for its barge-in gate. The text's
  "this review established no latency for it" is correctly scoped either way, but if the paper
  gives one, G2's distinction narrows to the budget alone.
- U6: SwarmChat's hardware (l.138-139 "Neither states the hardware"). The table cell is a dash;
  the prose turns it into "does not state". Issue 07 verified this for CommandSwarm only.

## 7. Examiner questions (D10b)

1. "Gap G2 is a stop with a budget of its own, and your contribution is said to close it. Chapter 6
   reports 545 ms idle and 547 ms loaded against 150 ms. What exactly is closed?" -- Partly answered.
   G2 (l.430-432) correctly says the design specifies the budget and Section 6.1 measures it, and
   G3 (l.445-446) says the budget "is met, or missed". Nothing in this chapter says the gap is
   closed by reporting a budgeted, separately measured stop, whatever the verdict. Ch6
   (ch5_validation.tex:95-100) locates the miss in the spotter's decision delay and the offset
   anchor, and the board's share rises only from 6 to 18 ms under load. That is the evidence G3's
   premise needs. Recommendation: one clause in G2, "whether it is met, and where a miss lies, is
   reported there".
2. "How did you select these studies, and on what grounds can you say that no reviewed system
   combines the four properties, or that no prior row runs on an SBC?" -- Not answered (m15). The
   silence claims are correctly scoped to "the systems reviewed", but the review's coverage is never
   stated, and three host cells are dashes (M3).
3. "The transcription-free paths in Table 3.2 report 7-21 ms, yet your keyword spotter is budgeted at
   150 ms and measured at 545 ms. Is your fast path slower than the literature's, or are the figures
   not comparable?" -- Not answered in this chapter. The table puts the targets beside measured
   figures in a column headed "Latency reported" (m12), and nowhere says that this work's span runs
   from the keyword offset and includes the spotter's decision delay and 80 ms framing
   (ch3_architecture.tex:432-446), while the sources time processing per utterance, or the first
   chunk. §3.4's own reading ("a property of the component and of its host together", l.372-373)
   is half the answer. The anchor difference is the other half.

(Also likely, and answered: "Why is Lim et al. the baseline and not CommandSwarm?" l.448-452
answers it by the Master-fixed part of the design, i.e. open models of the same families hosted
locally. m11 only scopes the superlative. "What do you add to MIRA?" G1 l.409-419 answers it: a path
that chooses between two commands raises the membership question a one-action gate does not. This
carries issue 07's corrected contrast intact.)

## 8. Carry-over check against issue 07 (nothing conceded may be claimed; no fixed overclaim may return)

| Issue 07 item | Status in rebuilt chapter |
|---|---|
| MIRA contrast rewritten to "one action vs a choice between two commands" | Kept (G1 l.409-415). |
| MIRA offline unverifiable -> "names no models and no host" | Kept (l.187-189). |
| SkySim: natural-language (not typed) text; previous waypoints kept on malformed output; 34/50 s are N=3/N=10 means | Kept (l.256-259; table cell "Text", not "typed"). |
| CommandSwarm: targets its simulator but never executes trees | Kept (l.260-261, l.283, l.302). |
| "Every LLM system checks" -> "constrains or checks" | Kept (l.146); m5 notes it still asserts over dash cells. |
| No-stop-path claim limited to the table, pointing to MIRA | Table-limited (l.151-152, l.421-423); MIRA handled in G2. New contradiction with Lim's human switch (M4). |
| TypeFly cell "Plan language; no check stated"; caption admits generation constraints | Kept (l.121, l.109-111). |
| Henry attribution tied to the 14-point explicit-command gap | Kept (l.169-170). |
| Concessions to CommandSwarm, SkySim, MIRA by name | Kept (l.393-402); fixed-language systems and Silva and Burke also conceded (l.402-404), fairly. Preemption conceded to MIRA but listed among the claimed (m8). CommandSwarm's "emergency stop only among recommended safeguards" dropped (m8). |
| Fourth property framed as a setting, not a contribution | Kept (l.441-444, l.509-510). |
| "This document does not claim to outperform Lim et al." | Dropped, but l.498-500 "no such comparison is made" carries the substance. Acceptable. |
