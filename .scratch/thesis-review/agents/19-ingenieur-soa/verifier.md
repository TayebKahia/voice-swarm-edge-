# Issue 19 -- Ingénieur Ch3 (State of the art) -- verifier report

Chapter: `thesis/ingenieur/ch3_state_of_the_art.tex` (511 lines, working tree = `c3fe8d5` + the six
uncommitted style edits), read in full. Line numbers below refer to it. Checked against: both agent
reports; issue 19; `docs/agents/thesis-chapter-review.md` (severity l.173-179); prd.md §2 C4 (l.124)
and §3.1 item 3 (l.187); issue 16 (M1 ruling) and `16-master-soa/verifier.md`; `master/ch3_state_of_the_art.tex`
This-work rows; `ch3_architecture.tex` l.122-133 (Placement); `ch4_implementation.tex` l.332, l.436-466;
`ch5_validation.tex` l.88-100, l.364-365, l.405-420; `generated/requirements_summary.tex`;
`tools/review/ingenieur_ch2.py`, `lib.py` (`find`, `text_claim`, `_codes`, `_refs`), `selftest.py` l.37-52,
`ingenieur_bg.py` l.81-91.

Primary sources: the arXiv HTML full text was downloaded with curl and grepped (MathML alttext
kept) for MIRA 2609.24547, Silva and Burke 2601.15486, Torkamani and Zarin 2512.12769, CommandSwarm
2605.07764, Henry 2606.24910, Iannoli 2605.03788, LLM2Swarm 2410.11387 (v1-v3), Lim 2506.07509,
Sikorski 2405.17670, Simões 2407.08658, SwarmChat 2509.16920, Chat with UAV 2512.08145. Submission
dates were read from the arXiv abs pages. I edited no repository file except this report. Every
wording below was tested in a scratch copy of the repo (`thesis/`, `tools/`, `results/`, `prd.md`,
`eval/`, `schema/` copied to the session scratchpad; the issue-18 files were only copied, never
touched in place).

## 1. Summary

