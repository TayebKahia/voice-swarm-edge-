# Issue 11: ingenieur-ch3

Status: ready-for-agent
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
