# Spike S0 Report: Audio Hardware Bring-Up & Noise Floor Validation

- **Date:** 2026-09-07
- **Owner:** Human (hands-on microphone)
- **Target Platform:** Raspberry Pi 5 / Workstation with USB Capture Microphone
- **Status:** Pending Execution

## Setup
- Capture device: USB Microphone (`arecord -l`)
- Configuration: 48 kHz, S16_LE, 1 channel (mono)
- Gain control: `alsamixer -c 1` (F4 Capture level set, AGC disabled)

## Measurements
- **Silence RMS (Noise Floor):** `[ENTER VALUE]` dBFS (Pass condition: $\le -50$ dBFS, hard ceiling $-40$ dBFS)
- **Speech Peak:** `[ENTER VALUE]` dBFS (Target: $\sim -20$ dBFS)
- **Loopback Latency:** `[ENTER VALUE]` ms
- **Resampling Strategy:** Offline 3:1 soxr VHQ resample for dataset; live-path evaluated against latency constraints.

## Observations & Decision
- Hardware check:
- R-2 Escalation needed? (Yes/No):
- Final Decision:
