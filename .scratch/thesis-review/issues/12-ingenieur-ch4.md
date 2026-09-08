# Issue 12: ingenieur-ch4

Status: open
Blocked by: 11
Chapter: thesis/ingenieur/ch4_implementation.tex (432 lines, lead-in + 6 sections, 8 distinct cites:
whispercpp, llamacpp, silero, pytorch, oww, piper, reynolds1987, pyflyt; drafted in 649feb6
(lead-in, 4.1), 4c8f3e2 (4.2), f34c84f (4.3), 52eda41 (4.4), db9d038 (4.5), 9b84c39 (4.6); STATE.md
record ae2573f. Hashes as on master after the history was redated; the chapter's content is
unchanged)
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

### 2026-09-24 -- review, verified findings (awaiting the author's decisions)

**Script.** Baseline on the chapter at 9b84c39 (432 lines), re-run before this entry: 1 FAIL,
15 WARN, 197 PASS. The first run gave 9 FAIL: six were script errors (triage in 57542f5's
message), and the one left is a chapter error: l.123 "14% of the training negatives" is the
all-splits share (720/5,040); the training split is 468/3,930 = 11.9% (verified as A2). All line
numbers below refer to that version.

**Agents.** The argument agent (D1, D2, D4, D6, D10) filed 36 findings: 5 BLOCKER, 7 MAJOR,
17 MINOR (4 raised for Ch1), 7 NIT (1 raised for Ch3). The citation/presentation agent (D5, D7,
D8, D9, D11, D12) filed 34: 0 BLOCKER, 3 MAJOR, 13 MINOR, 18 NIT. Clean build of the Ingenieur: 0
errors, 0 undefined citations or references, 0 Overfull lines. Promises kept by Ch4: Ch1's
structure (in order), Ch1/Ch3's third mechanism (kept for separation only, on the kinematic
backend, MINOR A23), Ch3's uncached prefix (kept; `parser.py:252` agrees), Ch3's reset rule
(kept). Ch3 V2: consistent. Ch3 V3: l.179-181 consistent, l.187-188 not (A6). D6 PASS.

**Verifier.** 15 BLOCKER/MAJOR findings were sent: 14 CONFIRMED, 1 DOWNGRADED (C3 to MINOR),
0 PARTIAL, 0 REFUTED. The verifier corrected seven of the reviewers' fixes (A1, A3, A7, A9, A11,
A12, C1): A1's "some frames later" is false at the median of the test abort class (-3 ms); A9's
evidence wrongly said no swarm/ module imports the validator (fsm.py does); A11's "(17 were
run)" is an outcome. It re-ran the code behind A3 (fake llama-server), A4 and A5 (PyFlyt, seeds
42/7/1), A10 (150 protocol trials) and C2 (forward Euler on the real NumpyEnv). Full reports:
`.scratch/thesis-review/agents/12-ingenieur-ch4/` (argument.md, citation-presentation.md,
verifier.md). A = argument agent's row, C = citation agent's row.

