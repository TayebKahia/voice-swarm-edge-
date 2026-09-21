# Issue 18 -- Ingénieur Ch2 (Background) -- verifier report

Chapter: `thesis/ingenieur/ch2_background.tex` (344 lines, working tree with uncommitted edits
on top of `b8ee6db`). Checked against:
- the neighbouring chapters: `ch1_introduction.tex` l.195-205 and l.325-350; `ch3_architecture.tex`
  l.398-470 and l.550-558; `ch3_state_of_the_art.tex` l.157-172, 210-232; `ch4_implementation.tex`
  l.66-76, 96-106, 330-380; `ch5_validation.tex` l.70-102; `ch6_conclusion.tex` l.350-360;
- `thesis/master/ch2_background.tex` l.270-292 and l.395-415, prd.md §3.1 and Table 3;
- `swarm/control.py` (`assign_slots`, l.111-126), `thesis/references.bib`, `tools/review/ingenieur_bg.py`
  and `tools/review/lib.py`.

Primary sources opened on 2026-09-26:
- Reynolds 1987, author-hosted copy (cs.toronto.edu/~dt/siggraph97-course/cwr87/);
- PyFlyt, arXiv 2304.01305: the abstract page and the full PDF, read with `pdftotext`;
- the PX4 user guide pages "Controller Diagrams" and "MC Filter Tuning";
- the CAPT record at CMU RI and SAGE (abstract only; full text not opened).

Nothing edited except this file.

Wording check: every recommended wording below was applied to a scratchpad copy of the repository.
There, `ingenieur_bg.py` gives 0 FAIL, 16 WARN, 48 PASS, against a baseline of 0/14/48. The two new
WARNs are the two new `\TODO` markers. `latexmk main_ingenieur.tex` builds with rc=0, and the log
shows no undefined reference or citation. The cross-chapter edits were applied to Ch1, Ch5
(`ch4_implementation.tex`) and Ch6 (`ch5_validation.tex`). They leave the FAIL sets of
`ingenieur_ch1.py`, `ingenieur_ch4.py` and `ingenieur_ch5.py` unchanged. Details are in §4.

## 1. Summary

