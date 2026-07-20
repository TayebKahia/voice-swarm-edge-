#!/usr/bin/env python3
"""
Spike S0: Audio Hardware Bring-Up & Noise Floor Validation
Uses sounddevice (PipeWire / ALSA default) with live level meter and playback verification.
Target: 48 kHz, mono capture.
Pass condition: Silence RMS <= -50 dBFS, Speech peak ~ -20 dBFS.
"""

import os
import sys
import time
import subprocess
import numpy as np

# Lock PipeWire / PulseAudio input stream directly to the verified USB microphone
if "PULSE_SOURCE" not in os.environ:
    os.environ["PULSE_SOURCE"] = "alsa_input.usb-GeneralPlus_USB_Audio_Device-00.mono-fallback"

import soundfile as sf
import sounddevice as sd

def draw_vu_meter(level_dbfs, peak_dbfs, label=""):
    # Normalize -60 dBFS to 0 dBFS into 30 characters
    clamped = max(-60.0, min(0.0, level_dbfs))
    bars = int((clamped + 60.0) / 60.0 * 30)
    meter = "#" * bars + "-" * (30 - bars)
    print(f"\r{label} [{meter}] RMS: {level_dbfs:6.1f} dBFS | Peak: {peak_dbfs:6.1f} dBFS", end="", flush=True)

def find_usb_input_device():
    """Locate the USB Audio Device index in sounddevice."""
    devices = sd.query_devices()
    # First priority: direct ALSA hw/plughw USB device
    for idx, dev in enumerate(devices):
        if dev.get("max_input_channels", 0) > 0:
            name = dev.get("name", "").lower()
            if ("usb" in name or "generalplus" in name) and ("hw:" in name or "plughw:" in name):
                return idx, dev["name"]
    # Second priority: any USB input
    for idx, dev in enumerate(devices):
        if dev.get("max_input_channels", 0) > 0:
            name = dev.get("name", "").lower()
            if "usb" in name or "generalplus" in name:
                return idx, dev["name"]
    return None, None

def record_stream(duration=5, rate=48000, filename="/tmp/s0_test.wav", label="Recording", device=None):
    dev_str = f"Device {device}" if device is not None else "Default"
    print(f"\n=== Recording {duration}s of {label} (48 kHz mono, {dev_str}) ===")
    
    total_frames = int(duration * rate)
    buffer = np.zeros((total_frames, 1), dtype=np.float32)
    frames_recorded = 0

    chunk_size = 2400 # 50 ms chunks

    try:
        with sd.InputStream(device=device, samplerate=rate, channels=1, dtype='float32', blocksize=chunk_size) as stream:
            # Settle ADC / capacitive coupling & discard initial Enter-key / power-on transient (300 ms)
            warmup_frames = int(rate * 0.3)
            for _ in range(0, warmup_frames, chunk_size):
                stream.read(min(chunk_size, warmup_frames))

            for _ in range(0, total_frames, chunk_size):
                chunk, overflowed = stream.read(chunk_size)
                end_frame = min(frames_recorded + chunk_size, total_frames)
                actual_frames = end_frame - frames_recorded
                buffer[frames_recorded:end_frame] = chunk[:actual_frames]
                frames_recorded += actual_frames

                # Live meter on chunk (AC centered)
                ac_chunk = chunk - np.mean(chunk)
                rms = np.sqrt(np.mean(ac_chunk**2) + 1e-12)
                rms_dbfs = 20 * np.log10(rms)
                peak_dbfs = 20 * np.log10(np.max(np.abs(ac_chunk)) + 1e-12)
                draw_vu_meter(rms_dbfs, peak_dbfs, label=label[:7])
                
        print() # Newline after meter
    except Exception as e:
        dev_arg = f"-D plughw:{device},0" if device is not None else "-D default"
        print(f"\nsounddevice stream error: {e}. Falling back to arecord {dev_arg}...")
        cmd = f"arecord {dev_arg} -d {duration} -f S16_LE -r {rate} -c 1 -t wav {filename}"
        subprocess.run(cmd, shell=True)
        data, _ = sf.read(filename)
        buffer = data.reshape(-1, 1)

    # Save to file
    sf.write(filename, buffer, rate)
    data = buffer.flatten()
    
    # Analyze AC component
    dc_offset = np.mean(data)
    ac_data = data - dc_offset
    rms_ac = np.sqrt(np.mean(ac_data**2) + 1e-12)
    rms_dbfs = 20 * np.log10(rms_ac)
    peak_ac = np.max(np.abs(ac_data)) + 1e-12
    peak_dbfs = 20 * np.log10(peak_ac)

    print(f"[{label} Summary]")
    print(f"  File saved:     {filename}")
    print(f"  DC Bias Offset: {dc_offset:.5f} ({20*np.log10(max(1e-6, abs(dc_offset))):.1f} dBFS)")
    print(f"  True AC RMS:    {rms_dbfs:.2f} dBFS")
    print(f"  True AC Peak:   {peak_dbfs:.2f} dBFS")
    return {"rms_dbfs": rms_dbfs, "peak_dbfs": peak_dbfs, "filename": filename}

