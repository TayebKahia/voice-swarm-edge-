# Citation / presentation review: thesis/ingenieur/ch5_validation.tex (Ingénieur Ch5)

Reviewed state: the working-tree file of 2026-09-24, 407 lines, last changed in b13c611. The issue
header gives 402 lines, which is stale. Line numbers below are for the 407-line file and match the
pre-review report (dregon l.237, McNemar/Dunn l.281-282).
Dimensions covered: D5, D7, D8, D9, D11, D12, plus fig:keyword-curve and the three generated
tables. D1/D2/D4/D6/D10 belong to the argument agent, and D3 (arithmetic) is the script's.
I did not redo any number the script marks PASS. The table-versus-prose checks (D7e) compare the
prose with the generated .tex, not with results/.

## 1. Verdict

The chapter is **ready after fixes**. Two things are clean: the build, and the figure against its
caption. The document builds from scratch into a scratch folder with 0 errors, 0 undefined
citations or references, no `Float too large`, and no Overfull or Underfull box anywhere. Every
element the caption of fig:keyword-curve names is in the drawn figure.

The three existing citations are correctly entered. mcnemar1947 and dunn1961 support their
sentence. dregon is PARTIAL, because the "evaluation partition" belongs to this project and not to
DREGON.

The MAJOR findings are all missing citations for methods or tool behaviour:
- Tukey's comparison and Cochran's Q are named after their authors but carry no citation, while
  McNemar and Bonferroni in the same paragraph do.
- The language-model server's once-per-second check, which the chapter gives as the located cause
  of the preemption-recovery miss, has no citation. I confirmed it in the llama.cpp source.
- The McNemar variant is not stated. It matters: the two pairs reported as "not significant"
  (p = 0.0051 and 0.0053) are the continuity-corrected chi-square p-values. The exact test gives
  0.0046 for both, which is below alpha = 0.0050.

The rest is caption completeness in the generated tables and small language points. Most caption
fixes belong in `eval/tables.py`, not in the chapter.

## 2. Scorecard

| Dim | Result |
|---|---|
| D5 References | ISSUES (8): 4 MAJOR, 4 MINOR |
| D7 Figures and tables | ISSUES (5): 4 MINOR, 1 NIT |
| D8 Language and style | ISSUES (8): 1 MINOR, 7 NIT |
| D9 LaTeX and build | PASS: clean scratch build, 0 errors, 0 undefined, 0 Overfull/Underfull, no markers, `~` everywhere |
| D11 Self-containment | ISSUES (2): 2 MINOR (P4 is counted under D5) |
| D12 Headings and register | ISSUES (3): 2 MINOR, 1 NIT |

## 3. Findings