| ID | Sev reported | Verdict | Sev verified | Evidence | Fix judgement |
|---|---|---|---|---|---|
| R-F1 (slot assignment, l.177-180) | BLOCKER | CONFIRMED | BLOCKER | Counterexample recomputed, including with the project's own `swarm.control.assign_slots`, which returns `[0 1]`. The squared-distance optimum (113 < 127) has paths crossing at (0.5, 0). Ch1 l.338-339 says the opposite ("crossing paths by construction"). The code's own docstring (`control.py` l.119-120) says the optimal assignment "does not eliminate crossings". Ch5 (`ch4_implementation.tex` l.355-357) implies the Background's claim | Reviewer's diagnosis is right, but the proposed sentence runs to about 45 words. Use the split wording in §3.1. Ch1 and Ch5 need consistent edits (§3.1b, §3.1c) |
| R-F2 (direct pipeline and endpointing, l.99-101) | MAJOR | CONFIRMED | MAJOR | l.31-34 already separate per-frame stages from per-utterance stages. The direct classifiers of ch3_state_of_the_art l.164-172 report per-utterance times (21 ms; 7/106 ms), so they classify complete utterances. An utterance-level direct model needs the endpoint just as a cascade does | Reviewer's fix is sound. Small rewording in §3.2 |
| R-F3 ("end of speech", l.69-71) | MAJOR | PARTLY | MINOR in Ch2; MAJOR cross-chapter in Ch6 | The Background's meaning, the endpointer's declaration, is the meaning of record: ch3_architecture l.403-404 and l.430 ($T_0$), ch1 l.200-201, ch4_implementation l.71, ch3_architecture l.554 and ch6_conclusion l.355 ("3,122 ms (3,602 ms with endpointing)") all use it. Only ch5_validation l.85-86 and l.94-95 use it for the acoustic, energy-based end of a keyword | The Ch2 sentence is correct, but "natural" is a judgement and the term is document-specific; fix in §3.3. The real fix is in Ch6 (§3.3b), because a reader holding the Background's definition would misread the anchor of the headline reflex-latency figure |
| R-F4 (WER, l.79-82) | MAJOR | CONFIRMED | MAJOR | The sentence is almost the Master's l.404-406 word for word. Table 3 gives "metrics" foundations to the Master, and Exp-0 (WER) is the Master's. The Ingénieur uses WER in Exp-3 (ch5_validation l.281-286) but, under Table 3, gets one sentence and a cross-reference | Owner: the Master. The reviewer's fix leaves WER stated twice in the Ingénieur (a pointer carrying the "can exceed one" point, plus a new sec:bg-master sentence). Use §3.4: one pointer, one sentence in sec:bg-master, and the unused "can exceed one" point dropped |
| R-F5 (p50/p95, l.227-233) | MAJOR | PARTLY | MAJOR (ownership reversed) | Two texts carry the same material: Ingénieur l.227-232 and Master l.282-285 both explain why latency varies and that p50 is the typical case. But prd §3.1 item 2 lists "percentiles" under the Ingénieur Background's "real-time systems and latency budgets", and Table 3 gives that row to the Ingénieur. The Master's l.282-285 sits under its CPU-inference section, which prd lists without percentiles | The reviewer's fix makes the owner defer to the non-owner, so it is rejected. The Ingénieur keeps a freshly worded exposition and drops the clause "the definition the Mémoire de Master gives" (§3.5). The Master's sentence gains a cross-reference (§3.5b). That is a Master edit, so the author decides |
| C-1 (flight-controller rates and setpoint interfaces uncited, l.124-131) | MAJOR | CONFIRMED | MAJOR | No flight-stack source in the bib. PyFlyt (PDF, read) carries the simulator half ("convenience functions for setting setpoints ... for all UAVs"; "cascaded Proportional Integral Derivative (PID) architecture"; a list of setpoint definitions). The PX4 "Controller Diagrams" page confirms the cascaded rate, attitude, velocity and position loops but gives no Hz. The 400 Hz default of the inner loop comes only from a search summary of the PX4 docs; I did not see it on a page | Cite `pyflyt` and add a `\TODO` that names the PX4 guide (§3.6). The rate claim is plausible and conservative, so keep it under the TODO |
| C-2 (slot-assignment property uncited, l.177-180) | MAJOR | CONFIRMED | MAJOR (merged into R-F1) | No assignment source in the bib (`grep assign\|kuhn\|hungarian\|turpin` finds nothing). The claim is also false (R-F1) | The citation agent's hedge option, "can avoid that", still says crossing is avoided, so it is rejected. The R-F1 wording carries the CAPT `\TODO` |
| C-3 (Reynolds "central force", l.167-171) | MINOR | CONFIRMED | **raise to MAJOR** | Reynolds' text: "the flocks used a central force model ... causing all members of a widely scattered flock to simultaneously converge toward the flock's centroid"; "More simplistic models ... (such as a central force model ...) do not allow splits". Velocity matching to the mean is not part of it, and "simpler to compute" is not stated. So the citation is PARTIAL on a literature attribution, which issue 15 treated as MAJOR (C-2, C-3 there). ch4_implementation l.374 relies on the term ("the central-force form his model avoids") | Citation agent's direction is right. Wording in §3.7 keeps the whole-group velocity term, which Ch5 needs, as the chapter's own statement without the Reynolds attribution |

No other BLOCKER or MAJOR. Of the 24 argument MINORs and 16 citation MINORs, one is raised (C-3). Two
proposed fixes would break something (R-F28, R-F29; §2.8). Several fixes are worth applying (§3.8).

## 2. Per-finding detail

### 2.1 R-F1: slot assignment and crossing paths (CONFIRMED, BLOCKER)

**Arithmetic, recomputed.** Starts a1 = (0,0), a2 = (-1,-1); slots b1 = (10,0), b2 = (2,1).

| Pairing | Squared costs | Squared total | Euclidean total |
|---|---|---|---|
| a1-b1, a2-b2 | 100 + 13 | **113** | 10 + 3.606 = 13.606 |
| a1-b2, a2-b1 | 5 + 122 | 127 | 2.236 + 11.045 = **13.281** |

- `scipy.optimize.linear_sum_assignment`, run through `swarm.control.assign_slots` with z = 0,
  returns `[0 1]`: the pairing a1-b1, a2-b2.
- **The squared optimum crosses.** Segment a1-b1 lies on y = 0, from x = 0 to x = 10. Segment a2-b2
  is (-1+3t, -1+2t), which meets y = 0 at t = 1/2, at (0.5, 0).
- **The Euclidean optimum does not cross.** It is the swap. Solving 2u = -1+11s, u = -1+s gives
  s = -1/9, outside [0,1].
