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
- **Simulated Duration:** 10.00 s
- **Wall-Clock Execution Time:** 2.117 s
- **Real-Time Factor (RTF):** **4.72x** (Pass condition: $\text{RTF} \ge 1.0$)
- **Per-step wall time:** 4.23 ms (budget per 50 Hz tick: 20.0 ms)

## Verdict & Architectural Implication
- **PASS**: PyFlyt with PyBullet backend comfortably runs 5-drone simulation at 4.72x faster than real-time on CPU.
- Real-time simulation headroom is $>78\%$, confirming that running Exp-4 SIL (Software-in-the-Loop) simulations on the workstation at 50 Hz is completely viable without bottlenecking.
