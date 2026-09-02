# Citation / presentation review: thesis/ingenieur/ch3_architecture.tex (Ingénieur Ch3)

Reviewed state: the working-tree file of 2026-09-24, 500 lines. It includes the author's two-sentence
reflex/cortex analogy at lines 43-48 (issue 11 comment of 2026-09-24). Line numbers below are for this
state and match the regenerated pre-review report (WARN lines 277/287/309/353/473/483/489).
Dimensions covered: D5, D7, D8, D9, D11, D12 and fig:architecture. D1/D2/D4/D6/D10 belong to the
argument agent and D3 to the script.

## 1. Verdict

The chapter builds cleanly from scratch and uses no project-internal vocabulary. Five of its seven
citation uses are fully supported by the primary sources. There is one BLOCKER: fig:architecture draws
the semantic validator (layer 2) only on the parse path, before the bus, so reflex commands appear to
skip it. That contradicts §3.1 (l.47-48), §3.2 (l.166-168), §3.3 (l.272-274) and the code
(`swarm/fsm.py:165`). The main MAJOR findings are these:
- The second openWakeWord citation (l.243) is only partial support: the false-accept argument is not in
  the source.
- The seeded "swarm onset" claim has no source.
- The "a context-free grammar cannot bound a value" claim is technically wrong as worded.
- The core-allocation caption contradicts its own row 0.
- The Silero bib entry is incomplete.

## 2. Scorecard

| Dim | Result |
|---|---|
| D5 References | ISSUES (5): 4 MAJOR, 1 MINOR |
| D7 Figures and tables | ISSUES (4): 1 BLOCKER, 1 MAJOR, 2 MINOR |
| D8 Language and style | ISSUES (8): 4 MINOR, 4 NIT |
| D9 LaTeX and build | ISSUES (1, NIT only): clean build, 0 errors, 0 Overfull |
| D11 Self-containment | ISSUES (1): 1 MINOR |
| D12 Headings and register | ISSUES (6): 3 MINOR, 3 NIT |

## 3. Findings

