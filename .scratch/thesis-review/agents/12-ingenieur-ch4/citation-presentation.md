# Citation / presentation review: thesis/ingenieur/ch4_implementation.tex (Ingénieur Ch4)

Reviewed state: the working-tree file of 2026-09-24, 432 lines, as matched by the pre-review report
(`.scratch/thesis-review/reports/ingenieur_ch4.md`, 1 FAIL / 15 WARN / 197 PASS). Line numbers are for
this state. Dimensions covered: D5, D7, D8, D9, D11, D12. D1/D2/D4/D6/D10 belong to the argument agent,
and D3 to the script. Where a finding touches an argument dimension, the overlap is marked and the finding
is limited to the presentation side.

## 1. Verdict

Ready after fixes. The chapter builds cleanly from scratch: 0 errors, 0 undefined references or citations,
0 overfull boxes. It carries no project-internal vocabulary, and every `\ref` to a Ch1/Ch3 table or
`fig:architecture` points at an element that says what Ch4 attributes to it. Two criterion attributions are
partial (MINOR). Seven of the eight citation uses are fully supported by their primary sources. There is no
BLOCKER. There are three MAJOR findings, all under D5:

- `reynolds1987` supports "flocking" only partly. Reynolds' rules act on *nearby* flockmates, and the paper
  rejects the whole-flock centroid model, which is the one the code implements.
- "Explicit integration adds energy on every tick ... could be mistaken for [an under-damped gain]" has no
  source. A check with the chapter's own gains finds no such effect.
- "roughly twice the rotor-tip diameter of a small quadrotor" has no source and no number, and it is not
  tied to either simulated vehicle. The physics backend flies PyFlyt's Crazyflie 2.x model, which the chapter
  never names.

## 2. Scorecard

| Dim | Result |
|---|---|
| D5 References | ISSUES (12): 3 MAJOR, 7 MINOR, 2 NIT |
| D7 Figures and tables (references to Ch1/Ch3 floats) | ISSUES (2): 2 MINOR. The chapter has no float of its own |
| D8 Language and style | ISSUES (10): 3 MINOR, 7 NIT (finding 5 counts under D7, finding 12 under D5) |
| D9 LaTeX and build | ISSUES (1 NIT row, two items): clean build, 0 errors, 0 Overfull |
| D11 Self-containment | ISSUES (2, NIT only): no project-internal reference, no undefined code, no file path in prose |
| D12 Headings and register | ISSUES (7): 1 MINOR, 6 NIT |

Totals: 34 findings, of which 0 BLOCKER, 3 MAJOR, 13 MINOR and 18 NIT. Some rows count under two dimensions, so the per-dimension
counts add up to more than these totals.

## 3. Findings

"Deferred class (issue 11)" marks sentence-length and register NITs. Issue 11 decided to leave that class
to the final whole-document language pass. They are listed here so that the pass has them.

