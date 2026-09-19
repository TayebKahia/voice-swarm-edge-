# Verified rows for `tab:soa-slu` -- ATIS, SNIPS, SLURP

Verified 2026-09-25 against primary pages only. Sources opened: ACL Anthology record and PDF
for H90-1021; LDC catalog LDC93S4B; arXiv abstract, arXiv HTML and arXiv PDF (v3) for
1805.10190; arXiv abstract and PDF (v1) plus ACL Anthology record 2020.emnlp-main.588 for
SLURP; arXiv abstract 2204.08582 for the MASSIVE lineage sentence. PDFs were read through
`pdftotext`; quotes below are verbatim from that text, with the section or table named. Page
numbers for locations are the printed page numbers of each PDF.

Status vocabulary: **VERIFIED** = read on the primary page, quote given. **NOT ESTABLISHED** =
the primary page does not state it; the table cell gets `---`. Nothing in this file comes from
the candidate notes or from a secondary source.

Column meaning, from the existing table (ch3_state_of_the_art.tex lines 264-269): Work | Kind |
Formulation and models | Metrics reported | Hardware and latency budget | Output constraint.
The MASSIVE row is the register to match: numbers only where the source states them, `\gls{em}`
for exact match, `\glspl{gpu}`, `---` for a property not established.

Glossary keys that exist in the thesis and are used below: `cpu`, `gpu`, `em`, `wer`. There is
no `crf`, `nlu` or `asr` acronym defined, so the draft cells spell those words out.

---

## 1. ATIS -- Hemphill, Godfrey, Doddington 1990 (H90-1021; LDC93S4B)

### (a) Bib metadata as read

| field | value | source |
|---|---|---|
| title | The ATIS Spoken Language Systems Pilot Corpus | Anthology record; PDF title block |
| authors | Charles T. Hemphill, John J. Godfrey, George R. Doddington | Anthology record; PDF (affiliation: Texas Instruments Incorporated, Dallas) |
| booktitle | Speech and Natural Language: Proceedings of a Workshop Held at Hidden Valley, Pennsylvania, June 24-27, 1990 | Anthology record |
| year | 1990 | Anthology record |
| pages | 96--101 | **printed page numbers on the PDF only**; the Anthology record shows no page field |
| DOI | none shown | Anthology record ("DOI: Not listed") |
| abstract | present in the PDF; not shown on the Anthology record | PDF, p. 96 |
| Anthology BibTeX key | `hemphill-etal-1990-atis` | Anthology record |

LDC record (a *distribution*, not the paper): catalog title "ATIS0 Pilot", LDC93S4B, 1993,
authors listed as Hemphill, Godfrey, Doddington, Garofolo, Fiscus, Dahlgren, Fisher, Tjaden,
Pallett. Do not merge the two author lists; cite the paper by its three authors.

### (b) Fact table

