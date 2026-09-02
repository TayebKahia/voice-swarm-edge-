# Issue 08 -- whole-document review of the Master (Template B), reviewer report

## 1. Header

- Reviewed: `thesis/main_master.tex` as a whole -- title page, dedication, acknowledgements, the
  three abstracts (`master/frontmatter/abstract.tex`, `frabstract.tex`, `arabstract.tex`),
  `shared/acronyms.tex`, Ch1-Ch6 (`master/ch1_introduction.tex` ... `ch6_conclusion.tex`), the
  seven generated tables `\input` by Ch4, `references.bib`, and the built PDF
  (`thesis/build/master/main_master.pdf`, 63 pages) via `pdftotext`.
- Against: `.agents/skills/thesis-writing/SKILL.md`; `prd.md` §2, §3, §3.1, §3.2 + Table 3,
  Table 31; the six pre-review reports `.scratch/thesis-review/reports/master_ch1..6.md`
  (every PASS number taken as recomputed, not redone); the Comments of issues 01-05 and 09
  (decided items not re-raised); `results/exp2_latency_budget.md`, `results/mcnemar.csv`,
  `results/exp3_pi.csv`, `results/exp3_pi_analysis.md`.
- Write-once (item 7) compared against `thesis/ingenieur/ch1..ch6*.tex` as on disk at review time
  (Ch1 full prose; Ch2 scaffold; Ch3 prose through §3.4 "Latency budget", §3.5 `\TODO`; Ch4-Ch6
  scaffolds). Ingénieur Ch3 changed on disk during the review (commits `da5f625`, `e694a12`);
  the current text was re-read.
- Git HEAD: `5ed20ba`. Working tree: `.scratch/thesis-review/reports/master_ch2.md` modified
  (report only); no `thesis/` file modified by this review.
- Review only: no file under `thesis/`, `tools/`, `results/` or `.scratch/` was edited except
  this report. No build was run; the build results given in the task brief are used as is.

## 2. Verdict

Ready after fixes; no rework. The golden thread is intact from RQ1 in Ch1 to its answer in Ch6,
every headline number is identical wherever it appears, the three abstracts carry the same
numbers and (as far as the French and Arabic can be read) the same qualifiers, every
cross-reference lands on a section that does what the text says, and the write-once rule holds
against the Ingénieur as it stands. One MAJOR remains: the method paragraph of all three
abstracts still says the control model "separates model family from size", the claim Ch1 dropped
under issue 03 (V20) and Ch4/Ch6 disown. Five MINORs (a Ch1 promise Ch4 does not keep for three
Ingénieur-sourced timing figures; one deployment fact missing from the scope paragraph; `p95`
used before it is expanded; three names for the golden split; the Intent-F1 requirement
measured but never given a verdict) and five NITs.

## 3. RQ / contribution traceability (Template B items 1 + 2)

Section numbers as printed in the PDF; file:line of the anchoring text.

| Thread | Ch1 stated / claimed | Ch2 positioned | Ch3 operationalised | Ch4 measured | Ch5 interpreted | Ch6 answered |
|---|---|---|---|---|---|---|
| **RQ1** (trade-off, 0.36-1.2 B, quantised, Pi 5) | §1.3 quote block, ch1:92-96 (verbatim prd §2); floor derived §1.1 ch1:26-28 | §2.5 Gap + Delta, ch2:177-205 ("supply the measurements from which Chapter 4 answers RQ1") | §3.3 model set spans the range, ch3:275-277; §3.4 two levels, ch3:373-375; §3.5 selection rule + statistical plan, ch3:620-643; constraints tab:requirements, tab:latency-budget | §4.2 benchmark (accuracy + Pi timing), ch4:66-156; §4.6 tests, ch4:266-308; §4.7 rule applied, ch4:310-396; Fig. 4.1 | §5.1 frontier read, knee, rule vs frontier, thermal axis, gaps, ch5:15-103 | §6.1 direct answer, ch6:17-44 |
| **C1** schema + bounded GBNF grammar (validity a property of the decoder) | §1.4 ch1:107-111; motivated §1.2 ch1:66-72 | Delta, ch2:191-194; mechanism §2.3 ch2:107-117 | §3.1 in full (grammar listing, `num`/`idlist` bounds, 90-char/96-token bound), ch3:10-121 | §4.2 schema validity 1.000 x18, ch4:89-94; §4.5 ablation, ch4:238-264 | §5.2 common-cause hypothesis, ch5:160-180; §5.3.2 "A small schema", ch5:316-327 | §6.2 para 1, ch6:49-58 |
| **C2** label-first dataset pipeline, family splits, round trip, card, tag, sealed pass | §1.4 ch1:112-116 | Delta, ch2:195-197; gap "no existing corpus", ch2:152, 186-187 | §3.2 in full (tab:dataset, splits 96/12/12, leakage gate clean on four axes, conformance, 81 `unknown` pairs, golden set, annotation seal), ch3:123-271 | Indirect: every split scored in §4.2-§4.5 is C2's; zero-shot baseline §4.3 ch4:200-206 is the floor the fine-tune on the corpus is measured from | §5.3.1 "Labels and evaluation splits", ch5:262-272; §5.2 the 81 pairs, ch5:164-167 | §6.2 para 2, ch6:60-68 |
| **C3** quantised-inference harness; cost of the deployment pipeline | §1.4 ch1:117-124 | Delta, ch2:197-202; §2.2 hand-off, ch2:86-89 | §3.4 reference vs deployed surfaces, what the delta does and does not isolate, parity gate, ch3:371-453; §3.5 protocol, ch3:455-509 | §4.2 tab:model-comparison; §4.4 tab:quantisation-delta, ch4:208-236; §4.5 | §5.1 (frontier from its measurements); §5.3.1 parity, untuned baseline, thermal, n, ch5:190-272; §5.3.2 "Models and quantisation levels", ch5:329-334 | §6.2 para 3, ch6:70-78 |

No empty cell. Item 2, both directions:

| Claimed (Ch1 / abstract) | Demonstrated where | Verdict |
|---|---|---|
| C1 as at ch1:107-111 (schema + bounded grammar; layers 2-3 in the Ingénieur) | ch3:10-121; ch4:89-94, 246-255; ch6:49-58 | demonstrated, same scope |
| C2 as at ch1:112-116 (pipeline, family splits, round trip, card, tag `dataset-v1.0`, SHA-256 sealed annotation pass) | ch3:128-137 (label first, card, tag), 180-191 (family splits, gate), 193-198 (round trip), 234-245 (seal) | demonstrated, same scope |
| C3 as at ch1:117-124 (EM, intent/slot F1, schema validity, false-command rate; three of four models, two levels; accuracy under deployed runtime + grammar; throughput on the Pi; pipeline cost) | ch4:69-156, 208-236; ch6:70-78 | demonstrated. The harness also reports safe-failure rate, latency, memory and throttle proportion (ch3:538-540, ch4) that the Ch1/Ch2 metric lists omit -- NIT-2 |
| Abstract l.19-20 "the fourth ... separates model family from size" | ch4:171-177 "measure a family difference at about 0.5 B; they do not express it as a share of a size effect"; ch6:86-88 same; ch1:137-138 "measures a model-family difference at fixed size" | **claimed stronger than demonstrated -- M-1** |
| Demonstrated but not among C1-C3: thermal headroom (ch4:103-119, ch6:76-78) | promised by ch1:33-37 ("every timing figure ... reported with the thermal state") | anchored to RQ1's efficiency axis; acceptable |
| Demonstrated but not among C1-C3: family control (ch4:158-198, ch6:80-88) | promised by ch1:25 and ch1:137-138 | issue 09 MINOR-7 (left as written by the author); not re-raised |
| Demonstrated but not promised in Ch1: zero-shot baseline (ch4:200-206) | declared in the statistical plan ch3:642-643 | acceptable (a baseline, not a contribution) |