| # | Sev | Dim | file:line | Quoted text | Problem | Evidence | Proposed fix |
|---|---|---|---|---|---|---|---|
| 1 | MAJOR | D5b | ch4_implementation.tex:344-347 | "The third is the cohesion and alignment of flocking~\cite{reynolds1987}, weighted at 0.15 towards the swarm's centroid and 0.25 towards its mean velocity." | PARTIAL support. (a) Reynolds' rules are "Velocity Matching" and "Flock Centering", and both act on *nearby flockmates*. The implementation steers every vehicle towards the centroid and mean velocity of the *whole* swarm. That is the central-force model the paper explicitly rejects. (b) "cohesion and alignment" and the "separation rule" (l.346) are not the 1987 paper's terms: its rule 1 is "Collision Avoidance". (c) Ch1 l.131 uses the same key for "vectorised flocking", so the same caveat applies there. | Reynolds 1987 (red3d.com/cwr/papers/1987/SIGGRAPH87.pdf), "Simulated Flocks": "2. Velocity Matching: attempt to match velocity with nearby flockmates"; "3. Flock Centering: attempt to stay close to nearby flockmates". The same section rejects the central force model, which it calls "just plain wrong". Code: `swarm/control.py:280-281` `positions.mean(axis=0) - positions`, `velocities.mean(axis=0) - velocities`, over all vehicles. | "The third term is a global form of the flock-centring and velocity-matching rules of flocking~\cite{reynolds1987}: where Reynolds' rules act on each vehicle's nearby flockmates, this term uses the centroid and mean velocity of the whole swarm, weighted at 0.15 and 0.25. With five vehicles the whole swarm is every vehicle's neighbourhood." Keep the last clause only if the author accepts it as a design assumption. At l.346, write "its collision-avoidance rule is replaced by the potential field". |
| 2 | MAJOR | D5c | ch4_implementation.tex:390-392 | "Explicit integration adds energy on every tick, and in a formation controller that energy appears as a slow oscillation about the slot, which resembles an under-damped gain and could be mistaken for one." | A numerical-analysis claim with no citation, stated as an absolute ("on every tick"). The part about "a formation controller" is not borne out for this controller at this tick. Explicit Euler adds energy only to an *undamped* oscillator. With $k_d = 3.0$, the closed-loop poles are real and the tick is 20 ms, and the two integrators then behave almost identically. references.bib has no numerical-methods entry. | My check: a 1-D point mass under the chapter's PID law ($k_p = 2.0$, $k_i = 0.05$, $k_d = 3.0$, 4 m/s² and 3 m/s limits, $h = 0.02$ s), starting 5 m from its slot. Explicit Euler gives an overshoot of −0.0470 m and 1 zero crossing. Semi-implicit Euler gives −0.0469 m and 1 zero crossing. An undamped oscillator under explicit Euler gains 4.1 % energy in 50 ticks. The linearised error dynamics $s^2 + 3s + 2$ have poles −1 and −2, so the forward-Euler map has eigenvalues 0.98 and 0.96: real and inside the unit circle. | Either cut the sentence and keep "The integration is semi-implicit: the velocity is updated first, and the new velocity moves the position", or scope it as a design choice: "Semi-implicit integration is used because explicit (forward) Euler integration adds energy to an undamped oscillator at every step; with the gains below the difference is negligible, and the choice removes the integrator as a possible source of oscillation." |
| 3 | MAJOR | D5c | ch4_implementation.tex:364-365 | "The clamp distance of 0.80~m is a choice of this work: roughly twice the rotor-tip diameter of a small quadrotor, so that the clamp acts while there is still space between the airframes." | A factual claim about airframe size with no source and no number. It implies a tip-to-tip span of about 0.4 m, but the text never says which quadrotor it means. The physics backend flies PyFlyt's default QuadX, the Crazyflie 2.x model, and the chapter does not name it. The kinematic backend has no airframe at all. The code comment it paraphrases says the value was "Not given by the PRD". | `swarm/control.py:46-50` ("Chosen as roughly twice the rotor-tip diameter of a small quadrotor ... Not given by the PRD"). PyFlyt `core/drones/quadx.py:29` `drone_model: str = "cf2x"`, and `swarm/pyflyt_env.py:78-84` passes no model. PyFlyt paper §QuadX: "The first is the model of a Bitcraze Crazyflie 2.x". references.bib has no airframe specification. | Give the assumption as a number and call it an assumption: "The clamp distance of 0.80~m is a choice of this work, twice an assumed airframe span of 0.40~m, so that the clamp acts while there is still space between the airframes; neither backend models an airframe of that size." Also name the physics backend's vehicle model at l.399 ("PyFlyt's Crazyflie~2.x quadrotor model~\cite{pyflyt}"). The paper supports that naming. |
| 4 | MINOR | D7e | ch4_implementation.tex:415-417, 422-425 | "That is the condition the simulation-backends criterion rests on (Table~\ref{tab:functional-requirements})." | Only partly what the table says. The criterion reads "Two interchangeable simulation backends sit behind one environment interface", and its verification is "Both pass a hover smoke test". The table never mentions the same controller or the same gains. Ch4 then lists five tests and never says which one is the hover smoke test the criterion names. A reader cannot tell whether the criterion's own verification was run. | ch1_introduction.tex:132. The "hover smoke test" appears nowhere else in the Ingénieur (grep `smoke`: only Ch1 l.132 and a comment in Ch6). | "The simulation-backends criterion asks for two interchangeable backends behind one interface, verified by a hover smoke test (Table~\ref{tab:functional-requirements}); interchangeable here means that the same controller, with the same gains, runs under both." In l.423-425, name the test that serves as the hover smoke test, e.g. "a line formation held on a station-keeping command must not sink, which is the hover smoke test of the criterion". |
| 5 | MINOR | D7e / D8 terminology | ch4_implementation.tex:365-367 | "A collision, in the collision criterion, is a pair closer than 0.35~m" | Attributes to the criterion a definition that the criterion does not contain. Ch1's row is "Collisions: Inter-drone collisions", with no distance. The name also drifts: Ch1 has "Collisions" in the table and "The collisions criterion" in its prose (l.213), while Ch4 writes "the collision criterion" at l.366, 371 and 431. | ch1_introduction.tex:163, 213; `grep -n '0\.35' thesis/ingenieur/*.tex` finds this line only (apart from the VAD threshold). | "A collision, as the formation-control experiment counts it for the collisions criterion, is a pair closer than 0.35~m". Use "collisions criterion" at l.371 and 431 as well. |
| 6 | MINOR | D8e | ch4_implementation.tex:216 | "it is sent as one UDP datagram" | Acronym typed by hand. The key `udp` exists in shared/acronyms.tex, and its first use is in Ch3. | shared/acronyms.tex:`\newacronym{udp}{UDP}{User Datagram Protocol}`; script WARN l.216. | `\gls{udp}`. |
| 7 | MINOR | D8e | ch4_implementation.tex:74-75, 116 | "on ONNX Runtime directly"; "written into an ONNX graph directly" | ONNX is an acronym with no key and no expansion anywhere in the Ingénieur. It appears only in this chapter, and not in the Master. | `grep -rn ONNX thesis/`: only these two lines. onnx-1.17.0 METADATA: "Summary: Open Neural Network Exchange". | Add `\newacronym{onnx}{ONNX}{Open Neural Network Exchange}` and write "\gls{onnx} Runtime" and "an \gls{onnx} graph". The long form is a proper noun, so it keeps its capitals. |
| 8 | MINOR | D5d | ch4_implementation.tex:74-75, 115-116 | "on ONNX Runtime directly"; "the heads are fitted with scikit-learn" | Two tools the deployed and training stack actually uses are named with no `\cite`. references.bib (74 entries) has no entry for either. Under SKILL §4, adding one is the author's job. | `grep -in 'onnx\|scikit\|sklearn' thesis/references.bib`: no hit. Installed: onnxruntime 1.29.0 and scikit-learn 1.9.0 in `pfe_swarm`. | Either the author adds entries for ONNX Runtime and scikit-learn, verified against their primary pages with version and url, or the house style records that software named only as an implementation vehicle is not cited. Apply the same rule to the Linux affinity call at l.191. The man page confirms that claim ("A child created via fork(2) inherits its parent's CPU affinity mask. The affinity mask is preserved across an execve(2).") |
| 9 | MINOR | D5c | ch4_implementation.tex:114-115 | "The upstream trainer requires PyTorch, which is kept out of this project's environment" | A claim about openWakeWord with no citation on the sentence. It is true, but only the source code supports it. The README does not state it. | openwakeword 0.6.0 `train.py:1-2` `import torch` / `from torch import optim, nn`. The README passages on architecture and training (fetched) do not mention PyTorch. `torch` is not installed in `pfe_swarm`, which confirms the second clause. | "The upstream trainer~\cite{oww} is written in PyTorch, which is kept out of this project's environment". |
| 10 | MINOR | D5f | ch4_implementation.tex:83-86 | "the gap of 0.15 between the two thresholds is Silero's own hysteresis"; "in place of Silero's default of 30~ms" | Two claims about Silero's defaults, three sentences after the only `\cite{silero}` (l.74). Both are correct, but the source is the package code, not the README. | silero_vad 6.2.1 `utils_vad.py:272` "neg_threshold: float (default = threshold - 0.15)", `:342-343` `neg_threshold = max(threshold - 0.15, 0.01)`, `:219` `speech_pad_ms: int = 30`. | Attach the key to the claim: "is the hysteresis of Silero's reference implementation~\cite{silero}"; "in place of that implementation's default of 30~ms". |
| 11 | MINOR | D5c | ch4_implementation.tex:171-174 | "without an assumption that caching leaves the decoded command unchanged; that assumption was not tested" | The cited server's own documentation states the risk the parity argument relies on. The sentence could cite it and does not, so the rationale reads as the author's conjecture. | llama.cpp `tools/server/README.md`, `/completion` `cache_prompt`: "Re-use KV cache from a previous request if possible ... enabling this option can cause nondeterministic results. Default: `true`". | "... without an assumption that caching leaves the decoded command unchanged, which the server's documentation does not guarantee~\cite{llamacpp}; the effect of the cache on this parser was not tested." |
| 12 | MINOR | D5c / D8a | ch4_implementation.tex:328-330 | "A greedy assignment, each vehicle to its nearest free slot, routinely produces crossing paths" | A general claim about assignment algorithms with no source, and "routinely" is a vague frequency. The chapter also never names the algorithm it uses to minimise the total squared distance. | references.bib has no assignment-problem entry. The code uses the Hungarian method (script PASS "assign_slots: Hungarian on squared distance"). | "A greedy assignment, each vehicle to its nearest free slot, can produce crossing paths, which sends two vehicles through the same volume; the minimum-total-squared-distance assignment is computed with the Hungarian method." Cite it only if the author adds an entry. |
| 13 | MINOR | D5b precision | ch4_implementation.tex:403 | "that velocity is sent to PyFlyt as a world-frame setpoint, which PyFlyt's inner loops then track; yaw is not commanded." | The PyFlyt mode used (mode 6) always carries a yaw-*rate* setpoint, and the backend sets it to zero. So yaw rate is commanded, as zero. PyFlyt supports the rest of the sentence. | PyFlyt `core/drones/quadx.py:244` "6: vx, vy, vr, vz", `:252` "vx, vy, vz = ground linear velocities"; paper §QuadX: "Linear velocity control and yaw rate"; script PASS "yaw-rate setpoint 0". | "...; the yaw-rate setpoint is held at zero." |
| 14 | MINOR | D5c | ch4_implementation.tex:337-338 | "The value of $k_d$ is slightly above critical damping for $k_p$, which is $2\sqrt{k_p} \approx 2.83$." | Correct only under assumptions the text does not state: unit mass, PD error dynamics $\ddot e + k_d \dot e + k_p e = 0$, with the integral, potential-field and flocking terms ignored. "Slightly" is a vague qualifier where the ratio is available. | $2\sqrt{2} = 2.828$; $\zeta = 3.0/2.828 = 1.06$. | "For the error dynamics of a unit point mass under the proportional and derivative terms alone, $\ddot e + k_d \dot e + k_p e = 0$, critical damping is $k_d = 2\sqrt{k_p} \approx 2.83$; $k_d = 3.0$ gives a damping ratio of 1.06." |
| 15 | MINOR | D8b / D12c (D4a overlap) | ch4_implementation.tex:418-421 | "the physics backend is what shows that those results describe a controller that also flies against rigid-body dynamics. A controller retuned for each backend would prove nothing" | "shows" is on SKILL's avoid-list, and "would prove nothing" is an absolute plus a rhetorical flourish (script WARN l.418, l.420). The strength of the claim is the argument agent's question. Only the wording is reported here. | SKILL §2 "Scholarly verb choices", "No unearned absolutes", "Register". | "The formation-control results come from the kinematic backend alone; the physics backend tests whether the same controller also flies against rigid-body dynamics. If the gains were retuned for each backend, the kinematic results would describe a controller that runs nowhere else, and a success on the physics backend would describe a different controller." |
| 16 | MINOR | D12a | ch4_implementation.tex:415 | `\paragraph{One controller, one set of gains.}` | A slogan that asserts the paragraph's finding (no per-backend tuning), not a noun phrase naming its topic. The same class as issue 11's "What pinning cannot isolate." | SKILL §2 "Headings": "The finding goes in the paragraph's first sentence (Assertion), not in the heading." | `\paragraph{Controller parity across backends.}` |
| 17 | NIT | D5d | ch4_implementation.tex:341-344 | "The second term is an artificial potential field that repels each pair of vehicles closer than 1.5~m" | A named method used here without a cite. Ch1 l.329-332 introduces it with `\cite{koren1991}`, so the chapter is not unsourced overall. | ch1_introduction.tex:332. | Optional: "an artificial potential field~\cite{koren1991}". The cite carries the method only, not the $6.0\,(1/d - 1/d_0)/d^2$ form (see UNVERIFIED 1). |
| 18 | NIT | D5e | references.bib `piper`, `silero` | `title = {{Piper}: A Fast, Local Neural Text-to-Speech System}`; `title = {{Silero VAD}: Pre-trained Enterprise-Grade Voice Activity Detector}` | Both titles are paraphrases. Piper's repository gives "A fast and local neural text-to-speech engine that embeds espeak-ng for phonemization". Silero's own citation block gives the longer title below. The years are now correct: `silero` 2024 has been added since issue 11, and `piper` 2026 matches v1.8.0. | piper1-gpl README (fetched); GitHub API: v1.8.0 published 2026-09-04. silero-vad README "Citations": "Silero VAD: pre-trained enterprise-grade Voice Activity Detector (VAD), Number Detector and Language Classifier", 2024. | Author's decision (SKILL §4; issue 11 left `silero` to the author). Keep the short titles knowingly, or copy the primary pages' wording. |
| 19 | NIT | D8a | ch4_implementation.tex:217 | "The largest command of the schema is far shorter" | A vague qualifier where the exact size is computable. | SKILL §2 "Quantitative specificity". | "The largest command of the schema serialises to N bytes". The author computes N from `schema/schema.py`. |
| 20 | NIT | D8a (argument WARN overlap) | ch4_implementation.tex:96, 395, 407, 409, 411 | "about two seconds"; "in under a second"; "a small steady error in altitude"; "within about two seconds"; "at about the speed of simulated time" | Vague qualifiers. l.96 has an exact value: 1.98 s, `train_wake.py` WINDOW_S. The other four are timing observations in a chapter that promises "every figure ... is a parameter" (script WARNs; the argument agent judges whether they belong). | Script PASS l.96 (1.98); WARN l.395, 408, 411. | l.96: "which span 1.98~s of audio". For the rest, either give the observed figure with its source, or drop the magnitude ("descends to the ground"; "slower than the kinematic backend"). |
| 21 | NIT | D8b | ch4_implementation.tex:153 | "rather than handled as a separate case" | "handle" is on SKILL's avoid-list. | SKILL §2. | "rather than treated as a separate case". |
| 22 | NIT | D8g, deferred class (issue 11) | ch4_implementation.tex: 63, 68, 81, 86, 118, 129, 157, 162, 171, 198, 251, 268, 291, 298, 324, 335, 406, 422 | (see §3a) | 18 sentences exceed about 40 words. | Word counts in §3a. | Split the longest at their colon or semicolon: l.68 (56), l.129 (54), l.157 (54), l.422 (53), l.162 (52), l.324 (52). |
| 23 | NIT | D8 terminology | ch4_implementation.tex:128-129, 270 | "the false-accept and false-reject criteria"; "every drone is on the ground" | Criterion names differ from Ch1's: "Keyword false accepts" / "Keyword false rejects", and Ch1 prose says "the two keyword criteria". "drone" appears only at l.270, while the chapter's term elsewhere is "vehicle". | ch1_introduction.tex:159-160, 191. | "the keyword false-accept and false-reject criteria"; "every vehicle is on the ground and ... nearly at rest". |
| 24 | NIT | D8e | ch4_implementation.tex:200 | "in the \gls{gguf} format" | This is the first `\gls{gguf}` in the document. It prints "GGML Universal File (GGUF)", and GGML is never expanded in the Ingénieur. | PDF p.36: "quantised to Q4_K_M in the GGML Universal File (GGUF) format"; `grep ggml thesis/ingenieur/`: no hit. | Accept it, since GGML is a name, or change the shared long form (a both-document decision): "GGML Universal File, the weight format of \texttt{llama.cpp}". |
| 25 | NIT | D9 typography | ch4_implementation.tex:199; ch4_implementation.tex:216 | "Qwen2.5-0.5B"; "4{,}096 bytes" | The model name breaks at its hyphen across lines in the PDF (p.36: "Qwen2.5-" / "0.5B"). The unit "bytes" has no `~`. | `pdftotext -layout -f 35 -l 37`: lines 133-134. SKILL §4.3 "Use `~` for units". | `\mbox{Qwen2.5-0.5B}`; `4{,}096~bytes`. |
| 26 | NIT | D8 wording | ch4_implementation.tex:41 | "every figure in this chapter is a parameter of the code, not a measurement" | "figure" is ambiguous in a chapter that has no Figure float, and the thesis also uses "figure" for numbers. | Ch4 has 0 floats. | "every number in this chapter is a parameter of the code, not a measurement". |
| 27 | NIT | D11b | ch4_implementation.tex:161, 205, 300 | "the harness that measures the parser's accuracy"; "assembled only by the harness of the latency experiment"; "the harness itself places each trial's state machine in \texttt{FLYING}" | "harness" is standard software-testing vocabulary, not project-management vocabulary, and Ch1 l.443 already uses "quantised-inference harness". It is never glossed for the latency experiment, though. A reader who holds only the thesis may not know that it means the experiment's driver program. | ch1_introduction.tex:443. | At l.205, first use for the latency experiment: "by the program that runs the latency experiment (its harness), which builds them for its trials". Keep "harness" after that. |
| 28 | NIT | D11d / D6b (typography) | ch4_implementation.tex:198 | `\paragraph{Artefacts from the M\'emoire de Master.}` | The document name appears in a heading without `\emph`, while the prose always italicises it. | SKILL §4.1 "always say 'the \emph{Mémoire de Master}'". | `\paragraph{Artefacts from the \emph{M\'emoire de Master}.}` |
| 29 | NIT | D12a | ch4_implementation.tex:57 | `\paragraph{One stream, two consumers.}` | A noun phrase, but written as a slogan that encodes the design point. The paragraph covers the frame loop, the queue, the worker and timestamping. | SKILL §2 "Headings". | `\paragraph{Frame loop and worker.}` |
| 30 | NIT | D12a | ch4_implementation.tex:241 | `\paragraph{Transport as run.}` | Elliptical: the reader must infer "as run in the experiments". | SKILL §2 "Headings". | `\paragraph{Transport in the experiments.}` |
| 31 | NIT | D12a | ch4_implementation.tex:286 | `\paragraph{Legality of the original intent.}` | A valid noun phrase, but opaque until the paragraph is read. The topic is the validator's substitution and a defect it exposes. | SKILL §2 "Headings". | `\paragraph{Substituted commands and legality.}` Optional. |
| 32 | NIT | D12c, deferred class (issue 11) | ch4_implementation.tex:351 | "The potential field is a force, and a force can be outrun" | A figurative aphorism. | SKILL §2 "Register". | "The potential field acts through the acceleration, and a bounded acceleration cannot always stop a pair in time: with a finite timestep, there is a closing speed from which ..." |
| 33 | NIT | D12c, deferred class (issue 11) | ch4_implementation.tex:384 | "The two backends exist because speed and fidelity are different needs, and neither backend serves both." | An aphorism. | SKILL §2 "Register". | "The kinematic backend is fast enough for the formation-control sweep and the physics backend models rotor and rigid-body dynamics; neither provides both." |
| 34 | NIT | D12c, deferred class (issue 11) | ch4_implementation.tex:125-126, 283-284 | "That weighting was introduced after a first fit whose false accepts on the validation split were all near-misses"; "Before the tests were accepted, three faults were introduced into the state machine in turn" | Both passages narrate the history of the work ("describe the work, not the working"). The first discloses a procedural fact that must stay (issue 12 seeded point), so only its phrasing is in question. | SKILL §2 "Describe the work, not the working". | "The weighting was chosen after the validation false accepts of an unweighted fit were found to be all near-misses; the held-out test split was therefore scored for both fits." "The tests were checked by fault injection: each of three faults introduced into the state machine in turn makes at least one test fail." |

