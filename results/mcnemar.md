### McNemar tests on the Surface-B predictions (RQ1)

Paired per-item predictions from `results/surface_b_preds/`, grammar on, scored
by `eval/metrics.py`. Cells: **a** both correct, **b** A correct and B wrong,
**c** A wrong and B correct, **d** both wrong. Only **b** and **c** carry
evidence about the difference; **a** and **d** say how much of the split the two
systems agreed on. The exact binomial test is used below 25 discordant pairs;
the two model comparisons against smollm2-360m exceed that and use the
continuity-corrected chi-square. Both p-values are carried in the CSV, and the
verdict is the same under either test for every row.

Bonferroni within each family of three: alpha = 0.0167 (family alpha 0.05).

#### Family 1 -- model against model, `test_golden`, Q4_K_M (confirmatory)

| A | B | n | EM A | EM B | a (both) | b (A only) | c (B only) | d (neither) | b+c | test | p | alpha | significant |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | ---: | ---: | :--- |
| llama-3.2-1b-instruct | qwen2.5-0.5b-instruct | 200 | 0.9100 | 0.9350 | 182 | 0 | 5 | 13 | 5 | exact | 0.0625 | 0.0167 | no |
| llama-3.2-1b-instruct | smollm2-360m-instruct | 200 | 0.9100 | 0.7600 | 148 | 34 | 4 | 14 | 38 | chi2_cc | 2.54587e-06 | 0.0167 | yes |
| qwen2.5-0.5b-instruct | smollm2-360m-instruct | 200 | 0.9350 | 0.7600 | 149 | 38 | 3 | 10 | 41 | chi2_cc | 1.09681e-07 | 0.0167 | yes |

#### Family 2 -- Q4_K_M against Q8_0 within each model, `test_golden` (confirmatory)

| A | B | n | EM A | EM B | a (both) | b (A only) | c (B only) | d (neither) | b+c | test | p | alpha | significant |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | ---: | ---: | :--- |
| llama-3.2-1b-instruct Q4_K_M | llama-3.2-1b-instruct Q8_0 | 200 | 0.9100 | 0.9150 | 182 | 0 | 1 | 17 | 1 | exact | 1 | 0.0167 | no |
| qwen2.5-0.5b-instruct Q4_K_M | qwen2.5-0.5b-instruct Q8_0 | 200 | 0.9350 | 0.9300 | 186 | 1 | 0 | 13 | 1 | exact | 1 | 0.0167 | no |
| smollm2-360m-instruct Q4_K_M | smollm2-360m-instruct Q8_0 | 200 | 0.7600 | 0.7900 | 144 | 8 | 14 | 34 | 22 | exact | 0.286279 | 0.0167 | no |

#### Secondary -- descriptive, not part of either correction

The model comparison repeated at Q8_0, and the quantisation pairs on the other
two splits. Reported so the confirmatory result can be seen not to depend on
the split or the quantisation it was run at; not corrected, and not evidence
in their own right.

| A | B | n | EM A | EM B | a (both) | b (A only) | c (B only) | d (neither) | b+c | test | p | alpha | significant |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | ---: | ---: | :--- |
| llama-3.2-1b-instruct | qwen2.5-0.5b-instruct | 200 | 0.9150 | 0.9300 | 182 | 1 | 4 | 13 | 5 | exact | 0.375 | 0.0167 | no |
| llama-3.2-1b-instruct | smollm2-360m-instruct | 200 | 0.9150 | 0.7900 | 154 | 29 | 4 | 13 | 33 | chi2_cc | 2.9426e-05 | 0.0167 | yes |
| qwen2.5-0.5b-instruct | smollm2-360m-instruct | 200 | 0.9300 | 0.7900 | 155 | 31 | 3 | 11 | 34 | chi2_cc | 3.64851e-06 | 0.0167 | yes |
| llama-3.2-1b-instruct Q4_K_M | llama-3.2-1b-instruct Q8_0 | 240 | 0.9583 | 0.9625 | 229 | 1 | 2 | 8 | 3 | exact | 1 | 0.0167 | no |
| qwen2.5-0.5b-instruct Q4_K_M | qwen2.5-0.5b-instruct Q8_0 | 240 | 0.9542 | 0.9583 | 229 | 0 | 1 | 10 | 1 | exact | 1 | 0.0167 | no |
| smollm2-360m-instruct Q4_K_M | smollm2-360m-instruct Q8_0 | 240 | 0.8125 | 0.8125 | 183 | 12 | 12 | 33 | 24 | exact | 1 | 0.0167 | no |
| llama-3.2-1b-instruct Q4_K_M | llama-3.2-1b-instruct Q8_0 | 150 | 0.8133 | 0.8000 | 119 | 3 | 1 | 27 | 4 | exact | 0.625 | 0.0167 | no |
| qwen2.5-0.5b-instruct Q4_K_M | qwen2.5-0.5b-instruct Q8_0 | 150 | 0.7467 | 0.7333 | 109 | 3 | 1 | 37 | 4 | exact | 0.625 | 0.0167 | no |
| smollm2-360m-instruct Q4_K_M | smollm2-360m-instruct Q8_0 | 150 | 0.6600 | 0.6067 | 87 | 12 | 4 | 47 | 16 | exact | 0.0768127 | 0.0167 | no |

