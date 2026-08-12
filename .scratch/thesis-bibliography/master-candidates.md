# Master's thesis -- candidate references for Chapter 2 (gaps 1 and 2)

Compiled 2026-09-22. This file covers two under-cited sections of `thesis/master/ch2_related_work.tex`:
"Constrained decoding" and "Quantisation", each of which currently cites only the llama.cpp
repository. Every entry below is an **UNVERIFIED CANDIDATE**: the author must open the listed
primary page, re-read the author list, title and venue, and confirm the claim it is being asked to
carry before adding anything to `thesis/references.bib`. Nothing here has been written into
`thesis/`. Read the "Notes for the author" section at the bottom before using GAP 2 --- part of it
contradicts the current framing of Contribution C3.

---

## GAP 1 --- Grammar-constrained / structured decoding

Ordered by how load-bearing each is for the argument in `\section{Constrained decoding}`.

### Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning
- Authors (as shown on page): Saibo Geng, Martin Josifoski, Maxime Peyrard, Robert West
- Venue / year: EMNLP 2023 Main Conference (arXiv listing states "Accepted at EMNLP 2023 Main Conference")
- Identifier: arXiv:2305.13971
- Page fetched: https://arxiv.org/abs/2305.13971
- Serves: Master ch2 section "Constrained decoding"
- Supports the claim: that grammar-constrained decoding is an established research technique with a
  formal guarantee ("the output follows a given structure"), not merely a feature of one runtime ---
  this is the single most important replacement for the bare `\cite{llamacpp}` in the section's
  opening sentence.

### Efficient Guided Generation for Large Language Models
- Authors (as shown on page): Brandon T. Willard, Rémi Louf
- Venue / year: arXiv preprint, 2023 (v1 19 Jul 2023, last revised 19 Aug 2023); no journal-ref listed
- Identifier: arXiv:2307.09702
- Page fetched: https://arxiv.org/abs/2307.09702
- Serves: Master ch2 section "Constrained decoding"
- Supports the claim: that decoding under a regular expression or context-free grammar can be
  reformulated as transitions of a finite-state machine with an index over the vocabulary, adding
  "little overhead" per token --- backs the thesis's phrase "at a fixed per-token overhead".

### PICARD: Parsing Incrementally for Constrained Auto-Regressive Decoding from Language Models
- Authors (as shown on page): Torsten Scholak, Nathan Schucher, Dzmitry Bahdanau
- Venue / year: Proceedings of EMNLP 2021, pages 9895--9901
- Identifier: doi:10.18653/v1/2021.emnlp-main.779
- Page fetched: https://aclanthology.org/2021.emnlp-main.779/
- Serves: Master ch2 section "Constrained decoding"
- Supports the claim: that rejecting inadmissible tokens *at each decoding step* (rather than
  filtering complete sequences afterwards) is the established mechanism --- directly backs the
  thesis's "the grammar acts inside the sampling loop ... rather than after a full sequence has
  already been generated".

### Grammar-Aligned Decoding
- Authors (as shown on page): Kanghee Park, Jiayu Wang, Taylor Berg-Kirkpatrick, Nadia Polikarpova, Loris D'Antoni
- Venue / year: NeurIPS 2024 (arXiv listing states "Accepted to NeurIPS 2024")
- Identifier: arXiv:2405.21047
- Page fetched: https://arxiv.org/abs/2405.21047
- Serves: Master ch2 section "Constrained decoding"
- Supports the claim: this is the *cost* citation the section currently lacks --- GCD "distorts the
  LLM's distribution", so outputs are grammatical but no longer weighted by the model's own
  conditional probabilities; it justifies running the grammar ablation rather than assuming the
  grammar is free.

### Guiding LLMs The Right Way: Fast, Non-Invasive Constrained Generation
- Authors (as shown on page): Luca Beurer-Kellner, Marc Fischer, Martin Vechev
- Venue / year: Proceedings of the 41st International Conference on Machine Learning (ICML), PMLR 235, pages 3658--3673, 2024
- Identifier: PMLR v235 (page URL below); arXiv:2403.06988 per search results (arXiv page NOT fetched)
- Page fetched: https://proceedings.mlr.press/v235/beurer-kellner24a.html
- Serves: Master ch2 section "Constrained decoding"
- Supports the claim: that constrained decoding methods "incur performance overhead" and can
  "impair task accuracy" when the constraint is not aligned with the model's subword vocabulary ---
  a second, independent cost/correctness citation, and the one that shows overhead is an
  implementation property rather than an inherent one.

### XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models
- Authors (as shown on page): Yixin Dong, Charlie F. Ruan, Yaxing Cai, Ruihang Lai, Ziyi Xu, Yilong Zhao, Tianqi Chen
- Venue / year: MLSys '25 (per arXiv comments field); arXiv submission 2024
- Identifier: arXiv:2411.15100
- Page fetched: https://arxiv.org/abs/2411.15100
- Serves: Master ch2 section "Constrained decoding"
- Supports the claim: quantifies where the per-token cost of a CFG mask actually comes from
  (walking stack states over the whole vocabulary at runtime) and that it can be driven to
  "near-zero overhead" --- useful precisely because the thesis runs on a throughput-bound
  Raspberry Pi 5 and asserts a "fixed per-token overhead".

### Let Me Speak Freely? A Study On The Impact Of Format Restrictions On Large Language Model Performance.
- Authors (as shown on page): Zhi Rui Tam, Cheng-Kuang Wu, Yi-Lin Tsai, Chieh-Yen Lin, Hung-yi Lee, Yun-Nung Chen
- Venue / year: Proceedings of EMNLP 2024: Industry Track, pages 1218--1236
- Identifier: doi:10.18653/v1/2024.emnlp-industry.91 (also arXiv:2408.02442)
- Page fetched: https://aclanthology.org/2024.emnlp-industry.91/ and https://arxiv.org/abs/2408.02442
- Serves: Master ch2 section "Constrained decoding"
- Supports the claim: that structural constraint is not accuracy-neutral --- "a significant decline
  in LLMs' reasoning abilities under format restrictions", worsening with stricter constraints.
  This is the empirical motivation for the grammar ablation the thesis promises in ch5, and it is
  the paper a reviewer is most likely to raise against an unqualified "the grammar costs nothing"
  reading of the section.

### Automata-based constraints for language model decoding
- Authors (as shown on page): Terry Koo, Frederick Liu, Luheng He
- Venue / year: COLM 2024 (arXiv comments field: "COLM 2024 Camera-ready")
- Identifier: arXiv:2407.08103
- Page fetched: https://arxiv.org/abs/2407.08103
- Serves: Master ch2 section "Constrained decoding"
- Supports the claim: gives the correctness half of the argument --- a closed-form automata
  construction for regular and deterministic context-free languages that is "provably correct",
  backing the thesis's "the question is closed by construction". Also explicitly motivates
  constraints by the fact that tuning "does not guarantee conformance, especially with smaller
  LMs" --- which is exactly the thesis's regime.

### JSONSchemaBench: A Rigorous Benchmark of Structured Outputs for Language Models
- Authors (as shown on page): Saibo Geng, Hudson Cooper, Michał Moskal, Samuel Jenkins, Julian Berman, Nathan Ranchin, Robert West, Eric Horvitz, Harsha Nori
- Venue / year: arXiv preprint, 2025 (v1 18 Jan 2025, v3 27 Feb 2025); no venue listed on the abstract page
- Identifier: arXiv:2501.10868
- Page fetched: https://arxiv.org/abs/2501.10868
- Serves: Master ch2 section "Constrained decoding"
- Supports the claim: that schema-constrained (as opposed to free-form) generation is a benchmarked
  research area, and that llama.cpp's grammar engine is one of six frameworks measured against the
  others --- lets the thesis situate its own runtime choice in a comparative literature rather than
  citing the repository alone. Note the title on the arXiv page differs from the title in some
  search listings ("Generating Structured Outputs from Language Models: Benchmark and Studies");
  verify which one the citation should carry.

### Constrained Language Models Yield Few-Shot Semantic Parsers
- Authors (as shown on page): Richard Shin, Christopher Lin, Sam Thomson, Charles Chen, Subhro Roy, Emmanouil Antonios Platanios, Adam Pauls, Dan Klein, Jason Eisner, Benjamin Van Durme
- Venue / year: Proceedings of EMNLP 2021, pages 7699--7715
- Identifier: doi:10.18653/v1/2021.emnlp-main.608
- Page fetched: https://aclanthology.org/2021.emnlp-main.608/
- Serves: Master ch2 section "Constrained decoding" (and bridges to "Spoken-language understanding for robotics")
- Supports the claim: that constraining a decoder to a formal meaning representation is the
  established approach for *semantic parsing specifically* --- i.e. for the thesis's actual task
  shape (utterance in, structured command out), not just for code or SQL. Useful for joining the
  constrained-decoding section to the SLU section in the Positioning synthesis.