### 3a. Sentences over about 40 words (D8g)

Counts are approximate: `\ref`, `\cite` and `\gls` count as one token each, and heading words are excluded.

| line | words | opening |
|---|---|---|
| 63 | ~42 | "For every frame the loop records how late it picked the frame up ..." |
| 68 | ~56 | "The endpointer reports $T_0$ in stream time, as the last sample ..." |
| 81 | ~49 | "It ends once the probability has stayed below 0.35 ..." |
| 86 | ~46 | "The padding costs no waiting time: both pads are taken ..." |
| 118 | ~43 | "Training windows are labelled by where the phrase falls ..." |
| 129 | ~54 | "It is the highest value on a grid, from 0.05 to 0.99 ..." |
| 157 | ~54 | "Each parse makes three requests to it: ..." |
| 162 | ~52 | "Prefill and decode times are read from the server's own timing report ..." |
| 171 | ~45 | "The \emph{M\'emoire de Master} scores the deployed parser with the cache disabled ..." |
| 198 | ~50 | "Three artefacts of the parse path are produced by the \emph{M\'emoire de Master} ..." |
| 251 | ~43 | "Its five states, its transitions and the legality of each intent ..." |
| 268 | ~44 | "The reset out of \texttt{ABORTED} is also an operation rather than a command ..." |
| 291 | ~43 | "A command that has not been validated and is handed to the state machine directly ..." |
| 298 | ~48 | "Outside its tests, the only code that runs it is the consumer of the latency experiment ..." |
| 324 | ~52 | "It is then re-centred on its own centroid: ..." |
| 335 | ~43 | "The first is a \gls{pid} law on the error between each vehicle and its slot ..." |
| 406 | ~49 | "PyFlyt's inner loop leaves a small steady error in altitude ..." |
| 422 | ~53 | "Each of the three formations is flown for 12~s and must end with ..." |

