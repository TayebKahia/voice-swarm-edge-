### Table 20: End-to-end on the golden set (Exp-3)

Golden-set audio through Silero endpointing (450 ms), whisper `tiny.en` and
`qwen2.5-0.5b-instruct-Q4_K_M` under the grammar; rotor noise (DREGON, evaluation
partition) mixed digitally on active-speech level. EM is the same items as reference
text through the same parser, so EM - CRR is the cost of the speech stage. Intervals
are 95% bootstrap over utterances; safe-failure is over failed items only.

| SNR | n | CRR | 95% CI | WER % | 95% CI | EM | EM - CRR | 95% CI | Safe-failure | E2E p50 / p95 (ms) |
| :--- | ---: | ---: | :--- | ---: | :--- | ---: | ---: | :--- | :--- | :--- |
| clean | 200 | 0.690 | [0.625, 0.750] | 23.4 | [20.3, 26.7] | 0.935 | +0.245 | [0.185, 0.310] | 0.032 (2/62) | pending (A7b, Pi) |
| 20 dB | 200 | 0.675 | [0.610, 0.740] | 24.3 | [21.5, 27.1] | 0.935 | +0.260 | [0.200, 0.325] | 0.015 (1/65) | pending (A7b, Pi) |
| 15 dB | 200 | 0.650 | [0.585, 0.715] | 26.1 | [23.4, 29.1] | 0.935 | +0.285 | [0.225, 0.350] | 0.014 (1/70) | pending (A7b, Pi) |
| 10 dB | 200 | 0.590 | [0.520, 0.660] | 28.8 | [26.0, 31.8] | 0.935 | +0.345 | [0.280, 0.410] | 0.049 (4/82) | pending (A7b, Pi) |
| 5 dB | 200 | 0.495 | [0.425, 0.565] | 36.2 | [33.0, 39.5] | 0.935 | +0.440 | [0.370, 0.510] | 0.040 (4/101) | pending (A7b, Pi) |

NFR-7 CRR (clean, >= 0.80): 0.690 -- **MISSES**.
NFR-8 CRR (10 dB, >= 0.65): 0.590 -- **MISSES**.
NFR-9 safe-failure (lowest across SNR, >= 0.70): 0.014 -- **MISSES**.
Tests across SNR, the operational envelope and the segmentation breakdown:
`results/exp3_analysis.md`.
