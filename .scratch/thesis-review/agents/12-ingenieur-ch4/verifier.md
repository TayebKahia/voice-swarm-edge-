# Adversarial verification: thesis/ingenieur/ch4_implementation.tex (issue 12)

The chapter as it is in the working tree has 432 lines, and every line number below refers to it.
Code was run with `~/miniconda3/envs/pfe_swarm/bin/python` from the repo root. Throwaway scripts are
in the session scratchpad (`v12/a3.py`, `a4.py`, `a5.py`, `a10.py`, `c2.py`), and none of them is in
the repo. The primary source (Reynolds 1987, red3d.com PDF) was fetched and its text extracted
locally. I worked only from the 15 BLOCKER/MAJOR findings and did not open the agents' full
reports. Nothing was edited except this file.

## 1. Summary

I checked fifteen findings:

- **14 CONFIRMED**: A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, C1, C2
- **1 DOWNGRADED**: C3, from MAJOR to MINOR
- **0 PARTIAL**
- **0 REFUTED**

That leaves **14 findings standing at BLOCKER or MAJOR**: 5 BLOCKER (A1-A5) and 9 MAJOR.

I changed seven of the proposed fixes: A1, A3, A7, A9, A11, A12 and C1. C2's fix should be the
"cut" option. Section 3 gives the reasons.

Notable results:

- **A3 reproduces exactly.** I ran a fake local server. An HTTP 500 carrying `{"error":{...}}` on
  `/completion` makes `parse()` return `raw=''` with no exception, and `PipelineRuntime.process`
  then publishes `BusMessage(seq=0, branch='B', command={'intent':'hover'})`. llama-server's real
  400 "exceeds the available context size" error body behaves the same way. A non-JSON error body,
  or any error on `/apply-template` or `/tokenize`, does raise `ParseAborted`.
- **A4 reproduces for seed 7.** I ran the loop of `test_pyflyt._fly` on PyFlyt for seeds 42, 7 and
  1 × three shapes. Eight of the nine runs pass the 85% criterion. The seed-7 wedge ends with
  formation accuracy 0.60 (slot errors 1.13 and 0.86 m). Its minimum pair distance is 0.202 m at
  tick 570, and it spends 10 ticks under the 0.35 m collision distance. The same seed on NumpyEnv
  without the clamp never closes below its 0.453 m spawn distance.
- **A5 is confirmed in the PyFlyt 0.29.0 source.** `quadx.py:520-522` says "express vels in local
  frame", `aviary.py:341` says "`state[2, :]` represents body frame linear velocity", and
  `PyFlytEnv.velocities` returns exactly that. The effect is not small: the world-frame velocity
  and the velocity returned to the controller differ by up to **0.50 m/s** within a 12 s run (seeds
  42 and 7, circle).
- **A5's code fix does not rescue A4.** With the velocity rotated back to the world frame, the
  seed-7 wedge still ends at formation accuracy 0.60, with a minimum pair distance of 0.218 m and 10
  ticks under 0.35 m. The two findings are independent. Seed 42 line and wedge still pass with the
  world-frame velocity. I did not re-run circle.
- **C2 is refuted in substance on the real NumpyEnv.** I ran the full 150-trial protocol (50 per
  shape, clamp as in `run_trial`) with forward Euler in place of semi-implicit Euler.
  - Formation accuracy is 1.000 in both cases.
  - The final mean error is identical to four decimals (0.2909, 0.1326, 0.0721).
  - Neither integrator changes the formation-accuracy series at all over the second half of any
    trial, so there is no oscillation.
  - The median convergence time differs by at most 0.06 s.

  The chapter's claim that explicit integration shows up "as a slow oscillation about the slot"
  does not hold for this controller.
- **C1 is confirmed from the primary text.** The paper's rules are "Collision Avoidance", "Velocity
  Matching" and "Flock Centering", each "with nearby flockmates". The paper names the
  whole-flock-centroid scheme the "central force model" and calls perfect global information "just
  plain wrong". The terms separation, alignment and cohesion do not occur in the 1987 paper; the
  WebFetch summariser claimed they do, and it was wrong. The code (`swarm/control.py:280-281`)
  implements the central-force form.