| ID | Sev reported | Verdict | Sev verified | Evidence | Fix judgement |
|---|---|---|---|---|---|
| Rev B1 = Cit B-5 (l.365-366 "the most recent system that accepts speech") | BLOCKER | CONFIRMED | BLOCKER (low impact) | arXiv abs pages: CommandSwarm submitted 8 May 2026, Henry et al. 19 Jun 2026, MIRA 21 Sep 2026. Henry and MIRA both take speech and are rows of the same table. | Both fixes are right. I drop the appositive altogether, inside the M-1 rewrite of that sentence (§3). |
| Cit B-1 (l.425-427 "established no latency" for MIRA; dual-path cell dash) | BLOCKER | CONFIRMED | BLOCKER | MIRA Table 3: "Deterministic Interruption Preemption, speech_started → abort_cmd_sent, 466 ms" (P50). §5.3: "the preemption latency is 466 ms at the median". §3.4: the gate fires when a segment "reaches the configured 450 ms interruption-confirmation threshold while playback is active". There is no target the 466 ms is judged against; the only "budget" in the paper is ROSCO's motion-emission budget. | The fix is right, and G2 still follows once the claim is narrowed (§2). The cell fill is right, but I leave the slow path as a dash. MIRA's 1.62 s is LLM time-to-first-token, not the deliberative arbiter that the table's "slow path" names. |
| Rev M4 + Cit B-2 (l.151-152, l.421-423 "no system ... reports a stopping command handled separately") | MAJOR / BLOCKER | CONFIRMED | BLOCKER | Silva and Burke: "The out-of-band emergency stop (the safety pilot disarming by radio, with no server involvement) was exercised deliberately on both airframes". Also "an out-of-band, four-ring override chain ... preserves human e-stop / radio-control (RC) takeover independent of the LLM". Lim et al.: "the operator will switch the flight mode to POSITION mode". The claim is refuted by two rows of the table it names. | The reviewer's "spoken or typed" scoping is the right cut: no row has a spoken or typed stop outside the interpreting path, and the ones that exist are human. Merged wording in §3. It is used in both places. |
| Cit B-3 (l.439-441 "The edge tier ... presumes that the network is available") | BLOCKER | CONFIRMED | BLOCKER | Torkamani: TinyLlama offline "enables operation without internet connectivity"; "In all other scenarios, online inference is preferred". The routing policy presumes the network; the edge tier does not. | Fix right. Folded into the G3 rewrite (§3). |
| Cit B-4 (tab:soa-swarm CommandSwarm role cell, l.283) | BLOCKER | CONFIRMED | BLOCKER | CommandSwarm §III: commands flagged by the safety classifier "are rejected before they reach the BT generator ... complemented by parser-level validation after generation, creating two independent control points". | Cell fix right. Shortened slightly (§3). |
| Rev M1 (tab:soa-swarm This-work row, l.285) | MAJOR | CONFIRMED | **BLOCKER** (raised) | ch4_implementation l.440-441: "the effective control rate is 24~Hz rather than the nominal 48~Hz or 50~Hz". l.447-451: "The formation-control results come from the kinematic backend alone ... apply no separation clamp". l.462-464: "exercised by these tests only ... Its runs apply no separation clamp". The cell says both simulators exercised the controller at 50 Hz, with the clamp. That contradicts Chapter 5, and the standard counts a contradiction with another chapter as a BLOCKER. | Fix right. Wording in §3 names both backends and both rates; 150 is left out so the cell stays short. |
| Rev M2 (tab:soa-speech This-work "Offline: Yes", l.358; closing l.506-507) | MAJOR | CONFIRMED | MAJOR | requirements_summary rows "Offline speech recognition ... No run with networking disabled ... Not yet run" and "Offline operation ... Not yet run"; ch5_validation l.413-415. Chapter 6 does not say "No", so this is an overclaim, not a contradiction. | Fix right in substance, but the proposed cell is too long for a 1.4 cm column. Cell "By design; not yet tested", with the qualification moved to the caption (§3). |
| Rev M3 (l.144, l.434-435 "No system in the table runs its full chain on an SBC without a GPU") | MAJOR | CONFIRMED | MAJOR | Taken literally, it includes the This-work row. Three prior host cells are dashes. U2 is resolved: Sikorski's control computer is "a Dell Precision 3660 Tower Core i7 ... and Nvidia RTXA4000 GPU", so that row does not break the claim. Torkamani's Jetson Xavier NX has a GPU. LLM2Swarm (not in this table) ran "TinyLlama via Ollama on a Raspberry Pi 5". | Fix right. "Speech and language chain" (m9) replaces "full chain", since the state machine and simulator run on the workstation (ch3_architecture l.122-124). G3 should also name the Pi 5 test honestly (§2). |
| Rev M5 (l.231-233; Synthesis l.384-386 "one to two orders of magnitude") | MAJOR | CONFIRMED (the proposed ratio is not like-for-like) | MAJOR | Henry: "(106 ms on CPU)" for the direct path. The only GPU the paper names is the RTX 2000 Ada, used for fine-tuning. Simões states no hardware at all. The reviewer's 202/106 = 1.9 compares a CPU direct path with a cascade whose host is not stated, so it compares hosts as well as pipeline shapes. | The qualifier is needed, but not the 1.9 ratio. Say what hardware each figure has (§3). |
| Rev M6 (l.299-305 "is therefore published"; "stops only as fast as the planner answers"; secondary l.234-235) | MAJOR | CONFIRMED | MAJOR | l.299-300 is a concession that repeats l.398-399. Its "therefore" does not follow from SkySim falling outside Strobel's categories. l.302-305 is G2's premise (l.423-424) in advance. Issue 16 M1 ruling: "a gap statement or design rationale is not" allowed in a critical comparison. Partial defence: the introduction (l.24-25) licenses "what none of them provides". The rewrite keeps a neutral reading of SkySim's latency, which is enough for that. | Fix right. The replacement reads the Evaluation column (with F-9/F-10) rather than repeating the prose's 34/50 s (§3). m2 ("four axes") is folded in. |
| Cit M-1 (tab:soa-speech omits Torkamani; "only Sikorski et al. state offline recognition") | MAJOR | CONFIRMED | MAJOR | Torkamani: "user voice input is first transcribed by an offline ASR module"; "a lightweight 8-bit tiny ASR engine based on the faster-whisper implementation"; "Jetson Mate Xavier NX edge device used for local ASR and LLM inference". No ASR latency is reported. SwarmChat accepts voice but names no recogniser. | Row and sentence right. The caption must say why SwarmChat has no row. The prose in sec:voice-uav and sec:speech-components must carry the new facts, so that G3 introduces nothing (§3). |
| Cit M-2 (Iannoli guardrails counted as "deterministic, automated checks"; "measure why") | MAJOR | CONFIRMED | MAJOR | Iannoli §III: "guardrail prompts ... When activated, they are injected into the LLM context to constrain or redirect reasoning ... without hard-coded control policies". The ablation is "area coverage (with and without planning tools)" only. One sentence says the guardrails "constrain or halt interactions", which does not make them a deterministic check between output and vehicle. | Fix right. Torkamani's rule-based validation and repair is also deterministic and dated 14 Dec 2025, so "appear in the systems of 2026" should become a count, not a date (§3). |
| NEW-1 (l.374-375 "none states a latency budget for its speech stage") | -- | NEW | MAJOR | Henry §IV: "UAV teleoperation systems require end-to-end latencies below 100 ms ... our End-to-End architecture reduces inference to 7 ms, well within this operational threshold". The source sets a stated latency limit against its speech-to-intent latency. | Scope it to "allocates a budget" and report Henry's limit (§3). G2 is unaffected, because Henry's limit is not for a stop. |

## 2. Reasoning per finding

### Rev B1 / Cit B-5 -- CONFIRMED, BLOCKER
Attempted disproof: read "the most recent system that accepts speech" as "the most recent
*swarm* system that accepts speech". That reading fails on the words, and even with "swarm" added
the sentence is not needed. Dates are verified above. The fix is simply to drop the appositive. The
M-1 rewrite of the same sentence does that.

### Cit B-1 -- CONFIRMED, BLOCKER; G2 narrowed, still follows
Attempted disproof: "this review established no latency" is a statement about the review, so it is
literally true if nobody read Table 3. That fails: a review may not assert the absence of a figure
that its own source prints, and G2 uses the absence as evidence. **Does G2 survive?** Yes, but
the gap changes. It is no longer that no stop latency is on record. It is that no reviewed stop is
held to a budget of its own, and none is triggered by a command. MIRA's abort is triggered by any
sustained speech during playback. Its 466 ms includes the 450 ms confirmation the gate waits for by
design, and the paper judges it against no target. Silva and Burke's and Lim et al.'s stops are
human. No other row has a stop outside the interpreting path. C4's first clause, "a reflex with a
latency budget of its own that preempts language-model inference" (prd l.124), closes exactly that.
Preemption is already conceded to MIRA (l.400-401; issue 07). So G2 must say that what is claimed
is the budget, and must promise only measurement: "reports whether it is met and where a miss lies".
Chapter 6 reports 545/547 ms against 150 ms and locates the miss (ch5_validation l.91-100). The
examiner's question about the miss is then answered by the gap itself. I did not add a sentence
saying MIRA's 466 ms is not comparable with 150 ms: the anchors do differ (speech onset against
keyword offset), but volunteering that next to a measured 545 ms reads as defensive.

