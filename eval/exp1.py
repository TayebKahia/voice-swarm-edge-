#!/usr/bin/env python3
"""Exp-1 --- the Pi-side half of Table 17 and the model-selection constraints.

Accuracy (EM, intent/slot F1, safe-failure, schema validity) is hardware-independent
and already measured on the workstation by `surface_b.py` (§ STATE.md, "the decision
that unlocks the schedule"): greedy decode under a fixed grammar is deterministic, so
the Pi would return the same strings after a much longer wait. This script measures
only what genuinely needs the hardware --- p50/p95/p99 latency, peak RSS, steady-state
SoC temperature and throttle flags --- for the three **Q4_K_M** configurations kept by
the Sat-19 triage (STATE.md; 60 timed runs, not the PRD's 200, wider CIs reported).

Also closes two of the three inputs the model-selection rule (prd.md line 633) needs:
NFR-9a (peak RSS <= 2.5 GB) and Table 6's SLM-decode budget (p95 <= 1,100 ms). The
third, NFR-2 end-to-end p95, is Exp-2 and is not touched here.

Protocol (prd.md Table 15's Exp-1 row, prd.md Table 7):
  - cores pinned `taskset -c 1-3`, three threads --- Table 7's inference allocation.
    Core 0 (capture/wake/VAD) is not exercised: Exp-1's input is reference text.
  - the governor must already be `performance`. Spike S1's numbers were measured
    under an `ondemand` governor thermally capped to 1.5 GHz mid-run; Table 7's
    steady-state clock assumption does not hold there, so this script refuses to
    start rather than silently repeat that confound.
  - swap disabled, one model resident at a time, page cache dropped before each
    config loads --- so one config's file-cache warmth can't flatter the next.
  - a ten-minute warm-up per config before anything is scored as a trial, so
    temperature and clock have reached steady state (S1 measured a cold->hot
    ramp; a p95 taken during that ramp is not the number the deployed system
    will show in flight). Warm-up requests are still real trials in the CSV,
    just tagged `<artefact>-warmup` so `bench.aggregate` keeps them out of the
    scored percentiles without any row being discarded.
  - `cache_prompt=true`. This is the one deliberate divergence from
    `surface_b.py`, which disables the cache for single-slot determinism across
    an accuracy sweep. Table 6's prefill budget ("cached prefix, ~15 tokens") is
    a claim about the deployed runtime, where the system-prompt prefix is
    resident in the KV cache across requests --- measuring prefill with the
    cache off would answer a different, harder question than the one Table 6
    asks.

Usage:
    python eval/exp1.py                        # all three Q4_K_M artefacts
    python eval/exp1.py --models qwen2.5-0.5b-instruct-Q4_K_M
    python eval/exp1.py --warmup-seconds 30 --trials 5   # smoke test, not for the record
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):  # `python eval/exp1.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.bench import Bench, aggregate, probe_platform, read_trials

REPO = Path(__file__).resolve().parent.parent
GGUF_DIR = REPO / "gguf"
GRAMMAR_PATH = REPO / "schema" / "cmd.gbnf"
AUDIT = REPO / "eval" / "fixed_audit_prompts.json"
GOLDEN = REPO / "data" / "test_golden.jsonl"
LLAMA_SERVER = Path.home() / "llama.cpp" / "build" / "bin" / "llama-server"

PORT = 8913
CONTEXT = 1024
THREADS = 3          # Table 7: cores 1-3 share `llama.cpp -t 3`
CORES = "1-3"
WARMUP_SECONDS = 600  # Table 15: "ten-minute warm-up"
N_TRIALS = 60         # STATE.md triage: 60, not the PRD's 200
#: Fixed so the golden-set sample is reproducible from a clean clone (ADR-0004
#: convention: no `hash()`-derived seeds). Distinct from eval/stats.py's
#: BOOTSTRAP_SEED --- this seed draws items, it does not resample statistics.
SAMPLE_SEED = 20_260_920
DECODE_BUDGET_MS = 1100.0   # Table 6, SLM decode p95
PREFILL_BUDGET_MS = 250.0   # Table 6, SLM prefill p95
RSS_BUDGET_MB = 2560.0      # NFR-9a: 2.5 GB


def _post(path: str, payload: dict, timeout: float = 120.0) -> dict:
    request = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def _wait_for_server(process: subprocess.Popen, timeout: float = 180.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"llama-server exited early ({process.returncode})")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2) as r:
                if json.loads(r.read()).get("status") == "ok":
                    return
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            time.sleep(1.0)
    raise RuntimeError("llama-server did not become healthy")


def _require_pi() -> dict[str, str]:
    info = probe_platform()
    if info["is_pi"] != "true":
        raise SystemExit(f"refusing to run Exp-1 off the Pi: probe_platform() = {info}")
    return info


def _require_performance_governor() -> None:
    paths = sorted(Path("/sys/devices/system/cpu").glob("cpu[0-9]*/cpufreq/scaling_governor"))
    if not paths:
        raise SystemExit("no cpufreq scaling_governor files found -- cannot verify the governor")
    seen = {p: p.read_text().strip() for p in paths}
    bad = {str(p): g for p, g in seen.items() if g != "performance"}
    if bad:
        raise SystemExit(
            "refusing to run: governor must be 'performance' on every core (Table 7 assumes "
            f"the steady-state clock, spike S1's numbers were confounded by 'ondemand' "
            f"throttling mid-run). Found: {bad}. Fix with:\n"
            "  sudo bash -c 'echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'"
        )


def _drop_caches() -> None:
    subprocess.run(["sync"], check=False)
    subprocess.run(["sudo", "tee", "/proc/sys/vm/drop_caches"],
                    input="3\n", text=True, capture_output=True, check=False)


#: Not on PATH under a plain `ssh host cmd` (no login shell); Debian keeps both here.
_SWAPON = "/sbin/swapon"
_SWAPOFF = "/sbin/swapoff"


def _swap_off() -> list[str]:
    """Best-effort, per Table 15 ('swap disabled'). Returns the swap device(s) turned off.

    Raspberry Pi OS manages its swapfile via `dphys-swapfile`, not an `/etc/fstab`
    entry, so `swapon -a` (which only re-activates fstab entries) silently fails to
    restore it -- caught the hard way once already. The device paths are recorded
    explicitly here and swapped back on by path, not by `-a`.
    """
    devices = subprocess.run([_SWAPON, "--show=NAME", "--noheadings"],
                              capture_output=True, text=True, check=False).stdout.split()
    if not devices:
        return []
    subprocess.run(["sudo", _SWAPOFF, "-a"], check=False)
    return devices


def _swap_on(devices: list[str]) -> None:
    for device in devices:
        subprocess.run(["sudo", _SWAPON, device], check=False)


def _load_sample(n: int, seed: int) -> list[dict]:
    rows = [json.loads(l) for l in GOLDEN.read_text().splitlines() if l.strip()]
    return random.Random(seed).sample(rows, n)


def _predict_timed(system_prompt: str, text: str, grammar: str) -> tuple[str, dict]:
    """One request through the deployed decode path; returns (content, response)."""
    templated = _post("/apply-template", {
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": text}],
    })["prompt"]
    tokens = _post("/tokenize", {"content": templated, "add_special": False})["tokens"]
    response = _post("/completion", {
        "prompt": tokens, "temperature": 0.0, "n_predict": 96,
        "cache_prompt": True, "grammar": grammar,
    })
    return response["content"].strip(), response


def run_config(gguf: Path, bench: Bench, system_prompt: str, grammar: str,
                sample: Sequence[dict], warmup_seconds: int, n_trials: int) -> None:
    tag = gguf.stem
    process = subprocess.Popen(
        ["taskset", "-c", CORES, str(LLAMA_SERVER), "-m", str(gguf), "--port", str(PORT),
         "-t", str(THREADS), "-c", str(CONTEXT), "--parallel", "1", "--log-disable"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        _wait_for_server(process)

        started = time.monotonic()
        warmup_n = 0
        while time.monotonic() - started < warmup_seconds:
            item = sample[warmup_n % len(sample)]
            try:
                with bench.trial(experiment=1, config=f"{tag}-warmup", item_id=item["id"],
                                  index=warmup_n, pid=process.pid) as trial:
                    _, response = _predict_timed(system_prompt, item["transcript"], grammar)
                    trial.stages_ms["slm_prefill"] = response["timings"]["prompt_ms"]
                    trial.stages_ms["slm_decode"] = response["timings"]["predicted_ms"]
                    trial.tokens_predicted = response["tokens_predicted"]
                    trial.tokens_evaluated = response["tokens_evaluated"]
            except Exception as exc:  # noqa: BLE001 -- row already recorded, keep warming up
                print(f"  {tag}: warm-up request {warmup_n} failed: {exc}")
            warmup_n += 1
        elapsed = time.monotonic() - started
        print(f"  {tag}: warm-up done -- {warmup_n} requests in {elapsed:.0f}s")

        for index, item in enumerate(sample[:n_trials]):
            try:
                with bench.trial(experiment=1, config=tag, item_id=item["id"],
                                  index=index, pid=process.pid) as trial:
                    _, response = _predict_timed(system_prompt, item["transcript"], grammar)
                    trial.stages_ms["slm_prefill"] = response["timings"]["prompt_ms"]
                    trial.stages_ms["slm_decode"] = response["timings"]["predicted_ms"]
                    trial.tokens_predicted = response["tokens_predicted"]
                    trial.tokens_evaluated = response["tokens_evaluated"]
            except Exception as exc:  # noqa: BLE001 -- the row records the failure; keep going
                print(f"  {tag}: trial {index} failed: {exc}")
                continue
            if (index + 1) % 20 == 0 or index + 1 == n_trials:
                print(f"  {tag}: {index + 1}/{n_trials} timed trials")
    finally:
        process.terminate()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--models", nargs="+", help="artefact stems; default all three Q4_K_M")
    parser.add_argument("--warmup-seconds", type=int, default=WARMUP_SECONDS)
    parser.add_argument("--trials", type=int, default=N_TRIALS)
    parser.add_argument("--out", type=Path, default=REPO / "results" / "exp1.csv")
    parser.add_argument("--append", action="store_true", help="resume onto an existing CSV")
    parser.add_argument("--skip-checks", action="store_true",
                        help="skip the is-Pi / governor guards (smoke-testing off the Pi only)")
    args = parser.parse_args(argv)

    if not args.skip_checks:
        info = _require_pi()
        _require_performance_governor()
    else:
        info = probe_platform()

    if not LLAMA_SERVER.is_file():
        raise SystemExit(f"llama-server not built at {LLAMA_SERVER}")

    artefacts = sorted(p for p in GGUF_DIR.glob("*-Q4_K_M.gguf"))
    if args.models:
        wanted = set(args.models)
        artefacts = [p for p in artefacts if p.stem in wanted]
    if not artefacts:
        raise SystemExit(f"no Q4_K_M artefacts in {GGUF_DIR}")

    sample = _load_sample(args.trials, SAMPLE_SEED)
    grammar = GRAMMAR_PATH.read_text()
    system_prompt = json.loads(AUDIT.read_text())["system_prompt"]

    print(f"host      : {info}")
    print(f"artefacts : {[p.stem for p in artefacts]}")
    print(f"trials    : {args.trials} per config, {args.warmup_seconds}s warm-up, "
          f"golden sample seed={SAMPLE_SEED}")

    swapped_off = _swap_off() if not args.skip_checks else []
    try:
        with Bench(args.out, append=args.append) as bench:
            for gguf in artefacts:
                if not args.skip_checks:
                    _drop_caches()
                run_config(gguf, bench, system_prompt, grammar, sample,
                           args.warmup_seconds, args.trials)
    finally:
        if swapped_off:
            _swap_on(swapped_off)

    rows = [r for r in read_trials(args.out) if not r["config"].endswith("-warmup")]
    summaries = aggregate(rows)
    print(f"\nwrote {args.out} -- {len(read_trials(args.out))} rows "
          f"({len(rows)} scored, rest warm-up)\n")
    for summary in summaries:
        prefill_p95 = summary.get("slm_prefill_p95", "")
        decode_p95 = summary.get("slm_decode_p95", "")
        rss = summary.get("peak_rss_mb", "")
        temp = summary.get("max_temperature_c", "")
        decode_verdict = "MEETS" if decode_p95 != "" and decode_p95 <= DECODE_BUDGET_MS else "MISS"
        rss_verdict = "MEETS" if rss != "" and rss <= RSS_BUDGET_MB else "MISS"
        print(f"  {summary['config']:32s} n={summary['n_latency']:3d} "
              f"prefill p50/p95={summary.get('slm_prefill_p50','')}/{prefill_p95} ms  "
              f"decode p50/p95={summary.get('slm_decode_p50','')}/{decode_p95} ms "
              f"[{decode_verdict} vs {DECODE_BUDGET_MS:.0f}]  "
              f"tok/s={summary.get('tokens_per_second','')}  "
              f"rss={rss} MB [{rss_verdict} vs {RSS_BUDGET_MB:.0f}]  "
              f"temp_max={temp}C  throttled={summary['throttled_fraction']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
