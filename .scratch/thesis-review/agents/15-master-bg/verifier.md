# Issue 15 -- Master Ch2 (Background) -- verifier report

Chapter: `thesis/master/ch2_background.tex` (425 lines) as in the working tree (uncommitted edits on
top of `7830694`). Checked against `thesis/master/ch3_method.tex` (l.300-332, 415-442, 458-480,
499-503, 526-538, 560-580, 655-666), `thesis/master/ch4_results.tex` l.38-43, `thesis/references.bib`
(entries `llama32card` l.194-202, `edwards1948` l.270-279, `awq` l.455-467), `train/configs/*.yaml`,
`tools/review/master_bg.py` and `tools/review/lib.py`, and the primary sources opened on 2026-09-25:
`transformers` `modeling_llama.py` and `modeling_qwen2.py` at `main` (raw GitHub), the four
`config.json` files on Hugging Face (Qwen/Qwen2.5-0.5B-Instruct, HuggingFaceTB/SmolLM2-360M-Instruct,
h2oai/h2o-danube3-500m-chat, unsloth/Llama-3.2-1B-Instruct as an ungated mirror of the Meta config),
the four model cards, the Crossref record for 10.1007/BF02289261, and the AWQ paper (arXiv 2306.00978
v6, PDF downloaded to the scratchpad and read with `pdftotext`; abs page and HTML rendering as
cross-checks). Nothing edited except this file; no build run.

## 1. Summary

