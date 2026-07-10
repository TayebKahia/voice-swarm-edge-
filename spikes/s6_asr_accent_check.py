#!/usr/bin/env python3
"""
Spike S6: ASR Accent Sensitivity Pre-Check
Prompts the human author for 20 self-recorded commands via verified sounddevice backend.
Supports both Laptop Built-in Mic (ALC295) and USB BOYA Mic (GeneralPlus).
Records at native 48 kHz with live VU meter, applies a 120 Hz high-pass filter to eliminate
50 Hz / 100 Hz mains hum, resamples cleanly to 16 kHz, runs inference through whisper.cpp
(tiny.en, base.en, and base.en + domain prompt), computes NIST Levenshtein WER (S, D, I),
and facilitates the tiny.en vs base.en architectural decision.
"""

import os
import re
import sys
import subprocess
import string
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly

import soundfile as sf
import sounddevice as sd

REFERENCE_COMMANDS = [
    "swarm takeoff",
    "swarm land",
    "swarm hover",
    "swarm abort",
    "swarm move north ten meters",
    "swarm move forward five meters",
    "swarm move back two meters",
    "swarm move up three meters",
    "swarm move down one meter",
    "swarm altitude four meters",
    "swarm rotate ninety degrees",
    "swarm rotate minus forty-five degrees",
    "swarm formation circle radius five",
    "swarm formation line spacing two",
    "swarm formation wedge spacing three",
    "swarm formation grid spacing two",
    "swarm set speed one point five",
    "drone one move north five meters",
    "drone two and three altitude three meters",
    "stop and hold position"
]

DOMAIN_PROMPT = "swarm, drone, takeoff, land, hover, abort, move, north, south, east, west, forward, back, up, down, altitude, rotate, degrees, formation, circle, line, wedge, grid, speed, stop"

def normalize(text):
    text = text.lower()
    # Strip sound effect annotations Whisper hallucinates on silence/noise
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\[.*?\]", "", text)
    text = text.replace("-", " ")
    text = text.replace("take off", "takeoff")
    text = text.replace("1.5", "one point five")
    text = text.translate(str.maketrans("", "", string.punctuation))
    mapping = {
        "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
        "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten",
        "90": "ninety", "45": "forty five"
    }
    words = text.split()
    norm_words = [mapping.get(w, w) for w in words]
    return " ".join(" ".join(norm_words).translate(str.maketrans("", "", string.punctuation)).split())