### Flexible and Efficient Grammar-Constrained Decoding
- Authors (as shown on page): Kanghee Park, Timothy Zhou, Loris D'Antoni
- Venue / year: arXiv preprint (v1 7 Feb 2025, v2 15 Jul 2025); no journal-ref listed
- Identifier: arXiv:2502.05111
- Page fetched: https://arxiv.org/abs/2502.05111
- Serves: Master ch2 section "Constrained decoding"
- Supports the claim: that the grammar is "compiled once" and then used to mask --- and that this
  offline compilation step is itself a measurable cost ("existing GCD algorithms require tens of
  minutes to preprocess common grammars"). Relevant if the thesis reports GBNF compile time
  separately from per-token decode overhead.

---

## GAP 2 --- Post-training quantisation of LLMs

Ordered so that the four method papers come first (they are what `\section{Quantisation}` needs to
stop citing a repository for), then the evaluation papers, which is where the thesis's C3 argument
is actually at risk.

### GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers
- Authors (as shown on page): Elias Frantar, Saleh Ashkboos, Torsten Hoefler, Dan Alistarh
- Venue / year: ICLR 2023 (per arXiv comments field); arXiv submission Oct 2022
- Identifier: arXiv:2210.17323
- Page fetched: https://arxiv.org/abs/2210.17323
- Serves: Master ch2 section "Quantisation"
- Supports the claim: that one-shot post-training weight quantisation to 3--4 bits is the standard
  route from a floating-point checkpoint to a deployable artefact, with "negligible accuracy
  degradation relative to the uncompressed baseline". The canonical citation for the sentence
  "Post-training quantisation is the standard route ...".

### AWQ: Activation-aware Weight Quantization for On-Device LLM Compression and Acceleration
- Authors (as shown on page): Ji Lin, Jiaming Tang, Haotian Tang, Shang Yang, Wei-Ming Chen, Wei-Chen Wang, Guangxuan Xiao, Xingyu Dang, Chuang Gan, Song Han
- Venue / year: Proceedings of Machine Learning and Systems 6 (MLSys 2024)
- Identifier: MLSys 2024 proceedings (page URL below)
- Page fetched: https://proceedings.mlsys.org/paper_files/paper/2024/hash/42a452cbafa9dd64e9ba4aa95cc1ef21-Abstract-Conference.html
- Serves: Master ch2 section "Quantisation"
- Supports the claim: that "weights are not equally important" and that protecting roughly 1% of
  salient weights sharply reduces quantisation error --- the research-literature analogue of what
  Q4_K_M's mixed-precision correction term does, i.e. the principle behind "spends more bits on the
  blocks quantisation error is largest in". This is the citation that turns that sentence from a
  description of one runtime into a statement about a known technique.

### LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale
- Authors (as shown on page): Tim Dettmers, Mike Lewis, Younes Belkada, Luke Zettlemoyer
- Venue / year: NeurIPS 2022 (arXiv page notes camera-ready)
- Identifier: arXiv:2208.07339
- Page fetched: https://arxiv.org/abs/2208.07339
- Serves: Master ch2 section "Quantisation"
- Supports the claim: outlier handling --- that a small set of systematic emergent outlier features
  dominates quantisation error and must be kept at higher precision. Backs the 8-bit half of the
  thesis's Q8_0 description and explains *why* a per-block scale is needed at all.

### SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models
- Authors (as shown on page): Guangxuan Xiao, Ji Lin, Mickael Seznec, Hao Wu, Julien Demouth, Song Han
- Venue / year: Proceedings of the 40th International Conference on Machine Learning (ICML), PMLR 202, pages 38087--38099, 2023
- Identifier: PMLR v202 (page URL below)
- Page fetched: https://proceedings.mlr.press/v202/xiao23c.html
- Serves: Master ch2 section "Quantisation"
- Supports the claim: the contrast that makes the thesis's scheme choice defensible --- weights are
  easy to quantise, activations are not. Justifies why a *weight-only* scheme (which is what k-quant
  is) is the right lever on a CPU-only board, rather than full W8A8.

### The case for 4-bit precision: k-bit Inference Scaling Laws
- Authors (as shown on page): Tim Dettmers, Luke Zettlemoyer
- Venue / year: Proceedings of the 40th International Conference on Machine Learning (ICML), PMLR 202, pages 7750--7774, 2023
- Identifier: PMLR v202 (page URL below)
- Page fetched: https://proceedings.mlr.press/v202/dettmers23a.html
- Serves: Master ch2 section "Quantisation"
- Supports the claim: that 4-bit is "almost universally optimal for total model bits and zero-shot
  accuracy", and that small block sizes are one of only two levers that improve the bit-level
  tradeoff --- which is a direct, peer-reviewed justification for the thesis's choice of Q4_K_M
  block quantisation. **But read the caveat in the notes below: this paper's headline metric is
  zero-shot accuracy, not perplexity.**

### SpQR: A Sparse-Quantized Representation for Near-Lossless LLM Weight Compression
- Authors (as shown on page): Tim Dettmers, Ruslan Svirschevski, Vage Egiazarian, Denis Kuznedelev, Elias Frantar, Saleh Ashkboos, Alexander Borzunov, Torsten Hoefler, Dan Alistarh
- Venue / year: arXiv preprint, Jun 2023 ("Extended preprint"); ICLR 2024 per search results (ICLR page NOT fetched)
- Identifier: arXiv:2306.03078
- Page fetched: https://arxiv.org/abs/2306.03078
- Serves: Master ch2 section "Quantisation"
- Supports the claim: **the strongest single piece of evidence for the thesis's framing.** Its
  headline cost figure is stated explicitly in perplexity --- "relative accuracy losses of less than
  1% in perplexity" --- with no downstream task metric in the abstract at all. This is the paper to
  cite for the sentence "the accuracy cost of that reduction is ... expressed as a perplexity delta
  on a generic language-modelling corpus".

### A Comprehensive Evaluation of Quantization Strategies for Large Language Models
- Authors (as shown on page): Renren Jin, Jiangcun Du, Wuwei Huang, Wei Liu, Jian Luan, Bin Wang, Deyi Xiong
- Venue / year: Findings of the Association for Computational Linguistics: ACL 2024, pages 12186--12215
- Identifier: doi:10.18653/v1/2024.findings-acl.726 (also arXiv:2402.16775)
- Page fetched: https://aclanthology.org/2024.findings-acl.726/ and https://arxiv.org/abs/2402.16775
- Serves: Master ch2 section "Quantisation"
- Supports the claim: **cuts both ways, and the author must decide which way before citing it.** It
  evaluates ten downstream benchmarks (so downstream evaluation of quantisation demonstrably
  exists), but its conclusion is that "perplexity can serve as a proxy metric for quantized LLMs on
  most benchmarks" --- which is a published defence of exactly the convention C3 is attacking. See
  the notes below.

### Evaluating Quantized Large Language Models
- Authors (as shown on page): Shiyao Li, Xuefei Ning, Luning Wang, Tengxuan Liu, Xiangsheng Shi, Shengen Yan, Guohao Dai, Huazhong Yang, Yu Wang
- Venue / year: arXiv preprint (v1 28 Feb 2024, v2 6 Jun 2024); no journal-ref on the abstract page
- Identifier: arXiv:2402.18158
- Page fetched: https://arxiv.org/abs/2402.18158
- Serves: Master ch2 section "Quantisation"
- Supports the claim: that PTQ tolerance is structured --- weight-only and KV-cache quantisation are
  tolerated far better than activation quantisation, and tolerance grows with model size. The second
  half is the one that matters for this thesis: it implies a 0.36--1.2 B model is at the *least*
  tolerant end of the scale, which is an argument for measuring rather than assuming.

### Accuracy is Not All You Need
- Authors (as shown on page): Abhinav Dutta, Sanjeev Krishnan, Nipun Kwatra, Ramachandran Ramjee
- Venue / year: NeurIPS 2024 (arXiv journal-ref points at the NeurIPS 2024 proceedings page)
- Identifier: arXiv:2407.09141
- Page fetched: https://arxiv.org/abs/2407.09141
- Serves: Master ch2 section "Quantisation"
- Supports the claim: that even when a compressed model's aggregate accuracy matches the baseline,
  answers "flip" from correct to incorrect and back in non-negligible proportion --- so aggregate
  agreement hides behavioural divergence. For a thesis whose output is "executed by a flight
  controller rather than read by a person", this is the strongest available argument that an
  aggregate delta is not a safety argument, and it generalises the thesis's point beyond perplexity.

### "Give Me BF16 or Give Me Death"? Accuracy-Performance Trade-Offs in LLM Quantization
- Authors (as shown on page): Eldar Kurtic, Alexandre Noll Marques, Shubhra Pandit, Mark Kurtz, Dan Alistarh
- Venue / year: Proceedings of ACL 2025 (Long Papers), pages 26872--26886
- Identifier: doi:10.18653/v1/2025.acl-long.1304 (also arXiv:2411.02355)
- Page fetched: https://aclanthology.org/2025.acl-long.1304/
- Serves: Master ch2 section "Quantisation"
- Supports the claim: **this is the paper that most directly threatens C3 as currently worded.** It
  evaluates FP8/INT8/INT4 across "academic benchmarks and real-world tasks" over the whole
  Llama-3.1 family with more than 500,000 individual evaluations, and reports accuracy degradation
  in percentage points on tasks (1--3% for INT8), not as a perplexity delta. Read before finalising
  the C3 wording.

### Which Quantization Should I Use? A Unified Evaluation of llama.cpp Quantization on Llama-3.1-8B-Instruct
- Authors (as shown on page): Uygar Kurt
- Venue / year: arXiv preprint, 11 Jan 2026 (17 pages, 6 tables, 1 figure); no journal-ref listed
- Identifier: arXiv:2601.14277
- Page fetched: https://arxiv.org/abs/2601.14277
- Serves: Master ch2 section "Quantisation"
- Supports the claim: **the closest published work to C3 and the one the author most needs to read
  in full.** It evaluates llama.cpp's own K-quant and legacy GGUF formats (Q3_K*, Q4_0/1, Q4_K*,
  Q5_*, Q6_K, Q8_0 against FP16) on downstream reasoning, knowledge, instruction-following and
  truthfulness benchmarks *alongside* perplexity, plus CPU throughput. It is a single-author
  preprint on an 8 B model rather than a sub-billion one, and it is a generic-benchmark study
  rather than a task-specific one --- which is where C3's remaining novelty has to be located.

