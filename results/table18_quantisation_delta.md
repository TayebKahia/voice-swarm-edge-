### Table 18: Quantisation delta --- exact match on `test_golden`

Exact match on `test_golden` (200 items) of each fine-tuned fp16 model on the reference
surface (base model plus adapter under `transformers` on a Kaggle T4, no grammar)
against its quantised artefacts on the deployed surface (`llama.cpp` under the [GBNF](#acr:gbnf)
grammar, scored on the workstation). Numeric format, runtime, grammar and decoding
settings change together, and for Llama-3.2-1B the checkpoint as well, so the delta
measures the *deployment pipeline*, not weight precision alone. b and c are the items
only the reference and only the deployed artefact get right; p is the exact McNemar
test, an exploratory family of 6 corrected to α = 0.0083; no pair reaches it. Sources:
`train/kaggle_out/surface_a.csv`, `results/surface_b.csv`, `results/mcnemar.csv`.

| Model | Quant | Reference [EM](#acr:em) | Deployed [EM](#acr:em) | Delta (pp) | b / c | p |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| llama-3.2-1b-instruct | Q4_K_M | 0.925 | 0.910 | −1.5 | 3 / 0 | 0.25 |
| llama-3.2-1b-instruct | Q8_0 | 0.925 | 0.915 | −1.0 | 2 / 0 | 0.50 |
| qwen2.5-0.5b-instruct | Q4_K_M | 0.935 | 0.935 | 0.0 | 0 / 0 | 1.00 |
| qwen2.5-0.5b-instruct | Q8_0 | 0.935 | 0.930 | −0.5 | 1 / 0 | 1.00 |
| smollm2-360m-instruct | Q4_K_M | 0.775 | 0.760 | −1.5 | 12 / 9 | 0.66 |
| smollm2-360m-instruct | Q8_0 | 0.775 | 0.790 | +1.5 | 0 / 3 | 0.25 |