| column | value | status | quote and location |
|---|---|---|---|
| Kind | Corpus (pilot); wizard-of-Oz data collection, no system | VERIFIED | "We describe the Air Travel Information System (ATIS) pilot corpus, a corpus designed to measure progress in Spoken Language Systems that include both a speech and natural language component." (Abstract, p. 96). "To collect the kind of English expected in a real working system, we simulate one." (Introduction, p. 96) |
| Domain | air-travel queries against a relational database built from the Official Airline Guide | VERIFIED | "The ATIS database consists of data obtained from the Official Airline Guide (OAG, 1990), organized under a relational schema. ... It contains information about flights, fares, airlines, cities, airports, and ground services" (Introduction, p. 96) |
| Spoken? | yes; spontaneous speech, two microphones, office environment | VERIFIED | "Instead of being read, the speech has many of the characteristics of spontaneous spoken language" and "The speech collection occurs in an office environment rather than a sound booth." (Introduction, p. 96). "a head-mounted Sennheiser (HMD 410-6) microphone. A desk mounted Crown (PCC-160 phase coherent cardioid) microphone was also used" (Session Introduction, p. 97). LDC page: 16 kHz, 16-bit, "close-talking and desk-top" microphones |
| Number of utterances (paper) | 1,041 utterances, 41 sessions, 8 weeks; 740 judged evaluable | VERIFIED | "Forty-one sessions containing 1041 utterances were collected over 8 weeks" (Results, p. 100; Table 1). "Of the 1041 utterances collected, 740 were judged evaluable according to the June 1990 criteria" (Results, p. 100; Table 3) |
| Number of utterances (LDC release) | 912 utterances, 36 speakers, about four hours | VERIFIED (LDC page) | "ATIS0 Pilot is comprised of about four hours of spontaneous speech, read speech and other material"; "36 speakers (24 male, 12 female)"; "912 utterances total" (LDC93S4B catalog page). **The paper's 1,041 and the LDC's 912 differ**; if a count goes in the row, say which one and from where. |
| Intents and slots defined by the paper? | **No.** Annotation is transcriptions, a query classification, reference SQL and reference answer tuples. The words "intent" and "slot" do not occur in the paper. | VERIFIED (absence) | "The ATIS corpus comprises the acoustic speech data for a query, transcriptions of that query, a set of tuples that constitute the answer, and the SQL expression for the query that produced the answer tuples." (Introduction, p. 96). "each query received a classification ... context-dependent/context-removable/context-independent ... ambiguous (vague)/clear ... unanswerable/answerable ... ill-formed (grossly)/well-formed ... noncooperative/cooperative" (Classification, p. 99). "The pilot corpus includes the ANSI-standard SQL expression that produced the reference answer" (Reference SQL, p. 99). |
| Intent / slot counts | --- | NOT ESTABLISHED | The paper states none. The intent/slot labelling of ATIS used by later NLU papers is a later convention and must not be attributed to H90-1021 or sourced from a secondary page. |
| Metrics reported | none for understanding; session statistics and evaluable yield only | VERIFIED | Tables 1-3 (p. 100) report utterances per session, minutes, seconds per answer, queries per hour, and "Session Yield of Evaluable Utterances" ("the yield would increase from 71% to 80%"). Table 4 is a questionnaire tally. No recognition or understanding accuracy is reported. |
| Hardware and latency budget | --- (none; the "system" is two human wizards) | NOT ESTABLISHED as a budget | Only simulation timing: "Typically, the subject received the typed transcription a few seconds after speaking and the answer approximately 20 seconds later." (Session Queries, p. 98); "Some subjects defined an acceptable response time as under 5 seconds." (Results, p. 100). These are observations, not a budget. The only hardware named is "a spare-station cpu and disk to replicate office noise" (p. 97). |
| Output constraint | --- | NOT ESTABLISHED | No parser or output format is proposed; answers are produced by the wizard with NLParse, "a natural language-oriented command language to produce an SQL expression" (p. 97). |

### (c) Draft row

```latex
ATIS~\cite{atis1990} & Corpus & Air-travel queries to a relational database; 1{,}041 spontaneous spoken utterances from 41 wizard-of-Oz sessions, annotated with reference SQL and answer tuples; no intent or slot labels in the 1990 paper & --- & --- & --- \\
```

Cell-by-cell status: Kind VERIFIED; Formulation VERIFIED (all four numbers/claims quoted above); Metrics `---` because the paper reports no understanding metric (the cell could instead read "None; session statistics only", both are true); Hardware `---`; Output constraint `---`.

Alternative shorter formulation cell if the row is too long: "Air-travel database queries; 1{,}041 spontaneous utterances, annotated with reference SQL; no intent or slot labels".

### (d) Draft bib entry

```bibtex
@inproceedings{atis1990,
  title     = {The {ATIS} Spoken Language Systems Pilot Corpus},
  author    = {Hemphill, Charles T. and Godfrey, John J. and Doddington, George R.},
  booktitle = {Speech and Natural Language: Proceedings of a Workshop Held at
               Hidden Valley, {P}ennsylvania, June 24--27, 1990},
  pages     = {96--101},
  year      = {1990},
  url       = {https://aclanthology.org/H90-1021/}
}
```