| ID | Sev (reviewer) | Verdict | Sev (verified) | Evidence | Fix judgement / corrected fix |
|---|---|---|---|---|---|
| A-1 (gated FFN, l.48-50) | MAJOR | CONFIRMED | MAJOR (definitional error; no number or result depends on it, so not BLOCKER) | `LlamaMLP.forward` and `Qwen2MLP.forward` both read `down_proj(act_fn(gate_proj(x)) * up_proj(x))`. All four `config.json`: `hidden_act: "silu"`; architectures `LlamaForCausalLM` (SmolLM2, Danube3, Llama 3.2) and `Qwen2ForCausalLM` (Qwen2.5). Qwen card: "Architecture: transformers with RoPE, SwiGLU, RMSNorm ..."; Danube3 card prints `LlamaMLP((gate_proj)... (up_proj)... (down_proj)... (act_fn): SiLU())`. The chapter's $\sigma(g \odot u)$ is a different function from $\sigma(g) \odot u$ | Reviewer's wording correct. No script anchor on l.44-52. Optional tightening in §2 |
| A-2 (reference-transcript protocol, l.386-388) | MAJOR | CONFIRMED | MAJOR | ch3:464-469 "Protocol ... take reference text as input"; ch3:532-535 the WER-ceiling justification; ch4:15 restates it; the chapter's own charter l.12-14 sends "every design decision" to Chapter 4; l.359-361 already hands operational definitions to `sec:definitions-of-record`. The sentence says what *this document* does and why ("therefore") | Reviewer's wording correct and anchor-safe (`\ref{sec:definitions-of-record}` at l.361 keeps the script's `foundations` check; no hedge/absolute/weak-verb hit; `Section~\ref` spacing right). Slightly shorter alternative in §2 |
| C-1 (edwards1948 title) | MAJOR | CONFIRMED | MAJOR | Crossref 10.1007/BF02289261: title "Note on the "Correction for Continuity" in Testing the Significance of the Difference between Correlated Proportions", Edwards, Psychometrika 13(3):185-187, Sept 1948; resource URL cambridge.org S0033312300045452. Bib l.271 carries a different title; author, journal, volume, issue, pages, year, DOI all match. The chapter sentence (l.395-397) is supported by the real paper | Fix correct. Exact bib line given in §2. The pre-review's bib table is generated, not anchored, so nothing in `master_bg.py` breaks |
| C-2 (llama32card for four models, l.84-85) | MAJOR | CONFIRMED | MAJOR | `grep huggingface.co references.bib` hits only l.199 (Llama card) and l.380 (a dataset); no Qwen, SmolLM2 or Danube3 card entry. Each of the three cards publishes a template: SmolLM2 `tokenizer.apply_chat_template(messages, tokenize=False)`; Qwen2.5 `tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)`; Danube3 "We use the HF Tokenizer chat template" with `<\|prompt\|>...</s><\|answer\|>`. The Llama card mentions no other family | Prefer the **argument agent's finding-3 wording**, which removes the citation from this chapter and resolves C-2 and A-3 together; `llama32card` stays cited at ch3:437 so no bib entry is orphaned, and `lib.py` only FAILs on dangling keys. The citation agent's option (b) is also correct if the sentence is kept; option (a) adds three entries the author must verify for one textbook sentence and is not worth it |
| C-3 (awq for "lever of choice ... on a CPU", l.244-246; PARTIAL at l.177) | MAJOR | CONFIRMED | MAJOR | AWQ §4.1: roofline on "the 4090 GPU ... 165 TFLOPS ... 1TB/s ... memory bounded on 4090 GPUs"; Fig. 3 caption "Bottleneck analysis for Llama-2-7B on NVIDIA RTX 4090 ... weight-only quantization is more effective for on-device LLMs". CPU content is TinyChat engineering only: "On CPUs, we lower the entire computation graph to C++"; SIMD packing "for ARM CPUs with 128-bit SIMD registers offering up to 1.2x speedup"; "Raspberry Pi 4B, achieving 0.7 tokens/s for 7B models"; Fig. 1 lists "Raspberry Pi (ARM CPU)" as a target. No CPU bandwidth analysis, no "lever of choice" statement. AWQ itself notes dequantisation "remains expensive ... particularly costly on CPUs with SIMD architecture", which is the argument agent's finding-7 point | Both reviewers' fixes are sound; take the argument agent's finding-7 sentence with `~\cite{awq}` on the rationale clause (wording in §2). AWQ supports that clause verbatim ("weight-only quantization leads to a lower bit width for weights (and thus higher theoretical performance upper bound)"). l.177 may keep its cite (PARTIAL, mechanism supported). No anchor on l.240-248 |

No BLOCKER. All five MAJORs stand at MAJOR. Two fix conflicts between the reports are resolved in §3
(A-16 vs C-7) and above (C-2 vs A-3).

## 2. Reasoning per finding

### A-1 -- gated feed-forward block -- CONFIRMED, MAJOR

Attempted disproof 1: the sentence could be a loose but acceptable paraphrase of the same block.
It fails. The chapter says the two expansions' *product* is passed through the non-linearity,
$\mathrm{down}(\sigma(\mathrm{gate}(x) \odot \mathrm{up}(x)))$. The block in every model of
`tab:bg-models` is $\mathrm{down}(\sigma(\mathrm{gate}(x)) \odot \mathrm{up}(x))$:
`modeling_llama.py` `LlamaMLP.forward`: `self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x))`;
`modeling_qwen2.py` `Qwen2MLP.forward`: identical line. These are different functions, not different
descriptions of one function (SiLU is not multiplicative).

Attempted disproof 2: one of the four might use a block where the description holds. It fails.
The four `config.json` files give `hidden_act: "silu"` with `LlamaForCausalLM` (SmolLM2-360M-Instruct,
h2o-danube3-500m-chat, Llama-3.2-1B-Instruct) or `Qwen2ForCausalLM` (Qwen2.5-0.5B-Instruct), so all
four run one of the two `forward` lines above. The Qwen card names it ("SwiGLU"); the Danube3 card
prints the module tree with `act_fn: SiLU()` inside `LlamaMLP`.

Consequence for the reader: `tab:lora` (ch3:310) and every `train/configs/*.yaml` (`target_modules`
l.19/99) name exactly these seven modules, so a jury member in the sub-field reads l.48-50 as the
definition of what the adapters attach to. The error changes no number, so MAJOR, not BLOCKER.

The reviewer's replacement is correct. If the author wants the activation named, all four models
share it, and the bracket is supported by the configs rather than by a bib entry, so keep it generic
or write "a non-linearity (the sigmoid-weighted linear unit in every model of
Table~\ref{tab:bg-models})". Neither version touches a script anchor: `master_bg.py` has no
`r.number`/`text_claim` on l.36-62.