### SLMQuant: Benchmarking Small Language Model Quantization for Practical Deployment
- Authors (as shown on page): Jiacheng Wang, Yejun Zeng, Jinyang Guo, Yuqing Ma, Aishan Liu, Xianglong Liu
- Venue / year: arXiv preprint, 17 Nov 2025; an ACM DOI is listed on the page (doi:10.1145/3746262.3761973) --- verify the venue behind it
- Identifier: arXiv:2511.13023
- Page fetched: https://arxiv.org/abs/2511.13023
- Serves: Master ch2 section "Quantisation"
- Supports the claim: that quantisation results obtained on large models do not transfer to small
  ones --- "direct transfer of LLM-optimized techniques leads to suboptimal results due to SLMs'
  unique architectural characteristics". This is the best available defence of the thesis's decision
  to measure quantisation cost on 0.36--1.2 B models rather than inherit a figure from the 7 B+
  literature, and it should probably be cited in the Gap paragraph of "Positioning" as well.

### An empirical study of LLaMA3 quantization: from LLMs to MLLMs
- Authors (as shown on page): Wei Huang, Xingyu Zheng, Xudong Ma, Haotong Qin, Chengtao Lv, Hong Chen, Jie Luo, Xiaojuan Qi, Xianglong Liu, Michele Magno
- Venue / year: published article, volume 2, article number 36 (2024), doi:10.1007/s44267-024-00070-x; arXiv v1 Apr 2024, v3 Jan 2025
- Identifier: arXiv:2404.14047 / doi:10.1007/s44267-024-00070-x
- Page fetched: https://arxiv.org/abs/2404.14047
- Serves: Master ch2 section "Quantisation"
- Supports the claim: that a modern instruction-tuned model "still suffers from non-negligible
  degradation" under low-bit PTQ, with the damage concentrated at ultra-low bit-widths. Useful as
  the counterweight to the "quantisation is expected to be cheap" assumption the thesis names.

