#!/usr/bin/env bash
# ==============================================================================
# Spike S2: whisper.cpp Timing on Raspberry Pi 5
# To be executed on the Raspberry Pi 5 (ssh pi)
# Evaluates tiny.en Q5 on a 3-second utterance over 20 runs with -t 3
# ==============================================================================
set -euo pipefail

echo "=== Spike S2: whisper.cpp Timing Benchmark on Pi 5 ==="
echo "Date: $(date -Iseconds)"

WHISPER_DIR="${HOME}/whisper.cpp"
WHISPER_BIN="${WHISPER_DIR}/build/bin/whisper-cli"
# Fallback to legacy path if build/bin is not used
if [ ! -x "${WHISPER_BIN}" ] && [ -x "${WHISPER_DIR}/main" ]; then
    WHISPER_BIN="${WHISPER_DIR}/main"
fi

if [ ! -x "${WHISPER_BIN}" ]; then
    echo "whisper.cpp binary not found. Building whisper.cpp..."
    if [ ! -d "${WHISPER_DIR}" ]; then
        git clone https://github.com/ggerganov/whisper.cpp "${WHISPER_DIR}"
    fi
    mkdir -p "${WHISPER_DIR}/build"
    cmake -B "${WHISPER_DIR}/build" -S "${WHISPER_DIR}" -DWHISPER_NATIVE=ON
    cmake --build "${WHISPER_DIR}/build" --config Release -j$(nproc)
    WHISPER_BIN="${WHISPER_DIR}/build/bin/whisper-cli"
fi

echo "whisper.cpp commit: $(cd "${WHISPER_DIR}" && git rev-parse HEAD)"

# Download tiny.en Q5 model if not present
MODEL_PATH="${WHISPER_DIR}/models/ggml-tiny.en-q5_1.bin"
if [ ! -f "${MODEL_PATH}" ]; then
    echo "Downloading ggml-tiny.en-q5_1.bin..."
    bash "${WHISPER_DIR}/models/download-ggml-model.sh" tiny.en-q5_1 || \
    bash "${WHISPER_DIR}/models/download-ggml-model.sh" tiny.en
    if [ ! -f "${MODEL_PATH}" ]; then
        MODEL_PATH="${WHISPER_DIR}/models/ggml-tiny.en.bin"
    fi
fi

# Ensure test audio (3s 16kHz WAV)
AUDIO_FILE="/tmp/test_3s_16k.wav"
if [ ! -f "${AUDIO_FILE}" ]; then
    echo "Generating 3s test audio..."
    # Generate 3s tone or record if available
    ffmpeg -y -f lavfi -i "sine=frequency=440:duration=3" -ar 16000 -ac 1 "${AUDIO_FILE}" 2>/dev/null || \
    arecord -d 3 -f S16_LE -r 16000 -c 1 "${AUDIO_FILE}"
fi

echo "--- Running 20 Benchmark Repetitions (-t 3) ---"
LOG_FILE="/tmp/whisper_bench_runs.txt"
rm -f "${LOG_FILE}"

for i in $(seq 1 20); do
    echo -n "Run $i/20... "
    # Run whisper and capture timing output
    OUT=$("${WHISPER_BIN}" -m "${MODEL_PATH}" -f "${AUDIO_FILE}" -t 3 -nt 2>&1)
    # Extract total time (look for whisper_print_timings:     total time =  xxxx.xx ms)
    TIME_MS=$(echo "${OUT}" | grep -o "total time = *[0-9.]* ms" | awk '{print $4}' | tail -n 1 || echo "")
    if [ -z "${TIME_MS}" ]; then
        # fallback parsing
        TIME_MS=$(echo "${OUT}" | grep -i "total time" | tail -n 1)
    fi
    echo "${TIME_MS}" | tee -a "${LOG_FILE}"
done

echo "=== Benchmark Complete ==="
echo "Raw timings saved to ${LOG_FILE}"
python3 -c "
import numpy as np
try:
    with open('${LOG_FILE}') as f:
        times = [float(l.strip().replace('ms','').split()[-1]) for l in f if l.strip()]
    if times:
        print(f'Count: {len(times)}')
        print(f'Mean:  {np.mean(times):.2f} ms')
        print(f'p50:   {np.percentile(times, 50):.2f} ms (Budget: 1200 ms)')
        print(f'p95:   {np.percentile(times, 95):.2f} ms')
        print(f'Min:   {np.min(times):.2f} ms')
        print(f'Max:   {np.max(times):.2f} ms')
        if np.percentile(times, 50) <= 1200:
            print('-> PASS: p50 meets <= 1200 ms budget.')
        else:
            print('-> WARNING: p50 exceeds 1200 ms budget.')
except Exception as e:
    print('Analysis error:', e)
"