The `pages` field is from the printed pagination of the PDF (96-101), not from the Anthology
record, which has no page field; drop it if the author prefers to carry only what the record
shows. No publisher is shown on the record.

---

## 2. SNIPS -- Coucke et al. 2018 (arXiv:1805.10190)

### (a) Bib metadata as read

| field | value | source |
|---|---|---|
| title | Snips Voice Platform: an embedded Spoken Language Understanding system for private-by-design voice interfaces | arXiv abstract page; PDF title block |
| authors | Alice Coucke, Alaa Saade, Adrien Ball, Théodore Bluche, Alexandre Caulier, David Leroy, Clément Doumouro, Thibault Gisselbrecht, Francesco Caltagirone, Thibaut Lavril, Maël Primet, Joseph Dureau | arXiv abstract page (12 authors; affiliation "Snips, Paris, France" on the PDF) |
| year | 2018 | v1 25 May 2018; v3 6 Dec 2018 (arXiv submission history) |
| venue | none; arXiv preprint, no journal-ref | arXiv abstract page: comments "29 pages, 9 figures, 17 tables"; subjects cs.CL, cs.NE; no journal-ref shown |
| eprint / class | 1805.10190, cs.CL | arXiv abstract page |

### (b) Fact table

| column | value | status | quote and location |
|---|---|---|---|
| Kind | embedded SLU system (ASR + NLU) with an in-house open NLU dataset | VERIFIED | "This paper presents the machine learning architecture of the Snips Voice Platform, a software solution to perform Spoken Language Understanding on microprocessors typical of IoT devices." (Abstract). "The Natural Language Understanding component of the platform is already open source" (Section 1, p. 2). |
| Number of intents (in-house dataset) | 7 | VERIFIED | "In June 2017, Snips NLU was evaluated on an in-house dataset of over 16K crowdsourced queries (freely available) distributed among 7 user intents of various complexity: SearchCreativeWork ... GetWeather ... BookRestaurant ... PlayMusic ... AddToPlaylist ... RateBook ... SearchScreeningEvent" (Section 3.3.2, "Evaluation on an in-house open dataset", pp. 13-14) |
| Utterances per intent | 2,242-2,300 per intent (PlayMusic 2300, GetWeather 2300, BookRestaurant 2273, AddToPlaylist 2242, RateBook 2256, SearchCreativeWork 2254, SearchScreeningEvent 2259) | VERIFIED | Table 15, "In-house slot-filling dataset summary", column "Samples" (Appendix, p. 23). **Caution:** these seven numbers sum to 15,884, whereas the text says "over 16K"; state either the per-intent range or the phrase, not a total of your own. |
| Number of slot types | --- | NOT ESTABLISHED | Table 15 lists slot names per intent but the paper never states a slot-type count. Do not count them yourself; the extracted table layout does not pair slots to intents reliably. |
| Models | deterministic regex intent parser, then logistic-regression intent classifier and per-intent linear-chain CRF slot fillers; ASR is a Kaldi-recipe neural acoustic model (nnet-256, 2.6 M parameters, 10 MB) with a domain-adapted language model | VERIFIED | "The NLU Engine calls two intent parsers successively: 1. a deterministic intent parser 2. a probabilistic intent parser" and "Its implementation relies on regular expressions." (Section 3.3.1, p. 12). "The intent classification is implemented with a logistic regression trained on the queries from every intent. The slot-filling step consists in several linear-chain Conditional Random Fields (CRFs) [24], each of them being trained for a specific intent." (Section 3.3.1, p. 12). Table 4 (Section 2.3.2, p. 8): "nnet-256 2.6 10 <1" (params M, size MB, RTF on Raspberry Pi 3). |
| What runs on-device | the whole SLU inference; training on servers | VERIFIED | "Within the Snips ecosystem, the SLU components are trained on servers, but the inference happens directly on the device once the assistant has been deployed - no data from the user is ever collected nor stored." (Section 1.2, p. 2) |
| Metrics: slot F1 | 0.930 (precision 0.946, recall 0.921) averaged over all slots and all intents with 2,000 training queries; 0.790 with 70 | VERIFIED | Table 7, "Precision, recall and F1-score averaged on all slots and on all intents of an in-house dataset, run in June 2017", row "Snips" (p. 15). "The main metric used in this benchmark is the average F1-score of slot filling on all slots." (Section 3.3.2, p. 14) |
| Metrics: intent accuracy | --- on the in-house set (evaluation deliberately per-intent) | NOT ESTABLISHED | "In this experiment, the comparison is done separately on each intent to focus on slot filling (rather than intent classification)." (Section 3.3.2, p. 14). The Braun et al. comparison (Table 6) uses "the average F1-score of intent classification and slot filling"; its numbers were not read for this pass, so do not quote them. |
| Metrics: exact / full-frame match | --- | NOT ESTABLISHED | No sentence-level or full-frame accuracy appears in Sections 3.3.2-3.3.3 or Tables 6-8. |
| Metrics: ASR | \gls{wer} 7.6 / 19.6 % (nnet-256, test-clean / test-other) | VERIFIED | Table 3, "Decoding accuracy of neural networks of different sizes (Word Error Rate, %)", row "nnet-256 7.3 19.2 7.6 19.6" (Section 2.3.1, p. 8). The test-set name is not stated in that passage; quote the column headers, not a corpus name. |
| Hardware | Raspberry Pi 3 (1.4 GHz CPU, 1 GB RAM) as reference; also IMX.7D, i.MX8M, DragonBoard 410c, Jetson TX2, Android 5+ ARM, iOS 11+ | VERIFIED | "Its embedded inference runs on common IoT hardware as light as the Raspberry Pi 3 (CPU with 1.4 GHz and 1GB of RAM), a popular choice among developers and therefore our reference hardware setting throughout this paper. Other Linux boards are also supported, such as IMX.7D, i.MX8M, DragonBoard 410c, and Jetson TX2. The Snips SDK for Android works with devices with Android 5 and ARM CPU, while the iOS SDK targets iOS 11 and newer." (Section 1.2, p. 2) |
| Latency figure | NLU inference 60.32 ms on Raspberry Pi 3, 220.02 ms on Raspberry Pi Zero (1.26 ms MacBook Pro 2.5 GHz, 2.12 ms iPhone 6s); ASR real-time factor < 1 on Pi 3 | VERIFIED | Table 8, "Inference runtimes of the Snips NLU Rust pipeline, in milliseconds" (Section 3.3.3, p. 16). Table 4 RTF "<1" for nnet-256 (p. 8). "The SLU components run faster than real time on a single core on a Raspberry Pi 3, as well as on the smaller NXP imx7D." (Section 4, p. 16) |
| Latency *budget* | none stated; the criterion is real-time factor below 1 | VERIFIED (absence of a budget) | "We trained models with various sizes enjoying a faster-than-real-time processing factor, to account for additional processing time (necessitated e.g. by the LM decoding or the NLU engine)" (Section 2.3.2, p. 8). No millisecond budget is set. |
| Output constraint | NLU output is structured by construction (regex patterns first, then classifier + CRF taggers; no generation); the ASR language model embeds entity grammars | VERIFIED | Regex: "The queries contained in the training data are used to build patterns covering all combinations of entity values." (Section 3.3.1, p. 12). ASR: "a generative grammar describing the construction of any instance of the entity" (Section 3.2, p. 9, on the entity transducers of the class-based LM). |

