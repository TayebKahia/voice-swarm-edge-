### Table 19: Grammar ablation

The six deployed artefacts decode the same 590 items (240 `test_synth`, 200
`test_golden`, 150 `test_ood`) greedily, with and without `schema/cmd.gbnf` given to
`llama.cpp`; nothing else changes. Scored on the workstation. Sources:
`results/surface_b.csv` (grammar on) and `results/surface_b_nogrammar.csv` (grammar off).

| Condition | Decodes | Schema validity | Malformed | [EM](#acr:em) (pooled) |
| :--- | ---: | ---: | ---: | ---: |
| Grammar on | 3540 | 1.0000 | 0 | 0.8508 |
| Grammar off | 3540 | 0.9997 | 1 | 0.8492 |

Pooled over every model, quantisation and split. Exact match is pooled by item, not
averaged over the eighteen rows, so the larger splits carry their real weight.
