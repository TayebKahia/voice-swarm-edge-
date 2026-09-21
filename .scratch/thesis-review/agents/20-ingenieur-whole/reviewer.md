# Issue 20 -- whole-document review of the Ingénieur (Template B, seven chapters in two parts), reviewer report

## 0. Header

- Reviewed: `thesis/main_ingenieur.tex` as a whole at HEAD `398b35a` (the only commit after
  `e4d2e4f` is a STATE.md entry; no `thesis/` file changed during the review, and this review edited
  none). Read in full: title page, shared dedication and acknowledgements, the English, French and
  Arabic abstracts, `shared/acronyms.tex`, Ch1 `ch1_introduction`, Ch2 `ch2_background`, Ch3
  `ch3_state_of_the_art`, Ch4 `ch3_architecture`, Ch5 `ch4_implementation`, Ch6 `ch5_validation`
  (with the three generated tables it `\input`s), Ch7 `ch6_conclusion`.
- Against: SKILL.md; prd.md §2, §3.1, §3.2 + Table 3, Table 12, Table 31; issues 10, 13, 14, 17, 18,
  19 and their Comments (author decisions not re-raised as new: the Ch5 "not built" statements, the
  jury placeholders, the nine Ch2 `\TODO`s, the issue 13 generated-table items P11/P13, the Master-side
  percentile overlap of issue 18 F5).
- Write-once (item 7): `thesis/master/*.tex` as on disk, by grep of every passage naming the
  Ingénieur (25 sites) and of every Ingénieur-owned topic in the Master's Background; full read of
  Master ch2 §2.4 (l.225-290), §2.6 (l.336-347) and the metric-ownership paragraph of ch3_method
  (l.526-548).
- Build: `cd thesis && rm -rf build/ingenieur && latexmk main_ingenieur.tex` (no other latexmk or
  xelatex was running); exit 0; log and PDF text inspected (section 9).
- File abbreviations: `abs`/`fr`/`ar` = the three abstracts; `ch1`..`ch7` = the chapters by their
  printed number (so `ch4` = `ch3_architecture.tex`, `ch5` = `ch4_implementation.tex`, `ch6` =
  `ch5_validation.tex`, `ch7` = `ch6_conclusion.tex`); `gen/` = `thesis/generated/`.

## 1. Verdict

Ready after fixes; no rework. The restructure holds together: the Ch1 structure paragraph matches the
seven printed chapters and two parts exactly, every prose `\ref` lands on the section that does the
thing (including every new `sec:bg-*`, `sec:component-choices` and `sec:research-gaps` target), every
headline number is identical at all of its 5-11 occurrences across the abstracts, Ch6, Ch7 and the
generated tables, the Background's nine definitions are used with one meaning in Ch3-Ch7, JSON, UDP,
LoRA, GGUF and GBNF now expand exactly once in Ch2, the 46 printed references are exactly the 46 cited
keys, and the build is clean (0 errors, 0 warnings, 0 overfull, 91 pages). One MAJOR: Gap G2 claims,
over the conceded MIRA, a stop "held to a latency budget of its own", but the reflex misses that budget
by 395 ms and, measured from the start of the keyword (965 ms median), is slower than MIRA's 466 ms
gate from speech onset; no chapter confronts this, and Ch7 still calls it the budget "the path is held
to". Eleven MINORs (the Open-components duplication deferred from issue 19 among them, with an
anchor-safe fix) and six NITs. Nine `\TODO`s and two jury placeholders remain in the PDF, all known.

## 2. RQ / contribution / gap traceability (check 1)

Printed section numbers; file:line of the anchoring text.

