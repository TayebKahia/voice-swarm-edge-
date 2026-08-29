# Verifier report: Ingénieur Ch1 (thesis/ingenieur/ch1_introduction.tex), findings A1-A7, P1-P5

Review only. No repo file was edited. Primary sources I opened: the chapter in full; ch3_architecture.tex
l.1-309; swarm/fsm.py; runtime/pipeline.py, branch_a.py, bus.py, parser.py; schema/validate.py
(fallback lines); docs/adr/0002, 0006; prd.md §3, §4.2-4.7, §5, Tables 9-12, 15, 31;
results/exp2_analysis.md; issue 00; the rubric; SKILL.md §2. I also downloaded and grepped the
Avizienis et al. 2004 full text (author-hosted copy, diag.uniroma1.it) and the STPA Handbook (the
bib URL). I ran fsm.py directly to check how rejections resolve.

## Summary table

| ID | Sev (reviewer) | Verdict | Sev (verified) | Evidence | Fix judgement / corrected fix |
|---|---|---|---|---|---|
| A1 | BLOCKER | CONFIRMED | BLOCKER | runtime/pipeline.py:172-177 (Branch A `bus.publish("A", ...)`) -> pipeline.py:64-79 `Dispatcher.apply` -> `self.fsm.handle_command` for **both** branches -> swarm/fsm.py:165 `cmd = validate(cmd_input)` (layer 2), then fsm.py:176-243 (layer 3). Layer 1 is the only one skipped: Branch A commands are constants built as schema objects (branch_a.py:68-73) and are never decoded. ch3:157-160 says the opposite of ch1:224-225. Ch1 l.189-193 and l.209 name the three layers explicitly, so the "validation = interpretation" reading is not available. | Diagnosis right. Fix needs three corrections: (1) "legal" must be qualified. Hover is legal only in TAKING_OFF and FLYING (fsm.py:60), as ch3:162-163 says. (2) Use "the reflex path", not "Branch~A" (issue 00). (3) Also fix l.225-226 "removing exactly the machinery the previous paragraphs justified" (the machinery is the three layers, which it does *not* remove) and l.332 "A fast path that bypasses validation". Corrected text below. |
| A2 | MAJOR | CONFIRMED | MAJOR | The ratio sentence is a non sequitur: both budgets are upper bounds. The anchoring argument partly rescues it, but the chapter never names the actual obstacle, which is the endpointer's silence wait (prd Table 6: 500 ms allowance; 450 ms of silence + one 32 ms window per ch3:287-288 comment). "no amount of tuning" is an unearned absolute (D4a). ch3:37-40 repeats the claim. | The reviewer's replacement contains a false statement: "each of its stages alone exceeds it". The validate/FSM/dispatch stage is budgeted at 50 ms (Table 6), under 150. Corrected text below. It keeps the anchor argument and states the endpointing wait as the reason. Ch3:37-40 needs the same change. |
| A3 | MAJOR | CONFIRMED | BLOCKER (rubric: "claim the evidence refutes"; contradicts ch3:222-223 prose) | fsm.py:212-243: a rejection becomes HOVER only where hover is legal. It is `None` (logged `noop_hover_illegal`) in LANDED, LANDING, ABORTED. ADR-0002 Decision 1-2. `unknown` is never dispatched (fsm.py:168-174). A parse-path transport fault publishes nothing (pipeline.py:190-197, parser.py:76-79). A layer-2 fallback HOVER that reaches the FSM in LANDED is also turned into a no-op (verified: `handle_command({'intent':'hover'})` in LANDED returns `None`). Layer 1 has no rejection exit. | The reviewer's fix is still slightly wrong. It says validator rejections always "resolve to a hold", but when the vehicles are on the ground they end as no-ops too. It also reuses the avizienis sentence that P2 shows is misattributed. Use the merged A3+P2 text below. |
| A4 | MAJOR | CONFIRMED | MAJOR | results/exp2_analysis.md:21 (idle p95 545 ms), :26 (loaded p95 547 ms), both MISSES against 150. l.218 "is bounded at" states a property. Only the next clause ("is required to hold") uses requirement language. | Fix correct and minimal. Also recommended: C4 at l.324-325 says "provides a bounded safety reflex", which is the same overclaim. Use "a safety reflex with its own latency budget". |
| A5 | MAJOR | CONFIRMED | MAJOR | The system's own stop commands cross a Wi-Fi hop (ch3:80, 103; runtime/bus.py:15, 92; prd §4.7). So l.33-34, read literally, condemns the system's own reflex channel. "Offline" is never defined. l.22 says "no operator-controlled access point", and FR-9 says "networking disabled on camera". | Adding a scope definition is right. Two problems with the reviewer's version: (1) it calls the hop "a local link", but it is Wi-Fi (ch3:103); (2) it rewrites the NFR-14 target cell. Tools/review compare that cell to prd Table 12, so the change would have to go into prd first. Keep the row as it is and define the term in prose. Corrected text below. |
| A6 | MAJOR | PARTLY | MINOR | prd Table 31 maps RQ3 to NFR-7, 8, 11, 12, 13, with no NFR-9. NFR-9 sits under RQ1. Table 12 NFR-9 is "≥ 0.70, Exp-1, Exp-3". The gap is real: l.305-308 never points to the metric. But "traces to no requirement in this document" overstates it, because l.161-165 names the safe-failure rate, defines it, and says it is measured here. | The minimal fix (one clause at l.307-308 pointing back to l.161-165) is correct. Do **not** take the "better still" option of adding NFR-9 to Table 1.2. It breaks the chapter's own subset rule (l.60-62: tabulated rows are those RQ2/RQ3 resolve to), which follows Table 31. It would need a prd Table 31 change first. It would also put a ≥ 0.70 target in the table that ADR-0006 has since re-baselined to 0.053, which Ch6 has to explain. |
| A7 | MAJOR | CONFIRMED | MAJOR | ch3:17-19 "This chapter turns the first two into a design; the third ... is realised in Chapter~\ref{chap:implementation}". prd §3.1 lists no clamp for Ch3, and Ch4 owns the swarm controller. Ch1 l.274-275 says Ch3 builds all three. | The fix goes in Ch1, as option (b). Option (a) would add clamp design to Ch3 against the frozen outline (D1). Option (b)'s wording is correct as given. |
| P1 | MAJOR | CONFIRMED-DOWNGRADE | MINOR | l.46-48: PyFlyt is not named, so the cite attaches to N = 5 / 50 Hz / two backends. The same key is correctly placed at l.80 (FR-8). Standard practice is to cite a tool at the point where it is named. A cite at the end of a sentence that never names the tool reads as a source for the sentence's claims. | Naming fix is right, with two corrections: use "a kinematic simulator" (FR-8's term, l.80), not "kinematic model", and drop the "(Section~\ref{sec:engineering-requirements})" pointer, which adds nothing. Text: "...two interchangeable backends, the PyFlyt simulator~\cite{pyflyt} and a kinematic simulator." |
| P2 | MAJOR | CONFIRMED | MAJOR | Avizienis et al. 2004, §3.3.1 "Service Failures" (journal p.19): "A system whose failures are, to an acceptable extent, all minor ones is a fail-safe system." Fail-safe is defined by the *severity* of failures, inside the wider class of *fail-controlled* systems ("fail only in specific modes of failure ... stuck output as opposed to delivering erratic values, silence as opposed to babbling"). The paper does not define fail-safe as a mechanism that maps faults to one safe state. | The reviewer's fix reproduces the definition correctly, but it keeps "resolving every detected fault to a hold" and "reachable from all three layers", which A3 refutes. The fail-controlled class (stuck service / silence, i.e. fail-passive / fail-silent) fits a hold / no-op exit *better* than fail-safe does. Merged text below. |
| P3 | MAJOR | CONFIRMED | MAJOR | STPA Handbook ch.1 p.3: "a relatively new hazard analysis technique", "advantages ... over traditional hazard/risk analysis". p.5-6: traditional analysis "calculate[s] the probability of failure". p.133: "Risk has traditionally been defined as the severity and likelihood ...", and STAMP's definition "does not require the determination of likelihood". STPA itself presents designing against consequence rather than rate as its **departure**. Avizienis §3.3.1 ties severity levels to "maximum acceptable probabilities of occurrence", so it grades by consequence but does not drop the rate. | Fix correct. Its "from minor to catastrophic" is acceptable (the paper gives these as the two extremes; it says the number of levels depends on the application). After the fix, "that principle" at l.182 still has an antecedent. |
| P4 | MAJOR | CONFIRMED | MAJOR | grep: Branch~A 8x, Branch~B 5x in ch1. There is no definition in ch1 or in anything the document inputs before it (main_ingenieur.tex:30-59; the abstracts are \TODO; shared/acronyms.tex has no entry). l.215-221 describes the spotter but never attaches the name to it. The code carries FR-6's prohibition and C4's rule, so the requirement rows can't be read without it. | Fix correct, and issue 00 requires it. Two corrections: the l.235 replacement must read "skip interpretation" (A1), not "skip validation"; and the l.224 replacement must be merged with A1's rewrite. Add the voice-activity detector to the parse-path definition. The rename will turn tools/review/lib.py:754 NFR "source" checks into WARNs (warn=True). That is a tooling note, not a thesis error. |
| P5 | MAJOR | CONFIRMED-DOWNGRADE | MINOR | Exp-2 7x, Exp-3 2x, Exp-4 3x, all only in the Verification/Source columns. The three experiments are described (unnamed) at l.364-367. | Fix correct and consistent with issue 00 names. Keeping the `l` column with short labels is sensible. The caption line that maps labels to experiments is needed. |

