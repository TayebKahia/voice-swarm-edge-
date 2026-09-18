# Issue 15: master-bg (Background, Chapter 2 since 25 Sep)

Status: resolved (two author bib entries outstanding: Pi 5 brief, Vaswani 2017)
Blocked by: 01 (resolved)
Chapter: thesis/master/ch2_background.tex (~425 lines, 23 cites; written 25 Sep, committed `1109a91`)
Script: tools/review/master_bg.py
Report: .scratch/thesis-review/reports/master_bg.md

Numbered 15 because it was drafted after 00-14 existed (spec.md: issues are never renumbered).
The chapter is new: it holds the foundations the old Chapters 2 and 3 used to carry inline
(prd.md §3.1 item 2, restructure of 25 Sep after the supervisor meeting). Issue 02 reviewed the
old Chapter 2; the passages moved here were reviewed there and are re-read here in their new
place, not re-litigated.

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_bg.py
```

## Agents

- **Citation agent** -- D5 only. Worklist: the report's citation sheet (23 keys) and "Numbers
  quoted from papers or tool documentation" (llama.cpp format construction, QLoRA's 4-bit base and
  all-linear-layers finding, MASSIVE's 1 M / 51 / 60 / 55). Open each identifier; verdict per row
  SUPPORTS / PARTIAL / DOES NOT SUPPORT / COULD NOT ACCESS. Also D5c: a textbook claim with no
  citation is fine in a Background chapter *if* it is textbook-level; a claim about a specific
  tool, paper or figure without one is a finding.
- **Argument agent** -- D1, D2, D4, D6, D8, D10, D11, D12. Worklist: the report's "Definitions to
  verify" table. Focus: (a) every definition is textbook-correct (LoRA scaling and parameter count,
  memory-bound decode, McNemar's discordant-pair logic, Bonferroni, Pareto dominance, perplexity);
  (b) foundations only -- no design decision, no result, no position on the literature (each of
  those belongs to Chapter 4, 5 or 3); (c) the generic metric definitions here agree in meaning
  with Chapter 4's tab:metrics; (d) level and length for a jury member outside the sub-field.
- **Verifier.**

## What the script establishes (baseline: see report)

- Seven foundation sections in prd.md §3.1 order, labels sec:bg-*, closing Conclusion.
- No throughput figure, metric value, p-value, project code or deployment decision in the prose.
- The three moved passages are stated here and nowhere else; the old locations cross-reference.
- Model table recomputed from results/table33_iso_parameter.md; the 144-bit arithmetic recomputed.

## Seeded findings

- Two visible markers, both the author's: \TODO (Vaswani 2017 not in references.bib) and \CHECK
  (Raspberry Pi 5 processor/memory designations, no bib entry). Known; not to be re-reported.
- "Every model compared in this work is the instruct variant ... rendered by the template its model
  card publishes~\cite{llama32card}" cites one model card for four models -- PARTIAL at best.
- The memory-bound argument cites AWQ for "weight-only quantisation is the lever of choice for
  throughput on a CPU"; AWQ's setting is GPU/edge accelerators. Check the scope of the citation.

## Comments
### 2026-09-25 -- review round 1 (citation + argument + verifier)

Script baseline: 0 FAIL, 8 WARN (six acronym WARNs are section/paragraph headings, by convention
exempt; the two markers are the author's), 67 PASS. Self-test: three planted errors caught
(wrong parameter count -> claim; a throughput figure in the foundations -> foundations; a moved
LoRA sentence repeated in Method -> write-once). Two script errors fixed before the run (LoRA
anchor wording; nth=1 for the 144-bit arithmetic) and one checker blind spot (tools/check_tex.py
now blanks display-math bodies before the bare-underscore rule; its own self-test passes).

Verdict (both reviewers, verifier concurs): ready after fixes. No BLOCKER. 5 MAJOR, all CONFIRMED
at MAJOR by the verifier; 14 MINOR, 8 NIT from the argument agent; 5 MINOR, 2 NIT from the
citation agent. Citations: 35 occurrences, 29 SUPPORTS, 6 PARTIAL, 0 DOES NOT SUPPORT; every
quoted number found in its primary source. Definitions: all textbook-correct except the gated
feed-forward block.

Verified MAJOR (verifier: 5 confirmed, 0 partly, 0 refuted):

| # | Sev | Line | Finding | Fix (verifier's judgement) |
|---|---|---|---|---|
| A-1 | MAJOR | 48-50 | Gated FFN described as sigma(gate*up); all four models run down(silu(gate(x)) * up(x)) (transformers LlamaMLP/Qwen2MLP; four config.json hidden_act=silu) | Reviewer's wording; optionally name the activation as "the sigmoid-weighted linear unit in every model of Table tab:bg-models" |
| A-2 | MAJOR | 386-388 | "the comparison of parsers in this document therefore takes reference transcripts as input" = the protocol decision and its WER-ceiling justification of ch3_method (l.464-469, 532-535), restated; the chapter's own charter sends decisions to Chapter 4 | Keep the generic fact, hand the choice to the definition of record (verifier's shorter form) |
| C-1 | MAJOR | bib edwards1948 | Title wrong since 4445be5; Crossref 10.1007/BF02289261: "Note on the ``Correction for Continuity'' in Testing the Significance of the Difference between Correlated Proportions"; every other field right | Replace the title line |
| C-2 | MAJOR | 84-85 | llama32card cited for four models' chat templates; the other three cards exist and publish templates but are not in the bib | Argument agent's finding-3 wording (drops the cite; resolves A-3 too). llama32card stays cited in Method |
| C-3 | MAJOR | 244-246 | awq cited for "weight-only quantisation is the lever of choice for throughput on a CPU"; AWQ's roofline is an RTX 4090, its CPU content is TinyChat engineering; AWQ itself says dequantisation is costly on SIMD CPUs | Verifier's combined sentence: proportionality as an upper bound, cite on the rationale clause, "matter of measurement" for a given processor |

Verifier rejected/downgraded: A-16 (delete the whisper.cpp clause) conflicts with C-7 (cite it):
keep the clause, add \cite{whispercpp}. A-17 (delete "intent accuracy"): the term appears in the
state-of-the-art MASSIVE row, keep. A-8 -> optional NIT. A-14: only the KL half was wrong.
A-18, A-24 style. A-6 ("nearly all of a model's parameters") confirmed with embedding shares
computed from the configs: 27.6% Qwen2.5-0.5B, 13.0% SmolLM2, 21.3% Llama-3.2-1B, 19.1% Danube3.
NEW-1 (NIT): "delimits a system turn" is not true of Danube3's template; "where the template has
one".

Pi 5 \CHECK: designations verified correct by the citation agent against product brief
RP-008348-DS-6 (BCM2712, quad-core Cortex-A76 @ 2.4 GHz, LPDDR4X-4267). The author resolves it by
adding the brief as a bib entry; the same entry covers the throttle-flag sentence (C-8). One
adjacent clause UNVERIFIED: "no accelerator a language-model runtime can use" (VideoCore VII has
Vulkan 1.2 and llama.cpp has a Vulkan backend); safer wording "no accelerator that a language-model
runtime uses in practice".

Awaiting the author's decision on each finding (spec.md step 5). Script anchors: none of the
five MAJOR fixes touches an anchor in master_bg.py.

### 2026-09-25 -- author's decision and fixes applied

Author: apply all five MAJORs and the minors. Applied in one edit (chapter) plus one bib line:
- A-1 gated FFN rewritten to the SwiGLU form; A-6 "most ... the embedding table holding the rest".
- A-2 reference-transcript decision removed; generic fact kept, input choice handed to the
  definition of record (verifier's shorter form). A-10 corpus WER wording; A-13 bootstrap interval
  defined in the same paragraph.
- C-1 edwards1948 title replaced with the Crossref title (bib edit made on the author's word;
  DOI unchanged). Verified in the built PDF: the reference prints "Correlated Proportions".
- C-2/A-3 llama32card cite dropped with the serving clause; template handling handed to Chapter 4.
  C-5 llama32card now cited on the architecture sentence in place of the blog post llama32.
- C-3/A-7/A-23 verifier's combined sentence: proportionality under the bound, cite on the rationale
  clause, "adds little". C-4 l.177 scoped to the desktop-GPU roofline.
- Minors/nits applied: A-4, A-5, A-8, A-9, A-11, A-12, A-14, A-15, A-18, A-19, A-20, A-21, A-22,
  A-24, C-6, C-7, C-9, NEW-1, and the "no accelerator ... uses in practice" wording.
- Not applied, per the verifier: A-16 (whisper.cpp clause kept, cited instead), A-17 (intent
  accuracy kept: the state-of-the-art MASSIVE row uses it). C-8 and the two markers wait on the
  author's two bib entries (Raspberry Pi 5 product brief RP-008348-DS-6; Vaswani et al. 2017).
- One weak verb my own fix introduced ("shows") caught by the re-run and replaced.

Script after fixes: 0 FAIL, 8 WARN, 67 PASS. The eight WARNs: six hand-typed acronyms, all in
section or paragraph headings (convention: headings exempt); the two author markers. check_tex:
only the three cross-chapter \ref false positives. Clean build: 0 errors, 0 undefined, 0 dropped
floats, 0 overfull; 79 pages (the state-of-the-art rebuild in the other session adds pages).

Status: resolved, pending the author's two bibliography entries.
