### Table 33: Exact match of the four fine-tuned models on the reference surface

Exact match of each fine-tuned fp16 model on the reference surface (base model plus
adapter under `transformers` on a Kaggle T4, greedy, no grammar), by split: 240
(`test_synth`), 200 (`test_golden`) and 150 (`test_ood`) items. Source:
`train/kaggle_out/surface_a.csv`; parameter counts and families from
`train/configs/*.yaml`. Ordered by parameter count.

| Model | Params | Family | test_synth | test_golden | test_ood |
| :--- | ---: | :--- | ---: | ---: | ---: |
| smollm2-360m-instruct | 362 M | HuggingFace (SmolLM2) | 0.825 | 0.775 | 0.620 |
| qwen2.5-0.5b-instruct | 494 M | Alibaba (Qwen2.5) | 0.954 | 0.935 | 0.727 |
| h2o-danube3-500m-chat | 514 M | H2O.ai (Danube3) | 0.887 | 0.870 | 0.720 |
| llama-3.2-1b-instruct | 1,236 M | Meta (Llama-3.2) | 0.958 | 0.925 | 0.733 |

**Family, at matched size** (qwen2.5-0.5b-instruct, 494 M, against h2o-danube3-500m-chat, 514 M, 4.0% apart): 6.5 pp on `test_golden` (0.935 against 0.870; 15 against 2 discordant items, exact McNemar p = 0.0023). **Full span** (smollm2-360m-instruct, 362 M, to llama-3.2-1b-instruct, 1,236 M, 3.4×): +15.0 pp on `test_golden` (0.775 → 0.925); the endpoints are also two different families, so this is not a size effect.

The recipe is frozen at three epochs for every model. Validation exact match was unchanged between epochs two and three only for llama-3.2-1b-instruct; it was still rising at epoch 3 for qwen2.5-0.5b-instruct (+0.008), smollm2-360m-instruct (+0.025), h2o-danube3-500m-chat (+0.038), so no model is shown to have converged, and the comparison is one **under an identical three-epoch budget**, not one of capability.