def main():
    print("=== Spike S0: Audio Bring-Up & Validation ===")
    target_device = None
    try:
        usb_idx, usb_name = find_usb_input_device()
        if usb_idx is not None:
            print(f"[+] Found USB Microphone: [Device {usb_idx}] '{usb_name}'")
            target_device = usb_idx
        else:
            dev_info = sd.query_devices(kind='input')
            print(f"[!] Warning: No USB mic detected. Falling back to default: '{dev_info['name']}'")
    except Exception as exc:
        print(f"[-] Device query error: {exc}")

    input("\n[1/2] Press Enter to record 5s of ROOM SILENCE (keep quiet)...")
    silence = record_stream(duration=5, filename="/tmp/s0_silence.wav", label="Silence", device=target_device)

    input("\n[2/2] Press Enter to record 5s of SPEECH (speak: 'swarm move forward five meters')...")
    speech = record_stream(duration=5, filename="/tmp/s0_speech.wav", label="Speech", device=target_device)

    print("\n=== SPIKE S0 EVALUATION ===")
    if silence:
        nf = silence["rms_dbfs"]
        print(f"Noise Floor (Silence RMS): {nf:.2f} dBFS (Target <= -50 dBFS, Ceiling -40 dBFS)")
        if nf <= -50.0:
            print("  -> PASS: Noise floor is optimal (<= -50 dBFS).")
        elif nf <= -40.0:
            print("  -> ACCEPTABLE: Between -50 dBFS and -40 dBFS.")
        else:
            print("  -> FAIL: Noise floor > -40 dBFS.")
            
    if speech:
        sp = speech["peak_dbfs"]
        print(f"Speech Peak: {sp:.2f} dBFS (Target ~ -20 dBFS)")
        if sp >= -30.0:
            print("  -> PASS: Speech volume is good.")
        else:
            print("  -> WARNING: Speech peak is low (< -30 dBFS). Speak closer to the mic.")

    print("\n--- Playback Verification ---")
    play = input("Would you like to play back your speech recording (normalized for clarity)? [Y/n]: ").strip().lower()
    if play in ("", "y", "yes"):
        # Save a normalized copy so the human ear can clearly hear every syllable
        raw_data, sr = sf.read(speech["filename"])
        ac = raw_data - np.mean(raw_data)
        peak = np.max(np.abs(ac))
        if peak > 0:
            boosted = ac / peak * 0.85
            norm_file = "/tmp/s0_speech_boosted.wav"
            sf.write(norm_file, boosted, sr)
            print(f"Playing normalized audio ({norm_file})...")
            subprocess.run(f"paplay {norm_file} 2>/dev/null || aplay {norm_file}", shell=True)
        else:
            subprocess.run(f"paplay {speech['filename']} 2>/dev/null || aplay {speech['filename']}", shell=True)

if __name__ == "__main__":
    main()
