### Latency budget versus measured (Exp-2)

Raspberry Pi 5, cooled, governor `performance`, Table 7 pinning (frame loop core 0;
STT and SLM cores 1-3). Real-time WAV replay: Branch B on the 200 golden utterances
(clean), one sample per endpointed segment; Branch A on the author's 40 real takes,
twice, idle and during a Branch B decode. Nearest-rank percentiles; the verdict is on
the p95. The bus is loopback on the Pi (the Wi-Fi hop is outside the budget, prd 4.7).

| Stage | n | p50 | p95 | p99 | Target p95 | Verdict |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| VAD endpointing wait | 226 | 480 | 480 | 480 | 500 | MEETS |
| STT (whisper tiny.en, -t 3) | 226 | 1,246 | 1,449 | 1,571 | 1,200 | MISSES |
| SLM prefill | 226 | 570 | 751 | 849 | 250 | MISSES |
| SLM decode | 226 | 561 | 915 | 984 | 1,100 | MEETS |
| Validate, FSM check, dispatch | 226 | 0 | 0 | 4 | 50 | MEETS |
| **E2E from end of speech (T0; NFR-2)** | 226 | 2,441 | 3,122 | 3,380 | 2,500 | MISSES |
| E2E incl. the VAD wait | 226 | 2,921 | 3,602 | 3,860 | 2,500 | MISSES |
| E2E from start of speech | 226 | 6,344 | 10,086 | 12,322 | -- | -- |
| **Branch A from keyword offset, idle (NFR-1)** | 78 | 195 | 545 | 555 | 150 | MISSES |
| of which spotter delay + frame quantisation | 78 | 190 | 540 | 550 | -- | -- |
| of which Pi compute + publish | 78 | 5 | 6 | 6 | -- | -- |
| **Branch A from keyword offset, loaded (NFR-1)** | 78 | 205 | 547 | 564 | 150 | MISSES |
| of which spotter delay + frame quantisation | 78 | 190 | 540 | 550 | -- | -- |
| of which Pi compute + publish | 78 | 12 | 18 | 19 | -- | -- |
| Branch A from keyword onset, idle | 78 | 965 | 1,265 | 1,265 | 850 | MISSES |
| Branch A from keyword onset, loaded | 78 | 967 | 1,266 | 1,278 | 850 | MISSES |
| Pre-emption recovery (NFR-17) | 78 | 601 | 1,195 | 1,505 | 300 | MISSES |

Prefill is the deployed parser's, with the prompt cache off (Surface B parity); Table 6's
line assumes a cached prefix. Start-of-speech has no verdict: its 5,500 ms target is for a
3 s utterance. Split rate, cross-trigger matrix, pre-emption outcomes and the core-0 frame
budget: `results/exp2_analysis.md`.