| # | Sev | Dim | file:line | Quoted text | Problem | Evidence | Proposed fix |
|---|---|---|---|---|---|---|---|
| 1 | BLOCKER | D7e | ch3_architecture.tex:71, 84-85 (figure) | `\node[stage] (val) ... {Validator\\(layer 2)}` on the parse path; `\draw[flow] (kws.east) -\| ... {fixed command} (bus.north)` | The figure places the semantic validator (layer 2) only on the parse path, on the Pi, before the bus. The reflex arrow runs from the spotter straight to the bus, and the workstation node lists only "State machine (layer 3), ordering rule". A reader of the figure concludes that reflex commands never pass layer 2. | Prose says the reverse. l.47-48: "its commands are checked by the validator and the state machine like any other". l.166-167: "pass the semantic validator and the state machine like any other message". l.272-273: "The second and third layers apply to every command from either path". Code: `swarm/fsm.py:165` `cmd = validate(cmd_input)` inside `handle_command`, at the consumer, for both paths; `runtime/pipeline.py:153` also validates parse-path output on the Pi before publishing. The caption's "the state machine validates every command" blurs the figure's own layer-2/layer-3 labels. | Relabel the workstation node "Validator (layer 2),\\ state machine (layer 3),\\ ordering rule". Add one caption sentence: "Layer 2 runs on the Pi before a parse-path command is published, and again at the consumer for every command from either path." Optionally rename the Pi-side node "Validator (layer 2, first pass)". |
| 2 | MAJOR | D5b | ch3_architecture.tex:242-245 | "A keyword classifier scores a fixed window of audio~\cite{oww}, and a single short word fills little of it, so a one-word class gives the classifier less evidence and invites more false accepts on continuous speech." | PARTIAL support. The openWakeWord documentation never says the classifier scores a fixed window. It says models process 80 ms frames and return a score per frame. The fixed window is visible only in the source code. Nothing in the repository says a shorter phrase raises false accepts. The model pages say the opposite kind of cost: shortened phrases give higher false *rejects*. | README "Project Goals" item 2: "Models process a stream of audio data in 80 ms frames". Code: `openwakeword/train.py:26` `input_shape=(16, 96)` and l.826 `seconds_per_example=1280*input_shape[0]/16000` (16 embeddings, 1.28 s). docs/models/hey_jarvis.md l.5: "just 'jarvis' ... likely with higher false-reject rates". The project's own head is 16 embeddings, about 1.975 s (`train/train_wake.py:79-81`). No README, model page or docs/*.md mentions false accepts versus phrase length. | Keep `\cite{oww}` only on the fixed-window fact and state it concretely: "The spotter's classifier scores a fixed window of 16 feature frames, about 2~s of audio in this deployment~\cite{oww}". Then present the consequence as the design's own reasoning, with no citation: "a single short word would occupy little of that window, and the design assumes that a two-word phrase gives the classifier more evidence against continuous speech". If the project's keyword evaluation measures this, point to it. Otherwise cut the false-accept clause. |
| 3 | MAJOR | D5c | ch3_architecture.tex:245-246 | "The shared word \emph{swarm} supplies an onset that is uncommon in ordinary speech to both classes at once." | An uncited factual claim about word frequency in speech, and the seeded finding. No entry in `thesis/references.bib` supports it: I checked all 74 titles. The nearest are `speechcommands` (a dataset) and `dualattn2023` (compute switching), and neither addresses word rarity or phrase onsets. | references.bib title list; `.scratch/thesis-bibliography/ingenieur-candidates.md:383` ("Nothing verified here is a paper for openWakeWord or Silero VAD"). | Reword as a design choice: "The shared prefix \emph{swarm} was chosen because it is not a word the operator uses in other commands; whether it keeps false accepts low is measured, not assumed (Section~\ref{sec:...keyword evaluation})". Or cut the sentence. The next sentence, which says the prefix brings the classes closer acoustically, stands without it. |
| 4 | MAJOR | D5c | ch3_architecture.tex:283-284 | "a context-free grammar can limit how many digits a number has, not whether that number is an admissible altitude." | Technically incorrect as a general claim about the formalism. A bounded range of fixed-precision decimals is a finite language, so it is regular and expressible in GBNF by digit alternation. For example `("1"[0-5] \| [0-9]) ("." [0-9])?` spans 0-15.9. The true statement is narrower: GBNF has no numeric-range construct, and this grammar does not encode per-slot ranges. Master Ch3 itself states that "the grammar's language is finite" (`master/ch3_method.tex:110`). | Formal-language fact (every finite language is regular, hence context-free). `schema/cmd.gbnf` `num` rule (three integer digits, one decimal) as checked by the script. | Rewrite: "It does not bound a number's value: \gls{gbnf} has no numeric-range construct, and encoding each slot's range as digit patterns would duplicate the physical envelope inside the grammar. Every constraint on magnitude therefore falls to the second layer." The same wording is in `master/ch3_method.tex:97-98`, outside this review's scope; flag it to that document's reviewer. |
| 5 | MAJOR | D7e | ch3_architecture.tex:459-461 vs 467 | "Each path's work is pinned to its cores. The reflex path runs entirely on core~0, so no parse-path work is scheduled on the core that serves it." | The table's own row 0 assigns "the endpointer" to core 0. The chapter makes the endpointer a parse-path stage in l.34 ("a \gls{vad} model ... segments the stream"), in the figure caption l.106 ("the parse path endpoints the utterance"), and in the figure, where the "Parse path" tag is anchored on the endpointer node (l.93). So parse-path work does run on core 0. | l.467 row 0: "Audio frame loop: frame buffering, the endpointer, the keyword spotter and the reflex path's publication"; l.473-474 "gives it to both the endpointer and the keyword spotter". | Caption: "Core~0 runs the audio frame loop, which includes the reflex path and the parse path's endpointer. No work of the parse-path worker (recognition, decoding, validation) is scheduled on core~0." |
| 6 | MAJOR | D5e | references.bib `silero` | `title = {{Silero VAD}: Pre-trained Enterprise-Grade Voice Activity Detector}`, no `year` | The title and year disagree with the authors' own citation block on the primary page. The title there is longer and the year is 2024. The printed reference [12] shows no year. | silero-vad README "Citations": `title = {Silero VAD: pre-trained enterprise-grade Voice Activity Detector (VAD), Number Detector and Language Classifier}`, `year = {2024}`. | The author (not an agent, per SKILL §4) should add `year = {2024}`, plus a `version` or commit for the model actually used. Either use the full title or keep the short one knowingly. |
| 7 | MINOR | D5e | references.bib `llamacpp` | no `year`; `version = {b10863}` | The year is missing even though the cited build is dated. Reference [13] prints without a year. | GitHub release `b10863`: `published_at 2026-09-08`. | Add `year = {2026}`, matching `whispercpp`, whose commit 52a939a is dated 2026-09-04, so its 2026 is correct. |
| 8 | MINOR | D8e | ch3_architecture.tex:72 | `{Command bus\\UDP, \acrshort{json}}` | The figure prints "JSON" before the acronym is expanded. The first `\gls{json}` in the document is l.129, after the figure. In the PDF text, the figure's "UDP, JSON" (page 25) precedes "JavaScript Object Notation (JSON)" in the Command-bus paragraph. | `pdftotext` of the clean build: figure line 743, first expansion line 788. No `json` use in Ch1, Ch2 or the front matter. | Move the first expansion before the figure, e.g. l.36-37 "parses the transcript into a structured \gls{json} command". The figure's `\acrshort` then follows an expanded use. |
| 9 | MINOR | D8e | ch3_architecture.tex:72, 129 | "single-line \gls{json} messages over UDP" | UDP is an acronym typed by hand, with no key in `shared/acronyms.tex`, and it is never spelled out anywhere in the Ingénieur. | `grep -rn 'UDP\|User Datagram' thesis/ingenieur/*.tex` gives only these two lines. | Add `\newacronym{udp}{UDP}{User Datagram Protocol}` and write `\gls{udp}`. |
| 10 | MINOR | D11c | ch3_architecture.tex:50-51 | "fine-tuned and quantised to Q4\_K\_M." | The code Q4\_K\_M is used without definition in this document. It appears nowhere in Ch1, Ch2 or the front matter, and it is left uncited. | `grep -rn 'Q4' thesis/ingenieur/` finds only this line. | "quantised to 4 bits per weight with the Q4\_K\_M scheme of \texttt{llama.cpp}~\cite{llamacpp}". The bib note already names k-quant schemes. |
| 11 | MINOR | D7b | ch3_architecture.tex:86-88, 104-112 | "A reflex-path trigger cancels any decode in progress (dashed)" | The figure has two dashed arrows with different meanings, the cancellation signal and the Wi-Fi hop, and the caption explains only one. The labels "(layer 2)" and "(layer 3)" appear before §3.3 introduces the layers, and the caption does not gloss them. "offline", "50 Hz" and "$N = 5$" are also unexplained, so the caption is not self-contained. | Figure source l.86 and l.88 both use `dashed`; the caption has no mention of layers, 50 Hz or $N$. | Draw the Wi-Fi hop with its own style (e.g. `densely dotted`) or say in the caption "dashed: the cancellation signal and the Wi-Fi hop". Add "layers 2 and 3 are the semantic validator and the flight state machine of Section~\ref{sec:validation-layers}; the controller runs at 50~Hz for $N = 5$ simulated vehicles". |
| 12 | MINOR | D7e | ch3_architecture.tex:116 vs 128, 131-132 | "Everything up to and including the command bus runs on the Raspberry~Pi~5." | The prose disagrees on where the bus sits. l.128 says "The two machines are joined by a minimal publish--subscribe bus", and l.131-132 puts its consumer on the workstation. The figure follows l.116 and draws the whole bus inside the Pi box. | l.116, l.128, l.131-132; figure l.97 `fit=(mic) (ta) (tb) (val) (bus)`. | l.116: "Everything up to and including publication on the command bus runs on the Raspberry~Pi~5". The figure can stay as drawn. |
| 13 | MINOR | D8g | ch3_architecture.tex:191 | "This is the test that answers the objection of the previous paragraph" | Wrong pointer. The previous paragraph ("Latency-decisive", l.179-186) raises no objection. The problem answered here, that no layer can detect a false accept, is stated at l.169-177, in the section's opening paragraph. | l.169: "The consequence is that no layer can detect a false accept." | "This is the test that answers the problem stated at the opening of this section". |
| 14 | MINOR | D8 (terminology) | ch3_architecture.tex:379-380 vs 406-407 | caption: "$T_0$, the instant the endpointer declares the utterance over"; prose: "$T_0$ is the time of the last audio frame in the buffer at the moment the endpointer declares the utterance over" | $T_0$ has two different definitions three dozen lines apart: a declaration instant and a frame timestamp. Ch1 l.192 uses the first. | l.379-380, l.406-407, `ingenieur/ch1_introduction.tex:192`. | Use one definition. Either the caption says "$T_0$, the end of speech (defined in the text)", or the prose sentence is marked explicitly as a refinement of Ch1's definition. |
| 15 | MINOR | D12a | ch3_architecture.tex:353 | `\paragraph{What the layers do not catch.}` | The heading is a free-relative clause that asserts a claim (the layers miss something), not a noun phrase. | SKILL §2 "Headings": "A heading is a noun phrase, not a sentence or a claim." | `\paragraph{Residual error classes.}` |
| 16 | MINOR | D12a | ch3_architecture.tex:489 | `\paragraph{What pinning cannot isolate.}` | Same problem: a clause that states a limitation as a claim. | SKILL §2 "Headings". | `\paragraph{Limits of core pinning.}` (or `\paragraph{Shared resources.}`) |
| 17 | MINOR | D12c | ch3_architecture.tex:437-438 | "the stage rows serve to locate a miss, not to excuse one." | An aphoristic chiasmus, the register SKILL §2 "Register" rules out. | SKILL §2: "No rhetorical flourishes or aphorisms". | "the stage rows attribute a miss to a stage; they do not change whether the end-to-end target is met." |
| 18 | NIT | D8g | ch3_architecture.tex: 15, 39, 123, 131, 231, 263, 270, 287, 304, 343, 369, 440, 452, 476 | (see list in §3a below) | 14 sentences exceed about 40 words. | Word counts in §3a. | Split the longest (l.39, 131, 263, 270, 287) at their semicolons or colons. |
| 19 | NIT | D8 (terminology) | ch3_architecture.tex:391 | "Speech recognition (whisper \texttt{tiny.en}, 3 threads)" | The tool is named inconsistently: "whisper tiny.en" here, "\texttt{whisper.cpp tiny.en}" at l.35 and in Ch1 l.129. | l.35, l.391. | "(\texttt{whisper.cpp tiny.en}, 3 threads)". This row name is also matched by the review script; update both together. |
| 20 | NIT | D8a | ch3_architecture.tex:428 | "Transcription and decoding are each allowed about a second" | A vague qualifier where exact figures sit in the table just above. | tab:stage-budget: 1,200 ms and 1,100 ms. | "Transcription and decoding are allowed 1{,}200 and 1{,}100~ms". |
| 21 | NIT | D8a | ch3_architecture.tex:252 | "The most obvious third class is excluded deliberately." | "obvious" belongs to the anti-fluff family ("obviously", SKILL §2). | SKILL §2 "Zero marketing adjectives". | "A third candidate class, \texttt{resume}, is excluded." |
| 22 | NIT | D12c | ch3_architecture.tex:236-237, 255-256 | "is a decision to lose the airframe"; "where the added 2.35~s costs nothing" | Figurative and absolute phrasing where a plain statement is available. | SKILL §2 "Register". | "would let the airframe fall from up to 15~m"; "where the added 2.35~s has no safety consequence". |
| 23 | NIT | D12c / D5c | ch3_architecture.tex:43-46 | "It borrows the distinction between a reflex and cortical deliberation ... A spinal reflex acts before the brain is consulted" | A figurative analogy with an uncited physiological claim. The author added it deliberately (issue 11 comment, 2026-09-24), so this is a wording note, not a request to remove it. | SKILL §2 "Register". | If kept, drop "cortical" and "spinal ... brain" and use one plain sentence: "The name borrows from the biological reflex: two stimuli receive a fixed response without interpretation, and everything else is interpreted before it is acted on." Keep the "The analogy stops at one point" sentence as written. |
| 24 | NIT | D9c | ch3_architecture.tex:19, 146 | "realised in Chapter~\ref{chap:implementation}"; "for a reason given in Chapter~\ref{chap:implementation}" | Both point at the whole chapter when Ch4 already has the precise labels. | `ch4_implementation.tex` defines `sec:swarm-controller` and `sec:runtime`. | `Section~\ref{sec:swarm-controller}` (l.19); `Section~\ref{sec:runtime}` (l.146). |

