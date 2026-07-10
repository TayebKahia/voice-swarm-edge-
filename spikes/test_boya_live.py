#!/usr/bin/env python3
"""
Dual Microphone Live Meter: USB BOYA Mic vs Laptop Built-in Mic
Monitors both inputs side-by-side in real-time so you can instantly see which one captures your voice.
"""

import os
import sys
import time
import numpy as np
import sounddevice as sd

def main():
    print("=" * 70)
    print("=== DUAL MICROPHONE LIVE MONITOR (USB BOYA vs Laptop Built-in) ===")
    print("=" * 70)
    print("Speak normally into your microphone. Watch which meter moves!")
    print("Press Ctrl+C to stop.\n")

    sr = 48000
    chunk_size = 2400 # 50 ms
    
    # Device indices:
    # 8: USB Audio Device (hw:2,0)
    # 4: HDA Intel PCH ALC295 (hw:1,0)
    dev_usb = 8
    dev_laptop = 4

    try:
        stream_usb = sd.InputStream(device=dev_usb, channels=1, samplerate=sr, blocksize=chunk_size, dtype='float32')
        stream_lap = sd.InputStream(device=dev_laptop, channels=1, samplerate=sr, blocksize=chunk_size, dtype='float32')
        stream_usb.start()
        stream_lap.start()
    except Exception as e:
        print(f"Error opening audio streams: {e}")
        return

    print("Status: Monitoring both microphones live...\n")
    print(f"{'DEVICE':<20} | {'METER (-60 to 0 dBFS)':<26} | {'RMS':<9} | {'PEAK':<9} | STATUS")
    print("-" * 75)

    max_usb_peak = -100.0
    max_lap_peak = -100.0

    try:
        while True:
            chunk_u, _ = stream_usb.read(chunk_size)
            chunk_l, _ = stream_lap.read(chunk_size)

            # USB analysis
            ac_u = chunk_u[:, 0] - np.mean(chunk_u[:, 0])
            rms_u = 20 * np.log10(np.sqrt(np.mean(ac_u**2)) + 1e-12)
            pk_u = 20 * np.log10(np.max(np.abs(ac_u)) + 1e-12)
            max_usb_peak = max(max_usb_peak, pk_u)

            # Laptop analysis
            ac_l = chunk_l[:, 0] - np.mean(chunk_l[:, 0])
            rms_l = 20 * np.log10(np.sqrt(np.mean(ac_l**2)) + 1e-12)
            pk_l = 20 * np.log10(np.max(np.abs(ac_l)) + 1e-12)
            max_lap_peak = max(max_lap_peak, pk_l)

            # Meters
            bars_u = int(max(0.0, min(20.0, (rms_u + 60.0) / 60.0 * 20)))
            m_u = "#" * bars_u + "-" * (20 - bars_u)

            bars_l = int(max(0.0, min(20.0, (rms_l + 60.0) / 60.0 * 20)))
            m_l = "#" * bars_l + "-" * (20 - bars_l)

            stat_u = "❌ UNPOWERED" if pk_u < -40 else ("✅ CLEAR" if pk_u < -10 else "⚠️ LOUD")
            stat_l = "❌ SILENT" if pk_l < -40 else ("✅ ACTIVE" if pk_l < -5 else "⚠️ LOUD")

            sys.stdout.write(f"\033[2K\r[1] USB BOYA:      [{m_u}] {rms_u:5.1f} dBFS | Pk: {pk_u:5.1f} dB | {stat_u}\n")
            sys.stdout.write(f"\033[2K[2] Laptop Mic:    [{m_l}] {rms_l:5.1f} dBFS | Pk: {pk_l:5.1f} dB | {stat_l}\033[1A")
            sys.stdout.flush()
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        stream_usb.stop()
        stream_lap.stop()
        stream_usb.close()
        stream_lap.close()
        print("\n\n" + "=" * 70)
        print(f"Summary of Max Recorded Peaks:")
        print(f"  - USB BOYA Max Peak:    {max_usb_peak:5.1f} dBFS")
        print(f"  - Laptop Built-in Peak: {max_lap_peak:5.1f} dBFS")
        print("=" * 70)

if __name__ == "__main__":
    main()
