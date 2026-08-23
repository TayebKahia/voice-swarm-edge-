# Issue 01: master-ch1

Status: resolved
Blocked by: 00 (resolved)
Chapter: thesis/master/ch1_introduction.tex
Script: tools/review/master_ch1.py
Report: .scratch/thesis-review/reports/master_ch1.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_ch1.py
```

## Agents (Template A, docs/agents/thesis-chapter-review.md)

- **Reviewer** -- D1, D2, D4, D5, D6, D7, D8, D10, D11, D12. D3 is done by the script (every Ch1 number
  recomputed; read only UNTRACED rows); D9 is done except the clean build.
- **Verifier** -- BLOCKER and MAJOR findings only.

## What the script establishes (baseline 2026-09-23: 3 FAIL, 13 WARN, 33 PASS; the 3 FAILs are D11)

- Every throughput figure (27.93, 14.53, 18.13 tok/s; the 40% margin; 22 tokens / 1.1 s = 20 tok/s)
  matches `results/thermal_headroom.md`.
- RQ1 is prd.md §2 verbatim; C1-C3 are listed, C4 is not; C3's metrics are columns the harness writes.
- The structure paragraph visits the chapters in `main_master.tex` order.

## Seeded findings (judge each)

- No `\label{chap:introduction}` -- every other Master chapter carries its chap: label.
- Acronyms typed by hand (CPU, JSON, GGML, BNF, GBNF; long forms of SBC, SLM, EM). Ch1 is where
  each `\acrfull` belongs, since it is first in document order.
- "three candidate models" (l.16) vs Ch2's "four candidate models": consistent in fact, but check the
  reader can see why.
- The S3 story (l.43-57): the script only confirms the words occur in the spike report -- read it.

- **D11**: "Spike S3" (l.43) is project-internal -- present it as a preliminary zero-shot
  experiment; "Exp-0" and "Exp-1" (l.102-103) are never defined in the Master.

## Done when

Zero FAIL on re-run; each WARN fixed or justified under Comments; findings decided; committed.

## Comments
### 2026-09-23 -- review round 1 (reviewer + verifier)

Verdict: ready after fixes. No rework needed, but the preliminary-experiment paragraph (l.43-57) has to be rewritten.

Verified BLOCKER/MAJOR (verifier: 6 confirmed, 1 partly):

| # | Sev | Line | Finding | Verifier | Fix |
|---|---|---|---|---|---|
| 1 | BLOCKER | 46 | "every output stayed grammar-valid" is false: two of the five outputs were truncated and failed to parse (S3:24-25) | CONFIRMED | three complete, two cut off mid-list and failed to parse |
| 2 | BLOCKER | 20 | "three threads ... reserves for the rest of the pipeline" is inverted: cores 1-3 are for STT+SLM, core 0 is the rest (Table 7, ch3:462) | CONFIRMED | "the three cores (three threads) the deployed configuration reserves for speech recognition and language-model inference" |
| 3 | MAJOR | 13-15 | sbc2025: "no board serves a model reliably" above the ceiling is contradicted (the paper reports 3B at 2-5 tok/s as acceptable); it is a benchmark, not a survey | CONFIRMED | "a recent benchmark of twenty-five quantised language models on three single-board computers finds that such boards reliably support models of up to about 1.5 billion parameters, with larger models dropping to a few tokens per second" |
| 4 | MAJOR | 47-56 | the lesson (bounded grammar + validator) does not cover the mis-addressed takeoff (ids [1] is in range; that one belongs to fine-tuning); the truncated outputs fell back to HOVER, so nothing reached the controller unfiltered | CONFIRMED | pair each lesson with its defect |
| 5 | MAJOR | 86-88 | C3 "each fine-tuned model at each quantisation level on the deployed edge hardware": 3 of 4 quantised; accuracy scored on the workstation; Q8_0 not timed on the Pi | CONFIRMED | "three of the four fine-tuned models at two quantisation levels, accuracy scored under the deployed runtime and grammar, latency and throughput timed on the Pi 5 (Q4_K_M)" |
| 6 | MAJOR | 78-80 | C1 claims "a two-layer semantic validator" that the Master does not describe (ch3:40-45 gives it to the Ingénieur); layer 3 is a state machine, not a semantic check | PARTLY | narrow C1 to schema + bounded grammar, "layer 1 of a three-layer validation stack" whose other layers are in the Ingénieur |
| 7 | MAJOR | 43-51 | "Spike S3" is internal; project-history narration; a sentence of ~110 words; not reproducible | CONFIRMED | rewrite as a preliminary zero-shot run (Q4_K_M, greedy, 48-token cap, five commands, early grammar draft); every fact checked against S3 and cmd.gbnf |

MINOR/NIT (not verified, #8-#29): acronyms -> \acrfull (all keys exist), \label{chap:introduction},
"three candidate models" -> name the three and the control, Exp-0/Exp-1 -> names (policy 00),
C1 before its definition, register (l.17-18, l.29, l.109-111, l.36), "production configuration" /
"wider project" / "sealed", RQ3 half-named at l.69, Ch2 title "Related Work" -> "Related work",
long sentences, llamacpp bib has no year, dutta2024 wording, acronym long forms in Title Case.

Found in Ch3 (for issue 03): ch3:325-327 says accuracy runs on the Pi, while ch3:389-391, Ch4 and
thermal_headroom.md say the workstation; ch3:94-98 repeats the S3 story with "spike-era";
"structurally unreachable" (ch3:99) is too strong (repeats are still possible).

### 2026-09-23 -- draft of the fixes (awaiting the author's approval)

All 29 findings are drafted in thesis/master/ch1_introduction.tex, except #8's optional
"one output in 3,540" sentence, which was left out. The script shows 0 FAIL and 3 WARN:
- l.78, l.80: `small language model` and `CPU` inside the RQ1 quote. Justified: RQ1 is quoted
  verbatim, and SLM and CPU are already expanded earlier in the chapter.
- l.125 \ref{chap:conclusion}: expected. The chapter is not written yet.

Changes outside Ch1, each forced by a finding:
- Ch2: title changed to "Related work" (#21); "four candidate models" changed to "four
  fine-tuned models" (#9).
- Ch4: \acrfull{gbnf}, \acrfullpl{slm} and \acrfull{sbc} are now \gls, since Ch1 has the first
  use. \acrfull{wer}, {crr} and {gguf} are now \gls too, because **\acrfull does not mark the
  entry used**: the next \gls printed the long form again ("word error rate (WER)" appeared
  twice in Ch4).
- shared/acronyms.tex: long forms are lower case (except proper nouns), since \gls prints them
  mid-sentence (#29). GGUF drops "(quantised weight format)". The header comment is corrected.
- references.bib llamacpp: added `version = {b10863}`, the build STATE.md records. No year was
  added: there is no release date on record (#26).
- shared/preamble.tex: the keep-section rule exempted the first section of a chapter with
  `\value{section}>0`, but titlesec has already stepped the counter by then. The first section
  was therefore only ever protected by landing on an empty page. Ch1's new opening sentence
  exposed this: §1.1 was pushed off the heading page on one pass and pulled back on the next,
  and latexmk gave up ("needed too many passes"). The test is now `>1`. The Ingénieur TOC is
  unchanged. From §1.2 on, every Master page shifts by exactly +1, because Ch1 is one page
  longer.
- SKILL.md, the review template, lib.py: rule changed from "\acrfull on first use" to "\gls at
  every use". lib.py now FAILs on \acrfull; the self-test has a mutation for it (10/10 pass).

### 2026-09-23 -- scope paragraph (author's request)

The author asked whether a reader of Ch1 would understand the project scope. Not fully: the
full pipeline, an example command, simulated vs real aircraft, English only, ten intents, what
is out of scope, and why there are two theses were all missing. Neither the script nor the
reviewer caught this, because both judged the chapter against its section list rather than
against what a reader needs. A 120-word scope paragraph now opens §1.3 Objectives. Its facts
come from prd §1 / §15, Ingénieur Ch1 l.45-52 and Master Ch3 l.12. No new section was added
(the outline is frozen). The later sentence about the other document was trimmed so it no
longer repeats the paragraph. The script still shows 0 FAIL; the build is clean.

For issue 03: "22 tokens" (Ch1 l.26) has no derivation anywhere in the thesis. The Ch3 latency
table gives only the 1,100 ms, and the 22 is in prd Table 6 alone.

### 2026-09-23 -- author's read; resolved

The author checked every changed sentence and confirmed the facts. Three changes came out of the read:
- l.8 `\enlargethispage{\baselineskip}`, added by another session: kept.
- l.75 "The system this work belongs to converts" -> "This work is part of a system that
  converts". The author flagged it: grammatical but conversational, and the subject arrives late.
- l.120-124, C3: another session had rewritten the end of C3 to say the delta belongs to the
  deployed pipeline (precision, runtime and grammar change together), which agrees with Ch4
  §4.4. That was correct, but it dropped the motivation ("rather than inherited from larger
  models and generic benchmarks"). It is now two sentences, carrying both points.

Final state: 0 FAIL; 3 WARN, all justified above (the RQ1 quote is verbatim x2;
chap:conclusion is not written yet). The build is clean. bf0017b was already pushed, so these
went into a follow-up commit rather than an amend.
