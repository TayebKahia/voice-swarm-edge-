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
├── swarm/        # Swarm FSM, numpy controller, PyFlyt link, and collision avoidance
├── schema/       # Formal GBNF grammar (cmd.gbnf), Pydantic schemas, canonical validators
├── data/         # Speech datasets (S1-S3), noise partitions, wake manifests, dataset card
├── train/        # LoRA fine-tuning scripts, GGUF quantization, and model configs
├── eval/         # Benchmarks for latency, acoustic robustness, and formation error
├── results/      # Raw benchmark CSVs and experimental verification metrics
├── docs/adr/     # Architectural Decision Records (ADRs)
├── scripts/      # Presentation slide notes and utility helpers
└── spikes/       # Hardware bring-up and profiling spikes on Raspberry Pi 5
```

---

## Quickstart

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/TayebKahia/voice-swarm-edge-.git
cd voice-swarm-edge-

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

> **Note**: `whisper.cpp` and `llama.cpp` are built natively on the target host (or Raspberry Pi 5) for optimal ARM NEON acceleration. Set the binary path via `export LLAMA_SERVER_BIN=/path/to/llama-server` or place them in your `PATH`.

### 2. Launch 3D Simulation Workstation

Run the workstation with PyBullet 3D visualization and Pygame telemetry HUD:

```bash
# PyFlyt aerodynamic backend with camera tracking
python demo/workstation.py --backend pyflyt --pybullet-gui

# Fast kinematic NumPy backend (headless or GUI)
python demo/workstation.py --backend numpy
```

### 3. Run Live Audio Pipeline

Launch the complete end-to-end edge pipeline on the Raspberry Pi (or host workstation):

```bash
# Default deployment model (Qwen2.5-0.5B-Instruct Q4_K_M)
./run_pipeline.sh

# Or specify a custom quantized model
./run_pipeline.sh --model gguf/smollm2-360m-instruct-Q4_K_M.gguf

# Reset from an emergency ABORTED state
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
