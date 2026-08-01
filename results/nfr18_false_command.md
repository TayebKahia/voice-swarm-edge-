### NFR-18: false-command rate on out-of-domain input

Budget: <= 0.05. Measured on `test_ood`, Surface B.

| Model | Quant | False-command rate | Verdict |
| :--- | :--- | ---: | :--- |
| llama-3.2-1b-instruct | Q4_K_M | 0.1867 | **MISS** |
| llama-3.2-1b-instruct | Q8_0 | 0.2000 | **MISS** |
| qwen2.5-0.5b-instruct | Q4_K_M | 0.2533 | **MISS** |
| qwen2.5-0.5b-instruct | Q8_0 | 0.2667 | **MISS** |
| smollm2-360m-instruct | Q4_K_M | 0.3400 | **MISS** |
| smollm2-360m-instruct | Q8_0 | 0.3933 | **MISS** |