- **Synchronised straight-line motion never brings the pair close.** The separation is
  (1+7t, 1-2t), whose squared norm is 2 + 10t + 53t^2. Its minimum on [0,1] is at t = 0: sqrt 2 = 1.414,
  the starting separation. So the two vehicles pass (0.5, 0) at t = 0.05 and at t = 0.5.
- **The chapter's greedy claim holds.** In one dimension, take starts 0 and 1 and slots 1.4 and -3.
  Greedy, taking the vehicle at 0 first, assigns 0 to 1.4 and 1 to -3, so the two paths pass
  through each other (cost 17.96, against 9.16 for the optimum).

**What minimum-total-squared-distance assignment gives.** I derived this myself; it agrees with the
CAPT result. Take a pair i, j with start difference A = x_i - x_j and goal difference B = g_i - g_j.
- Optimality against the swap gives |x_i-g_i|^2 + |x_j-g_j|^2 <= |x_i-g_j|^2 + |x_j-g_i|^2, which is
  equivalent to A.B >= 0.
- Under synchronised straight-line motion, the separation is (1-t)A + tB. Its squared norm is at
  least (1-t)^2|A|^2 + t^2|B|^2, which is at least min(|A|,|B|)^2 / 2.
- So no pair comes closer than 1/sqrt 2 of the smaller of its start and goal separations. Vehicles
  of radius R stay apart if starts and goals are spaced more than 2 sqrt 2 R.

**What it does not give.**
- It does not stop paths crossing in the plane. Removing crossings is a property of minimum total
  *unsquared* length, by the triangle inequality.
- It says nothing about motion that is not straight and synchronised.

Ch5's controller moves straight and synchronised only in the idealised case: identical linear PID,
from rest, since each error then decays as s(t) e_i(0) with one shared s(t). The potential-field
term, the flocking term, the backends' 3 m/s speed cap and non-zero initial velocities all break
this.

**Attempted disproofs.**
1. *"Cross paths" could mean "meet".* It fails: l.177-178 opposes "how far each vehicle travels"
   to "whether their paths cross", and "cross" is geometric. On either reading, "avoids that" is
   unconditional, and the property needs straight, synchronised, well-spaced motion.
2. *Perhaps no chapter contradicts it.* It fails:
   - ch1 l.338-339: "Five aircraft converging on assigned formation slots have crossing paths by
     construction", which is also false in the other direction: not every assignment crosses.
   - ch4_implementation l.355-357: "A greedy assignment ... routinely produces crossing paths, which
     sends two vehicles through the same volume". By contrast, this implies the optimal assignment
     does not. It also treats crossing paths as if they meant the same volume at the same time.

Contradiction with another chapter plus a claim the evidence refutes: BLOCKER under
docs/agents/thesis-chapter-review.md.

**Cross-chapter finding, for the author; issue 18 is scoped to Ch2.**
- Ch1 l.338-339 and Ch5 l.355-357 must change with Ch2, or the document stays inconsistent.
  Wording is in §3.1b and §3.1c.
- The Ch1 paragraph also carries the near-verbatim Koren passage (R-F9, l.342-346), so edit both
  in one pass.
- Not thesis text, but worth knowing: the `swarm/control.py` docstring says the optimal assignment
  "removes the ones that exist only because of the assignment". That is imprecise too.

### 2.2 R-F2: direct pipelines and the endpointing wait (CONFIRMED, MAJOR)

The chapter's own frame (l.31-34) puts the endpointing wait on per-utterance stages. A direct
pipeline can be either kind:
- A keyword spotter decides on every frame and needs no endpoint.
- An utterance-level spoken-language-understanding classifier maps a complete segment to a
  decision, so it needs the segment's end.

Ch3's direct rows are of the second kind. ch3_state_of_the_art l.164-172 and l.352-353 report a
per-utterance classification time for each system (0.021 s; 7 ms / 106 ms), not a streaming delay.
I did not open Simões or Henry, but the argument does not depend on them: an utterance-level
classifier cannot start before the utterance is complete.

**Attempted disproof.** "Direct" might be defined in the chapter by the keyword-spotter example.
It fails: l.98-99 says "as a keyword spotter does", which presents the spotter as an instance of a
direct pipeline, not as its definition.

Ch4's dual-path rationale rests on this sentence: the reflex path is justified by skipping the
endpointing wait. So this is an overclaim, MAJOR.

### 2.3 R-F3: "end of speech" (PARTLY; MINOR in Ch2, MAJOR cross-chapter)