### 3a. Sentences over about 40 words (D8g)

The counts are approximate: `\ref`/`\cite` count as one token and heading words are excluded.

| line | words | opening |
|---|---|---|
| 15 | ~43 | "Section~\ref{sec:safety-problem} reduced the safety problem to three requirements: ..." |
| 39 | ~51 | "The parse path cannot begin transcribing until the endpointer has confirmed ..." |
| 123 | ~41 | "The state machine is placed beside the controller rather than beside the parser ..." |
| 131 | ~51 | "The rule deciding whether a message may take effect belongs to its consumer ..." |
| 231 | ~41 | "The hover is already the state every rejection on the parse path resolves to ..." |
| 263 | ~50 | "For the present vocabulary the rule yields exactly two classes; ..." |
| 270 | ~47 | "Three layers stand between a decoded command and the vehicles, ..." |
| 287 | ~50 | "The first enforces the slots each intent requires: ..." |
| 304 | ~44 | "A command whose intent is right and whose magnitude is out of range, ..." |
| 343 | ~44 | "On the ground, during a landing and after an abort, a hold is not legal either, ..." |
| 369 | ~44 | "The latency budget gives every stage of both paths a target at the 95th percentile, ..." |
| 440 | ~43 | "Capture and buffering sit before $T_0$: ..." |
| 452 | ~43 | "The Raspberry~Pi~5 has four Cortex-A76 cores, and the design divides them ..." |
| 476 | ~41 | "If the loop could wait for a transcription or a decode, ..." |