### A-2 -- reference-transcript protocol -- CONFIRMED, MAJOR

Attempted disproof 1: the chapter names "the models compared in this work" at l.36 and l.84, so
naming *what* is compared is allowed and this is more of the same. It fails. l.387-388 does not name
an object; it states the input every parser metric takes ("takes reference transcripts as input")
and gives the reason ("A WER carries into the parser as noise ... therefore"). That is the Protocol
paragraph of ch3:464-469 and the justification of ch3:532-535 ("would impose a shared WER ceiling
on every model") in compressed form, and ch4:15 states it a third time. The chapter's own opening
(l.12-14) promises that "every design decision made in this work is stated and justified in
Chapter 4", and l.359-361 already defers operational definitions to `sec:definitions-of-record`.

Attempted disproof 2: the script's `foundations` regexes passed, so the chapter is clean by the
project's own test. It fails: the regexes list deployment vocabulary ("is deployed", "selected
configuration", ...) and result formats; a protocol input choice is outside their reach, which is
exactly what the issue hands to the argument agent ("no design decision").

The reviewer's fix keeps the generic fact and hands the choice over; it is anchor-safe (l.386-388
carry no anchor; `\ref{sec:definitions-of-record}` remains at l.361 in any case) and contains no
absolute, marketing or weak verb. A shorter form that avoids a second `\ref` to the same section
three paragraphs after l.361:

```
A \gls{wer} carries into the parser as noise in its input, so a parser scored on recognised text is
scored on the recogniser as well; which input each metric of this document takes is fixed with its
definition of record.
```

Either is fine. Note that the first half of the paragraph (the WER definition, l.384-386) is the
subject of A-10, which should be fixed in the same edit.

### C-1 -- edwards1948 bib title -- CONFIRMED, MAJOR

Independent check: `api.crossref.org/works/10.1007/BF02289261` returns title "Note on the
"Correction for Continuity" in Testing the Significance of the Difference between Correlated
Proportions", author Allen L. Edwards (University of Washington), Psychometrika 13(3), pp. 185-187,
issued September 1948, resource URL `cambridge.org/core/product/identifier/S0033312300045452`.
`references.bib` l.271 reads "Note on the ``Correction for Continuity'' in Any $\chi^2$ for
Between-Group Differences"; l.272-278 match Crossref field for field. `git log -S` shows the entry
arrived in `4445be5`, so it has been wrong since it was added. The printed reference would be wrong
while its DOI resolves to the right paper; the claim at l.395-397 (continuity correction for the
McNemar chi-square) is what the real paper is about, so the citation supports its sentence and this
is a record error, MAJOR under D5e, not a BLOCKER.

Corrected bib line (l.271):

```
  title        = {Note on the ``Correction for Continuity'' in Testing the Significance of the Difference between Correlated Proportions},
```

`master_bg.py` prints the bib title into the pre-review's key table but anchors nothing on it.

### C-2 -- one model card for four models -- CONFIRMED, MAJOR

Attempted disproof: the sentence might be read as citing an *example* card. It fails: the sentence
is universal ("Every model ... its model card publishes") and the citation sits at its end with no
"for instance". `references.bib` contains one model card (`llama32card`, l.194-202) and no entry
for the other three (grep of `huggingface.co`, `smollm2`, `qwen`, `danube` in the bib: only the
technical reports and the Common Voice dataset). Each of the three missing cards does publish a
template (quotes in the summary table), so the *claim* is true and the *citation* covers one
quarter of it: PARTIAL, MAJOR.