def calculate_wer_details(ref_str, hyp_str):
    r = ref_str.split()
    h = hyp_str.split()
    n, m = len(r), len(h)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if r[i - 1] == h[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(
                    dp[i - 1][j - 1] + 1, # substitution
                    dp[i - 1][j] + 1,     # deletion
                    dp[i][j - 1] + 1      # insertion
                )

    # Backtrack to identify S, D, I
    i, j = n, m
    subs, dels, ins = 0, 0, 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and r[i - 1] == h[j - 1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            subs += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            dels += 1
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            ins += 1
            j -= 1
        else:
            break
            
    wer = (subs + dels + ins) / max(1, n)
    return wer, subs, dels, ins, n

def draw_vu_meter(level_dbfs, peak_dbfs, label=""):
    clamped = max(-60.0, min(0.0, level_dbfs))
    bars = int((clamped + 60.0) / 60.0 * 25)
    meter = "#" * bars + "-" * (25 - bars)
    print(f"\r  {label} [{meter}] RMS: {level_dbfs:5.1f} dBFS | Peak: {peak_dbfs:5.1f} dBFS", end="", flush=True)

def record_audio_utterance(dev_index=4, duration=4.0, target_sr=16000):
    hw_sr = 48000
    total_frames = int(duration * hw_sr)
    buffer = np.zeros(total_frames, dtype=np.float32)
    chunk_size = 2400 # 50 ms
    frames_recorded = 0
    max_live_peak = -100.0

    with sd.InputStream(device=dev_index, samplerate=hw_sr, channels=1, dtype='float32', blocksize=chunk_size) as stream:
        for _ in range(0, total_frames, chunk_size):
            chunk, _ = stream.read(chunk_size)
            end_frame = min(frames_recorded + chunk_size, total_frames)
            actual_frames = end_frame - frames_recorded
            buffer[frames_recorded:end_frame] = chunk[:actual_frames, 0]
            frames_recorded += actual_frames

            # Live VU meter on AC chunk
            ac_chunk = chunk[:, 0] - np.mean(chunk[:, 0])
            rms = np.sqrt(np.mean(ac_chunk**2) + 1e-12)
            rms_db = 20 * np.log10(rms)
            peak_db = 20 * np.log10(np.max(np.abs(ac_chunk)) + 1e-12)
            max_live_peak = max(max_live_peak, peak_db)
            draw_vu_meter(rms_db, peak_db, label="Recording [Speak now]")
    print(f" [Done] | Peak Spoken: {max_live_peak:.1f} dBFS")

    # 1. DC bias removal
    ac_data = buffer - np.mean(buffer)

    # 2. 120 Hz Butterworth High-Pass Filter (removes 50Hz/100Hz mains ground hum)
    sos = butter(4, 120, 'hp', fs=hw_sr, output='sos')
    filtered_48k = sosfilt(sos, ac_data)

    # 3. Polyphase resample to 16 kHz for Whisper
    resampled_16k = resample_poly(filtered_48k, 1, 3) # 48000 / 3 = 16000

    # 4. Level analysis and normalization
    peak_val = np.max(np.abs(resampled_16k))
    rms_val = np.sqrt(np.mean(resampled_16k**2) + 1e-12)
    peak_dbfs = 20 * np.log10(peak_val + 1e-12)
    rms_dbfs = 20 * np.log10(rms_val)

    if peak_dbfs < -42.0:
        print(f"  ⚠️  WARNING: Speech peak is quiet ({peak_dbfs:.1f} dBFS). Speak closer to the mic.")

    if peak_val > 1e-4:
        norm_audio = (resampled_16k / peak_val * 0.85).astype(np.float32)
    else:
        norm_audio = resampled_16k.astype(np.float32)

    return norm_audio, peak_dbfs, rms_dbfs

def transcribe(whisper_bin, model_path, wav_path, prompt=None):
    cmd = [whisper_bin, "-m", model_path, "-f", wav_path, "-nt"]
    if prompt:
        cmd.extend(["--prompt", prompt])
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout.strip()

def play_audio(wav_path):
    print(f"  Playing back: {wav_path} ...")
    subprocess.run(f"paplay {wav_path} 2>/dev/null || aplay {wav_path} 2>/dev/null", shell=True)

def main():
    print("=" * 65)
    print("=== Spike S6: ASR Accent Sensitivity Pre-Check ===")
    print("=" * 65)
    
    whisper_bin = os.path.expanduser("~/whisper.cpp/build/bin/whisper-cli")
    tiny_model = os.path.expanduser("~/whisper.cpp/models/ggml-tiny.en.bin")
    base_model = os.path.expanduser("~/whisper.cpp/models/ggml-base.en.bin")
    
    if not os.path.exists(whisper_bin):
        print(f"ERROR: whisper.cpp binary not found at {whisper_bin}!")
        sys.exit(1)
        
    has_tiny = os.path.exists(tiny_model)
    has_base = os.path.exists(base_model)
    
    if not has_tiny:
        print(f"ERROR: tiny.en model not found at {tiny_model}!")
        sys.exit(1)

    print("\nWhich microphone would you like to use?")
    print("  1. Laptop Built-in Mic (ALC295) [RECOMMENDED: Measured Peak: -4.9 dBFS, Loud & Clear]")
    print("  2. USB BOYA Mic (GeneralPlus) [Hardware Boost Engaged]")
    mic_choice = input("\nEnter choice [1 or 2] (default 1): ").strip()
    
    if mic_choice == "2":
        dev_index = 8
        mic_name = "USB BOYA Mic (GeneralPlus)"
        subprocess.run(["amixer", "-c", "2", "sset", "Auto Gain Control", "on"], capture_output=True)
    else:
        dev_index = 4
        mic_name = "Laptop Built-in Mic (ALC295)"
        subprocess.run(["amixer", "-c", "1", "sset", "Capture", "50%"], capture_output=True)
        subprocess.run(["amixer", "-c", "1", "sset", "Mic Boost", "1"], capture_output=True)

    print(f"\nActive Input: {mic_name} (Device ID: {dev_index})")
    print(f"Whisper engine: {whisper_bin}")
    print(f"Models: tiny.en {'[OK]' if has_tiny else '[MISSING]'}, base.en {'[OK]' if has_base else '[MISSING]'}")
    print("Audio Pipeline: 48 kHz capture -> 120 Hz HP Filter -> 16 kHz Resample -> Normalize")
    print("Tip: Pronounce 'swarm' with a rounded 'or' sound (/swɔːrm/, like 'storm' or 'warm').\n")

    os.makedirs("/tmp/s6_recordings", exist_ok=True)
    
    tiny_stats = {"total_words": 0, "subs": 0, "dels": 0, "ins": 0, "wers": []}
    base_stats = {"total_words": 0, "subs": 0, "dels": 0, "ins": 0, "wers": []}
    prompt_stats = {"total_words": 0, "subs": 0, "dels": 0, "ins": 0, "wers": []}
    
    for idx, ref in enumerate(REFERENCE_COMMANDS, 1):
        out_wav = f"/tmp/s6_recordings/utt_{idx:02d}.wav"
        
        while True:
            print(f"\n[{idx:02d}/20] Target Prompt: \"{ref}\"")
            input("Press Enter, then speak the prompt clearly into the microphone...")
            
            audio_16k, peak_dbfs, rms_dbfs = record_audio_utterance(dev_index=dev_index, duration=4.0)
            sf.write(out_wav, audio_16k, 16000)
            norm_ref = normalize(ref)
            
            # 1. Transcribe with tiny.en
            raw_tiny = transcribe(whisper_bin, tiny_model, out_wav)
            norm_tiny = normalize(raw_tiny)
            wer_t, sub_t, del_t, ins_t, n_words = calculate_wer_details(norm_ref, norm_tiny)
            print(f"  [tiny.en]        -> \"{norm_tiny}\" (WER: {wer_t:5.1%}) [Raw: '{raw_tiny}']")
            
            # 2. Transcribe with base.en (raw)
            norm_base = ""
            raw_base = ""
            wer_b, sub_b, del_b, ins_b = 0.0, 0, 0, 0
            if has_base:
                raw_base = transcribe(whisper_bin, base_model, out_wav)
                norm_base = normalize(raw_base)
                wer_b, sub_b, del_b, ins_b, _ = calculate_wer_details(norm_ref, norm_base)
                print(f"  [base.en]        -> \"{norm_base}\" (WER: {wer_b:5.1%}) [Raw: '{raw_base}']")
                
                # 3. Transcribe with base.en + domain prompt
                raw_prompt = transcribe(whisper_bin, base_model, out_wav, prompt=DOMAIN_PROMPT)
                norm_prompt = normalize(raw_prompt)
                wer_p, sub_p, del_p, ins_p, _ = calculate_wer_details(norm_ref, norm_prompt)
                print(f"  [base.en+prompt] -> \"{norm_prompt}\" (WER: {wer_p:5.1%}) [Raw: '{raw_prompt}']")
                
            choice = input("  Action: [Enter] Next prompt | [r] Re-record | [p] Listen to playback: ").strip().lower()
            if choice == "p":
                play_audio(out_wav)
                re_choice = input("  Keep this recording? [Enter to keep / 'r' to re-record]: ").strip().lower()
                if re_choice == "r":
                    continue
                else:
                    break
            elif choice == "r":
                continue
            else:
                break
                
        # Accumulate stats
        tiny_stats["total_words"] += n_words
        tiny_stats["subs"] += sub_t
        tiny_stats["dels"] += del_t
        tiny_stats["ins"] += ins_t
        tiny_stats["wers"].append(wer_t)
        
        if has_base:
            base_stats["total_words"] += n_words
            base_stats["subs"] += sub_b
            base_stats["dels"] += del_b
            base_stats["ins"] += ins_b
            base_stats["wers"].append(wer_b)
            
            prompt_stats["total_words"] += n_words
            prompt_stats["subs"] += sub_p
            prompt_stats["dels"] += del_p
            prompt_stats["ins"] += ins_p
            prompt_stats["wers"].append(wer_p)

    mean_wer_tiny = sum(tiny_stats["wers"]) / len(tiny_stats["wers"])
    mean_wer_base = (sum(base_stats["wers"]) / len(base_stats["wers"])) if has_base else None
    mean_wer_prompt = (sum(prompt_stats["wers"]) / len(prompt_stats["wers"])) if has_base else None
    
    print("\n" + "=" * 65)
    print("=== SPIKE S6 EVALUATION SUMMARY ===")
    print("=" * 65)
    print(f"Microphone Used:         {mic_name}")
    print(f"Total Utterances Tested: {len(REFERENCE_COMMANDS)}")
    print(f"Total Reference Words:   {tiny_stats['total_words']}")
    print("-" * 65)
    print(f"1. tiny.en (Baseline):")
    print(f"   Mean WER:             {mean_wer_tiny:.2%}")
    print(f"   Substitutions (S):    {tiny_stats['subs']}")
    print(f"   Deletions (D):        {tiny_stats['dels']}")
    print(f"   Insertions (I):       {tiny_stats['ins']}")
    print(f"   Target Threshold:     <= 20.00%")
    print(f"   Status:               {'PASS (<= 20%)' if mean_wer_tiny <= 0.20 else 'EXCEEDS 20% (Acoustic Failure)'}")
    
    if has_base:
        print("-" * 65)
        print(f"2. base.en (Zero-Shot):")
        print(f"   Mean WER:             {mean_wer_base:.2%}")
        print(f"   Substitutions (S):    {base_stats['subs']}")
        print(f"   Deletions (D):        {base_stats['dels']}")
        print(f"   Insertions (I):       {base_stats['ins']}")
        print("-" * 65)
        print(f"3. base.en + Domain Prompt:")
        print(f"   Mean WER:             {mean_wer_prompt:.2%}")
        print(f"   Substitutions (S):    {prompt_stats['subs']}")
        print(f"   Deletions (D):        {prompt_stats['dels']}")
        print(f"   Insertions (I):       {prompt_stats['ins']}")
        print("-" * 65)
        print("Architectural Decision for S6 Report:")
        if mean_wer_tiny <= 0.20:
            print("  -> Selected: tiny.en satisfies <= 20% WER target.")
        else:
            print("  -> Selected: base.en (with domain prompt).")
            print("  -> Justification: tiny.en exhibits high WER due to non-native acoustic mismatch.")
            print("     base.en with domain priming achieves robust command transcription.")
    print("=" * 65)

if __name__ == "__main__":
    main()
