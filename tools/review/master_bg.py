#!/usr/bin/env python3
"""Pre-review checks for Master Ch2 (Background). See tools/review/lib.py.

The Background chapter (added 25 Sep, prd.md §3.1) states foundations only: textbook definitions
at the level a jury member outside the sub-field needs before the state of the art. It reports no
result, makes no design decision and takes no position on the literature. So, beyond the common
checks, the script tests three things: the chapter's shape against prd.md §3.1 item 2; that the
three passages moved here from the old Chapters 2 and 3 (the Q8_0/Q4_K_M construction, the GBNF
mechanism, the LoRA/QLoRA description) are stated once in the document; and that nothing in it is
a result or a decision (no metric values, no throughput figures, no "selected configuration").
The model table is recomputed from results/table33_iso_parameter.md. What the script cannot judge
-- whether each textbook definition is right and each paper supports its sentence -- is the
agents' job; the MANUAL sheets at the end are their worklists.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import MASTER, RESULTS, Chapter, Review, md_table, outline_check  # noqa: E402

r = Review("master_bg", "master", MASTER[1], [MASTER[0], *MASTER[2:]])  # Background, Chapter 2 since 25 Sep
r.common()
text = r.ch.text
prose = r.ch.prose()

# -- Shape: prd.md §3.1 item 2, seven foundation sections in the order the outline lists them ----
outline_check(r, 1, {"language models and the transformer decoder": r"language models",
                     "fine-tuning and LoRA": r"low-rank|lora",
                     "post-training quantisation and the GGUF formats": r"quantisation",
                     "CPU inference on a single-board computer": r"single-board",
                     "grammar-constrained decoding and GBNF": r"grammar-constrained",
                     "the intent-and-slot formulation": r"intents and slots",
                     "the metrics of record and the paired test": r"metrics"})
titles = [t for lvl, t, _ in r.ch.sections() if lvl == "section"]
r.expect("outline", titles[-1:] == ["Conclusion"], f"closes with a Conclusion section (last section: {titles[-1:]})")
labels = re.findall(r"\\label\{(sec:bg-[^}]*)\}", text)
want = ["sec:bg-lm", "sec:bg-lora", "sec:bg-quant", "sec:bg-edge", "sec:bg-gbnf", "sec:bg-slu", "sec:bg-metrics",
        "sec:bg-conclusion"]
r.expect("outline", labels == want, f"section labels in outline order: {labels}")
r.expect("label", "\\label{chap:background}" in text, "carries \\label{chap:background}")
intro = text[: text.find("\\section{")]
for chap in ("chap:state-of-the-art", "chap:method"):
    r.expect("outline", f"\\ref{{{chap}}}" in intro, f"the opening hands the literature/decisions to \\ref{{{chap}}}")

# -- Foundations only: no result, no decision, no position (prd.md §3.1 item 2) -----------------
for pat, what in ((r"\\ref\{chap:(results|discussion|conclusion)\}", "a forward reference to a results chapter"),
                  (r"\\ref\{(tab|fig):(?!bg-)", "a table or figure of another chapter"),
                  (r"\b\d+(?:\.\d+)?~tok/s\b", "a throughput figure"),
                  (r"\b0\.\d{3}\b", "a metric value (0.xxx)"),
                  (r"\b\d+(?:\.\d+)?~pp\b", "a percentage-point difference"),
                  (r"\bp\s*[=<>]\s*\d", "a p-value"),
                  (r"\b(selected configuration|is deployed|was selected|selection rule deploys|deploys )", "a deployment decision"),
                  (r"\b(Exp-\d|RQ\d|NFR-\d+|FR-\d+|Surface [AB]|Branch [AB])\b", "a project code")):
    hits = [(m.group(), r.ch.line_of(m.start())) for m in re.finditer(pat, prose)]
    r.expect("foundations", not hits, f"no {what} in the Background"
             if not hits else f"{what} in the Background: {hits[:3]} -- results and decisions belong to Chapters 4-6",
             hits[0][1] if hits else None)
r.expect("foundations", "\\ref{sec:definitions-of-record}" in text,
         "metric definitions are handed to Chapter 4's definitions of record rather than restated")

# -- Write-once inside the document: the moved passages are stated here and nowhere else --------
others = {rel: Chapter.load("master", rel) for rel in (MASTER[2], MASTER[3])}
moved = [("stores weights in super-blocks of 256", "Q4_K_M construction (from the old Ch2)"),
         ("blocks of 32 at eight bits with one scale per block", "Q8_0 construction (from the old Ch2)"),
         ("sets the logits of every other", "token-masking mechanism (new statement of the old Ch2 paragraph)"),
         ("freezing the pretrained weight matrices", "LoRA description (from the old Ch3 `Adaptation method`)"),
         ("quantising the frozen base weights to four bits", "QLoRA description (from the old Ch3)")]
for needle, what in moved:
    here = r.ch.find(needle)
    r.expect("write-once", bool(here), f"{what}: stated in the Background (`{needle}`)", here[0] if here else None)
    for rel, ch in others.items():
        dup = ch.find(needle)
        r.expect("write-once", not dup, f"{what}: not repeated in {rel}"
                 if not dup else f"{what}: also in {rel} l.{dup[0]} -- state once, cross-reference (SKILL §2)")
for needle, rel in (("Section~\\ref{sec:bg-quant}", MASTER[2]), ("Section~\\ref{sec:bg-gbnf}", MASTER[2]),
                    ("Section~\\ref{sec:bg-lora}", MASTER[3])):
    r.expect("write-once", needle in others[rel].text, f"{rel} points at `{needle}` where its passage used to be")

# -- Numbers that are arithmetic or the project's own, recomputed ---------------------------------
r.number("16 = 144$ bits", 32 * 4 + 16, "32 weights x 4 bits + one 16-bit scale", nth=1)
r.number("= 144$ bits, or 4.5~bits per", 144 / 32, "144 bits / 32 weights", nth=1)
r.number("against 512 for", 32 * 16, "32 weights x 16 bits")
params = {row["Model"].strip("`"): float(row["Params"].replace(",", "").split()[0])
          for row in md_table(RESULTS / "table33_iso_parameter.md", "Model")}
r.number("Hugging Face & 362~M", params["smollm2-360m-instruct"], "results/table33_iso_parameter.md Params")
r.number("Alibaba Qwen team & 494~M", params["qwen2.5-0.5b-instruct"], "results/table33_iso_parameter.md Params")
r.number("H2O.ai & 514~M", params["h2o-danube3-500m-chat"], "results/table33_iso_parameter.md Params")
r.number("Meta & 1{,}236~M", params["llama-3.2-1b-instruct"], "results/table33_iso_parameter.md Params")
r.text_claim("claim", "between a third of a billion and\none and a quarter billion parameters",
             round(min(params.values())) == 362 and round(max(params.values()) / 1000, 2) == 1.24,
             "'a third of a billion to one and a quarter billion' brackets 362 M .. 1,236 M")
r.text_claim("claim", "the released checkpoints, rounded to the nearest million",
             all(v == round(v) for v in params.values()), "table33 counts are whole millions")

# -- Numbers that belong to a cited paper or tool: the citation agent's worklist ------------------
paper_numbers = [("blocks of 32", "llamacpp"), ("super-blocks of 256", "llamacpp"), ("8.5~bits per weight in\nall", "llamacpp"),
                 ("4.5~bits per weight at the four-bit level", "llamacpp"), ("to six\nbits", "llamacpp"),
                 ("not a multiple of 256", "llamacpp"), ("five bits in place of four and eight in place of six", "llamacpp"),
                 ("to four bits during training", "qlora"), ("adapters\non every linear projection", "qlora"),
                 ("a million utterances in 51", "massive"), ("one of 60 intents", "massive"), ("55 slot types", "massive")]
rows = ["| line | claim | must be found in |", "|---|---|---|"]
for anchor, key in paper_numbers:
    where = r.ch.find(anchor)
    r.expect("paper-number", bool(where), f"anchor `{anchor}` present", where[0] if where else None)
    if where:
        rows.append(f"| {where[0]} | {anchor} | {key} (primary source, not the candidate notes) |")
r.manual.append("### Numbers quoted from papers or tool documentation (citation agent: find each)\n\n" + "\n".join(rows))

# -- Definitions the argument agent must check against a textbook or the primary source ----------
defs = [("sec:bg-lm", "autoregressive factorisation; prefill vs decode; greedy decoding is deterministic; the seven "
                      "projections of a gated (Llama-style) block and their names; causal mask; KV cache cost"),
        ("sec:bg-lm", "subword tokenisation; two implementations of one vocabulary must segment alike; chat templates "
                      "are part of the training distribution"),
        ("sec:bg-lora", "LoRA: W' = W + (alpha/r) B A, r(d+k) trainable parameters per projection, merge at inference "
                        "at no cost (Hu et al.); QLoRA's 4-bit frozen base and its all-linear-layers finding"),
        ("sec:bg-lora", "completion-only masking; AdamW = decoupled weight decay; loss vs task metric for checkpoint choice"),
        ("sec:bg-quant", "w ~ s*q block quantisation; PTQ vs QAT; weight-only rationale; GPTQ / AWQ / SpQR one-line "
                         "descriptions; perplexity = exp(mean NLL); KL divergence as a cost metric"),
        ("sec:bg-quant", "GGUF holds tensors + tokeniser + chat template; Q8_0 and Q4_K_M as described; K-quant "
                         "fallback rule; 'no calibration data' for the K-quants"),
        ("sec:bg-edge", "Raspberry Pi 5 designations (CHECK marker); llama.cpp = C/C++ on ggml, mmap, per-format "
                        "kernels, thread pinning, prompt cache; decode is memory-bound at batch 1, prefill is not; "
                        "throttling and the governor; p50/p95; peak resident memory"),
        ("sec:bg-gbnf", "CFG / BNF definitions; bounded grammar => finite language; token masking with logits set to "
                        "-inf; character-level admissibility and automaton constructions (Willard & Louf; Koo et al.); "
                        "GBNF adds character classes and bounded repetition; masking redistributes probability mass"),
        ("sec:bg-slu", "pipeline order; Whisper = encoder-decoder, weakly supervised; semantic frame, intent + slots; "
                       "joint vs separate (Qin et al.); MASSIVE figures; generative formulation; abstention"),
        ("sec:bg-metrics", "EM; precision/recall/F1; macro vs micro; slot F1 over (key,value) pairs; schema validity; "
                           "false-command and safe-failure denominators; WER; McNemar on discordant pairs, exact vs "
                           "continuity-corrected chi-square (Edwards 1948); Bonferroni (Dunn 1961); Pareto dominance")]
r.manual.append("### Definitions to verify (argument agent: each must be textbook-correct and consistent with the "
                "operational definition in Chapter 4's tab:metrics)\n\n| section | claims |\n|---|---|\n"
                + "\n".join(f"| {s} | {c} |" for s, c in defs))
r.manual.append("### For the argument agent\n\n- prd.md §3.1 item 2: foundations only. Any sentence that states what "
                "*this work chose* belongs in Chapter 4; any sentence that states what *the literature has measured* "
                "belongs in Chapter 3. List each.\n- Level: a jury member outside the sub-field. List any definition "
                "that assumes what it should define, and any that is longer than the document needs.\n- Consistency: "
                "the metric definitions here are generic; Chapter 4's tab:metrics is the definition of record. A "
                "difference in meaning (not in precision) between the two is a finding.\n- The two visible markers "
                "(\\TODO on the transformer citation, \\CHECK on the Pi 5 designations) are known; do not re-report "
                "them, but do check the claims they sit on.")
sys.exit(r.finish())