### (c) Draft row

```latex
Snips~\cite{snips2018} & System and corpus & Seven intents, 2{,}242--2{,}300 crowdsourced queries each; regex intent parser, then a logistic-regression classifier and per-intent CRF slot fillers & Slot F1 0.930 averaged over slots and intents; no intent accuracy or \gls{em} on that set & Raspberry~Pi~3 \gls{cpu} (1.4~GHz, 1~GB); language-understanding inference 60~ms; real-time factor below 1, no stated budget & Regex patterns, then classifier and CRF taggers; entity grammars in the speech-recognition language model \\
```

Cell-by-cell status: Kind VERIFIED; Formulation VERIFIED (7 intents, per-intent range, three model components); Metrics VERIFIED (0.930) with the two negatives VERIFIED as absences; Hardware VERIFIED (Pi 3 spec, 60.32 ms rounded to 60, RTF < 1); Output constraint VERIFIED as a description. If the last cell reads as too strong, the honest minimum is "Classifier and CRF output (no generation)". Note the Kind cell: SNIPS is first a system, second a corpus; "System and corpus" keeps that order and differs from MASSIVE's "Corpus and baselines" on purpose.

### (d) Draft bib entry

```bibtex
@misc{snips2018,
  title     = {Snips Voice Platform: an embedded Spoken Language Understanding
               system for private-by-design voice interfaces},
  author    = {Coucke, Alice and Saade, Alaa and Ball, Adrien and Bluche, Th{\'e}odore and
               Caulier, Alexandre and Leroy, David and Doumouro, Cl{\'e}ment and
               Gisselbrecht, Thibault and Caltagirone, Francesco and Lavril, Thibaut and
               Primet, Ma{\"e}l and Dureau, Joseph},
  year      = {2018},
  eprint    = {1805.10190},
  archivePrefix = {arXiv},
  primaryClass = {cs.CL},
  url       = {https://arxiv.org/abs/1805.10190}
}
```