| Thread | Stated (Ch1) | Gap (Ch3 §3.5) | Designed (Ch4) | Built (Ch5) | Measured (Ch6) | Answered (Ch7) |
|---|---|---|---|---|---|---|
| RQ2 pipeline latency | §1.4 quote, ch1:389-393; criteria tab 1.2 rows 1-4, ch1:182-185 | G2 (reflex budget) ch3:439-455; G3 (per-stage latency on the board) ch3:457-473; This-work budgets tab 3.2, ch3:225 | §4.1 dual path ch4:32-178; §4.4 budget ch4:390-472; §4.5 cores ch4:474-526 | §5.1 frame loop, timestamps ch5:59-74; §5.2 per-stage timing, uncached prefill, pinning ch5:150-214 | §6.1 ch6:61-173; tab 6.1 gen/exp2_latency_budget | §7.4 "Pipeline latency" ch7:346-369 |
| RQ3 clause 1 (CRR/WER vs SNR) | ch1:395-397; tab 1.2 rows 7-8 | **empty** -- no gap; nearest: tab 3.5 "Reported" row ch3:510 and ch3:517-518 ("the acoustic-robustness experiment ... has no counterpart there") | §4.4 endpointing threshold and its recognition cost ch4:444-452; §4.6 tiny.en accuracy risk ch4:568-574 | §5.1 endpointer ch5:76-93; §5.2 recogniser ch5:157-162 | §6.3 ch6:244-353; tab 6.2 | ch7:375-381 |
| RQ3 clause 2 (safe degradation) | ch1:397-398, 406-410; §1.3 ch1:248-292 | **empty** (the safe exit is Ch1's design principle, conceded close to SkySim's fallback ch3:415-417) | §4.3 layers, residual classes ch4:286-388 | §5.4 state machine ch5:271-327 | §6.3 "Direction of the errors" ch6:314-327 | ch7:383-387 |
| RQ3 clause 3 (formation) | ch1:398, 411-414; tab 1.2 rows 9-10 | **empty** as a gap; swarm critical comparison ch3:307 ("No prior row pairs the field with a mechanism that bounds what it fails to prevent") | by design none: ch4:20-22 assigns the third mechanism to Ch5 | §5.5 controller and clamp ch5:329-407; §5.6 backends ch5:409-467 | §6.4 ch6:355-406 | ch7:389-395 |
| C4 (contribution) | §1.5 quote ch1:426-431; ch1:436-446 | G1 = second clause ch3:433-437; G2 = first clause ch3:450-452 | §4.1 + §4.2 + §4.4 | §5.1 spotter, constant class map ch5:95-112; §5.2 preemption ch5:188-204; §5.3 sequence numbers, consumer ch5:245-261 | §6.1 reflex latency, preemption and class matrix ch6:91-124; §6.2 ch6:175-242 | §7.4 "System contribution" ch7:397-406 |
| G1 fast-path membership | -- | ch3:426-437 | §4.2 tab 4.1 ch4:180-284 | ch5:108-110 (map checked at load) | ch6:116-124 (no cross-trigger; the golden-set false hover on the fail-safe side); §6.2 false accepts | ch7:398-403 |
| G2 budgeted stop | -- | ch3:439-455 (promises measurement, not a pass) | §4.1, §4.4 tab 4.3 ch4:423-424 | ch5:68-70 (trigger carries the frame's due instant) | ch6:91-111: missed, 545/547 ms vs 150 ms, located | ch7:357-359, 404-406: missed -- consistent with G2; but see MAJOR-1 |
| G3 one-board execution | ch1:45-50 | ch3:457-473 | §4.5 ch4:474-526 | ch5:206-214 | ch6:103-110 (frames under 80 ms; board share 6 -> 18 ms) | ch7:351-352, 367 |

- Every Ch4-Ch7 cell is filled. G2 is reported consistently: Ch3 promises only that Chapter 6
  "measures it against that budget ... and reports whether it is met and where a miss lies"
  (ch3:454-455); Ch6 reports the miss and locates it; Ch7 repeats it in the RQ2 answer (ch7:357-359)
  and in the contribution paragraph (ch7:405-406). No chapter claims the budget is met.
- The empty Gap cells of RQ3 are sanctioned by prd §3.1 (G1-G3 are "each closed by a part of C4 or
  by an architecture decision of Chapter 4", and RQ3 is evaluation, not design), so they are MINOR-6
  rather than a structural defect; the literature motivation for RQ3 is simply never stated.
- prd Table 31 maps the keyword false-accept and false-reject criteria (NFR-15/16) to RQ2. The Ch7 RQ2
  answer (ch7:346-369) does not mention them; they are answered in ch7:262-266 and tab 6.3. Ch1 never
  assigns criteria to RQs, so a reader of the thesis alone sees no gap: noted, not a finding.

## 3. Headline-number occurrence table (check 3)

Every occurrence in the abstracts, the chapters and the generated tables Ch6 inputs (Ch1-Ch5 quote
no measured value, by design: ch1:121-122, ch4:29-30, ch5:40-42).

| Value | Every file:line | Identical? |
|---|---|---|
| Reflex p95 545 ms idle / 547 ms loaded | abs:26; fr:67-68; ar:27-28; ch6:92; ch7:252, 358; gen/exp2:20, 23; gen/requirements_summary:18 | yes |
| 540 ms (spotter delay + quantisation) / 6 and 18 ms (board) | ch6:94-95, 98, 108, 421; ch7:253-255, 367-368; gen/exp2:21-22, 24-25 | yes (see MINOR-2 on how the 540 ms is attributed) |
| Onset 1,265 / 1,266 ms vs 850 ms | ch6:111; gen/exp2:26-27 | yes |
| End-to-end p95 3,122 ms vs 2,500 ms; +622 ms; 25% | abs:27-28; fr:69-70; ar:30-31; ch6:137, 145-147; ch7:213, 255-256, 303, 357, 364; gen/exp2:17; gen/requirements_summary:19; Master ch4_results:344-346 | yes; 622 and 25% wherever the shortfall is quantified |
| 3,602 ms with endpointing | ch6:138; ch7:357; gen/exp2:18 | yes |
| STT 1,449 vs 1,200; prefill 751 vs 250; decode 915 vs 1,100; endpointing 480 vs 500; validation < 1 vs 50 | ch6:139-142, 152-153; ch7:256-257, 306, 308, 363-366; gen/exp2:12-16; Master ch4_results:141 (751) | yes |
| Recovery p95 1,195 ms (median 601, max 1,505) vs 300 ms | ch6:128, 132-133; ch7:228, 258, 304, 312, 359; gen/exp2:28; gen/requirements_summary:21 | yes |
| 78 of 78 cancelled; no cross-trigger | abs:25; fr:66; ar:26; ch6:113-119; ch7:404-406; gen/requirements_summary:13 | yes |
| CRR 0.690 [0.625, 0.750] clean; 0.590 [0.520, 0.660] at 10 dB; 0.650 at 15 dB; 0.485 at 5 dB | abs:29; fr:71-72; ar:32-33; ch6:267, 280, 287, 339; ch7:260-261, 376-377; gen/table20:12, 14-16; gen/requirements_summary:24-25; Master ch5_discussion:289 | yes |
| EM 0.935 on reference text; speech-stage cost 0.245 / 0.345 / 0.450 | ch6:269, 282-283; ch7:380-381, 412; gen/table20:12-16 | yes |
| WER 23.3 / 28.8 / 36.0 % | ch6:283-284; ch7:378; gen/table20:12, 15, 16 | yes |
| Safe failure 0.032 (2 of 62); 0.014-0.039; failures 62 -> 103; reference text 13 failures, 0 safe | abs:30; fr:72-73; ar:34-35; ch6:315-318, 324; ch7:231-236, 331, 384; gen/table20:12-16 | yes |
| Collisions 0 in 150; 432 interventions; 144 of 150 trials | abs:30-31; fr:73-74; ar:35-36; ch6:374-383; ch7:179-185, 390-391; gen/requirements_summary:26, 32 | yes (ch7:185 "96% of runs" = 144/150) |
| Formation accuracy 1.000; slowest convergence 4.32 s; medians 4.06 / 3.26 / 2.30 s | ch6:385-387, 396-397; ch7:160-161, 392-393; gen/requirements_summary:27 | yes |
| Keyword FA 2.33/h [0.06, 12.98]; FR hold 0.050 [0.001, 0.249], abort 0.000 [0.000, 0.168] | ch6:163-165, 230-232; ch7:263-265; gen/requirements_summary:22-23 (FR printed as 0.05 [0.00, 0.25] / 0.00 [0.00, 0.17]: issue 13 P11, known) | yes |
| Verdict counts 7 met / 5 missed / 2 not demonstrated / 2 not yet run / 1 planned | ch6:413-416; ch7:250-251; gen/requirements_summary (recounted: 7/5/2/2/1 of 17) | yes |
| 226 segments; 78 trials per condition; 360 thermal trials | ch6:37, 137; ch7:356; gen/exp2; Master ch3_method:480-481 | yes (360 = 200 + 80 + 80) |

## 4. Abstract comparison (check 4)

| Claim / number | EN | FR | AR | Chapters | Agree? |
|---|---|---|---|---|---|
| Stop must beat any interpreted command; no dependence on site infrastructure | abs:8-10 | fr:45-47 | ar:8-9 | ch1:23-36 | yes |
| Designs, builds and measures a speech-to-swarm runtime, models all on the Pi 5 | abs:10-11 | fr:47-49 | ar:9-11 | ch1:45-50; but ch5:43-46 "not built" (K1, known) | yes vs reality; vs Ch5 as deposited see K1 |
| RQ2/RQ3 as questions | abs:11-12 | fr:49-51 | ar:11-13 | ch1:389-399 | yes |
| Two paths, two keyword classes preempting the LM; membership rule from false-accept cost and time saved; no movement command | abs:15-18 | fr:54-58 | ar:16-20 | ch4 §4.2 | yes |
| Parse path endpointed, transcribed, grammar-constrained Qwen2.5-0.5B | abs:18-19 | fr:58-60 | ar:20-21 | ch4:38-42, 55-58 | yes |
| Validator and state machine check every command; "a rejection becomes a hold" | abs:19-20 | fr:60-61 "tout rejet" | ar:21-22 "كل رفض" | tab 4.2: a no-op on the ground, in landing, after abort | no -- MINOR-3 |
| Clamp at the integrator; five simulated drones | abs:20-22 | fr:61-63 | ar:22-23 | ch5 §5.5 | yes |
| 78/78; reflex 545/547 vs 150 ms "in the spotter's delay ... rather than in computation" | abs:25-27 | fr:66-69 | ar:26-29 | ch6:98-100 (delay, quantisation and anchor error not separated) | stronger than Ch6 §6.1 -- MINOR-2 |
| 3,122 vs 2,500 ms; STT and uncached prefill | abs:27-29 | fr:69-71 | ar:30-32 | ch6:136-142 | yes |
| CRR 0.690 / 0.590 vs 0.80 / 0.65; 2 of 62 safe | abs:29-30 | fr:71-73 | ar:32-35 | ch6:267, 280, 315 | yes |
| 0 collisions in 150 trials, backed by the clamp, 432 interventions | abs:30-32 | fr:73-74 | ar:35-36 | ch6:374-383 | yes (locked NFR-12 phrasing kept in all three) |
| Offline run and live demonstration left to the defence | abs:32-33 | fr:74-76 | ar:36-37 | ch6:413-416; ch7 §7.1 | yes |
| Keywords (8) | abs:37-38 | fr:80-82 | ar:40-42 | -- | same eight, same order |

Against the new chapter set: none of the three abstracts names a chapter count, a part, or a
structure, so the restructure left nothing stale in them; nor does any abstract mention the new
Background or the state of the art (appropriate for an abstract). Beyond MINOR-2 and MINOR-3, no
abstract claims more than the chapters show. The Arabic was read sentence by sentence against the
English by a non-native reader: same claims, same 14 numbers (UNVERIFIED as a certification).

## 5. Scorecard

| # | Check | Result |
|---|---|---|
| 1 | Golden thread RQ2/RQ3/C4 -> G1-G3 -> Ch4 -> Ch5 -> Ch6 -> Ch7 | ISSUES (1): MINOR-6 (RQ3 has no Ch3 anchor) |
| 2 | Contributions claimed = demonstrated | ISSUES (1): MAJOR-1 (G2's claimed difference over MIRA) |
| 3 | Headline numbers identical | PASS |
| 4 | Three abstracts agree; claim no more than the chapters | ISSUES (2): MINOR-2, MINOR-3 |
| 5 | Definitions consistent (Background -> Ch3-Ch7) | ISSUES (4): MINOR-4 (preemption verified by cancellation), MINOR-5 (allowances called allocations that "account for" the miss), MINOR-9 (potential field credited with convergence), MINOR-10 (future work returns to a soft mechanism as the clamp's replacement) |
| 6 | Every forward/backward reference lands | PASS (every `\ref` checked; NIT-2 on one ordering claim) |
| 7 | Write-once across documents | ISSUES (2): MINOR-8 (CRR comparator not cited as the Master says it is), MINOR-11 (Master-side speech-pipeline passage); issue 18 F5 carried as K4 |
| 8 | Front/back matter | ISSUES (1): MINOR-7 (GGML undefined in the List of Acronyms); LoF/LoT short titles PASS; bibliography 46 = 46 PASS; title page PASS except the known jury placeholders |
| 9 | Scope from Ch1 alone | PASS (NIT-6: no explicit out-of-scope sentence) |
| 10 | Clean build, no markers | Build PASS; markers: nine `\TODO` + two jury placeholders (known, author's) |

Also: MINOR-1 (the Open-components duplication deferred from issue 19 m14) sits across checks 5 and
7; MINOR-12 is a single-chapter count found while tracing numbers.

## 6. Findings (sorted BLOCKER -> NIT)

No BLOCKER.

| # | Sev | Check | file:line | Quoted text | Problem | Evidence | Proposed fix |
|---|---|---|---|---|---|---|---|
| MAJOR-1 | MAJOR | 2 (and 1) | ch3_state_of_the_art.tex:448-452; ch6_conclusion.tex:397-406 | "No reviewed system, therefore, holds a stop to a latency budget of its own. The first clause of the contribution closes this gap" / "together with the latency budget of its own that the path is held to while the language model decodes" | G2 concedes MIRA's preemption and claims only "the budget". The budget is missed by 395 ms (545 ms vs 150 ms), and measured from the start of the keyword the reflex takes 965 ms at the median, twice MIRA's 466 ms median from speech onset, which Ch3 reports three times (l.222, 244-245, 446-448). So the one property claimed over the conceded system is a target the system does not reach, on a stop that is slower than the conceded one; no chapter juxtaposes the two figures, and Ch7 still says the path "is held to" the budget. A jury will ask what remains of G2's claim; the text does not answer (examiner question 1). Not a contradiction of results -- every chapter reports the miss -- but the claim is stated more strongly than the evidence supports | gen/exp2_latency_budget.tex:26 "Reflex path from keyword onset, idle & 78 & 965 & 1,265"; l.20 545 ms; ch3:222 MIRA "466~ms, median from speech onset"; ch3:447-448 "once speech ... has lasted 450~ms, at a median of 466~ms from speech onset"; ch4:406 keyword "a phrase of about 700~ms" | (a) ch7:399-400: "together with the latency budget of its own against which the path is specified and measured while the language model decodes." (b) After ch7:406 add: "Measured from the onset of the keyword, the reflex takes 965~ms at the median (Table~\ref{tab:latency-budget}), longer than the 466~ms that MIRA's gate reports from speech onset (Section~\ref{sec:soa-dual-path}). What the reflex adds over that gate is therefore not speed but a trigger restricted to two commands by a derived rule, and a budget against which its latency is located; that budget is missed in the spotter's detection, not on the board." (c) ch3:450: "The first clause of the contribution addresses this gap: a reflex path ... with a budget of 150~ms ... ." Keep the labels sec:dual-path and sec:latency-budget in G2 (ingenieur_ch2.py `closers` check reads labels, not the verb). Check whether ingenieur_ch6.py flags 965 or 466 as numbers not in Ch6 prose (965 is only in the generated table) |
| MINOR-1 | MINOR | 5, 7 (deferred from issue 19 m14) | ch3_state_of_the_art.tex:337-343; ch3_architecture.tex:543-544, 555-557, 565-568; ch2_background.tex:77-79 | "openWakeWord supplies a frozen feature front end that turns audio into one speech embedding per 80~ms frame, over which small classifier heads can be trained for arbitrary phrases" | Three sentences are verbatim in Ch3 "Open components" and Ch4 sec:component-choices (openWakeWord, Silero VAD, whisper.cpp), and the Whisper facts appear three times (680,000 h and 39 M in Ch2 l.77-79 and Ch3 l.337-338; 39 M again in Ch4 l.566). The paragraph also sits oddly in the state of the art: it describes the components this system uses, not the reviewed systems its table compares | diff of the quoted lines; ingenieur_ch2.py:97-98 anchors "680{,}000 hours", "39 million", "80~ms frame", "32~ms windows" in Ch3; ingenieur_bg.py:108 anchors "680{,}000 hours" and "39~million parameters upwards" in Ch2; ingenieur_ch3.py anchors no sentence of sec:component-choices (its 80 ms and 32 ms anchors are l.439, 448, 499) | Fix A (no script change): keep Ch3's paragraph and its four anchors; in Ch4 replace the three restatements with a pointer and keep only the justification. l.542-545: "The reflex budget of 150~ms rests on the keyword spotter. openWakeWord~\cite{oww} was chosen for the property Section~\ref{sec:speech-components} describes: classifier heads trained over a frozen embedding front end." l.555-557: "Silero \gls{vad}~\cite{silero} (Section~\ref{sec:speech-components}) runs here on ONNX Runtime directly, ..." l.565-568: "The recogniser is \texttt{tiny.en}, Whisper's smallest English-only model (Section~\ref{sec:speech-components}), run by \texttt{whisper.cpp}~\cite{whispercpp}." Optional A' for the Ch2/Ch3 Whisper repeat: Ch3 l.337 "Whisper, whose training corpus Section~\ref{sec:bg-speech} gives, has as its smallest English-only model \texttt{tiny.en}, with 39 million parameters~\cite{whisper}" -- requires deleting the `("680{,}000 hours", "whisper")` anchor from ingenieur_ch2.py:97. Fix B (move the paragraph to Ch4, as m14 proposed) removes all four Ch3 anchors, needs ingenieur_ch2.py:97-98 edited and ch3:321-323 ("For two of the open components described below") reworded; not recommended |
| MINOR-2 | MINOR | 4, 3 | frontmatter/abstract.tex:26-27 (fr:68-69, ar:29); ch5_validation.tex:420-421 | "misses the 150~ms budget in the spotter's delay after the keyword rather than in computation" / "Reflex latency is missed in the spotter's delay after the keyword offset, not in the board's computation" | Ch6 §6.1 says the 540 ms "contains the spotter's decision delay, the quantisation into 80~ms frames and the anchor's error, which this measurement does not separate" (ch6:98-100), and Ch7 repeats that three-part attribution (ch7:253-254, 368-369). The abstracts and Ch6's own summary name only the spotter's delay | ch6:95-100 (6/78 and 4/78 detections before the recorded offset); gen/exp2:21 row "of which spotter delay and frame quantisation" | abs: "misses the 150~ms budget after the end of the keyword, before the spotter's detection, rather than in computation"; fr: "en raison de l'intervalle qui précède la détection après la fin du mot-clé, et non du calcul"; ar: the same change; ch6:420-421: "Reflex latency is missed after the keyword offset, in the spotter's decision delay, the frame quantisation and the anchor's error, not in the board's computation, ..." |
| MINOR-3 | MINOR | 4 | frontmatter/abstract.tex:19-20; frabstract.tex:60-61; arabstract.tex:21-22 | "A semantic validator and a flight state machine check every command, and a rejection becomes a hold." / "tout rejet se traduit par un maintien" / "ويتحوّل كل رفض إلى تثبيت" | A rejection becomes a hold only in TAKING_OFF and FLYING; on the ground, in LANDING and after ABORTED it is a logged no-op (tab 4.2 caption, ch4:342-345; ch1:280-282). The French and Arabic ("every rejection") are stronger than the English | ch4:362-366; ch5:285-286 | EN: "... check every command, and a rejection never becomes motion: in flight it becomes a hold." FR: "..., et aucun rejet ne produit de mouvement : en vol, il se traduit par un maintien." AR: "ولا يُنتج أيّ رفضٍ حركةً: ففي الطيران يتحوّل إلى تثبيت." |
| MINOR-4 | MINOR | 5 | ch1_introduction.tex:139; ch5_validation.tex:119-120; gen/requirements_summary.tex:13 | "either of which preempts an in-flight parse-path inference through a sequence-number ordering rule" / "The preemption behaviour and the class matrix together satisfy the verification that the reflex-path requirement names" | "Preemption" carries two mechanisms. Ch2 defines it as interruption or withdrawal of running work (ch2:270-275); Ch4 splits it into an ordering rule, "the needed one", and a cancellation, "an optimisation" (ch4:155-171). The requirement names the ordering rule; Ch6 and tab 6.3 verify it by "78/78 decodes cancelled", i.e. by the optimisation, while the ordering rule "never had to discard a late result" (ch6:115-116) and is verified only by Ch5's unit tests (ch5:259-261), which Ch6 does not cite | ch4:156-157 "only one of them is needed for correctness"; ch5:259-261 | After ch6:120 add: "The ordering rule, which no trial needed, is verified by the consumer's unit tests (Section~\ref{sec:command-bus})." In eval/tables.py the Measured cell: "78/78 decodes cancelled; ordering rule unit-tested; 0 cross-triggers" |
| MINOR-5 | MINOR | 5 | ch6_conclusion.tex:361-366 | "three stages meet their budget allocations ... Two stages account for the 622~ms shortfall" | The Background (ch2:253-261) and Ch4 (ch4:407-408, 460-464) state that stage allowances are ceilings for diagnosis, "not shares", and that percentiles do not add. "Allocations" and "account for" read the budget as a decomposition: the two over-runs sum to 249 + 501 = 750 ms, not 622, and the decode is 185 ms under. Ch6 words it correctly ("locate the shortfall in two stages", ch6:138-139) | gen/exp2:13-15; ch2:257-261 | ch7:362-364: "three stages meet their allowances: ... . The shortfall lies in two stages: speech recognition, ..., and prompt prefill, ..." |
| MINOR-6 | MINOR | 1 | ch3_state_of_the_art.tex:395-408 | "The tables leave three gaps, stated below in the order the design of Chapter~\ref{chap:architecture} closes them" | RQ3 (CRR/WER under propeller noise, safe degradation, formation quality) has no anchor in the Research gaps or the Synthesis; the only literature reading of noise robustness is Contreras et al.'s distortion levels (ch3:51-52), which no critical comparison takes up. prd §3.1 restricts G1-G3 to C4 and architecture decisions, so a gap is not owed, but a reader cannot tell from Ch3 why RQ3 is asked | section 2 traceability table, RQ3 rows | One sentence at the end of the Synthesis, e.g.: "Of the systems that take speech, one evaluates its recogniser under distortion~\cite{contreras2020}, and none reports in which direction its errors go as noise rises or measures the formation its commands produce; the second and third research questions of Section~\ref{sec:objectives} measure both, as evaluation rather than as gaps." Verify the silence claim against the four tables before inserting; check ingenieur_ch2.py's "no source introduced in the gaps" rule (contreras2020 is already cited in §3.1, so it is not a new source) |
| MINOR-7 | MINOR | 8 | ch2_background.tex:348-350 (List of Acronyms, PDF p.10) | "GBNF GGML Backus–Naur form" / "GGUF GGML Universal File" | Both long forms use GGML, which the Ingénieur never defines: `ggml` is in shared/acronyms.tex:18 but no Ingénieur file uses it, so the List of Acronyms prints 22 entries with GGML unexplained in two of them. The Master solved the same problem with `\glsadd{ggml}` (master ch1:110) | PDF text of the List of Acronyms; `grep -c ggml thesis/ingenieur/*.tex` = 0 | ch2:348: "... and the \gls{gguf}\glsadd{ggml} formats Q8\_0 and Q4\_K\_M ..." (adds the entry without printing it) |
| MINOR-8 | MINOR | 7 | ch5_validation.tex:259-261; ch1_introduction.tex:171-172 | "An utterance the endpointer splits into several segments counts as recognised only if every command it dispatched is correct." | The Master states that the Ingénieur "cites the comparator and the canonical form defined here rather than re-deriving them" (master ch3_method:547-548), and defines CRR as "the same comparison" as EM (master ch3_method:567 row). The Ingénieur never says what "correct" means for a dispatched command, nor points at the Master's comparator; the canonicaliser appears only in a list of Master-owned requirements (ch1:129, 228). The cross-document promise is not kept, and CRR is undefined in this document | grep "canonical\|comparator" thesis/ingenieur/*.tex: only ch1:129, 228 | ch6:259-261: "... the parser's accuracy on exactly these items, and a dispatched command is correct when it matches the reference under the canonical comparison that the \emph{M\'emoire de Master} defines, the same comparison as its \gls{em}. An utterance ..." |
| MINOR-9 | MINOR | 5 | ch6_conclusion.tex:160-162 | "The convergence times ... and trajectory profiles therefore evaluate the algorithmic logic of the potential field under idealised kinematics" | Convergence is driven by the formation PID term; Ch5 gives the potential field the second rank of authority and says that near the slots "the formation term determines the trajectory" (ch5:364-381); the field only repels pairs closer than 1.5 m. Attributing convergence to the potential field contradicts Ch5's control terms | ch5:364-373 | "... therefore evaluate the controller -- the formation law, the potential field and the flocking terms -- under idealised kinematics rather than the flight envelope of physical aircraft." |
| MINOR-10 | MINOR | 5 | ch6_conclusion.tex:286-291 | "the geometric separation clamp must be replaced with an active collision avoidance mechanism ... incorporating repulsive potential fields~\cite{koren1991} or velocity obstacles" | Ch1 (l.340-348), Ch2 (l.214-218) and Ch5 (l.383-386) argue that a potential field is a soft mechanism that can be outrun, which is why the hard clamp exists and why the system already carries a field beneath it; proposing a potential field as the clamp's replacement reverses that argument, and koren1991 is the paper on its failure modes. Velocity obstacles carry no citation | ch2:216-218 "a soft mechanism ... as opposed to a hard one, which constrains the state directly" | "... must be replaced with a mechanism that constrains motion on physical airframes, acting on the commanded velocity or acceleration with kinematic feasibility constraints, since the potential field already present is a soft mechanism whose failure modes are known~\cite{koren1991}." (drop "velocity obstacles" or add a `\TODO` for a source) |
| MINOR-11 | MINOR | 7 (Master side) | master/ch2_background.tex:339-346 | "The \gls{stt} stage in this work is a model of the Whisper family, an encoder--decoder transformer trained on a large corpus of weakly supervised audio-transcript pairs~\cite{whisper}" | Table 3 gives speech pipelines to the Ingénieur's Background ("Not repeated; the Master names what it needs in one sentence"). The Master spends three sentences on the pipeline stages and the Whisper architecture, restating ch2_background (Ingénieur) l.28-34 and 74-79 in substance. Issue 17 MINOR-4 flagged the same sentence as a design statement in a Background | prd Table 3 row "Foundations: speech pipelines ..."; Ingénieur ch2:75-79 | Master edit, outside this pass's edit scope: "A command reaches the parser as the transcript of a speech-recognition model of the Whisper family~\cite{whisper,whispercpp}; the pipeline around it is the subject of the \emph{M\'emoire d'Ing\'enieur}." Check master_bg.py anchors before editing |
| MINOR-12 | MINOR | 3 (single chapter, found in tracing) | ch5_validation.tex:284-286 | "At 10~dB, recognition errors that change the intent rise from 5 to 19 and those that corrupt a slot from 23 to 30, while the parser's own errors stay at 12 and the failures assigned to splits fall from 22 to 20." | The four causes give 81 of the 82 failures at 10 dB. The 82nd is a perfect transcript misparsed, a cause the clean paragraph says did not occur ("no utterance was transcribed perfectly and then misparsed", l.274) and which occurs once each at 20, 15 and 10 dB | results/exp3_pi_analysis.md:93-98 (10 dB: 12 / 0 / 20 / 1 / 19 / 30 = 82) | Append: "..., and one utterance transcribed perfectly was misparsed." |
| NIT-1 | NIT | 6, 7 | ch2_background.tex:340; ch4_implementation.tex:216 | "\section{Foundations defined in the M\'emoire de Master}" / "\paragraph{Artefacts from the M\'emoire de Master.}" | The Master's name without `\emph` (SKILL §4.1), in a section title printed in the contents (2.7) and a lead-in; issue 17 noted the second | TOC line "2.7 Foundations defined in the Mémoire de Master" | `\emph{M\'emoire de Master}` in both headings |
| NIT-2 | NIT | 6 | ch3_state_of_the_art.tex:406-407 | "stated below in the order the design of Chapter~\ref{chap:architecture} closes them" | G1 is closed by §4.2, G2 by §4.1 and §4.4, G3 by §4.5, so the gaps are not in Ch4's order (G2's first closer precedes G1's) | ch3:434-435, 453-454, 471 | "stated below, each with the part of the design of Chapter~\ref{chap:architecture} that closes it," |
| NIT-3 | NIT | 5 | ch2_background.tex:345 | "and a \gls{slm} is such a model" | Prints "a SLM"; the document writes "an STT", "an SBC" elsewhere | PDF text | "an \gls{slm}" |
| NIT-4 | NIT | 5 | ch1_introduction.tex:183, 201 | "from end-of-speech" | Hyphenated only here; "end of speech" everywhere else, including its definition (ch2:70) | grep | "from the end of speech" |
| NIT-5 | NIT | 7 | ch3_architecture.tex:458-460 | "the \emph{M\'emoire de Master} applies that combined figure as the deployment constraint of its model comparison" | The Master applies the 1,350 ms combined allowance, the 1,100 ms decode allowance and the 20 tok/s floor derived from it (master ch4_results:374-375); "the deployment constraint" suggests the combined figure alone | master ch4_results:125, 140, 374-375 | "applies that combined figure, beside the decode allowance and a throughput floor derived from it, as deployment constraints of its model comparison" |
| NIT-6 | NIT | 9 | ch1_introduction.tex:66-91 | (no sentence) | Scope passes (section 8), but out-of-scope is stated only implicitly (simulated aircraft, no wind, English commands). The Master has one sentence ("Reinforcement learning, vision input and languages other than English are outside the scope", master ch1:86) | master ch1:86 | After ch1:91: "Physical flight, vision input and languages other than English are outside the scope of both documents." |

Style items noticed in Ch7 and left to the author (not scored; issue 14 was a light pass): file paths
and a method name in prose (ch7:156 `swarm/simulate.py`, ch7:244 and 335
`FlightStateMachine.handle\_command`) where Ch5's rule is "the prose names components, not file
paths"; "Each of the five misses has a confirmed cause" (ch7:251) beside "which its 1~s HTTP polling
interval explains only in part" (ch7:258-259) -- "located cause", as ch6:420; "Recognition degrades
substantially" (ch7:376); ch7:205-206 "speaker sensitivity across diverse speakers and accent groups is
evaluated in the \emph{M\'emoire de Master}", where the Master measures only recogniser WER across
accents and states that "nothing in this document establishes that end-to-end accuracy transfers to
other speakers" (master ch3_method:220-221).

## 7. Known and already decided (reported, not scored as new)

- **K1 -- Ch5 "not built" statements (author's decision, STATE 24 Sep).** Commit cba9c1e built live
  capture (`runtime/audio.py`), the entry point (`runtime/main.py`), the state-machine-to-controller
  link (`swarm/link.py`) and the workstation display; the deposited text still says they are absent:
  ch5:43-46, 54-57, 222-225, 320-327, 337-341; ch7:53-58 ("the first run in which live capture feeds
  the pipeline"), 133-145 (Prerequisites); ch1:82-84, 152-155; ch3 tab 3.4 This-work row is unaffected.
  The abstracts' "designs, builds and measures a speech-to-swarm runtime" (abs:10) matches the code but
  not Ch5 as deposited. STATE 25 Sep also records an unrecorded live run of the full script. **Open
  author decision relevant to Ch7's protocol:** STATE 25 Sep confirms that the step-1 and step-7
  utterance of tab 7.1, "take off to five metres", is transcribed "take off to 5 meters" and parsed as
  `altitude`, illegal in LANDED, so success criterion 1 (ch7:116-117) fails with the thesis wording;
  whether to keep the wording or state a substitute is the author's.
- **K2 -- Open components duplication** (issue 19 m14): now MINOR-1, with an anchor-safe fix.
- **K3 -- Generated-table notes** print project paths and a host name (`results/exp2_analysis.md`,
  `results/exp3_pi_analysis.md`, "Host: \texttt{drone-pi}") and the false-reject intervals to two
  decimals: issue 13 P13 and P11, fixes in eval/tables.py, still open.
- **K4 -- Master Background percentiles** (master ch2_background:282-285) restate what the
  Ingénieur's §2.4 owns: issue 18 F5, Master edit not applied by decision.
- **K5 -- nine `\TODO`s in Ch2 and two jury placeholders** (section 9).
- **Examiner questions carried unanswered:** processor affinity rather than a real-time scheduling
  policy (issue 18 Q3: ch2:290-291 names the policies, ch4 §4.5 never says why they were not used);
  how the reviewed studies were selected (issue 19 m15).

## 8. Scope answers (check 9), from Ch1 alone

- System end to end with one example command: yes -- ch1:15-21 and 66-73, "form a circle with radius
  five metres" -> endpointed, transcribed, parsed to `{"intent":"formation","shape":"circle","radius":5.0}`,
  validator, state machine, controller assigns slots; ch1:56-64 the reflex path and hold/abort.
- Real vs simulated: yes -- ch1:75-91 (aircraft simulated, N = 5, 50 Hz, two backends; audio recorded
  and replayed, live capture not part of the reported system; parts evaluated separately; kinematic
  simulator; no spoken command carried to simulated flight, no wind).
- Language and command vocabulary: yes -- ch1:66-69 (English; ten intents listed) and ch1:56-58, 306-308
  (the two keyword phrases).
- Out of scope: partly -- physical flight, wind and live capture are stated as limits; languages other
  than English only by implication (NIT-6).
- Division between the documents: yes -- ch1:50-54, 95-107, 227-243, 275-276, 416-419, 423-456.

## 9. Build report (check 10)

`rm -rf build/ingenieur && latexmk main_ingenieur.tex`: exit 0, 91 pages. `main_ingenieur.log`: 0 lines
matching `^!`; 0 `LaTeX Warning` (so no undefined reference or citation); 0 `Float too large`;
0 `Overfull`; 0 `Underfull`. Remaining package warnings are the known non-findings (Amiri small-caps
shape for the Arabic cover; biblatex "Language 'arabic' not supported"; ExtSizes advisory).

Contents: Chapter 1 (p.11) before Part I (p.23: Chapters 2-3), Part II (p.45: Chapters 4-6), Chapter 7
(p.78) after Part II with no part above it, Bibliography p.87 -- the heading is on printed page 87,
so the issue 17 anchor fix holds here. The `.toc` also records every `\paragraph`, but tocdepth 3 keeps
them off the printed contents (checked in the PDF). LoF (2 entries) and LoT (15 entries) print short
titles only. List of Acronyms (p.10): 22 entries, each expanded exactly once in the text; JSON (ch2:328),
UDP (ch2:328), LoRA (ch2:346, "Low-rank adaptation (LoRA)"), GGUF (ch2:348) and GBNF (ch2:350) expand
once, in Ch2, and nowhere again. CRR never prints the "long (SHORT)" form in running text because its
first `\gls` sits in a tabularx (tab 1.2), whose trial typesetting marks the entry used; the caption
of tab 1.2 ("CRR: command recognition rate", ch1:171) defines it first, so no action. Bibliography:
46 distinct cited keys across the Ingénieur's inputs = 46 `\entry` in the .bbl = [1]-[46] printed.

Visible markers in the PDF (`pdftotext | grep TODO|CHECK|figtodo|Name]`): nine `[TODO: ...]`, all in
Ch2 -- ch2:116 (multirotor dynamics), 133 (PX4 flight stack), 150 (feedback-control text), 193 (CAPT),
209 (Khatib), 238 (real-time text), 295 (sched(7)/sched_setaffinity(2)), 318 (Harel), 325 (Eugster
et al.) -- plus "[President Name]" and "[Examiner Name]" on the title page. No `\CHECK` or `\figtodo`
anywhere; no marker outside Ch2.

## 10. UNVERIFIED

- The Arabic abstract was compared sentence by sentence by a non-native reader; MINOR-3's Arabic
  wording should be checked by the author.
- MINOR-6's proposed Synthesis sentence makes a silence claim ("none reports in which direction its
  errors go as noise rises"); it was checked against the four tables as drawn, not against the papers.
- ch7:192 "bounds commanded velocities at 2.0~m/s for \texttt{move} and \texttt{set\_param}": whether
  a `move` carries a speed slot was not checked against the Master's schema.
- master ch3_method:213-214 says the Ingénieur "states the consequence [of the two unrecorded sessions,
  another room and another day] for its runtime validation as a limitation". ch7:203-206 states a single
  speaker in a single session and the absence of room reverberation and ambient noise, but not
  day-to-day voice variation by name; judged kept in substance, not scored.
- Whether ingenieur_ch6.py and ingenieur_ch2.py pass after MAJOR-1 and MINOR-6 was not run (scripts
  were not run by this review; the fixes above name the anchors they touch).
