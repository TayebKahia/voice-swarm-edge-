### Table 17: Model comparison (Exp-1, RQ1)

Surface B --- the quantised artefact under `llama.cpp` with the GBNF grammar, which is
what the aircraft actually runs. Accuracy columns are from `results/surface_b.csv`;
latency, throughput and memory columns are `results/exp1_cooled.csv`, measured on
the Pi with an active cooler fitted: 0 of 180 scored trials throttled, 67.5--74.1 C.
The earlier uncooled run throttled on 180/180 and is reported separately, in the
thermal-headroom table. p50/p95 is the SLM prefill and decode stages combined. Exp-1
on the hardware covers only Q4_K_M -- a Q8_0 row keeps `--` because it was never measured
on the hardware, not because the join failed. Slot-F1 is `--` on `test_ood` because that
split carries no gold slots: its gold target is `{"intent":"unknown"}` on all 150 items,
so the metric has no dynamic range there. What the models do emit on those items is
reported properly by the false-command rate (NFR-18).

| Model | Quant | Split | Intent-F1 | Slot-F1 | EM | Safe-fail | Schema-valid | p50/p95 (ms) | tok/s | Peak RSS |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: | :--- |
| llama-3.2-1b-instruct | Q4_K_M | `test_synth` | 99.1 | 97.5 | 95.8 | 0.0 | 100.0 | 1351.09/2282.45 | 14.53 | 1.63 GB |
| llama-3.2-1b-instruct | Q4_K_M | `test_golden` | 99.6 | 94.5 | 91.0 | 0.0 | 100.0 | 1351.09/2282.45 | 14.53 | 1.63 GB |
| llama-3.2-1b-instruct | Q4_K_M | `test_ood` | 89.7 | -- | 81.3 | 10.7 | 100.0 | 1351.09/2282.45 | 14.53 | 1.63 GB |
| llama-3.2-1b-instruct | Q8_0 | `test_synth` | 99.1 | 97.8 | 96.2 | 0.0 | 100.0 | -- | -- | -- |
| llama-3.2-1b-instruct | Q8_0 | `test_golden` | 99.6 | 94.8 | 91.5 | 0.0 | 100.0 | -- | -- | -- |
| llama-3.2-1b-instruct | Q8_0 | `test_ood` | 88.9 | -- | 80.0 | 10.0 | 100.0 | -- | -- | -- |
| qwen2.5-0.5b-instruct | Q4_K_M | `test_synth` | 98.5 | 97.8 | 95.4 | 0.0 | 100.0 | 646.71/1072.41 | 27.93 | 0.68 GB |
| qwen2.5-0.5b-instruct | Q4_K_M | `test_golden` | 100.0 | 96.1 | 93.5 | 0.0 | 100.0 | 646.71/1072.41 | 27.93 | 0.68 GB |
| qwen2.5-0.5b-instruct | Q4_K_M | `test_ood` | 85.5 | -- | 74.7 | 15.8 | 100.0 | 646.71/1072.41 | 27.93 | 0.68 GB |
| qwen2.5-0.5b-instruct | Q8_0 | `test_synth` | 99.0 | 97.8 | 95.8 | 0.0 | 100.0 | -- | -- | -- |
| qwen2.5-0.5b-instruct | Q8_0 | `test_golden` | 100.0 | 95.8 | 93.0 | 0.0 | 100.0 | -- | -- | -- |
| qwen2.5-0.5b-instruct | Q8_0 | `test_ood` | 84.6 | -- | 73.3 | 15.0 | 100.0 | -- | -- | -- |
| smollm2-360m-instruct | Q4_K_M | `test_synth` | 96.8 | 88.1 | 81.2 | 2.2 | 100.0 | 475.41/894.25 | 40.63 | 0.55 GB |
| smollm2-360m-instruct | Q4_K_M | `test_golden` | 95.4 | 84.8 | 76.0 | 4.2 | 100.0 | 475.41/894.25 | 40.63 | 0.55 GB |
| smollm2-360m-instruct | Q4_K_M | `test_ood` | 79.5 | -- | 66.0 | 5.9 | 100.0 | 475.41/894.25 | 40.63 | 0.55 GB |
| smollm2-360m-instruct | Q8_0 | `test_synth` | 98.0 | 88.6 | 81.2 | 0.0 | 100.0 | -- | -- | -- |
| smollm2-360m-instruct | Q8_0 | `test_golden` | 97.2 | 86.6 | 79.0 | 0.0 | 100.0 | -- | -- | -- |
| smollm2-360m-instruct | Q8_0 | `test_ood` | 75.5 | -- | 60.7 | 6.8 | 100.0 | -- | -- | -- |
