# Master's thesis -- candidate references for ch2 "Spoken-language understanding for robotics"

Compiled 2026-09-23. This file covers the one `\TODO` in `thesis/master/ch2_related_work.tex`
§`sec:slu-robotics`: the opening sentence claims intent-and-slot parsing is "a long-settled task
shape in spoken-language understanding", but currently cites only `massive` --- a dataset, which
evidences the shape by example and not the lineage. Every entry below is an **UNVERIFIED
CANDIDATE**: the author must open the listed primary page, re-read the author list, title and
venue, and confirm the claim it is being asked to carry before adding anything to
`thesis/references.bib`. Nothing here has been written into `thesis/`.

Ordered by how load-bearing each is for the sentence that needs support. Entries 1--3 support the
claim *directly* (they assert the task shape is standard); entries 4--11 support it *by example*
(corpora and models built around the shape). Read "Notes for the author" at the bottom before use.

---

## Tier 1 --- Surveys that state the task shape is settled

These are the citations that actually do the work. A survey saying "this is the standard
formulation" backs the sentence; a dataset built on the formulation only illustrates it.

### A Survey on Spoken Language Understanding: Recent Advances and New Frontiers
- Authors (as shown on page): Libo Qin, Tianbao Xie, Wanxiang Che, Ting Liu
- Venue / year: IJCAI 2021 (arXiv listing states "Accepted at IJCAI2021")
- Identifier: arXiv:2103.03095
- Page fetched: https://arxiv.org/abs/2103.03095
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim: the abstract opens by defining the field's object as fixed and
  uncontroversial --- SLU "aims to extract the semantics frame of user queries, which is a core
  component in a task-oriented dialog system" --- and its stated taxonomy is organised around
  "single model vs. joint model", i.e. the joint intent/slot formulation is the axis the field is
  classified along, not a proposal under debate.

### A survey of joint intent detection and slot-filling models in natural language understanding
- Authors (as shown on page): H. Weld, X. Huang, S. Long, J. Poon, S. C. Han
- Venue / year: arXiv preprint, 2021 (comments line reads only "33 pages"; no journal-ref shown on
  the arXiv abstract page --- see Notes, this may since have appeared in a journal)
- Identifier: arXiv:2101.08091
- Page fetched: https://arxiv.org/abs/2101.08091
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim: this is the lineage citation in the most literal sense --- the abstract
  narrates the field's own history as a progression, "Traditionally the two tasks have been deemed
  to proceed independently. However, more recently, joint models for intent classification and slot
  filling have achieved state-of-the-art performance", which is exactly the "long-settled" arc the
  thesis sentence asserts.

### Recent Neural Methods on Slot Filling and Intent Classification for Task-Oriented Dialogue Systems: A Survey
- Authors (as shown on page): Samuel Louvan, Bernardo Magnini
- Venue / year: COLING 2020 (arXiv comments line states "COLING 2020")
- Identifier: arXiv:2011.00564
- Page fetched: https://arxiv.org/abs/2011.00564
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim: the abstract treats the two tasks as the settled decomposition of
  task-oriented NLU and surveys only the *architectures* used on them, sorting the literature into
  "independent model, which model SF and IC separately, joint models, which exploit the mutual
  benefit of the two tasks simultaneously, and transfer learning models" --- the shape is the
  premise, the modelling is the variable.

---

## Tier 2 --- The canonical benchmark corpora that predate MASSIVE

### The ATIS Spoken Language Systems Pilot Corpus
- Authors (as shown on page): Charles T. Hemphill, John J. Godfrey, George R. Doddington
- Venue / year: Speech and Natural Language: Proceedings of a Workshop Held at Hidden Valley,
  Pennsylvania, June 24--27, 1990
