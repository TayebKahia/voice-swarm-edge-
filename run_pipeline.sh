#!/usr/bin/env bash
# =====================================================================
#  run_pipeline.sh -- the live voice pipeline on the Raspberry Pi 5
#
#  Usage:
#      ./run_pipeline.sh                 start the pipeline
#      ./run_pipeline.sh --reset         clear the ABORTED state
#      ./run_pipeline.sh --model NAME    override the selected config
#      ./run_pipeline.sh --dry-run       show the core plan and exit
#
#  --reset exists because recovery from ABORTED is explicit, manual,
#  and NON-VOCAL by design. There is no spoken command that undoes an
#  abort: "resume" is barred from Branch A precisely so that a false
#  accept can never restart a swarm the operator just stopped.
#
#  Core plan (verify with: taskset -cp <pid>, then htop):
#      core 0    ALSA capture, ring buffer, Silero VAD, openWakeWord
#      cores 1-3 llama.cpp -t 3 and whisper.cpp -t 3
#  The two heavy stages are sequential by construction, so they never
#  contend for the same three cores.
# =====================================================================

set -euo pipefail
cd "$(dirname "$0")"

STATE_FILE="runtime/.state"
ENTRY="runtime/main.py"
MODEL="${PFE_MODEL:-}"
DRY_RUN=0
EXTRA_ARGS=()

# ---------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --reset)
      if [[ -f "$STATE_FILE" ]]; then
        echo "state was: $(cat "$STATE_FILE")"
        rm -f "$STATE_FILE"
        echo "state cleared -- swarm returns to LANDED, motors off."
      else
        echo "no state file; nothing to reset."
      fi
      exit 0
      ;;
    --model)    MODEL="${2:?--model needs a value}"; shift 2 ;;
    --bus-host) EXTRA_ARGS+=("--bus-host" "${2:?--bus-host needs a value}"); shift 2 ;;
    --dry-run)  DRY_RUN=1; shift ;;
    -h|--help)  sed -n '2,30p' "$0"; exit 0 ;;
    *)          EXTRA_ARGS+=("$1"); shift ;;
  esac
done

# ---------------------------------------------------------------------
# Pre-flight. Each check below has caused a wasted session at least
# once in projects of this shape; none of them is theoretical.
# ---------------------------------------------------------------------
if [[ ! -f "$ENTRY" ]]; then
  echo "MISSING: $ENTRY  (due D17 -- see the schedule in docs/PRD.tex)" >&2
  exit 1
fi

# A capture device must exist. If arecord -l lists no card, the mic is
# unplugged or the capture channel is muted -- open alsamixer -c 1,
# press F4 for the capture view, and unmute with M before concluding
# anything about the hardware.
if command -v arecord >/dev/null 2>&1; then
  if ! arecord -l 2>/dev/null | grep -q '^card'; then
    echo "no ALSA capture device. Check the cable, then: alsamixer -c 1 (F4, M)" >&2
    exit 1
  fi
fi

# An ABORTED swarm must not be silently restarted.
if [[ -f "$STATE_FILE" ]] && grep -q ABORTED "$STATE_FILE"; then
  echo "swarm is ABORTED. Recovery is manual: ./run_pipeline.sh --reset" >&2
  exit 1
fi

# Default to the deployed SLM model (Exp-1 / Exp-2 / Table 12) if none specified
if [[ -z "$MODEL" ]]; then
  if [[ -f "gguf/qwen2.5-0.5b-instruct-Q4_K_M.gguf" ]]; then
    MODEL="qwen2.5-0.5b-instruct-Q4_K_M.gguf"
  else
    echo "no model selected. Pass --model or set PFE_MODEL." >&2
    echo "The deployed configuration is fixed by Exp-1 and Exp-2 and recorded in docs/PRD.tex." >&2
    exit 1
  fi
fi

MODEL_PATH="$MODEL"
if [[ ! -f "$MODEL_PATH" && -f "gguf/$MODEL" ]]; then
  MODEL_PATH="gguf/$MODEL"
fi

if [[ ! -f "$MODEL_PATH" ]]; then
  echo "MISSING model file: $MODEL_PATH" >&2
  exit 1
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "model      : $MODEL_PATH"
  echo "core 0     : capture, ring buffer, Silero VAD, openWakeWord"
  echo "cores 1-3  : whisper.cpp -t 3 then llama.cpp -t 3 (sequential)"
  command -v vcgencmd >/dev/null 2>&1 && vcgencmd measure_temp || true
  exit 0
fi

# ---------------------------------------------------------------------
# Launch. Branch A is pinned to core 0 so a busy decode can never
# delay the reflex path; it preempts Branch B by sequence number.
# ---------------------------------------------------------------------
PYTHON_BIN="$(command -v python3 || command -v python)"
echo "starting pipeline with $MODEL_PATH using $PYTHON_BIN -- Ctrl-C to stop"
exec taskset -c 0-3 "$PYTHON_BIN" "$ENTRY" --model "$MODEL_PATH" --state "$STATE_FILE" "${EXTRA_ARGS[@]}"