---

## Notes for the author

**GAP 2: the C3 framing is partly contradicted by the literature, and you should adjust the wording
before your jury does.** The chapter currently says quantisation cost is "reported against generic
perplexity, not against exact match, intent and slot F1, or schema validity", and that the cost "is
an assumption carried by convention rather than a number anyone has measured". The first half of
that survives; the second half, as written, does not. Specifically:

1. **Kurtic et al. (ACL 2025)** run over 500,000 evaluations across academic benchmarks *and*
   real-world tasks and report accuracy degradation in task percentage points (1--3% for INT8).
   Downstream task cost of quantisation is measured, published, and peer-reviewed at a top venue.
2. **Kurt (arXiv:2601.14277, Jan 2026)** evaluates llama.cpp's exact K-quant ladder --- including
   Q4_K and Q8_0 --- on downstream reasoning, knowledge, instruction-following and truthfulness
   benchmarks, next to perplexity and CPU throughput. This is the same runtime, the same quant
   family, and downstream metrics. It is the nearest neighbour to C3 that exists.
3. **Jin et al. (ACL Findings 2024)** is worse than neutral for the argument: it evaluates ten
   downstream benchmarks and concludes that *perplexity is an adequate proxy* for quantised LLMs on
   most of them. That is a published position directly opposed to C3's premise.
