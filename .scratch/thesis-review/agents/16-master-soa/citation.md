# Citation agent report: thesis/master/ch3_state_of_the_art.tex (issue 16, D5 only)

Date: 2026-09-25. Chapter at commit `7830694` (341 lines, 19 keys, 57 citation sites, four tables).
Sources opened: every arXiv abstract page; the arXiv HTML full text for sbc2025, kurt2026, kurtic2025,
slmquant, park2024, tam2024, qwen25, smollm2; the ACL Anthology pages and PDFs (via pdftotext) for
kurtic2025, massive, tam2024; the GPTQ and Qin PDFs (pdftotext); the MLSys and ICLR proceedings pages
for awq and spqr; the Meta blog page for llama32; and the llama.cpp repository files
`grammars/README.md`, `tools/quantize/README.md`, `ggml/src/ggml-common.h`, `src/llama-quant.cpp`
(at `master`; the bib pins b10863, see UNVERIFIED). Candidate notes were not used as evidence.
Where a sentence is unchanged from the text issue 02 verified, the verdict is reused and marked
"(02)"; it was still re-read against the source this round.

## 1. Verdict

The chapter's citations are in good order: 53 of the 57 sheet rows are SUPPORTS, every one of the 19
quoted paper numbers is found at the stated value in the primary source (the MASSIVE figures are
the locale-averaged column of Table 3a, exactly as written), and the bibliography metadata now
agrees with the primary pages for all 19 keys (the two issue-02 fixes to spqr and awq are in). Two
cells and three prose claims must be fixed before the chapter is ready: Table 3.2 attributes
Kurtic's 1.5 B model to the Llama-3.1 family when it is a DeepSeek-R1-Distill-Qwen; Gap G3 says the
task-scoring quantisation studies "work at eight billion parameters and above", which the chapter's
own Table 3.2 rows for kurtic2025 (1.5 B) and slmquant (135 M, 0.5 B) refute; and the reading of
park2024 ("without stating how much accuracy that costs on any task") is contradicted by the paper's
own correctness counts. Ready after fixes.

## 2. Citation table (D5b)

Verdict per citation site of the report's sheet; table rows are grouped when every cell agrees.