Style note: `qin2021` in references.bib carries `eprint`, `archivePrefix` and `url` but no
`primaryClass`; drop `primaryClass` if strict consistency with that entry is wanted.

---

## 3. SLURP -- Bastianelli, Vanzo, Swietojanski, Rieser 2020 (EMNLP 2020)

### (a) Bib metadata as read

| field | value | source |
|---|---|---|
| title | SLURP: A Spoken Language Understanding Resource Package | Anthology record; arXiv abstract; PDF title block |
| authors | Emanuele Bastianelli, Andrea Vanzo, Pawel Swietojanski, Verena Rieser | Anthology record; arXiv abstract (affiliations on PDF: Heriot-Watt University; University of New South Wales) |
| booktitle | Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP) | Anthology record |
| Anthology ID | 2020.emnlp-main.588 | Anthology record -- **confirmed** |
| DOI | 10.18653/v1/2020.emnlp-main.588 | Anthology record -- **confirmed** |
| pages | 7252--7262 | Anthology record |
| month / location / publisher | November 2020, Online, Association for Computational Linguistics | Anthology record |
| arXiv | 2011.13205 (v1, 26 Nov 2020); comments "Published at the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP-2020)" | arXiv abstract page |

### (b) Fact table

| column | value | status | quote and location |
|---|---|---|---|
| Kind | corpus (audio + text) with pipeline baselines and a new metric | VERIFIED | "we release SLURP, a new SLU package containing the following: (1) A new challenging dataset in English spanning 18 domains ... (2) Competitive baselines based on state-of-the-art NLU and ASR systems; (3) A new transparent metric for entity labelling" (Abstract) |
| Recordings | ~72k audio recordings; 72,277 audio files (34,603 close-range, 37,674 far-range); ~58 hours; 177 speakers | VERIFIED | "SLURP is a collection of ~72k audio recordings of single turn user interactions with a home assistant" (Section 1, p. 1). Table 2, "Audio file statistics", column SLURP: "Speakers 177; Audio files 72,277; Close range 34,603; Far range 37,674; Duration [hrs] 58" (Section 3.3, p. 3). "After filtering, SLURP comprises ~58 hours of acoustic material." (Section 3.2, p. 3) |
| Distinct sentences | 17,181 (lexicalised) | VERIFIED | Table 3, "Analysis of Lexical diversity and sophistication", row "Sentences", SLURP LEX column: 17,181 (Section 3.3, p. 4) |
| Scenarios / actions / entity types | 18 scenarios; 46 actions; entity types stated as **55 in the text and 56 in Table 4** | VERIFIED with discrepancy | "including over 18 different scenarios, with 46 defined actions and 55 different entity types" (Section 1, p. 1). Table 4, "Semantic analysis of the number of scenarios, actions and entity types", SLURP column: "Scenarios 18; Actions 46; Entities 56" (Section 3.3, p. 4). **The paper contradicts itself on 55 vs 56.** MASSIVE (which localises SLURP) states 55 slots. For the row, write "55 entity types" only if you accept the intro sentence over the table, or write "55--56" and footnote the discrepancy; the safest cell is "18 scenarios, 46 actions" and leave the entity count to MASSIVE's row. |
| Intents | --- as a count. Intent = scenario and action taken together; the paper never gives a number of scenario-action pairs. | NOT ESTABLISHED (count) / VERIFIED (definition) | "each sentence is annotated with one scenario and one action" (Section 3.3, p. 4). "we generate another combined semantic layer, Scen_Act, to feed SF-ID with a label composed by the concatenation Scenario and Action." (Section 5.2, p. 6). MASSIVE's 60 intents is MASSIVE's own count, not SLURP's. |
| Audio included; how recorded | yes; read prompts, far-field microphone array plus close-talking headset for some users; home/office conditions | VERIFIED | "We asked 100+ participants to read out the collected prompts on a tablet ... Speech was captured at distance with a microphone array, but some users were also equipped with a close-talking headset microphone" (Section 3.1, p. 2). Also: "SLURP was collected for developing an in-home personal robot assistant (Miksik et al., 2020)." (Section 3.1, p. 2) |
| Baselines: models | NLU: HerMiT (self-attention + BiLSTM + CRF, top-down scenario/action/entity) and SF-ID (BiLSTM encoder + CRF tagger); ASR: Multi-ASR (Kaldi TDNN, 24,000 h), Google-ASR, SLURP-ASR (in-domain), Multi-ASR adapted to SLURP | VERIFIED | "We evaluate SLURP against two state-of-the-art NLU models: HerMiT (Vanzo et al., 2019) and SF-ID (E et al., 2019)." "HerMiT's architecture is a hierarchy of self-attention mechanisms and Bidirectional Long Short-Term Memory (BiLSTM) encoders followed by Conditoinal Random Field (CRF) tagging layers." "SF-ID's architecture is also based on attention, using a BiLSTM encoder and CRF tagger." (Section 5.2, p. 6). "Both are built with the Kaldi ASR toolkit ... a time-delay neural network acoustic model (Peddinti et al., 2015) is trained on 24,000 hours of augmented audio material" (Section 5.1, p. 5) |
| Baselines: sizes | --- | NOT ESTABLISHED | No parameter count for HerMiT or SF-ID appears anywhere in the paper (grep for "param", "million": only the unrelated "parameters are not logged with the dataset"). |
| Pipeline vs end-to-end | pipeline (ASR then NLU); end-to-end systems were tried and did not converge | VERIFIED | "We finally combine ASR and NLU, implementing several SLU pipelines." (Section 5, p. 5). "We have tested several SOTA E2E-SLU systems on SLURP, including (Lugosch et al., 2019b) ... However, re-training these models on this more complex domain did not converge or result in meaningful outputs." (Section 7, p. 8-9). "We show that SOTA modular approaches are able to provide a strong baseline for this challenging data, which has yet to be met by SOTA E2E systems." (Section 7, p. 9) |
| Metrics reported | scenario accuracy, action accuracy, combined Scen_Act accuracy; entity Word-F1, Char-F1, SLU-F1 and span F1 | VERIFIED | Table 7, "System accuracy of Scenario and Action", columns "Scenario Action Scen_Act" (Section 5.2, p. 6). Table 8, "System performance on entity prediction", columns "Word-F1 Char-F1 SLU-F1 F1" (Section 5.2, p. 7). SLU-F1 definition: "SLU-F1 combines span-based F1 evaluation with a text-based distance measure dist, e.g. WER." and "we combine Word-F1 and Char-F1 in a single number SLU-F1" (Section 4, pp. 4-5) |
| Headline numbers | gold text + HerMiT: scenario 90.15, action 86.99, Scen_Act 84.84 (Table 7); entity F1 78.19 (Table 8). Best from audio, Multi-ASR adapted to SLURP + HerMiT: 85.69 / 81.42 / 78.33 (Table 7); SLU-F1 70.84 (Table 8); \gls{wer} 16.2 (Table 5, "Multi-ASR + Adapt w/ SLURP", Test) | VERIFIED | Table 7 rows "Gold/HerMiT 90.15 86.99 84.84" and "Multi-SLURP/HerMiT 85.69 81.42 78.33" (p. 6). Table 8 rows "Gold/HerMiT -- -- -- 78.19" and "Multi-SLURP/HerMiT 69.34 72.39 70.84 64.16" (p. 7). Table 5 row "Multi-ASR + Adapt w/ SLURP 16.3 16.2" (p. 5). Abstract gives no numbers. |
| Full-frame / exact match | --- as a reported figure. The paper defines the standard E2E-SLU "accuracy" (all slots together) but reports no such figure of its own; Scen_Act accuracy covers intent only, not entities. | NOT ESTABLISHED (as reported); VERIFIED (definition) | "The standard metric for evaluating E2E-SLU is accuracy, which is defined as 'the accuracy of all slots for an utterance taken together -- that is, if the predicted intent differs from the true intent in even one slot, the prediction is deemed incorrect' (Lugosch et al., 2019b). However, this notion of accuracy is problematic when it comes to evaluating entities" (Section 4, p. 4). No table has such a column. |
| Hardware | --- | NOT ESTABLISHED | No occurrence of GPU, CPU, hardware, latency or Tesla in the text. |
| Latency budget | --- | NOT ESTABLISHED | None stated. |
| Output constraint | --- | NOT ESTABLISHED | None described; the NLU baselines are classifier/CRF taggers, but the paper does not frame that as a constraint. |

