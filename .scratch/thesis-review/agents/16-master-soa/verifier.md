# Issue 16 -- Master Ch3 (State of the art) -- verifier report

Chapter: `thesis/master/ch3_state_of_the_art.tex` (341 lines) at `7830694`, read in full with line
numbers. Checked against `ch1_introduction.tex` l.15-35 and l.85-140, `ch3_method.tex` (sec:dataset
l.126-127; sec:quantisation-procedure l.374-402; l.445-452; l.470-476; tab:latency-budget l.618;
tab:requirements l.629-638), `ch4_results.tex` l.1-30, l.67-72, l.121-127, l.238-262, l.378-396,
`thesis/generated/table19_grammar_ablation.tex`, `results/surface_b.csv` and
`results/surface_b_nogrammar.csv` headers, `results/table18_quantisation_delta.md`,
`tools/review/master_ch2.py` l.45-100, `tools/review/lib.py` (`Chapter.find`, `text_claim`,
`_numbers`), `tools/review/selftest.py` l.24-45, issue 02 Comments (#2, #4, #11, #16, #17),
`prd.md` §2, §3.1 item 3, Table 3, `SKILL.md` l.138-152, `docs/agents/thesis-chapter-review.md`.
Primary sources opened with WebFetch (arXiv HTML): sbc2025 (2511.07425), park2024 (2405.21047,
twice: metrics section and reference list), kurtic2025 (2411.02355), slmquant (2511.13023), tam2024
(2408.02442). Nothing edited except this file; no build run.

## 1. Summary

| ID | Sev (reported) | Verdict | Sev (verified) | Evidence | Fix judgement / corrected fix |
|---|---|---|---|---|---|
| BLOCKER-1 = citation #2 (l.329-331; l.147-149) | BLOCKER | CONFIRMED | BLOCKER | kurtic2025 Table 4 scores DeepSeek-R1-Distill Qwen-1.5B (AIME24, MATH-500, GPQA-Diamond); slmquant scores SmolLM2-135M and Qwen2.5-0.5B on MMLU, ARC-c/e, PIQA, HellaSwag. Both sit in Table 3.2 (l.131, l.133) and l.296 says "including at sub-billion scale". l.147-148 has the same false subject ("the evaluations that score task accuracy work at eight billion parameters and above") | Both fixes correct; merged wording in §3. Anchor `eight billion parameters and above` is matched at l.106 (`find` returns every occurrence), so rewording l.148 and l.330 does not break it, provided l.106 is left alone. The reviewer's l.147-149 wording keeps the phrase anyway |
| MAJOR-1 (l.66-77; l.279-285) | MAJOR | CONFIRMED | MAJOR | prd §3.1 item 3 and SKILL l.148-150 quoted in §5(i). l.66-77 is six sentences of design justification (model names, the control's fp16 reason owned by Method l.445-452, the runtime) and states G3 (l.325-337) in advance; l.282-285 states G2 (l.318-323) down to the same clause. l.279-282a is a reading of the table's fourth axis and is not a breach on its own | Fix correct in intent but **breaks the script**: deleting l.69-77 removes the `text_claim` anchor `Three of those models are carried through to quantised artefacts` (master_ch2.py l.72), and `text_claim` turns a missing anchor into a FAIL (lib.py l.359-360). Either keep that sentence or re-point the script (§3). The l.279-285 replacement is fine; keep "On the deployment" as a one-sentence axis reading (§3) |
| MAJOR-3 (l.51; l.135) | MAJOR | CONFIRMED | MAJOR | ch4:9-12 "Accuracy is scored on the workstation"; ch4:71-72 and ch3_method:391-392 timing on the Pi "for the Q4\_K\_M configurations"; ch4:334 (issue 09 verifier) "the benchmark timed only Q4\_K\_M on the board". The row's formats cell "Q8\_0 and Q4\_K\_M" plus "throughput, latency, memory" implies timing at both levels. Partial defence for the accuracy half: Method l.470-471 says outputs were identical on both machines for the golden set, so the document itself treats workstation scoring as deployed accuracy -- but only for the selected configuration (ch4:9-11) | Fix correct. Extend it: the same cell says "\texttt{llama.cpp}; Q8\_0 and Q4\_K\_M against fp16", but the fp16 reference is `transformers` on a Kaggle T4 without a grammar (ch3_method:386-389; table18 caption), not `llama.cpp`. See NEW-1 and §3 |
| MAJOR-4 (l.214) | MAJOR | CONFIRMED | MAJOR | `table19_grammar_ablation.tex` columns: Condition, Decodes, Schema validity, Malformed, EM (pooled). ch4:246-249 discusses EM and validity only. `surface_b_nogrammar.csv` header carries `intent_macro_f1,slot_micro_f1`, so the data exist but are not reported | Fix (a) correct and self-contained; (b) touches `eval/tables.py` and Ch5 prose and is out of this issue's scope. No anchor on l.214 |
| MAJOR-5 (l.282; l.320) | MAJOR | CONFIRMED | MAJOR | ch3_method:127 "No public corpus covering this vocabulary was found". Attempted defence (the schema is the project's own, so no corpus can cover it by construction) fails: G2 needs the claim in its semantic reading (no corpus of these drone-swarm intents), which is what was searched, not proven | Fix correct at both sites. No anchor on l.282/l.320 |
| MAJOR-6 = citation #6 (l.63-64) | MAJOR | CONFIRMED | MAJOR | sbc2025: 25 models from 135 M to 7 B (four at 7 B: Qwen2.5-7B, LLaMA2-7B, LLaMA3.2-7B, Mistral-7B); no 8 B model; "Larger models (>=3B) ... were only practically deployable on the Orange Pi 5 Pro, where they still operated below 5 tokens/s". "interactive speed" is defined nowhere in the document; "no SBC" generalises three boards to all | Both fixes are close but the citation agent's "a size at which the hardware benchmark's boards ran" is wrong in detail: the benchmark never ran 8 B, and only one board ran the >=3 B models. Corrected wording in §3, in words rather than digits so the number trace does not add an UNTRACED warning |
| citation #1 (l.131) | BLOCKER | CONFIRMED | BLOCKER | kurtic2025 §3.2: Llama-3.1 "instruction-tuned versions of all available sizes (8B, 70B, and 405B)"; the 1.5 B model is DeepSeek-R1-Distill "Qwen-1.5B" in Table 4 (reasoning suites: AIME24, MATH-500, GPQA-Diamond). The cell attributes it to the Llama-3.1 family: a wrong cell | Cell fix correct. The **optional l.107-108 rewording breaks the anchor** `has 1.5~billion parameters` (master_ch2.py l.80): keep that phrase and append the qualifier after it (§3). The new cell's digits (405) will show as UNTRACED unless a paper-number anchor is added for the line (§3) |
| citation #3 (l.228-230) | MAJOR | CONFIRMED | MAJOR | park2024 Evaluation: correctness = "how many of the sampled programs are correct solutions"; "ASAp produces correct samples 38% more often than GCD (geomean)"; "ASAp returns the correct solution for 1588 samples, whereas GCD only returns the correct solution 12 times"; on jointly solved SLIA "73% less often". No comparison against unconstrained decoding anywhere. So the distortion's task cost *is* stated -- against an aligned sampler | Fix correct in substance; shortened wording in §3 |
| citation #4 (l.210) | MAJOR | CONFIRMED (PARTLY on the divergence half) | MAJOR | park2024 defines the target Q^{P,G}(w) = 1[w in L(G)] P(w) / sum, the LLM renormalised over L(G), and reports KL(Q~ || P) noting "KL(Q~||P) = KL(Q~||Q^{P,G}) - log C", i.e. the two differ by a constant. So "divergence from the unconstrained distribution" is what is *computed* and is off from the *defined* target only by a constant; the wrong half of the cell is that the "Effect on accuracy measured" column reports divergence only, when solution correctness is also counted | Cell fix correct; a shorter version in §3. Not raised to BLOCKER: the divergence clause is defensible up to the constant the paper itself states; the omission is incompleteness, not a false statement |
| citation #5 (l.48) | MAJOR | CONFIRMED | **BLOCKER** (raised) | sbc2025: "All models were quantized using the q4_k_m quantization scheme". The cell says "formats as distributed", which the source contradicts; the issue's own rule is "a wrong cell is a BLOCKER", and the standard's BLOCKER line includes "citation that does not support its claim". Materially relevant: it is the one format this thesis times on the Pi | Fix "Ollama and Llamafile; Q4\_K\_M throughout" correct. No anchor on l.48 (the `twenty-five quantised language` anchor is l.20) |
| citation #7 (l.222) | MAJOR | CONFIRMED (PARTLY on the literal wording) | MAJOR | park2024 reference list: "[27] B. T. Willard and R. Louf (2023) Efficient guided generation..."; "[7] S. Geng ... Grammar-constrained decoding for structured NLP tasks without finetuning"; "We implemented the ASAp algorithm as an extension of the Transformers-CFG implementation of GCD"; CP problems from "prior GCD work" (Geng). tam2024 cites Willard and Louf (2023). Literal defence ("cite one another's *measurements*") is weak: Park re-runs GCD on Geng's own task set, so "on different models and tasks" (l.223) is false in part | Fix correct: drop the citation-graph claim and the "different ... tasks" clause (§3). No anchor on l.222 |
| NEW-1 (l.51, same cell as MAJOR-3) | -- | NEW | MAJOR (bordering BLOCKER; fixed by the MAJOR-3 edit) | Row reads "Raspberry~Pi~5 ... \texttt{llama.cpp}; Q8\_0 and Q4\_K\_M against fp16". The fp16 reference is base weights plus unmerged adapter under `transformers` on a Kaggle T4, no grammar (ch3_method:386-389; table18 caption). In a table whose columns are Hardware and "Runtime and formats", the row says the fp16 point was obtained in `llama.cpp` on the Pi | Cover it in the MAJOR-3 cell rewrite (§3). Listed separately so the corrected fix is not applied without it |

## 2. Reasoning per finding

### BLOCKER-1 / citation #2 -- CONFIRMED, BLOCKER

Attempted disproof 1: read "score tasks" as "score *downstream* tasks of the kind Ch5 scores"
(a structured task), so that generic suites do not count. Fails: l.328-329 has just called the
same studies' generic-benchmark accuracy "accuracy on general-purpose benchmarks", i.e. task
scoring, and l.296 says the evaluations report "accuracy on general-purpose suites ... including
at sub-billion scale~\cite{kurtic2025,kurt2026,slmquant}". The chapter cannot count slmquant as a
task-scoring evaluation in the Synthesis and not in G3.

Attempted disproof 2: read "those" as the two studies named at l.104-105 (kurtic2025, kurt2026)
only. Fails on kurtic2025 alone: Table 4 scores a 1.5 B model, and the chapter says so at
l.107-108 and l.148.

l.147-149 has the same fault in a softer form; the reviewer's rewrite is right. Anchor: `find` is
whitespace-insensitive and returns every occurrence (lib.py l.92-95), and l.106 "mostly of eight
billion parameters and above" is true and untouched, so the anchor survives either rewrite.

### MAJOR-1 -- CONFIRMED, MAJOR; the proposed l.66-77 fix breaks a script anchor

Attempted disproof: the table's last row is this work (caption l.42, prd-mandated per the issue),
so "walks the table's axes" necessarily touches this work, and a comparison paragraph may say on
which axes the last row differs. This holds for a hand-off sentence and for l.279-282a ("On the
deployment, this work's model has to run offline ...", which is the Hardware/budget axis read for
the last row). It does not hold for l.66-77: "This thesis narrows the scope ... and in exchange
scores what neither study does" (positioning), the four model names with citations (Method
material), "The fourth, a parameter-matched control, is reported at fp16 only, because
\texttt{llama.cpp} segments its prompt differently" (Method l.445-452 owns that), "The accuracy
cost of meeting a throughput budget ... is thus treated as a quantity to be measured, not assumed"
(this is G3, l.325-337, in advance), and the runtime sentence. Nor for l.282-285, which is G2
verbatim in substance ("No existing corpus covers this command vocabulary"; "does not show that it
can be solved at this size and within this budget"). SKILL l.150: "Do not scatter a gap statement
into every subsection." Verdict stands at MAJOR (a prd §3.1 rule breach, not a missing section).

Script: `r.text_claim("coherence", "Three of those models are carried through to quantised
artefacts", False, ..., warn=True)` (master_ch2.py l.72-74). `text_claim` adds a **FAIL** when the
anchor is absent (lib.py l.359-360). The reviewer's fix deletes that sentence. The
`four fine-tuned models` anchor (l.70) and the four `\cite{qwen25|smollm2|llama32|danube3}` checks
(l.71) survive the reviewer's wording. The `positioning` check (l.46-54) is unaffected: it only
compares keys cited in Research gaps against keys cited before it, and `llamacpp` (removed from
l.75) is still cited at l.130, l.168, l.212.

Also: the reviewer says l.152-157 "is acceptable if trimmed". Any trim must keep the exact string
`as part of Contribution~C3.` (l.155), the selftest EXTRA mutation target (selftest.py l.41).

### MAJOR-3 -- CONFIRMED, MAJOR

Attempted disproof: Method l.470-471 states that outputs were identical on the workstation and
the Pi for all 200 golden items, "These metrics are therefore scored on the workstation", so the
document's own position is that workstation-scored accuracy *is* the deployed accuracy, and a
Hardware cell naming the Pi is not false. Half succeeds: it covers the accuracy half for the
selected configuration only (ch4:9-11 says "for the selected configuration"), not for the other
five artefacts. It does not touch the timing half: the row's formats cell says both levels and its
metrics cell says throughput, latency and memory without qualification, while ch4:71-72 and
ch3_method:391-392 time the Q4\_K\_M configurations only. l.135 "throughput on the board" beside
"Q8\_0 and Q4\_K\_M" has the same implication. Issue 02 #2 fixed this pattern at BLOCKER; here the
correct qualifier exists two paragraphs later (l.334-335), so MAJOR (overclaim) is the right level.

While checking the cell I found NEW-1 (the fp16 reference is not a `llama.cpp` run); see §4.

### MAJOR-4 -- CONFIRMED, MAJOR

No disproof: the generated table has no F1 column and Ch5's ablation prose never reports F1
with the grammar off. The CSV header for the no-grammar run carries both F1 columns, so the
reviewer's option (b) is feasible, but it is a Ch5/tooling change. Option (a) is the fix within
this issue.

### MAJOR-5 -- CONFIRMED, MAJOR

Attempted disproof: the ten-intent schema and its slot names are this project's (Ch1 l.83-86;
Method sec:schema), so no pre-existing corpus can cover *this* vocabulary by definition, and the
sentence is trivially true. Fails as a defence of G2: read that way the sentence proves nothing
(any project's own labels are uncovered by definition), and G2 needs the semantic reading (no
corpus of these swarm-command intents exists), which is a claim about the world that Method
l.127 makes only as "was found". The hedged form is what the evidence supports and, as the
reviewer notes, it also answers examiner question 2.

### MAJOR-6 / citation #6 -- CONFIRMED, MAJOR

sbc2025's model table tops out at 7 B (four models) and its statement about large models is
">=3B ... only practically deployable on the Orange Pi 5 Pro, where they still operated below 5
tokens/s"; the two Raspberry Pis did not run them practically at all. So (a) no source in the
chapter says anything about 8 B on an SBC, (b) "interactive speed" is undefined, (c) "no SBC" is
the world. Both proposed fixes fix (a)-(c) but the citation agent's "a size at which the hardware
benchmark's boards ran below five tokens per second" says the benchmark ran 8 B on its boards
(plural); it ran up to 7 B, on one board. Corrected wording in §3.

### citation #1 -- CONFIRMED, BLOCKER

Kurtic §3.2 names the Llama-3.1 sizes (8B, 70B, 405B); Table 4's models are "Llama-8B, Llama-70B,
Qwen-32B, Qwen-14B, Qwen-7B, Qwen-1.5B" (DeepSeek-R1-Distill). The 1.5 B model is a Qwen
distillation. The number at l.108 is right; the family at l.131 is wrong, and a wrong cell is a
BLOCKER under the issue's rule. Two script consequences of the fix: (1) the citation agent's
optional prose rewording at l.107-108 replaces "has 1.5~billion parameters", which is a
paper-number anchor (master_ch2.py l.80) -- a broken anchor is a FAIL under "paper-number"; (2)
the new cell contains 405 (and 8, 70), which the number trace (lib.py l.628-657) will look up in
results/ and report UNTRACED unless l.131 becomes a paper-number line. Both handled in §3.

### citation #3 -- CONFIRMED, MAJOR

Attempted disproof: "how much accuracy that costs" could mean the cost relative to decoding
without a grammar, which Park indeed never measures. Fails: the sentence says "on any task", and
Park measures, on two SyGuS families and constituency parsing, how many GCD samples are correct
against how many aligned-sampler samples are correct (12 vs 1588 on one benchmark; 38% geomean;
the reverse, 73% less often, on jointly solved SLIA). That is the distortion's cost on a task,
stated, only against a different comparator. The fix must say what the comparator is.

### citation #4 -- CONFIRMED (PARTLY), MAJOR

Park defines the target as the grammar-conditioned Q^{P,G} and *computes* KL(Q~ || P) against the
raw LLM P, stating that the two differ by -log C. So "divergence from the unconstrained
distribution" describes the reported number and is off from the paper's own definition only by a
constant the paper names: this half is PARTLY. The half that is wrong outright is the column
answer: "Effect on accuracy measured: Yes, as divergence ..." omits that correctness is counted.
MAJOR stands; not raised, because the cell is incomplete rather than false.

### citation #5 -- CONFIRMED, raised to BLOCKER

The source states one format for all 25 models. "formats as distributed" is a positive claim the
source contradicts, in a table cell; the issue fixes the severity of a wrong cell. The corrected
cell also strengthens the chapter's own comparison (l.61-66), since Q4\_K\_M is the level this
thesis times on the Pi.

### citation #7 -- CONFIRMED (PARTLY on the literal reading), MAJOR

Attempted disproof: the claim is about *measurements*, and Park may cite Geng's paper and
implementation without citing Geng's accuracy numbers. Cannot be settled from the reference list
alone, and it does not rescue the sentence: it is an uncited claim about a citation graph (D5c),
and its second clause "on different models and tasks" is contradicted by Park evaluating GCD on
"6 problems from prior GCD work (Geng et al. 2023)" with Geng's Transformers-CFG implementation.
The safe wording drops both.

## 3. Corrected fixes (ready to apply)

Line numbers are those of `7830694`. Anchor status per edit.

**BLOCKER-1 / #2, l.329-331.** Replace "not \gls{em}, intent and slot F1, or schema validity on
a command-parsing task, and those that score tasks at all work at eight billion parameters and
above." with:

> not \gls{em}, intent and slot F1, or schema validity on a command-parsing task; the two that
> score tasks at scale work at 1.5~billion parameters and above, and the one sub-billion
> evaluation scores generic suites too.

Anchor: none on l.329-331; `eight billion parameters and above` remains matched at l.106. The
digit 1.5 on this line will be traced (the report already traces "1.5" at l.131/148/292 to
table18's 1.5 pp delta -- a false hit, but PASS, not UNTRACED).

**BLOCKER-1, l.147-149.** Replace "On scale, the evaluations that score task accuracy work at
eight billion parameters and above, with one reaching down to 1.5~billion, and the one study of
sub-billion models finds" with the reviewer's wording:

> On scale, two of the three evaluations work at eight billion parameters and above, one reaching
> down to 1.5~billion; the third, the one study of sub-billion models, finds

Anchor: unaffected.

**MAJOR-1, l.66-77.** Replace from "This thesis narrows the scope" (l.66) to "cost in accuracy."
(l.77) with:

> The last row narrows the scope to one task, one device and four fine-tuned models
> (Qwen2.5-0.5B~\cite{qwen25}, SmolLM2-360M~\cite{smollm2}, Llama-3.2-1B~\cite{llama32}, and
> H2O-Danube3-500M~\cite{danube3} as a parameter-matched control at fp16). Three of those models
> are carried through to quantised artefacts and timed against the 20~tok/s throughput floor of
> Chapter~\ref{chap:introduction}; Section~\ref{sec:research-gaps} states what the two studies
> leave open.

Anchors: keeps `four fine-tuned models`, `Three of those models are carried through to quantised
artefacts` (text_claim, l.72-74 of the script) and the four model `\cite`s. The 20 at l.70 was
traced (table16/exp3) and stays. If the author prefers the reviewer's shorter version without the
"Three of those models" sentence, the script line 72-74 must be deleted or re-pointed, or the run
FAILs with "anchor not found -- prose changed". The `\cite{llamacpp}` removed from l.75 is still
cited at l.130, l.168, l.212 (positioning check unaffected).

**MAJOR-1, l.279-285.** Replace from "On the deployment, this work's model" (l.279) to "answer
that question." (l.285) with:

> On the deployment, the last row is the only one with a hardware and latency budget and the only
> one whose output is constrained; Section~\ref{sec:research-gaps} states what that leaves open.

Anchor: none. G2 (l.318-323) already carries the offline / sub-billion / no-person / no-corpus
argument; the MAJOR-5 wording at l.320 stays.

**MAJOR-3 + NEW-1, l.51.** Replace the row with:

> This work & Three fine-tuned candidates of 0.36--1.2~B, and a fine-tuned, parameter-matched
> control at fp16 & Raspberry~Pi~5, three \gls{cpu} cores (timing); workstation, same runtime
> (accuracy) & \texttt{llama.cpp}; Q8\_0 and Q4\_K\_M, against an fp16 reference decoded under
> \texttt{transformers} & \gls{em}, intent and slot F1, schema validity, false-command rate on one
> task; throughput, latency, memory at Q4\_K\_M \\

(The Models cell is the reviewer's MINOR-9 wording, included because the row is rewritten
anyway; drop it if MINOR-9 is declined.) Anchor: none on l.51; the script's WARN at l.69
("three quantised + one fp16 control ... one story") is a text_claim on l.70's sentence, not on
this row, and is unaffected.

**MAJOR-3, l.135.** "... false-command rate, on one task; throughput on the board at Q4\_K\_M".
Anchor: none.

**MAJOR-4, l.214.** "Yes: \gls{em} and schema validity with and without the grammar". Anchor: none.

**MAJOR-5, l.282.** "No public corpus covering this command vocabulary was found
(Section~\ref{sec:dataset})." (If the l.279-285 replacement above is applied, this sentence is
gone and only l.320 needs the change.) **l.320:** "and no public corpus covering this command
vocabulary was found." Anchor: none.

**MAJOR-6 / #6, l.63-64.** Replace "an 8-billion-parameter model that no \gls{sbc} serves at
interactive speed" with:

> an 8-billion-parameter model, larger than any the hardware benchmark ran, whose models of three
> billion parameters and above decoded below five tokens per second on the one board that could
> run them~\cite{sbc2025}

Written in words so the number trace gains no digit; "8-billion" already sits on this line and
was not flagged. Anchor: none on l.63-64.

**citation #1, l.131.** Cell:

> Llama-3.1-Instruct at 8, 70 and 405~B; DeepSeek-R1 distillations from 1.5~B, on reasoning
> suites

and add to `paper_numbers` in master_ch2.py: `("8, 70 and 405~B", "kurtic2025")`, so l.131 is
listed under "Numbers quoted from papers" instead of producing an UNTRACED warning for 405 (the
script's expected value comes from kurtic2025 §3.2, not from the prose). **Do not apply** the
citation agent's optional l.107-108 rewording ("a 1.5-billion-parameter reasoning distillation"):
it removes the anchor `has 1.5~billion parameters`. Anchor-preserving alternative for l.107-108:

> the smallest model either study evaluates has 1.5~billion parameters, a reasoning distillation
> of the Qwen family rather than a Llama-3.1 model~\cite{kurtic2025}.

**citation #3, l.228-230.** Replace "the distortion result establishes that the constrained
distribution differs from the unconstrained one without stating how much accuracy that costs on
any task" with:

> the distortion result establishes that grammar-constrained sampling departs from the model's
> own grammar-conditioned distribution, and counts what that departure costs in correct solutions
> only against an aligned sampler, never against decoding without a grammar

Anchor: none.

**citation #4, l.210.** Cell: "Yes: Kullback--Leibler divergence from the model's
grammar-conditioned distribution, and solution correctness on program-synthesis tasks, against an
aligned sampler only". Anchor: none.

**citation #5, l.48.** Cell: "Ollama and Llamafile; Q4\_K\_M throughout". Anchor: none.

**citation #7, l.222-223.** Replace "the three kinds do not cite one another's measurements, so
the literature establishes correctness and cost separately, on different models and tasks" with:

> the cost studies measure the mask's effect in experiments of their own, so the literature
> establishes correctness and cost separately

Anchor: none. (The reviewer's MINOR-1 "four kinds" edit to the same sentence is compatible.)

**l.152-157 (if trimmed under MAJOR-1):** keep the exact string `as part of Contribution~C3.`
(selftest.py l.41).

## 4. NEW findings

**NEW-1 -- l.51, "Runtime and formats" cell: "\texttt{llama.cpp}; Q8\_0 and Q4\_K\_M against
fp16" beside Hardware "Raspberry~Pi~5, three \gls{cpu} cores".** Method l.386-389 defines the
fp16 reference as base weights plus the unmerged adapter "decoded under \texttt{transformers} on a
Kaggle T4, without a grammar: a reference point, not a deployed configuration"; table18's caption
says the same. In this table the row states that the fp16 point was a `llama.cpp` run on the Pi.
Severity: MAJOR bordering BLOCKER (a contradiction with Method in a table cell about this work,
not about a cited source); it is the same cell as MAJOR-3 and the corrected row in §3 covers it.
Not opened as a separate BLOCKER because the chapter states the reference/deployed distinction
correctly at l.155-157 and Ch5's Table 18 caption is explicit; the cell is the only site.

No other BLOCKER-level error found. Checked and clean: l.22-25 and l.291-293 against sbc2025;
l.106 "mostly"; l.107-108 the 1.5 B number; l.132 Kurt's format range; l.133 Wang's models and
metrics; l.211 Tam's "No" fine-tuning (all five models prompted); l.244-246 and l.264 MASSIVE
figures (citation agent's Table 3a reading, not re-fetched); l.153-155 "three quantised models at
both levels" against table18 (six rows); l.181-183 and l.314-316 against ch4:241-242 (same six
artefacts); l.333-335 against Ch1 C3 l.120-123 (Ch1 says "throughput timed on the Raspberry Pi
5" without "at Q4\_K\_M"; l.335 is more specific, not contradictory); l.266 "safe-failure rates"
against ch4:143-146; l.71-73 control at fp16 for the tokeniser reason against ch3_method:445-452.

## 5. Rulings

**(i) MAJOR-1 -- is positioning inside a critical comparison a breach?** prd §3.1 item 3, last
sentence, verbatim: "Studies are compared to each other in the tables, and to this thesis only in
the gaps." SKILL.md l.145-150, verbatim: "Each section is a taxonomy of the reviewed studies with
**one comparison table** (...) and a **critical-comparison paragraph** that walks the table's
axes and compares the studies *to each other*, as in Bensalah §3.3.4.1 and Boufafa §5.2.4/§6.5.
Close with one **Research gaps** section, numbered G1--G3 and mapped one to one onto C1--C3; the
studies are compared to this thesis only there. Do not scatter a gap statement into every
subsection." The chapter's own l.10-11 repeats the rule.

Ruling: the rule forbids *comparing the studies to this thesis* and *stating a gap* outside
Research gaps. It does not forbid the comparison paragraph from reading the table's last row,
because prd/SKILL require the paragraph to walk the table's axes and the table (caption l.42)
ends in this work. A **one-sentence hand-off** that names on which axes the last row differs and
points to `sec:research-gaps` is therefore acceptable, and l.233-234 is the model. What is not
acceptable is (a) explaining why this work is designed as it is (l.67-73: model list, the
control's fp16 reason, the runtime -- Method material), and (b) stating what the literature leaves
open (l.73-75 = G3; l.282-285 = G2), which is "a gap statement scattered into a subsection".
MAJOR-1 is CONFIRMED for l.66-77 in full and for l.282-285; l.279-282a is an axis reading and may
stay as one sentence. l.152-157 is a hand-off (three sentences, no design rationale, no gap
statement) and passes, subject to the l.155 anchor.

**(ii) The 1{,}100~ms allowance at l.266.** prd Table 3: "Latency budget and resource allocation
| Owned by Ingénieur, Ch. 3 | One table in Master Ch. 5 as the deployment constraint the selection
rule uses." The Master's permitted table is Method's `tab:latency-budget` (l.618), whose caption
names the Ingénieur as owner of the full budget; Ch1 l.27-28 also states the figure. l.266 is one
number in a cell under the column head "Hardware and latency budget", with no exposition of how
the budget is derived or distributed, and the number is traced by the script (PASS,
exp2_latency_budget.md). That is not a write-once breach (D6 asks whether the material is
*explained* here; it is not), so the seeded lead does not produce a MAJOR. What remains is the
reviewer's MINOR-2: the row is the only site in the chapter naming the constraint in
milliseconds, against "throughput floor" at l.70 and l.327 and "throughput budget" at l.73 and
l.280, four names for one constraint. **Confirmed at MINOR** (terminology drift, the standard's
MINOR line). The reviewer's fix ("20~tok/s throughput floor, from a 1{,}100~ms decode allowance
(Table~\ref{tab:latency-budget})") is correct: it keeps the traced figure, adds the derived one
that l.70 already uses, and makes the column head true for both. Should the author instead want
only the tok/s figure, the row would then carry a number that is not literally a latency budget
under a column named for one; keeping both is the cleaner option.