### 3b. Checked and clean

- **D5a.** All 8 keys resolve (`check_tex.py`: 8 cites, 74 bibitems, no dangling `\cite`).
- **D5e.** Every cited entry carries a url, eprint or doi. Years checked against the primary pages:
  - whispercpp 2026: commit 52a939a, 2026-09-04.
  - llamacpp 2026: b10863, published 2026-09-08. The issue-11 gap is closed.
  - silero 2024: the README citation block gives 2024. The issue-11 gap is closed.
  - pytorch: arXiv 1912.01703 title, 21 authors and "NeurIPS 2019" match.
  - oww 2024 / v0.6.0: README "v0.6.0 ... released 2024/02/11".
  - piper 2026 / 1.8.0: release 2026-09-04.
  - reynolds1987: Crossref gives "Flocks, herds and schools: A distributed behavioral model", ACM SIGGRAPH
    Computer Graphics 21(4) 25-34, 1987. This matches the entry. The author's own PDF has a serial comma.
  - pyflyt: arXiv title and six authors match.
- **D5f.** Every `\cite` sits on the noun it identifies. None is dumped at a paragraph end. The one
  placement gap is finding 10.
- **D8d.** British spelling is consistent (quantisation, tokenises, centre, behaviour, metres, artefacts).
  No -ize/-yze/-or forms.