### Rev M4 / Cit B-2 -- CONFIRMED, raised to BLOCKER
Attempted disproof: "stopping *command*" implies an utterance or message, and a radio kill is not
a command. That fails for Silva and Burke, whose override chain is described as the human e-stop
path. It also fails for the chapter's own wording, "handled separately from the path that
interprets commands". The citation agent's "automated" cut is weaker than the reviewer's "spoken or
typed": a radio kill switch is automated once thrown. So I use "spoken or typed stop" and name the
human stops. This is a claim the evidence refutes, so BLOCKER.

### Cit B-3 -- CONFIRMED, BLOCKER
There is no defensible reading: the cited sentence attributes to the edge tier the one property
that the source says it removes. The issue-07 uncited version ("Routing of that kind presumes ...")
was right. The G3 rewrite restores it, cited to the routing policy.

### Cit B-4 -- CONFIRMED, BLOCKER
A wrong table cell is a BLOCKER by the issue's own rule (chapter comment l.13-14). The Check cell in
tab:voice-uav-survey ("Primitive whitelist; parser; safety classifier") is a list without an order
and stays correct. So does l.148-149 "a whitelist parser behind a safety classifier", because the
parser does come after the classifier.

### Rev M1 -- CONFIRMED, raised to BLOCKER
Attempted disproof: "five vehicles at 50~Hz" is the controller's nominal rate, which Chapter 1
l.78 also states. That fails because the Evaluation column is "how the control layer was
exercised", and Chapter 5 says the physics backend exercised it at an effective 24 Hz, in tests
only, with no clamp. It is the issue-16 M2 pattern, but here it contradicts another chapter
outright, so it is a BLOCKER under the standard. The fix restores agreement with Ch5 (l.440-466)
and Ch6 (ch5_validation l.364-365, "60~s at the controller's 50~Hz tick" on the kinematic backend).

### Rev M2 -- CONFIRMED, MAJOR
Attempted disproof: whisper.cpp runs on the Pi and makes no network call, so "recognition runs
without a network connection" is a true design fact. It is true as design, but the caption says "as
the source states it", and for this row the source is Chapter 6, which records "Not yet run". It is
an overclaim, not a contradiction, so it stays MAJOR. My caption wording is "recognition needs no
network connection", not "no stage calls the network", because the command bus crosses the LAN to
the workstation (ch3_architecture l.134-136).

### Rev M3 -- CONFIRMED, MAJOR
U2 resolved from the source: the Sikorski control computer is a GPU desktop. The claim is true once
scoped to prior rows and to what they record. The LLM2Swarm Pi 5 test does not break it, since it
has no speech, is not in this table, and was a speed test. But a jury member who has read LLM2Swarm
would raise it, so G3 names it (citation F-15). Adding it to G3 required putting the fact in the
theme section first (the l.251-252 prose and the Strobel Evaluation cell), because the script rule is
that Research gaps introduces nothing.

### Rev M5 -- CONFIRMED, MAJOR; proposed ratio rejected
The two ratios in the text hold (1233/21 = 58.7; 202/7 = 28.9). What the Synthesis drops is the
host. Simões gives no hardware at all, so the reviewer's "on the hardware each reports" is itself
inexact. The replacement says "on a GPU or on hardware the study does not state". It keeps Henry's
106 ms CPU figure as a fact, without a ratio against a cascade whose host is not stated.

### Rev M6 -- CONFIRMED, MAJOR
See the table. The secondary l.234-235 ("bears on a fast path that must choose among several
commands") reads the studies against this work's G1 need. The reviewer's replacement ("Both studies
report the result for alternatives, not for two paths running at once") is applied.

### Cit M-1 -- CONFIRMED, MAJOR
The Torkamani row uses the same shape as its neighbours. "8-bit" and "faster-whisper" are the
source's words. The caption scopes out SwarmChat, whose paper never names a speech component.

### Cit M-2 -- CONFIRMED, MAJOR
The Synthesis cite list becomes `torkamani2025,silva2026,skysim2026,commandswarm2026`, with
`iannoli2026` cited separately for guardrails that re-prompt. All five keys are cited in the theme
sections, so the positioning check passes.

### NEW-1 -- MAJOR
Found while checking Henry's hardware for M5 (§1 quote). Henry states a latency limit and positions
its speech-to-intent path within it, which refutes the l.374-375 silence claim as written. It does
not touch G2: the limit is for teleoperation commands, not a stop, and it is borrowed from Henry's
reference [49], not allocated by the authors. So "None allocates a latency budget to its speech
stage" is true, and naming Henry's 100 ms limit keeps it honest.

### What the This-work rows must say (Chapters 5-7)
- tab:voice-uav-survey: already correct ("Five simulated UAVs"; Raspberry Pi 5 CPU; the state
  machine sits on the workstation, but "Check before execution" does not claim otherwise).
- tab:soa-dual-path: m12 relabels "targets" as "Budgets", with their anchors. Measured values are not
  put in a state-of-the-art row, which is the Master's convention (master ch3 l.52, 137, 216, 277:
  what is measured, never the result).
- tab:soa-swarm: M1. tab:soa-speech: M2. tab:lim-positioning: "Reported ... safe-failure rate"
  checked against ch5_validation l.249, l.314, so it is reported.

