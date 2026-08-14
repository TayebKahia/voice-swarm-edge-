# Bibliography candidates — Mémoire d'Ingénieur

Candidate references for the *Mémoire d'Ingénieur* only (the engineering document: dual-path
runtime, safety architecture, offline pipeline). Gathered 2026-09-22.
**Every entry below is an UNVERIFIED CANDIDATE.** Each was pulled from a primary page that was
actually fetched during this pass, but the author must re-open each primary page and check title,
authors, venue and year before any of it reaches `thesis/references.bib`.
Nothing here touches quantisation, constrained decoding, LoRA or NLU datasets — that material
belongs to the *Mémoire de Master* (Table 3, write-once).

---

## GAP 1 — Voice-controlled UAV and natural-language robot control

Ordered by how load-bearing each is for the survey in Ch. 2 §"Voice-controlled UAV systems" and
for the gap claim in Ch. 2 §"Gap".

### CommandSwarm: Safety-Aware Natural Language-to-Behavior-Tree Generation for Robotic Swarms
- Authors (as shown on page): Mohammed Majid, Amjad Yousef Majid
- Venue / year: arXiv preprint, 2026 (cs.RO)
- Identifier: arXiv:2605.07764
- Page fetched: https://arxiv.org/abs/2605.07764 and https://arxiv.org/html/2605.07764
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems" and section "Gap"
- Supports the claim: This is the nearest neighbour in the literature — speech-or-text to swarm
  behaviour trees with a safety filter, constrained prompting and a deterministic parser gate —
  and its own conclusion, that "parser acceptance and safety filtering remain necessary execution
  gates; generation quality alone is not sufficient", is independent support for the three-layer
  validation argument in Ch. 1 §safety-problem. **Read the "Notes for the author" section below
  before writing the gap paragraph.**
- **Verified 2026-09-23:** key `commandswarm2026` — record OK (arXiv abs v1; NB the PDF byline and e-mail spell the first author *Majeed*, the abs metadata *Majid*; the bib uses the byline) / claim CORRECTED: 6.7B–14B, all 4-bit, whitelist + deterministic XML parser gate, constrained prompting (a prompt that lists the allowed primitives — not constrained decoding), and the quoted conclusion are all confirmed verbatim. But (a) the ~5.2 s Whisper-medium figure is *speech-translation* latency (to English), not plain ASR, and it is the rejected option: the chosen front end is SeamlessM4T v2-large at ~4.0 s; (b) evaluation is BLEU/ROUGE-L/parser acceptance on generated XML — generated trees are *not* executed and scored in the simulator (simulator-in-the-loop is listed as future work); (c) the Llama-Guard-style safety classifier is "not independently evaluated"; (d) no emergency stop, preemption or hold path exists — the paper lists "emergency stop mechanisms" among safeguards real deployment "should require"; (e) no deployment hardware is named; the paper never claims offline operation (audio comes "from a web microphone"); (f) simulation = Violet, a PyGame-based swarm simulator; real-robot transfer (Crazyflie/e-puck, to measure latency) is future work.

### SkySim: A ROS2-based Simulation Environment for Natural Language Control of Drone Swarms using Large Language Models
- Authors (as shown on page): Aditya Shibu, Marah Saleh, Mohamed Al-Musleh, Nidhal Abdulaziz
- Venue / year: arXiv preprint, 2026
- Identifier: arXiv:2602.01226
- Page fetched: https://arxiv.org/abs/2602.01226
- Serves: Ingénieur ch2 sections "Voice-controlled UAV systems" and "Swarm control"
- Supports the claim: A contemporary system that also separates LLM high-level planning from a
  low-level safety enforcement layer running an artificial potential field at 20 Hz for collision
  avoidance and geo-fencing — the closest published analogue to the APF-plus-clamp arrangement of
  Ch. 1 §safety-problem, and a cloud-LLM counterexample to the offline requirement.
- **Verified 2026-09-23:** key `skysim2026` — record OK (arXiv abs v1; PDF header places it at DAUS 2026, Salzburg, not on the abs page) / claim CORRECTED: the LLM is **Gemini 3.5 Pro** ("Gemini 3.5 Pro Preview" in the results) via the google.generativeai cloud API; APF control loop at 20 Hz confirmed; swarm sizes 3, 10, 30 confirmed (the latency figure also has N=4); simulation-only (Gazebo Harmonic + ROS2 Jazzy, simulated Crazyflie 2.1 Brushless, noiseless ground-truth odometry). Geo-fencing is **not** done by the APF: the LLM Planner Node rejects out-of-bounds waypoints and falls back to position hold; the APF handles inter-agent repulsion, and velocity is saturated at 0.5 m/s. A malformed output or API timeout also holds the previous command. Input is **typed text — there is no speech at all**. Mean planning latency 34–50 s, outliers >100 s; the authors call it "unsuitable for time-critical missions".

### TypeFly: Flying Drones with Large Language Model
- Authors (as shown on page): Guojun Chen, Xiaojing Yu, Neiwen Ling, Lin Zhong
- Venue / year: arXiv preprint, v1 2023, revised 2024
- Identifier: arXiv:2312.14950
- Page fetched: https://arxiv.org/abs/2312.14950
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"
- Supports the claim: Establishes in the prior literature that token-by-token LLM generation
  imposes a latency that is the binding constraint for drone control, and that the response is to
  change the output representation — which is exactly the pressure that Ch. 1 §safety-problem
  answers architecturally instead, by removing the stopping command from the LLM path altogether.
- **Verified 2026-09-23:** key `typefly2024` — record OK / claim OK, with precision: the paper says sequential token generation "introduces substantial latency" proportional to plan length, and answers with MiniSpec (a token-efficient plan language) plus stream interpretation — up to 62% response-time reduction, <1.5 s response on its 11-task benchmark. LLM is remote (GPT-4, cloud); input is an English text task description, not speech.

