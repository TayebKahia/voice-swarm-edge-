# Issue 08: whole-documents (Master)

Status: ready-for-human
Blocked by: 01, 02, 03, 04, 05, 09
Documents: thesis/main_master.tex

## What

Template B of `docs/agents/thesis-chapter-review.md`, for the Master: RQ traceability through
every chapter, headline numbers identical across the three abstracts and all chapters, definitions
consistent, forward references true, write-once across the two documents, front matter, clean build.

The write-once check (Template B item 7) compares against the Ingénieur chapters as they stand
now. Issue 10 repeats it once the Ingénieur is complete.

Split 2026-09-24: this issue covered both documents, so the unwritten Ingénieur Ch2 (issue 07)
blocked the finished Master. The Ingénieur pass is now `issues/10-whole-document-ingenieur.md`.

## Agents

One reviewer + verifier. Not split by dimension: this pass exists to see every chapter at once.

## Before running

Re-run every chapter script (all must be 0 FAIL) and `tools/review/selftest.py`.

## Comments

- Added 2026-09-23 (from issue 01): **scope check.** Could a reader who has only this document
  state the system end to end, what is simulated, the language, the command vocabulary, what is
  out of scope, and how the work divides between the two theses? A per-chapter review against
  the section list does not ask this.

### 2026-09-24 -- review round 1 (1 reviewer + verifier)