## 3. Final text for every affected paragraph and table row

One coherent set, as tested (§5). Each block is the full replacement for the old lines named in
its heading; old line numbers are those of the current working tree. Where a block starts or ends
mid-sentence, the unchanged neighbouring words are included so it can be pasted over the old
lines exactly. G2, G3, the Synthesis and the Critical comparisons are given whole, so no two
findings patch the same sentence. Blocks marked (MINOR) or (NIT) can be dropped without breaking
the rest, except F-14 and F-16, which the rewritten Critical comparison relies on.

### Old l.36-38 -- m1 -- sec:voice-uav taxonomy (MINOR)

```latex
maps that field and the directions it is taking~\cite{javaid2024}. The systems reviewed here are of
four kinds: recognisers matched against a fixed command language, general language-model control
of robots, agents built for a single drone, and interfaces to swarms. Two further studies make the
host of the model their subject. Four properties separate them:
```

### Old l.79-80 -- F-12 -- Lim et al. goal (MINOR)

```latex
through Ollama on a local workstation \gls{gpu}, and flies one PX4-based quadcopter to a goal given
in its text message, with a vision-language model detecting the target; Section~\ref{sec:research-gaps} examines it as the baseline of this
```

### Old l.85-89 -- M-1/G3 support, B-3 support, n2, n6 -- 'Where the model runs' paragraph (the facts G3 now cites)

```latex
GPT-4-Turbo in the cloud against LLaMA~2-7B quantised to Q5\_K\_M and run offline on a desktop
control computer with a \gls{gpu}. Their authors describe the offline model's limitations in
consistency and reliability as significant~\cite{sikorski2025}. Torkamani and Zarin transcribe
spoken commands for Internet-of-Things devices offline, with a tiny 8-bit Whisper model. They then
route the language model between an NVIDIA Jetson board and the cloud according to processor load,
device temperature and network latency, preferring the cloud whenever these allow~\cite{torkamani2025}.
```

### Old l.107-107 -- m1 -- tab:voice-uav-survey caption (MINOR)

```latex
\caption[Published language interfaces to robots]{Published language interfaces to robots and devices, by
```

### Old l.124-125 -- F-16, F-14, n6 -- tab:voice-uav-survey Sikorski and Torkamani rows (core: the Critical comparison relies on them)

```latex
Sikorski et al.~\cite{sikorski2025} & Speech & One ground robot & GPT-4-Turbo, remote, or LLaMA~2-7B on a control computer & Validity test, unspecified \\
Torkamani and Zarin~\cite{torkamani2025} & Speech & Internet-of-Things devices & Edge (Jetson) or cloud, routed at run time & Rule-based validation and repair \\
```

### Old l.141-145 -- M3, m4/F-7, F-22 -- Critical comparison sec:voice-uav, host sentences

```latex
language model is remote in every system that names a provider, apart from a locally hosted arm in
Silva and Burke. It is local to a workstation \gls{gpu} in Lim et al.\ and to a control computer in
the offline arm of Sikorski et al. Torkamani and Zarin prefer the cloud and fall back to a Jetson
edge board when its runtime metrics call for it. No prior row records a speech and language chain
run on an \gls{sbc} without a \gls{gpu}, and three rows state no host at all. On the check, the
systems without a language model constrain the operator instead, through a command language or a
```

### Old l.147-152 -- M-2, M4/B-2 -- Critical comparison sec:voice-uav, check and stop sentences

```latex
The checks range from a prompt format and a sampling temperature (Lim et al.) to human review
(Vemprala et al.). Four are deterministic and automated: rule-based repair (Torkamani and Zarin),
server-side validation (Silva and Burke), waypoint bounds (SkySim) and a whitelist parser behind a
safety classifier (CommandSwarm). Iannoli et al.\ add runtime guardrails that re-prompt the model,
and report that general-purpose models without grounding and execution support struggle to execute
even simple swarm tasks reliably. No prior row reports a spoken or typed stop carried
outside the path that interprets commands. The stops reported outside that path are a human's:
Silva and Burke's safety pilot disarms by radio, and Lim et al.'s operator switches to position
mode.
```

### Old l.181-181 -- F-20 -- RelayS2S scope (MINOR; anchor kept contiguous)

```latex
first chunk falls from 1{,}006~ms to 81~ms on synthetic dialogues, excluding speech synthesis and network
time~\cite{relays2s}. MIRA combines low-latency barge-in
```

### Old l.203-203 -- m12 -- tab:soa-dual-path caption (MINOR)

```latex
reports for the fast and the slow path, in that order; the last row gives budgets, not measurements. A dash marks a property this review did not
```

### Old l.212-212 -- F-11 -- Sahai row (MINOR)

```latex
Sahai et al.~\cite{dualattn2023} & Cheaper attention branch; full branch, in one recognition model & One model, per frame & Nothing; wake-word spotting picks the branch per frame & Computation & --- \\
```

### Old l.214-214 -- B-1 -- tab:soa-dual-path MIRA row

```latex
MIRA~\cite{mira} & Barge-in gate on voice activity; deliberative turn decisions & Concurrent; preemption & One action: abort the response and stop motion & Barge-in & 466~ms, median from speech onset; --- \\
```

### Old l.217-217 -- m12 -- tab:soa-dual-path This-work row (MINOR)

```latex
This work & Two-class keyword spotter; endpointer, recognition, language model under a grammar, validator & Concurrent; preemption by sequence number & One of two swarm commands, a hold or an abort & Stopping the swarm & Budgets, p95: 150~ms from keyword offset; 2{,}500~ms from end of speech \\
```