### Evaluating Voice Command Pipelines for Drone Control: From STT and LLM to Direct Classification and Siamese Networks
- Authors (as shown on page): Lucca Emmanuel Pineli Simões, Lucas Brandão Rodrigues, Rafaela Mota Silva, Gustavo Rodrigues da Silva
- Venue / year: arXiv preprint, 2024 (cs.SD, cs.AI)
- Identifier: arXiv:2407.08658
- Page fetched: https://arxiv.org/abs/2407.08658
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"
- Supports the claim: Directly benchmarks an STT+LLM cascade against direct voice-to-function
  classification on inference time and accuracy for one drone — i.e. the literature has already
  measured the two halves of the dual path separately, which is the premise the architecture
  builds on and lets Ch. 2 claim the *combination*, not the components, as the contribution.
- **Verified 2026-09-23:** key `simoes2024` — record OK / claim OK: one Tello drone, Portuguese commands (wav2vec2-XLSR-53-Portuguese); STT+LLM 0.81 acc at 1.233 s, direct classifier 0.99 at 0.021 s, Siamese 0.74 at 0.006 s (Table 5).

### End-to-End Voice Intent Recognition for Spontaneous Human-Drone Interaction with Naive Users
- Authors (as shown on page): Allan Henry (GIPSA-COPERNIC, GETALP, LPNC), Solange Rossato (GETALP), Christian Graff (LPNC), Sylvain Huet (GIPSA-COPERNIC), Jose-Ernesto Gomez-Balderas (GIPSA-COPERNIC)
- Venue / year: 35th IEEE International Conference on Robot and Human Interactive Communication (RO-MAN 2026), Kitakyushu, Japan, 2026
- Identifier: arXiv:2606.24910
- Page fetched: https://arxiv.org/abs/2606.24910
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"; supports ch1 §safety-problem
- Supports the claim: Reports a transcription-free direct-intent path at 93% / 7 ms against a
  cascade at 79% / 202 ms on the same corpus — peer-reviewed, quantitative evidence that the
  reflex/parse latency asymmetry of NFR-1 vs NFR-2 is a property of the pipeline shape and not an
  artefact of this project's hardware.
- **Verified 2026-09-23:** key `henry2026` — record OK (arXiv; RO-MAN 2026 acceptance per comments, no DOI yet) / claim OK, with caveats: 93%/7 ms vs cascade (Whisper + CamemBERT-Large) 79%/202 ms is on the *explicit simple-command* subset; on the full spontaneous test set it is 82% vs 59%. The 7 ms is on an RTX 2000 Ada GPU (106 ms on CPU). French speech. The paper attributes the 14-point gap to "the cascade architecture itself rather than" ASR quality.

### SwarmChat: An LLM-Based, Context-Aware Multimodal Interaction System for Robotic Swarms
- Authors (as shown on page): Ettilla Mohiuddin Eumi, Hussein Abbass, Nadine Marcus
- Venue / year: 16th International Conference on Swarm Intelligence (ICSI 2025), Yokohama, Japan, July 2025
- Identifier: arXiv:2509.16920
- Page fetched: https://arxiv.org/abs/2509.16920
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"
- Supports the claim: A voice/text/teleoperation multimodal LLM interface to a robotic swarm,
  with intent recognition and task planning as separate LLM modules — the mainstream
  "everything through the LLM" design that the dual-path argument is positioned against.
- **Verified 2026-09-23:** key `swarmchat2025` — record OK (Springer LNCS, ICSI 2025, pp. 181–192, doi:10.1007/978-981-95-0982-9_15) / claim CORRECTED: the abstract says "four LLM-based modules", but in the body **Intent Recognition is rule-based keyword matching** ("patrol" → patrol mode) and the authors list it as a limitation; the LLM is never named; evaluation is preliminary (keyword combinations, no user study yet). Citable only as an LLM-mediated text/voice/teleop swarm interface over ROS2, not as an example of intent recognition by LLM.

### Say the Mission, Execute the Swarm: Agent-Enhanced LLM Reasoning in the Web-of-Drones
- Authors (as shown on page): Andrea Iannoli, Lorenzo Gigli, Luca Sciullo, Angelo Trotta, Marco Di Felice
- Venue / year: 2026 IEEE 27th International Symposium on a World of Wireless, Mobile and Multimedia Networks (WoWMoM), pp. 139–148, 2026
- Identifier: arXiv:2605.03788
- Page fetched: https://arxiv.org/abs/2605.03788
- Serves: Ingénieur ch2 sections "Voice-controlled UAV systems" and "Gap"
- Supports the claim: Finds across six leading LLMs and four swarm missions that general-purpose
  LLMs "still struggle to achieve reliable execution — even for simple swarm tasks — when
  operating without explicit grounding and execution support", and that runtime safeguards
  materially improve reliability. This is external, peer-reviewed justification for putting
  validation layers downstream of the model rather than trusting the model.
- **Verified 2026-09-23:** key `iannoli2026` — record OK (IEEE WoWMoM 2026, pp. 139–148, doi:10.1109/WoWMoM69805.2026.00027) / claim OK: quote confirmed in the abstract; "task-specific planning tools and runtime guardrails substantially improve robustness". Natural-language text, no speech; ArduPilot SITL simulation; MCP + W3C WoT abstraction, no code generation.

### An LLM-Agnostic, MAVLink-Based Drone Command and Control Interface and Agentic Harness Using the Model Context Protocol
- Authors (as shown on page): Javier Noé Ramos Silva, Peter J. Burke
- Venue / year: arXiv preprint, 2026
- Identifier: arXiv:2601.15486
- Page fetched: https://arxiv.org/abs/2601.15486
- Serves: Ingénieur ch2 sections "Voice-controlled UAV systems" and "Positioning against Lim et al."
- Supports the claim: The largest evaluation of LLM-driven drone command and control to date
  (>1,000 simulated flights plus real hardware, with safety-validation mechanisms and geofence
  trials) — useful both as scale context and as a second, stronger baseline than Lim et al. alone
  for the non-comparability argument.
