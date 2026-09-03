# Issue 11: ingenieur-ch3

Status: resolved
Blocked by: 06
Chapter: thesis/ingenieur/ch3_architecture.tex (497 lines, 6 distinct cites; drafted in b954b36,
da5f625, 61eb810, 113723a, with cca879e and a46a8d0 from other sessions; STATE.md record b1b884b)
Script: tools/review/ingenieur_ch3.py
Report: .scratch/thesis-review/reports/ingenieur_ch3.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/ingenieur_ch3.py
```

## Agents

Split like issue 06 (the chapter is as long as Master Ch3, but has 6 citations, not 18):

- **Argument agent** -- D1, D2, D4, D6, D10. Focus:
  - **Ch1's promises to this chapter** (P6, P7, P8, P14-P18, P21, P25, P26, P28 in
    `.scratch/thesis-review/agents/06-ingenieur-ch1/argument.md`). Check each one is kept, and that
    §3.3 states P15 and P17 exactly as Ch1 now does: a rejection is a hold while taking off or
    flying and a logged no-op otherwise; the reflex path skips interpretation, not validation.
  - **This chapter's promises to Ch4 and Ch5**, each listed with the label it points to (the
    report's "For the argument agent" sheet).
  - **Design claims that rest on the code, not on prd.md.** Read the code for each: the envelope,
    the rejection rule, `land` from TAKING_OFF, the sequence number reserved when an utterance is
    accepted, every command validated. The script checks the tables; the prose claims are the
    agent's.
  - **No measured figure anywhere.** The script checks the numbers. The agent checks the verbs:
    nothing may be stated as achieved ("holds", "isolates", "is met").
- **Citation / presentation agent** -- D5 (6 keys: oww, silero, whisper, whispercpp, llamacpp,
  qwen25), D7, D8, D9, D11, D12. It also checks the TikZ figure (`fig:architecture`): it must be
  vector, its caption self-contained, and it must agree with §3.1 and §3.5 on placement.
- **Verifier.**

## What the script establishes (baseline: 0 FAIL, 7 WARN, 100 PASS)

- **Outline and labels.** The five sections are the five topics of prd.md §3.1 item 3.
  `chap:architecture` is present. No label clashes with another chapter or with the generated
  latency table (which owns `tab:latency-budget`; the design table is `tab:stage-budget`).
- **Write-once.** There is no grammar listing. Layer 1 hands the schema and grammar to the
  *Mémoire de Master* in one sentence. No Master-owned literature is cited. The selected
  configuration is named, not derived.
- **tab:membership** lists the schema's ten intents. Its reflex rows equal
  `runtime/branch_a.py` `KEYWORD_TO_INTENT`, and each Path cell follows from the two tests. The
  2,350 ms, 4.7 m, 2.35 s and envelope figures in §3.2 are recomputed from the Ch1 targets and
  `schema/schema.py`.
- **§3.3.** The grammar properties are checked against `schema/cmd.gbnf`. Every envelope value
  matches `ENVELOPE` / `POS_MAX_NORM`. `tab:legality` equals `swarm/fsm.py TABLE_9_LEGALITY` on
  all ten intents.
- **tab:stage-budget.** Each of the 10 rows matches the generated latency table by name and
  target. They also match Master `tab:latency-budget` and Ch1's reflex, end-to-end and
  preemption-recovery targets. The 2,600 ms and 1,350 ms sums are recomputed. The 450 ms /
  32 ms / 482 ms derivation matches `runtime/vad.py`, and 80 ms matches `runtime/stream.py`.
- **§3.5.** The three threads match `runtime/parser.py` and `runtime/pipeline.py`. The memory
  paragraph matches Master tab:requirements (2.5 GiB, full stack) and Master Ch4 (no full-stack
  measurement).
- **Promise.** No value from the measured columns of the generated latency table appears.
- **Selftest.** Two planted errors are caught: `held within 60~m` fails `claim`, and `takeoff`
  legal in FLYING fails `legality`.

## Seeded findings

- **D12, 7 heading WARNs.** "Layer 1/2/3: ..." and "Core 0." / "Cores 1--3." contain a number;
  "What the layers do not catch." and "What pinning cannot isolate." read as sentences. For
  `\paragraph` lead-ins, judge whether the number is a name (the layer and core numbers are
  identifiers) or a result. Only the latter is a finding.
- **D5c, one unsourced claim.** In §3.2, "the shared word *swarm* supplies an onset that is
  uncommon in ordinary speech". This is a design rationale with no source in references.bib.
  Either it needs a citation or it should be cut (flagged to the author when drafted).
- **Refinements to prd.md made on purpose; check each is defensible:**
  - `set_param` is fail-safe "for a value that reduces speed or spacing" (prd Table 5: "Yes").
  - `hover` is legal "while taking off or flying", not "airborne": Table 9 rejects it in LANDING.
  - The validator's widening of an empty identifier list to all drones is not described. The
    grammar cannot emit an identifier outside 0-4, so the branch cannot fire on the deployed
    route. The author has not yet decided whether to name it anyway.
  - The worst-case memory arithmetic (prd §4.6) is left out on purpose. It is not an upper
    bound: the Master measured 0.68 / 1.63 GiB for the language-model process alone, above what
    the arithmetic predicts.
- **Kept by the author (2026-09-24); not a finding unless the surrounding prose is wrong:**
  - The start-of-speech target of 5,500 ms is not derived (3,000 + 500 + 2,500 = 6,000).
  - The stage ceilings after T0 sum to 2,600 ms, above 2,500; this is stated deliberately.
- **A Ch5 obligation, recorded here so it is not lost.** Ch1 and §3.4 end both spans at the bus
  on the device. `eval/exp2.py:355` stops the parse-path clock when the state machine has applied
  the command (loopback on the Pi). Ch5 must say which end point it measured.

## Tooling note

`tools/review/selftest.py` crashes before reaching this script. The crash is in
`master_ch4.py:203` (`StopIteration`): it looks for a generated-table row starting
`SLM prefill`, which 4d8d701 renamed to `Language-model prefill`. The fix belongs to the Master
Ch4 script and is not made here. The two Ch3 mutations were run through `selftest.run()`
directly, and both were caught.

## Comments

### 2026-09-24 -- one addition before the review (author's decision)

Ch3 3.1 gains two sentences after "a preference for redundancy": the reflex/cortex analogy, and
where it stops (the reflex path skips transcription and parsing only; its commands pass the
validator and the state machine). Author's choice among three options; the term stays "parse
path". Script unchanged at 0 FAIL, 7 WARN, 100 PASS; the report regenerated with lines +5 after
l.43. The argument agent should read the two sentences against P17 (reflex path validated).

### 2026-09-24 -- review, verified findings (awaiting the author's decisions)

**Script.** Baseline reproduced on the chapter at 85fd72e (500 lines, reflex/cortex sentences
included): 0 FAIL, 7 WARN, 100 PASS. There was no FAIL to triage and no script change. All line
numbers below are for that version.

**Agents.** The argument agent (D1, D2, D4, D6, D10) filed 23 findings: 1 BLOCKER, 3 MAJOR,
13 MINOR, 6 NIT. The citation/presentation agent (D5, D7, D8, D9, D11, D12, fig:architecture)
filed 24: 1 BLOCKER, 5 MAJOR, 11 MINOR, 7 NIT. Clean build of the Ingenieur: 0 errors, 0
undefined citations or references, 0 Overfull lines in Ch3. Promises: of the 12 Ch1 promises, 10
are kept and 2 are partial (P8, P15, see the MINOR list). P17 is kept word for word ("bypasses the
stages that interpret speech, not the stages that check commands"). No performance property is
stated as achieved. D6 PASS.

**Verifier.** 10 BLOCKER/MAJOR findings were sent: 6 CONFIRMED, 2 DOWNGRADED (C1 to MAJOR, C6 to
MINOR), 2 PARTIAL, 0 REFUTED. The verifier corrected the reviewers' fixes for C2 and C3 (both
contained a false fact) and re-ran the code behind A1, A2 and A3. Full reports:
`.scratch/thesis-review/agents/11-ingenieur-ch3/` (argument.md, citation-presentation.md,
verifier.md).

| # | Sev | Line | Finding | Verifier | Proposed fix (verifier-corrected) |
|---|---|---|---|---|---|
| V1 | BLOCKER | 293-295 | "held within 50~m of the origin by scaling the whole vector ... where clamping each component separately would rotate it". The code does something else. `schema/validate.py:120-122` clamps the height to 0.5-15 m on its own first, the per-component clamp the sentence rejects. `:132` then computes the 3-D distance from the origin, and `:136-141` scales only x and y. `[30,30,20]` -> `(30,30,15)` changes the direction. ADR-0001 §2 agrees with the code. | CONFIRMED (ran it) | "A target position has its height clamped to 0.5--15~m, like a target height; if it then lies more than 50~m from the origin, its horizontal part alone is scaled down until it does, so that the commanded bearing survives the clamp, where clamping each horizontal component separately would rotate it." |
| V2 | MAJOR | 109-110, 154-158 | The ordering rule protects only the utterance already in progress. Queued utterances take a sequence number only when the worker dequeues them (`stream.py:157,175`, `pipeline.py:188`), and a trigger does not clear the queue. So an utterance spoken before "swarm hold" but still queued is numbered after the hold and dispatched (the swarm is still FLYING). After an abort the state is ABORTED, so only a hold is affected. Queueing occurs (Exp-2 queue p99 430 ms, max 1,231 ms). | CONFIRMED (reproduced with the real Dispatcher and state machine: hold seq 1 applied, in-progress seq 0 discarded, queued seq 2 `rotate` dispatched) | Author's choice. (a) Code: reserve the number when the frame loop hands the utterance to the worker, or have a trigger clear the queue. (b) Prose: "The rule covers the utterance in progress when the trigger fires. An utterance already endpointed and waiting behind it reserves its number only when the worker takes it up, so after a hold it compares as newer and is not discarded" + pointer to `sec:limitations`. Caption: "whose sequence number precedes the latest reflex-path command". |
| V3 | MAJOR | 158-162 | "What the cancellation governs is recovery ... bounds at 300~ms". `abort()` reaches only a decode already running (`parser.py:215-224`, no-op otherwise, no pending flag). Transcription is a blocking `subprocess.run` (`data/asr.py:110`), and there is no sequence check before the decode. A trigger during transcription therefore leaves transcription and a full decode to run before the result is discarded. The 300 ms criterion (Ch1 l.176) applies to every trigger. Exp-2 tested only triggers during a decode (78/78). | CONFIRMED | "The cancellation reaches only a decode already in progress. A trigger that arrives while the utterance is still being transcribed leaves the transcription, and the decode that follows it, to run to completion before the ordering rule discards the result; in that case recovery is bounded by the remaining parse-path stages, not by the cancellation." |
| V4 | MAJOR (down from BLOCKER) | fig. 71, 84-85; caption 111-112 | The figure draws the validator (layer 2) only on the parse path, on the Pi, and the reflex arrow runs straight to the bus. The workstation node lists only the state machine and the ordering rule. The caption's "the state machine validates every command, from either path" is correct only because `fsm.py:165` calls `validate()`, and it blurs the figure's own layer-2/layer-3 labels. | DOWNGRADED: the caption already says every command is validated, and the Pi-side validator is real (`pipeline.py:200`). So the figure is incomplete, not contradictory. | Workstation node: "Validator (layer 2),\\ state machine (layer 3),\\ ordering rule". Caption: "the validator and the state machine check every command, from either path, before it takes effect; layer 2 also runs on the Pi before a parse-path command is published". (Covers argument MINOR 14.) |
| V5 | MAJOR | 369, 413-414 | "gives every stage of both paths a target". The reflex path has only span rows. The list of what the offset anchor contains leaves out the spotter's decision delay (frames after the offset before the score crosses the threshold). prd §4.4 names it, and the generated Exp-2 table reports it as a sub-row. Without it a reflex miss cannot be traced to a stage (RQ2). | CONFIRMED (`branch_a.py` fires on the first frame at or above the threshold; "the classifier" does not cover the wait) | l.369: "every stage of the parse path, and each span of the reflex path, a target". l.413-414: add "the spotter's decision delay, the frames after the offset before its score crosses the detection threshold"; say the parts are not budgeted separately and the 150 ms span bounds their sum. No measured number. |
| V6 | MAJOR | 242-245 | `\cite{oww}` sits on "scores a fixed window of audio", which openWakeWord supports (training notebook window size; `train.py` `input_shape=(16,96)`). The consequence "invites more false accepts" has no source. openWakeWord's `hey_jarvis` page says a shorter phrase gives more false *rejects*. | PARTIAL: citation placement is fine; the consequence is an uncited claim (D5c). The reviewer's fix put the project's own 1.975 s window (`train_wake.py`) under `\cite{oww}` -- wrong. | Keep the cite on the fixed-window clause only. State the consequence as the design's assumption ("the design assumes a one-word class gives the classifier less evidence and so more false accepts") with a forward pointer to the keyword-spotter evaluation in Ch5, or cut it. |
| V7 | MAJOR | 245-246 | "The shared word \emph{swarm} supplies an onset that is uncommon in ordinary speech" (seeded). Nothing in references.bib or results/ supports it. | PARTIAL: uncited, as seeded. The reviewer's rewording ("not a word the operator uses in other commands") is false: *swarm* appears in parse-path transcripts, 6/200 in `test_golden.jsonl` and 92/1940 in `train.jsonl`. | Cut the sentence and put the subject back in the next one ("The shared word also brings the two classes closer acoustically ..."). Or say only that the shared onset's effect on false accepts is measured, not assumed. |
| V8 | MAJOR | 283-284 | "a context-free grammar can limit how many digits a number has, not whether that number is an admissible altitude". False in general: a bounded fixed-precision range is a finite, hence context-free, language. The same paragraph (l.282) says the grammar restricts identifiers to five, which `cmd.gbnf:43` does with `[0-4]`, a value range. | CONFIRMED (reclassed D2/D4, not D5c; MAJOR because the design fact, magnitude left to layer 2, is true) | "It does not bound a number's value: \gls{gbnf} has no numeric-range construct, and a range spelt out as digit patterns would force an out-of-range value to an in-range one silently, where the second layer clamps it and logs the change. Every constraint on magnitude therefore falls to the second layer." Same error in `master/ch3_method.tex:97-98` and the `cmd.gbnf` header comment: raise it with the Master. |
| V9 | MAJOR | caption 459-461 vs row 467 | "The reflex path runs entirely on core~0, so no parse-path work is scheduled on the core that serves it". The table's own row 0 puts the endpointer on core 0 (`stream.py:153,169,172`, same thread as the spotter), and l.34, the caption at l.106 and the figure (l.93) make endpointing a parse-path stage. | CONFIRMED | "Core~0 runs the audio frame loop, which includes the reflex path and the parse path's endpointer. No work of the parse-path worker (recognition, decoding, validation) is scheduled on core~0." |

**Heading WARNs (D12).** The five "Layer 1/2/3" and "Core 0" / "Cores 1--3" lead-ins pass: the
numbers are identifiers the chapter defines, not results. The two clause headings are MINOR:
l.353 -> "Residual error classes.", l.489 -> "Limits of core pinning.".

**Seeded refinements.** The `hover` wording is defensible. Leaving out the widening of an empty
identifier list is right, because the grammar makes that branch unreachable (argument NIT 21).
`set_param` "reduces speed or spacing" is questionable for spacing: closer vehicles, and every
vehicle moves to a new slot, which is l.223's reason for failing `formation` (argument MINOR 7).
The 5,500 ms, 2,600 ms and memory decisions were not raised.

**MINOR / NIT, not verified (spec step 4), listed for decision.** Row numbers refer to the agent
reports (A = argument.md, P = citation-presentation.md):
- Promises: P15 partial, because the validator's fallback and "a cancelled decode publishes
  nothing" (Ch1 l.269-271) are only implied (A9). P8 partial, overlaps V3. The promise to Ch5 that
  every budget row is measured is at risk: the generated table has no "Language-model stages
  combined" row and gives no target for start of speech (A17).
- Argument: l.24 "neither path can spend the time of the other" vs §3.5's own limits (A5); l.176
  "The only protection is" (A6); 2,350 ms subtracts budgets with different anchors (A8); $T_0$
  defined twice (A10, P14); the 50 ms row's state-machine check lies past the bus where the span
  ends (A11); "in order" for the validator rules, which the code applies in another order (A12);
  l.279-281 vs l.299-300 on truncated decodes (A13); no ack/retransmit on the stop datagram over
  Wi-Fi (A15); no hand-off paragraph to Ch4 at the end (A16, also A23).
- New from the verifier (unverified): l.38 "share nothing between the audio buffer and the bus",
  but the endpointer and the spotter share a thread. A spoken stopping phrase is also queued on the
  parse path and dispatched after the hold (related to V2).
- Bib: `silero` has no year and a shortened title; the README gives 2024 (C6, down to MINOR).
  `llamacpp` has no year (2026, build b10863) (P7).
- Acronyms and codes: "JSON" in the figure before its first expansion (P8); UDP typed by hand,
  with no key (P9); Q4\_K\_M never defined (P10).
- Figures: two dashed arrows with different meanings and only one explained; layer labels shown
  before §3.3 (P11); where the bus sits, l.116 vs l.128/131 (P12); l.191 points at the wrong
  paragraph (P13).
- Register: l.437-438 chiasmus (P17); "obvious" l.252, the vague qualifier l.428, figurative
  phrasing l.236-237, 255-256 (P20-P22); the reflex/cortex analogy is a wording note only (P23).
- NIT: 14 sentences over 40 words (P18); "whisper tiny.en" vs `whisper.cpp tiny.en` (P19);
  l.19 and l.146 point at the whole of Ch4 where `sec:runtime` exists (A19, P24); no section names
  its RQ (A22).

### 2026-09-24 -- author's decisions on V1-V9

- **V1, V4, V5, V8, V9: accepted**, applied with the verifier's wording.
- **V6, V7: the verifier's versions.** The cite now covers the fixed-window clause only. The
  false-accept consequence is stated as a design assumption, "not tested against a one-word
  alternative", with a pointer to `sec:keyword-spotter-evaluation`. The "uncommon onset" sentence
  is cut, and the next sentence takes "the shared word \emph{swarm}" as its subject.
- **V2, V3: stated as limitations, code unchanged.** The Exp-2 figures were measured on this code,
  and changing it would leave the chapter describing an unmeasured system. §3.1 "Preemption and
  ordering" now says: (V2) queued utterances number at dequeue, so after a hold a queued command
  takes effect, while after an abort the state machine rejects it; (V3) the cancellation reaches
  only a running decode, so a trigger during transcription can exceed the recovery criterion.
  Both point to `sec:limitations`.
- **New obligation for Ch6 `sec:limitations`** (scaffold, not yet in its bullet list): name both
  limitations. For V3, also say that the latency experiment triggered only during decodes (78/78,
  `results/exp2_analysis.md`), so its recovery figure does not cover the transcription case.
- **Script.** V1 moved the anchor of the 50 m claim, and the script FAILed as it should. It is
  re-anchored to "more than 50~m from the origin" with the same expected value (POS_MAX_NORM). New
  checks: the height clamp 0.5--15 m, and a behavioural check of `_clamp_pos` (z first, then only
  x, y scaled). The selftest mutation is re-anchored too; both Ch3 mutations are still caught
  (run through `selftest.run()`; the full selftest still stops at master_ch4.py:203).
- **After the fixes:** 0 FAIL, 7 WARN, 103 PASS. Clean build: 0 errors, 0 undefined
  citations/references, no dropped float, no overfull box.
- **Open:** the 7 heading WARNs. Five are justified (the numbers are identifiers). Two are
  pending the author (l.367 "What the layers do not catch.", l.506 "What pinning cannot
  isolate."). Also open: the MINOR/NIT list above.

### 2026-09-24 -- MINOR/NIT decisions; issue resolved

**Fixed** (chapter commit after fd426b1): both claim headings -> "Residual error classes.",
"Limits of core pinning."; hand-off to Ch4 at the chapter end (A16, A23); $T_0$ given one
definition (A10, P14); l.24 absolute (A5); "in order" (A12); truncated decode vs "only strings
of the language" (A13); P15 stated in full in layer 3 (A9); `set_param` fail-safe for reduced
speed only (A7); JSON expanded before the figure (P8); UDP acronym key (P9); Q4\_K\_M glossed
(P10); the l.202 pointer (P13).

**Kept, with the reason:**
- Sentences over 40 words (P18), register NITs (P17 chiasmus, P20-P22), the analogy (P23), and
  "whisper tiny.en" vs `whisper.cpp tiny.en` (P19): left for the final whole-document language
  pass, so that one convention is applied once across all chapters.
- Stop datagram with no acknowledgement over Wi-Fi (A15), and the 50 ms row whose state-machine
  check lies past the bus (A11): these are limitations of the measured system, so they go to Ch6
  `sec:limitations` and to Ch5's end-point statement (already a Ch5 obligation above), not into
  the design chapter.
- Missing bib years, `silero` 2024 (C6) and `llamacpp` 2026 (P7): bibliography entries are the
  author's to verify against the primary page (SKILL §4); not touched here.
- The Ch5 promise that every budget row is measured (A17): the generated table has no
  "Language-model stages combined" row. This is a Ch5/`eval/tables.py` question, raised when Ch5
  is drafted.
- UDP prints in the figure before its expansion: a figure can only carry `\acrshort`, and the
  first prose use is in the 3.1 "Command bus" paragraph.
- Remaining items not in the fix list (A6, A8, A14 covered by V4, A18-A22, P11, P12, P24, and the
  verifier's two unverified notes): judged not worth a change in this pass. The verifier's second
  note (a spoken stopping phrase is also queued on the parse path and dispatched after the hold)
  goes with V2 into Ch6 `sec:limitations`.

**Ch6 `sec:limitations` now owes** (scaffold at ch6_conclusion.tex:66): V2 (queued utterance
after a hold, including the spoken stopping phrase itself), V3 (trigger during transcription;
recovery measured only during decodes, 78/78), A15 (unacknowledged stop datagram).

**Final:** 0 FAIL, 5 WARN, 103 PASS. The 5 WARNs are the Layer/Core headings, justified as
identifiers. Clean build: 0 errors, 0 undefined citations/references, 0 dropped floats,
0 overfull boxes.
