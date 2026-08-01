### Table 19: Grammar ablation

Same six artefacts, same 590 items, same greedy decode; the only change is whether
`llama.cpp` is given `schema/cmd.gbnf`. Decode p95 is Exp-1 on the Pi and is filled
by that run --- the workstation's decode time is not the deployed latency.

| Condition | Items | Schema validity | Malformed | EM (pooled) | Decode p95 |
| :--- | ---: | ---: | ---: | ---: | :--- |
| Grammar on | 3540 | 1.0000 | 0 | 0.8508 | -- |
| Grammar off | 3540 | 0.9997 | 1 | 0.8492 | -- |

Pooled over every model, quantisation and split. Exact match is pooled by item, not
averaged over the eighteen rows, so the larger splits carry their real weight.