- **Verified 2026-09-23:** key `silva2026` — record OK (arXiv v3, 11 Sep 2026) / claim CORRECTED: the paper does not say "largest"; it says "to our knowledge the broadest evaluation of an LLM–drone command interface reported to date" *on the axes it measures*. Confirmed: >1,000 simulated flights, 110 geofence-violation trials with no aircraft leaving the zone, three real quadcopters; LLM treated as an "untrusted commander" with server-side validation. Models are mostly cloud providers'.

### Deployment of Large Language Models to Control Mobile Robots at the Edge
- Authors (as shown on page): Pascal Sikorski, Leendert Schrader, Kaleb Yu, Lucy Billadeau, Jinka Meenakshi, Naveena Mutharasan, Flavio Esposito, Hadi AliAkbarpour, Madi Babaiasl
- Venue / year: arXiv preprint, v1 2024, revised v3 2024
- Identifier: arXiv:2405.17670
- Page fetched: https://arxiv.org/abs/2405.17670
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"; supports ch1 §operational-context
- Supports the claim: Compares a cloud LLM against a quantised offline LLM for spoken robot
  commands at the edge and finds the offline model markedly less consistent — the honest prior
  statement of the cost that offline operation imposes, which is the cost this project's
  architecture is designed to absorb rather than deny.
- **Verified 2026-09-23:** key `sikorski2025` — record OK (published: IEEE ICMCR 2025, pp. 19–24, doi:10.1109/ICMCR64890.2025.10963303; bib uses the venue record) / claim OK: GPT-4-Turbo (cloud) vs LLaMA 2-7B Q5_K_M (offline), the latter showing "significant limitations in consistency and reliability". Speech via offline VOSK; a wheeled mobile robot, with the LLM on a control computer (Pico W is only the radio link).

### Adaptive Edge-Cloud Inference for Speech-to-Action Systems Using ASR and Large Language Models
- Authors (as shown on page): Mohammad Jalili Torkamani, Israt Zarin
- Venue / year: arXiv preprint, 2025 (6 pages, 7 figures, 1 table)
- Identifier: arXiv:2512.12769
- Page fetched: https://arxiv.org/abs/2512.12769
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"; supports ch1 §operational-context
- Supports the claim: Routes spoken commands between edge and cloud on runtime metrics (CPU load,
  temperature, network latency) — the design this project explicitly forecloses, and therefore a
  clean citation for why NFR-14 makes offline a requirement rather than a routing policy.
- **Verified 2026-09-23:** key `torkamani2025` — record OK / claim OK with a scope correction: ASTA routes between edge and cloud on CPU load, device temperature and network latency, as claimed — but the targets are **IoT devices (smart lights, appliances), not robots or drones**. NVIDIA Jetson platform, 80 spoken commands, ASR accuracy 62.5%.

### LLM2Swarm: Robot Swarms that Responsively Reason, Plan, and Collaborate through LLMs
- Authors (as shown on page): Volker Strobel, Marco Dorigo, Mario Fritz
- Venue / year: NeurIPS 2024 Workshop on Open-World Agents, 2024
- Identifier: arXiv:2410.11387
- Page fetched: https://arxiv.org/abs/2410.11387
- Serves: Ingénieur ch2 sections "Voice-controlled UAV systems" and "Swarm control"
- Supports the claim: Distinguishes indirect integration (LLM writes the controller offline) from
  direct integration (an LLM instance runs on each robot at operation time) — a useful taxonomy
  for stating precisely where this project's single-operator, single-LLM, formation-level design
  sits.
- **Verified 2026-09-23:** key `llm2swarm2024` — record OK / claim OK, one nuance: indirect integration synthesises and validates controllers "before or during deployment" (not only offline); direct integration runs a separate LLM instance on each robot. The authors call the contribution "mainly conceptual".

### Chat with UAV — Human-UAV Interaction Based on Large Language Models
- Authors (as shown on page): Haoran Wang, Zhuohang Chen, Guang Li, Bo Ma, Chuanghuang Li
- Venue / year: arXiv preprint, 2025
- Identifier: arXiv:2512.08145
- Page fetched: https://arxiv.org/abs/2512.08145
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"
- Supports the claim: A "dual-agent" human-UAV interaction framework splitting planning from
  execution across two LLMs — worth citing precisely because it is a *dual* architecture that is
  not a dual *path*: both branches are LLM-latency branches, which sharpens what Ch. 1's
  16-fold budget separation actually buys.
- **Verified 2026-09-23:** key `chatwithuav2025` — record OK / claim OK: two independent LLM agents (task planning, execution), framework named UAV-GPT; simulation and real experiments.

### Unmanned Aerial Vehicle Control Through Domain-based Automatic Speech Recognition
- Authors (as shown on page): Ruben Contreras, Angel Ayala, Francisco Cruz
- Venue / year: arXiv preprint, 2020 (page states "Submitted to Computers")
- Identifier: arXiv:2009.04215
- Page fetched: https://arxiv.org/abs/2009.04215
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"
- Supports the claim: Pre-LLM speech-driven drone control evaluated under injected noise at
  several levels — the earlier generation of the field, and a precedent for the SNR-sweep
  methodology of RQ3 / Exp-3.
- **Verified 2026-09-23:** key `contreras2020` — record OK: bib uses the journal version *Computers* 9(3):75, 2020, doi:10.3390/computers9030075 (the DOI the arXiv abs page itself links; metadata via Crossref) / claim OK: voice commands with several levels of distortion applied; note the base recogniser is **cloud-based**, improved by domain phoneme matching (EN 74.81% → 93.33%, ES 97.04% → 100%), in a simulated V-REP domestic scene.

