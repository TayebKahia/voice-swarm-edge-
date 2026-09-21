# Citation agent report: thesis/ingenieur/ch3_state_of_the_art.tex (issue 19, D5 only)

Date: 2026-09-26. Chapter at commit `c3fe8d5` plus the uncommitted working-tree edit (512 lines,
29 distinct keys resolved per the script, 89 citation-sheet sites, five tables).
Pre-review script: `tools/review/ingenieur_ch2.py` -> 0 FAIL, 3 WARN, 70 PASS.

Sources opened this round (full text unless stated). The arXiv HTML full text was downloaded and
grepped locally for CommandSwarm (2605.07764), MIRA (2609.24547), RelayS2S (2603.23346), Henry
(2606.24910), Simões (2407.08658), TypeFly (2312.14950), Chat with UAV (2512.08145), Phadke
(2410.17602), Silva and Burke (2601.15486), Lim (2506.07509), Sikorski (2405.17670), Torkamani
(2512.12769), SwarmChat (2509.16920), Iannoli (2605.03788), Sahai (2304.01905), LLM2Swarm
(2410.11387), SayCan (2204.01691), Code as Policies (2209.07753), Vemprala (2306.17582), Contreras
(2009.04215, the arXiv version of the Computers article), Javaid (2405.01745), and Whisper
(2212.04356). The math that the HTML renders as MathML was read from its `alttext`, which is where
TypeFly's 62 %/1.5 s and Henry's 7/106/202 ms live. For SkySim (2602.01226) there is no HTML, so
the PDF was read with pdftotext. Reynolds (1987) was read in the author's full-text copy (cs.toronto.edu
siggraph97 course notes). Koren and Borenstein (1991) was read as a PDF from the CMU motion-planning
mirror. For openWakeWord and Silero VAD the READMEs were read, plus `src/silero_vad/utils_vad.py`;
for whisper.cpp the README. Bibliographic metadata came from Crossref for all 10 DOIs, from the
arXiv abs-page `citation_*` tags for 13 arXiv keys, and from Semantic Scholar for the Javaid abstract.
Landau and van Delden: ACM DL and Semantic Scholar both refuse the abstract, so only the ACM
abstract as quoted by the search index was available (see UNVERIFIED).
`.scratch/thesis-bibliography/ingenieur-candidates.md` was used for leads only.

