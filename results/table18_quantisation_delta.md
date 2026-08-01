### Table 18: Quantisation delta --- exact match on `test_golden`

Surface A is FP16 under `transformers` with no grammar. Surface B is the same
adapter merged, converted and quantised, decoded by `llama.cpp` under the GBNF
constraint. The delta therefore measures the *deployment pipeline*, not weight
precision alone --- the grammar is part of what changes, and on out-of-domain input
it is the dominant term.

| Model | Quant | FP16 EM (surface A) | Quantised EM (surface B) | Delta (pp) |
| :--- | :--- | ---: | ---: | ---: |
| llama-3.2-1b-instruct | Q4_K_M | 92.5 | 91.0 | -1.5 |
| llama-3.2-1b-instruct | Q8_0 | 92.5 | 91.5 | -1.0 |
| qwen2.5-0.5b-instruct | Q4_K_M | 93.5 | 93.5 | +0.0 |
| qwen2.5-0.5b-instruct | Q8_0 | 93.5 | 93.0 | -0.5 |
| smollm2-360m-instruct | Q4_K_M | 77.5 | 76.0 | -1.5 |
| smollm2-360m-instruct | Q8_0 | 77.5 | 79.0 | +1.5 |