- **A2 recounted.** In the training split, 468 of the 3,930 negative clips are adversarial
  (11.9%). Over all splits the share is 720/5,040 = 14.3%. Per head, the adversarial clips supply
  3,276 of 34,860 negative windows (9.4%), with 7 windows per clip and 39,107 − 4,247 negatives.
- **A7 and A8 confirmed in the harness.**
  - `eval/exp2.py` records the server's per-thread masks (`task_affinity`, `:114-121`, `:398`),
    the main thread (`:405`) and the loader (`:242`, `:428`). It never records the `branch-b`
    worker.
  - The worker does not run in the reflex trials at all (`StreamLoop(..., branch_b=False)`,
    `:288`). It runs only in the parse-path phase (`:335`).
  - `_frame_ms` (`:273-274`) keeps only `compute_s`. No `lag` field appears in
    `results/exp2_raw/*.jsonl` or `exp2_analysis.md`.
- **A10 recomputed.** Over the 150 protocol trials with the clamp, all 50 circle trials exceed
  2.0 m/s (max 2.427). Line peaks at 1.892 and wedge at 1.425.
- **Ch6 `sec:limitations` is still `\TODO{draft}`.** Its outline, `ch6_conclusion.tex:67-102`, has
  no item for:
  - the body-frame velocity (A5);
  - the seed dependence of the physics backend (A4);
  - the speed ceiling not being enforced (A10).

  The pointers in the fixes resolve, since the label exists, but the author must add these items to
  Ch6's plan.

## 2. Verdicts

