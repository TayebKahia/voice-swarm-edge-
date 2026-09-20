Restructure the Mémoire d'Ingénieur (thesis/main_ingenieur.tex) the way the Master was restructured
on 25-26 Sep 2026: a Background chapter before the state of the art, the state of the art rebuilt
as comparison tables with critical comparisons and numbered research gaps, and the chapters grouped
into TWO parts (Part I: Background and state of the art; Part II: the contribution), which is what
Prof. Khaldi asked for on 26 Sep. Deposit is Sunday 27 Sep. Work in this order and do not skip the reviews.

## Load first, in this order
1. CLAUDE.md (commit rules: one commit per coherent change, long messages with the reasoning, NO
   Co-Authored-By trailer, check HEAD before amending -- another session may commit concurrently).
2. .agents/skills/thesis-writing/SKILL.md, whole file. The Master blueprint there ("seven chapters in
   two parts", Background rules, State of the art rules) is the model; the Ingénieur blueprint must
   be rewritten to match, as part of this work.
3. prd.md §2 (RQ2, RQ3, C4), §3.1 (the Ingénieur outline, six chapters -- to be rewritten to seven in
   two parts), Table 3 (write-once: what each document owns; the row "Foundations" says the
   Ingénieur background, when written, owns speech pipelines, UAVs, swarm control and real-time
   systems, and names the Master's foundations in one sentence each). prd.md wins over SKILL.md.
4. .scratch/sprint-pfe/STATE.md, the sections dated Fri 25 Sep: "Master RESTRUCTURE", "Master state
   of the art REBUILT", the review closures for issues 15, 16, 17, and "Master LAYOUT pass". They
   record every decision and its reason.
5. git log for the Master's restructure, to mirror its shape and its commit messages:
   1109a91 (restructure + Background), 4bb8138 (review tooling re-pointed), 7830694 (state of the art
   rebuilt), 896ab25 and 5f4fb27 (review fixes), 16d70f4 (table rows added), d085655 (whole-document
   pass), 4c64e7c (layout pass).
6. The Master's own files as the worked example: thesis/main_master.tex (parts), thesis/master/
   ch2_background.tex, thesis/master/ch3_state_of_the_art.tex (tables with a "This work" last row,
   "Critical comparison." paragraphs, "Research gaps" with Synthesis and Gap G1..G3 mapped onto
   C1..C3).
7. The ESI PFE report template, ~/Downloads/thesos/thesis_ex/PFE_report_template_share/main.tex:
   introduction, \part{Background} with a definitions chapter, a state-of-the-art chapter,
   \part{Design & Implementation}, conclusion. This is the school's expected shape. It also has a
   "Project Management" chapter that the Ingénieur outline does not: do NOT add one unless the
   author says the supervisor asked for it.
8. The Ingénieur as it stands: thesis/ingenieur/ch1_introduction.tex .. ch6_conclusion.tex, all six
   written and reviewed (issues 06, 07, 10-14 in .scratch/thesis-review/issues/). Its Ch2 already
   has two comparison tables (tab:voice-uav-survey, tab:lim-positioning) and a Gap section stated as
   four properties conceded by name; keep what is right, bring it to the Master's form.
9. docs/agents/thesis-chapter-review.md and .scratch/thesis-review/spec.md (the review loop:
   script, agents, verifier, author decides, re-run, commit) and tools/review/ (lib.py has an
   INGENIEUR list and ingenieur_chN.py scripts that must be re-pointed like the Master's were in
   4bb8138; selftest.py must keep passing; use ~/miniconda3/envs/pfe_swarm/bin/python).

## Target structure (confirm with the author before writing)
1 Introduction (as is) | Part I, Background and state of the art: 2 Background (NEW), 3 State of the
art (Ch2 rebuilt) | Part II, Contribution (or "Design and implementation", the author's call): 4
Architecture and design, 5 Implementation, 6 Validation | 7 Demonstration, limitations and
conclusion (outside the parts). Two parts, exactly as the Master has since 26 Sep. File names keep their historical
numbers; never hardcode a chapter number in prose, use \ref. The Master's structure paragraph and
any hardcoded Ingénieur chapter numbers in the Master must be checked afterwards (prd Table 3 c).

## Background chapter rules
Foundations only, for a jury member outside the sub-field: speech pipelines (keyword spotting,
speech recognition, voice activity detection, endpointing), UAVs and swarm control (the vehicle,
the controller, separation, the simulation backends' idea), real-time systems and latency budgets
(p50/p95, preemption, budget allocation), the single-board computer, state machines and command
buses. No result, no design decision, no positioning. Anything the Master's Background defines
(language models, LoRA, quantisation, GBNF, intent/slot SLU, metrics) gets ONE sentence and a
cross-reference "the \emph{M\'emoire de Master}"; never re-explain it (write-once). Closed
bibliography: cite only keys in thesis/references.bib; where a foundation needs a source that is
not there, leave a visible \TODO{} naming it; .scratch/thesis-bibliography/ingenieur-candidates.md
holds unverified leads, never evidence. \gls{} for every acronym; ASCII body; headings as short noun
phrases; no sentence over 40 words.

## State of the art rules
Same four-part shape per section as the Master: taxonomy sentence, one comparison table along
fixed axes with "This work" as the last row (a dash marks what the review did not establish from
the source; a wrong cell is a BLOCKER), a "Critical comparison." paragraph reading the table column
by column and comparing the studies TO EACH OTHER, then a final "Research gaps" section (Synthesis,
then numbered gaps) where the studies are compared to this thesis ONLY, each gap closed by the part
of Contribution C4 (or by an architecture decision of Chapter 4) that closes it. Voice-UAV
literature belongs here (Table 3); constrained decoding and quantisation literature stay in the
Master and are named in one sentence with a cross-reference.

## Steps
1. Rewrite prd.md §3.1 (Ingénieur) and Table 2/3 rows, with a dated rationale paragraph, as
   1109a91 did for the Master. Rewrite the Ingénieur blueprint in SKILL.md.
2. Write thesis/ingenieur/ch2_background.tex; git mv ch2_state_of_the_art.tex to
   ch3_state_of_the_art.tex; rebuild it; wire main_ingenieur.tex with \part{}s; move any
   foundation text out of Ch1/Ch3/Ch4 into the Background (one commit per coherent change).
3. Re-point tools/review (lib.py INGENIEUR, ingenieur_ch1..ch6.py indices, selftest anchors), and
   write the pre-review script for the Background (model: tools/review/master_bg.py).
4. Build: cd thesis && rm -rf build/ingenieur && latexmk main_ingenieur.tex; require 0 `^!`,
   0 undefined citations/references, 0 "Float too large", 0 Overfull. python tools/check_tex.py
   <file> per chapter (cross-chapter \ref findings are expected false positives).
5. Review loop for the new Background and the rebuilt state of the art as issues 18 and 19
   (citation agent, argument agent, verifier; the author decides each surviving finding), then the
   whole-document pass as issue 20 (Template B), then the Ingénieur layout pass (the shared
   preamble already has the float settings from 4c64e7c; sparse pages were noted at 22-23, 33, 43,
   48 of the 77-page build and not examined).
6. Record everything in STATE.md and the issue files; commit thesis/ and tools/ separately.

## Do not
- Do not touch thesis/master/ except to fix a hardcoded Ingénieur chapter number.
- Do not add bibliography entries the author has not verified, unless the author explicitly
  delegates the verification (as they did for SLURP and Snips: an agent opens the primary page and
  records every cell fact with a quote, .scratch/thesis-bibliography/slu-rows-verified.md is the
  model).
- Do not add a Project Management chapter, jury names, or the repository address to the Ingénieur
  without asking; the Master names the repository in its Method chapter.
- Do not commit files another session has modified; check git status before every commit.

Start by confirming the target structure with me in one message, then begin with prd.md.
