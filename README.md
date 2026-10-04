# Voice-Swarm-Edge: Natural-Language UAV Swarm Control on Constrained Edge Hardware

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Hardware](https://img.shields.io/badge/Hardware-Raspberry%20Pi%205%20(8GB)-red.svg)](https://www.raspberrypi.com/)
[![Simulation](https://img.shields.io/badge/Simulation-PyFlyt%20%7C%20PyBullet-green.svg)](https://github.com/jjshoots/PyFlyt)
[![Inference](https://img.shields.io/badge/Inference-llama.cpp%20%7C%20whisper.cpp-purple.svg)](https://github.com/ggerganov)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Zero-cloud, fully offline natural language command and control for autonomous drone swarms, running in real time on a Raspberry Pi 5.**

---

## Overview

Operating a drone swarm in remote, GPS-degraded, or communications-denied environments requires high-level tactile interaction without relying on centralized cloud infrastructure. **Voice-Swarm-Edge** provides a complete, mathematically grounded spoken-language interface designed to run entirely on edge hardware (Raspberry Pi 5 with 8 GB RAM, ARM Cortex-A76).

Natural spoken commands (e.g., *"Swarm, form a line with two-meter spacing at five meters altitude"*) are captured, endpointed, transcribed, and parsed into validated JSON flight primitives, which are executed in a simulated multi-UAV environment with real-time aerodynamics and collision avoidance.

---

## Key Highlights

- **100% Offline Edge Execution**: Full speech recognition, SLM intent extraction, and swarm flight physics execute locally on a single Raspberry Pi 5 with zero internet connection.
- **Dual-Path Latency Architecture**:
  - **Branch A (Reflex Path, $\le$ 150 ms)**: Direct wake-word spotting (`openWakeWord` ONNX model) dedicated exclusively to safety-critical commands (`swarm abort` and `swarm hold`). Preempts Branch B by sequence counter.
  - **Branch B (Language Path, $\le$ 2,500 ms p95)**: Silero VAD endpointing $\to$ `whisper.cpp` (`tiny.en`) $\to$ Fine-tuned Small Language Model (SLM) with strict GBNF grammar-constrained decoding.
- **3-Tier Verification & Safety Guardrails**:
  1. **Structural Enforcement (GBNF)**: Grammar-constrained logits masking guarantees 100% valid JSON syntax at generation time.
  2. **Semantic Grounding (Pydantic)**: Physical bounding, velocity clamping, and coordinate validation reject out-of-envelope commands without hallucination.
  3. **Operational Legality (Swarm FSM)**: Drone state transitions are guarded against illegal orders (e.g., flight maneuvers while disarmed).
- **Physics Simulation & Workstation HUD**: Real-time multi-UAV aerodynamics via PyFlyt and PyBullet with smooth tracking cameras and Pygame telemetry display.

---

## Architecture

```
                          ┌───────────────────────────┐
                          │   Audio Stream (16 kHz)   │
                          └─────────────┬─────────────┘
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
     ┌───────────────────────┐                     ┌───────────────────────┐
     │ Branch A: Reflex Path │                     │ Branch B: Speech Path │
     │  (openWakeWord / ONNX)│                     │  (Silero VAD Endpoint)│
     └───────────┬───────────┘                     └───────────┬───────────┘
                 │ ≤150 ms                                     │
                 │ ("swarm abort" / "swarm hold")              ▼
                 │                                 ┌───────────────────────┐
                 │                                 │ whisper.cpp (tiny.en) │
                 │                                 └───────────┬───────────┘
                 │                                             │ Transcript
                 │                                             ▼
                 │                                 ┌───────────────────────┐
                 │                                 │ Fine-Tuned SLM        │
                 │                                 │ + GBNF Grammar        │
                 │                                 └───────────┬───────────┘
                 │                                             │ Valid JSON
                 │                                             ▼
                 │                                 ┌───────────────────────┐
                 │                                 │ Pydantic Validator    │
                 │                                 └───────────┬───────────┘
                 │                                             │
                 │ Preempts Branch B                           │
                 ▼                                             ▼
     ┌─────────────────────────────────────────────────────────────────────┐
     │                     ZeroMQ Flight Command Bus                       │
     └──────────────────────────────────┬──────────────────────────────────┘
                                        ▼
     ┌─────────────────────────────────────────────────────────────────────┐
     │             Flight State Machine & Collision Separation             │
     └──────────────────────────────────┬──────────────────────────────────┘
                                        ▼
     ┌─────────────────────────────────────────────────────────────────────┐
     │       Swarm Simulation (PyFlyt Kinematic/Dynamic Backend)           │
     └─────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
├── demo/         # Real-time multi-drone workstation GUI, HUD, and PyBullet 3D visualizer
├── runtime/      # Edge audio capture, Silero VAD, whisper.cpp & llama.cpp runners, ZeroMQ bus
│   └── models/   # Reflex ONNX heads (swarm_hold.onnx, swarm_abort.onnx)
├── swarm/        # Swarm FSM, numpy controller, PyFlyt link, and collision avoidance
├── schema/       # Formal GBNF grammar (cmd.gbnf), Pydantic schemas, canonical validators
├── data/         # Speech datasets (S1-S3), noise partitions, wake manifests, dataset card
├── train/        # LoRA fine-tuning scripts, GGUF quantization, and model configs
├── gguf/         # GGUF model storage (qwen2.5-0.5b-instruct-Q4_K_M.gguf)
├── eval/         # Benchmarks for latency, acoustic robustness, and formation error
├── results/      # Raw benchmark CSVs and experimental verification metrics
├── docs/adr/     # Architectural Decision Records (ADRs)
└── scripts/      # System doctor, slide notes, and utility helpers
```

---

## 🛠️ Environment Doctor

Run the included environment diagnostic tool to verify all Python packages, C++ inference binaries, model weights, and audio hardware:

```bash
python scripts/doctor.py
```
This tool prints a full report and gives the exact commands to resolve any missing component.

---

## ⚡ Mode 1: Workstation Simulation & Quickstart (No Pi Required)

You can run the full multi-UAV physics simulation and test the language pipeline on any standard laptop or workstation:

### 1. Install Python Dependencies
```bash
git clone https://github.com/TayebKahia/voice-swarm-edge-.git
cd voice-swarm-edge-

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Launch 3D Simulation Workstation
```bash
# PyFlyt aerodynamic rigid-body simulation with tracking camera
python demo/workstation.py --backend pyflyt --pybullet-gui

# Or fast kinematic simulation (NumPy backend)
python demo/workstation.py --backend numpy
```

### 3. Replay Test (Speech-to-Flight without a Microphone)
To test speech transcription, SLM parsing, and drone flight using one of the 200 included benchmark audio recordings (`data/audio/s1/`):
```bash
# Terminal 1: Start workstation listener
python demo/workstation.py --backend pyflyt --pybullet-gui

# Terminal 2: Replay pre-recorded voice command to workstation
python runtime/main.py --bus-host 127.0.0.1 --source data/audio/s1/0001.wav
```

---

## 🍓 Mode 2: Complete Raspberry Pi 5 Edge Deployment

To deploy the physical, real-time audio pipeline on a Raspberry Pi 5:

### 1. Install System Prerequisites on Pi OS (Debian 12 Bookworm)
```bash
sudo apt-get update && sudo apt-get install -y \
    cmake \
    build-essential \
    libasound2-dev \
    portaudio19-dev \
    alsa-utils
```

### 2. Build C++ Inference Engines on the Pi

#### A. Build `whisper.cpp` (Speech-to-Text)
```bash
git clone https://github.com/ggerganov/whisper.cpp ~/whisper.cpp
cd ~/whisper.cpp
cmake -B build -DWHISPER_NATIVE=ON
cmake --build build --config Release -j4

# Download the deployed speech model (tiny.en ~75 MB)
bash models/download-ggml-model.sh tiny.en
```
*Add to `~/.bashrc`:*
```bash
export WHISPER_CPP_DIR=~/whisper.cpp
```

#### B. Build `llama.cpp` (SLM Server)
```bash
git clone https://github.com/ggerganov/llama.cpp ~/llama.cpp
cd ~/llama.cpp
cmake -B build -DLLAMA_NATIVE=ON
cmake --build build --config Release -j4
```
*Add to `~/.bashrc`:*
```bash
export LLAMA_SERVER_BIN=~/llama.cpp/build/bin/llama-server
```

### 3. Model Weights Provisioning
Place the quantized GGUF model in the `gguf/` directory:
- **Deployed Model**: `gguf/qwen2.5-0.5b-instruct-Q4_K_M.gguf` (~380 MB).
- *The Branch A reflex models (`runtime/models/wake/swarm_hold.onnx` and `swarm_abort.onnx`) are tracked directly in Git and are ready out of the box.*

### 4. Audio Input & Level Check
Connect a USB microphone (e.g., Boya BY-M1) to the Raspberry Pi:
1. Verify device detection:
   ```bash
   arecord -l
   ```
2. Unmute and set capture volume:
   ```bash
   alsamixer -c 1   # Press F4 for capture view, press 'M' to unmute, set gain
   ```
3. Test speech levels (speak from 10 cm):
   ```bash
   python runtime/main.py --level-check
   ```

### 5. Launch Distributed Pipeline (Workstation + Pi)
The system operates over a ZeroMQ socket on port `8766`:

1. **On your PC / Workstation** (runs the 3D PyBullet simulation):
   ```bash
   python demo/workstation.py --backend pyflyt --pybullet-gui --bind 0.0.0.0
   ```
2. **On the Raspberry Pi 5** (runs the voice pipeline):
   ```bash
   ./run_pipeline.sh --bus-host <WORKSTATION_IP>
   ```

To reset an emergency `ABORTED` state (non-vocal by design):
```bash
./run_pipeline.sh --reset
```

---

## Evaluation & Reproducibility

Every table and figure in the research is backed by frozen datasets and committed trial logs in `results/`. To reproduce the benchmark evaluations:

```bash
# Run the full automated evaluation suite
./run_all.sh
```

### Benchmark Summary

- **Exp-0 (Acoustic Sensitivity)**: Evaluates `whisper.cpp` across accent subsets using Mozilla Common Voice 17.0.
- **Exp-1 (SLM Comparison & Grammar Ablation)**: Measures exact-match JSON generation across 4 model families (`Qwen2.5-0.5B`, `SmolLM2-360M`, `Llama-3.2-1B`, `H2O-Danube3-500M`) with and without GBNF constrained decoding.
- **Exp-2 (Dual-Path Latency Profiling)**: Measures end-to-end timing on Raspberry Pi 5, confirming Branch A latency $\le$ 150 ms and Branch B within the 2,500 ms envelope.
- **Exp-3 (Acoustic Robustness)**: Evaluates command recognition under synthetic and real ambient noise across calibrated SNR levels (20 dB down to 5 dB).
- **Exp-4 (Formation Flight Validation)**: Validates swarm formation convergence and inter-agent collision separation clamps.

---

## Architectural Decision Records

Major architectural and engineering decisions are documented as ADRs in [`docs/adr/`](docs/adr/):
- `0001`: Physical envelope analogies and coordinate systems.
- `0002`: FSM-grounded command rejection and canonical serialization.
- `0003`: Spoken surface form conventions and phonetic variations.
- `0004`: Audio augmentation, noise partitioning, and acoustic splits.
- `0005`: Golden capture protocol, wake corpus generation, and annotation intervals.
- `0006`: Rebaselining abstention thresholds under real-world noise.
