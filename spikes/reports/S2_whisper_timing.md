# Spike S2 Report: whisper.cpp Timing on Raspberry Pi 5

- **Date:** 2026-09-08
- **Target Platform:** Raspberry Pi 5 Model B Rev 1.0 (4× Cortex-A76 @ 2.4 GHz, 8GB RAM)
- **Status:** **PROVISIONAL / THERMALLY GATED** (The spec'd `-t 3` configuration under passive cooling is **OVER BUDGET: 2,014 ms p95 vs 1,200 ms target**; Active Cooler is a mandatory prerequisite to close NFR-2)

## Configuration
- **`whisper.cpp` commit SHA:** `c44b60b8053bbf2a5c1e014f11323fb3f2485177`
- **Model:** `tiny.en` Q5_1 quantization (`ggml-tiny.en-q5_1.bin`, 31.57 MB)
- **Test Stimulus:** Synthetic 3.0 s 440 Hz tone @ 16 kHz mono (48,000 samples) — encode cost is input-independent because Whisper pads all inputs to a fixed 30 s mel window.
- **Thread Allocation:** 3 threads (`-t 3`) per PRD Table 7 (Cores 1–3 assigned to Branch B; Core 0 pinned to Branch A)
- **Sample Count:** $N = 20$ timed repetitions

## Timing Measurements

### 1. Spec-Compliant 3-Thread Benchmark (`-t 3`, Under 1.50 GHz Thermal Throttle)
*Conducted immediately following the S1 benchmark without active cooling (Governor throttled to 1.50 GHz, code `0xe0008`):*

| Metric | Measured Value (ms) | Table 6 Stage Budget | Delta vs Budget |
| :--- | :--- | :--- | :--- |
| **p50 (Median)** | **1959.57 ms** | $\le 1200.00\text{ ms}$ | **+63.3%** |
| **p95** | **2013.66 ms** | $\le 1200.00\text{ ms}$ | **+67.8% (OVER BUDGET)** |
| **Min** | **1461.15 ms** | — | Fastest sample (unthrottled run 1) |
| **Max** | **2027.17 ms** | — | Saturated thermal ceiling |
| **Mean $\pm$ Std** | **1905.62 $\pm$ 146.90 ms** | — | — |

### 2. Off-Spec 4-Thread Benchmark (`-t 4`, Informational Only)
- **Total Latency:** **1137.39 ms** ($n=1$, single invocation)
- **Encode Time:** 962.32 ms
- **Mel Spectrum Time:** 4.61 ms
- **Sample Generation:** 26.35 ms
- **Model Load Time:** 72.89 ms
- **Architectural Status:** **UNUSABLE FOR PRODUCTION**. Table 7 explicitly reserves Core 0 for Branch A (Silero VAD / OpenWakeWord / 50 Hz PyFlyt safety loop). Running STT on 4 threads would starve Core 0 and violate NFR-1 (150 ms reflex abort). Therefore, 4-thread runs cannot discharge the budget.

---

## The System-Level Finding: NFR-2 Latency Stack-up

Summing the measured stage timings against PRD Table 6 under the mandated 3-thread allocation (`-t 3`) demonstrates that **NFR-2 does not close on passively cooled hardware**:

$T_0$ = **acoustic end-of-speech** (the instant the speaker stops). Capture buffering and VAD silence detection both fall *inside* the E2E window.

| Stage | Table 6 p95 Budget | Measured / Verified on Throttled Pi 5 (1.5 GHz, `-t 3`) | Basis | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Capture buffering** | — | **$\approx$ 43 ms** | 1024-frame ALSA period @ 48 kHz + double buffer (S0 estimate, pending loopback) | Included |
| **VAD endpointing** | 500 ms | 500 ms | Nominal silence wait | Upper bound |
| **STT (`tiny.en` Q5, `-t 3`)** | 1,200 ms | **2,014 ms** | Measured ($N=20$, p95) | **+67.8% (OVER BUDGET)** |
| **SLM prefill** (~15 tokens) | 250 ms | **335 ms** | Measured (`llama-bench -t 3`: 44.74 tok/s) | **+34.0% (OVER BUDGET)** |
| **SLM decode** (~22 tokens) | 1,100 ms | **1,049 ms** | Measured (`llama-bench -t 3`: 20.97 tok/s) | −4.6% (Pass) |
| **Validate + FSM + dispatch** | 50 ms | < 1 ms | Estimated Layer 2/3 execution | Pass |
| **E2E from End-of-Speech (NFR-2)** | **$\leq$ 2,500 ms** | **$\approx$ 3,942 ms** | Sum of `-t 3` stages (incl. capture) | **FAIL (+57.7%)** |

*Note on PRD Table 6 Internal Over-Sum:*
The PRD's individual stage targets ($500 + 1200 + 250 + 1100 + 50 = \mathbf{3,100\text{ ms}}$) over-sum the headline target ($\le \mathbf{2,500\text{ ms}}$) by 600 ms. This confirms that the stage ceilings were loose upper bounds; for NFR-2 to close in production, individual stages must execute with zero slack.

---

## Observations & Thermal Dependency

1. **Clock Throttling Mechanism:**
   - Under passive heatsink cooling, sustained CPU load drove temperatures to $85.1^\circ\text{C}$, triggering throttling flag `0xe0008`. The Linux CPU governor dropped clock speeds from nominal **2.40 GHz down to 1.50 GHz** (`frequency(0)=1500022656`).
   - Normalizing from median p50 (1,959 ms) at 1.5 GHz to nominal 2.4 GHz:
     $$1959.57\text{ ms} \times \frac{1.5\text{ GHz}}{2.4\text{ GHz}} = 1,224.7\text{ ms}$$
2. **Honest 2.4 GHz Projection Range (2,634 – 3,027 ms $\rightarrow$ FAILS NFR-2):**
   - **Best-Case Compute Scaling:** If both Whisper encoder and SLM decode scale purely with CPU clock ($1.5 \to 2.4\text{ GHz}$):
     - Capture buffering: $\approx 43\text{ ms}$
     - STT: $\approx 1,225\text{ ms}$
     - Prefill: $335 \times (1.5/2.4) \approx 209\text{ ms}$
     - Decode: $1,049 \times (1.5/2.4) \approx 656\text{ ms}$
     - VAD: $500\text{ ms}$
     - Total: **$\approx 2,634\text{ ms}$** (105.4% of budget $\rightarrow$ **FAIL**).
   - **Memory-Bandwidth Bound Reality:** LLM autoregressive token generation and Whisper's encoder attention are predominantly memory-bandwidth bound. The Pi 5 LPDDR4X memory clock does *not* scale with the CPU governor. If decode memory throughput remains flat, decode stays near $\approx 1,049\text{ ms}$, landing total E2E at **$\approx 3,027\text{ ms}$** (121% of budget $\rightarrow$ **FAIL**).
   - **Critical Takeaway:** **Every point in the honest 2,634 – 3,027 ms range fails NFR-2.** Mounting the Active Cooler is necessary but not sufficient on its own. Closing NFR-2 requires architectural overlap (e.g. streaming STT before speech offset) or an explicit budget renegotiation in Exp-2.
3. **Memory Footprint:**
   - Model size: **31.57 MB**
   - Compute buffers: $\approx 95.9\text{ MB}$ decode, $\approx 17.7\text{ MB}$ encode
   - **Total Peak RSS: $\approx 125\text{ MB}$**, safely within the $\le 300\text{ MB}$ budget.
4. **Final S2 Verdict:**
   - **GATED ON ACTIVE COOLER & ARCHITECTURAL OPTIMIZATION**: Under 1.5 GHz thermal throttling, STT p95 is 2,014 ms (+68% over budget). Once the Active Cooler is mounted, S2 must be re-run at `-t 3` ($N=20$) with clock locked at 2.40 GHz (`cpufreq` governor `performance`) to establish empirical unthrottled numbers.