#### Exploratory -- added after the results existed

fp16 reference model against each quantised artefact, `test_golden`: the
difference Table 18 reports as a delta. The reference side is the fine-tuned fp16
model under `transformers` without a grammar (`train/kaggle_out/preds_*.jsonl`);
precision, runtime and grammar all change across the pair. Bonferroni over the six
pairs: alpha = 0.0083.

| A | B | n | EM A | EM B | a (both) | b (A only) | c (B only) | d (neither) | b+c | test | p | alpha | significant |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | ---: | ---: | :--- |
| llama-3.2-1b-instruct fp16 | llama-3.2-1b-instruct Q4_K_M | 200 | 0.9250 | 0.9100 | 182 | 3 | 0 | 15 | 3 | exact | 0.25 | 0.0083 | no |
| llama-3.2-1b-instruct fp16 | llama-3.2-1b-instruct Q8_0 | 200 | 0.9250 | 0.9150 | 183 | 2 | 0 | 15 | 2 | exact | 0.5 | 0.0083 | no |
| qwen2.5-0.5b-instruct fp16 | qwen2.5-0.5b-instruct Q4_K_M | 200 | 0.9350 | 0.9350 | 187 | 0 | 0 | 13 | 0 | exact | 1 | 0.0083 | no |
| qwen2.5-0.5b-instruct fp16 | qwen2.5-0.5b-instruct Q8_0 | 200 | 0.9350 | 0.9300 | 186 | 1 | 0 | 13 | 1 | exact | 1 | 0.0083 | no |
| smollm2-360m-instruct fp16 | smollm2-360m-instruct Q4_K_M | 200 | 0.7750 | 0.7600 | 143 | 12 | 9 | 36 | 21 | exact | 0.663624 | 0.0083 | no |
| smollm2-360m-instruct fp16 | smollm2-360m-instruct Q8_0 | 200 | 0.7750 | 0.7900 | 155 | 0 | 3 | 42 | 3 | exact | 0.25 | 0.0083 | no |

Parameter-matched family control, fp16 reference, `test_golden` (single test, alpha 0.05):

| A | B | n | EM A | EM B | a (both) | b (A only) | c (B only) | d (neither) | b+c | test | p | alpha | significant |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | ---: | ---: | :--- |
| qwen2.5-0.5b-instruct fp16 | h2o-danube3-500m-chat fp16 | 200 | 0.9350 | 0.8700 | 172 | 15 | 2 | 11 | 17 | exact | 0.00234985 | 0.0500 | yes |

#### Reading these numbers

**A non-significant McNemar is not a finding of equivalence.** Where `b+c` is 1,
the smallest attainable exact p-value is 1.0: the test cannot reject regardless
of the truth. What such a row reports is that the two artefacts disagreed on one
item out of 200 -- a statement about how little they differ, which is a bound
worth quoting, and not the same claim as 'no difference exists'.

**An identical exact match is not an identical model.** smollm2-360m scores
0.8125 at both quantisations on `test_synth`, and the pairing shows why that is
a coincidence rather than a result: the two artefacts disagree on 24 items and
happen to split them 12/12. Comparing the summary figures alone would have
reported a difference of exactly zero where there are two dozen of them.

Provenance: exact match re-derived from the per-item predictions matches
every `grammar=on` row of `results/surface_b.csv` and every fine-tuned row of
`train/kaggle_out/surface_a.csv` it uses, to four decimal places.