| # | Key | file:line | Claim or cell it carries | Verdict | Source passage / note |
|---|---|---|---|---|---|
| 1 | sbc2025 | ch3:20-22 | 25 quantised models, 3 SBCs, 2 runtimes (Ollama, Llamafile) | SUPPORTS (02) | Abstract: "25 quantized open-source LLMs across three SBCs -- Raspberry Pi 4, Raspberry Pi 5, and Orange Pi 5 Pro -- using two inference runtimes: Ollama and Llamafile" |
| 1b | sbc2025 | ch3:22-23 | boards reliably support up to ~1.5 B; larger drop to a few tok/s | SUPPORTS (02) | Abstract: "SBCs can reliably support models up to 1.5B parameters"; body: "larger models (>=3B) ... only practically deployable on the Orange Pi 5 Pro, where they still operated below 5 tokens/s" |
| 2 | sbc2025 | ch3:23-25 | on the one board where both were compared, Llamafile up to 4x Ollama | SUPPORTS (02) | Abstract "up to 4x higher throughput"; body: "Llamafile on 4 performance cores (Orange Pi 5 Pro) achieved 3-4x speed improvements"; "Raspberry Pi 4 and 5 excluded due to Llamafile compatibility limitations" |
| 3 | kurt2026 | ch3:29-31 | llama.cpp formats on Llama-3.1-8B-Instruct; benchmark accuracy + perplexity + CPU throughput | SUPPORTS (02) | Abstract: "unified empirical study of llama.cpp quantization on a single modern model, Llama-3.1-8B-Instruct (FP16, GGUF), covering 3-8 bit K-quant and legacy formats ... downstream task performance ... perplexity and CPU throughput" |
| 4 | sbc2025 | ch3:48 (tab:soa-edge) | Models "25 quantised models, up to a few billion parameters" | PARTIAL | 25 models, but four are 7 B (Qwen2.5-7B, LLaMA2-7B, LLaMA3.2-7B, Mistral-7B); smallest 135 M. "Up to a few billion" understates. |
| 4b | sbc2025 | ch3:48 | Hardware "Three SBCs" | SUPPORTS | as row 1 |
| 4c | sbc2025 | ch3:48 | Runtime "Ollama and Llamafile; formats as distributed" | PARTIAL | Paper: "all models were quantized using the q4_k_m quantization scheme, which balances memory efficiency with minimal performance degradation". It never says "as distributed"; it names one format. See finding 5. |
| 4d | sbc2025 | ch3:48 | Metrics "Throughput, resource use; no task" | SUPPORTS | Abstract: "generation throughput, memory usage, and power consumption"; no output-quality metric anywhere in the paper |
| 5 | kurt2026 | ch3:49 (tab:soa-edge) | "Llama-3.1-8B-Instruct"; "CPU; ---"; "llama.cpp; K-quant and legacy GGUF formats against fp16"; "Perplexity, generic benchmark accuracy, CPU throughput; generic tasks" | SUPPORTS | Formats: Q3_K_S/M/L, Q4_0, Q4_1, Q4_K_S/M, Q5_0, Q5_1, Q5_K_S/M, Q6_K, Q8_0 vs F16; hardware: dual Intel Xeon Platinum 8488C, no GPU; benchmarks GSM8K, HellaSwag, IFEval, MMLU, TruthfulQA; WikiText-2 perplexity. The hardware dash is fillable (the CPU is named), not a finding. |
| 6 | qwen25 | ch3:68 | Qwen2.5-0.5B is a model of this report | SUPPORTS | Report intro: "open-weight offerings include base models and instruction-tuned models in sizes of 0.5B, 1.5B, 3B, 7B, 14B, 32B, and 72B" |
| 7 | smollm2 | ch3:68 | SmolLM2-360M | SUPPORTS | §6 "SmolLM2 135M and 360M": "we also trained two smaller models: SmolLM2-360M (360M parameters, trained on 4T tokens) and SmolLM2-135M" |
| 8 | llama32 | ch3:68 | Llama-3.2-1B | SUPPORTS | Blog (25 Sep 2024): "lightweight, text-only models (1B and 3B) that fit onto edge and mobile devices" |
| 9 | danube3 | ch3:69 | H2O-Danube3-500M | SUPPORTS | Abstract: "H2O-Danube3-4B, trained on 6T tokens and H2O-Danube3-500M, trained on 4T tokens" |
| 10 | llamacpp | ch3:75 | llama.cpp is the runtime | SUPPORTS | repository |
| 11 | gptq | ch3:81-82 | PTQ is the established route to reducing memory footprint | SUPPORTS (02) | Abstract: "extremely high computational and storage costs"; "allowing us for the first time to execute an 175 billion-parameter model inside a single GPU" |
| 12 | awq | ch3:82 | on-device deployment is a stated motivation | SUPPORTS (02) | Abstract: "on-device LLM is becoming increasingly important"; MLSys title "... for On-Device LLM Compression and Acceleration" |
| 13 | awq | ch3:88-90 | protecting ~1% of channels marked salient by activation statistics greatly reduces error | SUPPORTS (02) | Abstract: "protecting only 1% salient weights can greatly reduce quantization error. To identify salient weight channels, we should refer to the activation distribution, not weights" |
| 14 | llamacpp | ch3:92-93 | cost usually measured as perplexity or KL divergence | SUPPORTS (02) | tools/quantize/README.md: "may introduce some accuracy loss which is usually measured in Perplexity (ppl) and/or Kullback-Leibler Divergence (kld)" |
| 15 | spqr | ch3:100-101 | relative perplexity loss under 1% | SUPPORTS (02) | Abstract: "relative accuracy losses of less than 1% in perplexity for highly-accurate LLaMA and Falcon LLMs" |
| 16 | gptq | ch3:101-102 | perplexity + zero-shot on LAMBADA, ARC, PIQA | SUPPORTS (02) | §4 "Zero-Shot Tasks ... LAMBADA (Paperno et al., 2016), ARC (Easy and Challenge) ... and PIQA"; Tables 3-5 WikiText2/PTB/C4 perplexity |
| 17 | kurtic2025 | ch3:104-105 | downstream accuracy under quantisation at scale | SUPPORTS | Abstract: "comprehensive empirical study of quantized accuracy ... across academic benchmarks and real-world tasks, on the entire Llama-3.1 model family" (>500k evaluations) |
| 18 | kurt2026 | ch3:105 | ... and for llama.cpp's own formats | SUPPORTS | as row 3 |
| 19 | kurtic2025 | ch3:106-108 | models mostly >= 8 B; generic reasoning/knowledge/coding; decoder unconstrained; smallest model 1.5 B | SUPPORTS | §3.2: "instruction-tuned versions of all available sizes (8B, 70B, and 405B)"; §4.3 + Table 4: DeepSeek-R1-Distill "Qwen-1.5B" on AIME24, MATH-500, GPQA-Diamond (pass@1). The 1.5 B model exists, but it is not Llama-3.1 (see row 25). |
| 20 | slmquant | ch3:108-111 | sub-billion benchmark incl. Qwen2.5-0.5B; small models differ in sensitivity; large-model methods transfer poorly | SUPPORTS (02) | Abstract: "fundamental disparities between SLMs and LLMs in quantization sensitivity, demonstrating that direct transfer of LLM-optimized techniques leads to suboptimal results"; models SmolLM2-135M and Qwen2.5-0.5B |
| 21 | gptq | ch3:127 (tab:soa-quantisation) | "One-shot weight quantisation to 3--4 bits with error compensation from calibration data"; "Perplexity; zero-shot accuracy on generic benchmarks"; grammar No | SUPPORTS | Abstract: "one-shot weight quantization method based on approximate second-order information ... down to 3 or 4 bits per weight"; §3 OBQ: "updating all not-yet-quantized weights, in order to compensate for the error"; §4: "calibration data consists of 128 random 2048 token segments from the C4 dataset" |
| 22 | awq | ch3:128 | "Weight-only; salient channels protected by activation statistics"; cost "---"; grammar No | SUPPORTS | Abstract: "weight-only quantization"; salience from "the activation distribution, not weights". The cost dash is fillable (perplexity + coding/math + instruction-tuned + multimodal evals), not a finding. |
| 23 | spqr | ch3:129 | "Outlier weights isolated at higher precision"; "Relative perplexity loss under one percent" | SUPPORTS | Abstract: "identifying and isolating outlier weights ... storing them in higher precision, while compressing all other weights to 3-4 bits" |
| 24 | llamacpp | ch3:130 | "Any GGUF model"; "Bits by tensor role, position and shape; no calibration"; "Perplexity; KL divergence"; grammar "Optional" | SUPPORTS | src/llama-quant.cpp `llama_tensor_get_type`: attn_v and ffn_down -> Q6_K when `use_more_bits(i_layer, n_layer)` (= `i_layer < n_layer/8 || i_layer >= 7*n_layer/8 || (i_layer - n_layer/8)%3 == 2`); fallback when `ne[0] % QK_K != 0`: Q4_K -> Q5_0, Q6_K -> Q8_0; imatrix optional. Grammar: grammars/README, `--grammar` flag / server `grammar` field. Cost: quantize README as row 14. "No calibration" should read "none required" (imatrix is optional calibration); NIT. |
| 25 | kurtic2025 | ch3:131 | "Llama-3.1 family; smallest 1.5~B"; "FP8, INT8, INT4"; "Accuracy on academic benchmarks and real-world tasks"; grammar No | PARTIAL | Llama-3.1 sizes are 8B/70B/405B (§3.2). The 1.5 B model is DeepSeek-R1-Distill-Qwen-1.5B (Table 4), a Qwen-based distillation evaluated on reasoning suites only. Formats and benchmark classes agree (W8A8-FP, W8A8-INT, W4A16-INT; Open LLM Leaderboard V1/V2 vs Arena-Hard, HumanEval(+), RULER). Finding 1. |
| 26 | kurt2026 | ch3:132 | "Llama-3.1-8B-Instruct"; "llama.cpp formats from Q3_K to Q8_0"; "Perplexity; generic benchmark accuracy; CPU throughput"; grammar No | SUPPORTS | as row 5; the range Q3_K_S ... Q8_0 is exact, with the legacy Q4_0/Q4_1/Q5_0/Q5_1 inside it |
| 27 | slmquant | ch3:133 | "Sub-billion models, Qwen2.5-0.5B among them"; "Methods tuned on large models, applied to small ones"; "Generic benchmark accuracy"; grammar No | SUPPORTS | Models SmolLM2-135M, Qwen2.5-0.5B; methods SmoothQuant, OmniQuant, SpinQuant (W8A8, W4A8); MMLU, ARC-c/e, PIQA, HellaSwag, WikiText2 |
| 28 | geng2023 | ch3:161-162 | GCD applied to structured NLP tasks without fine-tuning | SUPPORTS (02) | Title "... without Finetuning"; abstract: information extraction, entity disambiguation, constituency parsing; EMNLP 2023 |
| 29 | willard2023, koo2024 | ch3:165-167 | regex or CFG compiled to an automaton over the vocabulary; decoder masked against it | SUPPORTS (02) | Willard abstract: "guiding text generation with regular expressions and context-free grammars by allowing the construction of an index over a language model's vocabulary"; Koo abstract: "application of automata theory, deriving an efficient closed-form solution for the regular languages ... deterministic context-free languages" |
| 30 | koo2024 | ch3:167-168 | correctness results for the covered language classes | SUPPORTS (02) | Abstract: "Our system compiles constraints ~7,000x faster, is provably correct" |
| 31 | llamacpp | ch3:168-169 | GBNF is llama.cpp's formalism | SUPPORTS | grammars/README: "GBNF (GGML BNF) is a format for defining formal grammars to constrain model outputs in llama.cpp" |
| 32 | park2024 | ch3:186-189 | constraining alters the distribution; outputs grammatical but likelihoods no longer track the unconstrained model | SUPPORTS | Abstract: "GCD techniques ... can distort the LLM's distribution, leading to outputs that are grammatical but appear with likelihoods that are not proportional to the ones given by the LLM, and so ultimately are low-quality" |
| 33 | tam2024 | ch3:189-191 | format restriction degrades reasoning more as it tightens; classification sometimes helped | SUPPORTS (02) | Abstract: "stricter format constraints generally lead to greater performance degradation in reasoning tasks"; §4: on classification (DDXPlus, MultiFin, Sports, NI Task 280) "JSON-mode performs competitively, and in some cases, surpasses the other" methods |
| 34 | geng2023 | ch3:207 (tab:soa-constrained) | "Application"; "Context-free grammar; token masking on structured NLP tasks"; fine-tuned "No"; accuracy "---" | SUPPORTS | As row 28; the accuracy dash is fillable (the paper reports GCD-enhanced LMs beating unconstrained and some finetuned baselines), not a finding |
| 35 | willard2023 | ch3:208 | "Construction"; "Regular expression or context-free grammar compiled to a finite-state index over the vocabulary"; "---"; "---" | SUPPORTS | as row 29; the paper reports overhead, not task accuracy |
| 36 | koo2024 | ch3:209 | "Construction"; "Automata for regular and deterministic context-free languages; provably correct masks" | SUPPORTS | as rows 29-30 |
| 37 | park2024 | ch3:210 | "Cost study"; "GCD shown to distort the distribution; an aligned alternative proposed"; fine-tuned "---"; accuracy "Yes, as divergence from the unconstrained distribution" | PARTIAL | Distortion and ASAp: supports. The measured divergence is KL(Q_GCD || P) where P = Q^{P,G}(w) = 1[w in L(G)] P(w) / sum, i.e. the model's distribution conditioned on the grammar, not the unconstrained one; and correctness is also measured ("ASAp returns the correct solution for 1588 samples, whereas GCD only returns the correct solution 12 times"; "38% more often than GCD (geomean)"). Finding 4. |
| 38 | tam2024 | ch3:211 | "Cost study"; "Format restriction of increasing strictness"; fine-tuned "No"; "reasoning accuracy falls as restriction tightens; classification sometimes helped" | SUPPORTS | Three settings JSON-mode > FRI > NL-to-Format; all models prompted (GPT-3.5-turbo, Claude-3-Haiku, Gemini-1.5-Flash, LLaMA-3-8B-Instruct, Gemma-2-9B-Instruct); no fine-tuning |
| 39 | llamacpp | ch3:212 | "Implementation"; "BNF dialect parsed per request and applied per step; cost depends on rule shape" | PARTIAL | README: "an extension of BNF"; grammar supplied per request (`--grammar`, `--grammar-file`, server `grammar` field) and constrains tokens at each step; "Grammars currently have performance gotchas"; "`x? x? x?.... x?` (with N repetitions) may result in extremely slow sampling". "Parsed per request" is not stated (only that a bad grammar "will fail to parse"). Finding 9. |
| 40 | qin2021 | ch3:240-242 | survey: semantic frame as object; methods by separate vs joint | SUPPORTS (02) | Abstract: "SLU aims to extract the semantics frame of user queries"; taxonomy "single model vs. joint model" |
| 41 | massive | ch3:243-244 | 1 M utterances, 51 languages, 60 intents, 55 slot types; same formulation | SUPPORTS (02) | Abstract: "1M realistic, parallel, labeled virtual assistant utterances spanning 51 languages, 18 domains, 60 intents, and 55 slots" |
| 42 | massive | ch3:244-246 | encoders 258-580 M; locale-avg intent 85.1-86.1, slot F1 73.6-76.8, EM 63.7-66.6 | SUPPORTS (02) | §5.1 p.4283: "270M parameters for XLM-R, 258M parameters for mT5 Encoder-Only, and 580M parameters for mT5 Text-to-Text"; Table 3a Avg columns: intent 85.3 / 86.1 / 85.1, slot F1 76.8 / 75.4 / 73.6, EM 66.6 / 65.9 / 63.7 (mT5 T2T / mT5 enc-only / XLM-R) |
| 43 | qin2021 | ch3:263 (tab:soa-slu) | "Survey"; "Semantic frame of intent and slots; methods sorted into single and joint models"; dashes | SUPPORTS | as row 40 |
| 44 | massive | ch3:264 | "Corpus and baselines"; "60 intents, 55 slot types, 51 languages; encoder baselines of 258--580 M"; the three metric ranges; "Data-centre GPUs; no budget"; "None" | SUPPORTS | Figures as row 42; §5.1: "single p3dn.24xlarge instances (8 x Nvidia v100) for XLM-R and mT5 Text-to-Text and a single g4dn.metal instance (8 x Nvidia T4) for mT5 Encoder-Only"; no latency, memory or grammar constraint anywhere in the paper. Note "encoder baselines": mT5 Text-to-Text is an encoder-decoder; harmless since "encoders of 258 to 580 M" at l.244 has the same looseness (NIT, not listed). |
| 45 | massive | ch3:275-279 | EM is its lowest figure; reported not optimised; trained on data-centre GPUs; no grammar; no latency/memory limit | SUPPORTS | Table 3a (EM < slot F1 < intent for all three); hardware as row 44 |
| 46 | sbc2025 | ch3:291-293 | boards reliably serve up to ~1.5 B; on one board runtime changed throughput up to 4x | SUPPORTS (02) | as rows 1b, 2 |
| 47 | gptq | ch3:293-294 | PTQ the established way to shrink a trained model | SUPPORTS | as row 11 |
| 48 | awq | ch3:294 | on-device deployment among its motivations | SUPPORTS | as row 12 |
| 49 | spqr, gptq | ch3:294-295 | cost reported as perplexity and generic zero-shot accuracy by the method papers | SUPPORTS (02) | rows 15-16 |
| 50 | kurtic2025, kurt2026, slmquant | ch3:295-296 | as accuracy on general-purpose suites by the evaluations, incl. sub-billion | SUPPORTS | rows 17-20 |
| 51 | willard2023, koo2024 | ch3:297-298 | structurally valid by construction | SUPPORTS | Willard: "guaranteeing the structure of the generated text"; Koo: "provably correct" |
| 52 | park2024 | ch3:298-299 | a distorted sampling distribution | SUPPORTS | row 32 |
| 53 | tam2024 | ch3:299-300 | on reasoning tasks, lower accuracy | SUPPORTS | row 33 |
| 54 | massive | ch3:300-302 | established formulation; large multilingual benchmark | SUPPORTS | row 41 |
| 55 | kurt2026 | ch3:302-303 | quantisation + CPU inference + downstream accuracy combined | SUPPORTS (02) | row 3 |
| 56 | slmquant | ch3:303-304 | quantisation + small models | SUPPORTS (02) | row 20 |
| 57 | tam2024 | ch3:304 | format restriction + task accuracy | SUPPORTS (02) | row 33 |