- **D8f.** No non-ASCII characters.
- **D8c (tense).** Built structure is described in the present. Procedures carried out during training
  and testing are in the past: "was introduced", "was scored", "selected", "were introduced". Both uses
  are consistent within their kind.
- **D8e.** `vad`, `tts`, `gguf`, `json`, `pid` all use `\gls`:
  - The first `\gls{tts}` and `\gls{gguf}` in the document are in this chapter and expand correctly (PDF
    p.34: "text-to-speech (TTS)").
  - `pid` was first used in Ch1 through `\acrlong`/`\acrshort` + `\glsunset`, so l.335 prints "PID".
  - `vad` and `json` were first used in Ch1/Ch3.
  - "key--value cache" is written out, not a hand-typed "KV". "mel spectrogram", "multilayer perceptron"
    and "rectified linear units" are written out and carry no acronym. The only hand-typed acronyms are
    UDP and ONNX (findings 6, 7).
- **D9b.** No `\TODO`, `\CHECK` or `\figtodo`.
- **D9c.** The labels are `chap:implementation`, `sec:audio-chain`, `sec:runtime`, `sec:command-bus`,
  `sec:state-machine`, `sec:swarm-controller` and `sec:simulation-backends`. All follow the pattern, and
  all are `\ref`'d from other chapters (6/5/5/4/3/7/5 times). Every `\ref` in other chapters resolves to a
  label that exists.
