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

# Download canonical PRD Table 22 models if not present
Q4_MODEL="${MODELS_DIR}/qwen2.5-0.5b-instruct-q4_k_m.gguf"
Q5_MODEL="${MODELS_DIR}/qwen2.5-0.5b-instruct-q5_k_m.gguf"

if [ ! -f "${Q4_MODEL}" ]; then
    echo "Downloading Qwen2.5-0.5B-Instruct Q4_K_M (~398 MB)..."
    curl -L -o "${Q4_MODEL}" "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf" || \
    wget -O "${Q4_MODEL}" "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
fi

if [ ! -f "${Q5_MODEL}" ]; then
    echo "Downloading Qwen2.5-0.5B-Instruct Q5_K_M (~440 MB)..."
    curl -L -o "${Q5_MODEL}" "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q5_k_m.gguf" || \
    wget -O "${Q5_MODEL}" "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q5_k_m.gguf"
fi

echo "--- Running llama-bench across available GGUF models ---"
# Test prompt: 64 tokens, generation: 32 tokens, threads: 4 per PRD Table 22
echo "Running benchmark (pp 64, tg 32, -t 4)..."
for m in "${Q4_MODEL}" "${Q5_MODEL}"; do
    if [ -f "$m" ]; then
        echo "Benchmarking $(basename "$m")..."
        "${BENCH_BIN}" -m "$m" -n 32 -p 64 -t 4 -r 5
        vcgencmd measure_temp || true
        vcgencmd get_throttled || true
    fi
done


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
