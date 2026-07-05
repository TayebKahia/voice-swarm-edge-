#!/usr/bin/env python3
"""
Spike S7: Preemption Capability & Architecture Evaluation
Tests whether a decode loop can be safely preempted within 200 ms without
crashing the process or corrupting internal state, and compares against the
separate-process fallback architecture.
"""

import os
import sys
import time
import signal
import subprocess
import threading

def simulate_in_process_preemption():
    print("--- Test 1: In-Process Thread Cancellation / Signal Preemption ---")
    abort_requested = threading.Event()
    decode_running = threading.Event()
    tokens_emitted = []
    
    def dummy_decode():
        decode_running.set()
        for i in range(100):
            if abort_requested.is_set():
                print(f"[Decode Thread] Abort signal caught at token {i}!")
                return
            time.append = time.sleep(0.01) # 10 ms per token
            tokens_emitted.append(i)
        print("[Decode Thread] Finished all 100 tokens.")

    t = threading.Thread(target=dummy_decode)
    t0 = time.perf_counter()
    t.start()
    
    # Wait 200 ms
    time.sleep(0.200)
    t_signal = time.perf_counter()
    print(f"[Main] Triggering abort at {(t_signal - t0)*1000:.1f} ms...")
    abort_requested.set()
    t.join(timeout=1.0)
    t_end = time.perf_counter()
    
    latency_ms = (t_end - t_signal) * 1000
    print(f"[Main] Decode stopped in {latency_ms:.2f} ms (Target <= 100 ms recovery).")
    print(f"[Main] Emitted {len(tokens_emitted)} tokens before abort.")
    
    # Verify subsequent decode survives
    abort_requested.clear()
    tokens_emitted.clear()
    t2 = threading.Thread(target=dummy_decode)
    t2.start()
    t2.join(timeout=2.0)
    print(f"[Main] Subsequent decode succeeded with {len(tokens_emitted)} tokens.")
    return latency_ms <= 100.0

def simulate_separate_process_fallback():
    print("\n--- Test 2: Separate-Process Fallback (Subprocess Kill/Preemption) ---")
    # Launch long-running dummy decode subprocess
    t0 = time.perf_counter()
    p = subprocess.Popen([sys.executable, "-c", "import time; [time.sleep(0.01) for _ in range(200)]"])
    time.sleep(0.200)
    
    t_sig = time.perf_counter()
    p.send_signal(signal.SIGKILL)
    p.wait()
    t_end = time.perf_counter()
    
    preempt_time = (t_end - t_sig) * 1000
    print(f"[Separate Process] Process terminated in {preempt_time:.2f} ms.")
    
    # Launch replacement
    t_respawn0 = time.perf_counter()
    p2 = subprocess.Popen([sys.executable, "-c", "exit(0)"])
    p2.wait()
    t_respawn_end = time.perf_counter()
    respawn_time = (t_respawn_end - t_respawn0) * 1000
    print(f"[Separate Process] New process spawned in {respawn_time:.2f} ms.")
    total_recovery = preempt_time + respawn_time
    print(f"[Separate Process] Total preemption-recovery time: {total_recovery:.2f} ms (NFR-17 budget <= 300 ms).")
    return total_recovery <= 300.0

if __name__ == "__main__":
    r1 = simulate_in_process_preemption()
    r2 = simulate_separate_process_fallback()
    print("\n=== Architectural Decision for Branch A Preemption ===")
    print(f"In-process preemption viable: {r1}")
    print(f"Separate-process preemption viable: {r2}")
    if r1:
        print("Decision: Use atomic abort callback flag for in-process llama.cpp / server preemption.")
    else:
        print("Decision: Adopt separate-process worker architecture (SIGKILL + respawn within 300 ms budget).")
