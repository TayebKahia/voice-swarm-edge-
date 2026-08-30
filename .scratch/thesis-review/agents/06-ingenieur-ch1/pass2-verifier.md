# Pass-2 verifier -- Ingenieur Ch1 (thesis/ingenieur/ch1_introduction.tex), findings #1-#5

Review only; nothing in the repo was edited. Severity follows docs/agents/thesis-chapter-review.md
Template A section 2 (BLOCKER = contradiction with another chapter or results/, or a claim the
evidence refutes; MAJOR = overclaim, reproducibility gap).

| # | Sev (reviewer) | Verdict | Sev (verified) | Evidence | Corrected fix |
|---|---|---|---|---|---|
| 1 | BLOCKER | CONFIRMED (for the controller; the validator part of the sentence is correct) | BLOCKER | ch3_architecture.tex:68-71 (fsm/ctl/sim nodes in the "Workstation" box), :110-111 ("The flight state machine, the swarm controller and the simulated aircraft run on a workstation"); prd.md:219-225 (Figure 1: WORKSTATION holds the state machine, controller and SwarmEnv); runtime/bus.py:13-15; validator on the Pi: runtime/pipeline.py:200 (`validate(result.raw)` in `PipelineRuntime.process`, before `bus.publish`), ch3 figure puts Validator inside the Pi box. The FSM validates again on the consumer side (swarm/fsm.py:165). | l.44-46: "What that decision puts on the device is the entire perception and language chain. The keyword spotter, the \gls{vad} model, the \gls{stt} model, the language model and the validator all execute on one Raspberry Pi~5 with 8~GB of memory, sharing four Cortex-A76 cores with each other and with the operating system; the flight state machine, the swarm controller and the simulated vehicles run on a workstation joined to the device by a wireless link, so that nothing outside the pipeline contends for those cores (Chapter~\ref{chap:architecture})." l.40-41: "The wireless link from the device to the workstation that runs the state machine, the controller and the simulation belongs to the system: ..." l.61: "The swarm controller, on the workstation, drives a software-in-the-loop simulation of $N = 5$ vehicles at 50~Hz, ..." |
| 2 | MAJOR | CONFIRMED | MAJOR | eval/exp2.py:34-37 ("What this does not measure ... the ROC / operating point: the threshold (0.999) is fixed by `train/train_wake.py` ... and quoted from `results/wake_training.md`"); results/exp2_analysis.md:77 (ambient false accepts 2.33/h quoted from wake_training); results/wake_training.md "False accepts" table (test ambient speech 0.429 h, 1 event); per-class curve: train/train_wake.py:555 (`record["roc"]`). Exp-2 does trial false rejects (exp2_analysis.md cross-trigger matrices, 40 real takes x 2 conditions) and recovery. Its only false-accept observation is 1 trigger on the golden set (exp2_analysis.md:40), which is not the ambient-speech criterion. | l.85-87: "... measures the reflex path both idle and while the parse path is decoding, and trials the keyword spotter's false rejects on the author's recorded keywords and the recovery after a preemption. The spotter's false-accept rate and its per-class curve come from the \emph{keyword-spotter evaluation}, which scores the trained spotter on held-out recordings, including a continuous stream of ambient speech, and fixes the operating point before any test data is scored." l.84: "Three experiments and one evaluation of the keyword spotter, reported in Chapter~\ref{chap:validation}, produce the measurements." l.148 Measured-by: "Keyword-spotter evaluation". The script's EXPERIMENTS map needs the new name added, with its prd row recorded as a known deviation. |
| 3 | MAJOR | CONFIRMED | MAJOR | l.333-335 puts the swarm controller in "the pipeline", so l.107's "no network access at any point in the pipeline" and l.154's "without a network" are false for the as-designed split (ch3:83, :106, :110-111, the figure's "Wi-Fi" edge; prd.md:364, :882). A fully network-free configuration exists only on one host: CommandBus defaults to 127.0.0.1 (runtime/bus.py:95), and the latency experiment ran the bus consumer (Dispatcher + FSM) on loopback on the Pi (eval/exp2.py:32-33, :151-158). No code or plan runs the controller and the simulation on the Pi, and no networking-disabled run is recorded anywhere (no rfkill/nmcli/interface check in eval/ or runtime/; STATE.md has no such entry). | Keep the table rows in prd wording. Append to l.42: "In the requirements below, \emph{network} carries this meaning: a run \emph{with networking disabled} disables every interface to infrastructure outside the system, and leaves only the link between the device and the workstation in place." Add to both table captions: "Offline and networking disabled exclude the device--workstation link (Section~\ref{sec:operational-context})." l.119-120: "... with every interface except the device--workstation link disabled on camera, so that ..." |
| 4 | MAJOR | CONFIRMED. The reviewer's fix is itself inaccurate. | MAJOR | l.210-211 and l.221-223 already say a well-formed, in-range, state-legal wrong command passes every layer. Safe-failure rate from results/table20_end_to_end.md: 0.032 (2/62) clean, 0.015, 0.014, 0.024, 0.039 at 20/15/10/5 dB. The minimum 0.014 and maximum 0.039 are confirmed. ADR-0006 Decision 2 splits the safe failures by origin. The validator also does not reject out-of-envelope values: schema/validate.py:5 ("CLAMP AND LOG, NEVER REJECT"), :62-89, :114-172, and the ch3 scaffold at ch3:266. So a misheard magnitude that *fails* the envelope check is executed at the envelope bound. That is motion. The reviewer's "that fails any check must not become motion" is therefore false as well. | l.217: "The objective is that an error should end in a hold rather than in motion, and how far the design can meet it depends on whether a check can see the error." After l.244: "Two classes of error fall outside that exit. A value outside the physical envelope is clamped to the envelope's bound and executed rather than refused, so the motion it produces is bounded but not withheld; and a command that is well-formed, within the envelope and legal in the current state passes all three layers unchanged. The safe-failure rate (Section~\ref{sec:engineering-requirements}) measures how often errors take the safe exit instead." |
| 5 | MAJOR | CONFIRMED, and stronger than stated | MAJOR | swarm/simulate.py:114-117: the clamp runs after `env.step`, and its corrected state is written back only `if activations and isinstance(env, NumpyEnv)`. swarm/simulate.py:119-126: the collision test runs on the *clamped* positions against `COLLISION_DISTANCE` = 0.35 (swarm/control.py:55), below `CLAMP_DISTANCE` = 0.80 (control.py:50). The code comment says "expected to be zero by construction". swarm/pyflyt_env.py has no `set_state`, and its `positions` reads the physics state (:108-109). On PyFlyt the count is therefore also taken on corrected positions that the aircraft never had. The formation-control experiment ran on the kinematic backend only (eval/exp4.py never builds an env, so `run_trial` defaults to `NumpyEnv`). results/exp4_formation.md:11: closest approach 0.800 m, 432 interventions. | Keep l.307-308 as it is (locked). Insert after l.308: "On the kinematic simulator, where the clamp rewrites position and collisions are counted after it against a distance smaller than the clamp distance, a zero count follows from the clamp's convergence rather than from the controller, and the intervention count is the informative figure; a physics simulator or an airframe exposes no integrator to rewrite, and Chapter~\ref{chap:demonstration} treats that as a limitation." |

## Reasoning per finding

**#1.** I found no reading that saves the sentence. It is in the present tense and describes this
system ("all execute on one Raspberry Pi 5"). Ch3 places the controller on the workstation,
and so do the Figure 1 subgraphs in the prd (lines 219-225) and the bus docstring. Ch3's reason for
the split (ch3:112-117: nothing sharing the Pi's cores may make latency depend on the simulator's
load) is the opposite of what Ch1 says. The "deployed, non-simulated system" reading does not work
either. Nothing in the chapter, the prd or the code says the controller would move to the Pi
in a real deployment, and l.44 presents the placement as a consequence of the offline decision.
That decision does not force it, because the workstation is also local to the site.

The validator is placed correctly. It runs in `PipelineRuntime.process` on the Pi, and the FSM
validates a second time on the consumer side (swarm/fsm.py:165). The error is therefore confined to
"and the swarm controller", together with "the entire chain" at l.44. The sentence also never
names the state machine. l.40-41 and l.61 still read wrongly after the correction: "the link from the device to the vehicles"
and "The controller drives a networked ... simulation" imply that the controller sits on the
device side of the link.

One nuance belongs to Ch5, not Ch1. In the latency experiment the Dispatcher and the FSM ran on
the Pi over loopback (eval/exp2.py:32-33). Ch5 must say that the measured "FSM applied" end point
is on the Pi. This does not rescue Ch1, which makes a design statement.

**#2.** The finding holds. The docstring of eval/exp2.py excludes the ROC and the operating
point. The only false-accept figure on ambient speech (2.33/h over 0.429 h) comes from
`train/train_wake.py` and is written up in results/wake_training.md. l.176-177 promises "the full
per-class curve with the chosen threshold marked", and that curve also lives in the wake-training
record (`record["roc"]`), not in the latency experiment. The latency experiment legitimately
measures false rejects on the author's voice on the Pi. The keyword false-rejects row stays
"Latency experiment", although the held-out and real-voice evaluations (results/wake_real_voice.md)
also report false-reject rates.

On the prd: Table 12 row NFR-15 (prd.md:543), the note at prd.md:551 ("selected from the measured
ROC in Exp-2") and D18 (prd.md:775) record the *plan*. The implementation moved ROC selection into
training on hardware-independent scores, which was the right call because the threshold must be
fixed before the test data is scored. The prd is out of date on this point; the thesis should
follow the as-built attribution. The review script compares the Measured-by cell with prd through
`EXPERIMENTS` (tools/review/ingenieur_ch1.py:48-53), so the change will produce a FAIL. The fix is
to extend that map with a documented deviation, not to keep a wrong cell.

Issue 00's 2026-09-24 amendment requires each named experiment or evaluation to be described in
one sentence where it is first named. The corrected l.85-87 text does that.

**#3.** Confirmed. Only one configuration makes "networking disabled" literally true while the
system still works: the pipeline, the bus consumer, the controller and the simulation all on the
Pi over loopback. The bus supports it (default host 127.0.0.1), and the latency experiment used the
loopback half of it. Nothing in the repo runs the controller or the simulation on the Pi, and
Ch3's placement argument forbids it. No networking-disabled run has been performed or scripted.
IMPLEMENTATION_ROADMAP Part 9 still lists it as unchecked.

The new paragraph at l.39-42 defines *offline*, but it does not reach the words the table rows
use: "no network access at any point in the pipeline" (l.107), "networking disabled on camera"
(l.111, l.119) and "without a network" (l.154). Read with l.333-335, these still say the
controller is cut off. The first-pass decision to keep prd wording in the rows is respected by
defining *network* and *networking disabled* in the prose and repeating that in the captions. The
prose at l.119 is not a table row and can be corrected directly.

Separately, and not a Ch1 fault: the verification method "end-to-end run with networking disabled"
has not been executed. Ch5 or Ch6 will have to report it as not done, or do it.

**#4.** l.217 sits directly after "The design objective that follows is ...", so it can be read
as an objective. As worded, though, it is an absolute prohibition, and the paragraph's own l.210-211
and l.221-223 concede that the design cannot enforce it. l.236 ("a safety mechanism rather than a
filter") and l.243-244 ("no rejection path ... can produce motion") then read as covering all
errors. The measured safe-failure rate (0.014 to 0.039 across SNR; 60 of 62 clean failures
dispatched a non-safe command) shows that the residual class is the common case. Ch1 must not
quote that figure, but it must stop promising the opposite.

Verification adds a point the reviewer missed. The validator clamps out-of-envelope values instead
of rejecting them (schema/validate.py:5), so a misheard altitude of fifty metres flies at 15 m. The
reviewer's "that fails any check must not become motion" is therefore false for the envelope
check. The corrected fix names both escaping classes: clamped out-of-envelope values and
undetectable wrong commands. l.243-244 remains true only because a clamp is not a rejection.

A related MINOR for the lead reviewer to consider: l.236 says a rejection never becomes a
"substituted or best-guess movement", yet a clamped value is arguably a substituted magnitude. The
corrected text above makes that explicit instead of leaving it for an examiner to find.

**#5.** The code path confirms the finding and extends it. On the kinematic backend,
`separation_clamp` projects positions apart until convergence (up to 64 sweeps). The result is
written back into the integrator, and collisions are then counted on those positions against
0.35 m. The count can be non-zero only if the clamp fails to converge. The recorded minimum of
exactly 0.800 m shows that it always converged. On PyFlyt the corrected positions are not written
back, yet the collision test still uses them, not `env.positions`. On that backend the metric
describes a corrected view, not the aircraft.

The chapter's framing at l.307-313 contrasts "a statement about the trials" with "a proof over the
reachable set", which implies the zero could have come out otherwise. On this backend it holds by
construction, conditional only on the clamp converging. The locked wording is accurate. The
misleading part is the surrounding contrast, together with the unstated scope of "at the point
where position is actually updated", which can only be done where the software owns the
integrator.

The one-sentence insertion after l.308 keeps the locked phrase, states the scope, and turns
l.315-319 (the intervention count) into the figure that carries the argument, which it already is.

## Live-demonstration check

No live-microphone path exists:
- `runtime/audio.py` is absent (pipeline.py:20-21: "Microphone capture (Table 4's `runtime/audio.py`) is not built yet").
- `runtime/main.py` is absent, so `run_pipeline.sh` exits at its pre-flight check with "MISSING: runtime/main.py".
- `runtime/stream.py` has only `WavSource`.
- No code connects the bus consumer (Dispatcher/FSM) to `swarm.control.SwarmController` or to an env. Only eval/exp4.py imports the controller, and it drives formations directly. The "networked software-in-the-loop" chain of l.61 has therefore never carried a command.

STATE.md records live capture as a declared cut:
- STATE.md:1581 ("Block A experiments are done except the declared cuts (A11 live capture, H2, A9)").
- STATE.md:1550 ("Not measured: ... live capture latency (A11)").
- STATE.md:1350 ("Still not built: `runtime/audio.py` (live mic)").
- The demo video planned for Mon 21 (STATE.md:40) is not recorded as done.

If the live demonstration does not happen, these Ch1 sentences are false as statements of fact.
Requirement rows are targets and would become unmet requirements, which Ch6 must report.
- l.38-39: "verified by an end-to-end run with networking disabled"
- l.65-66: "and the demonstration runs from a live microphone"
- l.117-120: "the demonstration is performed from a live microphone with networking disabled on camera, so that offline operation is exercised rather than asserted"
- l.396-398: "... a swarm controller with two interchangeable simulation backends and a live demonstration are the substance of the chapters that follow"
- l.420-421: "Chapter~\ref{chap:demonstration} presents the live demonstration"
- l.111 (Live demonstration row) and l.107/l.154 (verification "End-to-end run with networking disabled"): targets, not false, but unmet.
- l.61 and l.55-57 describe a pipeline-to-controller chain that exists in design only. They are acceptable as design statements, but Ch4 and Ch5 must not report that chain as exercised.