### Old l.231-235 -- M5, M6 (secondary), B-1 -- Critical comparison sec:soa-dual-path, latency axis

```latex
drone studies time the direct path one to two orders of magnitude below the cascade, 21~ms against
1{,}233~ms and 7~ms against 202~ms. Sim\~oes et al.\ do not state their hardware, and Henry et al.'s
7~ms is on a \gls{gpu}; their direct recogniser takes 106~ms on a \gls{cpu}. Henry et al.\ also
report the direct path as the more accurate of the two, by 14 points on explicit simple commands, so
on these tasks the faster shape costs no accuracy. Both studies report the result for alternatives,
not for two paths running at once. MIRA's gate aborts at a median of 466~ms from speech onset, after
waiting for 450~ms of sustained speech. No work in the
```

### Old l.252-252 -- M3/F-15 -- Strobel et al. prose (core: G3 cites the Pi 5 test)

```latex
conceptual, demonstrated in simulated showcases and in a preliminary test that ran TinyLlama on a
Raspberry~Pi~5~\cite{llm2swarm2024}. SkySim places a cloud-hosted planner, Gemini 3.5 Pro, above an
```

### Old l.259-259 -- F-17 -- SkySim citation (MINOR)

```latex
for time-critical missions~\cite{skysim2026}. CommandSwarm generates behaviour trees from a whitelist of executable
```

### Old l.280-280 -- F-15 -- Strobel row (MINOR)

```latex
Strobel et al.~\cite{llm2swarm2024} & --- & --- & Indirect: synthesises and validates controllers; or direct: one instance per robot & Mainly conceptual; ARGoS showcases; TinyLlama timed on a Raspberry~Pi~5 \\
```

### Old l.283-283 -- B-4 -- CommandSwarm row

```latex
Command\-Swarm~\cite{commandswarm2026} & Behaviour trees of whitelisted primitives & --- & Generates the tree; a safety classifier screens the command before generation, a parser the tree after & Trees scored, not executed \\
```

### Old l.285-285 -- M1 -- tab:soa-swarm This-work row

```latex
This work & Formation slots with a \gls{pid} law; low-weighted global flocking terms & Potential field; geometric clamp at the integrator (kinematic backend) & One instance on the operator's device chooses a formation-level command; not in the control loop & Five vehicles; kinematic simulator for the experiment, at 50~Hz; physics simulator in tests only, at an effective 24~Hz \\
```

### Old l.290-290 -- m2 -- four axes

```latex
\paragraph{Critical comparison.} Table~\ref{tab:soa-swarm} separates the works on four axes. On
```

### Old l.293-296 -- m5, F-18 -- separation axis

```latex
whitelisted primitives in CommandSwarm. On separation, SkySim is the one language-interface row
whose separation mechanism is recorded. It is a potential field, the method whose failure modes the
analysis of Koren and Borenstein catalogues, including the absence of a passage between closely
spaced obstacles~\cite{koren1991}. No prior row pairs the field with a mechanism that bounds what it fails to prevent. On
```

### Old l.299-305 -- M6, F-9, F-10 -- evaluation axis replaces the concession and the G2 restatement

```latex
layer beneath it. On evaluation, SkySim exercises its control layer in Gazebo simulation and Iannoli
et al.\ in ArduPilot software-in-the-loop simulation, while CommandSwarm's evaluation scores its trees
without executing them. Only SkySim reports how long its planner takes: tens of seconds, which its
authors judge unsuitable for time-critical missions.
```

### Old l.320-320 -- M-1 -- recognisers paragraph

```latex
recognise speech offline with VOSK~\cite{sikorski2025}, and Torkamani and Zarin with a tiny 8-bit
Whisper model, run through faster-whisper on a Jetson board~\cite{torkamani2025}. CommandSwarm chooses SeamlessM4T v2-large as
```

### Old l.344-344 -- M-1, M2 -- tab:soa-speech caption

```latex
SwarmChat, whose source names no speech component, has no row. The last row is this work; its
\emph{by design} means that recognition needs no network connection, but no run with networking
disabled has been made (Chapter~\ref{chap:validation}).}
```

### Insert after old l.354 -- M-1 -- new Torkamani row (after the Sikorski row)

```latex
Torkamani and Zarin~\cite{torkamani2025} & Whisper tiny, 8-bit, via faster-whisper & Yes & No & ---; Jetson Xavier~NX \\
```

### Old l.356-356 -- F-8 -- MIRA row

```latex
MIRA~\cite{mira} & Not named & --- & Gate on voice activity & Endpointing 10.0~ms, gate 466~ms (medians); host unstated \\
```

### Old l.358-358 -- M2 -- tab:soa-speech This-work row

```latex
This work & \texttt{whisper.cpp tiny.en}, after a Silero \gls{vad} endpointer & By design; not yet tested & Two-class keyword spotter on openWakeWord embeddings & Per stage, on the Raspberry~Pi~5 \gls{cpu} (Chapter~\ref{chap:validation}) \\
```

### Old l.364-366 -- B1/B-5, M-1 -- Critical comparison sec:speech-components, where recognition runs

```latex
On where recognition runs, the older systems depend on a platform or a cloud service. Sikorski
et al.\ and Torkamani and Zarin state offline recognition, the latter with a tiny Whisper model on
an edge board, and CommandSwarm does not claim it. On a transcription-free path, three systems have one, and each uses it
```

### Old l.374-375 -- NEW-1, F-8 -- Critical comparison sec:speech-components, last sentences

```latex
speech stage together with the processor that runs it. None allocates a latency budget to its
speech stage; Henry et al.\ set their 7~ms against a 100~ms end-to-end limit they cite for
teleoperation~\cite{henry2026}.
```