| # | Sev | Line | Finding | Verifier | Proposed fix (verifier-corrected) |
|---|---|---|---|---|---|
| V1 (A1) | BLOCKER | 121-122 | "which places detection at the keyword offset". `train_wake.py:220-228` labels a window positive only if it spans the phrase plus a margin (0.04 s measured, 0.45 s fitted); the labels say which windows are positive, not when the head fires. `results/wake_training.md`: delay after the last voiced sample -3 to 358 ms at p95; Ch5 l.93-97 puts the reflex miss (540 ms p95) in exactly this delay. | CONFIRMED | Replace l.119-122: positive = a window from before the phrase to past its end by a margin (40~ms measured, 450~ms predicted from the voice's length setting); negative = none of the phrase; a window that cuts the phrase is discarded. "A head is therefore trained to fire on the complete phrase rather than on a fragment of it, but the labelling does not fix the frame at which it fires. The time from the keyword offset, the anchor of the reflex budget, to the first frame above the threshold is the spotter's decision delay; it is part of the reflex latency, and Sections~\ref{sec:keyword-spotter-evaluation} and~\ref{sec:latency-experiment} report it." (full text: verifier.md A1) |
| V2 (A2) | BLOCKER | 123-124 | "14\% of the training negatives" is the all-splits share; train split 468/3,930 = 11.9%. Script FAIL. | CONFIRMED (recounted) | "the hand-written near-misses, 12\% of the negative clips of the training split" (468 of 3,930 may be added: a corpus count, not a measurement). The comment at `train/train_wake.py:87` has the same 14%: separate code commit. |
| V3 (A3) | BLOCKER | 181-183 | "any failure of a request ... no command is published". `parser.py:257` catches OSError/ValueError/KeyError only; `:266` reads `data.get("content","")`. A JSON error body on `/completion` returns `''`, the validator makes it a hold, and the hold is published. | CONFIRMED (fake server: HTTP 500 and llama-server's real 400 "exceeds the available context size" both publish `{'intent':'hover'}`; a non-JSON body, or any error on the first two requests, raises ParseAborted) | "The parser treats a failed request as an interrupted decode: a closed connection, a timeout, a reply that is not \gls{json}, or an error answer to either of the first two requests. It cannot tell a cancellation from such a fault and does not need to: no command is published for that utterance, and the event is logged. An error answer to the completion request is not treated so. It carries no command text, the validator resolves the empty output to a hold like any other output it cannot accept, and the hold is published." Or (code) make `parse()` raise on non-2xx / missing `content` and keep the sentence. Fail-safe, so no Ch6 item. |
| V4 (A4) | BLOCKER | 417-419 | "the physics backend is what shows that those results describe a controller that also flies against rigid-body dynamics". `test_pyflyt.py` flies one placement (seed 42), checks the final state only, no clamp, no collision count. | CONFIRMED (PyFlyt, seeds 42/7/1 x 3 shapes: 8/9 pass; seed 7 wedge ends at accuracy 0.60, closest pair 0.202 m, 10 ticks under 0.35 m; NumpyEnv, same seed, no clamp, never below 0.453 m) | "The formation-control results come from the kinematic backend alone. The physics backend's tests check that the same controller, with the same gains, also brings five rigid-body quadrotors into each formation from one initial placement; they do not reproduce the experiment's measures and apply no separation clamp. Whether the experiment's results hold under rigid-body dynamics is therefore not established (Section~\ref{sec:limitations})." New Ch6 item. |
| V5 (A5) | BLOCKER | 382-383 | "velocities in metres per second, in a world frame". `pyflyt_env.py:111-113` returns `state(i)[2]`, which PyFlyt 0.29.0 expresses in the body frame (`quadx.py:520-522`, `aviary.py:341`); positions and the setpoint are world-frame. | CONFIRMED (up to 0.50 m/s difference within a 12 s run; rotating to world frame does not rescue seed 7, so V4 stands either way) | Author's choice. (a) Code, preferred: return `p.getBaseVelocity(id)[0]` (world frame) from `PyFlytEnv.velocities`, then re-run all five tests before "All five tests pass" is kept. (b) Prose: "The interface fixes a world frame with the vertical axis pointing up. The physics backend departs from it for velocities: it returns the linear velocity as PyFlyt reports it, in each vehicle's body frame, so on that backend the controller's velocity terms act on a vector rotated by the vehicle's attitude. Positions and the velocity setpoint are in the world frame." + Ch6 item. |
| V6 (A6) | MAJOR | 187-188 | "How quickly the server stops decoding ... bounds the preemption-recovery criterion". Inverts the relation, and contradicts Ch3 V3: `abort()` is a no-op between requests and during transcription. | CONFIRMED | The reviewer's fix as written (argument.md #6): when a request is in flight, the server's reaction sets the recovery that the criterion bounds; a trigger during transcription or between requests closes nothing (Section~\ref{sec:dual-path}), and can exceed the criterion. |
| V7 (A7) | MAJOR | 195-196 | "records the affinity of every thread of the server and of the runtime at the start of each run". `exp2.py` records the server's threads at server start, the main thread and the load thread; never the branch-b worker, which does not even run in the reflex trials. | CONFIRMED | "The latency experiment records the affinity of every thread of the language-model server when the server starts, and that of the frame-loop thread and of the load thread; the worker's own restriction, and so that of the recogniser processes it starts, is applied by the code but not recorded." |
| V8 (A8) | MAJOR | 63-66 | Promises that the pick-up lag and the compute time are both reported by `sec:latency-experiment`. `exp2.py:273-274` keeps only `compute_s`; no lag in `results/`. | CONFIRMED | "For every frame the loop measures how late it picked the frame up and how long the spotter and the endpointer took on it; the second is the quantity against which the core-0 constraint of Table~\ref{tab:core-allocation} is judged, and Section~\ref{sec:latency-experiment} reports it." |
| V9 (A9) | MAJOR | 316-318 | "Commanded values reach the controller already held inside the envelope by the validator". No route from the validator to the controller is built (the chapter says so at l.297-304); the experiment commands the controller directly. | CONFIRMED | "The controller applies no envelope of its own. On the designed route the validator would bound every commanded value before it reached the controller (Section~\ref{sec:validation-layers}); that route is not built, and the formation-control experiment commands the controller directly, with a radius and a spacing that lie inside the envelope." |
| V10 (A10) | MAJOR | 317-318; 387-388 | The validator's speed ceiling (2.0 m/s, on `move`/`set_param` only) never reaches the integrator; both backends cap at 3 m/s. Implied by the chapter's own parameters, never stated. | CONFIRMED (150 trials: all 50 circle trials exceed 2.0 m/s) | "Nor is the envelope applied where motion happens. The backends limit speed to 3~m/s, above the validator's ceiling of 2.0~m/s on a commanded speed, so a formation change can move the vehicles faster than any command could set; Section~\ref{sec:limitations} returns to it." No measured speed in Ch4. New Ch6 item. Ch3's premise at l.193-195 goes to Ch3. |
| V11 (A11) | MAJOR | 112-126; 148-160; 399-411; 422-425 | Reproducibility: no optimiser settings, front-end release, library versions or test seed. | CONFIRMED (the repo pins all versions in `environment.yml`/`requirements.txt`, but no chapter points there) | "Training the spotter": "The heads are fitted by scikit-learn's Adam optimiser with L2 regularisation of $10^{-3}$, a learning rate of $10^{-3}$, batches of 256 and at most 40 epochs, on standardised inputs and with seed 42, over the feature models of openWakeWord's v0.5.1 release." "Physics backend": "PyFlyt~0.29.0; the tests place the vehicles with seed 42." Or one versions-and-seeds table, or a sentence naming the pinned environment file. |
| V12 (A12) | MAJOR | 40-41; 273-284; 425 | The lead-in excludes all measurements, but l.283-284 and l.425 state test outcomes; and `requirements_summary.tex` sends "Every cell passes" to `sec:state-machine`, which states no outcome. | CONFIRMED (`pytest swarm/test_fsm.py`: 100 passed) | Lead-in: "... every figure in this chapter is a parameter of the code or a criterion of a test, not a measured result; the outcomes of the automated tests that verify two criteria, the state machine's and the backends', are stated where the tests are described." After l.284: "Every test of the state machine passes, the 50 cell tests among them." |
| V13 (C1) | MAJOR | 344-347 | `\cite{reynolds1987}` on "cohesion and alignment". Reynolds' rules act on *nearby flockmates* and the paper rejects the whole-flock "central force model"; `control.py:280-281` uses the whole-swarm mean. "Cohesion/alignment/separation" are not the 1987 paper's terms. | CONFIRMED (primary text extracted) | "The third term is a global form of the flock-centring and velocity-matching rules of flocking~\cite{reynolds1987}, weighted at 0.15 towards the swarm's centroid and 0.25 towards its mean velocity. Reynolds' rules act on each vehicle's nearby flockmates; this term uses the whole swarm, the central-force form his model avoids, which is acceptable here because the formation slots, not flocking, organise the swarm." l.346: "its collision-avoidance rule is replaced by the potential field". Ch1 l.131 carries the same cite: raise in issue 06. |
| V14 (C2) | MAJOR | 390-392 | "Explicit integration adds energy on every tick ... a slow oscillation about the slot". Uncited, and false for this controller. | CONFIRMED (forward Euler on the real NumpyEnv, 150 trials: identical accuracy and final error to 4 decimals, no oscillation) | Cut the sentence; keep "The integration is semi-implicit: the velocity is updated first, and the new velocity moves the position." The reviewer's scoped option reports a result Ch4 cannot hold. The same argument in the `swarm/env.py:75-79` docstring: optional code fix. |
| -- (C3) | MINOR (down from MAJOR) | 364-365 | "roughly twice the rotor-tip diameter of a small quadrotor": unsourced gloss on a value already declared "a choice of this work". | DOWNGRADED | "The clamp distance of 0.80~m is a choice of this work, twice an assumed airframe span of 0.40~m, so that the clamp acts while there is still space between the airframes; neither backend models an airframe of that size." (PyFlyt's cf2x box is 0.09 m; the kinematic backend is a point mass.) |

**Seeded points.**
- 4.1 test split scored twice: kept, and Ch5 inherits it (ch5 l.162 "scored once for each of the
  heads' two fits").
- 4.2 `cache_prompt=false`: kept as the author decided; Ch3's promise is delivered. C11 (MINOR)
  notes that the server's own documentation states the risk and could be cited.
- 4.3 bus interface: Ch4 is right. Ch3 l.136-137 "sits behind an interface" still reads as an
  abstract type, and the `bus.py` docstring is false (A-R5, NIT): raise for Ch3 / code.
- 4.4 raw-intent defect: text correct; the promise that `sec:limitations` records it is
  unconditional while the Ch6 scaffold is conditional (A25, MINOR).
- 4.5 formation only, 3 of 6 shapes: Ch4 correct. Ch1's controller row ("PID point navigation")
  does not hold: no point-navigation command exists (A-R2), and Ch1 l.60-61 says every command
  reaches the controller validated (A-R4). Both MINOR, for Ch1.
- 4.6 48 Hz vs Ch1 l.69 "at 50 Hz": a Ch1 finding, MINOR (A-R1). Related in Ch4 itself: "every
  20~ms", "flown for 12~s" hold on the kinematic backend only; on PyFlyt 600 ticks are 12.5 s of
  simulated time and dt stays 0.02 against a 20.83 ms tick (A17; verifier new note 1).
- Not built: `runtime/audio.py`, `runtime/main.py` still absent (ls, and the script re-checks).

**New from the verifier (unverified).** (1) the 12.5 s / 20.83 ms point above; (2) V4 stands
however V5 is fixed; if V5(a) is applied, all five PyFlyt tests must be re-run; (3)
`swarm/simulate.py:113-116` runs the clamp on any env but writes back only for NumpyEnv (no
reported figure affected); (4) for issue 13: `requirements_summary.tex:15` "Hover smoke test on
both" -- the tests are formation tests, and "Passes on both" should be scoped to one placement;
(5) Ch6 `sec:limitations` is still `\TODO`, and its outline lacks V4, V5 (if prose) and V10.

**MINOR / NIT, not verified (spec step 4), listed for decision.** A = argument.md, C =
citation-presentation.md.
- Argument, MINOR: l.61-62 "the queue is the only link" vs l.179-181, 223-225 (A13); l.81-82 VAD
  end rule (a window in 0.35-0.5 counts as silence, the reset needs >= 0.5) (A14); l.134-136
  evaluation vs runtime debounce count different events when both heads fire (A15); l.280-281
  "unchanged" -- the test checks the intent only (A16); 20 ms / 12 s on PyFlyt (A17); three timing
  observations in a parameters-only chapter (l.394-395, 408-409, 411-412) (A18, also C20); the
  consumer thread inherits core 0, unstated (A19); formation subset / heading / centre not in the
  schema (A20); "routinely produces crossing paths", "would fly through each other" (A21, also
  C12); flocking "keeps the group together on the approach" (A22); third mechanism realised for
  separation only (A23); no hand-off to Ch5 at the end (A24); the unconditional `sec:limitations`
  promise (A25).
- For Ch1 / Ch3 (not fixed in Ch4): A-R1 50 Hz; A-R2 "point navigation"; A-R3 "hover smoke test"
  (Ch1 l.132 and `eval/tables.py`); A-R4 commands reach the controller; A-R5 bus interface (NIT).
- Citation / presentation, MINOR: C3 (above); C4 l.415-417 the criterion says nothing about the
  same gains; C5 l.365-367 the collision criterion has no distance, and its name drifts; C6 UDP
  typed by hand (key `udp` exists); C7 ONNX has no key and no expansion; C8 ONNX Runtime and
  scikit-learn uncited, no bib entries (author's job, SKILL §4); C9 PyTorch requirement uncited;
  C10 Silero defaults sourced from package code, not the README; C11 the caching risk could cite
  the server docs; C12 greedy assignment, and the chapter never names its assignment algorithm;
  C13 yaw *rate* is commanded (as zero); C14 critical-damping assumptions unstated, "slightly";
  C15 "shows", "would prove nothing" (l.418-420); C16 heading "One controller, one set of gains."
  is a claim.
- NIT: 85% of five vehicles means all five (A26); wall-clock covers three requests (A27); thread
  count differs per caller (A28); quantisation causal link (A29); no section names its RQ (A30);
  l.338-341 rationale written as fact (A31); potential field uncited here, cited in Ch1 (C17);
  `piper`/`silero` titles paraphrased (C18); "far shorter" (C19); vague qualifiers, l.96 has an
  exact 1.98 s (C20); "handled" (C21); 18 sentences over 40 words (C22); criterion names and
  "drone" vs "vehicle" (C23); first `\gls{gguf}` leaves GGML unexpanded (C24); "Qwen2.5-" line
  break, "4{,}096~bytes" (C25); "figure" ambiguous in the lead-in (C26); "harness" not glossed for
  the latency experiment (C27); `\emph` in the Artefacts heading (C28); headings l.57, 241, 286
  (C29-C31); aphorisms l.351, 384 (C32, C33); narrated history l.125-126, 283-284 (C34).

**Examiner questions (argument.md §6)** all trace to V1, V4/V5 and V9/V10; none needs a
separate fix.

### 2026-09-24 -- author's decisions on V1-V14; fixes applied

- **Accepted with the verifier's wording:** V1, V2, V4, V6, V7, V8, V9, V10, V12, V13, V14.
  V14 took the "cut" option. V12's lead-in now admits test criteria and states that the outcomes
  of the two criteria's automated tests are given where the tests are described; 4.4 gains
  "Every test of the state machine passes, the 50 cell tests among them".
- **V3: prose, code unchanged.** The latency figures were measured on this parser (same reason
  as issue 11's V2/V3). The published hold is fail-safe, so no Ch6 item.
- **V5: code.** `PyFlytEnv.velocities` now reads the world-frame velocity from Bullet
  (`getBaseVelocity`) instead of PyFlyt's body-frame `state(i)[2]`; the chapter's "world frame"
  sentence is now true and is unchanged. Re-run: `pytest swarm/test_pyflyt.py -m slow` 5 passed;
  `pytest swarm` 144 passed. No reported figure comes from PyFlyt.
- **V11: one sentence each.** 4.1: the front end is openWakeWord's v0.5.1 feature models; the fit
  is scikit-learn's Adam, L2 $10^{-3}$, learning rate $10^{-3}$, batch 256, at most 40 epochs,
  standardised inputs, seed 42. 4.6: PyFlyt~0.29.0; the tests place the vehicles with seed 42.
- **V2's code comment** (`train/train_wake.py:87`) corrected to 12% (468/3,930), all-splits 14%.
- **Ch6 `sec:limitations` outline** gains two bullets: V4 (transfer to rigid-body dynamics not
  established; seed 7 figures are in verifier.md, not in results/) and V10 (speed ceiling not
  applied at execution). Still missing from that outline, from issue 11: V2, V3, A15.
- **Script.** Four anchors followed the rewritten sentences (V2, V3, V7, V9), with the expected
  values unchanged; V3's judge() became two facts. New checks: the label margins (40/450 ms), the
  fit's settings, the v0.5.1 release, the PyFlyt pin, the test seed, the 3 m/s vs 2.0 m/s pair,
  and that the formation experiment bypasses the validator.
- **After the fixes:** 0 FAIL, 13 WARN, 217 PASS. `selftest.py` passes (all three Ch4 mutations
  caught). Clean build: 0 errors, 0 undefined citations/references, no Float too large, no
  Overfull box, 57 pages.

**New finding while applying V5 (open, author's decision).** The PyFlyt control tick is
**41.67 ms (24 Hz)**, not 20.83 ms (48 Hz). `Aviary.step()` is one step of the slowest drone
controller, and QuadX's runs at 120 Hz, so each call advances `updates_per_step` = 2 physics steps.
`PyFlytEnv.step` calls it `steps_per_tick` = 5 times: 10 physics steps per tick. Measured with
`aviary.elapsed_time` across one `step()`. So `effective_control_hz` (48) is wrong, the commanded
velocity is integrated with dt = 0.02 against a 41.67 ms tick, and a "12 s" test flies 25 s of
simulated time. Ch4 l.432-433 ("five ... 48~Hz rather than 50~Hz") is false, and so are the
docstring's "240 Hz and control at 50 Hz" and the A17 "12.5 s" note. The script WARNs on it
until decided. The review missed it because every check read the constants, not the simulated
clock.