Fix. The argument agent's finding 3 (MINOR) independently says the second half of the sentence is a
serving decision that ch3:419-431 makes and verifies. Both findings are right and one edit settles
both: the argument agent's wording, which drops the citation from this chapter. Checked:
`llama32card` is still cited at ch3:437, so the entry is not orphaned; `lib.py` `common()` FAILs
only on a key absent from the bib, never on a cite count; the wording uses `Chapter~\ref{chap:method}`
with the tie, which the l.96 spacing check requires; and "instruct variant" covers Danube3's
`-chat` suffix because l.79-80 defines instruct and chat as one thing. If the author prefers to keep
the sentence, the citation agent's option (b) is correct and minimal: "(for Llama~3.2,
\cite{llama32card})". Option (a), three new bib entries, is the heavy route for a textbook sentence
and is not recommended.

### C-3 -- AWQ for a CPU claim -- CONFIRMED, MAJOR

Attempted disproof 1: AWQ is an "on-device" paper and lists a Raspberry Pi in Figure 1, so its
conclusion covers CPUs. It fails. The bandwidth argument (§4.1, Fig. 3) is stated for one device
and says so three times: "roofline analysis ... The 4090 GPU has a peak computation throughput of
165 TFLOPS and a memory bandwidth of 1TB/s ... memory bounded on 4090 GPUs". The CPU material is
implementation (graph lowered to C++; NEON packing worth "up to 1.2x"; Pi 4B at 0.7 tok/s) with no
roofline for any CPU. Nothing in the paper says weight-only quantisation is the "lever of choice"
for throughput on a CPU; the closest sentence, "weight-only quantization is more effective for
on-device LLMs" (Fig. 3 caption), is derived from the 4090 numbers.

Attempted disproof 2: the mechanism is textbook and the citation is decorative. Partly true, and it
is why the fix is a move rather than a deletion: AWQ does support the rationale clause verbatim
("weight-only quantization leads to a lower bit width for weights (and thus higher theoretical
performance upper bound)" and "Quantizing the model weights to 4 bit integers will approximately
increase the arithmetic intensity to 4 FLOPs/Byte"). It also supports the argument agent's finding-7
qualification: "dequantizing a single 4-bit weight involves 1 shift, 1 bitwise AND, and 1 FMA ...
particularly costly on CPUs with SIMD architecture". So the proportionality is an upper bound on a
CPU, by AWQ's own account.