### A System Architecture for Hands-Free UAV Drone Control Using Intuitive Voice Commands
- Authors (as shown on page): Megan Landau, Sebastian van Delden
- Venue / year: HRI '17: Proceedings of the Companion of the 2017 ACM/IEEE International Conference on Human-Robot Interaction, pp. 181–182, published 06 March 2017
- Identifier: doi:10.1145/3029798.3038329
- Page fetched: https://dl.acm.org/doi/10.1145/3029798.3038329
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"
- Supports the claim: The early-generation reference point: a cloud speech platform (Nuance) with
  the control language defined by regular expressions on a single DJI airframe. It shows that
  *constraining the command language* is an old idea in this field, while *offline* and *swarm*
  are the parts that were not solved there.
- **Verified 2026-09-23:** key `landau2017` — record OK (via Crossref; ACM DL is behind a bot wall) / claim CORRECTED (abstract only; the paper is paywalled): Nuance speech recognition platform, DJI Mobile SDK (iOS/Swift), control language defined by regular expressions, tested on a DJI Phantom 4. The abstract does **not** say the Nuance service is cloud-hosted — do not call it "cloud" unless you read the paper.

### Code as Policies: Language Model Programs for Embodied Control
- Authors (as shown on page): Jacky Liang, Wenlong Huang, Fei Xia, Peng Xu, Karol Hausman, Brian Ichter, Pete Florence, Andy Zeng
- Venue / year: arXiv preprint, v1 2022, revised v4 2023 (ICRA 2023 — confirm on the page)
- Identifier: arXiv:2209.07753
- Page fetched: https://arxiv.org/abs/2209.07753
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"
- Supports the claim: The canonical statement of natural-language-to-executable-robot-action via
  a language model, and therefore the origin of the design this document departs from: free-form
  generated code is unbounded in what it can command, which is what the three validation layers
  exist to prevent.
- **Verified 2026-09-23:** key `codeaspolicies2023` — record OK (ICRA 2023, pp. 9493–9500, doi:10.1109/ICRA48891.2023.10160591) / claim CORRECTED: "unbounded in what it can command" is not the paper's claim — it re-composes given perception and control-primitive APIs (third-party libraries allowed) and says its scope is restricted by "which control primitives are available". What it does say, and what to cite: "Our approach also assumes all given instructions are feasible, and we cannot tell if a response will be correct a priori."

### Do As I Can, Not As I Say: Grounding Language in Robotic Affordances
- Authors (as shown on page): Michael Ahn, Anthony Brohan, Noah Brown, Yevgen Chebotar, Omar Cortes, Byron David, Chelsea Finn, Chuyuan Fu, Keerthana Gopalakrishnan, Karol Hausman, Alex Herzog, Daniel Ho, Jasmine Hsu, Julian Ibarz, Brian Ichter, Alex Irpan, Eric Jang, Rosario Jauregui Ruano, Kyle Jeffrey, Sally Jesmonth, Nikhil J Joshi, Ryan Julian, Dmitry Kalashnikov, Yuheng Kuang, Kuang-Huei Lee, Sergey Levine, Yao Lu, Linda Luu, Carolina Parada, Peter Pastor, Jornell Quiambao, Kanishka Rao, Jarek Rettinghouse, Diego Reyes, Pierre Sermanet, Nicolas Sievers, Clayton Tan, Alexander Toshev, Vincent Vanhoucke, Fei Xia, Ted Xiao, Peng Xu, Sichun Xu, Mengyuan Yan, Andy Zeng
- Venue / year: arXiv preprint, v1 2022, v2 2022 (SayCan)
- Identifier: arXiv:2204.01691
- Page fetched: https://arxiv.org/abs/2204.01691
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"
- Supports the claim: The reference work for *constraining a language model to the actions the
  embodiment can actually perform*. Cite it for the general principle, then distinguish: SayCan
  constrains by learned affordance scores, this system constrains by an explicit grammar plus a
  semantic validator plus a state machine, which is auditable and does not degrade silently.
  (Note the 44-author list — check the house style for `et al.` truncation.)
- **Verified 2026-09-23:** key `saycan2022` — record OK: bib uses the CoRL 2022 record (PMLR vol. 205, pp. 287–318, published 2023); **PMLR author order starts with Brian Ichter, not Michael Ahn** — biblatex will print "Ichter et al." / claim OK: pretrained skills with value functions "constrain the model to propose natural language actions that are both feasible and contextually appropriate".

### ChatGPT for Robotics: Design Principles and Model Abilities
- Authors (as shown on page): Sai Vemprala, Rogerio Bonatti, Arthur Bucker, Ashish Kapoor
- Venue / year: arXiv preprint, v1 2023, v2 2023
- Identifier: arXiv:2306.17582
- Page fetched: https://arxiv.org/abs/2306.17582
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"
- Supports the claim: Covers aerial navigation among its task domains and is the most-cited
  statement of the prompt-engineering-plus-function-library approach — the design whose absence
  of any verification gate the safety argument of Ch. 1 is a response to.
- **Verified 2026-09-23:** key `chatgptrobotics2024` — record OK: published in IEEE Access 12:55682–55696, 2024 (doi:10.1109/ACCESS.2024.3387941); bib uses it / claim CORRECTED: the paper does have a gate — a **human "on the loop"** who evaluates output quality and safety before execution (Fig. 2), and it says these tools "should not be given full control of the robotics pipeline". Correct framing: no *automated, deterministic* gate; safety rests on human supervision. Aerial navigation (AirSim, and a real drone) confirmed.