- **D9d.** `~` is present before every `\cite` and `\ref`, and before every SI unit (ms, s, kHz, Hz, m,
  m/s, m/s²). Counts ("512 samples", "96 tokens") are nouns, not units. The exception is "bytes"
  (finding 25).
- **D11a/b/c.** No prd, spike, gate, sprint, session, D-number, ADR, Branch A/B, NFR-/FR-, RQ or Exp-.
  No undefined codes: $T_0$ is defined in Ch3, and $k_p$, $k_i$, $k_d$, $d$, $d_0$ are defined inline. No
  file or module name in prose; the `\texttt` items are tool names (`whisper.cpp`, `tiny.en`,
  `llama-server`), intents and states defined in Ch3. PyFlyt's mode numbers (6, 7) are kept out of the
  prose.
- **D12b.** Sections are in sentence case, and `\paragraph` lead-ins are in sentence case with a final
  period. This is consistent with every other chapter.

## 4. Cross-chapter float references (D7)

| Ch4 line | Reference | What Ch4 attributes to it | What the float says | Verdict |
|---|---|---|---|---|
| 58 | tab:core-allocation | frame loop pinned to core 0 | Row 0: "Audio frame loop: frame buffering, the endpointer, the keyword spotter and the reflex path's publication" | Agrees |
| 64-65 | tab:core-allocation | "the core-0 constraint", judged by the per-frame lag and compute time | Row 0 constraint: "The work for one 80~ms frame completes within 80~ms, on every frame" | Agrees. The compute time tests the constraint directly, and the lag tests falling behind. |
| 129 | tab:nonfunctional-requirements | the false-accept and false-reject criteria describe one operating point | Caption: "The two keyword criteria are one operating point on one curve" | Agrees (name drift, finding 23) |
| 131-132 | tab:nonfunctional-requirements (implicit, "the budget of 0.10") | FR budget 0.10 | "Keyword false rejects ... $\leq$ 0.10" | Agrees |
| 146 | tab:stage-budget | per-stage figures reported against the budget | Parse rows: recognition, prefill, decode, validation/state machine/dispatch | Agrees. l.165 correctly says the request overhead has no row. |
| 177 | tab:stage-budget | the prefill allowance "assumes the cache" | Caption: "the prefill target assumes the fixed prefix is already cached" | Agrees |
| 190 | tab:core-allocation | applied per thread; worker on cores 1-3 | Row 1-3: "Parse-path worker: speech recognition and the language model, each on three threads" | Agrees |
| 244 | fig:architecture | the consumer and the state machine sit on the workstation in the design | Workstation node: "Validator (layer 2), state machine (layer 3), ordering rule"; Wi-Fi arrow from the bus | Agrees |
| 274 | tab:functional-requirements | flight-state-machine criterion verified by an automated test of every cell | "Automated test of every (flight state, intent) cell of the legality table" | Agrees |
| 293 | tab:legality | a hold is illegal in LANDING | `hover` not legal in LANDED, LANDING, ABORTED | Agrees |
| 339-341 | tab:nonfunctional-requirements | formation-accuracy criterion: 0.5 m tolerance over the final 5 s | "within $\tau = 0.5$~m of the assigned slot over the final 5~s of a 60~s trial" | Agrees |
| 366, 371, 431 | (Ch1 collisions criterion, by name) | defines a collision as a pair closer than 0.35 m; quotes the budget | "Inter-drone collisions"; "Zero observed across all trials, with a hard geometric separation clamp at the integrator" | The quote agrees with Ch1 l.354's prose form ("backed by"). The 0.35 m definition is not the criterion's (finding 5). |
| 417 | tab:functional-requirements | the simulation-backends criterion rests on one controller with one set of gains | "Two interchangeable simulation backends sit behind one environment interface ... Both pass a hover smoke test" | Partial (finding 4) |
| 188 | (Ch1 preemption-recovery criterion, by name) | bounded by how fast the server stops decoding | "Time from a reflex-path trigger until the parse path can accept a new utterance" | The name agrees. Whether the bound covers every trigger (V3) is the argument agent's. |