### (c) Draft row

```latex
SLURP~\cite{slurp2020} & Corpus and baselines & 18 scenarios and 46 actions, one of each per utterance; 72{,}277 recordings of 17{,}181 sentences; pipeline baselines of Kaldi speech recognition and BiLSTM--CRF language understanding & Scenario, action and scenario-action accuracy 90.2, 87.0 and 84.8\% on reference text; entity SLU-F1 70.8\% from audio; no \gls{em} & --- & --- \\
```

Cell-by-cell status: Kind VERIFIED; Formulation VERIFIED (18, 46, 72,277, 17,181, model families; entity-type count omitted because of the 55/56 conflict -- add "55 entity types" only with a footnote); Metrics VERIFIED (90.15, 86.99, 84.84 rounded to one decimal; 70.84 rounded; "no \gls{em}" VERIFIED as an absence); Hardware `---`; Output constraint `---`. If the metrics cell should stay unrounded like MASSIVE's, write 90.15, 86.99, 84.84 and 70.84.

### (d) Draft bib entry

```bibtex
@inproceedings{slurp2020,
  title     = {{SLURP}: A Spoken Language Understanding Resource Package},
  author    = {Bastianelli, Emanuele and Vanzo, Andrea and Swietojanski, Pawel and
               Rieser, Verena},
  booktitle = {Proceedings of the 2020 Conference on Empirical Methods in Natural
               Language Processing (EMNLP)},
  pages     = {7252--7262},
  year      = {2020},
  publisher = {Association for Computational Linguistics},
  doi       = {10.18653/v1/2020.emnlp-main.588},
  url       = {https://aclanthology.org/2020.emnlp-main.588/}
}
```

