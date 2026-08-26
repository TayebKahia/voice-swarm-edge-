# Issue 02: master-ch2

Status: resolved
Blocked by: 01
Chapter: thesis/master/ch2_related_work.tex
Script: tools/review/master_ch2.py
Report: .scratch/thesis-review/reports/master_ch2.md

## Run

```
~/miniconda3/envs/pfe_swarm/bin/python tools/review/master_ch2.py
```

## Agents

- **Citation agent** -- D5 only. Worklist: the report's citation sheet (34 citations, 16 keys) and
  "Numbers quoted from papers" (25 models, 3 SBCs, 2 runtimes, 1.5 B ceiling, 4x spread, <1%
  perplexity, >= 7 B, 1 M examples). Open each identifier; verdict per row SUPPORTS / PARTIAL /
  DOES NOT SUPPORT / COULD NOT ACCESS. `.scratch/thesis-bibliography/master-candidates.md` is a
  lead, never evidence.
- **Argument agent** -- D1, D2, D4, D6, D8, D10, D11, D12. Focus: the Gap paragraph claims four literatures
  are *silent*; that holds only for the papers cited. And the Delta credits C1 with isolating the
  grammar's contribution, which is the ablation's (C3's) doing.
- **Verifier.**

## What the script establishes (baseline: 0 FAIL, 13 WARN, 34 PASS)

- Four theme sections plus one closing Positioning with Synthesis / Gap / Delta.
- Positioning cites nothing the theme sections did not review.
- No voice-UAV literature (Table 3 gives it to the Ingénieur); no Outlines; all four models cited.

## Seeded findings

- "guarantee" used twice about the grammar (l.83, l.101) -- earned for a by-construction property?
- Acronyms by hand: LLM, CPU, GPU, GGUF, GGML, BNF, GBNF.
- The master-candidates notes flag a tension with C3's framing -- the argument agent reads it.

## Comments
### 2026-09-23 -- review round 1 (citation + argument + verifier)

Script re-baseline after the Ch1 fixes: 0 FAIL, 12 WARN, 35 PASS.

Verdict: ready after fixes. The four theme sections match the outline. The trouble is in (a) five
descriptions of papers or of llama.cpp that the sources contradict, (b) three Ch1 overclaims that
Ch2 still repeats, and (c) a Positioning section whose Gap claims silences the chapter's own
citations break. The fix is to rewrite Synthesis / Gap / Delta around the *four-way conjunction*
(sub-billion model fine-tuned to a command schema, quantised, grammar-decoded, scored on task
metrics next to its SBC throughput), not four separate silences.

Citations (24 rows): 4 DOES NOT SUPPORT, 8 PARTIAL, 12 SUPPORTS.

Verified BLOCKER/MAJOR (verifier: 17 confirmed, 7 partly, 0 refuted):

| # | Sev | Line | Finding | Verifier | Fix |
|---|---|---|---|---|---|
| 1 | BLOCKER | 179-180 | C1 "two-layer semantic validator" -- removed from Ch1 (#6 of issue 01) | CONFIRMED | Ch1 wording: schema + bounded grammar, layer 1 of three |
| 2 | BLOCKER | 185-187 | C3 "each quantisation level, on the Pi, every candidate model"; contradicts ch2:24-26 | CONFIRMED | Ch1 C3 wording (3 of 4, two levels, accuracy on workstation, timing on Pi at Q4_K_M). Source: ch3:389-391, ch4:9-11 -- NOT ch3:315-317, which is itself wrong (issue 03) |
| 3 | BLOCKER | 69-70 | "for every fine-tuned candidate model, is C3" | CONFIRMED | three quantised models; F1/validity ARE measured (surface_b.csv), only the delta table is EM-only |
| 4 | BLOCKER | 69-71, 187-190 | C3 = "the accuracy cost of quantisation ... rather than inherited" -- ch3:320-330 and ch4:212-219 say it must not be read against that literature | CONFIRMED | "accuracy cost of the deployment pipeline"; **Ch1 l.119-121 has the same error -- not fixed in issue 01** |
| 5 | BLOCKER | 9-10, 149-150 | sbc2025 "no board serves reliably above 1.5 B" (same misquote as Ch1 #3) | CONFIRMED | "reliably support up to about 1.5 B; larger models drop to a few tok/s"; benchmark, not survey |
| 6 | BLOCKER | 10-14, 150-151 | "runtime moves the bound further than the board" -- the 4x is Llamafile vs Ollama on one board (Orange Pi 5 Pro, 4 P-cores); no runtime-vs-board comparison | CONFIRMED | "the runtime alone changed throughput by up to 4x on the one board where two were compared" |
| 7 | BLOCKER | 44-46 | Q4_K_M "correction term ... more bits on the blocks error is largest in" -- it is a positional per-tensor rule (use_more_bits: attn_v/ffn_down to Q6_K), 256-weight super-blocks; no error measured | CONFIRMED | describe the actual scheme; not "more sensitive tensors" either |
| 8 | BLOCKER | 82-83 | GBNF "at a fixed per-token overhead" -- grammars/README warns of slow patterns | CONFIRMED | drop the overhead clause |
| 9 | BLOCKER | 61-64 | GPTQ "without naming a task metric" -- §4 reports LAMBADA/ARC/PIQA | CONFIRMED | "perplexity and generic zero-shot accuracy" |
| 22 | BLOCKER (raised) | 152-153 | same GPTQ misreport in Synthesis; AWQ also reports instruction/multimodal evals | CONFIRMED | fix with #9 |
| 10 | MAJOR | 147-148, 159-160 | "mature"; "have not been evaluated together" -- pairwise intersections exist (kurt2026, slmquant, tam2024, park2024) | PARTLY | "not all four together" |
| 11 | MAJOR | 67, 154, 166 | "7 B and above", "an order of magnitude larger" -- slmquant tests 135M/0.5B (Qwen2.5-0.5B!), kurtic2025 has a 1.5B | CONFIRMED | gap is task/metric/GGUF-on-SBC/grammar, not model size |
| 12 | MAJOR | 5-7, 16, 23, 162 | "surveys", "relatives", "growing body" from one cited benchmark | CONFIRMED | singular, "benchmark" |
| 13 | MAJOR | 133-135, 173-175 | MASSIVE baselines are 258-580M -- not unconstrained large models; "person reading the output" uncited | CONFIRMED | contrast = GPU, no latency/memory envelope, no grammar; drop the person clause |
| 15 | MAJOR | 127-130 | "nothing about that mapping is specific to robotics" uncited | PARTLY | soften; cross-ref Ingénieur Ch2. Do NOT import robotics papers (Table 3) |
| 16 | MAJOR | 178-182 | C1 credited with isolating the grammar -- that is the ablation (evaluation) | CONFIRMED | C1 supplies the property; the ablation measures it |
| 17 | MAJOR | 178, 182-185 | "one literature each" -- 3 contributions, 4 literatures; a dataset does not close a resource-envelope gap | CONFIRMED | explicit mapping: SBC+quant -> C3, grammar -> C1 (+ablation), SLU data -> C2 |
| 20 | MAJOR | 32-34, 50-52 | quantisation "what lets the model fit ... at all" -- RSS 0.55-1.63 GB vs 2.5 GB ceiling; 0.5B fits at f16 | CONFIRMED | quantisation is a throughput lever |
| 21 | MAJOR | 54-56 | "most reported uses" perplexity -- uncited | PARTLY | cite tools/quantize README (ppl and/or KLD) |
| 23 | MAJOR | 47-49 | AWQ salience is activation-based, protected by scaling; Q4_K_M does not "instantiate" it | CONFIRMED | "a similar intuition" at most |
| 24 | MAJOR | 42-43 | GPTQ is about one GPU, not edge | CONFIRMED | cite AWQ (on-device motivation) |
| 14 | MINOR (lowered) | 173-176 | sikorski2025 partly fills the SLU gap | PARTLY | the Ingénieur only lists it in a % comment; do not import into the Master |
| 18 | MINOR (lowered) | 96-99 | "fine-tuning has already done most of the work" is a result in Related work (ch3:102-105 repeats it) | PARTLY | cut the clause; "same model with and without" is correct (paired) |
| 19 | MINOR (lowered) | 89-94 | "closed by construction ... on any input" | PARTLY | holds: longest grammar string 90 chars <= 91 tokens < 96 cap; say "structural validity" |

MINOR/NIT (not verified): "guarantee" -> "property" (l.83, 101); no chapter intro, weak hand-off;
RQ1 never named; l.112-116 write-once bookkeeping paragraph (delete); Q8_0 is legacy, not K-quant,
"k-quant"/"K-quant" drift; "reference precision" undefined, "label-first" undefined; Danube3 is
fp16 because it failed tokenisation parity, not only by design (l.24-26); "consumed directly by a
flight controller" ignores the validator; tam2024 direction (tighter -> worse, so "looser schemas"
argues the wrong way, l.106-108); "latency floor" -> budget; three validity terms; flourishes
(l.5-6, 27-28, 61, 101, 140-141, 159-160, 162, 176); acronyms by hand; nine sentences > 50 words;
--- vs -- ; "fp16"/"FP16"; bib: spqr is ICLR 2024 (@inproceedings), stray venue comment above
kurtic2025, awq lacks eprint 2306.00978.

For issue 03: ch3:315-317 says Surface B runs on the Pi (wrong); ch3:102-105 repeats the
"fine-tuning already did most of the work" sentence.

### 2026-09-23 -- draft of the fixes (awaiting the author's approval)

The author chose "draft all + fix Ch1". Every verified BLOCKER/MAJOR and the MINOR/NIT list are
drafted in thesis/master/ch2_related_work.tex. The Positioning is rebuilt around the four-way
conjunction: Synthesis names the pairwise combinations that already exist (kurt2026, slmquant,
tam2024); Gap states what each literature leaves out of the conjunction; Delta maps C1 (property),
the ablation (run by C3's harness), C2 (data for this vocabulary) and C3 (pipeline cost, three of
four models, timing at Q4_K_M) explicitly. Added a chapter introduction that names RQ1; deleted
the l.112-116 write-once paragraph; the §2.1 heading is now "Edge language-model inference and
single-board-computer benchmarking" (no acronym in a heading). Sentences over 40 words: 9 over 50
before, none over 47 now.

Checked by hand before writing: MASSIVE Table 3a (locale-averaged intent 85.1-86.1%, slot F1
73.6-76.8%, EM 63.7-66.6%; Base models 258M/270M/580M; V100 training) and the SpQR ICLR 2024
proceedings page.

Script: 0 FAIL, 1 WARN, 45 PASS. The WARN (l.29, "three quantised + one fp16 control" vs Ch1's
"three deployment candidates plus a control") is a standing judgement prompt. Justified: Ch1
l.20-23 names the three and the control, and Ch2 l.29-32 says the same thing with the reason for
fp16. Clean build of both documents: no errors, no undefined citations (only the pending
chap:conclusion / Ingénieur chapters).

Changes outside Ch2:
- Ch1 C3 (l.119-121): "accuracy cost of quantisation ... rather than inherited" becomes "accuracy
  cost of the deployed pipeline, in which weight precision, runtime and grammar change together".
  The issue 01 review missed this; the verifier found it (finding #4).
- references.bib: spqr -> @inproceedings, ICLR 2024 (confirmed on proceedings.iclr.cc); awq gets
  eprint 2306.00978. The citation agent's "stray comment above kurtic2025" is not a finding: it
  is the qlora entry's comment.
- tools/review/lib.py: a number on a line with a PASS paper-number anchor is reported "quoted from
  a paper" instead of UNTRACED. Such numbers can never be in results/, so the WARN could never
  clear; the citation agent still verifies them.
- tools/review/master_ch2.py: anchors follow the new wording (18 paper numbers, including the
  MASSIVE figures); the argument-agent hints no longer quote stale line numbers.
- tools/review/selftest.py: the two Ch2 mutation targets moved to text that still exists. Passes.

For issue 03: ch3:331 says the method papers report "the perplexity delta"; Ch2 now says
perplexity plus generic zero-shot accuracy (GPTQ). ch3:38 "Three layers guarantee" is the same
unearned-absolute question Ch2 had. ch3:315-317 and ch3:102-105 as above.

### 2026-09-23 -- author asked for §2.2 and §2.3 to be checked claim by claim

Every factual sentence was re-checked against the primary source, not against the agents' reports.
Sources: llama.cpp at build b10863 (the local checkout is exactly the version the bib pins), the
deployed GGUF files, and the papers.

**Found and fixed in §2.2:**
- **Q4_K_M was misdescribed a second time.** "Most tensors at four bits" is false for two of the
  three quantised models. The artefacts themselves show it (GGUFReader, share of weights):
  - Qwen2.5-0.5B: Q5_0 51.0%, Q8_0 27.8%, Q6_K 10.6%, Q4_K 10.6%.
  - SmolLM2-360M: Q5_0 63.8%, Q8_0 14.4%, Q6_K 10.9%, Q4_K 10.9%.
  - Llama-3.2-1B: Q4_K 67.2%, Q6_K 32.8%.

  The cause is src/llama-quant.cpp:371-400: a tensor whose row length (ne[0]) is not a multiple
  of QK_K=256 falls back from Q4_K to Q5_0 and from Q6_K to Q8_0. Qwen's hidden size is 896 and
  SmolLM2's is 960; Llama's is 2048. Q4_K_M also raises the output tensor to Q6_K, and with it the
  token embeddings when they are tied, as Qwen's are (l.456-476). The draft left both facts out.
  The text now describes the recipe, the role/position rule and the shape fallback, each cited to
  llamacpp, and says in general terms that a model whose hidden size is not a multiple of 256
  ends up mostly at five or eight bits. No per-model numbers are given in Ch2: they are not in
  results/ yet.
- **"About a half and about a third"** was only true of the largest model. File sizes against
  fp16: Q8_0 is 53% for all three models; Q4_K_M is 40% (Qwen), 37% (SmolLM2) and 33% (Llama).
  Replaced with the exact block costs from ggml-common.h static_asserts: Q8_0 = 34 B / 32 weights
  = 8.5 bpw; Q4_K = 144 B / 256 = 4.5 bpw.
- **"Rounded to four or eight bits"** became "rounded to lower precision".
- **llama.cpp's quantize README says the loss is "usually measured"** in perplexity and/or KLD.
  The text now says "usually" and drops "on a generic corpus", which the README does not state.

**Found and fixed in §2.3:**
- **"Parsed once"** is not stated in grammars/README.md, so it was dropped. The masking description
  and the slow-sampling warning (README l.125, l.131) stay.
- **The last paragraph said the constraint literature studies "intermediate reasoning or
  open-ended generation".** park2024 evaluates code generation and structured NLP tasks, so the
  sentence was wrong. It is rewritten: park2024 shows the distortion exists, not how large it is;
  tam2024 finds even the direction task-dependent. tam2024 §4 was confirmed in the ACL PDF: JSON
  mode helped classification (DDXPlus), "stringent formats may hinder reasoning-intensive tasks
  but enhance accuracy in classification tasks". Classification is the closer of its two task
  types to intent parsing.

**Confirmed unchanged:**
- SpQR "<1% relative perplexity loss".
- GPTQ zero-shot LAMBADA/ARC/PIQA.
- kurtic2025's 1.5B model and kurt2026's 8B.
- SLMQuant including Qwen2.5-0.5B.
- AWQ's 1% activation-salient channels.
- geng2023 "without finetuning".
- willard2023: FSM index over the vocabulary for regex and CFG.
- koo2024: "provably correct", closed-form for regular and deterministic CF languages.
- park2024: distortion; NeurIPS 2024 per the arXiv comments.

Script 0 FAIL / 1 WARN (the standing prompt). Self-test passes; build clean.

**For issue 03 (Ch3) -- these matter more than anything above:**
- Ch3's quantisation procedure has to state what Q4_K_M actually is for each model, with a
  results/ artefact generated from the GGUF files; the tensor-type shares above are the data.
  Otherwise "Q4_K_M" reads as 4-bit.
- Ch4's quantisation-delta reading ("Qwen2.5-0.5B loses nothing at Q4_K_M", SmolLM2 -1.5 pp) is
  about artefacts that are mostly 5- and 8-bit for exactly those two models. Only Llama is the
  4-bit case. This may be part of why the delta is so small; Ch4/Ch5 should say so.
- The thesis never states the 96-token generation cap (eval/surface_b.py:71) or that the bounded
  grammar's longest string (90 characters, at most 91 tokens with EOS) fits under it. Ch2's
  reachability argument depends on both.

### 2026-09-23 -- author asked for §2.5 Positioning to be checked claim by claim

Each sentence was checked three ways: against the theme section it summarises, against the
source, and against Ch1's contribution wording as committed in 5bc0391.

**Fixed:**
- Synthesis: "the runtime alone can change throughput by up to four times". The 4x was measured on
  one board and is confounded with core configuration (Llamafile on 4 performance cores), and
  §2.1 already says "on the one board where both runtimes were compared". Now "on one board the
  choice of runtime changed throughput by up to four times".
- Synthesis: "the established way to shrink a model for such hardware~\cite{gptq,awq}". GPTQ is
  about one GPU, not SBC hardware (finding #24). Now matches §2.2: shrink a trained model
  (gptq), with on-device deployment among its motivations (awq).
- Synthesis: "a cost to the sampled distribution ... \cite{park2024,tam2024}". tam2024 measures
  accuracy under format restriction, not the sampled distribution. Each cost is now attributed to
  its own paper.
- Synthesis: tam2024 described as "constrained decoding with task accuracy". It studies format
  restriction (instructions, JSON mode), so it is now called "format restriction".
- Gap: "the constrained-decoding studies evaluate grammars on models not fine-tuned" is now
  scoped to "reviewed here". Confirmed per paper:
  - geng2023: "without finetuning".
  - park2024: Mistral-7B with 3 in-context examples (arXiv HTML, experimental setup).
  - tam2024: prompted API and open models.
- Gap: added the one-sentence impact the paragraph lacked: a deployment choice needs all four
  quantities measured together, on the deployed configuration.
- Delta: "Together they answer RQ1" is now "supply the measurements from which
  Chapter~\ref{chap:results} answers RQ1". Ch4 §sec:selection answers it, through the selection
  rule.

**Confirmed:**
- kurt2026 measures CPU throughput with llama.cpp K-quant and legacy formats on
  Llama-3.1-8B-Instruct (arXiv abstract).
- slmquant sub-billion; MASSIVE on V100s.
- The Delta's C1/C2/C3 match Ch1 exactly: layer-1 grammar; template-family splits; 3 of 4
  models at two levels; pipeline cost, not quantisation alone.
- Positioning cites only keys the theme sections reviewed (script PASS).

Script 0 FAIL / 1 WARN (the standing prompt). selftest.py: the Ch2 planted citation moved to the
new Synthesis sentence; passes. Build clean.

### 2026-09-23 -- resolved

The author read the draft and closed the issue. Final state: 0 FAIL, 1 WARN (the standing
three-plus-control prompt, justified above), 46 PASS; selftest passes; clean build of both
documents. §2.2, §2.3 and §2.5 were checked against primary sources claim by claim; §2.1 and §2.4
rest on the citation agent and the verifier (MASSIVE's figures in §2.4 were checked by hand).
Carried to issue 03: Q4_K_M shape fallback (needs a results/ artefact and Ch3/Ch4 wording), the
unstated 96-token cap and longest grammar string, ch3:315-317, ch3:102-105, ch3:38, ch3:331.
