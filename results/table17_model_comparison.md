### Table 17: Model comparison on the deployed surface

The deployed surface: each quantised artefact decoded by `llama.cpp` under the [GBNF](#acr:gbnf)
grammar. Accuracy columns are fractions, scored on the workstation from
`results/surface_b.csv` over 240 (`test_synth`), 200 (`test_golden`) and 150 (`test_ood`)
items; Safe-fail is the share of errors that resolve to `unknown` or `hover`.
Latency, throughput and memory are from `results/exp1_cooled.csv`, measured on the Raspberry
Pi 5 with an active cooler fitted (0 of 180 scored trials throttled, 67.5–74.1 °C;
the uncooled run is in [Table](#tab:thermal-headroom)). p50/p95 is the language-model prefill
and decode stages combined, 60 trials per configuration; Mem. is the peak resident
set of the language-model process, in GiB. Only Q4_K_M was timed on the board, so a Q8_0 row carries `--`
there. Slot-F1 is `--` on `test_ood`, whose 150 references carry no slots; what the models
emit there is reported by the false-command rate, [Table](#tab:false-command).

| Model | Quant | Split | Intent-F1 | Slot-F1 | [EM](#acr:em) | Safe-fail | Schema-valid | p50/p95 (ms) | tok/s | Mem. (GiB) |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: | :--- |
| llama-3.2-1b-instruct | Q4_K_M | `test_synth` | 0.991 | 0.975 | 0.958 | 0.000 | 1.000 | 1,351/2,282 | 14.53 | 1.63 |
| llama-3.2-1b-instruct | Q4_K_M | `test_golden` | 0.996 | 0.945 | 0.910 | 0.000 | 1.000 | 1,351/2,282 | 14.53 | 1.63 |
| llama-3.2-1b-instruct | Q4_K_M | `test_ood` | 0.897 | -- | 0.813 | 0.107 | 1.000 | 1,351/2,282 | 14.53 | 1.63 |
| llama-3.2-1b-instruct | Q8_0 | `test_synth` | 0.991 | 0.978 | 0.963 | 0.000 | 1.000 | -- | -- | -- |
| llama-3.2-1b-instruct | Q8_0 | `test_golden` | 0.996 | 0.948 | 0.915 | 0.000 | 1.000 | -- | -- | -- |
| llama-3.2-1b-instruct | Q8_0 | `test_ood` | 0.889 | -- | 0.800 | 0.100 | 1.000 | -- | -- | -- |
| qwen2.5-0.5b-instruct | Q4_K_M | `test_synth` | 0.985 | 0.978 | 0.954 | 0.000 | 1.000 | 647/1,072 | 27.93 | 0.68 |
| qwen2.5-0.5b-instruct | Q4_K_M | `test_golden` | 1.000 | 0.961 | 0.935 | 0.000 | 1.000 | 647/1,072 | 27.93 | 0.68 |
| qwen2.5-0.5b-instruct | Q4_K_M | `test_ood` | 0.855 | -- | 0.747 | 0.158 | 1.000 | 647/1,072 | 27.93 | 0.68 |
| qwen2.5-0.5b-instruct | Q8_0 | `test_synth` | 0.990 | 0.978 | 0.958 | 0.000 | 1.000 | -- | -- | -- |
| qwen2.5-0.5b-instruct | Q8_0 | `test_golden` | 1.000 | 0.958 | 0.930 | 0.000 | 1.000 | -- | -- | -- |
| qwen2.5-0.5b-instruct | Q8_0 | `test_ood` | 0.846 | -- | 0.733 | 0.150 | 1.000 | -- | -- | -- |
| smollm2-360m-instruct | Q4_K_M | `test_synth` | 0.968 | 0.881 | 0.812 | 0.022 | 1.000 | 475/894 | 40.63 | 0.55 |
| smollm2-360m-instruct | Q4_K_M | `test_golden` | 0.954 | 0.848 | 0.760 | 0.042 | 1.000 | 475/894 | 40.63 | 0.55 |
| smollm2-360m-instruct | Q4_K_M | `test_ood` | 0.795 | -- | 0.660 | 0.059 | 1.000 | 475/894 | 40.63 | 0.55 |
| smollm2-360m-instruct | Q8_0 | `test_synth` | 0.980 | 0.886 | 0.812 | 0.000 | 1.000 | -- | -- | -- |
| smollm2-360m-instruct | Q8_0 | `test_golden` | 0.972 | 0.866 | 0.790 | 0.000 | 1.000 | -- | -- | -- |
| smollm2-360m-instruct | Q8_0 | `test_ood` | 0.755 | -- | 0.607 | 0.068 | 1.000 | -- | -- | -- |
