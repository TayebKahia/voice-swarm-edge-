# Spike S6 Report: ASR Accent Sensitivity Check

- **Date:** 2026-09-07
- **Owner:** Human (hands on microphone)
- **Status:** Pending Execution

## Test Setup
- Audio Input: USB Microphone @ 16 kHz S16_LE mono
- Test Set: 20 typical drone-swarm spoken commands
- Engine: `whisper.cpp tiny.en` (and optionally `base.en` comparison)

## Results
- **Evaluated Utterances:** 20
- **Total Words:** `[ENTER VALUE]`
- **Word Substitutions:** `[ENTER VALUE]`
- **Word Deletions:** `[ENTER VALUE]`
- **Word Insertions:** `[ENTER VALUE]`
- **Mean WER:** `[ENTER VALUE]` %

## Analysis & Model Decision
- Common recognition failures (e.g. numbers, directional terms, phonetic ambiguities):
- Acoustic comparison:
- **Decision:** `tiny.en` vs `base.en`
  - Selected model: `[tiny.en / base.en]`
  - Justification (accuracy gain vs latency/memory cost on Pi 5):
