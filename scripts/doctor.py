#!/usr/bin/env python3
"""doctor.py -- Diagnostic pre-flight checker for Voice-Swarm-Edge.

Verifies system dependencies, Python packages, C++ inference binaries,
model weights, and audio hardware for both Workstation and Edge deployment.

Usage:
    python scripts/doctor.py
"""

from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ANSI color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"  {GREEN}✔ [PASS]{RESET} {msg}")


def warn(msg: str, hint: str | None = None) -> None:
    print(f"  {YELLOW}⚠ [WARN]{RESET} {msg}")
    if hint:
        print(f"         {BLUE}→ Hint:{RESET} {hint}")


def fail(msg: str, remedy: str | None = None) -> None:
    print(f"  {RED}✖ [FAIL]{RESET} {msg}")
    if remedy:
        print(f"         {BLUE}→ Fix:{RESET} {remedy}")


def section(title: str) -> None:
    print(f"\n{BOLD}{title}{RESET}")
    print("-" * 60)


def check_python_dependencies() -> tuple[int, int]:
    section("1. Python Environment & Dependencies")
    failures = 0
    warnings = 0

    py_ver = sys.version_info
    if py_ver >= (3, 10):
        ok(f"Python {py_ver.major}.{py_ver.minor}.{py_ver.micro}")
    else:
        fail(f"Python {py_ver.major}.{py_ver.minor}.{py_ver.micro} (Python 3.10+ recommended)")
        failures += 1

    packages = [
        ("pydantic", "Core schema validation"),
        ("numpy", "Vectorised maths & kinematics"),
        ("zmq", "ZeroMQ command bus (pyzmq)"),
        ("sounddevice", "Live ALSA microphone capture"),
        ("soundfile", "WAV audio encoding/decoding"),
        ("onnxruntime", "Wake-word reflex head inference"),
        ("openwakeword", "Reflex keyword spotting frontend"),
        ("pygame", "Workstation 2D GUI HUD"),
        ("pybullet", "3D multi-body physics visualizer"),
        ("PyFlyt", "Aerodynamic quadcopter simulation"),
    ]

    for pkg, purpose in packages:
        try:
            mod = importlib.import_module(pkg)
            version = getattr(mod, "__version__", "installed")
            ok(f"{pkg:14} ({version}) - {purpose}")
        except ImportError:
            if pkg in ("pygame", "pybullet", "PyFlyt"):
                warn(f"{pkg:14} missing - required for Workstation simulation", "pip install -r requirements.txt")
                warnings += 1
            else:
                fail(f"{pkg:14} missing - required for runtime pipeline", "pip install -r requirements.txt")
                failures += 1

    return failures, warnings


def check_inference_binaries() -> tuple[int, int]:
    section("2. C++ Inference Engines (llama.cpp & whisper.cpp)")
    failures = 0
    warnings = 0

    # 1. llama-server
    llama_env = os.environ.get("LLAMA_SERVER_BIN")
    llama_default = Path.home() / "llama.cpp" / "build" / "bin" / "llama-server"
    llama_bin = None

    if llama_env and Path(llama_env).is_file():
        llama_bin = Path(llama_env)
    elif llama_default.is_file():
        llama_bin = llama_default
    elif shutil.which("llama-server"):
        llama_bin = Path(shutil.which("llama-server"))

    if llama_bin:
        ok(f"llama-server: found at {llama_bin}")
    else:
        fail(
            "llama-server not found",
            "git clone https://github.com/ggerganov/llama.cpp ~/llama.cpp && "
            "cmake -B ~/llama.cpp/build -S ~/llama.cpp && cmake --build ~/llama.cpp/build -j4",
        )
        failures += 1

    # 2. whisper-cli
    whisper_dir = os.environ.get("WHISPER_CPP_DIR")
    candidate_dirs = [
        Path(whisper_dir) if whisper_dir else None,
        Path.home() / "whisper.cpp",
        Path("/opt/whisper.cpp"),
        Path("/usr/local/share/whisper.cpp"),
    ]
    whisper_bin = None
    model_bin = None

    for d in filter(None, candidate_dirs):
        if not d.is_dir():
            continue
        for sub in ("build/bin", "bin", "."):
            for name in ("whisper-cli", "main"):
                candidate = d / sub / name
                if candidate.is_file() and os.access(candidate, os.X_OK):
                    whisper_bin = candidate
                    break
            if whisper_bin:
                break
        candidate_model = d / "models" / "ggml-tiny.en.bin"
        if candidate_model.is_file():
            model_bin = candidate_model
        if whisper_bin and model_bin:
            break

    if not whisper_bin and shutil.which("whisper-cli"):
        whisper_bin = Path(shutil.which("whisper-cli"))

    if whisper_bin:
        ok(f"whisper-cli: found at {whisper_bin}")
    else:
        fail(
            "whisper-cli not found",
            "git clone https://github.com/ggerganov/whisper.cpp ~/whisper.cpp && "
            "cmake -B ~/whisper.cpp/build -S ~/whisper.cpp && cmake --build ~/whisper.cpp/build -j4",
        )
        failures += 1

    if model_bin:
        ok(f"whisper model: found {model_bin.name} ({model_bin.stat().st_size / 1e6:.1f} MB)")
    else:
        warn(
            "whisper ggml-tiny.en.bin model missing",
            "bash ~/whisper.cpp/models/download-ggml-model.sh tiny.en",
        )
        warnings += 1

    return failures, warnings