| # | Sev | Dim | file:line | Quoted text | Problem | Evidence | Proposed fix |
|---|---|---|---|---|---|---|---|
| P1 | MAJOR | D5d | ch5_validation.tex:275, 371 | "Tukey's pairwise comparison separates 5~dB from clean, 20 and 15~dB, and no other pair." | An author-named method with no `\cite`. SKILL §4 says "Never write author names without a citation key". The same paragraph cites McNemar and Dunn, so the gap is visible to a reader. references.bib (74 entries) has no Tukey entry. | `grep -i tukey thesis/references.bib`: no hit. The implementation is `scipy.stats.tukey_hsd` (eval/exp4.py:144). Dunn 1961, ref. [2], gives the HSD's primary source as Tukey, "The problem of multiple comparisons", mimeographed notes, Princeton (1953). | The author adds one entry after checking the primary source (SKILL §4). Candidates: (a) Tukey 1953, reprinted in *The Collected Works of John W. Tukey*, Vol. VIII (Chapman & Hall, 1994); (b) Kramer, "Extension of Multiple Range Tests to Group Means with Unequal Numbers of Replications", *Biometrics* 12(3):307-310, 1956, doi:10.2307/3001469 (Crossref-verified; the Tukey-Kramer form scipy computes, identical to Tukey's HSD at equal n). Do not use Tukey 1949 (*Biometrics* 5(2):99, doi:10.2307/3001913): that paper describes a different procedure. Then write "Tukey's honestly-significant-difference comparison~\cite{...}" at l.275, and keep l.371 without a second cite. |
| P2 | MAJOR | D5d | ch5_validation.tex:279-281 | "Cochran's $Q$ rejects equality across the five conditions ($Q = 61.05$, 4 degrees of freedom, $p = 1.7 \times 10^{-12}$)." | An author-named test with no `\cite`. references.bib has no Cochran entry. | `grep -i cochran thesis/references.bib`: no hit. Crossref: Cochran, W. G., "The Comparison of Percentages in Matched Samples", *Biometrika* 37(3-4):256-266, 1950, doi:10.1093/biomet/37.3-4.256. | The author adds this entry after checking it against the publisher's page, then writes "Cochran's $Q$~\cite{cochran1950}". |
| P3 | MAJOR | D5c | ch5_validation.tex:117-118 | "The server accepts a new request only after it has registered the closed connection, which it checks once per second." | An uncited claim about a tool's internals, and it is the located cause of a missed criterion. No results/ file contains it. Its only source is STATE.md l.1539 ("HTTP_POLLING_SECONDS=1"), which the reader never sees. The claim is true: llama.cpp master, `tools/server/server-context.cpp:39`, has `constexpr int HTTP_POLLING_SECONDS = 1;`, used as the response-reader poll interval (l.4038, 4232). | STATE.md:1539. Raw file from github.com/ggml-org/llama.cpp master, fetched 2026-09-24. The bib entry `llamacpp` pins version b10863 (see UNVERIFIED U2). | Attach the existing key and name the mechanism: "The server polls for a closed connection once per second (its HTTP polling interval~\cite{llamacpp}), and it accepts a new request only after it has registered the closed one." |
| P4 | MINOR | D5b / D11 | ch5_validation.tex:236-237 | "with rotor noise from the evaluation partition of the DREGON recordings~\cite{dregon}" | PARTIAL support. DREGON supports "rotor noise recorded on a UAV". It does not define an "evaluation partition". That split is this project's: the last 30% of one DREGON flight, held back from augmentation. The Ingénieur never defines it (`grep -i partition ch*.tex` finds only this line and two unrelated uses). A reader will take it for a split DREGON publishes. | dregon.inria.fr/datasets/dregon: pure-motor and in-flight noise recordings, no train/evaluation split. data/dataset_card.md:185-187 ("the last 30% are held back"). docs/adr/0004 "Partition". | "with rotor noise recorded in flight by the DREGON dataset~\cite{dregon}, taken from the last 30\% of the flight, which no training augmentation used, and mixed digitally ..." (or state the held-out portion however the Master's Ch3 does, and use the same words). |
| P5 | MAJOR | D5d | ch5_validation.tex:281-285 | "McNemar's test~\cite{mcnemar1947} on each of the ten pairs ... The comparison of 10~dB with 5~dB is not significant, at $p = 0.0051$ ..." | The test variant is neither stated nor cited, and it decides two reported comparisons. The harness uses the exact binomial test below 25 discordant pairs and Edwards' continuity-corrected chi-square above. Both "not significant" pairs are chi-square results. The exact test gives 0.0046 for both, below alpha = 0.0050. A reader cannot reproduce 0.0051 without knowing the variant. The argument agent should see this under D4c/D10a. | results/exp3_pi_analysis.md:39, 43 (`chi2_cc`, 0.0053 / 0.0051). eval/stats.py:113 (`EXACT_BELOW_DISCORDANT = 25`), l.171-178. Recomputed with scipy: binomtest(15, 51) p = 0.00460; binomtest(8, 33) p = 0.00455. Crossref: Edwards, "Note on the 'Correction for Continuity' in Testing the Significance of the Difference between Correlated Proportions", *Psychometrika* 13(3):185-187, 1948, doi:10.1007/BF02289261. | State the rule where the test is named: "McNemar's test~\cite{mcnemar1947}, exact below 25 discordant pairs and with Edwards' continuity correction~\cite{edwards1948} above, a rule fixed before measurement". The author adds edwards1948. Do not change the verdicts. Whether to report the exact p-values beside them is the author's decision, with the argument agent. |
| P6 | MINOR | D5c | ch5_validation.tex:147 | "a false-reject rate of 0.050 with an exact 95\% interval of [0.001, 0.249]" | The interval method is named only as "exact" and not cited. It is Clopper-Pearson. | eval/wake_real.py:26, 61-67 (`clopper_pearson`, beta quantiles). Crossref: Clopper & Pearson, "The Use of Confidence or Fiducial Limits Illustrated in the Case of the Binomial", *Biometrika* 26(4):404-413, 1934, doi:10.1093/biomet/26.4.404. | "an exact (Clopper--Pearson) 95\% interval~\cite{clopper1934}". The author adds the entry. |
| P7 | MINOR | D5c | ch5_validation.tex:211 | "That is 2.33 per hour, with a 95\% Poisson interval of [0.06, 12.98]" | The interval is the exact chi-square (Garwood) interval, which is neither named nor cited. "Poisson interval" alone does not identify it. | train/train_wake.py:339-343 (`chi2.ppf(0.025, 2k)/2`, `chi2.ppf(0.975, 2k+2)/2`). Crossref: Garwood, "Fiducial Limits for the Poisson Distribution", *Biometrika* 28(3-4):437-442, 1936, doi:10.1093/biomet/28.3-4.437. | "with an exact 95\% Poisson interval~\cite{garwood1936}". The author adds the entry. |
| P8 | MINOR | D5c | ch5_validation.tex:51; generated/table20_end_to_end.tex caption | "the bootstrap resamples"; "Intervals are 95\% bootstrap over utterances" | The bootstrap is used for every CRR, WER and EM-CRR interval but is never cited, and its form (percentile bootstrap, 10,000 resamples over utterances) is not given in the Ingénieur. The Master (ch3_method.tex:576, 641) also leaves it uncited, so both documents should get one fix. | eval/stats.py:50, 56, 76. Crossref: Efron, "Bootstrap Methods: Another Look at the Jackknife", *Ann. Statist.* 7(1), 1979, doi:10.1214/aos/1176344552. | "percentile bootstrap intervals~\cite{efron1979} over utterances, 10{,}000 resamples". The author adds the entry. |
| P9 | MINOR | D7b | generated/exp2_latency_budget.tex:6 (Table 5.1) | "Raspberry Pi 5, cooled, governor \texttt{performance}, cores pinned (...)" | The caption is not self-contained. (a) No unit anywhere: the p50/p95/p99/Target columns are milliseconds, but neither the header nor the caption says so. (b) The long caption, which is the one printed above the table, never says what is tabulated. Only the short List-of-Tables title does. (c) The reflex rows have n = 78, and the protocol and prose give 80 trials per condition; the caption does not explain the difference. (d) No takeaway. | Built PDF p.44: header "p50 p95 p99 Target p95". The 78 of 80 comes from l.101-106 (one take missed on both replays). | In the renderer: open the caption with "Measured latency of every stage of both paths against its p95 target, in ms." Add "Reflex rows: n = 78 of 80 trials, one hold take being missed on both replays." Close with "Every judged row misses except the endpointing wait, the decode and validation." Or put "(ms)" in the header. |
| P10 | MINOR | D7b | generated/table20_end_to_end.tex:6 (Table 5.2) | "EM is the same items as reference text through the same parser, so EM - CRR is the cost of the speech stage." | (a) The caption never says what is tabulated (it opens with the pipeline), and it has no takeaway. (b) The quoted sentence is ungrammatical. | Built PDF p.48. | In the renderer: open with "Accuracy of the parse path, and the stage sum of its latency, at each noise level." Then "EM is the parser's exact match on the reference text of the same items". End with a takeaway, e.g. "CRR falls from 0.690 clean to 0.485 at 5 dB, and the whole loss is in the speech stage." |
| P11 | MINOR | D7e | generated/requirements_summary.tex, row "Keyword false rejects" | "hold 0.05 [0.00, 0.25]; abort 0.00 [0.00, 0.17]" | The table prints two decimals where the prose (l.147-148) and the chapter's other rates use three. The hold lower bound 0.001 prints as 0.00, so a reader sees an interval that includes zero misses, which the prose's [0.001, 0.249] does not. | Prose l.147-148: 0.050 [0.001, 0.249], 0.000 [0.000, 0.168]. Same table: "0.690", "1.000". | Render three decimals: "hold 0.050 [0.001, 0.249]; abort 0.000 [0.000, 0.168]". |
| P12 | MINOR | D7a / D7e | ch5_validation.tex:138-140 | "Two intervals inside the span have no budget row and are recorded beside the stages: the segment's wait for the parse-path worker, 73~ms at p95, and the overhead ..." | "recorded beside the stages" points the reader at Table 5.1, but neither interval is in it. They exist only in results/exp2_analysis.md:12, 16. The reader therefore cannot see why the stage p95s in Table 5.1 do not add up to its end-to-end row. | thesis/generated/exp2_latency_budget.tex has no queue or request-overhead row. | Add the two rows to the renderer, with Target "--", and keep the sentence. If they stay out of the table, say "measured alongside the stages but not tabulated". |
| P13 | MINOR | D11a | generated/exp2_latency_budget.tex:32; generated/table20_end_to_end.tex:6, 20 | "... and the core-0 frame budget: \texttt{results/exp2\_analysis.md}."; "Host: \texttt{drone-pi}." | The table notes point the reader to repository files and a machine hostname. The reader holds only the thesis (SKILL §2). | Built PDF p.44 and p.48. | In the renderer, drop the file pointers, or replace them with the section that reports the item (e.g. "the tests across SNR: Section~\ref{sec:acoustic-robustness}"). Replace "Host: drone-pi" with "Measured on the Raspberry Pi 5". |
| P14 | MINOR | D8e | generated/table20_end_to_end.tex, generated/requirements_summary.tex; ch5_validation.tex:44 | "SNR & n & CRR & 95\% CI & WER \% ..."; "a CSV row per trial" | The generated tables hand-type CRR, EM, WER and SNR, plus CI, HTTP and Wi-Fi, instead of `\gls`. The print is correct only because the prose expanded them earlier. l.44 "CSV" has no key in shared/acronyms.tex, and Ch1 l.224 also uses it. | acronyms.tex has crr, em, wer, snr; no csv, ci or http. SKILL §4.5. | Make the renderer emit `\gls{crr}` etc. in headers and notes. Either add `\newacronym{csv}{CSV}{comma-separated values}` (the author's call: it appears in two chapters) or write "one comma-separated row". |
| P15 | MINOR | D11 | ch5_validation.tex:163, 228, 291/405 | "It judges the keyword false-accept criterion"; "the clean-audio recognition and recognition-in-noise criteria"; "the criterion of the \emph{M\'emoire de Master}" | Three places drift from Ch1's criterion names (tab:nonfunctional-requirements l.177, 180; l.231 for Safe failure), against the 2026-09-24 naming amendment. All other criterion names in Ch5 match Ch1 exactly (see §4c). | ch1_introduction.tex:177 "Keyword false accepts", :180 "Recognition in noise", :231 "the one the \emph{M\'emoire de Master} calls Safe failure". | l.163 "It judges the Keyword false accepts criterion"; l.228 "the Clean-audio recognition and Recognition in noise criteria" (or keep lower case but unhyphenated); l.291 "... set by the \emph{M\'emoire de Master}, whose Safe failure criterion it is." |
| P16 | MINOR | D12a | ch5_validation.tex:301, 154 | "\paragraph{No tuning.}"; "\paragraph{Not measured.}" | Neither heading is a noun phrase. "No tuning" states a claim, and "Not measured" states a status (SKILL §2 Headings). | SKILL §2: "A heading is a noun phrase, not a sentence or a claim." | "Tuning and the test set" (or "Candidate remedies"); "Delays outside the measurement". |
| P17 | MINOR | D12c | ch5_validation.tex:322-323 | "The sticky soft-temperature-limit flag was set from 17:45, during the last condition, 5~dB, and clear before it." | Run-log narration: a time of day tells the reader nothing, and "sticky" is jargon that is not explained. | SKILL §2 Register: "Describe the work, not the working." | "The soft-temperature-limit flag, which stays set once raised, was set part-way through the last condition (5~dB) and clear before it." |
| P18 | NIT | D8g | see §7 | -- | 15 sentences exceed about 40 words. The worst are l.70-74 (67 words), the caption at l.184-188 (57) and l.369-373 (56). | Word counts in §7. | Split at the colon or semicolon each already contains, e.g. l.70: "... for 80 trials per condition. The two conditions are idle, ... and loaded, ...". |
| P19 | NIT | D8b | ch5_validation.tex:319; generated/table20 caption | "It serves to show how latency moves with noise." | "show" is on the SKILL.md avoid-list. | SKILL §2 "Avoid: shows". | "It tracks how latency moves with noise." Make the same change in the renderer's "so it shows". |
| P20 | NIT | D12c | ch5_validation.tex:116, 150, 177, 216 | "The client's part of the cancellation is fast"; "At 20 takes per class it could not have been"; "the threshold does little of the classification"; "and so decides nothing either" | Conversational phrasing. | SKILL §2 Register. | "The client's part of the cancellation takes at most 6~ms at p95"; "With 20 takes per class, the criterion cannot be demonstrated even with no miss: the upper bound is then 0.168"; "where the heads' scores saturate, so that most detections do not depend on the threshold"; "and is equally inconclusive". |
| P21 | NIT | D7b | ch5_validation.tex:191-192 | "which is why the upper points lie on one vertical line" | "Upper" is ambiguous: the points on the vertical line are the highest thresholds, and some of them sit low on the y-axis (abort at 0.000-0.007). The caption also stops short of the takeaway. | results/figure_keyword_curve.png; wake_training.json roc.test thresholds 0.88-0.999 all at 2.33/h. | "which is why the points for thresholds of 0.88 and above lie on one vertical line at 2.33 per hour. Both false-reject rates lie below their budget, while the false-accept interval straddles its budget." |
| P22 | NIT | D8 | ch5_validation.tex:105 | "the 40 \emph{swarm abort} takes all fired the abort class, and 38 of the 40 \emph{swarm hold} takes" | The keyword phrases are `\emph` here but `\texttt` in the figure caption (l.184) and in Ch1 tab:functional-requirements (l.130). | -- | Use `\texttt{swarm abort}` / `\texttt{swarm hold}`. |
| P23 | NIT | D8 | generated/table20 (header and notes), generated/exp2_latency_budget.tex | "EM - CRR"; "(clean, >= 0.80)"; "pre-emption outcomes"; "the Wi-Fi hop"; "of which Pi compute and publish"; "the 200 golden utterances" | Typography and wording differ from the prose. The table uses a hyphen for minus and ASCII `>=` (Table 5.3 has $\geq$), and writes "pre-emption" where the prose has "preemption". It also has "Wi-Fi hop" for "wireless hop" (l.155), "Pi compute and publish" for "the board's computation and publication" (l.90), and "golden utterances" for "golden-set utterances". | Built PDF p.44, p.48. | In the renderer: `$-$`, `$\geq$`, "preemption", "wireless hop", "board computation and publication", "golden-set utterances". |
| P24 | NIT | D8a | ch5_validation.tex:360 | "an initial spread of 0.5~m is small beside a formation several metres across" | "several metres" is vague. | SKILL §2 "Quantitative specificity". Ch4 l.322 gives no radius value either. | Give the commanded radius and spacing, e.g. "beside a circle of radius X~m" (take the value from the controller configuration, via Section~\ref{sec:swarm-controller}). |
| P25 | NIT | D8c | ch5_validation.tex:74-75 | "The loaded condition is preceded by 300~s of the same load, after which the processor was at 73.0~$^{\circ}$C." | The sentence switches tense. The protocol paragraphs are otherwise consistently in the present, and measured events in the past. | Template D8c. | "... is preceded by 300~s of the same load, which brings the processor to 73.0~$^{\circ}$C" (or put both verbs in the past). |
| P26 | NIT | D8 (terms) | ch5_validation.tex:236, 169; generated/requirements_summary.tex | "rotor noise"; "Operating curve"; "Formation control, five drones" | Terms drift from Ch1. Ch1 says "propeller-type noise" (l.180, 211) where Ch5 says "rotor noise". Ch1 l.205 calls the keyword curve "one \gls{roc} curve"; Ch5 plots false rejects against false accepts per hour, which is not an ROC, so Ch5's "operating curve" is the better term. The summary table says "drones" where the Ch5 prose (and Ch4) say "vehicles". | ch1_introduction.tex:180, 205, 211. | Pick one term for each. The simplest fix: Ch5 says "rotor (propeller-type) noise" once, and Ch1 l.205 says "one operating curve" (a Ch1 edit, for the author). |

## 4. Figure and table checks

### 4a. fig:keyword-curve against the drawn figure (results/figure_keyword_curve.png; PDF and PNG from the same eval/plots.py run, 14:12)

| Caption element | In the figure? | Note |
|---|---|---|
| For each class, swarm hold and swarm abort | Yes | Two curves in the legend: blue hold, orange abort |
| FRR on the 300 synthetic test takes of that class | Yes | Legend "(n = 300 test takes)" for both; y-label "False-reject rate (synthetic test takes)" |
| Against false accepts per hour on 0.429 h of ambient speech, both classes summed | Yes | x-label "... both classes together (0.429 h, test split)" |
| Threshold sweeps the grid from 0.05 (right) to 0.999 | Yes | "threshold 0.05" annotated at the right end (53.6/h); grid is 98 points, 0.05-0.99 step 0.01, plus 0.995, 0.998, 0.999 |
| Horizontal axis logarithmic | Yes | 0.1 / 1 / 10 decades |
| Open circles mark the operating threshold 0.999 | Yes | Two open circles at (2.33, 0.027) and (2.33, 0.007), annotated "operating threshold 0.999" |
| Shaded band = 95% interval of the FA rate at that threshold | Yes | Band from 0.06 to 12.98, labelled in the plot |
| Band contains the FA budget of one per hour (dashed) | Yes | Red dashed vertical line at 1 |
| Dotted line = FRR budget 0.10 | Yes | Green dotted horizontal line at 0.10 |
| Every threshold from 0.88 up gives the same FA rate, so the upper points lie on one vertical line | Yes (wording, P21) | Thresholds 0.88-0.999 are all at 2.33/h |
| 80 ms frames, 1.0 s debounce | Not drawn (method) | Consistent with l.165-166 |
| Vector | Yes | Script: PDF is vector |

The prose interprets the figure (l.169-178: the flat top, and the lack of any threshold that would
remove the single false accept). The figure is referenced at l.169, before the float.

### 4b. Generated tables

| Table | \ref before float | Interpreted in text | Caption self-contained | Prose = generated .tex (D7e) | Stage-sum naming |
|---|---|---|---|---|---|
| tab:latency-budget (5.1) | l.64 (script) | Yes, l.86-143 row by row | No: units, what is tabulated, n = 78, takeaway (P9) | Yes for every quoted value: 545/547, 540, 6/18, 1,265/1,266 vs 850, 1,195 (p50 601), 3,122 (n 226), 3,602, 1,449/1,200, 751/250, 915/1,100, 480/500, validation 0 (< 1 ms) vs 50. The 73 ms and 8 ms are not in the table (P12) | n/a |
| tab:end-to-end (5.2) | l.230 (script) | Yes, l.247-325 | Partly: n and units given; what is tabulated and takeaway missing; grammar (P10) | Yes: 0.690 [0.625, 0.750]; EM 0.935; +0.245 [0.185, 0.310]; 0.590 [0.520, 0.660]; +0.345 [0.280, 0.410]; +0.450 [0.380, 0.520]; WER 23.3/28.8/36.0; safe-failure 0.032 (2/62), 0.014-0.039; 103 failures at 5 dB; 15 dB 0.650; 5 dB 0.485; stage sum 2869 → 2977 | Called a stage sum at l.316-317 and in the column header ("Stage sum p50/p95 (ms)"); the caption describes it as a sum and routes end-to-end to Table 5.1. No other chapter uses the column. PASS |
| tab:requirements-summary (5.3) | l.382 (script) | Yes, l.382-407 | Yes (the verdict rule is stated) | Yes except the precision of the keyword false-reject intervals (P11). Counts 7 met / 5 missed / 2 not demonstrated / 2 not yet run / 1 planned = 17 | n/a |

Every table's last row is present in the built PDF: "Preemption recovery" (p.44), "5 dB" (p.48)
and "Offline operation" (p.53). No `Float too large`. As the brief says, the float placement of
fig:keyword-curve (its own page, p.47) is left to B13.

### 4c. Criterion names against Ch1 (tab:functional-requirements, tab:nonfunctional-requirements)

These match exactly, as headings or in the prose: Reflex latency, End-to-end latency, Per-stage
attribution, Preemption recovery, Keyword false rejects, Keyword false accepts (l.210 heading),
Clean-audio recognition, Recognition in noise (l.260 heading), Collisions, Formation accuracy,
Offline speech recognition, Offline operation, Live demonstration. "Reflex-path requirement" and
"swarm-controller requirement" follow Ch1's own attributive usage (ch1 l.143-146). The drifts are
listed in P15. The summary table uses Ch1's names verbatim.

## 5. Citation table (D5b)

| Key | file:line | Claim it carries | Verdict | Note |
|---|---|---|---|---|
| dregon | ch5_validation.tex:237 | The rotor noise mixed into the golden set comes from the "evaluation partition of the DREGON recordings" | PARTIAL | Dataset page (dregon.inria.fr/datasets/dregon): pure motor-noise and in-flight noise recordings from a UAV-embedded array, with no train/evaluation split. The partition is this project's (P4). Bib entry checked against Crossref: title, authors (Strauss, Mordel, Miguet, Deleforge), IROS 2018, pp. 1-8 and DOI all match. IEEE Xplore and ACM DL pages were not readable (empty / 403); Crossref and the dataset page were. |
| mcnemar1947 | ch5_validation.tex:281 | McNemar's test for paired correct/incorrect outcomes on the same 200 utterances | SUPPORTS | Crossref abstract: "Two formulas are presented for judging the significance of the difference between correlated proportions". Bib checked against Crossref: *Psychometrika* 12(2):153-157, 1947, doi:10.1007/BF02295996, all match. The variant actually used (exact / Edwards) is not stated (P5). |
| dunn1961 | ch5_validation.tex:282 | "the Bonferroni-corrected level ... alpha = 0.0050" (0.05 over 10 pairs) | SUPPORTS | Full text (JSTOR copy) read: m pre-chosen comparisons, and "using a Bonferroni inequality" to bound the joint coverage (eq. 4). Dunn applies it to t-intervals on normal means; dividing alpha by m for McNemar tests is the standard generalisation. Bib checked against Crossref: *JASA* 56(293):52-64, 1961, doi:10.1080/01621459.1961.10482090, all match. |

Uncited methods or tool behaviour with no bib entry: Tukey's HSD (P1), Cochran's Q (P2), the
McNemar continuity correction (P5), the Clopper-Pearson interval (P6), the Garwood Poisson
interval (P7) and the bootstrap (P8). The llama-server polling claim (P3) has an existing key
(`llamacpp`) and needs only the `\cite`. Every DOI proposed above was resolved through
api.crossref.org on 2026-09-24. No bib entry was added (SKILL §4).

Checked and not findings: whisper.cpp (l.49) and whisper `tiny.en` (l.235) are cited at their
first mention in Ch1/Ch3/Ch4. Silero and qwen2.5 in the Table 5.2 caption are cited earlier in the
document (silero ×3, qwen25). The artificial potential field (l.350) is introduced in Ch3/Ch4.
The one-way ANOVA and the arcsine transform are textbook methods, and leaving them uncited is
common practice. The Master's figures (l.37-38, 268-271, 295-297) are named in words, per the
write-once rule.

## 6. Build result (D9)

- Engine as in `thesis/.latexmkrc`: `$pdf_mode = 5` (XeLaTeX), biber, makeglossaries. The explicit
  `-outdir` overrides the per-thesis folder, so thesis/build/ was not touched.
- Command: `cd thesis && latexmk -outdir=/tmp/claude-1000/-home-kahia-tayeb-PFE/81f115bb-6d39-43f8-876e-938a0b6bc86e/scratchpad/build_ing main_ingenieur.tex`, run on an empty folder.
- Exit 0; 56 pages; `grep -c '^!'` = 0; no `Citation.*undefined`, no `Reference.*undefined`, no
  `Float too large`, no multiply-defined labels. Overfull: 0 and Underfull: 0 in the whole log
  (Ch5 spans log lines 2223-2235, pp. 41-50).
- The List of Acronyms prints (CRR, EM, JSON, SNR and WER among them). Ch5's `\gls` calls print the
  short form, because each was first expanded earlier in the document.
- `tools/check_tex.py ch5_validation.tex`: the only problems are 23 cross-chapter `\ref`s (expected
  false positives; all resolve in the build). 3 cites resolve. No non-ASCII in the body.
- No `\TODO`, `\CHECK` or `\figtodo`. Labels follow chap:/sec:/fig:/tab:. Every `\ref`/`\cite` is
  preceded by `~`, and every unit after a number carries `~`.
- Ch6 (scaffold) `\ref`s no Ch5 label yet. The Ch5 labels referenced elsewhere are
  `sec:latency-experiment`, `sec:acoustic-robustness`, `sec:keyword-spotter-evaluation` and
  `sec:formation-control` (from Ch3/Ch4), and all of them exist.

## 7. Sentences over ~40 words (D8g)

Counts include numbers and units, with `\ref`/`$...$` counted as one word each.

| Line | Words | Opening |
|---|---|---|
| 25 | 45 | "A criterion is met or missed on the point estimate of the statistic its budget names, with one exception: ..." |
| 44 | 41 | "Every trial is kept as one record: a CSV row per trial ..." |
| 70 | 67 | "The reflex path is measured on the author's 40 recorded keyword takes, 20 per class, each replayed twice ..." |
| 94 | 51 | "Loading the parse path raised the reflex path's p95 by 2~ms, and no frame in any condition ..." |
| 145 | 49 | "The author's 40 takes, scored at the operating threshold by the keyword-spotter evaluation's own procedure, ..." |
| 160 | 43 | "The keyword-spotter evaluation scores the two trained heads on held-out recordings, ..." |
| 184 | 57 | Caption: "For each class, \texttt{swarm hold} and \texttt{swarm abort}, the false-reject rate ..." |
| 233 | 41 | "The 200 golden-set recordings, one speaker in one session, are passed through the parse path ..." |
| 252 | 44 | "A recognition error that left the intent right but a slot wrong accounts for 23, ..." |
| 261 | 42 | "Parser accuracy on reference text does not depend on the audio, so the whole fall ..." |
| 264 | 43 | "At 10~dB, recognition errors that change the intent rise from 5 to 19 ..." |
| 268 | 46 | "The clean \gls{wer} matches, within a fraction of a point, the figure that ..." |
| 316 | 41 | "The last column of Table~\ref{tab:end-to-end} is a stage sum, not an end-to-end latency: ..." |
| 351 | 46 | "Collisions are counted after the clamp, against a distance smaller than the clamp distance ..." |
| 369 | 56 | "A one-way analysis of variance across the three formations rejects equality, ..." |

l.25, 44, 233 and 316 are borderline and read acceptably. The ones worth splitting are l.70, 94,
145, 184, 268, 351 and 369.

## 8. UNVERIFIED

- U1. The DREGON bib entry's `pages = {1--8}` matches Crossref. IEEE Xplore itself could not be
  read, so the publisher page was not checked directly.
- U2. `llamacpp` pins version b10863. I verified `HTTP_POLLING_SECONDS = 1` only on llama.cpp
  master of 2026-09-24, not at tag b10863 (P3). Before citing it, the author should confirm that
  the deployed build has the same constant.
- U3. The chapter does not say how the active-speech level (l.237-238) is measured.
  data/mix_noise.py:13-18 uses its own frame-energy rule, not ITU-T P.56. If Master Ch3 defines
  it, one clause and a cross-document mention would do. That is a D10a question for the argument
  agent.
- U4. The "sticky" soft-temperature-limit flag (l.322) is a statement about Raspberry Pi firmware
  (the `vcgencmd get_throttled` bits) with no source in the bib. I did not check it against
  Raspberry Pi documentation.
- Out of scope, noted for the author: eval/stats.py:109-111 says that "every comparison this
  project runs falls below" 25 discordant pairs, so the exact test is always used. The acoustic
  experiment contradicts this: 7 of its 10 pairs are `chi2_cc` (results/exp3_pi_analysis.md:34-43).
  The code comment is stale.
