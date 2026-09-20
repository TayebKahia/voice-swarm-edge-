### Thermal headroom: cooled and uncooled benchmark runs

The multi-model benchmark's run of record with the active cooler fitted
(`results/exp1_cooled.csv`) against an earlier run without it (`results/exp1.csv`), on
the same board with the same three Q4_K_M artefacts and protocol.

| Config | Run | Throttled trials | Max temp. (°C) | Decode p95 (ms) | [SLM](#acr:slm) total p95 (ms) | tok/s |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| llama-3.2-1b-instruct Q4_K_M | cooled | 0% | 70.8 | 1842.5 | 2282.4 | 14.53 |
| llama-3.2-1b-instruct Q4_K_M | uncooled | 100% | 90.6 | 2458.8 | 3238.6 | 10.75 |
| qwen2.5-0.5b-instruct Q4_K_M | cooled | 0% | 74.1 | 1033.2 | 1072.4 | 27.93 |
| qwen2.5-0.5b-instruct Q4_K_M | uncooled | 100% | 90.6 | 1518.9 | 1771.5 | 18.13 |
| smollm2-360m-instruct Q4_K_M | cooled | 0% | 74.1 | 785.5 | 894.2 | 40.63 |
| smollm2-360m-instruct Q4_K_M | uncooled | 100% | 91.1 | 1338.9 | 1610.2 | 24.11 |

Protocol: 60 scored trials per configuration after a ten-minute warm-up, cores 1–3 pinned, `performance` governor, swap disabled. Accuracy is not repeated: it is scored on the workstation and does not depend on the board's clock. **Throttling** (share of trials with a non-zero throttle flag, budget 5%): cooled, worst configuration 0% (meets); uncooled, worst configuration 100% (misses). **Cooled relative to uncooled**: llama-3.2-1b-instruct Q4_K_M, decode p95 −25.1% and throughput +35.2%; qwen2.5-0.5b-instruct Q4_K_M, decode p95 −32.0% and throughput +54.1%; smollm2-360m-instruct Q4_K_M, decode p95 −41.3% and throughput +68.5%. The uncooled run was capped at 1.5 GHz against the 2.4 GHz the `performance` governor sets, a clock ratio of at least 1.6×; the clock actually held was not logged. The largest throughput gain, 1.69× on smollm2-360m-instruct, is accounted for by the clock alone only if the throttled clock fell below 1.42 GHz.