Criterion names checked against Ch1's tables: flight-state-machine, simulation-backends,
formation-accuracy and preemption-recovery match. "collision" should be "collisions" (finding 5), and
"false-accept / false-reject" should be "keyword false-accept / false-reject" (finding 23).

## 5. Citation table (D5b)

| Key | file:line | Claim it carries | Verdict | Note (source passage) |
|---|---|---|---|---|
| silero | ch4:74 | The endpointer runs the Silero VAD model on ONNX Runtime, not through the package wrapper, because the wrapper imports PyTorch. | SUPPORTS | README: `silero-vad[onnx-cpu]` installs "onnxruntime>=1.16.1"; "The core requirement is torch>=1.12.0". Installed `utils_vad.py:1` `import torch`. The 512-sample window with 64 samples of context and the carried state are at `utils_vad.py:60-87`. |
| pytorch | ch4:76 | (identifies the library the wrapper imports) | SUPPORTS | arXiv 1912.01703: "PyTorch is a machine learning library ...". The key only identifies the library, and that is all it needs to do. |
| oww | ch4:94 | Two classifier heads over openWakeWord's frozen feature front end. | SUPPORTS | README: "A classification model that follows the shared (and frozen) feature extraction model". |
| oww (same paragraph, uncited) | ch4:94-96 | mel spectrogram, then one 96-dim embedding per 80 ms frame; heads score the last 16 embeddings. | SUPPORTS (source code, not README) | README: "computes melspectrogram"; "Models process a stream of audio data in 80 ms frames". `utils.py:323` `embedding_dim = 96  # fixed by embedding model`; embeddings are stepped every 8 mel frames (`:229`, `:330`), i.e. 80 ms; `train.py:26` default `input_shape=(16, 96)`. The 16-embedding window and its 1.98 s span are the project's (`train_wake.py`). |
| oww (uncited) | ch4:114 | "The upstream trainer requires PyTorch" | SUPPORTS if cited (finding 9) | `openwakeword/train.py:1` `import torch`. |
| piper | ch4:117 | Synthetic positives were rendered by three TTS voices. | SUPPORTS | README: "A fast and local neural text-to-speech engine"; voices are listed in docs/VOICES.md. The three voices are named in `data/wake/wake_manifest.json` (script PASS), not in the text. |
| whispercpp | ch4:148 | `whisper.cpp` run as a process per utterance, `tiny.en`, three threads, initial prompt. | SUPPORTS | README: "High-performance inference of OpenAI's Whisper automatic speech recognition (ASR) model"; `make -j tiny.en`. examples/cli/README: "-t N, --threads N ... number of threads"; "--prompt PROMPT ... initial prompt". |
| llamacpp | ch4:155 | `llama-server`, a persistent process: one slot, three threads, 512-token context; three requests (template, tokenise without special tokens, grammar-constrained completion); server timing report. | SUPPORTS | tools/server/README: "Fast, lightweight, pure C/C++ HTTP server"; "--parallel ... number of server slots"; "--threads"; "--ctx-size"; `/apply-template` "convert chat messages to a single string"; `/tokenize` `add_special` "Default: false"; `/completion` `grammar`; timings `prompt_ms` / `predicted_ms`. |
| reynolds1987 | ch4:344 | The third control term is the cohesion and alignment of flocking, towards the swarm's centroid and mean velocity. | PARTIAL | The rules are "Velocity Matching" and "Flock Centering", both on "nearby flockmates". The paper rejects the central force model, which makes "all members ... converge toward the flock's centroid". Finding 1. |
| pyflyt | ch4:400 | Five quadrotors in PyFlyt, on the Bullet physics engine, with rigid-body dynamics, rotor dynamics and PyFlyt's own attitude control. | SUPPORTS | Abstract: "a platform built on the Bullet physics engine". §Motors: RPM modelled with "a first-order transfer function plus noise depending on the motor time constant". §QuadX: "cascaded Proportional Integral Derivative (PID) architecture ... to achieve increasingly higher levels of attitude control". |
| pyflyt (same paragraph, uncited) | ch4:402-404, 409 | World-frame velocity setpoint; PyFlyt also accepts a position setpoint; physics at 240 Hz. | SUPPORTS (the yaw clause needs precision, finding 13) | Paper §QuadX setpoints: "Linear velocity control and yaw rate", "Position control and yaw rate"; "physics looprate of 240 Hz". `quadx.py:244-252` mode 6 "vx, vy, vr, vz", mode 7 "x, y, r, z". |