### 3b. Checked and clean

- D5a: all 6 keys resolve (`check_tex.py`: 6 cites, 74 bibitems, no dangling `\cite`).
- D5f: every citation sits on the clause it supports; none is dumped at a paragraph end.
- D8d: British spelling is consistent (quantised, optimisation, realised; no -ize/-yze forms in prose).
- D8f: no non-ASCII characters.
- D9b: no `\TODO`, `\CHECK` or `\figtodo`.
- D9d: `~` is present before every `\cite` and `\ref` and before every unit.
- D11a/b: no prd, spike, gate, sprint, D-number, ADR, Branch A/B, NFR-/FR-, RQ or Exp- in prose. `T_0` is
  defined at first use (l.379) and `p95` in Ch1 (l.32, l.161).
- D11d: Master material is named as "\emph{M\'emoire de Master}" with no chapter numbers.
- D12b: section titles are sentence case, consistent with every other chapter.
- D7a: every float is referenced before it appears: fig l.31/113, tab:membership l.198/209,
  tab:legality l.316/326, tab:stage-budget l.372/385, tab:core-allocation l.453/462. The prose
  interprets each one.
- D7c: the figure is native TikZ (vector). Its scaled text measures about 9 pt in the PDF, which is
  legible.
- D7d: no table needs xltabular. The last row of each of the four tables is present in the built PDF.

