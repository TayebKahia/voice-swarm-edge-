#!/usr/bin/env python3
"""
Spike S4: PyFlyt Swarm Simulation Feasibility Benchmark
Evaluates a 5-drone swarm simulation at 50 Hz control loop frequency in PyFlyt.
Pass condition: Real-Time Factor (RTF) >= 1.0 (simulation faster than real-time).
"""

import time
import numpy as np
from PyFlyt.core import Aviary

def run_benchmark(num_drones=5, sim_seconds=10.0, control_hz=50, physics_hz=250):
    print(f"=== Spike S4: PyFlyt Swarm Simulation Benchmark ===")
    print(f"Drones: {num_drones} quadx")
    print(f"Control frequency: {control_hz} Hz")
    print(f"Physics frequency: {physics_hz} Hz")
    print(f"Duration: {sim_seconds:.1f} simulated seconds")
    
    angles = np.linspace(0, 2 * np.pi, num_drones, endpoint=False)
    radius = 2.0
    start_pos = np.zeros((num_drones, 3))
    start_pos[:, 0] = radius * np.cos(angles)
    start_pos[:, 1] = radius * np.sin(angles)
    start_pos[:, 2] = 1.0
    start_orn = np.zeros((num_drones, 3))

    total_control_steps = int(sim_seconds * control_hz)
    drone_options = [{"control_hz": control_hz}] * num_drones

    env = Aviary(
        start_pos=start_pos,
        start_orn=start_orn,
        drone_type="quadx",
        drone_options=drone_options,
        render=False,
        physics_hz=physics_hz
    )

    # In PyFlyt, aviary.step() steps the whole aviary by one control step (advancing physics by physics_hz / control_hz)
    # Warmup
    env.step()

    # Benchmark loop
    t_start = time.perf_counter()
    for _ in range(total_control_steps):
        # In actual control, setpoints are passed; here we step the physical swarm dynamics
        env.step()
            
    t_end = time.perf_counter()
    wall_time = t_end - t_start
    rtf = sim_seconds / wall_time

    print(f"\n--- Simulation Benchmark Results ---")
    print(f"Simulated time: {sim_seconds:.2f} s")
    print(f"Wall-clock time: {wall_time:.3f} s")
    print(f"Real-Time Factor (RTF): {rtf:.2f}x (Target >= 1.0x)")
    
    if rtf >= 1.0:
        print("-> PASS: Simulation executes faster than real-time.")
    else:
        print("-> FAIL: Simulation is slower than real-time.")
        
    return {
        "num_drones": num_drones,
        "sim_seconds": sim_seconds,
        "wall_time": wall_time,
        "rtf": rtf,
        "control_hz": control_hz,
        "physics_hz": physics_hz,
        "passed": rtf >= 1.0
    }

if __name__ == "__main__":
    run_benchmark()