Uncited claims checked (D5c), in addition to the rows above:

- l.83-85, Silero defaults: true, see finding 10.
- l.191-192, Linux affinity inheritance: true (`sched_setaffinity(2)`), see finding 8.
- l.337-338, critical damping: true under unstated assumptions, see finding 14.
- l.364-365, rotor-tip diameter: unsourced, see finding 3.
- l.390-392, explicit integration: unsourced and not borne out, see finding 2.
- l.328-330, greedy assignment: unsourced, see finding 12.
- l.406-409, PyFlyt's steady altitude error: an observation from the project's own test, not a
  documented PyFlyt property. The argument agent judges whether it belongs in a no-measurement chapter.

## 6. Heading table (D12)

| line | heading | verdict | replacement |
|---|---|---|---|
| 30 | Implementation | OK (prd §3.1) | none |
| 46 | Audio chain | OK | none |
| 57 | One stream, two consumers. | NIT (finding 29): slogan-like | Frame loop and worker. |
| 74 | Endpointing. | OK | none |
| 93 | Keyword spotter. | OK | none |
| 112 | Training the spotter. | OK | none |
| 139 | Runtime | OK | none |
| 148 | Speech recognition. | OK | none |
| 155 | Parser. | OK | none |
| 168 | Prompt cache. | OK | none |
| 179 | Preemption. | OK | none |
| 190 | Core pinning. | OK | none |
| 198 | Artefacts from the M\'emoire de Master. | OK in length (5 words); NIT on the missing `\emph` (finding 28) | Artefacts from the \emph{M\'emoire de Master}. |
| 204 | Entry point. | OK | none |
| 209 | Command bus | OK | none |
| 223 | Sequence numbers. | OK | none |
| 232 | Consumer. | OK | none |
| 241 | Transport as run. | NIT (finding 30): elliptical | Transport in the experiments. |
| 249 | Flight state machine | OK | none |
| 259 | Handling a command. | OK | none |
| 273 | Verification. | OK | none |
| 286 | Legality of the original intent. | NIT (finding 31): a noun phrase, but opaque | Substituted commands and legality. |
| 297 | Link to the swarm controller. | OK | none |
| 306 | Swarm controller | OK | none |
| 320 | Formation slots. | OK | none |
| 334 | Control terms. | OK | none |
| 351 | Separation clamp. | OK | none |
| 377 | Simulation backends | OK | none |
| 386 | Kinematic backend. | OK | none |
| 399 | Physics backend. | OK | none |
| 415 | One controller, one set of gains. | MINOR (finding 16): a claim | Controller parity across backends. |
| 427 | Scope of the physics backend. | OK | none |

## 7. Build results (D9)

- `tools/check_tex.py thesis/ingenieur/ch4_implementation.tex` (without `--xelatex`): 21 problems, all
  cross-chapter `\ref`s. Every one resolves in the full build. There is 1 note: `chap:implementation` is
  not referenced within the file, but Ch1/Ch3/Ch5/Ch6 reference it 6 times. 8 cites, all resolved; 0
  tables.
- Clean build: `rm -rf thesis/build/ingenieur && cd thesis && latexmk -xelatex main_ingenieur.tex`.
  latexmk exited 0, giving 56 pages and 531,983 bytes.
  - `grep -c '^!'` = 0.
  - No `Citation ... undefined`, `Reference ... undefined`, `There were undefined references` or `Float
    too large`.
  - No Overfull or Underfull box lines anywhere in the log, so none in ch4_implementation.tex.
  - The only warning is the Amiri small-caps font substitution (front matter, not Ch4).
- Ch4 occupies PDF pp. 33-41 (4.1 p.33, 4.2 p.35, 4.3-4.4 p.37, 4.5 p.39, 4.6 p.40). The one visible
  typographic defect is the hyphen break in "Qwen2.5-0.5B" on p.36 (finding 25).

## 8. UNVERIFIED

1. **koren1991 content.** The paper is paywalled (IEEE), so I did not check whether it presents the
   repulsive-force form $\eta\,(1/d - 1/d_0)/d^2$. If finding 17's optional cite is added, it should
   carry the method only.
2. **Crazyflie dimensions.** Finding 3 rests on two facts: the physics backend uses PyFlyt's Crazyflie 2.x
   model, and the text states no airframe size. I did not fetch the Crazyflie's physical span, so I do not
   assert how far 0.80 m is from twice it.
3. **Origin of the "cohesion / alignment / separation" terms.** I did not verify which source introduced
   them (they are often attributed to Reynolds' later work). Finding 1 says only that the 1987 paper uses
   "Collision Avoidance", "Velocity Matching" and "Flock Centering".
4. **Explicit-integration check (finding 2).** I ran it on a 1-D linearised model: PID, acceleration and
   speed limits, no flocking, no potential field, one vehicle. I did not run the full five-vehicle
   `NumpyEnv` with its integrator switched to explicit Euler. The verifier can do this if the author
   wants to keep the sentence.
5. **`piper` author field** ("Hansen, Michael and the Open Home Foundation"). Not checked against the
   repository's own credits.
6. **scikit-learn / ONNX Runtime bibliography entries.** Not drafted. SKILL §4 makes that the author's job,
   against the primary pages.