**Before running.** Every Master chapter script re-run, all 0 FAIL: Ch1 0 FAIL / 2 WARN / 40 PASS;
Ch2 0 / 1 / 46; Ch3 0 / 4 / 132; Ch4 0 / 1 / 208; Ch5 0 / 1 / 96; Ch6 0 / 0 / 54. The self-test passes
(10 planted errors, 10 caught). Every WARN is one already justified in its own issue (hand-typed
`CPU`, `LoRA`, `JSON`; "small language model" inside the quoted RQ1; the negated, cited "not
guaranteed" in Ch3-Ch5; the 1,350 ms sum row; Ch2's three-plus-control coherence note). The only
report that changed on re-run is `reports/master_ch2.md`: two `results/table18_quantisation_delta.md`
and one `table16` row numbers moved after the other session's `eval/` commits, and the heading check
now lists Ch6. No expected value changed.

**Build.** Clean from scratch (`rm -rf thesis/build/master && latexmk main_master.tex`, after
checking that no other latexmk or xelatex process was running): exit 0, 63 pages, 0 `^!` errors,
0 undefined citations, 0 undefined references, 0 "Float too large", 0 Overfull boxes, and no
TODO / CHECK / figtodo text in the PDF. Remaining warnings, all judged non-findings (NIT-5): the
Amiri small-caps font shape on the Arabic cover, "biblatex: Language 'arabic' not supported" (no
Arabic bib entry), and xdvipdfmx "Object @table.3.3 already defined" twice, which is hyperref
defining `tab:metrics`'s anchor once per page of a two-page `xltabular`.

**Scope of the pass.** Reviewed at `5ed20ba`; the Master files are unchanged through `4b34475`
(the commits in between are the other session's Ingénieur Ch3, Ch5/Ch6 and `eval/` work). The
write-once check (item 7) therefore ran against the Ingénieur with Ch1 in prose, Ch3 through §3.4,
and Ch2, Ch4-Ch6 as scaffolds; Ingénieur Ch3 §3.5 and the Ch5/Ch6 changes landed during the review
and were not compared. Issue 10 repeats the check on the finished Ingénieur, as planned.
Agent reports: `agents/08-master/reviewer.md`, `agents/08-master/verifier.md`.

**Verdict.** Ready after fixes; no rework. These pass:
- item 1, the golden thread: RQ1 and C1-C3 traced Ch1 -> Ch3 -> Ch4 -> Ch5 -> Ch6 with no empty cell;
- item 3, every headline number is identical at every occurrence (13 values, all abstracts and chapters);
- item 4, the three abstracts carry the same numbers (0.36-1.2 B, 200, 0.935, 17.5 pp, 2,500, 622, 3,122)
  and, as far as the French and Arabic can be read, the same qualifiers; issue 09's NEW-1 landed in all three;
- item 6, all 44 `\ref` targets do what the text says;
- item 7, no duplicated exposition against the Ingénieur as it stands;
- item 8, the acronym list (18 entries) is complete for every `\gls` key used, the LoF/LoT titles are
  short forms, 45 printed bibliography entries = 45 cited keys, the title page fields are right;
- item 10, the build.
Must-check C: "significant", "not established", "re-baselined" and "reference text" are present at
every occurrence of their number in the abstracts and chapters; "exploratory" and "language-model
process only" are absent from the abstracts only because 6.5 pp and 0.68 GiB are not quoted there.

**Verified BLOCKER/MAJOR.** There were no BLOCKERs. The reviewer raised 1 MAJOR; the verifier confirmed
it, tried three disproofs, checked the fix under every rule, and added no NEW item after spot-checking
the abstracts and the five headline values most likely to hide a dropped qualifier.

| # | Sev | Where | Finding | Verifier | Proposed fix (passes every check as written) |
|---|---|---|---|---|---|
| M-1 | MAJOR | `frontmatter/abstract.tex:19-20`, `frabstract.tex:20`, `arabstract.tex:20` | The method paragraph of all three abstracts says the control model "separates model family from size" (FR "sépare l'effet de la famille de modèles de celui de la taille"; AR the same). Ch4 l.176-177 says the data "measure a family difference at about 0.5 B parameters; they do not express it as a share of a size effect"; Ch3 l.287-288 "It does not remove family from the size comparison"; Ch6 l.87-88 the same. Ch1 dropped exactly this wording under issue 03 V20 (`ad09efb`); the abstract was drafted after that (`9362cd0`) and issue 09's NEW-1 re-derived only the §6.1 sentences of the abstracts (`afc692f` touched only the "timed on the board" clause of this sentence), so it survived | CONFIRMED, MAJOR (borders BLOCKER, since Ch3 negates it in terms; kept MAJOR for consistency with issue 03 V20 and issue 04 A8, which rated the same claim MAJOR in Ch1 and Ch4). Grep over `thesis/master/` shows these three lines are the only remaining occurrences | Ch1 l.137-138's wording in all three languages. EN: "and the fourth, matched in size to one of them, measures a model-family difference at fixed size." FR: "et le quatrième, de taille appariée à l'un d'eux, mesure une différence entre familles de modèles à taille fixée." AR: "أما الرابع، المماثل في الحجم لأحدها، فيقيس فرقًا بين عائلات النماذج عند حجم ثابت." No new number, no hedging word in any language, not stronger than Ch4/Ch6, no `tools/review` script reads the front matter, so no anchor is touched. `abstract.tex:19` is an overlong source line and can be rewrapped |

**MINOR/NIT (reviewer only, not verified except where noted).** Proposed wording is in the reviewer
report §7; the key items:
- **MIN-1** Ch4 l.140-141 and l.348-350: the three Ingénieur-sourced timing figures (3,122 / 1,063 / 751 ms)
  carry no thermal state, although Ch1 l.35-37 promises one for every timing figure; only Ch5 l.81-82
  says "cooled" for 3,122. `results/exp2_latency_budget.md:3` says cooled. -> add "on the cooled board"
  at both sites; the `master_ch4.py` anchors on those sentences stay intact. (Verifier: correctly MINOR;
  the fix relies on the results header.)
- **MIN-2** Ch1 l.75-79 (scope check, item 9): "entirely on the Raspberry Pi 5 ... the swarm controller
  executes it" reads as the controller running on the Pi; the Master never says the state machine,
  controller and simulation run on a workstation (Ingénieur Ch1 l.48-50 does). -> "and the swarm
  controller, which runs with the simulation on a workstation linked to the board, executes it."
- **MIN-3** `p50`/`p95` are used in three Ch3 tables before Ch4 l.122 expands them. -> expand in the
  Percentiles row of `tab:metrics` (ch3:574); check `master_ch3.py` for an anchor on that row first.
- **MIN-4** three names for one split: `test_golden` (tables), "golden set" (Ch3, abstracts), "golden
  split" (Ch4-Ch6, 14 uses), never tied together. -> one parenthesis at ch3:201.
- **MIN-5** the Intent-F1 requirement (Table 3.4, >= 0.90) is measured at Ch4 l.82-83 but never given a
  verdict; Ch4 l.376 omits it from the list of thresholds met. -> add "the 0.90 intent-F1 threshold"
  to that list; first confirm `master_ch4.py`'s "configs meeting all six" check counts from data.
- NITs:
  - **NIT-1** SHA-256 hand-typed twice while the `sha` acronym key exists and is never used, so SHA is
    absent from the printed list. Either `\gls{sha}` or delete the key.
  - **NIT-2** C3's metric lists (ch1:117-118, ch2:28, 198-199) omit the safe-failure rate, which Ch6
    relies on. `master_ch1.py` checks each named C3 metric against a `surface_b.csv` column, so the
    script may need a second source before the word is added.
  - **NIT-3** full checkpoint names in Ch1/Ch3 ("Qwen2.5-0.5B-Instruct", "H2O-Danube3-500M-Chat"),
    short names elsewhere. Acceptable if deliberate.
  - **NIT-4** FR/AR abstracts use "référence" / "مرجعي" for both the golden set and the reference text
    in one sentence; the English distinguishes them.
  - **NIT-5** the three remaining build warnings need no action.

**Not re-raised.** Issue 05 C5-C14, M14-M16 and NITs; issue 09 MINOR-3, -4, -6, -7 and NIT-1..6; issue
09's step-3 scope; issue 03's latency-budget table staying in Ch3; the title-page placeholders; the
chapter WARNs. The reviewer checked each against the later edits (Ch6, abstracts, Ingénieur Ch3):
none has become wrong.

**Unverified** (reviewer §10): the Arabic qualifiers beyond a non-native reading; the Raspberry Pi 5
RAM variant (the Ingénieur says 8 GB, the Master says none, no `results/` file carries it); whether
`master_ch4.py`'s six-criteria check counts from data (bears only on MIN-5's fix); issue 09's "widest
margin" item stands as before.

**Corrections to the agent reports.** The reviewer cites issue 03's V20 at "Comments l.416-417"; the
verifier found it at l.168-169. Cosmetic; the reports are left as written.

**For issue 10 (Ingénieur side, not Master findings).**
- Ingénieur Ch1 l.182 repeats the Master's formation-accuracy definition (`tab:metrics`, ch3:575)
  verbatim; the Master owns the definitions of record (Table 3).
- Ingénieur Ch1 l.119-121 says the first five functional requirements "are stated in the Mémoire de
  Master"; the Master carries them as method (§3.1-§3.5), not as requirement rows.
- Three Master cross-references point at Ingénieur sections whose prose is not yet written
  (ch3:212-213 -> Ingénieur Ch6 limitations; ch3:528 -> Ch5 acoustic robustness; ch4:140, 348,
  ch5:281-282 -> Ch5 §5.1/§5.3). The names match the Ingénieur's own; the content must be checked
  once written.
- When the Ingénieur abstracts are drafted, check the method paragraph against the chapters it
  derives from, not only the verdict paragraph against Ch6: issue 09's NEW-1 and this M-1 are the
  same failure mode twice.

**Examiner view** (reviewer §11): the reference-text vs speech question and the re-baselining
question are both answered in the text (ch4:13-16, 58-64, 357-373; ch5:52-68, 281-292; ch6:23,
31-37). The reproducibility question is partly answered: versions, seeds, protocol and every table's
`results/` source are given, but no repository or artefact location appears in the document (issue
03, "revisit before submission"), the GGUF converter commit is unpinned (ch3:502-504) and the
control's training image is unrecorded (ch3:502).

**Decisions only you can make:**
- M-1: take the fix in all three abstracts (recommended; it is Ch1's own wording, and no anchor moves).
- Which MINORs to take. MIN-1 and MIN-2 are the cheapest and close a Ch1 promise and the scope gap;
  MIN-5 needs the `master_ch4.py` check confirmed first.
- NIT-1 (use or delete the `sha` key), NIT-3 (whether the two naming conventions are deliberate).
- Whether the artefact-location and converter-pin gaps from the examiner view are addressed before
  submission (a standing issue-03 decision, not a new finding).

### 2026-09-24 -- author's decisions, and what was applied

The author took **M-1 in all three abstracts, MIN-1 and MIN-2**, with the reviewer's wording as
verified. Applied:
- **M-1** (`frontmatter/abstract.tex`, `frabstract.tex`, `arabstract.tex`): the method paragraph now
  says the fourth model "measures a model-family difference at fixed size" / "mesure une différence
  entre familles de modèles à taille fixée" / "فيقيس فرقًا بين عائلات النماذج عند حجم ثابت". This is
  Ch1 l.137-138's wording, the one issue 03 V20 put there. The overlong English and French source
  lines were rewrapped; nothing anchors on the front matter.
- **MIN-1** (`ch4_results.tex`): "has a p95 of 751~ms on the cooled board" (§4.1) and "measured the
  full parse path for the selected configuration alone, on the cooled board: from end of speech, ..."
  (§4.7), so the three Ingénieur-sourced timing figures (751, 3,122, 1,063 ms) now carry the thermal
  state Ch1 promises. Source: `results/exp2_latency_budget.md` header, "Raspberry Pi 5, cooled". The
  `master_ch4.py` anchors on both sentences are unchanged; one was rewrapped, which the
  whitespace-tolerant matcher accepts.
- **MIN-2** (`ch1_introduction.tex` l.78-80): "and the swarm controller, which runs with the
  simulation on a workstation linked to the board, executes it." Matches Ingénieur Ch1 l.48-50.

**Script error found while re-running, fixed in `tools/review`.** `master_ch4.py` and
`master_ch5.py` stopped with `StopIteration` on HEAD as well as on the edited chapters: the other
session's `4d8d701` renamed the rows of `results/exp2_latency_budget.md` ("SLM prefill" is now
"Language-model prefill"; the end-to-end row lost its `(T0; NFR-2)` suffix), and both scripts looked
the prefill row up by the old prefix. The lookup now matches on "prefill" (the only row containing
it). No expected value changed. The end-to-end lookup already matched on "end of speech" and was
unaffected, which is why `master_ch6.py` kept passing.

**Final state.**
- Scripts: Ch1 0 FAIL / 2 WARN / 40 PASS; Ch2 0 / 1 / 46; Ch3 0 / 4 / 132; Ch4 0 / 1 / 208;
  Ch5 0 / 1 / 96; Ch6 0 / 0 / 54. The same counts as round 1. The self-test passes.
- `check_tex`: clean on Ch1, Ch4 and the English abstract; on the French and Arabic abstracts it
  reports non-ASCII notes only (30 and 27; one more in the French than before, from the rewrapped
  line), all marked fine under XeLaTeX.
- Build (`latexmk main_master.tex`, incremental on the clean round-1 build; no other latexmk or
  xelatex was running): 0 errors, 0 undefined citations or references, 0 dropped floats, 0 overfull
  boxes, 63 pages. The new English, French, Ch1 and Ch4 wording is in the PDF text; the Arabic line
  compiles (pdftotext does not reproduce shaped Arabic reliably enough to grep it).
- The six `reports/master_ch*.md` are regenerated; their line-number columns moved with the other
  session's `results/` changes and with the rewrapped lines.

**Left for the author** (not decided in this round): MIN-3 (p50/p95 expanded in `tab:metrics`),
MIN-4 (tie "golden split" to `test_golden`), MIN-5 (the Intent-F1 verdict; confirm `master_ch4.py`'s
six-criteria check first), NIT-1 to NIT-5. Status stays ready-for-human until these are taken or
kept as written.