Reuse of issue 07. No per-site record of the issue-07 check survives (there is no
`agents/07-*` folder; issue 07's closing comment and commit `bbd113b` summarise it). A sentence
whose wording is unchanged from `git show c3fe8d5~1:thesis/ingenieur/ch3_state_of_the_art.tex`
is marked **(07)**. Its verdict is the issue-07 verdict, re-read against the source this round, and
where the re-read disagrees this report says so. Every table cell of tab:soa-dual-path,
tab:soa-swarm and tab:soa-speech, every critical comparison, the Synthesis, and G1-G3 are new or
changed, so all of them were verified from scratch.

## 1. Verdict

The chapter needs fixes before it is ready. The problems are few and contained: every one of the
32 quoted paper numbers is found at the stated value in its primary source, bibliography metadata
agrees with the primary records for all keys, and most table cells are right. There are
**five BLOCKERs**: three new research-gap or comparison claims that a source refutes, one wrong
table cell, and one false recency claim. The most consequential are these. Gap G2 says the
review "established no latency" for MIRA's stop gate, but MIRA's Table 3 reports it: 466 ms median
from speech onset to the abort command. G2 and the first critical comparison also say that no system
in tab:voice-uav-survey handles a stop separately from the interpreting path, but Silva and Burke
exercise and report an out-of-band radio kill, and Lim et al. a human switch to position mode.
The fifth BLOCKER is new text in G3, which attaches the "presumes the network" claim to Torkamani
and Zarin's *edge* tier; the paper says that tier works without internet. There are also 2 MAJOR
findings: tab:soa-speech omits Torkamani and Zarin's offline recogniser, which falsifies "only Sikorski
et al. state offline recognition", and the guardrails of Iannoli et al. are being counted as
"deterministic, automated checks". Every fix is a local rewording or a cell edit, and the replacement
text is given in §5.

## 2. Table-cell verification

Verdict key: OK = the source states it; PARTIAL = supported with a nuance; WRONG = source does not
support (BLOCKER); dash = not a finding; "could fill" = source plainly states the property (MINOR).

### 2a. tab:voice-uav-survey (l.104-134)

The table was kept from the issue-07 version minus the Simões and Henry rows. The cells are
unchanged, so the verdicts are **(07)**; all were re-read.

| Table | Row | Column | Cell text | Verdict | Evidence quote |
|---|---|---|---|---|---|
| voice-uav | Landau and van Delden | Input | Speech | OK (07) | ACM abstract (search-index copy): control "using simple voice commands" |
| voice-uav | Landau and van Delden | Target | One UAV | OK (07) | tested "using a DJI Phantom 4 drone" |
| voice-uav | Landau and van Delden | Language path and host | Nuance recogniser; no language model | OK (07) | "Nuance speech recognition platform" (host not stated; cell correctly avoids "cloud") |
| voice-uav | Landau and van Delden | Check | Regular-expression command language | OK (07) | "control language defined using regular expressions" |
| voice-uav | Contreras et al. | Input | Speech | OK | voice commands to the drone |
| voice-uav | Contreras et al. | Target | One simulated UAV | OK | "Simulated quadrotor drone in V-REP" |
| voice-uav | Contreras et al. | Language path | Cloud recogniser; no language model | OK | "cloud-based speech recognition system" (Google Cloud Speech) |
| voice-uav | Contreras et al. | Check | Matching against domain phonemes | OK | "improved by a domain-based language", phoneme matching |
| voice-uav | Vemprala et al. | Input | Text | OK (07) | prompts and textual feedback, user "on the loop" |
| voice-uav | Vemprala et al. | Target | Robots, including aerial | OK (07) | AirSim and real-drone tasks (66 drone/AirSim mentions) |
| voice-uav | Vemprala et al. | Language path | ChatGPT, remote | OK (07) | ChatGPT (hosted service) |
| voice-uav | Vemprala et al. | Check | Human on the loop | OK | "user on the loop to evaluate the output's quality and safety" (Fig. 2) |
| voice-uav | TypeFly | Input | Text | OK | "a TypeFly user provides a task description in English" |
| voice-uav | TypeFly | Target | One UAV | OK | one drone, edge server |
| voice-uav | TypeFly | Language path | GPT-4, remote | OK | "its use of GPT4"; large models need data-centre GPU servers |
| voice-uav | TypeFly | Check | Plan language; no check stated | OK (07) | MiniSpec plan language; no pre-execution check described |
| voice-uav | Silva and Burke | Input | --- | dash | (operator converses with an MCP host application) |
| voice-uav | Silva and Burke | Target | UAVs | OK | "commanded three quadcopters"; ArduPilot and PX4 SITL |
| voice-uav | Silva and Burke | Language path | Mostly cloud models | OK | core of "eleven direct-API models across four providers"; plus 7 broker-routed and a local laptop arm |
| voice-uav | Silva and Burke | Check | Server-side validation; geofence | OK | "server-side pipeline that no tool can bypass"; "independent, server-side geofence" |
| voice-uav | Lim et al. | Input | Text | OK | mission starts by "publishing a ROS2 string message" |
| voice-uav | Lim et al. | Target | One UAV | OK | single custom quadcopter |
| voice-uav | Lim et al. | Language path | Open models, local GPU workstation | OK | RTX 3080Ti workstation hosts Ollama "as a remote server" on the LAN |
| voice-uav | Lim et al. | Check | Prompt format; temperature 0.2 | OK | "sampling temperature ... held at a low value of 0.2"; "Turn"/"Move" format |
| voice-uav | Sikorski et al. | Input | Speech | OK | "Convert spoken command to text using VOSK" |
| voice-uav | Sikorski et al. | Target | One ground robot | OK | ELEGOO Smart Car, a wheeled mobile robot |
| voice-uav | Sikorski et al. | Language path | GPT-4-Turbo, remote, or LLaMA 2-7B on a control computer | OK | OpenAI API vs llama.cpp LLaMA 2 7B; Dell Precision 3660 tower |
| voice-uav | Sikorski et al. | Check | --- | dash; could fill (MINOR) | Algorithm 1: "if LLM_Return is Valid then Robot_Command <- LLM_Return" (validity test, unspecified) |
| voice-uav | Torkamani and Zarin | Input | Speech | OK | "80 audio files, each containing an English-spoken command" |
| voice-uav | Torkamani and Zarin | Target | IoT devices | OK | smart lights, speakers |
| voice-uav | Torkamani and Zarin | Language path | Edge (Jetson) or cloud, routed at run time | OK | "Jetson Mate Xavier NX"; GPT-3.5-turbo online, TinyLlama-1.1B offline |
| voice-uav | Torkamani and Zarin | Check | --- | dash; **could fill** (MINOR) | "rule-based command validation and repair component" (action, device, index layers) |
| voice-uav | SwarmChat | Input | Speech, text, teleoperation | OK (07) | "text, voice, or teleoperation" |
| voice-uav | SwarmChat | Target | Robot swarm | OK | TurtleBots over ROS2 |
| voice-uav | SwarmChat | Language path | Modules based on language models; --- | OK (07) | "four LLM-based modules"; LLM and host never named |
| voice-uav | SwarmChat | Check | Rule-based intent keywords | PARTIAL (07) | "rule-based checks to infer user intent from keyword sets": an intent step, admitted by the caption's "constraint" clause |
| voice-uav | Iannoli et al. | Input | Text | OK | mission "expressed in natural language" (user prompt); no speech |
| voice-uav | Iannoli et al. | Target | UAV swarm | OK | ArduPilot SITL, one instance per drone |
| voice-uav | Iannoli et al. | Language path | Six general-purpose models; --- | OK | GPT 5.2, DeepSeek V3.2, Claude Haiku 4.5, Qwen3 8B, GLM, Grok |
| voice-uav | Iannoli et al. | Check | Planning tools; runtime guardrails | OK | "Task-specific planning tools and runtime guardrails" (but see M-2 on what a guardrail is) |
| voice-uav | SkySim | Input | Text | OK | "natural language command" typed into the prompt; no speech path anywhere; "multi-modal inputs" are future work |
| voice-uav | SkySim | Target | UAV swarm, 3--30 | OK | "Swarm sizes of (N = 3, 10, and 30)" |
| voice-uav | SkySim | Language path | Gemini 3.5 Pro, remote | OK | "reliance on cloud-based inference (Google Gemini API)" |
| voice-uav | SkySim | Check | Waypoint bounds; potential-field layer | OK; could add | geofence rejection and APF; also "deterministically parsed via Abstract Syntax Tree for validation" |
| voice-uav | CommandSwarm | Input | Speech or text | OK | "from speech or text commands" |
| voice-uav | CommandSwarm | Target | Robot swarm | OK | Violet swarm simulator |
| voice-uav | CommandSwarm | Language path | Open models of 6.7--14B, 4-bit; --- | OK | "eleven open 6.7B–14B parameter LLMs, all using 4-bit quantization"; no hardware named |
| voice-uav | CommandSwarm | Check | Primitive whitelist; parser; safety classifier | OK | whitelist, "deterministic parser validation", "Llama-Guard-style safety classifier" |

### 2b. tab:soa-dual-path (l.196-220), all new

| Table | Row | Column | Cell text | Verdict | Evidence quote |
|---|---|---|---|---|---|
| dual-path | Simões et al. | Fast; slow | Direct speech-to-command classifier; recognition then a language model | OK | Pipeline 2 "direct mapping of audio inputs to drone commands"; Pipeline 1 wav2vec2 + "LLM pretrained from Llama3" |
| dual-path | Simões et al. | Arrangement | Alternatives | OK | three pipelines built and compared |
| dual-path | Simões et al. | Fast path decides | The command | OK | predicts one of UP/DOWN/FORWARD/BACKWARD/RIGHT/LEFT |
| dual-path | Simões et al. | Purpose | --- | dash | |
| dual-path | Simões et al. | Latency | 0.021 s; 1.233 s | OK | Table 5: Direct 0.99 / 0.021 s; STT and LLM 0.81 / 1.233 s |
| dual-path | Henry et al. | Fast; slow | Transcription-free intent recogniser; Whisper then CamemBERT-Large | OK | "without requiring transcription at inference time"; "Cascade baseline (Whisper + CamemBERT-Large)" (Whisper Large-v2) |
| dual-path | Henry et al. | Arrangement | Alternatives | OK | "systematic comparison against cascade baselines" |
| dual-path | Henry et al. | Fast path decides | The intent | OK | 7 intent classes |
| dual-path | Henry et al. | Purpose | --- | dash | |
| dual-path | Henry et al. | Latency | 7 ms (GPU), 106 ms (CPU); 202 ms | OK (NIT) | "93 % accuracy at 7 ms (106 ms on CPU)"; cascade 202 ms. "GPU" is implied, since the only GPU named is the RTX 2000 Ada |
| dual-path | Sahai et al. | Fast; slow | Cheaper attention branch; full branch, in one recognition model | OK | "select which branch of its attention networks to execute for an input audio frame"; small MHA for lead-in/WW frames |
| dual-path | Sahai et al. | Arrangement | One model, per frame | OK | "for an input audio frame" |
| dual-path | Sahai et al. | Fast path decides | Which branch runs on a frame | **PARTIAL (MINOR)** | the branch is chosen by "exploiting WW spotting", not by the cheaper branch; the cheaper branch biases lead-in frames toward wake-word embeddings |
| dual-path | Sahai et al. | Purpose | Computation | OK (NIT) | "saving runtime compute cost as defined by FLOPs"; the paper also aims to boost wake-word accuracy |
| dual-path | Sahai et al. | Latency | --- | dash | FLOPs only, no latency |
| dual-path | RelayS2S | Fast; slow | Duplex speech-to-speech draft; recognition then a language model | OK | fast path "a duplex S2S model"; slow "a cascaded ASR → LLM pipeline" |
| dual-path | RelayS2S | Arrangement | Concurrent; learned verifier | OK | "runs two paths in parallel upon turn detection"; "lightweight learned verifier gates the handoff" |
| dual-path | RelayS2S | Fast path decides | The opening of a response, if committed | OK | "drafts a short response prefix"; verifier commits or falls back |
| dual-path | RelayS2S | Purpose | Responsiveness | OK | "low-latency response onset" |
| dual-path | RelayS2S | Latency | 81 ms; 1,006 ms at p90, first chunk | OK (NIT) | "P90 first-chunk latency of 81 ms ... compared with 1,006 ms"; on synthetic dialogues, excluding TTS and network |
| dual-path | MIRA | Fast; slow | Barge-in gate on voice activity; deliberative turn decisions | OK | "local VAD-based gate"; "Deliberative Turn Arbiter" |
| dual-path | MIRA | Arrangement | Concurrent; preemption | OK | gate aborts "Meanwhile, audio is sent incrementally to the ASR backend" |
| dual-path | MIRA | Fast path decides | One action: abort the response and stop motion | OK | "marks the current response as aborted, clears pending TTS output ... terminates the ongoing robot motion" |
| dual-path | MIRA | Purpose | Barge-in | OK | "To minimize barge-in latency" |
| dual-path | MIRA | Latency | --- | dash; **could fill**, see B-1 | Table 3: "Deterministic Interruption Preemption, speech_started → abort_cmd_sent, 466 ms" (P50); slow path "LLM First-Token Latency 1.62 s" |
| dual-path | Chat with UAV | Fast; slow | None: planning agent and execution agent, both language models | OK | "two independent LLM agents (a task planning agent, and an execution agent)" |
| dual-path | Chat with UAV | Arrangement | Split by function | OK | planning vs execution |
| dual-path | Chat with UAV | decides / purpose / latency | --- | dash | |

### 2c. tab:soa-swarm (l.266-288), all new

| Table | Row | Column | Cell text | Verdict | Evidence quote |
|---|---|---|---|---|---|
| swarm | Reynolds | Coordination | Three local rules: separation, velocity matching, centring | OK (NIT) | "Collision Avoidance ... Velocity Matching ... Flock Centering", applied to "nearby flockmates". The source says "collision avoidance", not "separation" |
| swarm | Reynolds | Separation | Collision-avoidance rule | OK | "Collision Avoidance: avoid collisions with nearby flockmates" |
| swarm | Reynolds | Role of LM | None | OK | |
| swarm | Reynolds | Evaluation | --- | dash | |
| swarm | Koren and Borenstein | Coordination | --- | dash | |
| swarm | Koren and Borenstein | Separation | Potential field; failure modes analysed | OK | §5 "problems that are inherent to PFMs": traps, no passage between closely spaced obstacles, two oscillation modes |
| swarm | Koren and Borenstein | Role / Evaluation | None / --- | OK / dash | |
| swarm | Strobel et al. | Coordination / Separation | --- / --- | dash | |
| swarm | Strobel et al. | Role of LM | Indirect: synthesises and validates controllers; or direct: one instance per robot | OK | "LLMs are used to synthesize and validate the robot controllers"; "each robot locally executes a separate LLM instance" |
| swarm | Strobel et al. | Evaluation | Mainly conceptual | OK; **could fill** (MINOR) | "our mainly conceptual contribution" (abstract). What was actually exercised: ARGoS showcases with each robot on an external LLM, plus a preliminary TinyLlama/Ollama test on a Raspberry Pi 5 at 10-12 tokens/s |
| swarm | SkySim | Coordination | Waypoints from the planner | OK | "translates user commands ... into spatial waypoints" |
| swarm | SkySim | Separation | Potential-field layer at 20 Hz; speed saturated at 0.5 m/s | OK | "control loop operates at 20 Hz"; "saturated at vmax = 0.5 m/s" |
| swarm | SkySim | Role of LM | Remote planner above the control layer; geofence in the planner | OK | "LLM Planner Node enforces a strict virtual geo-fence" |
| swarm | SkySim | Evaluation | Gazebo with ROS 2; 3, 10 and 30 drones | OK | "Gazebo Harmonic Environment and ROS2 Jazzy"; N = 3, 10, 30 |
| swarm | Iannoli et al. | Coordination / Separation | --- / --- | dash | |
| swarm | Iannoli et al. | Role of LM | General-purpose models with planning tools and runtime guardrails | OK | abstract |
| swarm | Iannoli et al. | Evaluation | ArduPilot software-in-the-loop; four missions | OK | "ArduPilot Software-In-The-Loop (SITL)"; "four swarm missions" |
| swarm | CommandSwarm | Coordination | Behaviour trees of whitelisted primitives | OK | "arrange a fixed set of primitives into a valid BT" |
| swarm | CommandSwarm | Separation | --- | dash | |
| swarm | CommandSwarm | Role of LM | Generates the tree; parser and safety classifier gate it | **WRONG (BLOCKER B-4)** | the classifier screens the *command* "Before generation"; only the parser gates the tree ("one at the command level and one at the executable-plan level") |
| swarm | CommandSwarm | Evaluation | Trees scored, not executed | OK | future work: BTs "executed and scored according to task success rather than only text similarity and parser validity" |

### 2d. tab:soa-speech (l.336-361), all new

| Table | Row | Column | Cell text | Verdict | Evidence quote |
|---|---|---|---|---|---|
| speech | Landau and van Delden | Recogniser | Nuance platform | OK | abstract |
| speech | Landau and van Delden | Offline / latency | --- / --- | dash | |
| speech | Landau and van Delden | Transcription-free | No | OK | recogniser output matched by regular expressions |
| speech | Contreras et al. | Recogniser | Cloud recogniser, corrected against domain phonemes | OK; could name | Google Cloud Speech through the Web Speech API |
| speech | Contreras et al. | Offline | No | OK | cloud service |
| speech | Contreras et al. | Transcription-free | No | OK | transcription then phoneme matching |
| speech | Contreras et al. | Latency | --- | dash | |
| speech | Simões et al. | Recogniser | Recognition then a language model | OK; could name | wav2vec2-large-xlsr-53-portuguese, then a Llama3-based LLM |
| speech | Simões et al. | Offline | --- | dash | |
| speech | Simões et al. | Transcription-free | Direct classifier | OK | "without requiring a text intermediary" |
| speech | Simões et al. | Latency | Whole pipeline 1.233 s (cascade), 0.021 s (direct); --- | OK | Table 5 "Inference Time (in seconds)" per pipeline |
| speech | Henry et al. | Recogniser | Whisper, then CamemBERT-Large | OK | Whisper Large-v2 + CamemBERT-Large |
| speech | Henry et al. | Offline | --- | dash | |
| speech | Henry et al. | Transcription-free | Direct intent recogniser | OK | |
| speech | Henry et al. | Latency | 202 ms (cascade); 7 ms on a GPU, 106 ms on a CPU (direct) | OK (NIT on "GPU") | Table I; §III-A |
| speech | Sikorski et al. | Recogniser | VOSK | OK | "Speech recognition module (VOSK)" |
| speech | Sikorski et al. | Offline | Yes | OK | Fig. 1 caption "offline speech recognition" |
| speech | Sikorski et al. | Transcription-free | No | OK | |
| speech | Sikorski et al. | Latency | --- | dash | |
| speech | CommandSwarm | Recogniser | SeamlessM4T v2-large; Whisper-medium rejected | OK | "SeamlessM4T for spoken commands" chosen over Whisper-medium |
| speech | CommandSwarm | Offline | Not claimed | OK | audio "captured from a web microphone"; only "should be processed locally when possible" |
| speech | CommandSwarm | Transcription-free | No | OK | speech translation to English text |
| speech | CommandSwarm | Latency | About 4.0 s and 5.2 s per utterance; unstated hardware | OK | "approximately 5.2s per utterance" (Whisper-medium), "approximately 4.0s" (SeamlessM4T); no hardware named |
| speech | MIRA | Recogniser | Not named | OK | "ASR backend", "provider-specific final ... transcription" |
| speech | MIRA | Offline | --- | dash | |
| speech | MIRA | Transcription-free | Gate on voice activity | OK; could name | "local VAD-based gate", footnoted to github.com/snakers4/silero-vad |
| speech | MIRA | Latency | --- | dash; **could fill** (MINOR) | Table 3 P50: "Streaming ASR Endpointing 10.0 ms", preemption 466 ms, on the Astribot S1 deployment |
| speech | *(missing row)* Torkamani and Zarin | --- | --- | **omission (MAJOR M-1)** | "transcribed by an offline ASR module ... 8-bit tiny ASR engine based on the faster-whisper implementation", on a Jetson |

### 2e. tab:lim-positioning, Lim et al. column (l.462-485); moved unchanged from the old §2.2 (07)

| Table | Row | Column | Cell text | Verdict | Evidence quote |
|---|---|---|---|---|---|
| lim | Input | Lim et al. | Text message on ROS 2; no speech | OK (07) | "publishing a ROS2 string message" |
| lim | Language model | Lim et al. | Gemma3, Qwen2.5, Llama-3.2, DeepSeek-LLM | OK; could add sizes (NIT) | Table I: Gemma3 4B, Qwen2.5 3B, Llama-3.2 3B, DeepSeek-LLM 7B |
| lim | Adaptation | Lim et al. | Zero-shot prompting | PARTIAL (MINOR) | the paper says neither "zero-shot" nor "no fine-tuning"; it prompts off-the-shelf Ollama models at "system-level", and lists an "absence of ablation studies examining ... few-shot examples". Supported as an inference |
| lim | Output constraint | Lim et al. | Temperature 0.2; prompt fixing the command format | OK | "held at a low value of 0.2"; outputs must be "Turn" or "Move" |
| lim | Inference hardware | Lim et al. | RTX 3080 Ti workstation on the local network | OK | "RTX 3080Ti (16 GB) GPU ... acts as a remote server" |
| lim | Vehicles and task | Lim et al. | One quadcopter flown to a goal | OK | "guiding a quadcopter ... to a predefined goal location" |
| lim | Perception | Lim et al. | Vision-language model detects the target | OK | VLM "binary 'Yes' or 'No'" on object presence |
| lim | Stop | Lim et al. | Human operator switches to position mode | OK | "operator will switch the flight mode to POSITION mode" (real-world runs) |
| lim | Reported | Lim et al. | Valid commands; task success; detection rate | OK | Table I columns; latency explicitly not measured |

## 3. Prose citation sites (the report's sheet, 89 rows)

| # | Key | file:line | Claim | Verdict | Evidence |
|---|---|---|---|---|---|
| 1 | javaid2024 | ch3:36 | field moved to LLMs; a recent survey maps it | SUPPORTS (07), framing | abstract: "We comprehensively review LLM architectures ... state-of-the-art LLM-based UAV architectures" |
| 2 | landau2017 | 47 | Nuance output -> regex -> DJI Phantom 4 | SUPPORTS (07) | ACM abstract (search-index copy) |
| 3 | contreras2020 | 51 | cloud recogniser, phoneme matching, 74.81 -> 93.33 %, distortion levels | SUPPORTS (07) | "cloud-based approach achieves 74.81% ... 93.33%"; "different levels of distortion" |
| 4 | saycan2022 | 56 | value functions constrain proposals | SUPPORTS (07) | value functions "provide the grounding"; affordance function |
| 5 | codeaspolicies2023 | 59 | assumes instructions feasible; cannot tell a priori | SUPPORTS (07) | "assumes all given instructions are feasible, and we cannot tell if a response will be correct a priori" |
| 6 | chatgptrobotics2024 | 63 | human on the loop; not full control | SUPPORTS (07) | "should not be given full control of the robotics pipeline" |
| 7 | typefly2024 | 70 | latency grows with plan; MiniSpec, up to 62 %, < 1.5 s, 11 tasks, GPT-4, text | SUPPORTS (07) | "latency that is proportional to the length of the output plan"; alttext 62\%, 1.5s; "benchmark of 11 tasks" |
| 8 | chatwithuav2025 | 71 | planning vs execution, two LLM agents | SUPPORTS (07) | abstract |
| 9 | phadke2024 | 72 | modular template framework, LLMs + simulators | SUPPORTS (07) | "template development framework"; "integrate existing LLM models and popular robotic simulation platforms" |
| 10 | silva2026 | 76 | broadest on its axes; > 1,000 flights; 110 trials; 3 quadcopters; untrusted commander, server-side | SUPPORTS (07) | "On the axes it measures, this is to our knowledge the broadest evaluation" |
| 11 | lim2025 | 78 | open models via Ollama, local GPU, one PX4 quadcopter "to a goal found by a vision-language model" | PARTIAL (MINOR F-12) | the goal coordinates come in the operator's text message; the VLM only answers whether the target is in view. l.455-456 states this correctly |
| 12 | sikorski2025 | 87 | GPT-4-Turbo vs LLaMA 2-7B Q5_K_M offline on control computer; significant limitations | SUPPORTS (07) | abstract, verbatim phrase |
| 13 | torkamani2025 | 89 | routing on CPU load, temperature, network latency; Jetson | SUPPORTS (07) | abstract |
| 14 | swarmchat2025 | 94 | rule-based keyword intent, listed limitation; preliminary evaluation | SUPPORTS (07) | "relies on rule-based intent recognition"; evaluation "still in its initial stages" |
| 15 | iannoli2026 | 99 | struggle without grounding; tools and guardrails improve robustness | SUPPORTS (07) | abstract, near-verbatim |
| 16 | skysim2026 | 100 | cloud model plans waypoints above potential field | SUPPORTS | Summary; §2.2 |
| 17 | commandswarm2026 | 101 | speech/text -> BTs, deterministic parser gate | SUPPORTS | abstract |
| 18-29 | (table rows) | 118-129 | tab:voice-uav-survey cells | see §2a | |
| 30 | simoes2024 | 167 | 0.81 at 1.233 s; 0.99 at 0.021 s | SUPPORTS (07) | Table 5 |
| 31 | henry2026 | 172 | 82 % / 59 % full set; 7 ms GPU (106 ms CPU); 14-point gap attributed to architecture | SUPPORTS (07) | Table I; "stems from the cascade architecture itself rather than transcription errors" |
| 32 | dualattn2023 | 176 | WW frames get the cheaper branch, to save compute | SUPPORTS (07) | small MHA trained "for the lead-in segments"; "reduce the compute cost ... for WW audio frames" |
| 33 | relays2s | 181 | verifier commits fast draft; p90 1,006 -> 81 ms | SUPPORTS (07) | abstract (NIT: on synthetic dialogues, excluding TTS/network) |
| 34 | mira | 183 | dual-timescale policy; barge-in preemption + deliberative decisions | SUPPORTS (07) | abstract, verbatim |
| -- | (mira, uncited continuation) | 183-189 | short interruptible prefix; control-rate safety layer; VAD gate; abort, stop TTS, end motion, hold last safe pose; single companion; models and host unnamed | SUPPORTS (07) | 15-frame (0.50 s) commitment; 250 Hz joint loop; "holds the last safe pose or invokes the configured fallback policy"; "ASR backend"/"provider-specific" |
| 35 | chatwithuav2025 | 192 | division by role; both branches at LM latency | SUPPORTS (07) | two LLM agents via API |
| 36-41 | (table rows) | 210-215 | tab:soa-dual-path cells | see §2b | |
| 42 | reynolds1987 | 243 | Reynolds' flocking rules as a foundation | SUPPORTS | three rules, "nearby flockmates" |
| 43 | koren1991 | 245 | failure modes inherent to the method | SUPPORTS | title and §5 "problems that are inherent to PFMs" |
| 44 | llm2swarm2024 | 252 | indirect/direct; "mainly conceptual" | SUPPORTS (07) | abstract; §1 |
| 45 | skysim2026 | 255 | Gemini 3.5 Pro above APF at 20 Hz, repulsion, 0.5 m/s, N = 3/10/30, Gazebo + ROS 2 | SUPPORTS | §2.2, §3 |
| -- | (skysim, uncited continuation) | 255-259 | geofence in planner -> position hold; malformed/timeout keeps previous command; 34 s -> 50 s, > 100 s, "unsuitable for time-critical" | SUPPORTS (07); NIT | "immediately rejected, triggering a position-hold fallback"; "holds the position of the previous command" (ambiguous wording, see F-19); §3.3 "34s to 50s"; "outliers > 100s"; "currently unsuitable for time-critical missions" |
| 46 | commandswarm2026 | 261 | PyGame simulator; scored by text metrics and parser acceptance, not executed | SUPPORTS (07) | "Violet simulator, a lightweight PyGame-based swarm simulation environment"; future-work sentence |
| 47 | iannoli2026 | 263 | ArduPilot SIL with planning tools and guardrails | SUPPORTS | §V "ArduPilot Software-In-The-Loop (SITL)" |
| 48-53 | (table rows) | 278-283 | tab:soa-swarm cells | see §2c (B-4 at 283) | |
| 54-55 | oww, silero | 313-314 | no peer-reviewed description found; software releases | SUPPORTS (07) (a silence claim; the READMEs cite no paper beyond Silero's software citation) | Silero README citation block is a GitHub software entry |
| 56-57 | landau2017, contreras2020 | 318-319 | Nuance platform; cloud recogniser corrected against domain phonemes | SUPPORTS | as #2, #3 |
| 58 | sikorski2025 | 320 | offline recognition with VOSK | SUPPORTS | Fig. 1 caption; Algorithm 1 |
| 59 | commandswarm2026 | 322 | SeamlessM4T v2-large ~4.0 s chosen, unstated hardware; Whisper-medium speech translation ~5.2 s rejected | SUPPORTS (07) | §IV-B; §V-D |
| 60 | henry2026, simoes2024 | 324 | Henry cascade transcribes with Whisper; both direct paths decide without transcript | SUPPORTS | as #30-31 |
| 61 | mira | 325 | gate reacts to voice activity alone | SUPPORTS | "local VAD-based gate" |
| 62 | whisper | 328 | 680,000 h weakly supervised; tiny.en 39 M | SUPPORTS (07) | "680,000 hours"; Table 1 "Tiny 39M" (English-only .en variants share the size) |
| 63 | whispercpp | 329 | C/C++ on CPU, no Python runtime | SUPPORTS (07) | README: "Plain C/C++ implementation without dependencies"; "Support for CPU-only inference" |
| 64 | oww | 332 | frozen front end, one embedding per 80 ms frame, small heads for arbitrary phrases | SUPPORTS (07) | "process a stream of audio data in 80 ms frames"; "small model on top of the frozen shared feature extractor" |
| 65 | silero | 333 | pre-trained neural VAD, ONNX, 32 ms windows, recurrent state | SUPPORTS (07) | `utils_vad.py`: `num_samples = 512 if sr == 16000` (= 32 ms), `state` tensor carried between calls; README says only "30+ ms" chunks (NIT) |
| 66-72 | (table rows) | 350-356 | tab:soa-speech cells | see §2d | |
| 73 | iannoli2026, commandswarm2026 | 384 | "deterministic, automated checks appear in recent swarm systems" | **PARTIAL (MAJOR M-2)** for iannoli2026 | guardrails are "short, targeted prompt fragments ... injected dynamically" that "instruct the LLM to re-evaluate". The trigger is automated, the remedy is a prompt, not a check between output and vehicle. SUPPORTS for commandswarm2026 |
| 74 | simoes2024, henry2026 | 386 | transcription-free cuts latency by one to two orders at no accuracy cost | SUPPORTS | 1.233/0.021 = 59x; 202/7 = 29x; accuracy 0.81 -> 0.99, 79 -> 93 % (59 -> 82 % full set) |
| 75 | relays2s, mira | 387 | fast paths concurrent with slow ones, gated by a verifier or preemption | SUPPORTS | "two paths in parallel"; VAD gate + ASR "Meanwhile" |
| 76 | skysim2026 | 388 | LM planners placed above a potential field that keeps vehicles apart | SUPPORTS | |
| 77 | sikorski2025 | 389 | offline speech; quantised LM offline on control computer | SUPPORTS | |
| 78 | commandswarm2026 | 395 | spoken commands to a group, output checked deterministically before effect | SUPPORTS (07) | parser before execution. NIT: "group of robots" (the Violet swarm agents are robots, not vehicles) |
| -- | (commandswarm, uncited continuation) | 396-397 | parser acceptance and safety filtering remain necessary gates | SUPPORTS (07) | abstract, verbatim |
| 79 | skysim2026 | 400 | planner/lower layer at the control rate; position-hold fallback on rejected waypoint | SUPPORTS (07) | §2.2 |
| 80 | mira | 402 | uninterpreted stop + hold; preemption; control-rate safety layer | SUPPORTS (07) | §3.2, §3.4 |
| 81 | landau2017, contreras2020 | 403 | constraining what the operator may say is established | SUPPORTS (07) | regex language; domain phoneme vocabulary |
| 82 | silva2026 | 404 | validation downstream of an untrusted model | SUPPORTS (07) | §4.2 "The LLM as an untrusted commander" |
| 83 | llm2swarm2024 | 405 | this system is outside both categories | SUPPORTS (07) (categories correctly stated) | |
| 84 | skysim2026 | 424 | planner latency runs to tens of seconds | SUPPORTS | 34-50 s means, outliers > 100 s |
| 85 | typefly2024 | 425 | TypeFly shortens the path every command takes | SUPPORTS (07), interpretive | a token-efficient plan language reduces response time for all tasks |
| -- | (mira, uncited) | 425-427 | "this review established no latency for it and no budget it is held to" | **DOES NOT SUPPORT (BLOCKER B-1)** | Table 3 "Deterministic Interruption Preemption, speech_started → abort_cmd_sent, 466 ms"; §5.3 "the preemption latency is 466 ms at the median"; 450 ms confirmation threshold; §7 "handles bounded-latency interruption" |
| -- | (table-scoped, uncited) | 151-152, 421-423 | no system in tab:voice-uav-survey reports a stop handled separately from the interpreting path | **REFUTED (BLOCKER B-2)** | Silva: "The out-of-band emergency stop (the safety pilot disarming by radio, with no server involvement) was exercised deliberately on both airframes" (Fig. 14); Lim: operator switches to POSITION mode |
| 86 | sikorski2025 | 438 | offline arm on a control computer; significant limitations | SUPPORTS (07) | |
| 87 | torkamani2025 | 440 | "The edge tier ... presumes that the network is available at least part of the time" | **DOES NOT SUPPORT (BLOCKER B-3)** | the offline tier (TinyLlama-1.1B) "enables operation without internet connectivity". It is the *routing policy* that presumes a cloud: "In all other scenarios, online inference is preferred". The issue-07 sentence ("Routing of that kind presumes ...", uncited) was accurate; the rewrite moved the claim onto the edge tier and attached the citation |
| 88 | lim2025 | 448 | baseline: same families, local, PX4; zero-shot via Ollama from RTX 3080 Ti; temperature 0.2; ROS 2 text; VLM; 3 of 4 models 100 %, DeepSeek 38 %; 40 % Gemma3+VLM; POSITION-mode fallback; no latency | SUPPORTS (07); "zero-shot / no fine-tuning" PARTIAL (F-13) | Table I; §IV; "lacks a quantitative analysis of ... end-to-end latency" |
| 89 | lim2025 | 466 | caption: design points of Lim et al. | SUPPORTS | see §2e |

Uncited source claims in the critical comparisons (these read the tables, so they carry no \cite;
each checked against the sources):

| file:line | Claim | Verdict | Evidence |
|---|---|---|---|
| 138-139 | speech + group only in SwarmChat and CommandSwarm; neither states model hardware | SUPPORTS (within the table) | neither paper names a host |
| 140-144 | LM "remote in every system that names a provider" | PARTIAL (MINOR F-7) | Silva and Burke add "A locally hosted open-weight arm ... on a consumer laptop" (MacBook Air M4, LM Studio/Ollama) |
| 142-144 | Torkamani "hands work to the cloud when its runtime metrics call for it" | PARTIAL (NIT F-22) | the cloud is the default; offline is chosen when CPU > 80 % and temperature > 50, or cloud latency > 150 ms |
| 146-149 | every system with a language model constrains or checks its output | SUPPORTS as broadened (Sikorski's "is Valid" step and Torkamani's validation are uncredited in the table) | see the could-fill cells |
| 149-151 | deterministic automated checks appear in 2026 systems; "Iannoli et al. measure why: without planning tools and guardrails" | PARTIAL (MAJOR M-2) | Iannoli's with/without ablation is of planning tools only (the no-tool arm used a weaker success criterion, where GPT reached 100 %); guardrails were not ablated and are prompt fragments |
| 231-233 | 21 vs 1,233 ms; 7 vs 202 ms; +14 points | SUPPORTS | Table 5; Table I |
| 297-299 | SkySim outside both of Strobel's categories | SUPPORTS | one cloud planner, waypoints to an APF layer |
| 300-302 | "SkySim and Iannoli et al. exercise their control layers in software-in-the-loop simulation, while CommandSwarm does not execute its output" | PARTIAL (MINOR F-9, F-10) | SkySim is a Gazebo simulation with velocity commands on /cmd_vel, and no flight-software SITL is stated. CommandSwarm's architecture does execute valid trees in Violet (§III-E); only its *evaluation* does not |
| 302-303 | SkySim's tens-of-seconds latency judged unsuitable by its authors | SUPPORTS | §4 |
| 364-366 | "only Sikorski et al. state offline recognition. CommandSwarm, the most recent system that accepts speech, does not claim it" | "only Sikorski" false against reviewed systems (MAJOR M-1); "most recent" **REFUTED (BLOCKER B-5)** | Torkamani: "offline ASR module"; dates: CommandSwarm arXiv 8 May 2026, Henry 19 Jun 2026, MIRA 21 Sep 2026, all speech-input rows of the same table |
| 369-372 | 7 ms to about 4 s, nearly three orders; GPU -> CPU x ~15 | SUPPORTS | 4000/7 = 571 (2.76 orders); 106/7 = 15.1 |
| 373-375 | no prior row reports each speech stage's latency on its deployment processor | SUPPORTS narrowly (MINOR F-8) | MIRA reports per-stage P50s on its deployed robot (endpointing 10.0 ms, TTFT 1.62 s, preemption 466 ms) but does not name the processor running recognition |
| 409-412 | G1: fast paths have one action or serve responsiveness/computation; direct paths only as alternatives; none states a membership rule | SUPPORTS | as §2b |
| 434-436 | G3: no row of tab:voice-uav on an SBC without a GPU; no row of tab:soa-speech with per-stage latency on its deployment processor | SUPPORTS as scoped (see F-8) | Torkamani's Jetson Xavier NX has a GPU |

## 4. Paper numbers (report sheet, 32 anchors)

| line | value | source | found? | where |
|---|---|---|---|---|
| 49 | 74.81 % | contreras2020 | yes | abstract (English, cloud-based) |
| 50 | 93.33 % | contreras2020 | yes | abstract (phoneme matching) |
| 68 | up to 62 % | typefly2024 | yes | abstract, alttext `62\%` |
| 69 | below 1.5 s | typefly2024 | yes | abstract, alttext `1.5s` |
| 69 | eleven tasks | typefly2024 | yes | "a benchmark of 11 tasks" |
| 74 | more than 1,000 | silva2026 | yes | "Over 1,000 simulated flights"; 1,037 scored trials |
| 74 | 110 geofence-violation | silva2026 | yes | "no aircraft left the permitted zone in 110 geofence-violation" trials |
| 75 | three real quadcopters | silva2026 | yes | "commanded three quadcopters" |
| 85 | Q5_K_M | sikorski2025 | yes | "LLaMA 2-7B.Q5 K M"; Table II caption |
| 95 | six general-purpose LMs | iannoli2026 | yes | "six state-of-the-art LLMs" |
| 129 | 6.7--14B | commandswarm2026 | yes | "eleven open 6.7B–14B parameter LLMs" |
| 166 | 0.81 at 1.233 s | simoes2024 | yes | Table 5 |
| 166 | 0.99 at 0.021 s | simoes2024 | yes | Table 5 |
| 168 | 93 % at 7 ms | henry2026 | yes | Table I, XLSR-53-FR, explicit subset |
| 169 | 79 % at 202 ms | henry2026 | yes | Table I, cascade CamemBERT-Large |
| 171 | 82 % and 59 % | henry2026 | yes | Table I, Full column |
| 171 | 106 ms on a CPU | henry2026 | yes | "(106 ms on CPU)" |
| 181 | 1,006 ms to 81 ms | relays2s | yes | abstract (P90 first chunk, synthetic dialogues) |
| 253 | 20 Hz | skysim2026 | yes | §2.2 |
| 254 | 0.5 m/s | skysim2026 | yes | Eq. 5, vmax = 0.5 m/s |
| 254 | 3, 10 and 30 | skysim2026 | yes | §3 |
| 258 | 34 s for 3 drones (50 s for 10) | skysim2026 | yes, with a NIT | §3.3 "(N = 3 to N = 10) ... (34s to 50s)"; the paper's own §3.1 says "≈ 50 seconds (for N=30)", so the paper is internally inconsistent; the thesis follows §3.3 |
| 258 | above 100 s | skysim2026 | yes | "outliers > 100s" |
| 321 | about 4.0 s | commandswarm2026 | yes | §IV-B SeamlessM4T v2-large |
| 322 | about 5.2 s | commandswarm2026 | yes | §IV-B Whisper-medium |
| 327 | 680,000 hours | whisper | yes | §1, §2 |
| 328 | 39 million | whisper | yes | Table 1, Tiny 39M |
| 331 | 80 ms frame | oww | yes | README "80 ms frames" |
| 333 | 32 ms windows | silero | yes (source code) | 512 samples at 16 kHz; README only "30+ ms" |
| 454 | temperature of 0.2 | lim2025 | yes | §IV |
| 457 | in 38 % | lim2025 | yes | abstract; Table I |
| 458 | 40 % | lim2025 | yes | Table I, Gemma3 + Gemma3 VLM |

Result: 32 of 32 found at the stated value.

## 5. Findings (BLOCKER -> NIT)

| # | Sev | Dim | file:line | Quoted text | Problem | Evidence | Proposed fix |
|---|---|---|---|---|---|---|---|
| B-1 | BLOCKER | D5b | ch3:425-427 | "MIRA's gate stops the robot's motion and preempts the slower path, but this review established no latency for it and no budget it is held to." | MIRA reports that latency; the sentence misrepresents a source that G2 rests on. The tab:soa-dual-path MIRA latency dash hides the same number | MIRA Table 3 / §5.3: preemption "466 ms at the median, measured from speech onset (speech_started) to abort-command dispatch"; gate waits for a 450 ms interruption-confirmation threshold; §7 "handles bounded-latency interruption" | "MIRA's gate stops the robot's motion and preempts the slower path after sustained speech of 450~ms, and reports a median of 466~ms from speech onset to the abort command~\cite{mira}; it states no budget that latency is held to." Fill the tab:soa-dual-path MIRA latency cell: "466~ms, P50, speech onset to abort; ---" (or "466~ms (P50); LLM first token 1.62~s"). The argument agent should check that G2 still follows once a 466 ms stop is on record beside a 150 ms budget |
| B-2 | BLOCKER | D5b/D4 | ch3:151-152 and 421-423 | "None of the systems in the table reports a stopping command handled separately from the path that interprets commands." | Two rows of the same table report exactly that, in both places the sentence occurs (the Critical comparison and the opening of G2) | Silva and Burke: "The out-of-band emergency stop (the safety pilot disarming by radio, with no server involvement) was exercised deliberately on both airframes" (Fig. 14). Lim et al.: "the operator will switch the flight mode to POSITION mode" | l.151: "No system in the table reports an automated stopping command handled separately from the path that interprets commands; the separate stops that are reported, the radio kill of Silva and Burke's safety pilot and the switch to position mode by Lim et al.'s operator, are made by a human." l.421-423: "No system in Table~\ref{tab:voice-uav-survey} reports an automated stopping command handled separately from the path that interprets commands; where a separate stop exists it is a human safety pilot's~\cite{silva2026,lim2025}." |
| B-3 | BLOCKER | D5b | ch3:439-441 | "The edge tier of Torkamani and Zarin presumes that the network is available at least part of the time~\cite{torkamani2025}" | The citation says the opposite of the claim as worded. The on-device tier is what works offline; the cloud-preferring routing policy is what presumes a network | "the TinyLlama-1.1B-chat-v1.0 model was employed for offline inference. This enables operation without internet connectivity"; "In all other scenarios, online inference is preferred" | "Torkamani and Zarin prefer the cloud whenever the device's metrics allow and fall back to on-device inference when they do not~\cite{torkamani2025}; a routing policy of that kind presumes that the network is available at least part of the time, which the deployment site of Section~\ref{sec:operational-context} does not assure." |
| B-4 | BLOCKER | D5b (table cell) | ch3:283 | tab:soa-swarm CommandSwarm, Role: "Generates the tree; parser and safety classifier gate it" | The safety classifier gates the command before generation, not the tree | §III-C: "Before generation, CommandSwarm passes the normalized command to a Llama-Guard-style safety classifier ... two independent control points: one at the command level and one at the executable-plan level" | "Generates the tree; a safety classifier screens the command before generation, and a whitelist parser the tree after" |
| B-5 | BLOCKER | D5c/D4 | ch3:365-366 | "CommandSwarm, the most recent system that accepts speech, does not claim it." | Chronology is wrong: two later speech-input systems are rows of the same table | arXiv v1 dates: CommandSwarm 8 May 2026 (2605.07764v1), Henry et al. 19 Jun 2026 (2606.24910v1), MIRA 21 Sep 2026 (2609.24547) | "CommandSwarm, the one swarm system in the table whose recogniser is named, does not claim it." (or simply "CommandSwarm does not claim it.") |
| M-1 | MAJOR | D5c | ch3:336-361, 364-365 | tab:soa-speech caption "the spoken-command systems reviewed in this chapter"; "only Sikorski et al.\ state offline recognition" | Torkamani and Zarin are a spoken-command system reviewed in this chapter (tab:voice-uav-survey, Speech). They state an offline recogniser, yet they are absent from the table, which makes "only Sikorski" false against the systems the caption claims to cover. Their recogniser, an 8-bit tiny faster-whisper on a Jetson, is also the nearest published analogue of this work's whisper.cpp tiny.en | "user voice input is first transcribed by an offline ASR module"; "a lightweight 8-bit tiny ASR engine based on the faster-whisper implementation"; "Jetson Mate Xavier NX edge device used for local ASR and LLM inference"; "ASR accuracy of 62.5%" | Add the row: `Torkamani and Zarin~\cite{torkamani2025} & Whisper tiny, 8-bit (faster-whisper) & Yes & No & ---; Jetson Xavier NX \\`. Change l.364-365 to: "On where recognition runs, the older systems depend on a platform or a cloud service, and only Sikorski et al.\ and Torkamani and Zarin state offline recognition." (SwarmChat and Chat with UAV also accept voice but name no recogniser; either add them with dashes or narrow the caption to "whose front end the source describes") |
| M-2 | MAJOR | D5b | ch3:383-384; 149-151 | "deterministic, automated checks appear in recent swarm systems~\cite{iannoli2026,commandswarm2026}"; "Iannoli et al.\ measure why: without planning tools and guardrails, general-purpose models do not execute swarm tasks reliably" | Iannoli's guardrails are not deterministic checks between output and vehicle: they are prompt text injected when the Agent Core detects a failure condition. The ablation varies planning tools only | "Runtime guardrails are implemented as short, targeted prompt fragments that are injected dynamically"; "guardrails explicitly instruct the LLM to re-evaluate system state"; experiments are "with-tool" vs "no-tool" | l.383-384: "... and deterministic, automated checks appear in recent systems~\cite{silva2026,skysim2026,commandswarm2026}, beside runtime guardrails that re-prompt the model~\cite{iannoli2026}." l.150-151: "... and Iannoli et al.\ report why: without explicit grounding and execution support, general-purpose models do not execute even simple swarm tasks reliably." |
| F-7 | MINOR | D5b | ch3:140-141 | "the language model is remote in every system that names a provider" | Silva and Burke also run a locally hosted arm | "five open-weight rows hosted locally on a consumer laptop (MacBook Air M4 ...)" | "... is remote in every system that names a provider, apart from an exploratory locally hosted arm in Silva and Burke, ..." |
| F-8 | MINOR | D5b | ch3:373-375; 435-436; tab:soa-speech MIRA row | "No prior row reports the latency of each speech stage on the processor it deploys on"; MIRA latency "---" | True only because MIRA names no processor for recognition; MIRA does report per-stage medians on its deployed robot, which the dash conceals | Table 3: "Streaming ASR Endpointing ... 10.0 ms"; "LLM First-Token Latency (TTFT) ... 1.62 s"; all on "the physical Astribot S1 platform" | MIRA cell: "Endpointing 10.0~ms, preemption 466~ms (P50); recognition host unstated"; l.373: "No prior row reports the latency of each speech stage together with the processor that runs it, ..." |
| F-9 | MINOR | D5b | ch3:300-301 | "SkySim and Iannoli et al.\ exercise their control layers in software-in-the-loop simulation" | SkySim states no flight-software-in-the-loop; it drives simulated Crazyflies by velocity commands in Gazebo | §2.2 velocity "published to the ROS2 (/cmd_vel) topic"; §3 "simulation experiments using Gazebo Harmonic Environment and ROS2 Jazzy" | "SkySim exercises its control layer in Gazebo simulation and Iannoli et al.\ in ArduPilot software-in-the-loop simulation, while CommandSwarm does not execute its output in its evaluation." |
| F-10 | MINOR | D5b | ch3:301-302 | "CommandSwarm does not execute its output" | Its architecture does execute valid trees; only the evaluation does not | §III-E "Valid trees are executed by the low-level control layer ... in the Violet simulator" | add "in its evaluation" (see F-9 text) |
| F-11 | MINOR | D5b (table cell) | ch3:212 | tab:soa-dual-path Sahai, "What the fast path decides": "Which branch runs on a frame" | Wake-word spotting decides which branch runs. The cheaper branch decides nothing; it biases lead-in frames toward wake-word embeddings | "exploiting WW spotting to select which branch of its attention networks to execute" | "Nothing; wake-word spotting selects which branch runs on a frame" |
| F-12 | MINOR | D5b | ch3:79-80 | "flies one PX4-based quadcopter to a goal found by a vision-language model" | The goal is given in the operator's text; the VLM only detects the target | "specifying a target object to search and a textual description of the coordinate of the goal"; VLM "binary 'Yes' or 'No'" | "... flies one PX4-based quadcopter to a goal given in a text message, with a vision-language model detecting the target;" |
| F-13 | MINOR | D5b | ch3:452-453; tab:lim-positioning Adaptation | "zero-shot ... with no fine-tuning"; "Zero-shot prompting" | Inferred, not stated: the paper never uses "zero-shot" or "fine-tuning" about its own setup (issue 07 recorded it as CONFIRMED) | "absence of ablation studies examining the impact of ... few-shot examples"; future work "curating domain-specific datasets" | Keep, or use the source's own wording: "prompts off-the-shelf models through Ollama with system-level instructions, reporting neither fine-tuning nor few-shot examples"; cell: "Prompting of off-the-shelf models" |
| F-14 | MINOR | D5b (could fill) | ch3:125 | tab:voice-uav Torkamani, Check: "---" | The source plainly states a check | "a rule-based command validation and repair component"; three layers: action, device, index | "Rule-based validation and repair" |
| F-15 | MINOR | D5b (could fill) | ch3:280 | tab:soa-swarm Strobel, Evaluation: "Mainly conceptual" | Supported (the authors' own phrase), but it describes the contribution, not how the control layer was exercised. The fuller fact also includes an LLM on a Raspberry Pi 5, which examiners may raise against G3 | "showcases implemented in the ARGoS robot swarm simulator"; "we executed TinyLlama via Ollama on a Raspberry Pi 5 ... between 10 and 12 tokens per second"; each showcase robot "connected to a separate external LLM" | "ARGoS showcases on external models; a preliminary TinyLlama test on a Raspberry Pi~5" (the argument agent should decide whether G3 needs a sentence on it) |
| F-16 | MINOR | D5b (could fill) | ch3:124 | tab:voice-uav Sikorski, Check: "---" | A validity test exists (unspecified) | Algorithm 1: "if LLM_Return is Valid then Robot_Command <- LLM_Return" | "Validity test on the model's return" (optional) |
| F-17 | MINOR | D5f | ch3:255-259 | SkySim geofence, malformed-output and latency sentences (34 s, 50 s, > 100 s) | Three sentences of specific facts and numbers sit after the \cite that closes l.255, with no citation of their own | SkySim §2.2, §3.3, §4 | Add `~\cite{skysim2026}` after "... time-critical missions" (l.259) |
| F-18 | NIT | D5f | ch3:294-296 | "the method whose failure modes the analysis of Koren and Borenstein catalogues, including the absence of a passage between closely spaced obstacles" | A new, specific attribution without \cite (the l.245 cite does not name the item) | Koren §5.2 "No Passage Between Closely Spaced Obstacles" | append `~\cite{koren1991}` |
| F-19 | NIT | D5b | ch3:256-257 | "A malformed output or a timeout ... instead keeps the waypoints of the previous command." | The source's wording is ambiguous (holding the *position* of the previous command could mean hovering where the swarm is); the thesis picks one reading | "the system holds the position of the previous command to prevent undefined system states" | "... instead holds the position of the previous command, in the paper's words" (optional) |
| F-20 | NIT | D5b | ch3:180-181; 213 | "the 90th-percentile latency of the first chunk falls from 1,006 ms to 81 ms" | Scope qualifier missing | "On synthetic voice dialogues ... excluding TTS and network latency" | add "on synthetic dialogues, excluding speech synthesis and network time" |
| F-21 | NIT | D5b | ch3:278 | "separation, velocity matching, centring" | Reynolds (1987) names the first rule "Collision Avoidance" and the third "Flock Centering" | §"Simulated Flocks" rule list | "collision avoidance, velocity matching, flock centring" |
| F-22 | NIT | D5b | ch3:142-144 | Torkamani "hands work to the cloud when its runtime metrics call for it" | Reversed emphasis: cloud is the default | "In all other scenarios, online inference is preferred" | "which prefers the cloud and falls back to the edge when its runtime metrics call for it" |
| F-23 | NIT | D5b | ch3:171, 211, 353 | "7 ms is measured on a GPU" | The paper states "(106 ms on CPU)" and names only one GPU (RTX 2000 Ada), so "GPU" is inferred | §II-C, §III-A | none required; optionally "on the authors' GPU" |
| F-24 | NIT | D5e | references.bib typefly2024 | year = 2024 | arXiv v1 is 8 Dec 2023 (revised 2024); Silva and Burke cite a 2025 version (a venue version may exist) | arXiv abs `citation_date` 2023/12/08 | Keep (the last revision is defensible) or check for a 2025 venue record |
| F-25 | NIT | D5b | ch3:395 | "spoken commands to a group of vehicles" | CommandSwarm's agents are swarm robots in Violet, not vehicles | §IV-A | "to a group of robots" |

No D5a problems: every key resolves (script PASS). No D5d problems: tools named in the prose
(Nuance, VOSK, Ollama, SeamlessM4T, CamemBERT, Gazebo, ArduPilot) are attributes of cited systems.
No D5e problems of substance: title, authors and year agree with Crossref (10 DOIs) and with the
arXiv abs metadata (13 arXiv keys). The known Majeed/Majid spelling of CommandSwarm's first author
follows the PDF byline, as recorded in the candidate notes. The Javaid bib lists four authors, which
matches the journal record.

## 6. UNVERIFIED

- **landau2017**: the full text and the ACM abstract page could not be opened (ACM DL 403;
  Semantic Scholar elides the abstract). The Nuance / regular-expression / DJI Phantom 4 facts rest
  on the ACM abstract as quoted by the search index, and on issue 07's Crossref-era reading.
  The dashes in tab:soa-speech (offline, latency) cannot be tested.
- **Iannoli et al., host of the six models** (dash): token usage is read from "the LLM API", which
  suggests hosted models, but Qwen3 8B may have been local; not established.
- **SkySim, 34 s vs 50 s**: the paper contradicts itself (§3.1 "≈ 50 seconds (for N=30)" vs
  §3.3 "34s to 50s" for N = 3 -> 10; Fig. 5 was not readable in the PDF text). The thesis follows
  §3.3, which is the explicit statement.
- **Henry et al., whether 202 ms (cascade) was measured on the same GPU as the 7 ms**: not stated.
- **Whisper tiny.en = 39 M**: Table 1 gives the Tiny size as 39M; the paper does not list tiny.en
  separately in that table, only in its results tables.
- **codeaspolicies2023 / saycan2022 / chatgptrobotics2024** were checked against the arXiv full
  texts; the published venue versions (ICRA, CoRL/PMLR, IEEE Access) could not be opened, and the
  quoted sentences are assumed to survive into them.