## 4. Citation table (D5b)

| Key | file:line | Claim it carries | Verdict | Note (quote <= 15 words from the source) |
|---|---|---|---|---|
| oww | ch3_architecture.tex:32 | The reflex path is a two-class keyword spotter that listens continuously. | SUPPORTS | README: "Models process a stream of audio data in 80 ms frames". The two classes are the project's own heads on the openWakeWord backbone (`train/train_wake.py:14`). |
| silero | ch3_architecture.tex:34 | A VAD model segments the stream into utterances. | SUPPORTS | README: "pre-trained enterprise-grade Voice Activity Detector". The segmentation rule (450 ms silence) is the project's own (`runtime/vad.py`). |
| whisper | ch3_architecture.tex:35 | `whisper.cpp tiny.en` performs STT. | SUPPORTS (model) | PMLR v202 pp. 28492-28518. Table 1: "Tiny 4 384 6 39M"; the paper also trains English-only models. |
| whispercpp | ch3_architecture.tex:35 | (same sentence: the implementation) | SUPPORTS | README: "High-performance inference of OpenAI's Whisper automatic speech recognition (ASR) model". models/README lists `tiny.en`. |
| llamacpp | ch3_architecture.tex:37 | The SLM parses under a decoding grammar. | SUPPORTS | grammars/README (linked from the repo README): GBNF defines "formal grammars to constrain model outputs in llama.cpp". |
| qwen25 | ch3_architecture.tex:50 | The language model is Qwen2.5-0.5B. | SUPPORTS | arXiv 2412.15115 Table 1 row: "0.5B \| 24 \| 14 / 2 \| Yes \| 32K / 8K". |
| oww | ch3_architecture.tex:243 | A keyword classifier scores a fixed window; a short word fills little of it and invites more false accepts. | PARTIAL | The fixed window appears only in code (`train.py` `input_shape=(16, 96)`). The docs say shortened phrases give "higher false-reject rates", not more false accepts. See finding 2. |