### Old l.381-389 -- M5, M-2, n4 -- Synthesis

```latex
\paragraph{Synthesis.} The four bodies of work reviewed above each settle part of the problem.
Language interfaces to robots have moved from fixed command languages to language models whose
output is checked. Deterministic, automated checks appear in recent
systems~\cite{torkamani2025,silva2026,skysim2026,commandswarm2026}, beside runtime guardrails that re-prompt the
model~\cite{iannoli2026}. Transcription-free paths have been timed at one to two orders of magnitude
below a cascade, with no loss of accuracy on the tasks measured, on a \gls{gpu} or on hardware the
study does not state~\cite{simoes2024,henry2026}. Fast paths have run concurrently with slow ones,
gated by a verifier or by preemption~\cite{relays2s,mira}. Language-model planners have been placed
above a potential-field layer that keeps vehicles apart~\cite{skysim2026}. Speech has been
recognised offline and a local language model run beside it, on a desktop computer and on an edge
board, each with a \gls{gpu}~\cite{sikorski2025,torkamani2025}. The tables leave three gaps, stated below in the order the
```

### Old l.394-394 -- F-25 -- Conceded prior art (NIT)

```latex
claimed here. CommandSwarm covers spoken commands to a group of robots with the model's output
```

### Old l.409-411 -- m7 -- Gap G1 opening (MINOR)

```latex
\paragraph{Gap G1, fast-path membership.} Of the fast paths in Table~\ref{tab:soa-dual-path}
that coexist with a slower path at run time, MIRA's has one action, the abort, and those of Sahai
et al.\ and RelayS2S serve computation or responsiveness rather than safety. The drone studies that measure a direct path choosing among commands build it as an
```

### Old l.421-432 -- B-1, B-2/M4, m8 -- Gap G2 (whole paragraph)

```latex
\paragraph{Gap G2, a budgeted stop.} No prior row of Table~\ref{tab:voice-uav-survey} reports a
spoken or typed stop carried outside the path that interprets commands. The stops that bypass that
path are a human's: Silva and Burke's safety pilot disarms by radio, and Lim et al.'s operator
switches to position mode~\cite{silva2026,lim2025}. The layered design nearest to this one routes
every command through a planner whose latency runs to tens of seconds~\cite{skysim2026}. TypeFly
answers the latency of generation by shortening the path every command takes~\cite{typefly2024}, and
CommandSwarm lists emergency stop mechanisms only among the safeguards a real deployment should
require~\cite{commandswarm2026}. MIRA's gate does stop motion and preempt the slower path, once
speech during the robot's playback has lasted 450~ms, at a median of 466~ms from speech
onset~\cite{mira}. It reacts to any sustained speech rather than to a command, and states no latency
target against which that median is judged. No reviewed system, therefore, holds a stop to a latency
budget of its own. The first clause of the contribution closes this gap: a reflex path that preempts
language-model inference, with a budget of 150~ms at p95 from the keyword offset that must hold
while the model decodes. Its preemption is conceded to MIRA; the budget is what is claimed. The
dual-path decomposition (Section~\ref{sec:dual-path}) and the latency budget
(Section~\ref{sec:latency-budget}) specify it. Section~\ref{sec:latency-experiment} measures it
against that budget, idle and under load, and reports whether it is met and where a miss lies.
```

### Old l.434-446 -- M3, B-3, m9, F-15 -- Gap G3 (whole paragraph)

```latex
\paragraph{Gap G3, one-board execution.} No prior row of Table~\ref{tab:voice-uav-survey} records
a speech and language chain run on an \gls{sbc} without a \gls{gpu}, and three rows state no host.
No prior row of Table~\ref{tab:soa-speech} reports each speech stage's latency together with the
processor that runs it. The offline arm of Sikorski et al.\ runs on a desktop computer with a
\gls{gpu}, and its authors describe the offline model's limitations as
significant~\cite{sikorski2025}. The \emph{M\'emoire de Master} measures that cost for the models
that can run on this device. The nearest chain, that of Torkamani and Zarin, can run a tiny Whisper
model and TinyLlama on a Jetson board with a \gls{gpu}, but prefers the cloud whenever the board's
metrics allow~\cite{torkamani2025}. A routing policy of that kind presumes that the network is
available at least part of the time, which the deployment site of
Section~\ref{sec:operational-context} does not assure. Strobel et al.\ ran TinyLlama on a
Raspberry~Pi~5 only as a preliminary test of generation speed, without speech~\cite{llm2swarm2024}.
Running the chain on one board is engineering rather than a research contribution
(Section~\ref{sec:contributions}), and an architecture decision closes this gap: the allocation of
the four cores of Section~\ref{sec:resource-allocation}. It belongs among the gaps because it is the
condition under which the second is tested: Section~\ref{sec:latency-experiment} measures the
reflex, stage by stage, on the same four cores on which the language model decodes.
```

### Old l.449-449 -- m11 -- baseline (MINOR)

```latex
because, among the systems reviewed, it is the one nearest to this one in the part of the design the \emph{M\'emoire
```

### Old l.466-467 -- m10 -- tab:lim-positioning caption (MINOR)

```latex
al.~\cite{lim2025} and of this work. Every design row differs, and each such difference changes either
the latency or the accuracy a system can reach, which is why the two are compared by design and not by
```

### Old l.501-502 -- m10 -- Comparison by design, last sentence (MINOR)