- Identifier: ACL Anthology ID H90-1021 (no DOI shown on the anthology page)
- Page fetched: https://aclanthology.org/H90-1021/
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim: **the anthology page shows no abstract** --- the record establishes date and
  authorship only. The quotable description comes from the LDC distribution page for the same
  corpus (https://catalog.ldc.upenn.edu/LDC93S4B, fetched, catalog no. LDC93S4B, 1993), which says
  the collection "was developed to support the research and development of speech understanding
  systems". Cite this for the *age* of the task --- 1990, thirty-odd years before MASSIVE --- and
  verify the quotation route before relying on it.

### Snips Voice Platform: an embedded Spoken Language Understanding system for private-by-design voice interfaces
- Authors (as shown on page): Alice Coucke, Alaa Saade, Adrien Ball, Théodore Bluche, Alexandre
  Caulier, David Leroy, Clément Doumouro, Thibault Gisselbrecht, Francesco Caltagirone, Thibaut
  Lavril, Maël Primet, Joseph Dureau
- Venue / year: arXiv preprint, 2018 (submitted 25 May 2018, last revised 6 Dec 2018)
- Identifier: arXiv:1805.10190
- Page fetched: https://arxiv.org/abs/1805.10190
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim: SNIPS is the second half of the ATIS/SNIPS benchmark pair every joint model
  below reports on; it is also the closest prior art to this thesis's *constraint*, describing SLU
  performed "on microprocessors typical of IoT devices" with models "small enough to run in
  real-time on small devices" --- useful, but see Notes on the ownership boundary.

### SLURP: A Spoken Language Understanding Resource Package
- Authors (as shown on page): Emanuele Bastianelli, Andrea Vanzo, Pawel Swietojanski, Verena Rieser
- Venue / year: EMNLP 2020 (arXiv listing states "Published at EMNLP-2020")
- Identifier: arXiv:2011.13205
- Page fetched: https://arxiv.org/abs/2011.13205
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim: SLURP is MASSIVE's direct parent --- MASSIVE's own abstract says it was made
  by localizing "the English-only SLURP dataset" into 50 languages. Citing SLURP alongside MASSIVE
  turns a single data point into a two-step lineage, and its abstract states the motivation that
  the corpora exist because "publicly available SLU resources are limited", not because the task
  shape was in question.

---

## Tier 3 --- Models establishing JOINT intent classification + slot filling as the task formulation

### Attention-Based Recurrent Neural Network Models for Joint Intent Detection and Slot Filling
- Authors (as shown on page): Bing Liu, Ian Lane
- Venue / year: Interspeech 2016 (arXiv comments line states "Accepted at Interspeech 2016")
- Identifier: arXiv:1609.01454
- Page fetched: https://arxiv.org/abs/1609.01454
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim: the abstract frames the two tasks as already-given components, "both of which
  are critical steps for many speech understanding and dialog systems", and reports joint training
  gains over separate models on ATIS --- the paper most often cited as fixing the joint formulation
  in the neural era.

### Multi-Domain Joint Semantic Frame Parsing Using Bi-Directional RNN-LSTM
- Authors (as shown on page): Dilek Hakkani-Tür, Gokhan Tur, Asli Celikyilmaz, Yun-Nung Chen,
  Jianfeng Gao, Li Deng, Ye-Yi Wang
- Venue / year: Interspeech 2016, pages 715--719
- Identifier: doi:10.21437/Interspeech.2016-402
- Page fetched: https://www.isca-archive.org/interspeech_2016/hakkanitur16_interspeech.html
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim: this is the paper that names the output object the thesis is producing --- an
  "RNN-LSTM architecture for joint modeling of slot filling, intent determination, and domain
  classification", estimating a complete *semantic frame* per utterance. That "one intent plus a
  set of slot values" is a single structured output, not two separate predictions, is precisely the
  shape the thesis says it inherited.

### Slot-Gated Modeling for Joint Slot Filling and Intent Prediction
- Authors (as shown on page): Chih-Wen Goo, Guang Gao, Yun-Kai Hsu, Chih-Li Huo, Tsung-Chieh Chen,
  Keng-Wei Hsu, Yun-Nung Chen
- Venue / year: NAACL-HLT 2018, Volume 2 (Short Papers), pages 753--757
- Identifier: doi:10.18653/v1/N18-2118
- Page fetched: https://aclanthology.org/N18-2118/
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim: its abstract opens by treating the joint formulation as the incumbent ---
  "Attention-based recurrent neural network models for joint intent detection and slot filling have
  achieved the state-of-the-art performance" --- and evaluates on "benchmark ATIS and Snips
  datasets", which is the sentence that establishes those two corpora as *the* standard pair.

### BERT for Joint Intent Classification and Slot Filling
- Authors (as shown on page): Qian Chen, Zhu Zhuo, Wen Wang
- Venue / year: arXiv preprint, 2019 (comments line reads "4 pages, 1 figure"; no venue stated)
- Identifier: arXiv:1902.10909
- Page fetched: https://arxiv.org/abs/1902.10909
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim: shows the task shape surviving the architectural shift to pre-trained
  transformers unchanged --- the abstract still opens "Intent classification and slot filling are
  two essential tasks for natural language understanding" and reports the same three metrics the
  thesis uses, "intent classification accuracy, slot filling F1, and sentence-level semantic frame
  accuracy". This is the bridge between the RNN-era formulation and the LLM the thesis fine-tunes.

---

## Tier 4 --- Intent-and-slot parsing for robot command interfaces (optional, lowest priority)

### HuRIC: a Human Robot Interaction Corpus
- Authors (as shown on page): Emanuele Bastianelli, Giuseppe Castellucci, Danilo Croce, Luca Iocchi,
  Roberto Basili, Daniele Nardi
- Venue / year: LREC 2014 (Proceedings of the Ninth International Conference on Language Resources
  and Evaluation), pages 4519--4526
- Identifier: ACL Anthology ID L14-1440 (no DOI shown on the anthology page)
- Page fetched: https://aclanthology.org/L14-1440/
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim: backs the section's *second* sentence rather than its first --- that robot
  command parsing inherits the utterance-to-structure shape. The corpus is "audio files paired with
  their transcriptions referring to commands for a robot, e.g. in a home environment", annotated so
  the representation "can be easily translated into the internal representation of the robot",
  which is structurally the thesis's own pipeline minus the flight controller.

---

## UNVERIFIED --- could not fetch a primary page

IEEE Xplore, the ACM Digital Library and Wiley Online Library all refused the fetch (403 /
connection refused) during this pass. The three records below are **search-derived**: author lists
and page numbers have NOT been read off a primary page and must be reconstructed from the
publisher's own record before use. Listed because each would be genuinely load-bearing if verified.

### Using Recurrent Neural Networks for Slot Filling in Spoken Language Understanding
- Authors (SEARCH-DERIVED, unverified): Grégoire Mesnil, Yann Dauphin, Kaisheng Yao, Yoshua Bengio,
  Li Deng, Dilek Hakkani-Tür, Xiaodong He, Larry Heck, Gokhan Tur, Dong Yu, Geoffrey Zweig
  (author *order* is uncertain --- the search result and the ACM record disagree)
- Venue / year: IEEE/ACM Transactions on Audio, Speech, and Language Processing, vol. 23 no. 3, 2015
- Identifier: doi:10.1109/TASLP.2014.2383614
- Page attempted: https://ieeexplore.ieee.org/document/6998838 (empty response),
  https://dl.acm.org/doi/10.5555/2817174.2817185 (HTTP 403)
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim (unverified): the journal-level statement that slot filling on ATIS is the
  field's standard evaluation. Lower priority than the Tier 3 entries because it treats slot filling
  alone, not the joint shape.

### Spoken Language Understanding [An introduction to the statistical framework]
- Authors (SEARCH-DERIVED, unverified): Ye-Yi Wang, Li Deng, Alex Acero
- Venue / year: IEEE Signal Processing Magazine, vol. 22 no. 5, 2005, pages 16--31
- Identifier: doi not confirmed (IEEE record not reachable)
- Page attempted: IEEE Xplore (blocked); only Microsoft Research and Semantic Scholar mirrors were
  returned by search, both of which are secondary and were therefore not used
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim (unverified): would be the *earliest* overview asserting the shape is standard,
  describing SLU as slot-oriented semantic decoding twenty years before MASSIVE. Verify in person;
  if it holds, it pairs with Qin et al. to bracket the lineage at both ends.

### What is left to be understood in ATIS?
- Authors (SEARCH-DERIVED, unverified): Gökhan Tür, Dilek Hakkani-Tür, Larry Heck
- Venue / year: 2010 IEEE Spoken Language Technology Workshop (SLT)
- Identifier: doi not confirmed (IEEE record not reachable)
- Page attempted: IEEE Xplore (blocked)
- Serves: Master ch2 section "Spoken-language understanding for robotics"
- Supports the claim (unverified): reportedly states that error rates below 5% on ATIS for both
  intent determination and slot filling were already standard by 2010 --- the most direct evidence
  available that the task was considered close to saturated long before this thesis. **Do not cite
  from this description**; the claim about the 5% figure came from a search snippet, not a fetched
  abstract, and would be exactly the kind of number that is wrong when reconstructed from memory.

---

## Notes for the author

**If only one citation can be added: Qin, Xie, Che & Liu, arXiv:2103.03095 (IJCAI 2021).** It is
the only fetched-and-verified item that supports the sentence *as written* rather than by example.
The thesis claims the task shape is long-settled; a survey whose abstract calls the semantic frame
"a core component in a task-oriented dialog system" and organises the whole field by whether the
two tasks are modelled jointly is a statement that the shape is settled. A dataset paper, however
large the dataset, can only demonstrate that someone built on the shape.

If two can be added, pair it with **Weld et al. (arXiv:2101.08091)**, which narrates the
independent-to-joint progression explicitly and so carries the word "lineage" better than anything
else here. If three, add **Hemphill et al. (H90-1021)** purely for the date --- the 1990 anchor is
what converts "settled" from an assertion into an interval.

**Suggested repair of the sentence.** As written, `\cite{massive}` sits on a lineage claim it
cannot support. The cheapest correct fix is to split the citation load: put the survey(s) on the
"long-settled" clause and leave `massive` where it already belongs, on the following sentence about
scale and accuracy. The clause "not one this thesis introduces" is the part a reader will check,
and a survey is the only thing that answers it.

**Watch the ownership boundary on SNIPS.** arXiv:1805.10190 is an embedded, on-device SLU system
with privacy-by-design framing --- close enough to this thesis's deployment that citing it for
*that* would encroach on material the thesis owns. Cite it only as the second half of the
ATIS/SNIPS benchmark pair. If it starts doing work in a sentence about running small models on
small hardware, it is in the wrong section.

**On the ACL Anthology and abstracts.** Pre-2000 workshop proceedings (the whole H90-* series) carry
no abstract field in the Anthology. For ATIS this means the standard citation cannot be
claim-checked from the Anthology page alone; the LDC catalog entry (LDC93S4B) was fetched as the
substitute source for a quotable description, and the two records list different author sets --- the
LDC entry adds Garofolo, Fiscus, Dahlgren, Fisher, Tjaden and Pallett. Use the H90-1021 author list
for the paper and do not merge the two.

**What was looked for and not found.**
- *A fetchable primary page for anything on IEEE Xplore.* Every IEEE attempt in this pass returned
  an empty body or a refused connection, which cost three otherwise-strong candidates (Mesnil et al.,
  Wang/Deng/Acero, Tür et al.) their verification. They are in the UNVERIFIED section for that
  reason alone, not because they are doubtful.
- *The Tur & De Mori book*, `Spoken Language Understanding: Systems for Extracting Semantic
  Information from Speech` (Wiley, 2011), would be the textbook-level statement that this task shape
  is canonical --- the strongest possible support for the sentence. The Wiley page returned HTTP 403
  and it is not listed above at all, since nothing about it was verified. Worth one manual attempt
  through a library proxy.
- *A survey specific to robot or drone command parsing* framed in intent/slot terms. Nothing was
  found; the HRI literature that was reachable (HuRIC) uses frame-semantic and AMR annotation rather
  than the flat intent-plus-slots schema, so the thesis's claim that "nothing about that mapping is
  specific to robotics" is, as far as this pass could establish, defensible but not directly
  citable. If a reviewer presses on it, HuRIC is the honest answer: the same utterance-to-structure
  problem, a different structure.