Prose claims about a cited study that carry no \cite of their own (checked against the same sources):

| # | Key | file:line | Claim | Verdict | Source passage / note |
|---|---|---|---|---|---|
| P1 | sbc2025 | ch3:62-64 | "an 8-billion-parameter model that no SBC serves at interactive speed" | PARTIAL, uncited | sbc2025 ran four 7 B models and reports ">=3B ... below 5 tokens/s" on the Orange Pi 5 Pro; nothing in the chapter's sources says 8 B or "interactive". Finding 6. |
| P2 | gptq et al. | ch3:145-147 | "the shift from a distributional measure to a task measure is recent" | PARTIAL, uncited | The table's own GPTQ row (ICLR 2023, submitted Oct 2022) already reports zero-shot accuracy. Finding 10. |
| P3 | park2024, geng2023, willard2023, tam2024 | ch3:222 | "the three kinds do not cite one another's measurements" | DOES NOT SUPPORT | park2024 cites Willard and Louf [28] and Geng et al. [7], implements GCD "as an extension of the Transformers-CFG implementation of GCD" (Geng's), and evaluates on "6 problems from prior GCD work (Geng et al. 2023)"; tam2024 cites Willard and Louf. Finding 7. |
| P4 | park2024 | ch3:228-230 | "without stating how much accuracy that costs on any task" | DOES NOT SUPPORT | Park §Evaluation reports correctness under GCD vs ASAp on SLIA/INV-BV: "ASAp produces correct samples 38% more often than GCD (geomean)"; "1588 samples ... whereas GCD only ... 12 times"; on jointly-solved SLIA "73% less often". What Park never reports is accuracy against unconstrained decoding. Finding 3. |
| P5 | qin2021 | ch3:272-273 | "with the joint model as the modern default" | SUPPORTS, cite absent | Qin §3.2: "dominant work in the literature adopts joint model to leverage the shared knowledge across tasks"; §1: "dominant models in the literature adopt joint models". Finding 11. |
| P6 | kurtic2025, slmquant | ch3:330-331 | "those that score tasks at all work at eight billion parameters and above" | DOES NOT SUPPORT | kurtic2025 Table 4 scores DeepSeek-R1-Distill-Qwen-1.5B (pass@1 on AIME24, MATH-500, GPQA-Diamond); slmquant scores 135 M and 0.5 B models on MMLU, ARC, PIQA, HellaSwag. Both sit in Table 3.2 and are cited at l.296 "including at sub-billion scale". Finding 2. |

## 3. Numbers quoted from papers

| line | figure as written | source location | figure in source | OK? |
|---|---|---|---|---|
| ch3:20 | twenty-five quantised language models | sbc2025 abstract | "25 quantized open-source LLMs" | OK |
| ch3:21 | three SBCs | sbc2025 abstract | Raspberry Pi 4, Raspberry Pi 5, Orange Pi 5 Pro | OK |
| ch3:21 | two inference runtimes | sbc2025 abstract | Ollama and Llamafile | OK |
| ch3:22-23 | roughly 1.5 billion parameters | sbc2025 abstract | "reliably support models up to 1.5B parameters" | OK |
| ch3:24 | up to four times | sbc2025 abstract; body | "up to 4x higher throughput"; "3-4x speed improvements" on Orange Pi 5 Pro, 4 performance cores | OK |
| ch3:48 | 25 quantised models | sbc2025 abstract | 25 | OK |
| ch3:48 | up to a few billion parameters | sbc2025 model table | largest 7 B (four models) | Understated; MINOR, finding 8 |
| ch3:57 | twenty-five models on three boards | sbc2025 abstract | 25 / 3 | OK |
| ch3:88 | one percent of weight channels | awq abstract | "protecting only 1% salient weights can greatly reduce quantization error" | OK |
| ch3:100 | under one percent | spqr abstract | "relative accuracy losses of less than 1% in perplexity" | OK |
| ch3:106 | eight billion parameters and above | kurtic2025 §3.2; kurt2026 abstract | "(8B, 70B, and 405B)"; Llama-3.1-8B-Instruct | OK ("mostly": the 1.5 B and 7 B DeepSeek distils are the exceptions) |
| ch3:108 | has 1.5 billion parameters | kurtic2025 Table 4 | "Qwen-1.5B" row (DeepSeek-R1-Distill) | OK as a number; family wrong at l.131 (finding 1) |
| ch3:131 | smallest 1.5 B | kurtic2025 Table 4 | as above | number OK, attribution not |
| ch3:132 | Q3_K to Q8_0 | kurt2026 §formats | Q3_K_S ... Q8_0 (13 formats + F16) | OK |
| ch3:148 | one reaching down to 1.5 billion | kurtic2025 Table 4 | as above | OK |
| ch3:243 | one million utterances in 51 languages | massive abstract | "1M ... utterances spanning 51 languages" | OK |
| ch3:243 | 60 intents and 55 slot types | massive abstract | "60 intents, and 55 slots" | OK |
| ch3:244 | 258 to 580 million | massive §5.1 p.4283 | 270M (XLM-R), 258M (mT5 enc-only), 580M (mT5 T2T) | OK |
| ch3:245 | 85.1--86.1 | massive Table 3a, Intent Acc, Avg | 85.3, 86.1, 85.1 | OK |
| ch3:246 | 73.6--76.8 | massive Table 3a, Slot F1, Avg | 76.8, 75.4, 73.6 | OK |
| ch3:246 | 63.7--66.6 | massive Table 3a, Exact Match, Avg | 66.6, 65.9, 63.7 | OK |
| ch3:264 | 258--580 M; 85.1--86.1; 73.6--76.8; 63.7--66.6 | same | same | OK (clears the script's six UNTRACED warnings) |
| ch3:291-292 | about 1.5 billion; up to four times | sbc2025 | as above | OK |
| ch2 bg:198 | blocks of 32 | ggml-common.h | `#define QK8_0 32` | OK |
| ch2 bg:199 | super-blocks of 256 | ggml-common.h | `#define QK_K 256`; block_q4_K scales "8 sub-blocks of 32" | OK |
| ch2 bg:198 | 8.5 bits per weight | ggml-common.h | `sizeof(block_q8_0) == sizeof(ggml_half) + QK8_0` = 34 B / 32 = 8.5; quantize README table "Q8_0 8.50 bpw" | OK |
| ch2 bg:167 | 4.5 bits per weight (Q4_K block) | ggml-common.h | `sizeof(block_q4_K) == 2*sizeof(ggml_half) + K_SCALE_SIZE + QK_K/2` = 4+12+128 = 144 B / 256 = 4.5 | OK (the README's 4.89 bpw is the Q4_K_M mix, not the block) |

## 4. Findings (BLOCKER -> NIT)

| # | Sev | Dim | file:line | Quoted text | Problem | Evidence | Proposed fix |
|---|---|---|---|---|---|---|---|
| 1 | BLOCKER | D5b | ch3:131 | "Llama-3.1 family; smallest 1.5~B" | The cell attributes the 1.5 B model to the Llama-3.1 family. Kurtic's Llama-3.1 models are 8B, 70B, 405B; the 1.5 B model is DeepSeek-R1-Distill-Qwen-1.5B, evaluated only on reasoning suites. | kurtic2025 §3.2 "instruction-tuned versions of all available sizes (8B, 70B, and 405B)"; §4.3 and Table 4 "DeepSeek-R1-Distill models from both Llama and Qwen families ... Qwen-1.5B" (AIME24, MATH-500, GPQA-Diamond, pass@1) | Cell: "Llama-3.1-Instruct 8, 70 and 405~B; DeepSeek-R1-Distill 1.5--70~B on reasoning suites". Optionally at l.107-108: "the smallest model either study evaluates, a 1.5-billion-parameter reasoning distillation, ..." |
| 2 | BLOCKER | D5c | ch3:330-331 | "and those that score tasks at all work at eight billion parameters and above" | Refuted by two of the chapter's own Table 3.2 rows and by l.296 "including at sub-billion scale". | kurtic2025 Table 4 scores a 1.5 B model; slmquant scores SmolLM2-135M and Qwen2.5-0.5B on MMLU, ARC, PIQA, HellaSwag | "...with the decoder unconstrained, not EM, intent and slot F1, or schema validity on a command-parsing task; the one study at sub-billion scale scores generic suites too." (The scale point is already made correctly at l.147-150.) |
| 3 | MAJOR | D5b | ch3:228-230 | "the distortion result establishes that the constrained distribution differs from the unconstrained one without stating how much accuracy that costs on any task" | Park does state task correctness under GCD, against its aligned sampler, on two SyGuS task families. What it never does is compare against unconstrained decoding. | park2024 §Evaluation: "ASAp produces correct samples 38% more often than GCD (geomean)"; "ASAp returns the correct solution for 1588 samples, whereas GCD only returns the correct solution 12 times"; on jointly-solved SLIA "73% less often" | "...differs from the model's own grammar-conditioned one, and compares constrained decoders with each other, never with unconstrained decoding, so it does not say what a grammar costs against decoding without one" |
| 4 | MAJOR | D5b | ch3:210 | "Yes, as divergence from the unconstrained distribution" | The KL is to the grammar-conditioned model distribution, not the unconstrained one, and solution correctness is also reported. | park2024: P defined as Q^{P,G}(w) = 1[w in L(G)] P(w) / sum over L(G); metrics KL(Q_GCD || P), KL(Q_ASAp || P), expected values, and correctness counts on SLIA/INV-BV | Cell: "Yes: KL divergence from the model's grammar-conditioned distribution, and solution correctness on program-synthesis tasks, GCD against the aligned sampler only" |
| 5 | MAJOR | D5b | ch3:48 | "Ollama and Llamafile; formats as distributed" | The source does not say the models were used as distributed; it states one format for all 25. The true cell strengthens the comparison, since it is the format this thesis times on the Pi. | sbc2025: "all models were quantized using the q4_k_m quantization scheme, which balances memory efficiency with minimal performance degradation" | Cell: "Ollama and Llamafile; Q4\_K\_M throughout" |
| 6 | MAJOR | D5c | ch3:63-64 | "the format evaluation studies an 8-billion-parameter model that no \gls{sbc} serves at interactive speed" | Uncited literature claim; the only SBC source ran up to 7 B and says nothing about 8 B or "interactive". | sbc2025 model table (Qwen2.5-7B, LLaMA2-7B, LLaMA3.2-7B, Mistral-7B); ">=3B ... only practically deployable on the Orange Pi 5 Pro, where they still operated below 5 tokens/s" | "...an 8-billion-parameter model, a size at which the hardware benchmark's boards ran below five tokens per second~\cite{sbc2025}" |
| 7 | MAJOR | D5c | ch3:222 | "the three kinds do not cite one another's measurements, so the literature establishes correctness and cost separately, on different models and tasks" | The cost studies cite the constructions and the application; Park builds its GCD baseline on Geng's implementation and evaluates on Geng's constituency-parsing problems, so "different tasks" is also wrong in part. | park2024 cites Willard and Louf (2023) [28] and Geng et al. (2023) [7]; "We implemented the ASAp algorithm as an extension of the Transformers-CFG implementation of GCD"; CP "6 problems from prior GCD work (Geng et al. 2023)"; tam2024 cites Willard and Louf (2023) | "...the cost studies measure the mask's effect on models and tasks of their own, so the literature establishes correctness and cost in separate experiments" (drop the citation claim) |
| 8 | MINOR | D5b | ch3:48 | "25 quantised models, up to a few billion parameters" | Understates the range: four of the 25 are 7 B. | sbc2025 model table: SmolLM 135M ... Mistral 7B | "25 models, 135~M to 7~B" |
| 9 | MINOR | D5b | ch3:212 | "\gls{bnf} dialect parsed per request and applied per step" | "Parsed per request" is not in the README; "supplied per request" is. | grammars/README: `--grammar`, `--grammar-file`, server `grammar` field; "the grammar will fail to parse" is its only parsing statement | "BNF dialect supplied per request and applied at each sampling step; cost depends on rule shape" |
| 10 | MINOR | D5c | ch3:146 | "the shift from a distributional measure to a task measure is recent" | Uncited, and the table's own GPTQ row (2022/2023) already reports zero-shot task accuracy. | gptq §4 "Zero-Shot Tasks"; ICLR 2023 | "...the task measure is the evaluation studies' (2025--2026), and is made on generic benchmarks only" or drop "is recent" |
| 11 | MINOR | D5f | ch3:273 | "with the joint model as the modern default" | Supported by the survey but not cited where stated, and not in the survey's table cell either. | qin2021 §3.2 "dominant work in the literature adopts joint model" | Add "~\cite{qin2021}" after "default", or extend the l.263 cell to "...single and joint models, the joint model dominant" |
| 12 | NIT | D5b | ch3:130 | "no calibration" | An imatrix is optional calibration data for the same formats. | tools/quantize README: "This can be minimized by using a suitable imatrix file"; llama-quant.cpp accepts an optional imatrix | "no calibration required" |
| 13 | NIT | D5e | references.bib:186 | "Ben Allal, Loubna and others" | Truncated author list (25 authors on the paper). Acceptable in biblatex; an examiner may want the list. | arXiv 2502.02737 author list | Expand or leave; author's call |

Not findings (a dash is never a finding, per the issue), but fillable from the sources if the author wants fewer dashes: ch3:49 hardware "---" (dual Intel Xeon Platinum 8488C, 96 cores, no GPU); ch3:128 AWQ cost "---" (perplexity, coding/maths, instruction-tuned and multimodal evaluations); ch3:207 Geng accuracy "---" (GCD beats unconstrained and some finetuned baselines); ch3:210 Park fine-tuned "---" (Mistral-7B with 3 or 8 in-context examples, so "No").

For the argument agent (not D5): ch3:60-61 "the two agree that the inference engine is a variable of the same order as the model" -- kurt2026 has one model and one engine, so it cannot establish anything "of the same order as the model"; the sentence's own gloss ("the other by comparing one engine's formats") concedes this.

## 5. D5e bibliography metadata

| Key | identifier present | title/authors/year agree | note |
|---|---|---|---|
| sbc2025 | eprint 2511.07425, url | yes | arXiv authors "Tung (Thomas) Nguyen, Tuyen Nguyen"; 2025 |
| kurt2026 | eprint 2601.14277, url | yes | single author Uygar Kurt; submitted 11 Jan 2026 |
| qwen25 | eprint 2412.15115, url | yes | paper prints "Qwen Team" as author; arXiv listing expands to 42 names; bib's {Qwen Team} matches the paper |
| smollm2 | eprint 2502.02737, url | yes (first author) | "and others" for 25 authors (finding 13, NIT); title dash rendered "---" vs arXiv "--", fine |
| llama32 | url, urldate | yes | Meta blog, 25 Sep 2024; title case differs from the page ("edge AI and vision") only in capitalisation |
| danube3 | eprint 2407.09276, url | yes | six authors as listed |
| llamacpp | url, version b10863, urldate | yes | checked at master, not at b10863 (UNVERIFIED note) |
| gptq | eprint 2210.17323, url; ICLR 2023 | yes | arXiv comment "ICLR 2023" |
| awq | eprint 2306.00978, url (MLSys) | yes | eprint added since issue 02. Bib title carries "On-Device", which is the MLSys 2024 proceedings title (vol. 6); arXiv v6 (Apr 2026) drops "On-Device". The bib cites the proceedings, so it is right as is. |
| spqr | eprint 2306.03078, url (ICLR proceedings) | yes | @inproceedings ICLR 2024 since issue 02; proceedings page confirms |
| kurtic2025 | doi 10.18653/v1/2025.acl-long.1304, url | yes | ACL 2025 long, pp. 26872-26886; arXiv 2411.02355 comment "Accepted to ACL 2025" |
| slmquant | eprint 2511.13023, url | yes | arXiv prints "SLMQuant:Benchmarking" without the space; cosmetic |
| geng2023 | eprint 2305.13971, url; EMNLP 2023 | yes | arXiv comment "Accepted at EMNLP 2023 Main Conference". The "% No venue: arXiv preprint only" comment after this entry belongs to willard2023 below it; harmless |
| willard2023 | eprint 2307.09702, url | yes | preprint, no venue; correct as @misc |
| koo2024 | eprint 2407.08103, url; COLM 2024 | yes | arXiv comment "COLM 2024 camera-ready" |
| park2024 | eprint 2405.21047, url; NeurIPS 2024 | yes | arXiv comment "Accepted to NeurIPS 2024" |
| tam2024 | doi 10.18653/v1/2024.emnlp-industry.91, url | yes | pp. 1218-1236 |
| qin2021 | eprint 2103.03095, url; IJCAI 2021 | yes | arXiv comment "Accepted at IJCAI 2021" |
| massive | doi 10.18653/v1/2023.acl-long.235, url | yes | ACL 2023 long, pp. 4277-4302; 16 authors as listed |

## 6. UNVERIFIED / COULD NOT ACCESS

- llama.cpp was read at `master` (grammars/README.md, tools/quantize/README.md, ggml-common.h,
  llama-quant.cpp), not at the pinned build b10863. The four block constants and the two README
  passages are long-standing and issue 02 confirmed them on the local b10863 checkout; the
  `use_more_bits` rule and the QK_K fallback are likewise unchanged in substance. Not re-pinned here.
- slmquant's model set was read from the arXiv HTML as SmolLM2-135M and Qwen2.5-0.5B. If the
  paper has further sub-billion models the chapter's cells are unaffected (all are sub-billion).
- The GPTQ arXiv PDF could not be read by WebFetch (binary stream); it was downloaded and converted
  with pdftotext, and the §4 passages quoted above are from that text. Same route for the ACL PDFs
  of kurtic2025 and massive and for the Qin PDF; every figure in section 3 was read from the
  converted text, not from a summary.
- Nothing was COULD NOT ACCESS.

## 7. Counts

Citation sheet (57 rows): SUPPORTS 53 / PARTIAL 4 (rows 4, 25, 37, 39) / DOES NOT SUPPORT 0 /
COULD NOT ACCESS 0. Of the 53 SUPPORTS, 27 reuse an issue-02 verdict on unchanged text and were
re-read against the source this round.

Uncited prose claims about the cited studies (6): SUPPORTS 1 / PARTIAL 2 / DOES NOT SUPPORT 3.

Numbers quoted from papers: 19 of 19 found at the stated value (plus the six duplicates in the
l.264 cell); one attribution wrong (l.131), one understatement (l.48).
