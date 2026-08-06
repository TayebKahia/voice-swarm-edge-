#!/usr/bin/env bash
# =====================================================================
#  run_all.sh -- one-command reproduction (NFR-19)
#
#  From frozen data (dataset v1.0) to every table and figure in both
#  theses. Nothing here regenerates the dataset: the freeze at D5 is
#  the input, not an output.
#
#  Usage:
#      ./run_all.sh            run every stage
#      ./run_all.sh --list     show stages and whether each is ready
#      ./run_all.sh exp3       run one stage only
#
#  Every stage writes exactly one CSV into results/. Tables and figures
#  are generated from those CSVs and never edited by hand.
# =====================================================================

set -euo pipefail
cd "$(dirname "$0")"

# ---------------------------------------------------------------------
# Scripts this file drives, and the day each is due. A stage that is
# not implemented yet stops the run with its due date -- it never
# silently succeeds, because a partial run that exits 0 is how a thesis
# ends up with a stale number in it.
# ---------------------------------------------------------------------
declare -A DUE=(
  [schema/test_grammar.py]="D1"
  [schema/test_canon.py]="D1"
  [swarm/test_fsm.py]="D2"
  [data/check_leakage.py]="D3"
  [eval/test_template_parity.py]="D9"
  [eval/bench.py]="D11"
  [eval/mcnemar.py]="D14"
  [eval/plots.py]="D14"
)

require() {
  local f="$1"
  if [[ ! -f "$f" ]]; then
    echo "MISSING: $f  (due ${DUE[$f]:-see docs/PRD.tex} -- see the schedule in docs/PRD.tex)" >&2
    exit 1
  fi
}

banner() { echo; echo "=== $* ==============================================="; }

# ---------------------------------------------------------------------
# Stage 0 -- gates. Nothing downstream is trustworthy if these fail.
# ---------------------------------------------------------------------
stage_gates() {
  banner "gates"
  require schema/test_grammar.py
  require schema/test_canon.py
  require swarm/test_fsm.py
  require eval/test_template_parity.py
  require data/check_leakage.py

  pytest -q schema/ swarm/ eval/
  # Template-family leakage is a gate, not a report: a shared family
  # across the split boundary inflates every accuracy figure below.
  python data/check_leakage.py --strict
  # Chat-template mismatch between HF training and llama.cpp inference
  # produces no error message, only worse numbers.
  python eval/test_template_parity.py
}

# ---------------------------------------------------------------------
# Experiments. Each appends raw per-trial rows; none aggregates.
# ---------------------------------------------------------------------
stage_exp0() {  # speaker sensitivity at the acoustic model
  banner "Exp-0  Common Voice speaker baseline"
  require eval/bench.py
  python eval/bench.py --experiment 0 --split commonvoice --out results/exp0.csv
}

stage_exp1() {  # text -> JSON exact match, three models x two quantisations
  banner "Exp-1  parser accuracy (text input)"
  require eval/bench.py
  python eval/bench.py --experiment 1 --split test_synth --out results/exp1.csv
}

stage_exp2() {  # end-to-end latency, live microphone path
  banner "Exp-2  end-to-end latency"
  require eval/bench.py
  python eval/bench.py --experiment 2 --trials 200 --out results/exp2.csv
}

stage_exp3() {  # SNR sweep on golden-set audio
  banner "Exp-3  SNR sweep"
  require eval/bench.py
  python eval/bench.py --experiment 3 --split test_golden \
      --snr clean,20,15,10,5 --out results/exp3.csv
}

stage_exp4() {  # swarm convergence
  banner "Exp-4  swarm convergence"
  require eval/bench.py
  python eval/bench.py --experiment 4 --out results/exp4.csv
}

# ---------------------------------------------------------------------
# Statistics and figures. Read results/, write thesis/.
# ---------------------------------------------------------------------
stage_report() {
  banner "statistics and figures"
  require eval/mcnemar.py
  require eval/plots.py
  # `eval/stats.py` is a library, not a stage: it holds the conventions
  # (nearest-rank percentiles, the bootstrap unit, McNemar) that the
  # runners below import. Invoking it as a script -- which this stage
  # used to do -- runs no analysis and exits 0, which is the silent
  # partial run this file's header warns about.
  #
  # McNemar with Bonferroni alpha = 0.0167 within each family of three,
  # on the paired Surface-B predictions (RQ1).
  python eval/mcnemar.py
  # Figure 2, the accuracy/latency Pareto plot, from results/*.csv.
  python eval/plots.py
}

STAGES=(gates exp0 exp1 exp2 exp3 exp4 report)

if [[ "${1:-}" == "--list" ]]; then
  printf '%-10s %s\n' STAGE STATUS
  for s in "${STAGES[@]}"; do
    printf '%-10s %s\n' "$s" "$(declare -F "stage_$s" >/dev/null && echo defined)"
  done
  exit 0
fi

if [[ $# -gt 0 ]]; then
  for s in "$@"; do "stage_$s"; done
else
  for s in "${STAGES[@]}"; do "stage_$s"; done
fi

banner "done -- every CSV in results/, every figure in thesis/"