### Large Language Models for UAVs: Current State and Pathways to the Future
- Authors (as shown on page): Shumaila Javaid, Nasir Saeed, Bin He
- Venue / year: arXiv preprint, 2024
- Identifier: arXiv:2405.01745
- Page fetched: https://arxiv.org/abs/2405.01745
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"
- Supports the claim: A survey to anchor the opening sentence of the section, so that the review
  is framed as a field rather than as a list of systems. Lower priority — use it for framing
  only; the specific claims should rest on the primary systems above.
- **Verified 2026-09-23:** key `javaid2024` — record OK: published in IEEE Open Journal of Vehicular Technology 5:1166–1192, 2024 (doi:10.1109/OJVT.2024.3446799); **journal author list is Javaid, Fahim, He, Saeed** (four authors; arXiv has three) / claim OK for framing.

### Integrating Large Language Models for UAV Control in Simulated Environments: A Modular Interaction Approach
- Authors (as shown on page): Abhishek Phadke, Alihan Hadimlioglu, Tianxing Chu, Chandra N Sekharan
- Venue / year: arXiv preprint, 2024
- Identifier: arXiv:2410.17602
- Page fetched: https://arxiv.org/abs/2410.17602
- Serves: Ingénieur ch2 section "Voice-controlled UAV systems"
- Supports the claim: Lower priority. A proof-of-concept modular framework coupling existing LLMs
  to robotic simulators; useful only if the survey needs a second example of simulator-coupled
  LLM UAV control alongside Lim et al.
- **Verified 2026-09-23:** key `phadke2024` — record OK / claim OK: review plus a template framework and proof-of-concept LLM–simulator integration.

---

## GAP 2 — Safety-critical design principles

For Ch. 1 §"The safety problem" (currently uncited) and Ch. 2. Ordered by how directly each owns
one of the three principles the section currently presents as if novel.

### STPA Handbook
- Authors (as shown on page): Nancy G. Leveson, John P. Thomas
- Venue / year: March 2018 (MIT; handbook, 188 pp., © 2018 Nancy Leveson and John Thomas)
- Identifier: no DOI — MIT Partnership for Systems Approaches to Safety and Security (PSAS)
- Page fetched: http://psas.scripts.mit.edu/home/get_file.php?name=STPA_handbook.pdf (title page read directly from the PDF)
- Serves: Ingénieur ch1 section "The safety problem"; ch2
- Supports the claim: **The single most load-bearing citation for this section.** STPA's
  unsafe-control-action taxonomy is precisely the sentence in Ch. 1 that reads "a command correct
  in isolation can arrive while the swarm is in a state that cannot accept it" — that is an STPA
  UCA of the "provided in the wrong context/state" type, and the flight state machine of FR-11 is
  the control-structure response to it. Citing Leveson converts that paragraph from an assertion
  into an application of an established hazard-analysis method.

### IEC 61508-1:2010 — Functional safety of electrical/electronic/programmable electronic safety-related systems — Part 1: General requirements
- Authors (as shown on page): International Electrotechnical Commission (corporate author), Edition 2.0
- Venue / year: IEC, published 2010-04-30 (supersedes the 1998 first edition)
- Identifier: IEC 61508-1:2010 (standard number; cite as a standard, not a DOI)
- Page fetched: https://webstore.iec.ch/en/publication/5515
- Serves: Ingénieur ch1 section "The safety problem"
- Supports the claim: The standard that owns the principle stated in Ch. 1 as "every rejection at
  every layer resolves to a hold": a safety-related system must either work correctly or fail into
  a defined safe state. Cite it for the *safe state* concept so the hold is recognisable as
  fail-safe design rather than a local convention. Check which part actually carries the
  definitions you quote — Part 4 is the vocabulary part; fetch it separately before citing.

### Basic Concepts and Taxonomy of Dependable and Secure Computing
- Authors (as shown on page): Algirdas Avizienis, Jean-Claude Laprie, Brian Randell, Carl Landwehr
- Venue / year: IEEE Transactions on Dependable and Secure Computing, Volume 1, Issue 1, pp. 11–33, published 01 January 2004
- Identifier: doi:10.1109/TDSC.2004.2
- Page fetched: https://dl.acm.org/doi/10.1109/TDSC.2004.2
- Serves: Ingénieur ch1 section "The safety problem"
- Supports the claim: The reference that defines the failure-mode vocabulary — fail-safe,
  fail-silent, and the fault/error/failure chain. It gives Ch. 1's asymmetry argument its proper
  name: the design restricts the system's failure modes to the benign class, which is a *failure
  mode assumption*, not a performance claim.

### Guidance on the Assurance of Machine Learning in Autonomous Systems (AMLAS)
- Authors (as shown on page): Richard Hawkins, Colin Paterson, Chiara Picardi, Yan Jia, Radu Calinescu, Ibrahim Habli
- Venue / year: arXiv preprint, 2021 (University of York / Assuring Autonomy International Programme)
- Identifier: arXiv:2102.01564
- Page fetched: https://arxiv.org/abs/2102.01564
- Serves: Ingénieur ch1 section "The safety problem"; ch2
- Supports the claim: Owns the third principle directly — that an ML component's performance
  metric is not a safety argument, and that safety requirements must be derived from system-level
  hazards and evidenced separately. This is the citation for "an accuracy target on its own does
  not express that objective", and it is also the frame within which the safe-failure rate is a
  legitimate requirement rather than an invented metric.

### Unifying Evaluation of Machine Learning Safety Monitors
- Authors (as shown on page): Joris Guerin, Raul Sena Ferreira, Kevin Delmas, Jérémie Guiochet
- Venue / year: 33rd IEEE International Symposium on Software Reliability Engineering (ISSRE 2022), 2022
- Identifier: arXiv:2208.14660
- Page fetched: https://arxiv.org/abs/2208.14660
- Serves: Ingénieur ch1 section "The safety problem"; ch5 (validation metrics)
- Supports the claim: Proposes Safety Gain, Residual Hazard and Availability Cost as the metrics
  a safety monitor should be judged by, instead of accuracy — i.e. the literature has already
  formalised "the score that ranks them equal is measuring the wrong property". Use it to justify
  reporting the safe-failure rate *beside* CRR, and to name the price of the hold-on-rejection
  policy as availability cost rather than leaving it unnamed.