Combined corrected sentence for l.244-246 (the argument agent's, with the cite placed):

```
First, under that bound a smaller model or a lower-precision format decodes faster in proportion
to the bytes it saves, which is the rationale for weight-only quantisation as a means to decode
throughput~\cite{awq}; how closely a given processor approaches the bound, given the arithmetic its
low-bit kernels add, is a matter of measurement.
```

Checked against `lib.py`: no absolute, marketing or weak verb; no number, so no `foundations` hit;
`~\cite`. The l.177 occurrence (C-4, MINOR) can stay as is: the mechanism it carries is the one AWQ
argues, and the sentence points forward to `sec:bg-edge` where the hardware condition is stated.

## 3. Reviewer findings I reject, downgrade, or flag as conflicting

- **A-16 (D6a, delete "served by a C/C++ port of the same kind as the language-model runtime",
  l.327-328) -- reject; conflicts with C-7.** The two reports propose opposite edits to one clause:
  A-16 deletes it, C-7 adds `~\cite{whispercpp}` to it. prd.md Table 3 (l.210) gives the Ingenieur
  ownership of the speech pipeline's *exposition*; the Master's Method already names `whisper.cpp`
  with its citation at ch3:197 and ch3:500, and ch4:28 cites it again, so the runtime is Master
  material by the Master's own usage. The clause is eight words inside the one sentence Table 3
  allows and names a kind of tool; it explains nothing about the pipeline. Keep it and apply C-7.
- **A-18 (NIT, "expand to itself without limit") -- style, not a rule.** The chapter's phrase is a
  correct informal statement of "no unbounded recursion" for a reader who has just been told GBNF
  offers *bounded* repetition (l.300-301); the reviewer's "no non-terminal can derive a string that
  contains itself" is the same condition in formal words. Either is acceptable.
- **A-8 (MINOR, greedy decoding deterministic) -- downgrade to optional NIT.** "Greedy decoding ...
  is deterministic" is the textbook property of the decoding rule (argmax of a fixed distribution).
  ch3:466-467 adds "one sequence at a time" because batched arithmetic can change the logits, which
  is an implementation fact about floating point, not a different meaning of the term. The reviewer's
  qualifier is harmless if added; it is not a disagreement between chapters.
- **A-14 (MINOR, "how much less confident") -- half right.** For perplexity the gloss is the standard
  one (exp of mean NLL of the true next token is exactly a measure of how much probability the model
  gives the right answer); for KL it is wrong, since KL is a divergence between two distributions.
  The reviewer's replacement is fine; the note is that only the KL half needed it.
- **A-6 (MINOR, "nearly all") -- confirmed, and the UNVERIFIED item is now verified.** From the
  fetched configs (vocab x hidden, counted twice where untied): Qwen2.5-0.5B 151,936 x 896 = 136 M of
  494 M (27.6%, tied); SmolLM2-360M 49,152 x 960 = 47 M of 362 M (13.0%, tied); Llama-3.2-1B
  128,256 x 2,048 = 263 M of 1,236 M (21.3%, tied); Danube3-500M 32,000 x 1,536 x 2 = 98 M of 514 M
  (19.1%, `tie_word_embeddings: false`). "Most" is right; "nearly all" is not.
- **A-17 (NIT, "intent accuracy" unused)** -- one correction to the evidence: the term does appear
  once more, in the state-of-the-art table (ch3_state_of_the_art.tex:264, MASSIVE's reported
  "Intent accuracy 85.1--86.1\%"). That is a reason to *keep* the one-sentence definition, since a
  reader meets the term in Chapter 3. Reject the deletion; no edit needed.
- **A-24 (NIT, "and it is reported with both")** -- accept the wording, but it is a style choice: the
  sentence reads as a norm of the field rather than a rule of this work, and the replacement
  ("interpretable only when both are reported with it") says the same thing. Low priority.
- All other findings in both reports (A-3, 4, 5, 7, 9, 10, 11, 12, 13, 15, 19-23; C-4, 5, 6, 8, 9, 10)
  are correct as stated; A-9 and A-10 were checked against `tab:metrics` (ch3:570 counts `hover`
  as a false command; ch3:574 defines corpus WER as summed edits over total reference words) and A-13
  against ch3:575 and ch4:41 (bootstrap interval reported, never defined in the Background).

## 4. NEW items

No new BLOCKER or MAJOR found while verifying. One observation below the bar, recorded so it is
not lost:

- **NEW-1 (NIT, l.81-83).** The chat-template definition says the template "delimits a system turn,
  the user's turn and the assistant's reply". The Danube3 card's template is
  `<|prompt|>...</s><|answer|>` with no system role, which is why the Method folds its system prompt
  into the user turn (ch3:379 and the Ch6 verifier's MAJOR-5 note). As a generic definition the
  sentence is fine; "a system turn where the template has one" would make it true of all four models
  in `tab:bg-models`. Not a finding against the chapter's correctness.

## 5. Script-anchor impact (`tools/review/master_bg.py`)

| Fix | Anchor affected | Action |
|---|---|---|
| A-1 (l.48-50) | none (no `r.number`/`text_claim` in `sec:bg-lm` before l.87) | none |
| A-2 (l.386-388) | none; `foundations` check needs `\ref{sec:definitions-of-record}` somewhere in the chapter, kept at l.361 regardless of which wording is taken | none |
| C-1 (bib title) | none; the bib table in the report is generated | none |
| C-2 / A-3 (l.84-85) | none; `lib.py` `common()` only FAILs on a key absent from the bib. `llama32card` remains cited at ch3:437 | none |
| C-3 / A-7 (l.244-246) | none; the nearest anchors are `against 512 for` (l.168) and the `paper_numbers` list at l.198-205 | none |

All proposed wording was checked against `ABSOLUTES`, `MARKETING` and `WEAK_VERBS` in `lib.py`
l.39-43 and against the `foundations` regexes in `master_bg.py` l.48-55; none matches, and no number
is added to the chapter.