---

## 4. MASSIVE lineage sentence

VERIFIED. arXiv:2204.08582 abstract: "MASSIVE was created by tasking professional translators
to localize the English-only SLURP dataset into 50 typologically diverse languages from 29
genera." Also: "MASSIVE contains 1M realistic, parallel, labeled virtual assistant utterances
spanning 51 languages, 18 domains, 60 intents, and 55 slots." A sentence of the form "SLURP is
the English parent that MASSIVE localises into 50 further languages" is supportable from the
MASSIVE abstract alone. Note the 18 domains of MASSIVE match SLURP's 18 scenarios; the 60
intents and 55 slots are MASSIVE's counts and should be cited to `massive`, not `slurp2020`.

---

## Cautions

1. **SNIPS ownership boundary.** arXiv:1805.10190 is an on-device SLU system whose selling
   point is exactly the property this thesis's last row claims for itself: inference on a
   Raspberry-class board, faster than real time, private by design. The table row may state the
   verified facts (Pi 3, 60 ms, RTF < 1, classifier + CRF), because the table's purpose is to
   put prior work on the same axes and a reader would rightly ask why an embedded SLU paper is
   absent. The *prose* should not claim that this work is the first to run intent-and-slot
   parsing on a Raspberry Pi, or the first with a hardware budget; SNIPS did it in 2018 with
   classical models. What remains this work's own, and what the critical-comparison paragraph
   can say, is: a *generative decoder* (not a classifier/CRF) under a *stated millisecond
   budget* (SNIPS states runtimes but sets no budget), with a *grammar on the output* (SNIPS
   constrains by construction, not by decoding), and with \gls{em} reported (SNIPS reports slot
   F1 only). The sentence "the last row is the only one with a hardware and latency budget" at
   line 282-283 survives only because SNIPS has no *budget*; if SNIPS enters the table, that
   sentence must be re-read against the new row, and "the only one whose output is
   constrained" must be qualified, since SNIPS's regex parser is an output constraint of a
   kind. Whether the embedded-deployment comparison belongs in this thesis or in the companion
   Ingenieur document is the author's call; the candidate notes flag it as the latter.