Which document meaning is of record: the Background's.
- ch3_architecture l.430: "$T_0$ is the time of the last audio sample the endpointer has processed
  at the moment it declares the utterance over".
- The same meaning appears in ch3_architecture l.403-404 (the table caption), ch1 l.200-201
  ("end-of-speech, the moment the endpointer declares the utterance over"), ch4_implementation l.71,
  ch3_architecture l.554 and ch6_conclusion l.355.

The outlier is ch5_validation:
- l.85-86: "The keyword offset is the end of speech as the capture tool recorded it from the
  signal's energy".
- l.94-95: "the capture tool's energy-based end of speech".

The reflex anchor is the keyword offset, defined at ch3_architecture l.435 as "the last frame of
the spoken phrase". A reader who holds the Background's definition would take the 545 ms p95 as
measured from a point about 450 ms after the keyword ended, the silence threshold. That is a
misreading of a headline figure, so the Ch6 part stays MAJOR. It belongs to the Ch6 issue, not to
Ch2.

Two points remain in Ch2:
- "natural" is a judgement.
- The usage is document-specific. In the literature, "end of speech" often means the acoustic end,
  which is exactly Ch6's usage.

The reviewer says the declaration follows the last word "by at least the silence threshold". That
is too strong: the VAD can flag a weak word tail as non-speech early. Use "by about".

### 2.4 R-F4: WER write-once (CONFIRMED, MAJOR)

Side by side:

| Ingénieur l.79-82 | Master l.404-406 |
|---|---|
| "the number of word substitutions, deletions and insertions needed to turn the transcript into the reference, divided by the number of words in the reference" | "the number of word substitutions, deletions and insertions needed to turn the transcript into the reference, summed over a corpus and divided by the total number of reference words" |

The two are identical for 17 words, a near-verbatim sentence across the two documents (prd risk
R-13).

**Ownership.**
- Table 3 "Foundations: ... metrics" goes to the Master, and Exp-0 goes to Master Ch5.
- The Master's Background already defines WER, with the bootstrap interval.
- The Ingénieur owns "speech pipelines". WER sits on the boundary, but the Master has the full
  exposition and the Ingénieur's Exp-3 needs only the definition.

So the Master owns WER, and the Ingénieur gets one sentence. The "can exceed one" point is carried
by nothing in the Ingénieur: its WER values run from 23.3% upwards and stay well below 1
(ch5_validation l.281, ch6 l.377). Drop it.

The alternative, the Ingénieur owning WER, would require shrinking the Master's paragraph, which
issue 15 has already verified. That costs more and contradicts Table 3.

R-F16 ("minimum" missing) is correct and belongs in the new sentence. The Master's l.404 has the
same gap, a MINOR for the Master (author).

### 2.5 R-F5: percentiles write-once (PARTLY: MAJOR stands, ownership reversed)

Side by side:

| Ingénieur l.227-232 | Master l.282-285 |
|---|---|
| "do not take the same time, because scheduling, caches and temperature vary between them. Latency is therefore reported as percentiles of a sample ... The median, p50, describes the typical case" | "Because latency varies between repetitions of the same request with scheduling, cache state and thermal state, it is reported as percentiles of a sample: the median, or p50, describes the typical case" |

The duplication is real. Ownership, however, is not the Master's:
- prd §3.1 lists the Ingénieur Background's topics as "real-time systems and latency budgets
  (percentiles, preemption, budget allocation)".
- Table 3 gives "real-time systems and latency budgets" to the Ingénieur.
- The Master's §3.1 list for its CPU-inference section does not mention percentiles.

The present Ingénieur clause, "the definition the Mémoire de Master gives for the latency of one
inference process", hands the definition to the wrong document. The reviewer's fix would make it
worse.

Resolution:
- The Ingénieur keeps the exposition, freshly worded, and drops the deferral clause.
- The Master's single sentence is already the "one freshly worded sentence" that Table 3 allows. It
  lacks only the cross-reference (§3.5b).
- `master_bg.py` anchors nothing on l.282-285 (grep for `p50`, `repetition`, `scheduling`: no
  anchor), so that edit is safe.

### 2.6 C-1: flight-controller paragraph uncited (CONFIRMED, MAJOR)

**PyFlyt PDF**, read:
- "RL agent actions to setpoints in the flight controller";
- "convenience functions for setting setpoints, arming status, and flight modes for all UAVs";
- "cascaded Proportional Integral Derivative (PID) architecture";
- a list running from "Angular velocity control" to "Position control and yaw angle".