```latex
difference: this system moves the design axes of Table~\ref{tab:lim-positioning} towards the deployment of
Section~\ref{sec:operational-context}. Those axes are spoken input, an \gls{sbc} without a
\gls{gpu}, five vehicles, output checked before it is published, and a stop that does not wait for
a human.
```

### Old l.504-509 -- M2, m8, m13 -- closing paragraph (its last sentence, 'Chapter~\ref{chap:architecture} designs ...', l.510-511, is unchanged)

```latex
\paragraph{Summary.} The gap this document fills is therefore a conjunction, narrower than any of
its parts. Among the systems reviewed, none combines four properties. They are deterministic
checking of spoken swarm commands, a separate control-rate safety layer, a reflex that preempts the
language model under a derived membership rule and its own budget, and execution on an \gls{sbc}
with no network dependency by design. The first two are conceded to CommandSwarm and SkySim. The
third is claimed, for its membership rule and its budget, as Gaps G1 and G2; its preemption is
conceded to MIRA. The fourth, Gap G3, is the setting that turns the third into a problem of
```

## 4. MINORs (and NITs) -- judgement

Applied in the tested set (§3), and worth applying with the BLOCKER/MAJOR fixes, because several
of them rewrite the same sentences:

| ID | Judgement |
|---|---|
| m1 (four kinds + two host studies; caption "robots and devices") | Apply. Safe. The "kinds that exist" in the introduction (l.22) can stay: the section openings now scope themselves. |
| m2 ("four axes") | Apply (done inside M6). |
| m4 / F-7 (host sentence, 58 words; Silva's local arm) | Apply (done inside M3/M4). F-22 (the cloud is Torkamani's default) is folded in too. |
| m5 (dashes turned into facts) | l.146 is resolved by filling F-14 and F-16 (both checked against the sources: Torkamani's "rule-based command validation and repair component"; Sikorski's Algorithm 1 "if LLM_Return is Valid then Robot_Command <- LLM_Return"). l.146 is then true of every row and stays unchanged. l.293 is applied. l.374-375 is subsumed by NEW-1. |
| m6 | Subsumed by M-2. |
| m7 (G1 opening) | Apply, reworded: the reviewer's "that run beside a slower one" miscasts Sahai's per-frame branch. Mine is "that coexist with a slower path at run time". |
| m8 (preemption conceded; CommandSwarm's emergency stop among safeguards) | Apply (done in G2 and Summary). CommandSwarm verified: "Real-world deployment should require additional safeguards, including ... emergency stop mechanisms". |
| m9 (speech and language chain; G3 names the per-stage measurement) | Apply (done in G3). |
| m10 (design axes; caption) | Apply. Split into two sentences to stay at or under 40 words. |
| m11 (baseline superlative scoped) | Apply. |
| m12 (dual-path This-work latency cell relabelled as budgets) | Apply. It becomes more important once MIRA's 466 ms sits in the same column. |
| m13 (closing paragraph gets a lead-in and maps to G1-G3) | Apply (done: `\paragraph{Summary.}`). No script check depends on the paragraph list after G3. |
| n2 ("significant" attributed to the authors) | Apply (done at l.86 and in G3). |
| n4 (Synthesis opening identical to the Master's) | Apply (done). |
| n6 (IoT typed by hand) | Apply (done: "Internet-of-Things" at both sites, l.87 and l.125). |
| F-9 / F-10 (SkySim is Gazebo, not SITL; CommandSwarm executes, but not in its evaluation) | Apply (done inside M6). |
| F-11 (Sahai cell) | Apply: "Nothing; wake-word spotting picks the branch per frame". |
| F-12 (Lim's goal is given in the text message) | Apply. Verified: "specifying a target object to search and a textual description of the coordinate of the goal by publishing a ROS2 string message". |
| F-14 / F-16 (fill the Torkamani and Sikorski checks) | Apply. The Critical comparison now leans on F-14 ("Four are deterministic and automated"), so I treat it as part of the core set. |
| F-15 (Strobel's Evaluation cell and prose) | Apply. The prose half is core, since G3 cites it. |
| F-17 (SkySim sentences uncited) | Apply. |
| F-18 (`\cite{koren1991}` on the passage-between-obstacles item) | Apply (done inside M6). |
| F-20 (RelayS2S scope) | Apply. The anchor `1{,}006~ms to 81~ms` stays contiguous. |
| F-8 (MIRA per-stage medians) | Apply (cell filled; l.373-374 reworded). |
| F-25 ("group of robots") | Apply. |

Not applied / flagged:

| ID | Judgement |
|---|---|
| **n5** ("6.7--14~B") | **Unsafe for the script.** The anchor `6.7--14B` (ingenieur_ch2.py, paper_numbers) is matched literally, and `~` is not whitespace to `find`, so the change FAILs. Change the anchor in the same commit, or leave the cell alone ("0.5~B" in the This-work row is safe). |
| **m14** (move "Open components" to Ch4) | **Unsafe as proposed.** It removes four anchors (`680{,}000 hours`, `39 million`, `80~ms frame`, `32~ms windows`), and each missing anchor FAILs. Its alternative, cutting the repeats in ch3_architecture.tex, is outside this issue. Defer to issue 20. |
| **m16** (retitle "Voice-controlled UAV systems") | **Unsafe without a script edit.** The TOPICS map in ingenieur_ch2.py matches `voice-controlled`, and `outline_check` FAILs if no section matches. Apply only together with the script change; otherwise leave it for issue 20. |
| m15 (`\TODO` for the search method) | Right in substance, since the silence claims do rest on coverage. It needs facts only the author has. It adds one `marker` WARN, and the TODO text is inside `prose()`, so keep acronyms and numbers out of it. Recommended as a separate author action. |
| m3 (a fifth kind of speech front end) | Optional. CommandSwarm's front end is covered in the prose. |
| F-13 (Lim "zero-shot") | Keep. It is a fair inference, and issue 07 confirmed it. The source's own wording is an acceptable alternative. |
| F-21 (Reynolds' rule names) | Optional NIT. It does not collide with ingenieur_bg.py's moved-passage check, whose needle is a different phrase. |
| n1 (sentences over 40 words) | The rewritten paragraphs have none. The remaining ones (l.19-22, l.77-81, l.240-242, l.309-311, l.398-400) are untouched NITs. |
| n7, n9, n10, n11, n12 | Wording NITs; safe; not tested. n12 touches ch3_architecture.tex (outside this issue). |

No MINOR is wrong in substance. The only ones that should be raised are covered by BLOCKERs or
MAJORs here: m8 (the conceded-preemption clause is now needed for G2 to be true) and m12 (once
MIRA's 466 ms sits in that column).

## 5. Anchor safety and test record

- **Script, scratch copy:** the unmodified chapter gives 0 FAIL, 3 WARN, 70 PASS. The BLOCKER/MAJOR
  set alone (23 edits) gives **0 FAIL, 3 WARN, 70 PASS**, and the same with the MINORs of §4 (37
  edits). The three WARNs are unchanged in kind: untraced numbers (9 -> 10: the new 466/450/100/24
  sit on lines with no paper-number anchor), and the UAV/LLM heading and model-name hits.
- **All 32 paper-number anchors survive** (32 PASS). The rewrites near anchors keep them intact:
  `106~ms on a` (l.171 untouched; a second match at the new l.239 is harmless), `1{,}006~ms to
  81~ms` (F-20 appends after it), `34~s for 3 drones` and `above 100~s` (prose l.257-258 untouched;
  M6 no longer repeats them), `Q5\_K\_M` (kept inside the Sikorski rewrite), `temperature of 0.2`
  and `in 38\%` (the baseline paragraph is untouched apart from m11).
- **Structure checks:** Synthesis, Conceded prior art, `Gap G1,`/`Gap G2,`/`Gap G3,` lead-ins,
  tab:lim-positioning and `\cite{lim2025}` in the gaps: all untouched. Each gap still `\ref`s its
  closers: G1 sec:membership-rule + sec:contributions; G2 sec:dual-path + sec:latency-budget; G3
  sec:resource-allocation. G2 and G3 also add sec:latency-experiment, which resolves. There is
  still one table and one Critical comparison per theme section, and every "This work &" row is kept.
- **No new source in the gaps:** the gaps now cite silva2026, lim2025, commandswarm2026,
  torkamani2025 and llm2swarm2024, and each is cited in a theme section (Torkamani in sec:voice-uav
  and sec:speech-components; LLM2Swarm in sec:swarm-control-sota l.252). No key outside
  references.bib is used.
- **Positioning WARN:** no theme-section sentence gains "this work/system/design/document". The
  new "this one" in G2 is inside Research gaps.
- **Codes:** the new text never types "C4" (the CODES regex would demand a definition) and says
  "the first clause of the contribution", as before.
- **selftest mutations:** `\section{Swarm control}` and `\paragraph{Conceded prior art.} Three`
  (selftest.py l.37, l.51) are unchanged (grep: 1 hit each). The full selftest could not run in the
  scratch copy (master_ch1.py needs `spikes/`, which was not copied), so this is environment only.
  ingenieur_bg.py in the scratch copy: 0 FAIL.
- **Build:** `latexmk main_ingenieur.tex` in the scratch copy gives rc=0, no undefined reference or
  citation, and no overfull box. Pages 38-43 were rendered and inspected. tab:soa-swarm and
  tab:soa-speech fit their columns: "By design; not yet tested" wraps to three lines in the 1.4 cm
  Offline column, and the Torkamani row fits.
- **Sentence length:** no sentence in the rewritten blocks exceeds 40 words (checked with a script
  that strips cites and refs).
- The tested edit set is `patch_issue19.py` in the session scratchpad. It is ephemeral; the text in
  §3 is the record.

## 6. UNVERIFIED

- **Henry et al., hardware of the 202 ms cascade and of the 7 ms direct path.** The paper names only
  the RTX 2000 Ada, in its fine-tuning setup, and says "(106 ms on CPU)". "7 ms on a GPU" stays an
  inference (citation F-23); my wording does not rest on the cascade's host.
- **MIRA's recognition host.** Table 3 calls endpointing "Local ASR endpointing", but the recogniser
  is a "provider-specific" backend. The Offline dash is kept. The claim that the gate "states no
  latency target" rests on a full-text grep for budget/threshold/target: the paper has only the
  450 ms confirmation threshold and ROSCO's emission budget, and "bounded-latency interruption" in
  §7 names no figure.
- **Whether MIRA's gate runs while its language model decodes** is not stated. G2 does not claim
  otherwise.
- **Raspberry Pi 5 and "without a GPU".** The Pi 5 has a VideoCore GPU that llama.cpp does not use.
  The phrase "\gls{sbc} without a \gls{gpu}" is the document's established usage and is not changed
  here, but a jury member could raise it. Issue 20 could consider "without a compute \gls{gpu}".
- **Iannoli's guardrails.** One sentence says they "constrain or halt interactions in response to
  invalid requests or unsafe conditions". Whether any guardrail halts deterministically, without the
  model, is not described. "re-prompt the model" follows §III's definition.
- **Landau and van Delden, SkySim 34 s vs 50 s:** as in the citation report (not re-opened).