2. **ATIS has no intents or slots in the primary source.** The intent/slot version of ATIS
   used since the 2010s is a later relabelling. The row must not carry intent or slot counts
   for ATIS, and the prose must not say the 1990 paper "labelled intents". What ATIS supports
   is the *age* of the utterance-to-structure formulation (1990) and the fact that it was
   spoken and spontaneous.

3. **Two utterance counts for ATIS.** The paper: 1,041 collected, 740 evaluable. The LDC
   release: 912. Cite one and say which. The draft row uses the paper's 1,041.

4. **SLURP 55 vs 56 entity types.** The intro says 55, Table 4 says 56. The draft row omits
   the entity count; if added, footnote the discrepancy. MASSIVE's 55 slots is a separate,
   consistent statement from a different paper.

5. **SLURP intents.** No intent count is stated. Do not write "60 intents" for SLURP; that is
   MASSIVE's count. Do not derive 18 x 46 either; scenario-action pairs are not a product.

6. **SNIPS "over 16K" vs Table 15 sum of 15,884.** Quote either the phrase or the per-intent
   range; do not print a total.

7. **SNIPS is an arXiv preprint with no venue.** The bib entry is `@misc`; do not add a
   conference.

8. **Rounding.** The MASSIVE row prints one decimal (85.1, 73.6, 63.7). The SLURP draft rounds
   90.15 to 90.2 etc. to match; the SNIPS draft keeps 0.930 because the paper reports F1 as a
   fraction, not a percentage. Either convention is defensible; pick one for the whole table.

9. **Glossary.** No `crf`, `nlu` or `asr` acronym exists; the drafts spell them out. If the
   author adds keys, replace the words.
