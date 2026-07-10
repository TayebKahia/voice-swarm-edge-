# Spike S4 Report: PyFlyt Swarm Simulation Feasibility

- **Date:** 2026-09-07
- **Owner:** Agent (executed end-to-end on workstation)
- **Status:** PASS

## Test Parameters
- Platform: Workstation CPU (Intel / AMD x86_64, Linux)
- Swarm size: 5 `quadx` drones in circular formation
- Physics frequency: 250 Hz (substeps per control step = 5)
- Control loop frequency: 50 Hz ($\Delta t = 0.02$ s)
- Duration: 10.0 simulated seconds (500 control steps)

## Benchmark Measurements
- **Simulated Duration:** 10.00 s (500 control steps)
- **Wall-Clock Execution Time:** 2.117 s
- **Real-Time Factor (RTF):** **4.72x** (Pass condition: $\text{RTF} \ge 1.0$)
- **Mean Per-Step Wall Time:** 4.23 ms (budget per 50 Hz tick: 20.0 ms)
- **Headroom Claim:** $\approx 78\%$ headroom against the 20 ms tick budget on workstation.

## Caveats & Engineering Scope

1. **Unactuated Physics Baseline:**
   The benchmark stepped raw PyBullet physics (`env.step()`) without closed-loop PID attitude controllers, formation trajectory planners, or inter-drone collision clamps active. Real control setpoint compute will consume additional CPU cycles per tick.
2. **Mean vs. Hard-Deadline Max Ticks:**
   A 50 Hz flight control loop is a hard real-time constraint. While the mean tick is 4.23 ms, physics engines experience periodic multi-millisecond garbage collection / collision detection spikes. Per-step latency distribution ($p50, p95, \text{max}$) must be benchmarked with setpoints applied across 150 trials in Exp-4.
3. **Platform Scope:**
   S4 validates workstation SIL simulation throughput for batch evaluation. It does not measure Pi 5 Core 0 load, where OpenWakeWord, Silero VAD, and ALSA capture run concurrently (Table 7).

## Verdict
- **PASS (Workstation Physics Feasibility)**: Confirms PyFlyt/PyBullet on CPU easily sustains 5-drone simulation without choking workstation test pipelines. Closed-loop control jitter will be benchmarked in Session 08 (Exp-4).