## 4. Headline-number occurrence table (item 3; must-check B and C)

Sources are the pre-review reports' PASS rows (recomputed there); this table adds the
cross-document occurrence list and the qualifier check. "Qualifier kept" = the qualifier the
source chapter attaches is present at that occurrence or in its immediate sentence/paragraph.

| Value | Occurrences (file:line) | Source (per report PASS) | Qualifier of record | Qualifier kept at every occurrence? |
|---|---|---|---|---|
| **0.935** EM, Qwen Q4_K_M, golden | abstract:25; frabstract:26; arabstract:27; ch4:78, 371, 374; ch5:43 (fp16 reference, 0.935 = same value on surface A), 59, 289; ch6:23, 66, 81 (reference surface) | surface_b qwen Q4 golden; surface_a qwen golden (also 0.935) | "scored on reference text" (ch4:14-16, 76-77, 388) | Yes: abstracts x3 carry "scored on reference text"; ch6:23 carries it; ch6:66 and ch6:81 are in the same chapter after l.23 (l.81 is explicitly "on the reference surface"); ch5:289 carries it |
| **0.760** EM, SmolLM2 Q4_K_M, golden | ch4:79, 371; ch5:59; ch6:26 | surface_b smollm2 Q4 golden | -- | n/a |
| **17.5 pp** Qwen - SmolLM2 | abstract:25 ("17.5 percentage points"); frabstract:27 ("17,5 points"); arabstract:29; ch4:290; ch5:27, 33; ch6:26 | qwen - smollm2 EM; mcnemar.csv row 3, p = 1.1e-7 | "significant" only with McNemar, corrected alpha (ch4:286-290) | Yes: abstract "a significant difference"; FR "une différence significative"; AR "فرق دالّ إحصائيًا"; ch5:28 "paired tests establish as significant"; ch6:26 "significant at the corrected alpha (Section 4.6)" |
| **0.910** EM, Llama Q4_K_M, golden | ch4:78; ch6:28 | surface_b llama Q4 golden | "not established" vs Qwen (ch4:289-290, p = 0.0625 on 5 discordant) | Yes: ch6:28 "a difference ... that the test does not establish"; abstracts "not statistically established" / "n'est pas statistiquement établie" / "غير مُثبتة إحصائيًا"; ch5:30-31 "not distinguishable from zero on this evidence" |
| **894 / 1,072 / 2,282 ms** combined SLM p95, cooled | ch4:122-123, 352 (2,282), 354 (894); ch5:27 (894, 1,072); ch6:25 (894, 1,072), 29 (2,282) | thermal_headroom / exp1_cooled total p95 | cooled board; cached prefill (ch4:131-133, 352) | Yes: ch6:24 "On the cooled board"; ch5:71 "measured on a cooled board"; ch4:352 "measured with the prompt cache enabled" |
| **622 ms (25%)** miss of the 2,500 ms budget | abstract:28 (622, no %); frabstract:30; arabstract:32; ch4:350, 391; ch5:64; ch6:33 | exp2_latency_budget.md E2E p95 - 2,500 | "as specified", "re-baselined" | Yes: all three abstracts say re-baselined to the measured 3,122; ch4:391 "as specified"; ch5:63-64; ch6:32-33 |
| **3,122 ms (n = 226)** E2E p95 from end of speech | abstract:29; frabstract:32 (`3\,122`); arabstract:33; ch4:349 (with 226), 361; ch6:33; n = 226 also ch3:480 | exp2_latency_budget.md E2E row | "re-baselined"; Ingénieur's latency experiment; n = 226; cooled | Yes for "re-baselined" everywhere. Owner + n only at ch4:349 (issue 09 MINOR-3 left as written). Thermal state absent at ch4:349 (see MIN-1) |
| **0.68 GiB** peak RSS, Qwen | ch4:126; ch6:34 (ch5:27, 30 use it only as the 0.13 / 0.95 GiB differences) | exp1_cooled peak RSS / 1024 | "language-model process only" against the 2.5 GiB full-stack ceiling (ch3:586-590, ch4:126-127, 341-344) | Yes: ch4:126 "of the language-model process"; ch6:34 "confirmed for the language-model process only" |
| **3,540 decodes / 1 malformed / 0.17 pp** | ch4:246-249, 255, 261; ch5:121, 162-163, 324; ch6:51-57 | surface_b + surface_b_nogrammar sums | "on these test splits"; the 0.17 pp falls in the grammar's favour; not a measure of the reachability property (ch4:251-255) | Yes: ch6:52-56 restates both; ch5:324 "one malformed output in 3,540 decodes" |
| **6.5 pp** family difference at ~0.5 B | ch4:171; ch5:40, 209; ch6:80; table33 note | surface_a qwen - danube golden | "exploratory" (McNemar 15/2, p = 0.0023); reference surface; single adapters; prompt fold; separate session; unconverged (ch4:173, 179-198; ch5:204-216) | Yes: ch4:173 "an exploratory test"; ch5:216 "exploratory exact McNemar"; ch6:80-86 "on the reference surface ... exploratory test ... single trained adapters ... prompt ... session ... not shown to have converged"; ch5:40 quotes the point difference without the test but l.209-216 in the same chapter carry it |
| **0.0000-0.1579** safe-failure rate; **0.0530 over 528** pooled | ch4:144-145 (both); ch5:116-117 (0.0530, 28/528); ch6:39 (range) | nfr9_nfr18_abstention.csv | "missed, not adjusted"; ">= 0.70 budget" | Yes: ch4:154-155; ch6:38-40 with the budget |
| **0.1867-0.3933** false-command rate | ch4:146; ch6:40; ch5:129 as the complement (60.7-81.3%) | surface_b test_ood rows | "<= 0.05 budget"; "one tendency" (ch4:149-150) | Yes: ch6:40-42 carries Ch4's "one tendency" sentence; abstracts x3 carry it ("both misses reflect one tendency" / "une même tendance" / "نزعةً واحدة") |
| **81 unknown pairs (20 / 21 / 40)** | ch3:174-177 (81 = 20 + 21 + 40); ch5:165 (81); ch6:108 (81) | data/train.jsonl by family | "every one an utterance the schema does not support as a command; none a supported command made unreadable" | Yes: ch5:165-167; ch6:108-109 |
| 27.93 / 14.53 / 18.13 tok/s | ch1:31 (27.93, 14.53), 33 (18.13); ch3:44 (27.93); ch4:122-123 (27.93, 14.53) | thermal_headroom cooled / uncooled | thermal state | Yes: ch1:29-37 states cooled vs throttled; ch4:121 "On the cooled run" |
| 20 tok/s floor; 22 tokens / 1,100 ms | ch1:27-28, 146; ch2:30; ch3:584-585, 605, 669; ch4:124, 376-377; ch5:79 | 22 / 1.1 s | design allowance above the 16.0-token mean (ch3:584-585) | Yes |
| 0.36-1.2 B | ch1:94; abstract:11; frabstract:9-10 (0,36 à 1,2); arabstract:11; ch3:277; ch5:18; ch6:21 | prd §2 verbatim; largest model 1.236 B | -- | n/a |
| 2,500 ms budget | abstract:28; frabstract:31; arabstract:32; ch3:603, 621, 651, 673; ch4:314, 332, 347, 391; ch5:63; ch6:32 | exp2_latency_budget.md target | "missed, re-baselined, never met" | Yes (register check of master_ch6.py PASS) |
| 0.870 / 15 vs 2 / p = 0.0023 | ch4:172-173; ch5:216; ch6:82-83 | surface_a danube golden; mcnemar.csv family control | "exploratory" | Yes |
| 590 items; 0.000 zero-shot | ch4:202, 242; ch6:65 | 240 + 200 + 150; surface_a zero-shot rows | "does not attribute the gain to either intervention" (ch4:205-206, ch5:233-237) | Yes: ch6:67-68 |
| -1.5 to +1.5 pp; three items; smallest p 0.25 | ch4:218-225; ch6:73-74 | table18 / mcnemar deployment family | "not separated from zero", pipeline not precision (ch4:227-231) | Yes: ch6:70-76 |
| 25.1-41.3% decode-p95 reduction | ch4:115; ch6:77-78 | thermal_headroom | thermal state as a whole, not clock (ch5:239-246) | Yes |
| 751 ms uncached prefill p95; 1,063 ms min STT | ch4:141, 350; ch5:78 (751) | exp2_latency_budget.md; exp2_preds/clean.jsonl | Ingénieur's latency experiment; uncached | Owner named at ch4:140, 348; thermal state absent (MIN-1) |
| 0.690 / 0.590 CRR | ch5:288 | exp3_pi.csv clean, 10 dB | deployed system, speech input, board | Yes (ch5:281-292) |
| 1,350 ms combined stage allowance | ch3:649, 672; ch4:139, 331, 377; ch5:73 | sum of two tab:latency-budget rows | "under cached prefill" (ch4:138-141) | Yes: ch4:377 "under cached prefill"; ch5:77 |

