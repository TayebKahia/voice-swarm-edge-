# Issue 12: ingenieur-ch4

Status: open
Blocked by: 11
Chapter: thesis/ingenieur/ch4_implementation.tex (432 lines, lead-in + 6 sections, 8 distinct cites:
whispercpp, llamacpp, silero, pytorch, oww, piper, reynolds1987, pyflyt; drafted Thu 24 Sep in e0f1674
(lead-in, 4.1), 2be5441 (4.2), ee4f18b (4.3), 2e2116d (4.4), 084a227 (4.5), 11500b4 (4.6); STATE.md
record 667bbff)
Script: tools/review/ingenieur_ch4.py
Report: .scratch/thesis-review/reports/ingenieur_ch4.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/ingenieur_ch4.py
```

## Agents

Split like issue 11:

- **Argument agent** -- D1, D2, D4, D6, D10. Focus:
  - **Promises kept.** Ch1's structure paragraph (audio chain, runtime and bus, state machine,
    controller, backends, in that order) and safety-problem paragraph (the third mechanism realised in
    the controller). Ch3's two: the clamp (3.1 lead-in), and the reason for `cache_prompt=false` in
    `sec:runtime` (3.1 "Prompt and prefix").
  - **Promises made**, each with its label: to Ch5 (`sec:latency-experiment`,
    `sec:keyword-spotter-evaluation`, `sec:acoustic-robustness`, `sec:formation-control`) and to Ch6
    (`sec:limitations`, `sec:demonstration-protocol`). Check that Ch5 (drafted by another session)
    keeps the Ch5 ones.
  - **Every design-at-code-level claim, checked against the code**, not against STATE.md or prd.md.
  - **Consistency with issue 11's decisions.** Ch3 3.1 now says (V2) queued utterances take their
    sequence number at dequeue and (V3) the cancellation reaches only a running decode. Ch4 4.2
    "Preemption" must say nothing that contradicts either.
- **Citation / presentation agent** -- D5 (the 8 keys), D7, D8, D9, D11, D12. The chapter has no
  table or figure of its own; it checks the references to Ch1/Ch3 tables and `fig:architecture`.
- **Verifier**, given only the BLOCKER and MAJOR findings; re-runs code where a finding rests on
  behaviour.

## What the script establishes

Ch4 promises "every figure in this chapter is a parameter of the code, not a measurement", so every
number is checked against the module it describes (4.1: stream.py, vad.py, the silero-vad default,
branch_a.py, train_wake.py, wake_heads.json, the wake manifest; 4.2: parser.py, pipeline.py, stt.py,
eval/surface_b.py, eval/exp2.py; 4.3: bus.py and the Dispatcher; 4.4: fsm.py, with the raw-intent
defect probed; 4.5: control.py and simulate.py, with the clamp exercised on a chain of three and a
coincident pair; 4.6: env.py, pyflyt_env.py, test_pyflyt.py). The promise check: no significant number
that is not a recomputed parameter appears, and none appears in `results/*.md` or
`thesis/generated/*.tex`. The three "not built" items are re-checked (`runtime/audio.py` and
`runtime/main.py` absent; no swarm/ module imports the state machine; only `eval/exp2.py` builds a
`StreamLoop`).

Selftest: three planted errors are caught (clamp distance 0.60 m -> `claim`; a measured false-reject
rate inserted -> `promise`; 45 legality cells -> `claim`).

## Seeded points (from the drafting session -- not findings unless the text is wrong)

- 4.1: the keyword-spotter test split was scored twice (`results/wake_training.md`). Kept as a
  procedure fact; Ch5's keyword-spotter section should inherit it.
- 4.2: the `cache_prompt=false` reason is parity with the accuracy measurement; the "caching changes
  nothing" assumption was not tested. No fix is promised (author's decision).
- 4.3: there is no abstract bus type (the bus.py docstring says there is); the bus has only run on the
  Pi's loopback. Ch3 3.1 says the bus "sits behind an interface": a contradiction to raise for Ch3?
- 4.4: the raw-intent defect (`FlightStateMachine(LANDING).handle_command({'intent':'set_param'})` ->
  Hover). Unreachable on the deployed route; Ch1 l.275 scopes its claim to that route.
- 4.5: the controller takes only a formation and implements 3 of the schema's 6 shapes. Do Ch1's
  controller row and Ch3's "no controller entry point" wording still hold?
- 4.6: PyFlyt's control rate is 48 Hz; Ch1 l.69 says "at 50 Hz". A Ch1 finding?
- "Not built" items stated once each, in their own section (author's decision): live capture 4.1,
  entry point 4.2, state machine -> controller link 4.4.

## Comments