## Reasoning per finding

**A1.** I traced the full path. `PipelineRuntime.on_wake_frame` publishes the spotter's command on
the bus (pipeline.py:172-177). The consumer's `Dispatcher.apply` sends every message, Branch A or B,
to `FlightStateMachine.handle_command` (pipeline.py:79). That function starts with
`validate(cmd_input)` (fsm.py:165) and then checks Table 9 legality. So a Branch A command passes
layers 2 and 3. It skips only the grammar, because it is never decoded. Ch1 l.189-193 defines "the
three validation layers" as grammar, validator and state machine, and l.209 uses the same phrase
for the parse path. The claim at l.224-225 is therefore simply false and contradicts ch3:157-160.
The reviewer's reframing holds: a false accept is well-formed and in range, so no check can tell it
from a spoken command. One qualification: it is *legal* only while taking off or flying. In other
states the FSM turns it into a no-op, which still does not tell the two apart, so the argument
survives with the qualifier. The same wrong premise also appears at l.225-226 ("removing exactly
the machinery the previous paragraphs justified") and l.332 ("A fast path that bypasses
validation"), neither of which the reviewer listed.

Corrected text (l.224-235), with the issue-00 naming:
> A phrase admitted to the reflex path reaches the swarm without transcription or parsing, the two
> stages that establish what the operator said. The validator and the state machine still check the
> command it publishes, but a spurious trigger publishes a command that is well-formed, within the
> physical envelope and, while the swarm is in flight, legal, so that no check in the architecture
> can distinguish it from one the operator spoke; speed is bought by removing the only stages that
> could have noticed the error. A path whose false accepts no check can detect may therefore carry
> only commands whose incorrect execution is harmless, [...] would on a false accept produce
> uncommanded motion that every check in the architecture would pass, [...] without invalidating
> the reason the reflex path is permitted to skip interpretation.

At l.332: "A fast path that skips interpretation is a familiar pattern" (coordinate with the
citation report's row 7 on the same sentence).

**A2.** The reviewer is right that "a separation of more than sixteenfold, and no single path can
satisfy both" does not follow: any path that meets 150 ms also meets 2,500 ms. The anchor argument
at l.129-133 is closer to the truth but leaves out the reason. A path that has to know the utterance
is complete cannot start transcribing until the endpointer has seen enough silence, and that wait
alone is 450-500 ms. The reviewer's "streaming recogniser" point is fair against "no amount of
tuning". The reviewer's replacement is wrong on one fact: the last stage of the parse path
(validate, FSM, dispatch) is budgeted at 50 ms, so it is not true that "each of its stages alone
exceeds" 150 ms. Corrected l.127-133:
> The reflex budget and the parse budget are not one budget with two tolerances, and they are not
> anchored at the same instant: NFR-1 is measured from the keyword offset, NFR-2 from end-of-speech.
> A path that transcribes and parses a complete utterance cannot begin until the endpointer has
> confirmed that the operator has stopped speaking, a wait that alone exceeds 150~ms, and
> transcription and decoding then each take of the order of a second on this device
> (Chapter~\ref{chap:architecture}). A command that must act within 150~ms of its keyword offset
> therefore cannot travel on the parse path, however that path is tuned; it needs a path that
> neither transcribes nor parses.

Then keep l.133-137. Ch3:37-40 ("so no single path can meet both") needs the same repair in its
own review.

**A3.** Confirmed from the code, the ADR and my own run of fsm.py. A state-machine rejection is
HOVER only in TAKING_OFF and FLYING. In LANDED, LANDING and ABORTED it is a logged no-op
(ADR-0002; fsm.py:226-243). Because the FSM re-checks the HOVER that layer 2 falls back to, a
validator rejection on the ground also ends as a no-op. `unknown` is logged and never dispatched,
and an aborted or failed decode publishes nothing. So "the same state in each [layer]" is false,
and the grammar has no rejection exit at all. The conclusion that no rejection produces motion
does survive. Ch3:222-223 already says "where the flight state permits it", so Ch1 contradicts
Ch3's prose as well as the code. That is a BLOCKER under the rubric's own wording. Delete
l.200-201 "The vocabulary of failure has one word in it". It is the wrong premise as a slogan, and
SKILL §2 "Register" cites it by name as a banned flourish. Merged A3 + P2 text for l.195-201:
> What makes them a safety mechanism rather than a filter is the exit they share: a rejection
> never becomes a substituted or best-guess movement. Output the validator cannot accept,
> including output the parser fails to complete, resolves to a hold with a log entry, as does a
> command the state machine rejects while the swarm is taking off or in flight; where the flight
> state does not admit a hold --- on the ground, during a descent and after an abort --- the
> rejection is a logged no-op instead. The dependability taxonomy calls a system that fails only
> in such specified modes fail-controlled, and one whose failures are, to an acceptable extent,
> all minor, fail-safe~\cite{avizienis2004}; the hold and the no-op are how this architecture
> seeks the second property through the first, and what is specific to it is that no rejection
> path anywhere in the stack can produce motion.

(The definition follows the paper's wording closely. Put it in quotation marks with a page
reference if a verbatim quotation is preferred.)

Out of scope, observed in passing: `handle_command({'intent':'takeoff','z':NaN})` in LANDED takes
the FSM to TAKING_OFF and dispatches HOVER. This happens because legality is checked on the raw
intent after layer 2 has already fallen back. The deployed path validates on the Pi before
publishing (pipeline.py:199-200), so the bus carries `hover` and the case cannot be reached there.
It can only be reached if something publishes an unvalidated command. Worth a test, not a thesis
fix.

**A4.** The numbers match (545 / 547 ms p95, MISSES). l.63-64 says the requirements section quotes
only targets, but l.218 sits in the safety-problem section and says "The reflex is bounded", which
states a property. A reader of Ch5 will see a 3.6x miss against a sentence that asserted the bound.
The fix is right. The C4 wording at l.324-325 ("provides a bounded safety reflex") has the same
problem and should change with it.

**A5.** Not an over-reading. By design the stop commands cross a Wi-Fi hop from the Pi to the
workstation (ch3:80, 103-117; bus.py:15). Read literally, "a command channel that can be
partitioned away from the aircraft is not a fail-safe in any useful sense" applies to that hop, and
"offline" is never scoped. The argument can be rescued with the chapter's own criterion at
l.24-25: availability that is "a property of the site and not of the system". Corrected insertion
after l.35 (prose only; leave the NFR-14 row matching Table 12):
> Offline here means independent of any infrastructure the site does not provide. The wireless
> link from the device to the vehicles, which in this work joins the device to the workstation
> running the simulation, belongs to the system: its availability is the system's responsibility
> rather than the site's, and it lies outside this requirement.

Change l.33-34 to match: "a stopping command that depends on infrastructure the site may not
provide is not a fail-safe in any useful sense." Whether FR-9's "networking disabled on camera"
matches what the demonstration actually disables (external networking only, or everything with
the Wi-Fi hop kept) I could not verify from the repo. Ch6 has to state it either way.

**A6.** Table 31 confirms RQ3 has no NFR-9, and NFR-9 is assigned to RQ1, which the Master owns.
So the chapter's decision not to tabulate NFR-9 follows its own rule at l.60-62, and the reviewer's
preferred fix would break that rule. The chapter does not leave the measurement unnamed: l.161-165
defines the safe-failure rate, says it is measured here, and says Ch6 returns to it. The actual
defect is smaller. The RQ3 clause the chapter calls central (l.305-308) does not point to that
metric. The reviewer's first fix handles it; make it point back rather than restate:
"...the \emph{direction} that curve takes as it falls, measured as the safe-failure rate named in
Section~\ref{sec:engineering-requirements}." Downgraded to MINOR. The prd traceability gap (Table
31's RQ3 row omits NFR-9 even though Table 12 sources it from Exp-3) is a prd issue, not a thesis
issue.

**A7.** The contradiction is real, and Ch3 is the side that agrees with the prd §3.1 outline.
Ch1 l.359-362 and l.362-364 already place the swarm controller in Ch4. So Ch1 l.274-275 is the only
sentence out of line, and option (b) fixes it without touching the frozen outline. Under the
rubric's letter ("contradiction with another chapter") this could be a BLOCKER. It is a roadmap
sentence, so MAJOR is a reasonable call.

**P1.** The placement is wrong because the tool is not named, not because citing a tool you use is
improper. Once PyFlyt is named, the cite is standard practice and correct, since the source
supports "a PyFlyt backend exists". Nothing substantive is misattributed and the same key is
correctly placed at l.80, so this is a placement (D5f) issue: MINOR.

**P2.** Primary text found and read (§3.3.1). The taxonomy defines fail-safe by outcome severity
("failures are, to an acceptable extent, all minor"). The mechanism-like classes are fail-controlled
/ fail-passive / fail-silent ("stuck output", "silence"). Ch1's sentence attributes to the taxonomy
a mechanism it does not define. The paper does call aerospace "fail-safe (FS) requirements"
classical (§5), which helps the "not a local convention" point, but only for fail-safe as a
severity property. MAJOR (partial support) stands. The reviewer's fix has to be merged with A3, as
given above.

**P3.** Confirmed from the Handbook itself. STPA presents itself as new and as an alternative to
traditional probabilistic analysis. It also says the traditional definition of risk includes
likelihood (p.133). So "designing against the consequence rather than against the rate" is
exactly what STPA calls its departure, and citing it for "standing practice ... rather than a
departure" reverses its framing. Avizienis supports severity grading but pairs severity with
acceptable probabilities, so the combined cite does not carry "rather than against the rate" as
standing practice either. The reviewer's fix correctly cites each source only for what it says.

**P4.** Confirmed by grep. There is no definition anywhere before or in ch1. MAJOR is defensible
because the undefined term carries FR-6's prohibition and the C4 rule, so the requirement rows are
unreadable without it. Issue 00 already requires the rename to "the reflex path" / "the parse
path", so the fix is not optional. The reviewer's l.235 replacement ("skip validation") keeps the
A1 error; use "skip interpretation". Ch3's roughly 30 uses and its heading "Branch A membership
rule" (ch3:155) have to be renamed in the same way, or Ch3 will read as introducing a second term.

**P5.** Confirmed. The codes appear only in verification/source cells, and l.364-367 describes the
three experiments, so a reader can reconstruct them. That makes it a mechanical terminology fix
under issue 00: MINOR. The proposed labels and caption line are correct. NFR-14's source "FR-5"
may stay, since FR-5 is defined in Table 1.1.

## Sources consulted outside the repo
- Avizienis, Laprie, Randell, Landwehr (2004), full text: http://www.diag.uniroma1.it/~deluca/pHRI_elective/IEEE_TDSC04_Dependability_Avizienis_etal.pdf (§3.3.1, journal p.19; §5 on FO/FS requirements)
- Leveson & Thomas, STPA Handbook (2018): http://psas.scripts.mit.edu/home/get_file.php?name=STPA_handbook.pdf (ch.1 pp.3-6; p.133)