| # | Orig sev | Verdict | New sev | Line | Evidence (what I ran / read) | Fix (reviewer's, or corrected) |
|---|---|---|---|---|---|---|
| A1 | BLOCKER | CONFIRMED | BLOCKER | 121-122 | **Code.** `train/train_wake.py:220-228`: a window is a positive only if `start <= onset-0.01 and end >= kw_end + margin`, with margins 0.04 s exact and 0.45 s fitted (`:82-83`). Windows ending between the onset and `kw_end+margin` are discarded, not negatives. So the labels constrain which windows count as positive, not the frame at which the head fires. **Results.** `results/wake_training.md` gives delay p50/p95 from the last voiced sample of −3/131 ms (test abort) up to 45/358 ms (val hold). **Ch5 contradicts the chapter.** ch5:93-97 locates the reflex miss in "how long the spotter's score takes to cross the threshold after the keyword ends" (540 ms at p95 on the author's voice). "Places detection at the keyword offset" therefore contradicts Ch5 and results/. The "fitted" lengths come from a per-(class, voice) fit on Piper's `length_scale` (`:140-156`), so "speaking rate" is a fair gloss. | **Corrected fix.** The reviewer's "the score crosses the threshold some frames later" is false at the median of the test abort class (−3 ms). Replace l.119-122 with: "Training windows are labelled by where the phrase falls, not by the clip they come from: a window that begins before the phrase and extends past its end by a margin, 40~ms where the phrase's length was measured and 450~ms where it was predicted from the synthesis voice's length setting, is a positive; a window containing none of the phrase is a negative; and a window that cuts the phrase is discarded. A head is therefore trained to fire on the complete phrase rather than on a fragment of it, but the labelling does not fix the frame at which it fires. The time from the keyword offset, the anchor of the reflex budget, to the first frame above the threshold is the spotter's decision delay; it is part of the reflex latency, and Sections~\ref{sec:keyword-spotter-evaluation} and~\ref{sec:latency-experiment} report it." |
| A2 | BLOCKER | CONFIRMED | BLOCKER | 123-124 | **Recount** from `data/wake/wake_manifest.json`. Train negatives: adversarial 468, librispeech 1,779, speech_commands 1,683, total 3,930, so 11.9%. Val is 108/348 and test 144/762. All splits: 720/5,040 = 14.3%, which is where "14%" comes from. **Per-head windows:** 22 embeddings − 16 + 1 = 7 per clip, and 468 × 7 = 3,276 of 39,107 − 4,247 = 34,860 negative windows (9.4%). **Code comment.** `train_wake.py:87` carries the same 14%. | The reviewer's fix is correct: "the hand-written near-misses, 12\% of the negative clips of the training split". The count 468 of 3,930 may be added. It is a corpus figure, not a measurement. The code comment at `train/train_wake.py:87` needs the same correction; that is a code change for the author and a separate commit. |
| A3 | BLOCKER | CONFIRMED | BLOCKER | 181-183 | **Reproduced** (`v12/a3.py`). I ran a fake HTTP server and patched `transcribe_utterance`. A 500 with a JSON error body on `/completion` gives `parse` → `raw=''` and publishes `BusMessage(seq=0, branch='B', command={'intent':'hover'})`. llama-server's 400 `exceed_context_size_error` body gives the same result. An HTML (non-JSON) error body on `/completion` raises `ParseAborted` (ValueError) and publishes nothing. Any error body on `/apply-template` or `/tokenize` raises `ParseAborted` (KeyError on `prompt`/`tokens`). **Code.** `runtime/parser.py:257` catches `(OSError, ValueError, KeyError)`; `:266` reads `data.get("content","")`; `runtime/pipeline.py:200-201` validates and publishes. The claim "any failure of a request ... no command is published" is refuted, although the outcome is fail-safe. | **Corrected fix.** The reviewer's "unreadable reply" misses the KeyError path and leaves out that the hold is published. Use: "The parser treats a failed request as an interrupted decode: a closed connection, a timeout, a reply that is not \gls{json}, or an error answer to either of the first two requests. It cannot tell a cancellation from such a fault and does not need to: no command is published for that utterance, and the event is logged. An error answer to the completion request is not treated so. It carries no command text, the validator resolves the empty output to a hold like any other output it cannot accept, and the hold is published." (Or change `parse()` to raise on a non-2xx status or a missing `content`, and keep the current sentence. That is a code change for the author.) |
| A4 | BLOCKER | CONFIRMED | BLOCKER | 417-419 | **Tests.** `swarm/test_pyflyt.py:28-34` uses one seed (42), checks the final state only, applies no clamp and counts no collisions. **Re-run** (`v12/a4.py`, the `_fly` loop plus per-tick minimum pair distance), PyFlyt seeds 42, 7 and 1 × circle/line/wedge. 8 of 9 pass the ≥ 0.85 criterion. **Seed 7 wedge:** FA 0.60, errors [0.06, 0.13, 1.13, 0.13, 0.86] m, minimum pair 0.202 m at tick 570, 10 ticks < 0.35 m. The same seed on NumpyEnv (no clamp) stays at FA 1.00, with a minimum pair equal to the 0.453 m spawn distance. "Shows that those results describe a controller that also flies" therefore does not survive a second placement, and the experiment's collision and accuracy results do not transfer. | The reviewer's fix is correct and adds no number: "The formation-control results come from the kinematic backend alone. The physics backend's tests check that the same controller, with the same gains, also brings five rigid-body quadrotors into each formation from one initial placement; they do not reproduce the experiment's measures and apply no separation clamp. Whether the experiment's results hold under rigid-body dynamics is therefore not established (Section~\ref{sec:limitations})." Add the item to Ch6's `sec:limitations` plan, which is still TODO. Ch5's requirements-summary row "Passes on both" (issue 13) should be read against this. |
| A5 | BLOCKER | CONFIRMED | BLOCKER | 382-383 | **PyFlyt 0.29.0 source.** `core/drones/quadx.py:520-522` ("# express vels in local frame", `lin_vel = rotation.T @ lin_vel`) and `core/aviary.py:341` ("`state[2, :]` represents body frame linear velocity"). `swarm/pyflyt_env.py:111-113` returns `state(i)[2]`. Mode 6 takes a ground-frame setpoint and rotates it by yaw internally (`quadx.py:447-451`), so the setpoint is world-frame and the returned velocity is body-frame. **Magnitude:** max ‖v_world − v_returned‖ reaches 0.495 m/s (seed 42 circle), 0.497 (seed 7 circle) and 0.41 (seed 7 wedge), against a 3 m/s speed limit. Max yaw is 3-12°, and the rest comes from tilt. `swarm/env.py:15` itself says "ENU". | Both options stand; I prefer (a). **(a) Code:** return `p.getBaseVelocity(id)[0]` (world frame) from `PyFlytEnv.velocities`, then re-run the five tests before keeping "All five tests pass". With that patch, seed 42 line and wedge still pass (circle not re-run). **(b) Prose, corrected to be exact:** "The interface fixes a world frame with the vertical axis pointing up. The physics backend departs from it for velocities: it returns the linear velocity as PyFlyt reports it, in each vehicle's body frame, so on that backend the controller's velocity terms act on a vector rotated by the vehicle's attitude. Positions and the velocity setpoint are in the world frame." Add a Ch6 limitation item if (b) is chosen. |
| A6 | MAJOR | CONFIRMED | MAJOR | 187-188 | **Code.** `runtime/parser.py:215-224`: `abort()` is a no-op when `_conn` is None. `_post` clears `_conn` in `finally` (`:210-213`), so between the three requests nothing is in flight. `runtime/pipeline.py:189-192` runs STT before `parse`, with no cancellation hook. **Ch3 and Ch5.** ch3:170-174 already states V3. Ch5 (l.114-119) measures only triggers against the load thread (78/78 in flight) and attributes recovery to the server's once-per-second disconnect check. "Bounds the criterion" inverts the relation: the criterion bounds recovery. | The reviewer's fix is correct and adds no number. Keep it as written. Optionally end with "…(Section~\ref{sec:dual-path}), and can exceed the criterion". |
| A7 | MAJOR | CONFIRMED | MAJOR | 195-196 | **Code.** `eval/exp2.py:114-121` collects the set of distinct `Cpus_allowed_list` over the server's threads, recorded once at server start (`:398`). `:405` records the main thread. `:242` records the load thread when it starts, which is in the loaded phase, not at run start, and `:428` stores it. The `branch-b` worker pins itself (`runtime/stream.py:184-185`) and nothing reads its mask back. It is not even started in the reflex-path trials (`exp2.py:288`, `branch_b=False`), only in the parse-path phase (`:335`). Recogniser subprocesses are not recorded either. `exp2_analysis.md` l.5 lists only server, loader and frame loop. | **Corrected fix** (timing made exact): "The latency experiment records the affinity of every thread of the language-model server when the server starts, and that of the frame-loop thread and of the load thread; the worker's own restriction, and so that of the recogniser processes it starts, is applied by the code but not recorded." |
| A8 | MAJOR | CONFIRMED | MAJOR | 63-66 | **Code.** `runtime/stream.py:105-106,178` computes `lag_s` and `compute_s` in memory. `eval/exp2.py:273-274` writes only `compute_s`. `results/exp2_raw/loaded.jsonl` has `frame_ms` and no lag. Ch5 (l.97-100) reports compute only. The core-0 constraint (ch3:489, 501) is on per-frame work, which is compute, so the promise "the two quantities ... which Section reports" is not kept. | The reviewer's fix is correct: "For every frame the loop measures how late it picked the frame up and how long the spotter and the endpointer took on it; the second is the quantity against which the core-0 constraint of Table~\ref{tab:core-allocation} is judged, and Section~\ref{sec:latency-experiment} reports it." |
| A9 | MAJOR | CONFIRMED | MAJOR | 316-318 | **Code.** `swarm/simulate.py:102` commands the controller directly from `TrialSpec` defaults (`:58-59`, radius 5.0, spacing 2.0). `swarm/control.py` never calls the validator. **One evidence claim is wrong but does not change the verdict.** The reviewer says "no `swarm/` module imports `schema.validate`", but `swarm/fsm.py:32,165` does. The state machine does not drive the controller (ch4:297-304), so nothing validated reaches the controller. The sentence describes a route that does not exist, two sentences after saying so. | **Corrected fix** (no new number needed, and it says the values lie inside the envelope): "The controller applies no envelope of its own. On the designed route the validator would bound every commanded value before it reached the controller (Section~\ref{sec:validation-layers}); that route is not built, and the formation-control experiment commands the controller directly, with a radius and a spacing that lie inside the envelope." |
| A10 | MAJOR | CONFIRMED | MAJOR | 317-318; 387-388 | **Code.** `schema/schema.py:116` sets speed (0.2, 2.0). That is a field of `move` and `set_param` only (`:151-201`); `formation` carries no speed. `swarm/env.py:44-45` and `pyflyt_env.py:96-97` cap speed at 3 m/s. **Re-run** (`v12/a10.py`, 150 protocol trials, clamp as in `run_trial`, seeds index × 42 as in `results/exp4.csv`): circle 50/50 trials > 2.0 m/s, max 2.427; line max 1.892; wedge max 1.425. The limitation is implied by the chapter's own parameters and never stated. Ch3's latency-decisive premise (ch3:193-195) belongs to issue 11 and Ch3, not here. | The reviewer's fix, lightly corrected (the ceiling bounds a commanded value, not a formation change): "Nor is the envelope applied where motion happens. The backends limit speed to 3~m/s, above the validator's ceiling of 2.0~m/s on a commanded speed, so a formation change can move the vehicles faster than any command could set; Section~\ref{sec:limitations} returns to it." The measured 2.43 m/s stays out of Ch4. Add the item to Ch6's plan. Raise ch3:193-195 against Ch3. |
| A11 | MAJOR | CONFIRMED | MAJOR | 112-126; 148-160; 399-411; 422-425 | **Code.** `train/train_wake.py:238-254` sets `alpha=1e-3`, `batch_size=256`, `learning_rate_init=1e-3`, `max_iter=40`, `random_state=42` and a StandardScaler. The solver is sklearn's default Adam. **Other sources.** `runtime/models/wake/wake_heads.json` gives the feature models' source as the openWakeWord v0.5.1 release tag. `environment.yml` and `requirements.txt` pin onnxruntime 1.29.0, openwakeword 0.6.0, PyFlyt 0.29.0, scikit-learn 1.9.0 and silero-vad 6.2.1. `swarm/test_pyflyt.py:28` seeds 42. **Mitigating but not curing:** the repo pins every version, but no chapter points to that file. Ch5 l.48-50 says only that the environment is "pinned". | **Corrected fix.** Drop the reviewer's "(17 were run)": it is a training outcome, not a parameter, so it breaks the chapter's own rule. Name the optimiser. For "Training the spotter": "The heads are fitted by scikit-learn's Adam optimiser with L2 regularisation of $10^{-3}$, a learning rate of $10^{-3}$, batches of 256 and at most 40 epochs, on standardised inputs and with seed 42, over the feature models of openWakeWord's v0.5.1 release." For "Physics backend": "PyFlyt~0.29.0; the tests place the vehicles with seed 42." Preferably add one short versions-and-seeds table, or a sentence naming the pinned environment file shipped with the code. |
| A12 | MAJOR | CONFIRMED | MAJOR | 40-41; 273-284; 425 | **Summary table.** `thesis/generated/requirements_summary.tex:15,17` sends "Every cell passes / Met" to `sec:state-machine` and "Passes on both" to `sec:simulation-backends`. 4.4 never states an outcome. **Tests.** `pytest swarm/test_fsm.py`: 100 passed. **Lead-in.** The lead-in excludes measurements, yet l.283-284 (three injected faults each made tests fail) and l.425 (all five pass) are already test outcomes. | **Corrected fix** (no brittle test count): lead-in "... every figure in this chapter is a parameter of the code or a criterion of a test, not a measured result; the outcomes of the automated tests that verify two criteria, the state machine's and the backends', are stated where the tests are described." In 4.4, after l.284: "Every test of the state machine passes, the 50 cell tests among them." (Ch5's "Hover smoke test on both" row wording goes to issue 13; the backends' tests are formation tests.) |
| C1 | MAJOR | CONFIRMED | MAJOR | 344-347 | **Primary text** (Reynolds 1987, extracted locally). Rules: "1. Collision Avoidance: avoid collisions with nearby flockmates", "2. Velocity Matching: … with nearby flockmates", "3. Flock Centering: attempt to stay close to nearby flockmates". It says "'center of the flock' actually means the center of the nearby flockmates" and rejects the "central force model", which causes "all members of a widely scattered flock to simultaneously converge toward the flock's centroid". "Separation", "alignment" and "cohesion" do not occur as rule names (the WebFetch summariser claimed they do; the extracted text refutes it). **Code:** `swarm/control.py:280-281` uses the whole-swarm mean, which is the central-force form. Ch1 l.131 ("vectorised flocking~\cite{reynolds1987}") carries the same citation and needs the same caveat, but that belongs to Ch1. | **Corrected fix.** Drop the reviewer's optional "with five vehicles the whole swarm is every vehicle's neighbourhood": it is an unsourced assumption, and a 5 m-radius circle spans 10 m. Use: "The third term is a global form of the flock-centring and velocity-matching rules of flocking~\cite{reynolds1987}, weighted at 0.15 towards the swarm's centroid and 0.25 towards its mean velocity. Reynolds' rules act on each vehicle's nearby flockmates; this term uses the whole swarm, the central-force form his model avoids, which is acceptable here because the formation slots, not flocking, organise the swarm." At l.346: "its collision-avoidance rule is replaced by the potential field". Raise Ch1 l.131 in issue 06 / Ch1. |
| C2 | MAJOR | CONFIRMED | MAJOR | 390-392 | **Re-run on the real NumpyEnv** (`v12/c2.py`). A forward-Euler subclass (old velocity moves the position) was run through the full `run_trial` protocol, 50 trials per shape. Semi-implicit / explicit: circle FA 1.000/1.000, final error 0.2909/0.2909, median convergence 4.06/4.00 s; line 0.1326/0.1326, 3.26/3.23 s; wedge 0.0721/0.0721, 2.30/2.29 s. The FA series changes 0 times in the second half of every trial under both integrators, so there is no oscillation. The claim "adds energy on every tick" is false for a damped closed loop at these gains: the reviewer's poles are −1 and −2, and the forward-Euler eigenvalues 0.98 and 0.96 are inside the unit circle. The claim is uncited and does not hold for this controller. | **Corrected choice:** take the reviewer's first option and cut the sentence, keeping "The integration is semi-implicit: the velocity is updated first, and the new velocity moves the position." The reviewer's second option asserts "with the gains below the difference is negligible", a result of a run that Ch4 cannot report. The same argument appears in the `NumpyEnv` docstring (`swarm/env.py:75-79`); correcting it there is optional and a code change. |
| C3 | MAJOR | DOWNGRADED | MINOR | 364-365 | The value is already declared "a choice of this work", so the unsourced part is a heuristic rationale, not a literature claim that carries an argument. MINOR (unsupported gloss). **Facts check out.** PyFlyt's default model is `cf2x` (`quadx.py:28`), and `pyflyt_env.py:78-84` passes none. The cf2x collision box is 0.09 × 0.09 m (`models/vehicles/cf2x/cf2x.urdf:34`), and the kinematic backend is a point mass, so "neither backend models an airframe of that size" is true. I did not re-open the PyFlyt paper for the Crazyflie naming. | The reviewer's fix is correct: "The clamp distance of 0.80~m is a choice of this work, twice an assumed airframe span of 0.40~m, so that the clamp acts while there is still space between the airframes; neither backend models an airframe of that size." Naming the vehicle at l.399 ("PyFlyt's Crazyflie~2.x quadrotor model") matches the code default. Confirm the wording against the PyFlyt paper before putting it under `\cite{pyflyt}`. |

## 3. Notes on corrected fixes, and things found in passing

**Fixes corrected, and why**

- **A1.** "Crosses the threshold some frames later" is false at the median of the synthetic test
  abort class (−3 ms). The labelling constrains positives, not firing time. The rewrite states
  exactly that.
- **A3.** The reviewer's wording left out two things: the KeyError path (an error body on
  `/apply-template` or `/tokenize` *is* an interrupted decode) and the fact that the hold is
  published.