def check_models() -> tuple[int, int]:
    section("3. Pre-trained Weights & Models")
    failures = 0
    warnings = 0

    # 1. GGUF Models
    gguf_dir = REPO_ROOT / "gguf"
    default_model = gguf_dir / "qwen2.5-0.5b-instruct-Q4_K_M.gguf"
    gguf_files = list(gguf_dir.glob("*.gguf")) if gguf_dir.is_dir() else []

    if default_model.is_file():
        ok(f"Default SLM: {default_model.name} ({default_model.stat().st_size / 1e6:.1f} MB)")
    elif gguf_files:
        ok(f"Found {len(gguf_files)} GGUF models in gguf/ (default {default_model.name} not present)")
    else:
        fail(
            "No GGUF models found in gguf/",
            f"Place {default_model.name} into gguf/ (exported from training or download from releases)",
        )
        failures += 1

    # 2. Wake-word reflex heads
    wake_dir = REPO_ROOT / "runtime" / "models" / "wake"
    hold_head = wake_dir / "swarm_hold.onnx"
    abort_head = wake_dir / "swarm_abort.onnx"
    manifest = wake_dir / "wake_heads.json"

    if hold_head.is_file() and abort_head.is_file() and manifest.is_file():
        ok(f"Branch A Reflex heads: swarm_hold.onnx & swarm_abort.onnx present in {wake_dir.relative_to(REPO_ROOT)}")
    else:
        fail(
            "Branch A reflex ONNX models missing in runtime/models/wake/",
            "Ensure swarm_hold.onnx and swarm_abort.onnx are present in runtime/models/wake/",
        )
        failures += 1

    return failures, warnings


def check_audio_hardware() -> tuple[int, int]:
    section("4. Audio & Capture Devices (Raspberry Pi / Host)")
    failures = 0
    warnings = 0

    if shutil.which("arecord"):
        try:
            proc = subprocess.run(["arecord", "-l"], capture_output=True, text=True, timeout=5)
            cards = [line for line in proc.stdout.splitlines() if line.startswith("card ")]
            if cards:
                ok(f"ALSA capture devices found ({len(cards)} card(s)):")
                for c in cards:
                    print(f"        {c.strip()}")
            else:
                warn(
                    "No ALSA audio capture devices found via arecord -l",
                    "Plug in USB microphone or run with --source <audio.wav> replay mode",
                )
                warnings += 1
        except Exception:
            warn("Unable to enumerate ALSA cards")
            warnings += 1
    else:
        warn("arecord binary not installed", "sudo apt-get install alsa-utils")
        warnings += 1

    return failures, warnings


def main() -> int:
    print(f"\n{BOLD}============================================================{RESET}")
    print(f"{BOLD}   Voice-Swarm-Edge: System Diagnostic & Environment Doctor{RESET}")
    print(f"{BOLD}============================================================{RESET}")

    f1, w1 = check_python_dependencies()
    f2, w2 = check_inference_binaries()
    f3, w3 = check_models()
    f4, w4 = check_audio_hardware()

    total_failures = f1 + f2 + f3 + f4
    total_warnings = w1 + w2 + w3 + w4

    print(f"\n{BOLD}============================================================{RESET}")
    print(f"{BOLD}   Diagnostic Summary{RESET}")
    print(f"{BOLD}============================================================{RESET}")

    if total_failures == 0 and total_warnings == 0:
        print(f"\n{GREEN}{BOLD}🎉 ALL CHECKS PASSED!{RESET}")
        print("Your environment is completely ready to run both simulation and the live voice pipeline.")
        print(f"\nTo launch simulation workstation:")
        print(f"    {BLUE}python demo/workstation.py --backend pyflyt --pybullet-gui{RESET}")
        print(f"To launch live audio edge pipeline:")
        print(f"    {BLUE}./run_pipeline.sh{RESET}\n")
        return 0

    if total_failures == 0:
        print(f"\n{YELLOW}{BOLD}✔ WORKSTATION READY (with {total_warnings} warnings){RESET}")
        print("Simulation and offline evaluation can run. Review warnings above before physical Pi deployment.\n")
        return 0

    print(f"\n{RED}{BOLD}✖ {total_failures} FATAL REQUIREMENT(S) MISSING{RESET}")
    print("Address the [FAIL] items above using the suggested commands before running the live pipeline.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
