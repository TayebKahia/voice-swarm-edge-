# Spike S7 Report: Preemption Capability & Architecture

- **Date:** 2026-09-08
- **Owner:** PFE Edge Architecture Team
- **Status:** **DEFERRED / ARCHITECTURE ONLY** (Dual-path architectural design established; real hardware measurement with in-flight GGML graph abort and 463 MB model reload scheduled for Exp-2)

## Architectural Requirement (PRD §4.3 & NFR-17)

When Branch A triggers a reflex abort (`swarm hold` or `swarm abort`) while Branch B is mid-inference, two requirements apply:
1. **Correctness (Mandatory):** Every bus message carries a monotonically increasing sequence number and a `branch` tag. The state machine discards any Branch B message whose sequence number is lower than the highest Branch A message already applied. A stale Branch B result *cannot* take effect, regardless of whether its decode was stopped.
2. **Resource Recovery (Desirable, NFR-17):** Preemption recovery time from a Branch A trigger until Branch B can accept a new utterance must meet **$p95 \le 300\text{ ms}$**. The three inference cores must be released immediately so the system is unblocked.

---

## The Dual-Path Architecture Design

### Primary Path: In-Process Atomic Abort Callback
- The `llama.cpp` decoding loop accepts an `abort_callback` (`llama_progress_callback` or `ggml_abort_callback`).
- When Branch A triggers, the shared atomic boolean `abort_requested` is set to `true`.
- The decoder checks the flag between graph node evaluations or token iterations.
- **Latency Upper Bound:** Bounded by the single-token compute duration under 3 threads ($\approx 47.7\text{ ms}$ at 1.5 GHz; $\approx 30\text{ ms}$ at 2.4 GHz). Once aborted, the engine resets the KV context and is immediately ready for the next command ($\approx 5\text{--}10\text{ ms}$ reset overhead), easily satisfying the $\le 300\text{ ms}$ budget.

### Fallback Path: Out-of-Process Worker with Process Signaling
- If the in-process engine hangs, deadlocks, or fails to poll the abort callback promptly, Branch B runs in a dedicated worker process.
- The supervisor dispatches `SIGKILL` to the worker process (terminating in $< 1\text{ ms}$).
- A replacement worker is spawned immediately.
- **Critical Risk (Model Load Time):** A real worker respawn must load **462.96 MiB** of Qwen2.5 weights and initialize memory pools. For comparison, Spike S2 measured 72.89 ms to load a 31.57 MB Whisper model. Loading a 463 MB model from Pi 5 NVMe / SD card without pre-warmed OS page caches could take $\approx 250\text{--}400\text{ ms}$, putting NFR-17's $300\text{ ms}$ ceiling at risk.
- **Mitigation:** Memory-mapped I/O (`mmap=True`, standard in `llama.cpp`) keeps weight pages resident in the Linux page cache across process respawns, reducing reload time to $\approx 30\text{--}50\text{ ms}$.

---

## Hardware Spike Protocol (Exp-2 on Raspberry Pi 5)

Previous workstation simulations using Python `time.sleep` and empty subprocess exits did not execute real GGML graph evaluations or measure weight memory loading. The definitive hardware experiment will execute on Pi 5 during Exp-2:
1. **In-Process Benchmark:** Start a 48-token decode with `Qwen2.5-0.5B-Instruct-Q4_K_M.gguf` under `-t 3`. Fire `abort_callback` at $T=200\text{ ms}$ across $N=20$ trials. Measure $p50$ and $p95$ interruption latency and time-to-first-token on subsequent prompt.
2. **Process Respawn Benchmark:** Measure wall-clock latency from `SIGKILL` delivery to worker process through `mmap` reload and completion of the first generated token under `-t 3` ($N=20$, report $p95$ against $300\text{ ms}$).

---

## Architectural Decision
- Adopt the in-process atomic abort callback as the **primary real-time preemption mechanism**.
- Retain the out-of-process worker model with sequence-number bus arbitration as the **safety fallback**, leveraging `mmap` page cache residency to bound respawn latency within NFR-17.