- **A7.** The loader's mask is read when the load thread starts, in the loaded phase, not "at the
  start of each run". The recogniser processes are not recorded either.
- **A9.** One of the reviewer's evidence claims is false (`swarm/fsm.py` does import the validator).
  The fix also drops the 5 m / 2 m figures in favour of "inside the envelope".
- **A11.** "(17 were run)" is an outcome and breaks the no-measurement rule. The optimiser (Adam)
  was missing.
- **A12.** "100 tests" is a brittle count. "Every test passes" carries the same fact.
- **C1.** The neighbourhood assumption was dropped. The rewrite names the central-force form
  honestly.
- **C2.** Only the "cut" option is safe. The scoped option reports a result.

**New, unverified by a second pass**

1. **NEW, MINOR (D3).** l.422-423 says each formation "is flown for 12~s", but the PyFlyt run is
   longer and uses the wrong tick length.
   - `_fly` runs `int(round(12/0.02)) = 600` ticks. PyFlyt ticks are 5/240 s (l.409-411), so the
     run lasts 600 × 5/240 = **12.5 s** of simulated time.
   - `PyFlytEnv.step` and the controller's integral still use `dt = 0.02` while the real tick is
     20.83 ms, a 4% mismatch the chapter does not mention (`pyflyt_env.py:92-94`, `:65`).
   - Suggested: "flown for 600 control ticks, 12.5~s of simulated time".
