#!/usr/bin/env bash
# ==============================================================================
# Spike S1: llama.cpp Throughput & Thermals on Raspberry Pi 5
# To be executed on the Raspberry Pi 5 (ssh pi)
# ==============================================================================
set -euo pipefail

echo "=== Spike S1: llama.cpp Throughput & Thermals on Pi 5 ==="
echo "Date: $(date -Iseconds)"
echo "Hostname: $(hostname)"
uname -a

# Ensure build directory exists
LLAMA_DIR="${HOME}/llama.cpp"
BENCH_BIN="${LLAMA_DIR}/build/bin/llama-bench"

if [ ! -x "${BENCH_BIN}" ]; then
    echo "llama-bench binary not found at ${BENCH_BIN}."
    echo "Attempting to build llama.cpp..."
    if [ ! -d "${LLAMA_DIR}" ]; then
        git clone https://github.com/ggerganov/llama.cpp "${LLAMA_DIR}"
    fi
    mkdir -p "${LLAMA_DIR}/build"
    cmake -B "${LLAMA_DIR}/build" -S "${LLAMA_DIR}" -DGGML_NATIVE=ON -DGGML_FAST=ON
    cmake --build "${LLAMA_DIR}/build" --config Release -j$(nproc) --target llama-bench
fi

echo "llama.cpp commit: $(cd "${LLAMA_DIR}" && git rev-parse HEAD)"

# System baseline
echo "--- Baseline System Status ---"
vcgencmd measure_temp || true
vcgencmd get_throttled || true
free -h

MODELS_DIR="${HOME}/models"
mkdir -p "${MODELS_DIR}"

echo "--- Running llama-bench across available GGUF models ---"
# Test prompt: 64 tokens, generation: 32 tokens, threads: 4
echo "Running benchmark (pp 64, tg 32, -t 4)..."
if ls "${MODELS_DIR}"/*.gguf 1>/dev/null 2>&1; then
    for m in "${MODELS_DIR}"/*.gguf; do
        echo "Benchmarking $m..."
        "${BENCH_BIN}" -m "$m" -n 32 -p 64 -t 4 -r 5
        vcgencmd measure_temp || true
        vcgencmd get_throttled || true
    done
else
    echo "No GGUF models found in ${MODELS_DIR}. Run synthetic benchmark mode if supported:"
    "${BENCH_BIN}" -h || true
fi

echo "--- 10-Minute Thermal Soak ---"
echo "Starting 10-minute thermal soak monitoring..."
for i in {1..20}; do
    sleep 30
    echo -n "T+$(($i * 30))s: "
    vcgencmd measure_temp || true
    vcgencmd get_throttled || true
done

echo "--- Final System Status ---"
free -h
vcgencmd measure_temp || true
vcgencmd get_throttled || true
echo "Spike S1 completed."
