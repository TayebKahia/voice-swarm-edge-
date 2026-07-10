#!/usr/bin/env python3
"""
Audio Diagnostic Tool: Dual-Mic Live Level Monitor
Monitors both the USB Audio Device and the Built-in Laptop Microphone simultaneously.
"""

import os
import sys
import time
import numpy as np
import sounddevice as sd

def main():
    print("=== Audio Diagnostic: Live Multi-Device Monitor ===")
    print("This will monitor all active microphone inputs for 10 seconds.")
    print("Speak or tap your microphone to see which bar moves!\n")

    # Target sources
    sources = [
        ("USB Microphone (GeneralPlus)", "alsa_input.usb-GeneralPlus_USB_Audio_Device-00.mono-fallback"),
        ("Laptop Built-in Mic (ALC295)", "alsa_input.pci-0000_00_1f.3.analog-stereo")
    ]

    duration = 10
    block_size = 2400 # 50 ms
    sr = 48000

    # We will test each source with a quick 5-second test or interactive selection
    print("Which microphone would you like to test?")
    print("  1. USB Audio Device (GeneralPlus)")
    print("  2. Built-in Laptop Mic (ALC295 Analog)")
    print("  3. Test both sequentially (5s each with live meter)")
    
    choice = input("\nEnter choice [1, 2, or 3] (default 3): ").strip()
    if choice not in ("1", "2", "3"):
        choice = "3"

    selected = sources if choice == "3" else ([sources[0]] if choice == "1" else [sources[1]])

    for name, pulse_src in selected:
        print(f"\n---> Testing: {name}")
        print("Speak now or tap the mic! Watch the VU meter:\n")
        
        # Set environment for pulse/pipewire routing
        os.environ['PULSE_SOURCE'] = pulse_src
        
        # Test 5 seconds with live visual meter
        t_end = time.time() + 5.0
        max_peak = -100.0
        
        with sd.InputStream(samplerate=sr, channels=1, dtype='float32', blocksize=block_size) as stream:
            while time.time() < t_end:
                data, _ = stream.read(block_size)
                ac = data - np.mean(data)
                rms = np.sqrt(np.mean(ac**2) + 1e-12)
                rms_db = 20 * np.log10(rms)
                peak_db = 20 * np.log10(np.max(np.abs(ac)) + 1e-12)
                max_peak = max(max_peak, peak_db)
                
                # Visual bar
                bars = int(max(0, min(30, (rms_db + 60) / 60 * 30)))
                bar_str = "#" * bars + "-" * (30 - bars)
                print(f"\r[{bar_str}] Level: {rms_db:6.1f} dBFS | Peak: {peak_db:6.1f} dBFS", end="", flush=True)
                time.sleep(0.02)
        print(f"\nTest finished for {name}. Max Peak: {max_peak:.1f} dBFS")
        if max_peak > -30.0:
            print(f"  -> SUCCESS! {name} is working and captured clear sound!")
        else:
            print(f"  -> No voice signal detected on {name} (peak stayed below -30 dBFS).")

if __name__ == "__main__":
    main()