4. **Dettmers & Zettlemoyer (ICML 2023)** report the 4-bit result in terms of **zero-shot accuracy**,
   not perplexity, across ~35,000 experiments. So "the literature reports perplexity" is not true of
   the flagship scaling-law paper either.

What *does* survive, and what I would recommend C3 be narrowed to, is the conjunction of four
things, none of which I found covered together anywhere: (a) sub-billion-parameter models --- the
downstream-evaluation literature above is 7 B and up, and **Wang et al. (SLMQuant)** is explicit
that small-model quantisation behaves differently and is "significantly underexplored"; (b) a
*task-specific* metric set (exact match, intent/slot F1, schema validity, false-command rate) rather
than a generic benchmark suite; (c) measured on the deployed Raspberry Pi 5 rather than a server;
and (d) under grammar-constrained decoding, which none of the quantisation papers combine with.
"Nobody has measured the downstream cost of quantisation" is refutable; "nobody has measured it for
this model class, on this task, on this hardware" is not, on what I could find. The method-paper
side of the framing is safe: **SpQR** states its cost as "less than 1% in perplexity" with no
downstream metric in the abstract at all, and **GPTQ** says only "negligible accuracy degradation".

**GAP 1: one thing worth folding into the chapter.** The section currently presents the grammar as
pure gain at a fixed per-token overhead. Two papers complicate that and would strengthen the
ablation's motivation rather than weaken it: **Park et al., Grammar-Aligned Decoding (NeurIPS 2024)**
shows that constraining the decoder *distorts the model's distribution* --- grammatical outputs whose
likelihoods no longer track the model's own --- and **Tam et al. (EMNLP 2024 Industry)** measures a
significant drop in reasoning accuracy under format restriction. Both are reasons the grammar
ablation you promise in ch5 is the right experiment, but the current text does not anticipate either.
Also note that **Koo et al. (COLM 2024)** motivates constrained decoding precisely by the failure of
fine-tuning to guarantee conformance "especially with smaller LMs suitable for large-scale
deployment" --- that sentence is almost a description of this thesis's setup and is worth citing
where the chapter distinguishes what the grammar contributes from what fine-tuning already did.

**What I looked for and could not find.** (i) No paper evaluating quantisation cost on an
intent-and-slot / spoken-language-understanding task at sub-billion scale --- the nearest hits were
distillation+quantisation frameworks for speech understanding, not PTQ ablations on an LLM parser.
(ii) No paper measuring the *interaction* between grammar-constrained decoding and quantisation
(i.e. whether the grammar recovers accuracy a quantised model loses). If your ch5 reports that
interaction, it is likely the least-contested part of C3. (iii) No peer-reviewed analysis of the
k-quant scheme itself (Q4_K_M's block structure and correction term) --- it appears to exist only in
the llama.cpp repository and in third-party evaluations of it, so `\cite{llamacpp}` stays load-bearing
for the *scheme description*, with AWQ and Dettmers & Zettlemoyer supplying the principles it
instantiates.

---

## UNVERIFIED --- could not fetch

- **Synchromesh: Reliable Code Generation from Pre-trained Language Models** (ICLR 2022; authors
  reported by search as Gabriel Poesia, Alex Polozov, Vu Le, Ashish Tiwari, Gustavo Soares,
  Christopher Meek, Sumit Gulwani). Introduces Constrained Semantic Decoding. OpenReview
  (`https://openreview.net/forum?id=KmtVD97J43e`) returned a bot-verification page on every attempt
  and the API endpoint redirected to the same challenge, so **the author list, title and venue above
  are from search-result text, not from a page I retrieved.** It is a reasonable addition to GAP 1 if
  you verify it yourself; do not cite it as listed here.
- **Guiding LLMs The Right Way** --- the PMLR proceedings page *was* fetched and is authoritative for
  authors, title, venue and pages. The arXiv number (2403.06988) came from search results only; if
  you prefer to cite the preprint, open the arXiv page first.
- **SpQR** --- the arXiv abstract page was fetched. Its ICLR 2024 publication was reported by search
  results only and the ICLR proceedings page was not retrieved; verify before citing it as ICLR.