No number differs between any two occurrences. No occurrence carries a stronger qualifier than
its source chapter. One occurrence drops a qualifier the document promises for all timing figures
(MIN-1).

## 5. Abstract comparison (item 4; must-check A)

Every number and claim, side by side, with the Ch6 §6.1 sentence it derives from (or Ch3/Ch4
where the abstract's method paragraph derives from those).

| # | English (abstract.tex) | French (frabstract.tex) | Arabic (arabstract.tex) | Derives from | Same numbers / qualifiers? |
|---|---|---|---|---|---|
| A1 | l.10-12: trade-off across SLMs of **0.36-1.2 B**, fine-tuned for drone-swarm command parsing, quantised for CPU-only execution on a Raspberry Pi 5 | l.9-11: **0,36 à 1,2 milliard**, affinés ..., quantifiés pour ... le seul processeur central d'un Raspberry Pi 5 | l.11-13: **0.36** و **1.2** مليار معلمة ... المعالج المركزي وحده ... Raspberry Pi 5 | RQ1, ch1:93-95 | Yes |
| A2 | l.15-16: frozen schema + matched grammar; structural validity a property of the decoder | l.14-15: schéma figé, grammaire ... validité structurelle ... propriété du décodeur | l.16-17: مخطط أوامر مُثبَّت ... الصحة البنيوية خاصيةً لمفكّك الترميز | C1, ch1:107-109; ch6:49 | Yes |
| A3 | l.16-18: label-first pipeline; splits by template family; golden test set of **200** recorded commands | l.15-18: chaîne ... part des étiquettes; partitions par famille de gabarits; jeu de test de référence de **200** commandes enregistrées | l.17-18: سلسلةٌ لبناء البيانات تنطلق من التسميات ... عائلة القوالب ... **200** أمر مسجَّل | C2, ch3:128, 180-182, 201 | Yes |
| A4 | l.18-19: **four** models fine-tuned under one recipe; **three** quantised at **two** levels; their Q4_K_M artefacts timed on the board | l.18-19: quatre ... même recette; trois ... deux niveaux; artefacts Q4_K_M chronométrés sur la carte | l.18-19: أربعة نماذج ... وصفة واحدة؛ ثلاثة ... بمستويين ... Q4_K_M ... على الجهاز | ch3:275-280, 373-375, 478-479 | Yes (issue 09 NEW-1 fix landed in all three) |
| A5 | l.19-20: the fourth, matched in size to one of them, **separates model family from size** | l.19-20: le quatrième, de taille appariée ..., **sépare l'effet de la famille de modèles de celui de la taille** | l.19-20: الرابع، المماثل في الحجم لأحدها، **فيفصل أثر عائلة النموذج عن أثر الحجم** | ch4:176-177 "measure a family difference at about 0.5 B; they do not express it as a share of a size effect"; ch6:86-88; ch1:137-138 | **No -- claim stronger than the chapters in all three languages (M-1)** |
| A6 | l.20: selection rule fixed before any result existed | l.20-21: règle ... fixée avant l'obtention de tout résultat | l.20-21: قاعدةُ انتقاءٍ ثُبِّتت قبل وجود أي نتيجة | ch3:622 | Yes |
| A7 | l.23-25: among the **three** models timed on the board, the trade-off at Q4_K_M reduces to **two** non-dominated configurations, SmolLM2-360M and Qwen2.5-0.5B; rule deploys Qwen2.5-0.5B at Q4_K_M | l.24-26: parmi les trois ... chronométrés ..., deux configurations non dominées ...; la règle déploie Qwen2.5-0.5B en Q4_K_M | l.24-27: النماذج الثلاثة التي قيس زمنها ... تهيئتين غير مُهيمَن عليهما ... وتنشر القاعدة Qwen2.5-0.5B | ch6:20-23 | Yes ("timed", Q4_K_M scope kept in all three) |
| A8 | l.25: **0.935** exact match on the golden set, **scored on reference text** | l.26-27: **0,935** sur le jeu de référence, **évaluée sur le texte de référence des commandes** | l.27-28: **0.935** على المجموعة المرجعية، **محسوبةً على النص المرجعي للأوامر** | ch6:23 | Yes (NEW-1 fix landed x3). NIT-4: FR/AR use "référence"/"مرجعي" for both the golden set and reference text in one sentence |
| A9 | l.25: SmolLM2-360M faster and **17.5 percentage points** less accurate, **a significant difference** | l.27-28: plus rapide et moins précis de **17,5 points de pourcentage**, **une différence significative** | l.29: أسرع وأقل دقة بـ**17.5** نقطة مئوية، **وهو فرق دالّ إحصائيًا** | ch6:24-26 | Yes |
| A10 | l.26: Llama-3.2-1B slower; lower accuracy on the golden set **not statistically established** | l.28-29: plus lent, et sa précision inférieure ... **n'est pas statistiquement établie** | l.29-30: فأبطأ، ودقته الأدنى ... **غير مُثبتة إحصائيًا** | ch6:27-29 | Yes (no number quoted for Llama in any abstract) |
| A11 | l.27-29: selection on accuracy against **re-baselined** constraints; misses the **2,500 ms** budget by **622 ms**; budget re-baselined to the measured **3,122 ms** | l.29-32: contraintes **redéfinies d'après les mesures**; dépasse de **622 ms** le budget de **2 500 ms**; redéfini à **3 122 ms** | l.30-33: قيود **أُعيد ضبطها على القيم المقيسة** ... **2,500** ... **622** ... **3,122** | ch6:31-33 | Yes. The "(25%)" of ch6:33 is omitted in all three (omission, not a change) |
| A12 | l.29-31: **every** configuration misses the safe-failure and false-command requirements; **both misses reflect one tendency**: when wrong or out of domain, it emits a well-formed command rather than declining | l.32-34: **aucune** configuration ne satisfait ...; **une même tendance** ...; commande bien formée au lieu de s'abstenir | l.33-35: **ولا تستوفي أي تهيئة** ...; **نزعةً واحدة** ...; أمرًا سليم البنية بدل الامتناع | ch6:37-42 | Yes (NEW-1 M3 fix landed x3). No rates quoted in the abstracts |
| A13 | l.31-32: a confidence gate on the decoder's output is the first step proposed | l.34-35: un seuil de confiance ... la première étape proposée | l.35: بوابة ثقة ... أولى الخطوات المقترحة | ch6:99 | Yes |
| A14 | Not in any abstract: memory (0.68 GiB, ceiling, "language-model process only"); grammar ablation figures; family-control figures; thermal result | -- | -- | ch6:33-34, 49-58, 76-88 | Omissions only; nothing in an abstract outruns Ch6 except A5 |

Numbers per abstract (in order of appearance): EN 0.36, 1.2, 200, 0.935, 17.5, 2,500, 622, 3,122
| FR 0,36, 1,2, 200, 0,935, 17,5, 622, 2 500, 3 122 | AR 0.36, 1.2, 200, 0.935, 17.5, 2,500, 622,
3,122. Identical sets (FR orders 622 before 2 500 in the sentence). Keywords: EN 8 terms; FR 8,
same terms; AR 8, same terms.

## 6. Scorecard

| Item | Result |
|---|---|
| 1 Golden thread (RQ1, C1-C3 through every chapter) | PASS |
| 2 Contributions claimed vs demonstrated | ISSUES (1): M-1 (abstract claim stronger than Ch4/Ch6); NIT-2 |
| 3 Same number identical everywhere | PASS (one qualifier gap, MIN-1) |
| 4 Three abstracts say the same thing; none outruns the chapters | ISSUES (1): M-1 in all three; NIT-4 |
| 5 Definitions and notation consistent | ISSUES (2): MIN-3, MIN-4; NIT-3 |
| 6 Forward/backward references true | PASS (table in §8; 44 targets checked, all do what the text says) |
| 7 Write-once against the Ingénieur | PASS (overlaps recorded in §9; none is duplicated exposition; two Ingénieur-side items handed to issue 10) |
| 8 Front/back matter | ISSUES (1): NIT-1 (SHA hand-typed, key unused). Acronym list 18 entries, complete for every `\gls` key used; LoF/LoT short titles; 45 bibliography entries = 45 cited keys; title page fields correct |
| 9 Scope from Ch1 alone | ISSUES (1): MIN-2 (where the controller and simulation run is not stated) |
| 10 Clean build | PASS (0 errors, 0 undefined, 0 dropped floats, 0 TODO/CHECK/figtodo; remaining warnings judged non-findings, NIT-5) |
| Cross-chapter consistency (must-check C) | ISSUES (2): MIN-1, MIN-5 |

## 7. Findings

Sorted BLOCKER -> NIT. Proposed fixes introduce no new number and no hedging word in Ch6 or the
abstracts. Script anchors checked with `grep` over `tools/review/*.py`.

| # | Sev | Item | file:line | Quoted text | Problem | Evidence | Proposed fix |
|---|---|---|---|---|---|---|---|
| M-1 | MAJOR | 2, 4 | `master/frontmatter/abstract.tex:19-20`; `frabstract.tex:19-20`; `arabstract.tex:19-20` | EN: "the fourth, matched in size to one of them, separates model family from size"; FR: "sépare l'effet de la famille de modèles de celui de la taille"; AR: "فيفصل أثر عائلة النموذج عن أثر الحجم" | Overclaim: the chapters say the control measures a family difference at one size and explicitly does not separate family from size. This is the wording Ch1 dropped under issue 03 (V20: "separates model family from model size" -> "measures a model-family difference at fixed size", Comments of issue 03, l.416-417 of the Comments). Issue 09's NEW-1 re-derived the abstracts from §6.1 only; this sentence sits in the method paragraph and was not touched | `ch4_results.tex:174-177` "its endpoints also differ in family, and no family appears at two sizes. These data therefore measure a family difference at about 0.5 B parameters; they do not express it as a share of a size effect"; `ch3_method.tex:287-288` "It does not remove family from the size comparison"; `ch6_conclusion.tex:86-88`; `ch1_introduction.tex:137-138` | EN l.19-20: "and the fourth, matched in size to one of them, measures a model-family difference at fixed size." (Ch1 l.137-138 wording). FR l.19-20: "et le quatrième, de taille appariée à l'un d'eux, mesure une différence entre familles de modèles à taille fixée." AR l.19-20: "أما الرابع، المماثل في الحجم لأحدها، فيقيس فرقًا بين عائلات النماذج عند حجم ثابت." No `tools/review` script anchors on the abstracts (grep: no match for "separates" or "abstract" in `tools/review/*.py`) |
| MIN-1 | MINOR | 3, C | `master/ch4_results.tex:348-350` and `:140-141` | l.349: "from end of speech, Qwen2.5-0.5B's p95 is 3{,}122~ms over 226 segments, ... and the shortest speech-recognition time it recorded is 1{,}063~ms"; l.141: "has a p95 of 751~ms" | Ch1 promises "every timing figure in this document is reported with the thermal state it was measured under" (`ch1_introduction.tex:35-37`). The three Ingénieur-sourced timing figures in Ch4 (3,122; 1,063; 751 ms) carry no thermal state; only Ch5 l.81-82 supplies "measured on the cooled board" for 3,122 | `results/exp2_latency_budget.md:3` "Raspberry Pi 5, cooled, governor `performance`"; commit `5ed20ba` "the latency experiment ran cooled". Note: issue 03 W9 (Comments l.572-574) recorded that "nothing records whether [the cooler] was fitted for the latency experiment"; the results header now does | l.348-349: "measured the full parse path for the selected configuration alone, on the cooled board: from end of speech, Qwen2.5-0.5B's p95 is 3{,}122~ms over 226 segments, ..."; l.140-141: "has a p95 of 751~ms on the cooled board, so this margin describes the cached condition only." Anchors `p95 is 3{,}122~ms over 226`, `recorded is 1{,}063~ms`, `has a p95 of 751~ms` (master_ch4.py) stay intact |
| MIN-2 | MINOR | 9 | `master/ch1_introduction.tex:75-79` | "converts spoken English commands into validated structured commands for a swarm of five drones, entirely on the Raspberry Pi 5 ... a validator checks it, and the swarm controller executes it" | Scope check: from Ch1 alone a reader cannot tell that the flight state machine, the swarm controller and the simulation run on a workstation linked to the board; "entirely on the Raspberry Pi 5" followed by "the swarm controller executes it" invites the reading that the controller runs on the Pi. The Master never states the placement anywhere (grep "workstation" in Ch1-Ch6: only the accuracy-scoring workstation) | `ingenieur/ch1_introduction.tex:48-50` "The flight state machine, the swarm controller and the simulated vehicles run on a workstation joined to the device by the wireless link"; `ingenieur/ch3_architecture.tex:111-113` | l.78-79: "a validator checks it, and the swarm controller, which runs with the simulation on a workstation linked to the board, executes it." No master_ch1.py anchor on this sentence (grep "swarm controller executes": none) |
| MIN-3 | MINOR | 5 | `master/ch3_method.tex:573-574, 603, 664` (first uses); expansion only at `ch4_results.tex:122` | ch3:603 "p95 $\leq$ 2{,}500~ms"; ch3:664 "Target p95"; ch4:122 "p95 (95th percentile)" | Notation `p50`/`p95` is used in three Ch3 tables (tab:metrics, tab:requirements, tab:latency-budget) before it is expanded in Ch4. The Percentiles row of tab:metrics (l.574) defines the rule but not the notation. The Ingénieur defines it at first use (`ingenieur/ch1_introduction.tex:32`) | ch3:574 "Percentiles & Nearest-rank on the sorted sample, no interpolation; sample size $n$ stated in every cell" | ch3:574: "Percentiles & Nearest-rank on the sorted sample, no interpolation; p50 and p95 denote the 50th and 95th percentiles; sample size $n$ stated in every cell & all \\". Check master_ch3.py for an anchor on "Nearest-rank on the sorted sample" before editing (appending after the semicolon keeps any prefix anchor) |
| MIN-4 | MINOR | 5 | `master/ch3_method.tex:201` (defines "golden set"), `tab:dataset:160` (`test_golden`), `ch4_results.tex:82` (first "golden split") | ch3:201 "The single-speaker \textbf{golden set}"; ch4:82 "On the golden split" | Three names for one split -- `test_golden` (tables), "golden set" (Ch3, abstracts), "golden split" (Ch4-Ch6, 14 uses) -- and no sentence ties the third to the first two. Terminology drift across chapters | ch3:160, 201; ch4:76-77, 82; ch6:23 | ch3:201: "The single-speaker \textbf{golden set} (\texttt{test\_golden}; the golden split of Chapter~\ref{chap:results}) is the author reading 200 utterances ..." Check master_ch3.py anchors on "golden set" (grep found none on this line) |
| MIN-5 | MINOR | 1 | `master/ch4_results.tex:375-378` | "The selected configuration is also the only one of the three meeting the 0.85 exact-match threshold, the 1{,}100~ms decode allowance, the 1{,}350~ms combined stage allowance under cached prefill, the 20~tok/s throughput floor and the throttling budget together" | The Intent-F1 requirement (`ch3_method.tex:606`, "Intent macro-F1, best model, >= 0.90, Multi-model benchmark") is measured (ch4:82-83 "intent macro-F1 is above 0.95 for every configuration and reaches 1.000 for Qwen2.5-0.5B") but no sentence states its verdict, although tab:requirements' caption promises a verdict per requirement ("a missed requirement is reported as missed") and ch3:581-582 says the table lists every requirement Ch4 uses | ch3:606; ch4:82-83; table17 golden intent-F1 min 0.954 | ch4:376: "meeting the 0.85 exact-match threshold, the 0.90 intent-F1 threshold, the 1{,}100~ms decode allowance, ..." (0.90 is already in Table 3.4). master_ch4.py has a "configs meeting all six" data check (report row l.376) -- confirm it counts criteria from data, not from this sentence, before editing; the text anchor at l.379 (`misses the exact-match threshold by 9~pp`) is unaffected |
| NIT-1 | NIT | 8 | `master/ch1_introduction.tex:115`; `master/ch3_method.tex:235` | "sealed under a SHA-256 checksum"; "sealed that pass under SHA-256" | `shared/acronyms.tex:48` defines `sha` (Secure Hash Algorithm) but it is never `\gls`'d, so SHA is absent from the printed List of Acronyms while the term appears twice in the body | PDF List of Acronyms (18 entries, no SHA); grep `\gls{sha}`: none | Either `\gls{sha}-256` at both sites (first use prints "Secure Hash Algorithm (SHA)-256"), or keep the hand-typed algorithm name and delete the unused `sha` key so the list and the text agree. Author's call |
| NIT-2 | NIT | 2 | `master/ch1_introduction.tex:117-118`; `master/ch2_related_work.tex:28, 198-199` | "measures \gls{em}, intent and slot F1, schema validity, and false-command rate" | C3's metric list omits the safe-failure rate, which the same harness reports (ch3:538-540, ch4:143-150) and which Ch6 relies on ("misses both abstention requirements", ch6:38-40) | ch3:538-540; ch4:144-145; ch6:38-40 | Add "safe-failure rate" to the three lists: "measures \gls{em}, intent and slot F1, schema validity, safe-failure rate and false-command rate". master_ch1.py checks each named C3 metric against a surface_b.csv column (report rows l.117-118); the safe-failure figures come from `nfr9_nfr18_abstention.csv` (ch4 report l.145), so the script's column check may need a second source before the word is added |
| NIT-3 | NIT | 5 | `master/ch1_introduction.tex:24, 30-31`; `master/ch3_method.tex:275-277, 284, 375` vs Ch2, Ch4-Ch6, abstracts | Ch1/Ch3: "Qwen2.5-0.5B-Instruct", "H2O-Danube3-500M-Chat"; elsewhere: "Qwen2.5-0.5B", "H2O-Danube3-500M" | Two naming conventions for the same models across chapters; the generated tables use one display name (issue 04, "One display name per model") | ch1:24; ch4:77-79; table17/table33 | Acceptable if deliberate (full checkpoint name at first mention in Ch1 and in the recipe, short name thereafter). If not, use the short names at ch1:30-31 and ch3:284, 375, keeping the full names only at ch1:24 and ch3:275-277 where the checkpoints are introduced |
| NIT-4 | NIT | 4 | `master/frontmatter/frabstract.tex:26-27`; `arabstract.tex:27-28` | FR: "sur le jeu de référence, évaluée sur le texte de référence des commandes"; AR: "على المجموعة المرجعية، محسوبةً على النص المرجعي للأوامر" | "référence"/"مرجعي" carries two senses in one sentence (the golden set; the reference transcripts). The English distinguishes "golden set" from "reference text". Not a translation error, but the qualifier the sentence exists to carry is harder to read | abstract.tex:25 | FR: "avec une correspondance exacte de 0,935 sur le jeu de test de référence, évaluée sur les transcriptions de référence des commandes et non sur la parole"; AR: "على مجموعة الاختبار المرجعية، محسوبةً على النصوص المرجعية للأوامر لا على الكلام". Native-speaker check remains out of scope |
| NIT-5 | NIT | 10 | `shared/frontmatter/institution_header.tex:9, 14`; `master/ch3_method.tex:548` (tab:metrics) | `\textsc{...}` inside `\begin{Arabic}`; xltabular spanning two pages | Remaining build warnings: "Font shape TU/Amiri(0)/m/sc undefined" (Amiri has no small caps; XeLaTeX silently substitutes the upright shape) and xdvipdfmx "Object @table.3.3 already defined" twice (hyperref defines tab:metrics' anchor on each page it spans; the link resolves to the first). "biblatex: Language 'arabic' not supported" is harmless: no bib entry is Arabic | `thesis/build/master/main_master.log:1937`; task brief | No action required for the PDF. If the warning is to be silenced, `\textbf` instead of `\textsc` at institution_header.tex:9 and :14 changes rendering (the cover is the school's template, "Do not reword" -- formatting is the author's call). The duplicate anchor is inherent to a multi-page `xltabular` |

Not re-raised (already decided in the issues' Comments, still true as written): issue 05
C5-C14, M14-M16 and NITs (e.g. "knee" undefined, "of record", the 622/751 figures without their
`\ref`, "lost at the speech stage"); issue 09 MINOR-3, -4, -6, -7 and NIT-1..6 (3,122 without
owner/n in Ch6; "the test" without antecedent; "hold for a cooled board"; the family-control
paragraph outside the contributions; "six configurations" for 18 rows); issue 09's step-3 scope;
issue 03's latency-budget table staying in Ch3 (prd Table 3 says Ch4); the title-page
placeholders; the Ch1 WARNs (`CPU`, "small language model" inside the verbatim RQ1 quote), the
Ch3 WARNs (`LoRA` in the outline heading, `JSON` in the verbatim system prompt, the 1,350 ms sum
row, the negated cited "not guaranteed"), the Ch2 three-plus-control WARN. None has become wrong
since: the later edits (Ch6, abstracts, Ingénieur Ch3) contradict none of them.

## 8. Forward / backward reference table (item 6)

Every `\ref` in the Master resolves to a label (44 targets, `grep` comm: no unlabelled ref). Below,
each reference that makes a claim about its target ("X defines/reports/measures/argues ..."), with
whether the target does it. Bare figure/table refs whose target is the object itself are omitted.

| file:line | reference text | target label -> section | does the target do it? |
|---|---|---|---|
| ch1:22 | "Chapter 2 takes up that literature in full" | chap:related-work -> §2.1 | Yes, ch2:10-40 |
| ch1:25 | fourth, parameter-matched model fine-tuned as a control "(Chapter 3)" | chap:method -> §3.3 "The parameter-matched control" | Yes, ch3:282-294 |
| ch1:32 | 27.93 / 14.53 tok/s "(Chapter 4)" | chap:results -> §4.2 | Yes, ch4:121-123 |
| ch1:69 | "The grammar of Section 3.1 bounds the identifier list at five entries" | sec:schema | Yes, ch3:88, 103-104 |
| ch1:124 | "Chapter 4 presents what [C3] measured" | chap:results | Yes, §4.2, §4.4 |
| ch1:132-143 | structure paragraph: Ch2 four literatures; Ch3 schema, dataset, recipe, quantisation, protocol; Ch4 speaker-sensitivity, benchmark, control, delta, ablation, statistics, selection; Ch5 trade-off, failure modes, threats; Ch6 answer + next steps | chap:related-work, chap:method, chap:results, chap:discussion, chap:conclusion | Yes, all seven Ch4 items are sections/paragraphs (§4.1-§4.7); Ch5 §5.1-§5.3; Ch6 §6.1, §6.3 |
| ch2:30 | "the 20 tok/s throughput floor of Chapter 1" | chap:introduction | Yes, ch1:27-28 |
| ch2:32 | llama.cpp "segments its prompt differently from the tokeniser it was trained under (Chapter 3)" | chap:method -> §3.4 "Exclusion of the control model" | Yes, ch3:443-453 |
| ch2:40 | "Section 2.2 takes up what those schemes cost in accuracy" | sec:quantisation | Yes, ch2:65-89 |
| ch2:86-89 | "Chapter 4 measures the accuracy cost of the whole deployment pipeline ...; Section 3.4 explains why that pipeline cost is not the cost of quantisation alone" | chap:results §4.4; sec:quantisation-procedure | Yes, ch4:208-236; ch3:397-415 |
| ch2:113 | "The bounded grammar of Section 3.1 makes that length finite" | sec:schema | Yes, ch3:110-114 |
| ch2:115-117, 129 | "grammar ablation of Chapter 4 decodes ... with and without the grammar"; "reports accuracy with and without" | chap:results §4.5 | Yes, ch4:241-249 |
| ch2:152 | "No existing corpus covers this command vocabulary (Section 3.2)" | sec:dataset | Yes, ch3:125 |
| ch2:154-155 | "The evaluation protocol of Chapter 3 is built to answer that question" | chap:method §3.5 | Yes, ch3:455-643 |
| ch2:203-205 | "Chapter 4 answers RQ1 ...; Chapter 3 specifies how each contribution was built" | chap:results §4.7; chap:method | Yes |
| ch3:12 | "the contract Section 2.3 argued for" | sec:constrained-decoding | Yes, ch2:107-117 |
| ch3:45 | "27.93 tok/s ... (Chapter 4)" | chap:results | Yes, ch4:122 |
| ch3:58 | "the conformance check of Section 3.2, which parses this grammar file itself" | sec:dataset | Yes, ch3:188-191 |
| ch3:100 | "the canonical comparator of Section 3.5 rounds every numeric slot to one decimal" | sec:definitions-of-record | Yes, ch3:515-520 |
| ch3:118-119 | "Section 2.3 made that argument in the abstract. Table 4.7 in Chapter 4 makes it concrete" | sec:constrained-decoding; tab:grammar-ablation | Yes |
| ch3:218 | speaker variation characterised "by the speaker-sensitivity experiment (Section 4.1)" | sec:speaker-sensitivity | Yes, ch4:23-64 |
| ch3:292 | "It holds on the reference surface only (Section 3.4)" | sec:quantisation-procedure | Yes, ch3:383-395, 443-453 |
| ch3:368 | "Chapter 5 carries it into the threats to validity" | chap:discussion §5.3.1 | Yes, ch5:204-216 |
| ch3:390 | latency and throughput "timed on the Raspberry Pi 5 (Section 3.5)" | sec:definitions-of-record | Yes, ch3:471-473, 485-494 |
| ch3:394 | "Table 4.6 presents it" (reference-minus-deployed) | tab:quantisation-delta | Yes |
| ch3:409 | grammar disabled "Chapter 4 reports it" | chap:results §4.5 | Yes |
| ch3:415 | "(Section 2.2)" for perplexity/generic changes | sec:quantisation | Yes, ch2:65-89 |
| ch3:561-573 | tab:metrics "Reported in" column | sec:benchmark, sec:grammar-ablation, sec:selection, sec:speaker-sensitivity | Yes, every row: EM §4.2-4.5; intent/slot F1 §4.2 (Table 4.2); validity §4.2, §4.5; safe-failure §4.2; false-command §4.2; throughput/RSS §4.2, §4.7; throttle §4.2; WER + speaker position §4.1; latency §4.2, §4.7 |
| ch3:584-585 | "decode allowance of Table 3.5 ... the 16.0-token mean measured in Section 3.1" | tab:latency-budget; sec:schema | Yes, ch3:669; ch3:40 |
| ch3:649 | "the 1,350 ms stage allowance used in Figure 4.1" | fig:pareto | Yes, caption ch4:330-331 |
| ch4:6-7 | "the selection rule stated in Section 3.5" | sec:definitions-of-record | Yes, ch3:620-629 |
| ch4:12 | identical outputs on workstation and Pi "(Section 3.5)" | sec:definitions-of-record | Yes, ch3:466-467 |
| ch4:17 | "Section 4.1 measures the recognition error that the audio input carries" | sec:speaker-sensitivity | Yes |
| ch4:43 | "The speaker-sensitivity requirement (Table 3.4) asks for that position rather than for a threshold" | tab:requirements | Yes, ch3:614 |
| ch4:80, 371, 381, 387 | "Section 4.6 does not find significant" / "establishes as significant" | sec:statistics | Yes, ch4:282-290 |
| ch4:104 | "the run of record, whose protocol Section 3.5 describes" | sec:definitions-of-record | Yes, ch3:485-494 |
| ch4:133 | prompt cache on in the benchmark, off in the parser "(Section 3.5)" | sec:definitions-of-record | Yes, ch3:491-494 |
| ch4:156 | "The likely cause of the failure is examined in Section 5.2" | sec:failure-modes | Yes, ch5:127-180 |
| ch4:192 | trained in a separate session "(Section 3.3)" | sec:lora | Yes, ch3:362-369 |
| ch4:194, 230 | "chat-template parity check of Section 3.4"; decoding settings and checkpoint "(Section 3.4)" | sec:quantisation-procedure | Yes, ch3:417-453; 397-405 |
| ch4:263 | "Chapter 5 takes up what these two readings imply" | chap:discussion §5.3.2 | Yes, ch5:316-327 |
| ch4:272 | "The statistical plan of Section 3.5 declares two confirmatory families" | sec:definitions-of-record | Yes, ch3:630-634 |
| ch4:395 | "Chapter 5 takes up the consequences of these shortfalls and what would address them" | chap:discussion | Yes, ch5:52-68, 176-180 |
| ch5:29, 59 | "(Section 4.6)" paired tests | sec:statistics | Yes |
| ch5:39, 47, 220 | "iso-parameter control of Section 4.3"; convergence gains "(Section 4.3)" | sec:iso-parameter | Yes, ch4:171-186 |
| ch5:52 | "The rule of Section 4.7" | sec:selection | Yes, ch4:313-316 |
| ch5:61 | "0.85 exact-match threshold of Table 3.4" | tab:requirements | Yes, ch3:604 |
| ch5:71 | "Table 4.3 reports how far they move without the cooler" | tab:thermal-headroom | Yes |
| ch5:73 | "1,350 ms stage allowance of Table 3.5" | tab:latency-budget | Yes, ch3:672 |
| ch5:76 | "not the 250 ms prefill allowance (Section 4.2)" | sec:benchmark | Yes, ch4:129-131 |
| ch5:94, 99, 102 | end-to-end miss / Llama lower bound / full stack not measured "(Section 4.7)" | sec:selection | Yes, ch4:346-364, 341-344 |
| ch5:117 | "safe-failure rate of 0.0530 reported in Section 4.2" | sec:benchmark | Yes, ch4:145 |
| ch5:152 | "none of the three validation layers of Section 3.1" | sec:schema | Yes, ch3:48-52 |
| ch5:160, 167 | "grammar ablation of Section 4.5"; 81 pairs "(Section 3.2)" | sec:grammar-ablation; sec:dataset | Yes; ch3:174-180 |
| ch5:176, 237 | "(Section 5.3.1)" untuned baseline; "hypothesis of Section 5.2 remains untested" | sec:threats-internal; sec:failure-modes | Yes, ch5:230-237; 160-180 |
| ch5:198, 205 | parity check "of Section 3.4"; declared differences "(Section 4.3)" | sec:quantisation-procedure; sec:iso-parameter | Yes |
| ch5:224, 228 | "one seed (Table 3.2)"; fp16 substitution "(Section 3.3)" | tab:lora; sec:lora | Yes, ch3:313; 349-360 |
| ch5:241 | clock cap "(Section 4.2)" | sec:benchmark | Yes, ch4:116-119 |
| ch5:251 | 12 patterns, optimistic p "(Section 3.5)" | sec:definitions-of-record | Yes, ch3:637-641 |
| ch5:259 | "the 67 ms decode margin of Section 5.1" | sec:tradeoff | Yes, ch5:79 |
| ch5:268, 297, 305 | "(Section 3.2)" golden from test_synth families; WER "(Section 4.1)"; "Section 5.1 argued" | sec:dataset; sec:speaker-sensitivity; sec:tradeoff | Yes, ch3:202-204; ch4:41-44; ch5:70-85 |
| ch5:339-342 | hand-off: Ch6 "sets out, in order of priority, three steps ... Two are the interventions of Section 5.2 ...; the third ... which Section 5.1 notes was not made" | chap:conclusion §6.3; sec:failure-modes; sec:tradeoff | Yes, ch6:93-116; ch5:176-180; ch5:92-103 |
| ch6:26, 36 | significance "(Section 4.6)" | sec:statistics | Yes |
| ch6:32 | re-baselined under the failure clause "(Section 4.7)" | sec:selection | Yes, ch4:357-364 |
| ch6:52 | one malformed, 0.17 pp "(Section 4.5)" | sec:grammar-ablation | Yes |
| ch6:63 | family splits, gate clean on four axes "(Section 3.2)" | sec:dataset | Yes, ch3:180-188 |
| ch6:65 | zero-shot 590 items "(Section 4.3)" | sec:iso-parameter | Yes, ch4:200-206 (paragraph inside §4.3) |
| ch6:74 | deltas, smallest p 0.25 "(Section 4.4)" | sec:quantisation-delta | Yes, ch4:218-225 |
| ch6:78 | thermal 25.1-41.3% "(Section 4.2)" | sec:benchmark | Yes, ch4:114-115 |
| ch6:85-86 | "(Sections 4.3 and 5.3.1)" | sec:iso-parameter; sec:threats-internal | Yes |
| ch6:100, 103, 109, 115 | widest-margin misses "(Section 4.2)"; in-domain errors "(Section 5.2)"; 81 pairs "(Section 3.2)"; "frontier of Section 6.1" | sec:benchmark; sec:failure-modes; sec:dataset; sec:rq1-answer | Yes, ch4:147-148; ch5:144-158; ch3:174-180; ch6:20-23 |
| Cross-document (no `\ref` possible): ch1:110-111, ch3:51-52 "the Mémoire d'Ingénieur's architecture chapter" (validator + state machine) | -> Ingénieur Ch3 "Architecture and design" §3.3 | Yes: `ingenieur/ch3_architecture.tex:263-360` now carries both layers; chapter title matches prd §3.1 item 3; no chapter number hardcoded |
| ch3:212-213 "the Mémoire d'Ingénieur states the consequence [unrecorded sessions] ... as a limitation" | -> Ingénieur Ch6 §Limitations | Planned in the scaffold (`ingenieur/ch6_conclusion.tex:77-79` note "One speaker, one room, one recording session"); prose not yet written -- for issue 10 |
| ch3:528 "The Mémoire d'Ingénieur reports that gap [EM - CRR] as a finding in its own right" | -> Ingénieur Ch5 §Acoustic-robustness | Planned (`ingenieur/ch5_validation.tex:102-103` note); prose not yet written -- for issue 10 |
| ch4:140, 348; ch5:281-282 "latency experiment" / "acoustic-robustness experiment of the Mémoire d'Ingénieur" | -> Ingénieur Ch5 §5.1, §5.3 | Names match the Ingénieur's own (`ingenieur/ch1_introduction.tex:102-110`); prose pending -- issue 10 |

Hardcoded chapter numbers of the other document: none in the Master (grep `Chapter~[0-9]`,
`Ch\. [0-9]`: no match). The companion is named "the \emph{M\'emoire d'Ing\'enieur}" at every one
of its 17 mentions (grep: no "companion report", no bare "Ingénieur document").

## 9. Write-once table (item 7)

Mechanical scan (9-word shingles over de-macroed prose, Master Ch1-Ch6 + abstract vs Ingénieur
Ch1-Ch6) plus a manual read of every passage that names the other document.

| Master file:line | Ingénieur file:line | Overlap | Verdict |
|---|---|---|---|
| ch3_method.tex:575 tab:metrics "Formation accuracy: Fraction of drones within τ = 0.5 m of the assigned slot, averaged over the final 5 s of a 60 s trial" | ch1_introduction.tex:182 tab:nonfunctional-requirements "Fraction of drones within τ = 0.5 m of the assigned slot over the final 5 s of a 60 s trial" | Identical metric definition (shingle hit) | Master owns "the definitions of record" (prd §3.1 item 3) and marks the row †. The Ingénieur's copy is the duplicate -- **for issue 10** (one fresh clause + cross-reference there). Not a Master finding |
| ch3_method.tex:608-609 tab:requirements "Clean-audio recognition: CRR on the golden set, clean audio, ≥ 0.80, Acoustic-robustness experiment*"; "Recognition in noise: CRR at 10 dB SNR, ≥ 0.65" | ch1_introduction.tex:179-180 same two rows (the Ingénieur adds "under propeller-type noise") | Two near-identical requirement rows (shingle hit) | Acceptable: the Ingénieur declares shared criteria "carry the same name there" (ch1:97-98) and the Master stars them as measured in the Ingénieur. No exposition duplicated; a table row is the one-sentence statement Table 3 allows. Same for "End-to-end latency" (ch3:603 vs ing-ch1:174) |
| ch3_method.tex:655-676 tab:latency-budget (parse rows 500/1,200/250/1,100/50; 1,350; 2,500) | ch3_architecture.tex:379-397 tab:stage-budget (same values; fresh row wording; adds start-of-speech and reflex rows) | Same seven values | Acceptable by Table 3 ("one table in Master ... as the deployment constraint"); wording fresh on both sides; the Master names the owner (ch3:645-647, 659-660) and the Ingénieur names the Master's use (ing-ch3:426-428). Location (Ch3 not Ch4) decided in issue 03 |
| ch3_method.tex:648-651 "The allowances are targets, not a decomposition of the end-to-end budget ... the measured end-to-end figure, not their sum" | ch3_architecture.tex:428-432 "The allowances are ceilings, not shares of the end-to-end target ... judged on the measured end-to-end figure, never on the sum" | Same point, different words | Acceptable: one sentence in the Master with the cross-reference |
| ch3_method.tex:573 tab:metrics Latency row "Parse path: T0 = end of speech, T1 = return of the publish call ...; reflex path: T0 = keyword offset, same T1; both paths also report an onset-anchored figure" | ch3_architecture.tex:399-410 "Anchors" paragraph | Master states the anchors in one table cell; the Ingénieur derives them | Acceptable: definition of record (Master) vs design rationale (Ingénieur) |
| ch3_method.tex:48-52 "Three layers stand between the decoder and the flight controller ... This chapter owns only the first. The second and third ... belong to the Mémoire d'Ingénieur's architecture chapter" | ch1_introduction.tex:260-265; ch3_architecture.tex:263-270 | Same three-layer statement | Acceptable: each side names the owner; Master gives one sentence, the Ingénieur the exposition |
| ch3_method.tex:93-98 GBNF cannot express a range; range enforcement to the validator | ch3_architecture.tex:272-276 "It cannot bound a number's value ... Every constraint on magnitude therefore falls to the second layer" | Same fact | Acceptable: Ingénieur §3.3 Layer 1 explicitly relies on the Master ("specified, with the grammar in full, in the Mémoire de Master") and states only the three properties it needs |
| ch3_method.tex:139-142 reflex path / parse path defined in two sentences | ch1_introduction.tex:56-64 | Same decomposition | Acceptable: the Master defines the terms it uses in tab:dataset and tab:metrics, names the Ingénieur as the runtime's owner (ch3:137-139); no derivation |
| ch3_method.tex:247-264 "The wake corpus" (two paragraphs) incl. l.253-254 "The spotter itself is a classifier head fitted over openWakeWord's frozen feature front end" | ch4_implementation.tex:47-51 (scaffold note: spotter as built, training) | Corpus construction is the Master's (Table 3 "Dataset construction"); the spotter's architecture is the Ingénieur's | Acceptable now (one sentence on the spotter, justified at ch3:248-250). **Watch in issue 10** that Ingénieur Ch4 does not re-describe the corpus |
| ch1_introduction.tex:12-13 "with no network access at any point in the pipeline" | ch1_introduction.tex:129 FR row "with no network access at any point in the pipeline" | Nine-word phrase | Acceptable (a requirement clause, not exposition) |
| ch1_introduction.tex:77 example "form a circle with radius five metres" | ch1_introduction.tex:17 same example | One example utterance | Acceptable; issue 01 sourced the scope paragraph from Ingénieur Ch1 deliberately |
| ch1_introduction.tex:80-81, 127-129 keyword spotter / C4 in one sentence each | ch1_introduction.tex:409-419 | -- | Acceptable (Table 3: Master states C4 in words) |
| ch4_results.tex:140-141, 346-355; ch3:479-481 latency-experiment figures (751; 3,122; 226; 78; 1,063) | Ingénieur Ch5 (prose pending) | Master quotes the Ingénieur's measurements as the selection constraint | Acceptable: author's decision in issue 04 (A1 fail-openly); owner named at each use; Table 3 gives Exp-2 to the Ingénieur and the Master uses only what the rule needs |
| ch5_discussion.tex:281-292 acoustic-robustness experiment named once | Ingénieur Ch5 (pending) | -- | Complies with Table 3 ("Master Ch5 references Exp-3 once"); script PASS |
| Master Ch2 constrained-decoding literature | Ingénieur Ch2 scaffold note l.10-11 "Do not repeat the constrained-decoding survey from the Master Ch. 2" | -- | Complies; Master Ch2 carries no voice-UAV literature (script PASS) and defers robot/aircraft LM control to the Ingénieur (ch2:143-144) |
| Master (no TTFT / preemption latency anywhere; grep "first token", "preempt": Ch1 l.128 names preemption in the C4 sentence only) | Ingénieur Ch3 §3.1 "Preemption and ordering" | -- | Complies with Table 3 / SKILL D6d |
| Ingénieur ch1_introduction.tex:119-121 "the first five [FRs: grammar, dataset, fine-tuning, export pipeline, canonicaliser] are stated in the Mémoire de Master" | Master tab:requirements (ch3:592-618) carries budgets only; those five are the Master's §3.1-§3.5 method, not requirement rows | Cross-document promise about the Master | Not a Master finding; **for issue 10** ("are the subject of the Mémoire de Master's method chapter" would be exact) |
| Ingénieur ch1_introduction.tex:47 "one Raspberry Pi 5 with 8 GB of memory" | Master states no RAM size (issue 03 W9: unrecorded) | Fact present in one document only | See UNVERIFIED |

No paragraph appears in both documents. No hardcoded chapter number of the other document in the
Master; the Ingénieur's two Master mentions with a location say "method chapter"/"Ch 3" only in
`%` comments.

## 10. UNVERIFIED

- Arabic qualifiers: read as matching the English at every point listed in §5 (A5 included), but
  a native-speaker check is out of scope by the task's terms.
- Raspberry Pi 5 memory variant: the Ingénieur states 8 GB (`ingenieur/ch1_introduction.tex:47`);
  the Master states none, and issue 03 W9 recorded that the variant "is recorded nowhere". Which
  board the timing runs used cannot be verified from the repository; if the Ingénieur's 8 GB is
  from `prd.md`, the Master's memory-ceiling discussion (2.5 GiB) would read better with the same
  fact, but no source in `results/` carries it.
- Thermal state of the latency experiment: `results/exp2_latency_budget.md:3` says "cooled" and
  commit `5ed20ba` asserts it; issue 03's W9 note said nothing recorded it at the time. MIN-1's fix
  relies on the results header being right.
- xdvipdfmx "Object @table.3.3 already defined": not present in `main_master.log` (xdvipdfmx
  writes to latexmk's stdout); taken from the task brief. The interpretation (multi-page
  `xltabular` anchor) is consistent with tab:metrics spanning pp. 31-32 in the PDF but was not
  reproduced here.
- Whether `master_ch4.py`'s "configs meeting all six" check (report row l.376) counts criteria
  from data or from the sentence at ch4:376-378 -- relevant only to MIN-5's fix.
- Issue 09's unverified item stands: "widest margin" (ch6:93-94, 99-100) holds on ratios over
  tab:requirements rows; the prefill allowance (missed, cached 328.8 vs 250 ms) is a stage
  allowance, not a requirement row, so it does not enter.

## 11. Examiner view

1. **"Your headline 0.935 is on reference text, and the deployed system recognises 0.690 of the
   same commands from speech. What does the Master's comparison say about the system that
   flies?"** Answered: ch4:13-16 and 58-64 (every accuracy figure is on reference text and
   overstates what the pipeline achieves from audio); ch5:281-292 (0.690 / 0.590 vs 0.935; the loss
   is at the speech stage; EM is "the parser's accuracy given a correct transcript, a level the
   deployed system did not reach"); ch6:23 and all three abstracts ("scored on reference text").
   The Master does not claim the deployed accuracy; the Ingénieur owns it (ch3:528).
2. **"The selection rule's budget was re-baselined to the selected model's own 3,122 ms. Have you
   not moved the goalposts?"** Answered: ch4:357-364 ("the re-baselined budget cannot test
   Qwen2.5-0.5B, which satisfies it by construction. It still tests Llama-3.2-1B ... and
   SmolLM2-360M ... is shown neither to satisfy it nor to miss it"); ch4:366-373 (selection
   unchanged under the reading most favourable to the others, on a significant EM gap); ch5:52-68
   (the trade-off does not reach the decision under a rule of this form); ch6:31-37; the
   abstracts state the re-baseline. The remaining exposure is that SmolLM2-360M was never measured
   end to end (ch6:112-116 makes it step 3).
3. **"Where are the code, the dataset and the six GGUF artefacts, and could we rerun this?"**
   Partly answered: ch3:496-509 pins llama.cpp b10863, whisper.cpp 52a939a, peft 0.19.1,
   transformers 5.0.0, PyTorch 2.10.0, the system prompt, seeds and caps; ch3:485-494 the timing
   protocol; tab:lora the recipe; every table names its `results/` source. Not answered: no
   repository or artefact location appears anywhere in the document (issue 03, "Not done, by the
   author's decision ... revisit before submission"); the GGUF converter commit is unpinned
   (ch3:502-504); the control's training image is unrecorded (ch3:502). This is a known decision,
   not a new finding, but it is the question a jury asks first about reproducibility.