### Pre-Execution Safety Gate & Task Safety Contracts for LLM-Controlled Robot Systems
- Authors (as shown on page): Ike Obi, Vishnunandan L.N. Venkatesh, Weizheng Wang, Ruiqi Wang, Dayoon Suh, Temitope I. Amosa, Wonse Jo, Byung-Cheol Min
- Venue / year: arXiv preprint, 2026
- Identifier: arXiv:2604.05427
- Page fetched: https://arxiv.org/abs/2604.05427
- Serves: Ingénieur ch1 section "The safety problem"; ch3 (architecture)
- Supports the claim: A deterministic pre-execution gate that authorises or rejects a natural-
  language command before it becomes robot code, with invariants, guards and explicit abort
  conditions — the same structural commitment as the semantic validator and state machine, from
  an independent group, and grounded in a published safety standard (ISO 13482).

### A Survey of Research into Mixed Criticality Systems
- Authors (as shown on page): Alan Burns (University of York), Robert I. Davis (University of York)
- Venue / year: ACM Computing Surveys / ACM Trans. Embedd. Comput. Syst., Article 82, December 2017, 35 pages (the authors' PDF carries an inconsistent journal line — verify the venue on the ACM DL record at doi:10.1145/3131347 before citing)
- Identifier: doi:10.1145/3131347
- Page fetched: https://www-users.york.ac.uk/~rd17/papers/CSURreviewMCS.pdf (authors' copy, University of York)
- Serves: Ingénieur ch1 section "The safety problem"; ch3 section on core allocation
- Supports the claim: The survey of the field that owns "criticality is a designation of the level
  of assurance needed against failure for a system component" and the scheduling consequences of
  running components of two criticality levels on one platform. This is the discipline NFR-1's
  "must hold *while* Branch B is decoding" belongs to, and citing it makes the four-core
  allocation argument in Ch. 3 a mixed-criticality argument rather than an ad-hoc one.

### Learning Safe-Stoppability Monitors for Humanoid Robots
- Authors (as shown on page): Yifan Sun, Yiyuan Pan, Shangtao Li, Caiwu Ding, Tao Cui, Lingyun Wang, Changliu Liu
- Venue / year: arXiv preprint, 2026 (8 pages, 5 figures)
- Identifier: arXiv:2603.22703
- Page fetched: https://arxiv.org/abs/2603.22703
- Serves: Ingénieur ch1 section "The safety problem"
- Supports the claim: Formalises safe stopping as a controlled transition to a low-risk state
  rather than a power cut, which is exactly why `swarm hold` maps to `hover` and not to motor
  cut-off. Useful if Ch. 3 needs to defend the *content* of the two Branch A classes as well as
  their membership rule.

### Safe LLM-Controlled Robots with Formal Guarantees via Reachability Analysis
- Authors (as shown on page): Ahmad Hafez, Alireza Naderi Akhormeh, Amr Hegazy, Amr Alanwar
- Venue / year: arXiv preprint, 2025
- Identifier: arXiv:2503.03911
- Page fetched: https://arxiv.org/abs/2503.03911
- Serves: Ingénieur ch1 section "The safety problem"; ch6 (limitations)
- Supports the claim: Shows what a guarantee over the reachable set would actually require. Cite
  it at the point where Ch. 1 declines to make one — "would require a proof over the reachable set
  that this work does not attempt" — so that the restraint is visibly informed rather than vague.

---

## Lower priority — speech-component justification and the dual-path pattern

For Ch. 2 §"Offline speech components" and for the concession in Ch. 1 §contributions that a fast
path is "a familiar pattern". Nothing verified here is a paper for openWakeWord or Silero VAD
specifically — see the notes.

### Speech Commands: A Dataset for Limited-Vocabulary Speech Recognition
- Authors (as shown on page): Pete Warden
- Venue / year: arXiv preprint, 2018
- Identifier: arXiv:1804.03209
- Page fetched: https://arxiv.org/abs/1804.03209
- Serves: Ingénieur ch2 section "Offline speech components"
- Supports the claim: The standard reference for why keyword spotting is a distinct task from
  full ASR and needs its own reproducible accuracy methodology — the justification for evaluating
  Branch A on a false-accepts-per-hour / false-rejects-per-class curve (NFR-15/16) rather than on
  a transcription metric.

### Dual-Attention Neural Transducers for Efficient Wake Word Spotting in Speech Recognition
- Authors (as shown on page): Saumya Y. Sahai, Jing Liu, Thejaswi Muniyappa, Kanthashree M. Sathyendra, Anastasios Alexandridis, Grant P. Strimel, Ross McGowan, Ariya Rastrow, Feng-Ju Chang, Athanasios Mouchtaris, Siegfried Kunzmann
- Venue / year: Proc. IEEE ICASSP 2023
- Identifier: arXiv:2304.01905
- Page fetched: https://arxiv.org/abs/2304.01905
- Serves: Ingénieur ch2 section "Offline speech components"; ch1 section "Contributions"
- Supports the claim: Wake-word detection used to select which compute branch runs per audio
  frame — prior art that a keyword spotter can gate a second, heavier path. Cite it where Ch. 1
  concedes the dual path is a familiar pattern, so the concession is evidenced.
- **Verified 2026-09-23:** key `dualattn2023` — record OK (ICASSP 2023, doi:10.1109/ICASSP49357.2023.10096075) / claim CORRECTED: wake-word spotting selects which branch *of its attention networks* to execute per audio frame, inside one ASR model — and the wake-word frames get the **cheaper** branch (−90% FLOPs on those frames). So it is prior art for per-frame keyword-driven switching of compute paths, not for a keyword spotter gating a separate, heavier second path; its purpose is compute saving, not safety.

### RelayS2S: A Dual-Path Speculative Generation for Real-Time Dialogue
- Authors (as shown on page): Long Mai, Junli Liang
- Venue / year: EMNLP 2026 Findings, 2026
- Identifier: arXiv:2603.23346
- Page fetched: https://arxiv.org/abs/2603.23346
- Serves: Ingénieur ch1 section "Contributions"; ch2
- Supports the claim: An explicit fast-path/slow-path speech architecture with a verifier deciding
  whether to commit the fast path's output — the same shape as Branch A / Branch B but with the
  fast path serving *quality of experience*, not safety. A clean contrast for showing that what is
  novel here is the membership rule, not the topology.
- **Verified 2026-09-23:** key `relays2s` (already in bib) — record OK (v2, 9 Sep 2026; primaryClass cs.AI added; EMNLP 2026 Findings per comments, kept as preprint) / claim OK: fast path = duplex speech-to-speech model drafting a prefix, slow path = cascaded ASR→LLM (GPT-4.1), a lightweight learned verifier gates the handoff; P90 first-chunk latency 81 ms vs 1,006 ms.

### MIRA: Real-Time Full-Duplex Human-Robot Interaction for Embodied Companions
- Authors (as shown on page): Lijian Lin, Ye Zhu, Fan Zhang, Yunfei Liu, Baofeng Li, Xianwen Zeng, Jianan Wang, Yu Li
- Venue / year: arXiv preprint, 2026
- Identifier: arXiv:2609.24547
- Page fetched: https://arxiv.org/abs/2609.24547
- Serves: Ingénieur ch1 section "Contributions"; ch2
- Supports the claim: A dual-timescale interaction policy with a robot-side execution layer
  enforcing physical safety at the control rate, and motion committed only as a short cancellable
  prefix. The "commit only what you can cancel" idea is the closest published relative of the
  hard geometric clamp at the integrator, and the dual-timescale policy is the closest relative of
  the preemption requirement (NFR-17).

---

## UNVERIFIED — could not fetch

These look directly relevant but the primary page returned 403 / an empty body / a timeout during
this pass. **Do not cite any of them until the primary page has been opened by hand.** Author
lists below are as reported by the search index, not as read from the publisher page, and must be
treated as unreliable.

- *Designing a Speech Interface for Voice activated MAV Ground Control Station* — IEEE Xplore
  document 9012132. https://ieeexplore.ieee.org/document/9012132 returned an empty body to both
  WebFetch and the browser. Likely the best single "earlier speech-interface work for UAV ground
  control" citation; worth retrieving through the university's IEEE subscription.
- *Research and Application of Human-computer Interaction Technology based on Voice Control in
  Ground Control Station of UAV* — IEEE Xplore document 9344892. Same failure.
- *Unmanned Aerial Vehicle (UAV) Control Through Speech Recognition* — IEEE Xplore document
  10675578. Same failure.
- *Voice enabled smart drone control* — IEEE Xplore document 7993759. Same failure.
- *Multimodal speech recognition for unmanned aerial vehicles* — ScienceDirect
  pii/S0045790620307904 (Computers & Electrical Engineering). 403 to WebFetch and to the browser.
  Reportedly uses drone imagery to improve recognition of spoken commands, with a 37-participant
  NASA-TLX workload study — the workload evidence would strengthen Ch. 1 §operational-context.
- *In-Vehicle Speech Recognition for Voice-Driven UAV Control in a Collaborative Environment of
  MAV and UAV* — doi:10.3390/aerospace10100841 (MDPI Aerospace 10(10):841). MDPI returned 403 and
  the browser was denied navigation.
- *Unmanned Aerial Vehicle Control through Domain-Based Automatic Speech Recognition* —
  doi:10.3390/computers9030075. Appears to be the journal version of arXiv:2009.04215, which *was*
  verified above; prefer the journal record once it can be opened.
- *Leveraging Large Language Models for Real-Time UAV Control* — doi:10.3390/electronics14214312
  (MDPI Electronics 14(21):4312). Reported to claim ~95% recognition accuracy at 300–500 ms
  end-to-end; if that holds it is a latency data point worth having in Ch. 2.
- *Using Natural Language to Enable Mission Managers to Control Multiple Heterogeneous UAVs* —
  Trujillo, Puig-Navarro, Mehdi, McQuarry (approximate), NASA NTRS 20160010334. ntrs.nasa.gov
  timed out. This is the pre-LLM precedent for natural-language control of *multiple* UAVs by one
  operator and is the closest historical analogue to the one-operator-five-aircraft framing; worth
  the effort to retrieve.
- *Towards human-centered interaction with UAV swarms: Framework, system design, and user study* —
  ScienceDirect pii/S3050741325000291. Not fetched.

---

## Notes for the author

**Does any system already do what the thesis claims no system does?**

No. On the evidence gathered here the four-way conjunction — fully offline, grammar-constrained,
dual-path, on a single single-board computer — is not met by any system whose primary page was
fetched. But the claim is more exposed than the current scaffold assumes, and two of the four
conjuncts are individually well covered by 2026 work. Take the threats in order.

1. **CommandSwarm (arXiv:2605.07764) is the system to name before someone else names it for you.**
   It is speech-to-swarm, it uses a whitelist of executable swarm primitives with a deterministic
   parser as an execution gate, it uses constrained prompting, and it runs open-source models under
   4-bit quantisation — so *offline-capable*, *constrained*, and *swarm* are all present in one
   paper. What it does not have: the paper reports no emergency-stop or reflex path and no
   preemption of any kind; its own ASR figure is Whisper-medium at roughly 5.2 s per utterance,
   which is an order of magnitude outside NFR-2 let alone NFR-1; the models are 6.7B–14B, which
   will not meet a throughput floor on a Pi 5; no deployment hardware is stated at all; and the
   evaluation is simulation-only, with the authors themselves flagging the absence of real-robot
   latency validation. **The dual-path conjunct and the single-SBC conjunct both survive against
   it, and they are the two doing the work.** Ch. 2 §"Gap" should cite it explicitly and concede
   the overlap on the other two conjuncts — the gap statement is stronger, not weaker, for saying
   "a 2026 system already does the offline-and-constrained half; what none does is bound the
   stopping command independently of the parse path, on a device this size."
   *Correction (verified 2026-09-23):* the 5.2 s figure is Whisper-medium **speech translation**
   (into English), and it is the option the paper rejects — its chosen front end is SeamlessM4T
   v2-large at ~4.0 s, still an order of magnitude outside NFR-2. "Offline-capable" is our
   inference from open 4-bit models; the paper never claims offline operation and names no
   hardware. Its evaluation scores generated XML (BLEU/ROUGE-L/parser acceptance) — trees are not
   executed and scored in the simulator — and its safety classifier is "not independently
   evaluated". It lists "emergency stop mechanisms" only among safeguards real deployment
   "should require". Say "constrained prompting", not "constrained decoding".

2. **SkySim (arXiv:2602.01226)** independently arrives at the same two-tier idea as your
   architecture — LLM planning above, an artificial-potential-field safety layer at 20 Hz below,
   handling collision avoidance, kinematic limits and geo-fencing — for swarms of 3, 10 and 30
   drones. It is cloud-LLM (Gemini) and simulation-only, so it threatens neither *offline* nor the
   Pi. But it does weaken any phrasing that presents "separate the planner from a low-level safety
   enforcement layer" as itself novel. Ch. 1's C4 already avoids that trap by claiming the
   *membership rule* rather than the separation; keep that discipline in Ch. 2 §"Gap".
   *Correction (verified 2026-09-23):* the model is **Gemini 3.5 Pro** (cloud API). Geo-fencing is
   done by the planner node rejecting out-of-bounds waypoints (fallback: position hold), not by
   the APF; the APF does inter-agent repulsion, with a 0.5 m/s velocity clamp. Input is **typed
   text — SkySim has no speech path**. Planning latency is 34–50 s on average (outliers >100 s).
   Note that it also holds on malformed LLM output, which is close to this work's hold-on-rejection
   rule — concede that too.

3. **The dual-path topology is prior art and should be cited as such, not discovered.**
   RelayS2S (arXiv:2603.23346) runs an explicit fast-path/slow-path speech architecture with a
   verifier; the ICASSP 2023 dual-attention transducer (arXiv:2304.01905) uses wake-word detection
   to select a compute branch per frame; MIRA (arXiv:2609.24547) pairs a dual-timescale policy with
   a cancellable-prefix commitment and a control-rate safety layer. Ch. 1 §contributions already
   concedes "a fast path that bypasses validation is a familiar pattern" — good. Ch. 2 should
   discharge that concession with these three citations rather than leaving it as a bare admission,
   because an examiner who knows this literature will otherwise supply the citations themselves.
   *Correction (verified 2026-09-23):* the ICASSP 2023 paper switches between two branches *of its
   attention networks inside one ASR model*, per frame, and the wake-word frames get the cheaper
   branch (for compute saving). Cite it as per-frame keyword-driven switching of compute paths, not
   as a keyword spotter gating a separate heavier path.

4. **A wording risk, not a novelty risk.** The phrase "fully offline" is safe. "Grammar-constrained"
   is safe as long as Ch. 2 does not survey constrained decoding (Table 3 forbids it) — cite the
   *systems* that constrain output (SayCan by affordance, Landau & van Delden by regular
   expressions, CommandSwarm by whitelist-plus-parser) rather than the decoding methods, and the
   boundary holds. "Single SBC" is the most defensible conjunct in the set: nothing academic was
   found that runs a speech-to-swarm command pipeline on a Raspberry Pi-class board. Note that
   hobbyist projects doing offline Vosk-or-Whisper voice control of a single drone on a Pi are
   abundant; they are not citable and not swarm systems, but be ready to say so out loud at the
   defence rather than be surprised by the question.
   *Correction (verified 2026-09-23):* the Landau & van Delden abstract names the Nuance platform
   but does not say it is cloud-hosted — do not write "cloud" for it unless the paper itself is
   read. For "systems without any verification gate", do not cite ChatGPT for Robotics: it has a
   human-on-the-loop gate; what it lacks is an *automated* one. Code as Policies does not claim
   its code is unbounded; cite its own admission that it "assumes all given instructions are
   feasible".

**On GAP 2.** The three principles in Ch. 1 §safety-problem map cleanly onto owners: STPA /
Leveson & Thomas for the wrong-state command and for hazard analysis generally, IEC 61508 for the
safe state, Avizienis et al. for the fail-safe/fail-silent vocabulary, AMLAS for "accuracy is not
a safety argument", Guerin et al. for what to measure instead, Burns & Davis for the
mixed-criticality reading of NFR-1. Four or five well-placed citations in the opening two
paragraphs are enough; the rest of that section genuinely is your own contribution and should stay
uncited — do not let a citation pass dilute the argument that is actually yours.

**On the speech-tool justification.** Nothing was found that is a citable paper for openWakeWord
or for Silero VAD; both are software releases, not publications, and the comparative VAD material
that surfaced was vendor blog content, which fails the sourcing bar. If Ch. 2 §"Offline speech
components" needs to justify each choice, the honest route is (a) Warden's Speech Commands paper
for the evaluation methodology of the keyword class, (b) your own Exp-2 ROC curve as the evidence
for the operating point, and (c) an explicit statement that the VAD and wake-word components were
selected on measured on-device latency and licence rather than on published comparative
benchmarks — which is true, defensible, and better than citing a blog.
