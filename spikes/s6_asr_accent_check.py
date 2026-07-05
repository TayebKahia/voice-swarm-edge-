#!/usr/bin/env python3
"""
Spike S6: ASR Accent Sensitivity Pre-Check
Prompts the human author for 20 self-recorded commands, feeds them through
whisper.cpp tiny.en, computes Word Error Rate (WER) against reference,
and facilitates the tiny.en vs base.en decision.
"""

import os
import re
import sys
import subprocess
import string

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

def normalize(text):
    # Fixed normalisation: lowercase, strip punctuation, strip extra whitespace
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return " ".join(text.split())

def calculate_wer(ref, hyp):
    r = ref.split()
    h = hyp.split()
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if r[i - 1] == h[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                sub = d[i - 1][j - 1] + 1
                ins = d[i][j - 1] + 1
                delt = d[i - 1][j] + 1
                d[i][j] = min(sub, ins, delt)
    return d[len(r)][len(h)] / max(1, len(r))

def main():
    print("=== Spike S6: ASR Accent Sensitivity Pre-Check ===")
    print("This script prompts for 20 voice utterances and computes WER.\n")
    
    whisper_bin = os.path.expanduser("~/whisper.cpp/build/bin/whisper-cli")
    if not os.path.exists(whisper_bin):
        whisper_bin = os.path.expanduser("~/whisper.cpp/main")
    
    model_path = os.path.expanduser("~/whisper.cpp/models/ggml-tiny.en.bin")
    
    record_mode = True
    if not os.path.exists(whisper_bin) or not os.path.exists(model_path):
        print(f"[NOTE] whisper.cpp or model not yet present on workstation ({whisper_bin}).")
        print("You can record the 20 audio clips now, and transcribe them once whisper is built, or run on Pi.\n")

    os.makedirs("/tmp/s6_recordings", exist_ok=True)
    
    results = []
    total_wer = []
    
    for idx, ref in enumerate(REFERENCE_COMMANDS, 1):
        out_wav = f"/tmp/s6_recordings/utt_{idx:02d}.wav"
        print(f"\n[{idx}/20] Prompt: \"{ref}\"")
        input(f"Press Enter, then clearly speak the prompt (recording for 4 seconds)...")
        cmd = f"arecord -d 4 -f S16_LE -r 16000 -c 1 {out_wav} 2>/dev/null"
        subprocess.run(cmd, shell=True)
        print(f"Recorded to {out_wav}")
        
        if os.path.exists(whisper_bin) and os.path.exists(model_path):
            trans_cmd = f"{whisper_bin} -m {model_path} -f {out_wav} -nt 2>/dev/null"
            res = subprocess.run(trans_cmd, shell=True, capture_output=True, text=True)
            hyp = res.stdout.strip()
            wer = calculate_wer(normalize(ref), normalize(hyp))
            total_wer.append(wer)
            print(f"  Recognized: \"{hyp}\"")
            print(f"  Item WER:   {wer:.2f}")
            results.append((ref, hyp, wer))

    if total_wer:
        mean_wer = sum(total_wer) / len(total_wer)
        print("\n=== SUMMARY S6 RESULTS ===")
        print(f"Total Utterances: {len(total_wer)}")
        print(f"Mean WER: {mean_wer:.2%}")
        if mean_wer <= 0.20:
            print("-> Recommendation: tiny.en satisfies accuracy requirement.")
        else:
            print("-> Recommendation: Consider evaluating base.en vs tiny.en trade-off.")

if __name__ == "__main__":
    main()
