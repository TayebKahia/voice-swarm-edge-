# Spike S0 Report: Audio Hardware Bring-Up & Noise Floor Validation

- **Date:** 2026-09-08
- **Owner:** Human author (hands-on microphone)
- **Target Platform:** Workstation USB capture chain (`GeneralPlus USB Audio Device` / `ALC295 Built-in`)
- **Status:** **PASS (Noise Floor)** / **INCOMPLETE (Loopback Latency, Table 22 Speech Peak, Pi-Side Runtime Capture)**

## Setup
- **Capture Device:** USB Audio Device (`GeneralPlus`, `alsa_input.usb-GeneralPlus_USB_Audio_Device-00.mono-fallback`) & Laptop Built-in Mic (Realtek ALC295)
- **Format:** 48 kHz, S16_LE, 1 channel (mono)
- **Power Condition:** Running on battery power (unplugged from AC wall charger to eliminate 50 Hz ground hum)
- **ALSA Hardware Gain:** `Capture 28 [100%] [30.00dB] [on]`, AGC disabled per PRD §9.3

## Acoustic & Hardware Measurements

| Metric | Measured Value | PRD Table 22 Target | Status |
| :--- | :--- | :--- | :--- |
| **Silence RMS (Noise Floor)** | **`-64.47 dBFS`** | $\le -50\text{ dBFS}$ | **PASS** (14.5 dB margin) |
| **Speech Peak (BOYA BY-M1 USB)**| **`-36.06 dBFS`** | $\approx -20\text{ dBFS}$ | **PARTIAL MISS** (16 dB below target) |
| **Speech Peak (Built-in Mic)** | **`-4.90 dBFS`** | $\approx -20\text{ dBFS}$ | Exceeds target (high gain) |
| **Signal-to-Noise Ratio (SNR)** | **`28.4 dB`** (USB) | $> 20\text{ dB}$ | PASS |
| **Hardware DC Bias Offset** | $+0.0065$ | $\approx 0.0$ | Mitigated via digital centering |
| **Hardware Loopback Latency** | **Pending Hardware Test** | Reported separately | **INCOMPLETE** (`prd.md:358`) |

---

## Audio Path Decisions (PRD §4.7)

1. **Corpus Recording Path (Offline, Quality-First):**
   - Direct ALSA capture at 48 kHz, `S16_LE`, mono.
   - Offline 3:1 resampling to 16 kHz using `soxr` at Very High Quality (`VHQ`).
   - ALSA `plug` software resampling is strictly avoided to eliminate uncontrolled sample interpolation variances in Exp-3.
2. **Live Runtime Path (Online, Latency-First):**
   - The USB audio adapter supports native 16 kHz capture; native 16 kHz capture will be configured directly in the ALSA ring buffer to bypass runtime polyphase filtering entirely, eliminating resampling latency from the edge perception loop.

---

## Observations & Open Gaps

1. **Ground-Loop Hum Diagnosis:**
   When connected to the AC wall charger, an intense 50 Hz/100 Hz hum dominated 67.7% of the signal energy (−42 dBFS). Operating on battery power completely eliminated the hum, dropping the noise floor to **−64.47 dBFS**. **Rule for Session 03:** All 200 speech dataset recordings must be conducted on battery power.
2. **Speech Peak Miss:**
   The BOYA capsule's −36.06 dBFS peak misses Table 22's −20 dBFS target. While the 28.4 dB SNR provides clean acoustic separation, offline peak normalization to −14 dBFS will be applied across the dataset before model training/evaluation to prevent low-amplitude gradient issues.
3. **Missing Loopback Latency (`prd.md:358`):**
   PRD §4.7 requires capture and buffering latency to be measured once at S0 via a loopback test and reported as a separate number. Based on the 1024-frame ALSA period size at 48 kHz plus double buffering, hardware capture latency is estimated at **$\approx 42.6\text{ ms}$**. $T_0$ anchors at **acoustic end-of-speech** (the instant the speaker stops); capture buffering and VAD silence detection both fall *inside* the E2E window, and 42.6 ms is accounted for as an explicit row in S2's latency stack-up. Will be empirically verified with a physical audio pulse loopback cable prior to Exp-2.
4. **Platform Scope:**
   S0 characterizes the workstation recording chain. The Pi 5 runtime capture chain utilizes the RP1 southbridge USB controller and a distinct ALSA kernel stack, which will be benchmarked directly during live drone integration.