Bib metadata check (D5e). oww: 2024 and v0.6.0 are correct (release 2024-02-11). whisper: title,
authors, volume, pages and year match PMLR. whispercpp: 2026 is correct (commit 52a939a dated
2026-09-04). qwen25: title, 2024 and eprint are correct; the corporate author "Qwen Team" is an
acceptable rendering of the arXiv "Qwen: An Yang, ..." line. silero: see finding 6. llamacpp: see
finding 7. All six entries carry a url or eprint.

## 5. Figure check (fig:architecture)

| fig:architecture element | prose line | agrees? |
|---|---|---|
| Vector format (native TikZ) | n/a | Yes |
| Referenced before it appears, and interpreted | l.31, l.30-48, l.116-126 | Yes |
| Mic, ring buffer, spotter, endpointer, STT, SLM, validator and bus inside the "Raspberry Pi 5" box | l.116 "Everything up to and including the command bus runs on the Raspberry~Pi~5" | Yes with l.116. **Partly no** with l.128 and l.131-132, where the bus joins the two machines and its consumer is on the workstation (finding 12). |
| State machine, controller and simulated swarm inside the "Workstation" box | l.116-118, caption l.110-111 | Yes |
| Ordering rule drawn in the state-machine node, on the workstation | l.131-132 "belongs to its consumer, beside the state machine"; l.151 | Yes |
| Only the bus-to-state-machine arrow crosses the Pi/workstation boundary, labelled Wi-Fi | l.128-129 (UDP bus), l.443-444 "The wireless hop from the device to the workstation sits after publication" | Yes |
| Bus node labelled "UDP, JSON" | l.128-129 | Yes. "JSON" prints before its expansion (finding 8). |
| Validator (layer 2) only on the parse path, on the Pi, before the bus; the reflex arrow bypasses it | l.47-48, l.166-168, l.272-274; `swarm/fsm.py:165` | **No: BLOCKER** (finding 1). The Pi-side validator agrees with l.37 and tab:core-allocation row 1-3 ("then validation and publication"), but the second, consumer-side layer-2 pass that reflex commands go through is missing. |
| State machine labelled layer 3 | l.309 onward | Yes, but the label is used before §3.3 numbers the layers and the caption does not gloss it (finding 11). |
| Reflex path: spotter to bus, "fixed command" | l.32-34, tab:core-allocation row 0 ("the reflex path's publication" on core 0) | Yes |
| Dashed "cancel decode" arrow from spotter to SLM | l.158-160 (decode cancelled, the three inference cores released); l.486-487 | Yes. The dashed style is shared with the Wi-Fi arrow (finding 11). |
| Endpointer tagged under "Parse path" | l.34, caption l.106; but tab:core-allocation l.467 runs the endpointer on core 0 with the spotter | The figure agrees with the prose. The core-allocation caption, which claims no parse-path work on core 0, contradicts both (finding 5). The figure shows no core assignment, which is not required, so there is no direct figure/table conflict. |
| STT, SLM and validator on one worker (cores 1-3) | tab:core-allocation row 1-3, l.483-487 | Not drawn. Nothing in the figure contradicts it. |
| "Swarm controller 50 Hz", "Simulated swarm $N = 5$" | Ch1 l.69, l.131 (50 Hz, $N = 5$) | Yes. Not glossed in the caption (finding 11). |
| Caption: what, components, the two paths, takeaway | l.104-112 | Mostly. It covers the components, both paths, preemption, ordering and placement. It lacks a legend for the second dashed style, the layer labels and 50 Hz / $N$ (finding 11), and it blurs layer 2 and layer 3 ("the state machine validates every command"). |

## 6. Heading table (D12)

| line | heading | verdict | replacement |
|---|---|---|---|
| 12 | Architecture and design | OK (prd §3.1 title, sentence case) | none |
| 28 | Dual-path decomposition | OK | none |
| 116 | Placement. | OK | none |
| 128 | Command bus. | OK | none |
| 139 | Prompt and prefix. | OK | none |
| 149 | Preemption and ordering. | OK | none |
| 164 | Reflex-path membership rule | OK | none |
| 179 | Latency-decisive. | OK (the name of test 1, used in tab:membership's header) | none |
| 188 | Fail-safe under false accept. | OK (the name of test 2; 5 words) | none |
| 268 | Three validation layers | OK. "Three" is a count from the prd outline, not a result. | none |
| 277 | Layer 1: the decoding grammar. | **PASS (WARN cleared).** "1" is an identifier: l.270-275 introduce the layers in order (first, second, third) and the figure uses the same numbering. It is not a result. | Optional: "Decoding grammar." This would also remove the figure's forward use of "layer N" (finding 11). |
| 287 | Layer 2: the semantic validator. | **PASS (WARN cleared).** Identifier, as above. | Optional: "Semantic validator." |
| 309 | Layer 3: the flight state machine. | **PASS (WARN cleared).** Identifier. At 6 words it is marginally over "about five". | Optional: "Flight state machine." |
| 353 | What the layers do not catch. | **FINDING 15 (MINOR).** A clause stating a claim, not a noun phrase. | "Residual error classes." |
| 367 | Latency budget | OK | none |
| 405 | Anchors. | OK | none |
| 418 | Endpointing. | OK | none |
| 428 | Stage allowances. | OK | none |
| 440 | Outside the budget. | OK (prepositional noun phrase, a scope label, not a claim) | none |
| 448 | Resource allocation | OK | none |
| 473 | Core 0. | **PASS (WARN cleared).** "0" names a physical core, defined in tab:core-allocation (l.467), which appears just above. | Optional: "Audio core." |
| 483 | Cores 1--3. | **PASS (WARN cleared).** Identifier, as above (l.468). | Optional: "Inference cores." |
| 489 | What pinning cannot isolate. | **FINDING 16 (MINOR).** A clause stating a limitation. | "Limits of core pinning." |
| 496 | Memory. | OK | none |

Capitalisation is consistent: sentence case for chapter and sections, and sentence case with a final
period for `\paragraph` lead-ins.

## 7. Build result (D9e)

Command: `rm -rf thesis/build/ingenieur && cd thesis && latexmk main_ingenieur.tex`. The main file is
`thesis/main_ingenieur.tex`, and `.latexmkrc` pins XeLaTeX.

- latexmk exited 0; the PDF is 38+ pages, 416,906 bytes.
- `grep -c '^!' main_ingenieur.log` = 0.
- No `Citation ... undefined`, `Reference ... undefined` or `Float too large`.
- There are no Overfull or Underfull `\hbox` lines anywhere in the log, so none in ch3_architecture.tex.
- The only warnings are package/font notes outside Ch3 (microtype footnote patch, extsizes, biblatex
  Arabic, Amiri small caps).
- Ch3 starts at PDF page 23. Figure 3.1 is on p.25; the 4 tables are Tables 3.1-3.4.
- `tools/check_tex.py thesis/ingenieur/ch3_architecture.tex` (without `--xelatex`) reports 9 `\ref`
  problems, all cross-chapter. Every one resolves in the full build, which has no undefined references.
  The single note is that `chap:architecture` is never referenced within the file; Ch1 references it 9
  times.

## 8. UNVERIFIED

1. **openWakeWord Colab training notebook.** The notebook linked from the README (Google Colab, id
   1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb) could not be opened with the tools available. It may contain
   guidance on phrase length or syllable count. If it does, it could support the false-accept clause of
   l.243-245 (finding 2) and possibly the "onset" rationale (finding 3). The author should check it
   before cutting. The repo's `notebooks/automatic_model_training.ipynb`, README, `docs/*.md` and
   `docs/models/*.md` were read, and none of them supports either clause.
2. **Keyword evaluation as a substitute source.** I did not check whether the project's keyword-spotter
   evaluation (`results/wake_training.*`, the Ch5 keyword evaluation) measures false accepts for one-word
   versus two-word classes. If it does, it would be the right evidence for l.243-245 in place of
   `\cite{oww}`.
3. **Figure 3.1 rendering.** I checked the figure's placement and text size from `pdftotext -bbox`, not
   visually. Overlap between the "cancel decode" label and the "Parse path" tag was not inspected.