2. **NEW, bears on A4/A5.** Correcting the velocity frame (A5 option a) does not fix the seed-7
   wedge. With world-frame velocity it reaches FA 0.60, a minimum pair of 0.218 m and 10 ticks under
   0.35 m. So A4 stands whichever way A5 is resolved. If A5(a) is applied, all five tests must be
   re-run. Seed 42 line and wedge pass with the patch; circle and the other two tests were not
   re-run.
3. **NEW, MINOR (code, not prose).** `swarm/simulate.py:113-116` runs `separation_clamp` on any
   env, but writes the corrected state back only for `NumpyEnv`. On a non-NumPy env the metrics
   (collisions, minimum pair) would be computed on clamped positions the vehicles never occupied. No
   experiment runs `run_trial` on PyFlyt, so no reported figure is affected.
4. **NEW, for issue 13 (Ch5).** `requirements_summary.tex:15` gives the simulation-backends
   verification as "Hover smoke test on both". The tests in ch4:422-425 are formation tests, plus
   one test that the vehicles do not sink. Given A4, "Passes on both" should be qualified to the one
   placement the tests fly.
5. **NEW, for Ch6.** `sec:limitations` (`ch6_conclusion.tex:66-103`) is undrafted. Its outline
   lacks A4 (seed dependence and no collision measure on physics), A5 (body-frame velocity, if not
   fixed in code) and A10 (speed ceiling not applied at execution). A3's published hold is fail-safe
   and does not need a limitation. The Ch4 fixes point there, so the items must be added.
6. **Cross-chapter, not fixed here.** C1's caveat also applies to Ch1 l.131 (issue 06). A10's
   premise at ch3:193-195 belongs to Ch3 (issue 11). At 3 m/s the 2.35 s interval is 7.05 m, so
   Ch3's conclusion strengthens, but the stated premise is not what the system does.
