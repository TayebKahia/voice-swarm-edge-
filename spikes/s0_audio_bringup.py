#!/usr/bin/env python3
"""
Spike S0: Audio Hardware Bring-Up & Noise Floor Validation
Target: 48 kHz, S16_LE, mono capture.
Pass condition: Silence RMS <= -50 dBFS, Speech peak ~ -20 dBFS.
If noise floor > -40 dBFS -> R-2 escalation ladder.
"""

import os
import sys
import time
import subprocess
import numpy as np

def run_cmd(cmd):
    print(f"[CMD] {cmd}")
    res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    return res

def list_devices():
    print("=== Step 1: Listing Audio Capture Devices (arecord -l) ===")
    run_cmd("arecord -l")
    print("\nNOTE: Unmute capture and set appropriate gain using 'alsamixer -c 1' (F4) before measuring.\n")

def record_and_analyze(duration=5, rate=48000, filename="/tmp/s0_silence.wav", label="Silence"):
    print(f"=== Step 2: Recording {duration}s of {label} at {rate} Hz (S16_LE, mono) ===")
    cmd = f"arecord -d {duration} -f S16_LE -r {rate} -c 1 -t wav {filename}"
    res = run_cmd(cmd)
    if res.returncode != 0:
        print(f"Error recording {label}: {res.stderr}")
        return None

    # Load audio
    try:
        import soundfile as sf
        data, sr = sf.read(filename)
    except Exception:
        import wave
        with wave.open(filename, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

    rms = np.sqrt(np.mean(data**2) + 1e-12)
    rms_dbfs = 20 * np.log10(rms)
    peak = np.max(np.abs(data)) + 1e-12
    peak_dbfs = 20 * np.log10(peak)

    print(f"[{label} Analysis]")
    print(f"  RMS:  {rms_dbfs:.2f} dBFS")
    print(f"  Peak: {peak_dbfs:.2f} dBFS")
    return {"rms_dbfs": rms_dbfs, "peak_dbfs": peak_dbfs}

def main():
    list_devices()
    input("Press Enter to record 5 seconds of ROOM SILENCE (keep quiet)...")
    silence = record_and_analyze(duration=5, filename="/tmp/s0_silence.wav", label="Silence")
    
    input("Press Enter to record 5 seconds of NORMAL SPEECH (say: 'swarm move forward five meters')...")
    speech = record_and_analyze(duration=5, filename="/tmp/s0_speech.wav", label="Speech")

    print("\n=== SPIKE S0 EVALUATION ===")
    if silence:
        nf = silence["rms_dbfs"]
        print(f"Noise Floor (Silence RMS): {nf:.2f} dBFS (Target <= -50 dBFS, Ceiling -40 dBFS)")
        if nf <= -50.0:
            print("  -> PASS: Noise floor is optimal (<= -50 dBFS).")
        elif nf <= -40.0:
            print("  -> ACCEPTABLE: Between -50 dBFS and -40 dBFS. Verify gain staging.")
        else:
            print("  -> FAIL: Noise floor > -40 dBFS. Escalate to R-2 ladder (check USB ground loop, gain, acoustic environment).")
            
    if speech:
        sp = speech["peak_dbfs"]
        print(f"Speech Peak: {sp:.2f} dBFS (Target ~ -20 dBFS)")
        if -30.0 <= sp <= -10.0:
            print("  -> PASS: Speech peak in expected dynamic range.")
        else:
            print("  -> WARNING: Adjust mic gain in alsamixer.")

if __name__ == "__main__":
    main()