So `pyflyt` carries "so do simulators that model the flight controller". It also supports nested
setpoint levels, but only for a simulator.

**PX4 "Controller Diagrams"**: "a standard cascaded control architecture", with position (P),
velocity (PID), attitude and angular-rate loops. The page gives no rates. "MC Filter Tuning" names
the gyro publication rate that caps the inner loop, but the page does not give the default.

"Several hundred cycles per second" is plausible and conservative (hundreds of Hz to kHz). It is
still uncited, and the l.114 `\TODO` sits in the previous paragraph and does not cover it.

### 2.7 C-3, raised to MAJOR

Verified against the author-hosted text. The chapter's definition folds velocity matching into
"central force" and attributes "simpler to compute" to Reynolds; neither is in the source. The
clause "the form Reynolds' local model avoids" is supported ("Before the current implementation of
localized flock centering behavior was implemented, the flocks used a central force model").

The citation sits on a mixed sentence and supports only part of it. That is PARTIAL on a literature
attribution, and ch4_implementation l.372-374 uses the Background's definition to label its own
term. Raised to MAJOR, as issue 15 did for its PARTIALs.

### 2.8 MINORs: wrong, unsafe, or worth raising

- **R-F28 (opening promise).** The problem is right: Ch5 also makes and justifies decisions, such as
  the 1.0 s refractory interval, the PID gains and the clamp distance. But the proposed wording adds
  `\ref{chap:implementation}` to the Background, which the script's `foundations` pattern exists to
  forbid ("a reference to a results or build chapter"). That check is currently vacuous: `prose()`
  strips every `\ref{...}` before the regex runs, so it would not FAIL. The intent is clear all the
  same. Use "from Chapter~\ref{chap:architecture} onwards", which keeps the intro's required
  `\ref{chap:architecture}`.
- **R-F29 (Whisper figures).** Dropping "680{,}000 hours" and "39~million parameters upwards"
  **FAILs** two `paper-number` anchors (`r.expect("paper-number", bool(where), ...)`). Reject the
  drop. Use the citation agent's C-5 wording, which keeps both anchors and fixes the scope.
- **R-F20 (preemption).** The reviewer overstates the problem. The Background's definition,
  "interruption of running work in favour of more urgent work", is broad enough to cover
  cancellation, and it never says the work resumes. The clarification is still worth applying,
  because the document's headline "preemption" (preemption recovery, 1,195 ms) is cooperative
  cancellation. Stays MINOR.
- **R-F22 (affinity).** The overstatement does not propagate. Ch4 claims only that parse-path work is
  never *scheduled* on core 0 (ch3_architecture l.27, l.487, l.517), which affinity does deliver.
  Stays MINOR.
- **R-F9 (Ch1 repeats the Background).** Confirmed: ch1 l.339-346 against bg l.195-201. It is
  intra-document repetition, so MINOR. It is cross-chapter work to be done with §3.1b.
- **R-F19** has the same overstatement in ch3_architecture l.505-507 (author, cross-chapter).
- **C-6** (cite `oww` for per-hour false accepts). Acceptable: `prose()` strips `\cite`, so no
  foundations check fires, and a citation is not a naming. A peer-reviewed keyword-spotting source
  would be better.
- **Script defects, not chapter findings.**
  - The `\ref` foundations pattern is vacuous (see R-F28).
  - The memory-bound pattern `memory bandwidth\b.*decod` misses l.261, where "decod" precedes
    "memory bandwidth" and the pattern does not span lines (R-F32 noted this).

All other MINORs and NITs were checked and are correct as reported. The textbook points were
re-derived:
- critical damping from rest;
- symplectic Euler bounded for omega*h < 2, while explicit Euler grows at every step;
- the energy argument of R-F15;
- max(X+Y) <= max X + max Y in R-F6.

## 3. Recommended wording

All wordings are ASCII LaTeX, use `\gls{}` for acronyms and British spelling, and keep sentences at
40 words or fewer. They were tested together in a scratch copy (§4).

### 3.1 R-F1 + C-2 (Ch2 l.177-180, from "The assignment decides" to "linear assignment problem.")

```latex
The assignment decides how far each vehicle travels and whether two of them can meet on the way.
Assigning each vehicle to its nearest free slot in turn can send two vehicles through the same
place at the same time. Minimising the total squared distance over all vehicles at once, an
instance of the linear assignment problem, prevents such a meeting under two conditions. The
vehicles move in straight lines and arrive together, and their starting positions, like their
slots, are spaced widely enough for their size. Two paths may then still cross, but the vehicles
reach the crossing at different times. \TODO{Turpin, Michael and Kumar, ``CAPT: Concurrent
assignment and planning of trajectories for multiple robots'', International Journal of Robotics
Research 33(1), 2014 --- not in references.bib; add and verify, then cite here}
```

Optional, for precision; the derivation is in §2.1. Insert it before "Two paths may then still
cross": "No two vehicles then come closer than $1/\sqrt{2}$ of the smaller of their separations at
the start and at the slots."

**3.1b Ch1 l.338-339** (cross-chapter; the author decides). Replace "Five aircraft converging on
assigned formation slots have crossing paths by construction." with:

```latex
Five aircraft converging on assigned formation slots can come close to one another on the way.
```

**3.1c Ch5, `ch4_implementation.tex` l.355-357** (cross-chapter). Keep "Vehicles are assigned to
slots by minimising the total squared distance between each vehicle and its slot.": it is an
`ingenieur_ch4.py` fact anchor. Replace the next sentence with:

```latex
A greedy assignment, each vehicle to its nearest free slot, can send two vehicles through the same
place at the same time. The optimal assignment rules this out only for straight, synchronised motion
between well-spaced positions (Section~\ref{sec:bg-swarm}), which the potential-field and flocking
terms and the backends' speed limit disturb, so separation still rests on the potential field and
the clamp.
```

### 3.2 R-F2 (Ch2 l.99-101)

```latex
The direct pipeline is limited to the decisions it was trained on, and it avoids the cost of
transcription. A direct pipeline that decides on every frame, as a keyword spotter does, also
avoids the endpointing wait; one that classifies a complete utterance must wait for its end, as a
cascade does.
```

### 3.3 R-F3 (Ch2 l.69-71, from "The instant at which" to "the complete utterance.")

```latex
In this document, the \emph{end of speech} is the instant at which the endpointer declares the
utterance over. It follows the last spoken word by about the silence threshold, and it is the
earliest instant at which a stage that needs the complete utterance can begin.
```

**3.3b Ch6, `ch5_validation.tex`** (cross-chapter, MAJOR there).
- l.85-86: "The keyword offset is the end of the spoken keyword as the capture tool detected it from
  the signal's energy, not a forced alignment."
- l.94-95: replace "the capture tool's energy-based end of speech," with "the capture tool's
  energy-based estimate of where the keyword ends,".
- Keep "before it (6 of 78 idle" and "earliest $-$234.7~ms" as they are; they are `ingenieur_ch5.py`
  anchors, matched whitespace-insensitively.

### 3.4 R-F4 + R-F16 (WER)

Ch2 l.79-82, from "Recognition accuracy is measured" to "length of the reference.":

```latex
Recognition accuracy is scored by the \gls{wer}, a metric the \emph{M\'emoire de Master} defines
(Section~\ref{sec:bg-master}).
```

In sec:bg-master, after "the frame of spoken-language understanding" (C-16's `qin2021` citation
added in the same edit):

```latex
the frame of spoken-language understanding~\cite{qin2021}. A transcript is scored by the \gls{wer},
the minimum number of word edits that turn it into its reference, divided by the number of
reference words.
```

### 3.5 R-F5 (Ch2 l.227-233, from "Repeated runs" to "one in a hundred.")

```latex
Repeated runs of the same operation take different times, because what else the processor is
doing, what its caches hold and how hot it is vary from run to run. Latency is therefore reported
as percentiles of a sample of runs. By the nearest-rank method, the $q$-th percentile of $n$
sorted measurements is the one at rank $\lceil q n / 100 \rceil$. The median, p50, is the typical
run; p95 and p99 describe the tail, since about one run in twenty is slower than p95 and one in a
hundred slower than p99.
```

The next two sentences ("A requirement written on the mean ...", "A requirement on p95 ...") stay;
R-F33 optionally changes "says nothing" to "says little".

**3.5b Master `ch2_background.tex` l.285** (cross-document; the author decides). After "...is the
figure a budget is set against.", add:

```latex
The \emph{M\'emoire d'Ing\'enieur} defines these percentiles and the latency budgets set against them.
```

### 3.6 C-1 (Ch2 l.130-131)

```latex
Open-source flight-control software exposes such setpoint interfaces, and so do simulators that
model the flight controller~\cite{pyflyt}. \TODO{a flight-stack source for the nested loops, their
rates and the setpoint interfaces, e.g.\ the PX4 Autopilot user guide, pages Controller Diagrams
and multicopter filter tuning --- not in references.bib; add and verify, then cite here}
```

"Open-source flight-control software" replaces "Open flight stacks", which also settles R-F31. The
TODO avoids acronyms typed by hand and numbers, which `prose()` would see.

### 3.7 C-3, raised to MAJOR (Ch2 l.167-171, from "Applying the centring" to "avoids~\cite{reynolds1987}.")

```latex
Applied to the whole group rather than to each individual's neighbours, the centring rule
becomes a pull towards the group's centroid, which Reynolds calls a \emph{central-force} model. He
replaced it with his local rule because it draws every member of a scattered flock towards the
centroid at once~\cite{reynolds1987}. Velocity matching applied to the whole group becomes, in the
same way, a pull towards the group's mean velocity.
```

Cross-chapter, optional: in ch4_implementation l.374, change "the central-force form his model
avoids" to "the whole-swarm form his model replaced". No script anchors that phrase.

### 3.8 MINORs worth applying (all tested together with §3.1-3.7)

| ID | Location | Replacement |
|---|---|---|
| R-F28 | l.23-24 | "and the decisions made in this work are stated and justified from Chapter~\ref{chap:architecture} onwards." |
| R-F7 + C-7 | l.43-45 | "One utterance can hold the score above the threshold for several consecutive frames, so a spotter commonly \emph{debounces} its detections: it ignores a frame above the threshold if another crossed it within a short \emph{refractory} interval before~\cite{speechcmd}." |
| C-8 | l.29 | "commonly 16{,}000 per second for speech~\cite{speechcmd,whisper}," |
| R-F10 | l.50-52 | "A false-accept rate quoted without the false-reject rate at the same threshold is therefore uninformative, since a rate as low as desired can be reached by raising the threshold far enough." |
| R-F11 | l.74 | "Many current recognisers are neural sequence-to-sequence models:" |
| C-5 (instead of R-F29) | l.76-77 | "The Whisper models of the original release are transformers of this kind, trained on 680{,}000 hours of weakly supervised audio in sizes from 39~million parameters upwards~\cite{whisper}." |
| R-F25 | l.97-98 | "errors made by the recogniser reach the second stage as text, without the audio that could have resolved them." |
| R-F26 | l.121-122 | "The distinction matters for safety: the harm of a collision grows with the kinetic energy at impact, and that of a fall with the height it starts from." |
| R-F13 | l.142-144 | "When the output saturates, the integral keeps accumulating error the actuator cannot act on, and the controlled value overshoots while that surplus unwinds after the saturation ends. This \emph{integral wind-up} is limited by bounding the integral, among other methods." |
| R-F12 | l.151-152 | "...when $k_d = 2\sqrt{k_p}$: starting from rest, it reaches the setpoint in the shortest time that any $k_d$ allows for that $k_p$ without overshooting." |
| R-F14 + R-F30 | l.153-155 | "In discrete time the integration is done in steps of a fixed duration. The \emph{semi-implicit} step updates the velocity first and moves the position with the new velocity. For an undamped oscillator and a small enough step it keeps the amplitude bounded, whereas updating both from the old values makes the amplitude grow at every step." |
| R-F34 | l.159 | "In this document, a swarm is a group of vehicles commanded as one." |
| R-F17 | l.162 | "Formation control needs a separate mechanism to keep the vehicles apart while they move; flocking contains one among its rules." |
| R-F15 | l.198-200 | "A force also acts only through the dynamics. A closing pair stops short of the separation distance only if the potential there exceeds the pair's relative kinetic energy, and with bounded acceleration and a discrete timestep even contact becomes reachable." |
| R-F18 | l.218-221 | "In a \emph{hard} real-time system a missed deadline is a failure of the system, even if the late result is right. In a \emph{soft} one it degrades the service, and requirements state how rarely a deadline may be missed rather than promising that it never is." |
| R-F6 | l.237-238 | "When the end-to-end target is missed, a stage that exceeded its own allowance is the first place to look. Allowances that bound worst cases can be added, because the worst case of a sum is at most the sum of the worst cases. Percentiles do not add: ..." |
| R-F19 | l.246-247 | "If it overruns, the following frames wait in a queue and their results are late until the backlog drains; if it overruns on average, the queue grows without bound." |
| R-F20 + R-F27c | l.254-256 | "Withdrawn work is discarded rather than resumed, and this document calls its withdrawal preemption as well. The latency of such a cancellation is bounded by the longest interval between checks, plus the time needed to release what the computation held. It helps the urgent work only if that work can run while the work to be withdrawn still holds the processor, for instance on a core of its own." |
| R-F21 | l.266-268 | "Under its default policy it aims at throughput and fairness, and it gives no timing guarantee to any one thread: ... hold the cores. Linux also provides real-time scheduling policies, which give a thread strict priority over ordinary threads." Widen the l.271 TODO to "the sched(7) and sched\_setaffinity(2) manual pages". |
| R-F22 | l.270-271 | "has that core to itself, apart from kernel work and interrupts, which affinity set by a program does not move." |
| R-F23 | l.299-301 | "Producers \emph{publish} messages to the bus without addressing any receiver, and consumers receive them without addressing any sender, so either side can be replaced without changing the other. A message may still name its origin in its content." |
| R-F24 | l.327-328 | "...outside a formal language. Every output is then a string of that language or, if cut off at a token limit, a prefix of one." This splits a 43-word sentence. |
| R-F27a/b | l.33-34, l.65 | "Stages of the first kind determine how soon a system can react; stages of the second kind, which see the whole utterance, determine what it can interpret." / "That duration sets a trade-off." |

Not tested, fine as proposed by their agents: R-F8, R-F31, R-F32, R-F33, and C-9 to C-15 (TODO widening
or cites of keys already in the bib).

## 4. Anchor safety

- **Scratch run.** The repository was copied to the session scratchpad and all of §3.1-3.8 applied.
  - `ingenieur_bg.py` gives **0 FAIL, 16 WARN, 48 PASS**; the MAJOR-only subset gives the same.
    The +2 WARN are the new `\TODO`s (flight stack, CAPT).
  - All `text_claim`/`find` anchors are untouched: Reynolds' rules, "It is a task distinct from
    full speech recognition", "every 10~dB fall ...", "The magnitude of the resulting force ...",
    "\emph{critically damped} when $k_d = 2\sqrt{k_p}$", "680{,}000 hours" and "39~million
    parameters upwards".
  - No forbidden `~ms`, 0.xx, component, project-code or "this system uses" pattern is introduced,
    and none of the Master's terms appears outside sec:bg-master.
- **sec:bg-master sentence count.** It is 9 with the MAJOR fixes and **10** with R-F24's split: the
  PASS limit (the check WARNs above 10). Any further sentence there WARNs, so fold additions into
  existing sentences.
- **Build.** `latexmk main_ingenieur.tex` in the scratch copy: rc=0, no undefined reference or
  citation. New cites use only keys already in `references.bib` (`pyflyt`, `speechcmd`, `whisper`,
  `qin2021`, `reynolds1987`); CAPT and PX4 are visible `\TODO`s.
- **Unsafe proposals.**
  - R-F29: dropping the Whisper numbers FAILs two `paper-number` anchors.
  - R-F28 as proposed: adds a `\ref{chap:implementation}`, against the script's intent; the check
    itself is vacuous.
- **Cross-chapter edits (§3.1b, §3.1c, §3.3b, §3.7 note).** Applied in the scratch copy, they leave
  the FAIL sets of `ingenieur_ch1.py` (0), `ingenieur_ch5.py` (0) and `ingenieur_ch4.py` unchanged.
  The scratch copy shows 5 environment-only FAILs for ch4 (git and untracked-file checks), identical
  before and after. Anchors preserved:
  - `ingenieur_ch4.py` fact "minimising the total squared distance";
  - `ingenieur_ch5.py` "before it (6 of 78 idle", "earliest\n$-$234.7~ms" and "keyword offset is
    545~ms idle".
- **TODO text is in `prose()`.** `prose()` does not strip `\TODO{}`, so TODO text is subject to the
  foundations and acronym checks. Keep acronyms typed by hand, `~ms` figures and chosen-component
  names out of new TODOs.

## 5. UNVERIFIED

- **CAPT's exact separation condition and theorem statement.** Only the abstract and the metadata
  (IJRR 33(1):98-112, Jan 2014) were seen. The 2 sqrt 2 R property is my own derivation (§2.1),
  and a secondary search summary agrees.
- **PX4's default inner-loop rate (400 Hz).** Seen in a search summary of the PX4 docs, not on the
  fetched page.
- **Simões and Henry.** That their direct classifiers take segmented utterances is inferred from
  the per-utterance timings in Ch3. The papers were not opened; R-F2 does not depend on it.
