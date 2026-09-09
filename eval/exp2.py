#!/usr/bin/env python3
"""Exp-2 --- dual-path latency on the Pi (RQ2; prd.md Table 15 row 2, Tables 6 and 7).

Runs on the Pi. Every trial is WAV replay through `runtime/stream.py` in real time:
80 ms frames to Branch A's spotter and Branch B's endpointer on core 0, Branch B's
STT and SLM on cores 1-3. Replay rather than a live microphone is deliberate: the
idle and loaded conditions must hear *identical* audio, and every trial must be
reproducible from the repo. Live capture latency is A11's separate number.

Three phases, in this order (Sat-19 triage: >= 60 trials per branch, both Branch A
conditions kept, because NFR-1 means nothing without both):

  loaded   Branch A under active Branch B inference. A loader thread on cores 1-3
           runs the deployed decode path (`CommandParser.parse`, validate, publish)
           back to back on golden transcripts. Each trial replays one of the author's
           40 real keyword takes (two passes, 80 trials); its trigger pre-empts
           whatever decode is in flight, so the same trials give NFR-1 (loaded),
           NFR-17 (recovery) and FR-6 (the sequence rule). Preceded by a warm-up of
           the same load so the SoC is at thermal equilibrium.
  branch_b The 200 golden utterances, clean audio, through the whole of Branch B
           (NFR-2, NFR-3). Branch A listens too, as deployed. Predictions are saved
           in `eval/exp3.py`'s row format so A7b can diff them against A7a.
  idle     The same 80 keyword trials with Branch B resident and idle (NFR-1, idle).

**Anchors (prd.md Sec. 4.4, 4.7).** Branch A: from keyword *offset*, the capture
tool's own end-of-speech (`session_meta.json`: take length minus trailing silence),
to the bus publish, so frame quantisation and debounce are inside the figure; the
onset-anchored figure (lead silence) is reported beside it. Branch B: from T0, the
wall time of the last sample the VAD had consumed when it declared end of speech,
to the FSM having applied the command. The figure from the *true* end of speech adds
the VAD's own wait (Table 6 row 1); both are reported.

**What this does not measure.** The Wi-Fi hop to the workstation (prd 4.7: measured
once by UDP echo, reported separately) -- the bus here is loopback on the Pi. And the
ROC / operating point: the threshold (0.999) is fixed by `train/train_wake.py` on
hardware-independent scores and quoted from `results/wake_training.md`, never
re-selected here.

Usage (on the Pi, governor `performance`):
    python eval/exp2.py                     # all three phases, then analyse
    python eval/exp2.py --phases idle --passes 1 --limit 4 --warmup-seconds 0   # smoke
    python eval/exp2.py --analyse-only      # on the workstation, from the raw JSONL
"""

from __future__ import annotations

import argparse
import csv
import http.client
import json
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):  # `python eval/exp2.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from eval.stats import nearest_rank

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results"
RAW = RESULTS / "exp2_raw"
PREDS = RESULTS / "exp2_preds"
TAKES = REPO / "data" / "audio" / "wake_real_16k"
META = REPO / "data" / "audio" / "wake_real" / "session_meta.json"
PROMPTS = REPO / "data" / "wake_real_transcripts.txt"
PORT = 8916        # llama-server; clear of surface_b (8912), parser (8914), exp3 (8915)
BUS_PORT = 8766

PHASES = ("loaded", "branch_b", "idle")
PAD_S = 1.0        # silence either side of a take: train_wake.py's and wake_real.py's pad
GAP_S = 0.5        # between trials
FRONT = {0}        # Table 7
BACK = {1, 2, 3}

#: Table 6 target p95s, in ms, and the NFR each one serves.
BUDGETS = {
    "vad_wait": 500, "stt": 1200, "prefill": 250, "decode": 1100, "validate_fsm": 50,
    "llm": 1350,  # Table 6's "language-model stages combined" (cached-prefix allowance, as prefill's)
    "e2e_t0": 2500,
    "a_offset": 150, "a_onset": 850, "recovery": 300,
}


# --- platform checks (the Pi) -----------------------------------------------


def _read(path: str) -> str:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return ""


def soc_state() -> dict:
    """Temperature and the firmware throttle word; empty off a Pi."""
    out = {}
    for key, cmd in (("temp", "measure_temp"), ("throttled", "get_throttled")):
        try:
            text = subprocess.run(["vcgencmd", cmd], capture_output=True, text=True, timeout=5).stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        value = text.strip().split("=")[-1]
        out[key] = float(value.rstrip("'C")) if key == "temp" else value
    out["freq_khz"] = _read("/sys/devices/system/cpu/cpu1/cpufreq/scaling_cur_freq")
    return out


def task_affinity(pid: int) -> list[str]:
    """Every thread's allowed CPUs -- Table 7's `taskset` verification, per thread."""
    lists = set()
    for status in Path(f"/proc/{pid}/task").glob("*/status"):
        for line in status.read_text().splitlines():
            if line.startswith("Cpus_allowed_list"):
                lists.add(line.split(":")[1].strip())
    return sorted(lists)


# --- inputs -----------------------------------------------------------------


def keyword_trials(passes: int, limit: int | None) -> list[dict]:
    """The author's 40 real takes with their anchors, `passes` times over."""
    import soundfile as sf

    meta = json.loads(META.read_text())["takes"]
    takes = []
    for line in PROMPTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        take, phrase = line.split("\t")
        m = meta[take]
        audio, rate = sf.read(str(TAKES / f"{take}.wav"), dtype="int16")
        assert rate == 16_000 and audio.ndim == 1, take
        takes.append({"take": take, "class": phrase.strip().replace(" ", "_"), "audio": audio,
                      "kw_onset_s": PAD_S + m["lead_seconds"],
                      "kw_offset_s": PAD_S + m["seconds"] - m["tail_seconds"]})
    takes = takes[:limit]
    return [dict(t, pass_=p) for p in range(passes) for t in takes]


# --- the harness ------------------------------------------------------------


class Subscriber:
    """The consumer side of the bus: Dispatcher + FSM, timing every applied message."""

    def __init__(self, bus) -> None:
        from runtime.pipeline import Dispatcher
        from swarm.fsm import FlightStateMachine

        self.bus = bus
        self.dispatcher = Dispatcher(FlightStateMachine())
        self.applied: dict[int, dict] = {}
        self.highest_a = -1
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="subscriber", daemon=True)
        self._thread.start()

    def fly(self) -> None:
        """A fresh airborne FSM per trial, so every command meets Table 9's FLYING row."""
        from swarm.fsm import FlightStateMachine

        fsm = FlightStateMachine()
        fsm.handle_command({"intent": "takeoff"})
        fsm.on_altitude_reached()
        self.dispatcher.fsm = fsm

    def _run(self) -> None:
        while not self._stop.is_set():
            msg = self.bus.recv(timeout=0.2)
            if msg is None:
                continue
            stale = msg.branch == "B" and msg.seq < self.highest_a
            if msg.branch == "A":
                self.highest_a = max(self.highest_a, msg.seq)
            result = self.dispatcher.apply(msg)
            self.applied[msg.seq] = {"branch": msg.branch, "t_applied": time.monotonic(),
                                     "stale_discarded": stale, "applied": result is not None}

    def wait_for(self, seq: int, timeout: float = 2.0) -> dict | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if seq in self.applied:
                return self.applied[seq]
            time.sleep(0.002)
        return None

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)


def server_idle(port: int, timeout: float = 10.0) -> float | None:
    """monotonic time at which llama-server's one slot is no longer processing."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        try:
            conn.request("GET", "/slots")
            slots = json.loads(conn.getresponse().read())
            if not any(s.get("is_processing") for s in slots):
                return time.monotonic()
        except (OSError, ValueError):
            pass
        finally:
            conn.close()
        time.sleep(0.005)
    return None


class Loader:
    """Branch B decoding back to back on cores 1-3: the 'loaded' condition's load.

    It is the deployed decode path, not a synthetic burner: reserve a sequence
    number, `parse`, validate, publish -- so a decode that finishes despite a
    Branch A trigger reaches the Dispatcher with its older number, and FR-6's
    sequence rule is exercised by the same trials that measure NFR-1.
    """

    def __init__(self, runtime, transcripts: Sequence[str]) -> None:
        self.runtime = runtime
        self.transcripts = list(transcripts)
        self.requests: list[dict] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="loader", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _run(self) -> None:
        from runtime.parser import ParseAborted
        from runtime.stream import pin
        from schema.validate import validate

        pin(BACK)
        self.affinity = sorted(__import__("os").sched_getaffinity(0))
        k = 0
        while not self._stop.is_set():
            transcript = self.transcripts[k % len(self.transcripts)]
            k += 1
            seq = self.runtime.bus.next_seq()
            record = {"seq": seq, "t_req": time.monotonic()}
            self.requests.append(record)      # visible to in_flight() while it runs
            try:
                result = self.runtime.parser.parse(transcript)
            except ParseAborted:
                record["t_end"] = time.monotonic()
                record["aborted"] = True
                record["t_idle"] = server_idle(PORT)
            else:
                record["t_end"] = time.monotonic()
                record["aborted"] = False
                self.runtime.bus.publish("B", validate(result.raw), seq=seq)
            record["done"] = True             # set last: t_idle is written before it

    def in_flight(self, t: float) -> dict | None:
        for record in reversed(self.requests):
            if record["t_req"] <= t <= record.get("t_end", float("inf")):
                return record
        return None

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=30)


def _frame_ms(result) -> list[float]:
    return [round(f.compute_s * 1000, 3) for f in result.frames]


def run_keyword_trial(trial: dict, condition: str, runtime, endpointer, subscriber, loader) -> dict:
    from runtime.stream import StreamLoop, WavSource
    from train.train_wake import SEED

    np.random.seed(SEED)                 # openwakeword's reset() draws from np.random
    runtime.branch_a.reset()
    endpointer.reset()
    subscriber.fly()
    pad = np.zeros(int(PAD_S * 16_000), dtype=np.int16)
    source = WavSource(np.concatenate([pad, trial["audio"], pad]))
    soc = soc_state()
    result = StreamLoop(runtime, endpointer, branch_b=False, front_cores=FRONT).run(source)
    t0 = source.t_start
    events = []
    for event in result.branch_a:
        msg = event.message
        applied = subscriber.wait_for(msg.seq)
        entry = {"intent": msg.command["intent"], "seq": msg.seq, "frame_index": event.frame_index,
                 "latency_offset_ms": (msg.t_publish - (t0 + trial["kw_offset_s"])) * 1000,
                 "latency_onset_ms": (msg.t_publish - (t0 + trial["kw_onset_s"])) * 1000,
                 "fsm_ms": None if applied is None else (applied["t_applied"] - msg.t_publish) * 1000}
        if loader is not None:
            request = loader.in_flight(msg.t_publish)
            entry["in_flight"] = request is not None
            if request is not None:
                deadline = time.monotonic() + 15
                while not request.get("done") and time.monotonic() < deadline:
                    time.sleep(0.005)
                entry["aborted"] = request.get("aborted")
                entry["abort_return_ms"] = (request["t_end"] - msg.t_publish) * 1000
                if request.get("aborted"):
                    idle = request.get("t_idle")
                    entry["server_idle_ms"] = None if idle is None else (idle - msg.t_publish) * 1000
                else:
                    b = subscriber.wait_for(request["seq"])
                    entry["late_b_stale_discarded"] = None if b is None else b["stale_discarded"]
        events.append(entry)
    return {"condition": condition, "take": trial["take"], "class": trial["class"],
            "pass": trial["pass_"], "kw_offset_s": trial["kw_offset_s"],
            "kw_onset_s": trial["kw_onset_s"], "events": events,
            "n_segments_seen": len(result.branch_b), "soc": soc, "frame_ms": _frame_ms(result)}


def run_utterance_trial(item: dict, runtime, endpointer, subscriber) -> dict:
    import soundfile as sf

    from eval.exp3 import CLEAN_AUDIO, TAIL_S, score_segment
    from runtime.stream import StreamLoop, WavSource
    from train.train_wake import SEED

    np.random.seed(SEED)
    runtime.branch_a.reset()
    endpointer.reset()
    subscriber.fly()
    audio, rate = sf.read(str(CLEAN_AUDIO / f"{item['id']}.wav"), dtype="int16")
    assert rate == 16_000 and audio.ndim == 1, item["id"]
    source = WavSource(np.concatenate([audio, np.zeros(int(TAIL_S * 16_000), dtype=np.int16)]))
    soc = soc_state()
    result = StreamLoop(runtime, endpointer, front_cores=FRONT, back_cores=BACK).run(source)
    pad_s = endpointer._pad / 16_000
    segments = []
    for record in result.branch_b:
        u, trace = record.utterance, record.trace
        vad_wait_s = 0.0 if u.forced else u.t0_s - (u.end_s - pad_s)
        seg = {"start_s": round(u.start_s, 4), "end_s": round(u.end_s, 4), "t0_s": round(u.t0_s, 4),
               "forced": u.forced, "transcript": trace.transcript, "raw": trace.raw,
               "aborted": trace.aborted, "vad_wait_ms": vad_wait_s * 1000,
               "queue_ms": (trace.t_start - record.t0_wall) * 1000, "stt_ms": trace.stt_ms,
               "parse_wall_ms": trace.parse_wall_ms, "prefill_ms": trace.prefill_ms,
               "decode_ms": trace.decode_ms}
        if trace.raw is not None:
            seg.update(score_segment(trace.raw, item["target"]))
        else:
            seg.update({"canonical": None, "dispatched": None, "correct": False})
        applied = None if trace.message is None else subscriber.wait_for(trace.message.seq)
        if applied is not None:
            t_done = applied["t_applied"]
            seg["validate_fsm_ms"] = (t_done - trace.t_parsed) * 1000
            seg["e2e_t0_ms"] = (t_done - record.t0_wall) * 1000
            seg["e2e_speech_end_ms"] = seg["e2e_t0_ms"] + seg["vad_wait_ms"]
            seg["e2e_speech_start_ms"] = (t_done - (source.t_start + u.start_s + pad_s)) * 1000
        segments.append(seg)
    return {"id": item["id"], "condition": "clean", "reference": item["transcript"],
            "gold": item["target"], "segments": segments,
            "branch_a_events": [e.message.command["intent"] for e in result.branch_a],
            "soc": soc, "frame_ms": _frame_ms(result)}


def _write_rows(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read_rows(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def run(phases: Sequence[str], passes: int, limit: int | None, warmup_s: float,
        any_governor: bool = False) -> None:
    from eval.exp3 import GGUF, _load_golden
    from runtime.branch_a import load_trained
    from runtime.bus import CommandBus
    from runtime.parser import CommandParser
    from runtime.pipeline import PipelineRuntime
    from runtime.stream import pin
    from runtime.vad import Endpointer

    governor = _read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    if governor != "performance" and not any_governor:
        raise SystemExit(f"governor is {governor!r}; Table 7's clock assumption needs 'performance'")

    # llama-server inherits the spawning thread's mask: start it from cores 1-3,
    # then move this thread (the frame loop, Branch A, the VAD) to core 0.
    pin(BACK)
    parser, server = CommandParser.for_gguf(GGUF, port=PORT)
    pin(FRONT)
    items = _load_golden()[:limit]
    trials = keyword_trials(passes, limit)
    meta = {"host": platform.node(), "governor": governor, "started": time.strftime("%FT%T%z"),
            "llama_server_affinity": task_affinity(server._process.pid), "passes": passes,
            "limit": limit, "warmup_s": warmup_s}
    bus = CommandBus(port=BUS_PORT, bind=True)
    subscriber = Subscriber(bus)
    try:
        runtime = PipelineRuntime(bus=bus, branch_a=load_trained(), parser=parser)
        endpointer = Endpointer()
        meta["main_affinity"] = sorted(__import__("os").sched_getaffinity(0))
        for phase in phases:
            started = time.monotonic()
            loader = None
            if phase == "loaded":
                loader = Loader(runtime, [i["transcript"] for i in _load_golden()])
                loader.start()
                print(f"  warm-up {warmup_s:.0f} s under load", flush=True)
                time.sleep(warmup_s)
                meta["soc_after_warmup"] = soc_state()
            rows = []
            if phase == "branch_b":
                for item in items:
                    rows.append(run_utterance_trial(item, runtime, endpointer, subscriber))
                    time.sleep(GAP_S)
                _write_rows(PREDS / "clean.jsonl", rows)
            else:
                for trial in trials:
                    rows.append(run_keyword_trial(trial, phase, runtime, endpointer, subscriber, loader))
                    time.sleep(GAP_S)
            if loader is not None:
                loader.stop()
                meta["loader_requests"] = len(loader.requests)
                meta["loader_affinity"] = getattr(loader, "affinity", None)
            for row in rows:
                row["host"] = meta["host"]
            _write_rows(RAW / f"{phase}.jsonl", rows)
            meta[f"{phase}_seconds"] = round(time.monotonic() - started, 1)
            meta[f"{phase}_soc_end"] = soc_state()
            print(f"  {phase:>8s}: {len(rows)} trials in {meta[f'{phase}_seconds']:.0f} s "
                  f"soc {meta[f'{phase}_soc_end']}", flush=True)
    finally:
        subscriber.close()
        bus.close()
        server.stop()
        meta["ended"] = time.strftime("%FT%T%z")
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")


# --- analysis -----------------------------------------------------------------


def percentiles(values: Sequence[float]) -> dict:
    values = [v for v in values if v is not None]
    return {"n": len(values), "p50": nearest_rank(values, 50), "p95": nearest_rank(values, 95),
            "p99": nearest_rank(values, 99), "max": max(values) if values else float("nan")}


def first_own_event(row: dict) -> dict | None:
    """The trial's detection: the first event of the take's own class."""
    intent = {"swarm_hold": "hover", "swarm_abort": "abort"}[row["class"]]
    return next((e for e in row["events"] if e["intent"] == intent), None)


def cross_trigger(rows: Sequence[dict]) -> dict:
    """take class -> {fired hover, fired abort, missed}: the 2x2 matrix plus misses."""
    out = {c: {"hover": 0, "abort": 0, "missed": 0, "n": 0} for c in ("swarm_hold", "swarm_abort")}
    for row in rows:
        cell = out[row["class"]]
        cell["n"] += 1
        fired = {e["intent"] for e in row["events"]}
        for intent in fired:
            cell[intent] += 1
        if first_own_event(row) is None:
            cell["missed"] += 1
    return out


def stage_rows(branch_b: Sequence[dict]) -> list[dict]:
    segs = [s for row in branch_b for s in row["segments"]]
    done = [s for s in segs if "e2e_t0_ms" in s]
    stages = [("vad_wait", "VAD endpointing wait", [s["vad_wait_ms"] for s in segs]),
              ("queue", "queue (segment waits for Branch B)", [s["queue_ms"] for s in segs]),
              ("stt", "STT (whisper-cli, -t 3)", [s["stt_ms"] for s in segs]),
              ("prefill", "SLM prefill (server timing, no prompt cache)", [s["prefill_ms"] for s in done]),
              ("decode", "SLM decode (server timing)", [s["decode_ms"] for s in done]),
              ("llm", "SLM prefill + decode (Table 6 combined row)",
               [s["prefill_ms"] + s["decode_ms"] for s in done]),
              ("http", "SLM request overhead (template, tokenize, HTTP)",
               [s["parse_wall_ms"] - s["prefill_ms"] - s["decode_ms"] for s in done]),
              ("validate_fsm", "validate, bus, FSM check", [s["validate_fsm_ms"] for s in done]),
              ("e2e_t0", "E2E from T0 (NFR-2 headline)", [s["e2e_t0_ms"] for s in done]),
              ("e2e_speech_end", "E2E from true end of speech (+ VAD wait)",
               [s["e2e_speech_end_ms"] for s in done]),
              ("e2e_speech_start", "E2E from start of speech", [s["e2e_speech_start_ms"] for s in done])]
    rows = []
    for key, label, values in stages:
        # Table 6's 5,500 ms from start of speech is for a 3 s utterance; the golden set's
        # run to 9 s, so that row is reported without a verdict.
        budget = None if key == "e2e_speech_start" else BUDGETS.get(key if key != "e2e_speech_end" else "e2e_t0")
        rows.append({"measure": key, "label": label, "condition": "branch_b", **percentiles(values),
                     "budget_p95_ms": budget})
    return rows


def algorithmic_ms(row: dict, event: dict) -> float:
    """Keyword offset to the end of the frame that fired: the spotter's own delay plus
    frame quantisation. Hardware-independent -- the same audio fires on the same frame
    on any machine -- so what is left of the latency is the Pi's."""
    from runtime.stream import FRAME_S

    return ((event["frame_index"] + 1) * FRAME_S - row["kw_offset_s"]) * 1000


def keyword_rows(rows: Sequence[dict], condition: str) -> list[dict]:
    pairs = [(r, first_own_event(r)) for r in rows if first_own_event(r) is not None]
    detected = [e for _, e in pairs]
    algorithmic = [algorithmic_ms(r, e) for r, e in pairs]
    out = [{"measure": "a_offset", "label": f"Branch A from keyword offset ({condition})",
            "condition": condition, **percentiles([e["latency_offset_ms"] for e in detected]),
            "budget_p95_ms": BUDGETS["a_offset"]},
           {"measure": "a_onset", "label": f"Branch A from keyword onset ({condition})",
            "condition": condition, **percentiles([e["latency_onset_ms"] for e in detected]),
            "budget_p95_ms": BUDGETS["a_onset"]},
           {"measure": "a_algorithmic", "label": f"  of which spotter delay + frame quantisation ({condition})",
            "condition": condition, **percentiles(algorithmic), "budget_p95_ms": None},
           {"measure": "a_system", "label": f"  of which Pi compute + publish ({condition})",
            "condition": condition,
            **percentiles([e["latency_offset_ms"] - a for (_, e), a in zip(pairs, algorithmic)]),
            "budget_p95_ms": None},
           {"measure": "a_fsm", "label": f"Branch A publish to FSM applied ({condition})",
            "condition": condition, **percentiles([e["fsm_ms"] for e in detected]),
            "budget_p95_ms": None}]
    if condition == "loaded":
        pre = [e for e in detected if e.get("in_flight") and e.get("aborted")]
        recovery = [max(e["abort_return_ms"], e["server_idle_ms"]) for e in pre
                    if e.get("server_idle_ms") is not None]
        out += [{"measure": "abort_return", "label": "trigger to aborted decode returning",
                 "condition": condition, **percentiles([e["abort_return_ms"] for e in pre]),
                 "budget_p95_ms": None},
                {"measure": "recovery", "label": "NFR-17 recovery: trigger to Branch B free",
                 "condition": condition, **percentiles(recovery), "budget_p95_ms": BUDGETS["recovery"]}]
    return out


def verdict(row: dict) -> str:
    if row["budget_p95_ms"] is None or not row["n"]:
        return ""
    return "MEETS" if row["p95"] <= row["budget_p95_ms"] else "MISSES"


def analyse() -> int:
    phases = {p: _read_rows(RAW / f"{p}.jsonl") for p in PHASES if (RAW / f"{p}.jsonl").is_file()}
    table = []
    if "branch_b" in phases:
        table += stage_rows(phases["branch_b"])
    for condition in ("idle", "loaded"):
        if condition in phases:
            table += keyword_rows(phases[condition], condition)
    for row in table:
        row["verdict"] = verdict(row)
    fields = ["measure", "label", "condition", "n", "p50", "p95", "p99", "max", "budget_p95_ms", "verdict"]
    with (RESULTS / "exp2.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in table:
            writer.writerow({k: (round(v, 1) if isinstance(v, float) else v) for k, v in row.items()})
    (RESULTS / "exp2_analysis.md").write_text(analysis_markdown(phases, table), encoding="utf-8")
    print(f"wrote results/exp2.csv ({len(table)} rows) and results/exp2_analysis.md")
    for row in table:
        print(f"  {row['condition']:>8s} {row['measure']:>16s} n={row['n']:>3d} "
              f"p50={row['p50']:8.1f} p95={row['p95']:8.1f} {row['verdict']}")
    return 0


def _ms(v: float) -> str:
    return "--" if v is None or v != v else f"{v:,.0f}"


def analysis_markdown(phases: dict, table: Sequence[dict]) -> str:
    meta = json.loads((RAW / "meta.json").read_text()) if (RAW / "meta.json").is_file() else {}
    lines = ["# Exp-2 -- dual-path latency on the Pi", "",
             "Generated by `python eval/exp2.py --analyse-only`. Do not edit by hand.", "",
             f"Host `{meta.get('host', '?')}`, governor `{meta.get('governor', '?')}`, "
             f"started {meta.get('started', '?')}. llama-server thread affinity "
             f"{meta.get('llama_server_affinity')}, loader {meta.get('loader_affinity')}, frame loop "
             f"{meta.get('main_affinity')} (Table 7). "
             f"Warm-up {meta.get('warmup_s')} s under load; SoC after warm-up {meta.get('soc_after_warmup')}.",
             "", "## Budget versus measured (Table 6)", "",
             "| measure | condition | n | p50 | p95 | p99 | max | budget p95 | verdict |",
             "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |"]
    for r in table:
        lines.append(f"| {r['label']} | {r['condition']} | {r['n']} | {_ms(r['p50'])} | {_ms(r['p95'])} "
                     f"| {_ms(r['p99'])} | {_ms(r['max'])} | {_ms(r['budget_p95_ms'])} | {r['verdict']} |")
    lines += ["", "All times ms, nearest-rank percentiles. Branch B rows count endpointed segments, "
              "not utterances."]

    if "branch_b" in phases:
        rows = phases["branch_b"]
        split = sum(len(r["segments"]) > 1 for r in rows)
        none = sum(not r["segments"] for r in rows)
        a_fp = sum(len(r["branch_a_events"]) for r in rows)
        correct = sum(bool(r["segments"]) and all(s["correct"] for s in r["segments"]) for r in rows)
        lines += ["", "## Branch B, clean golden set", "",
                  f"- {len(rows)} utterances, {sum(len(r['segments']) for r in rows)} segments. "
                  f"Split into >1 segment: **{split}/{len(rows)} ({split / len(rows):.1%})**; "
                  f"no segment: {none}. Every segment is a separate Branch B pass and a separate "
                  "latency sample.",
                  f"- CRR on the Pi, every-segment rule: {correct}/{len(rows)} = {correct / len(rows):.3f} "
                  "(A7b compares every prediction with A7a's; `results/exp2_preds/clean.jsonl`).",
                  f"- Branch A triggers while listening to the golden set: {a_fp}."]
    for condition in ("idle", "loaded"):
        if condition not in phases:
            continue
        matrix = cross_trigger(phases[condition])
        lines += ["", f"## Branch A, {condition}: cross-trigger matrix", "",
                  "| take class | n | fired hover | fired abort | missed |",
                  "| :--- | ---: | ---: | ---: | ---: |"]
        for c, cell in matrix.items():
            lines.append(f"| `{c}` | {cell['n']} | {cell['hover']} | {cell['abort']} | {cell['missed']} |")
        # The offset is the capture tool's energy-based end of speech; a detection that
        # precedes it measures the anchor's error, not a negative spotter delay.
        early = sorted((e["latency_offset_ms"], r["take"]) for r in phases[condition]
                       if (e := first_own_event(r)) is not None and e["latency_offset_ms"] < 0)
        n_detected = sum(first_own_event(r) is not None for r in phases[condition])
        lines += ["", f"Detections before the recorded keyword offset: {len(early)}/{n_detected}"
                  + (f", earliest {early[0][0]:.1f} ms (takes {', '.join(sorted({t for _, t in early}))})."
                     if early else ".")]
    if "loaded" in phases:
        detected = [first_own_event(r) for r in phases["loaded"] if first_own_event(r)]
        in_flight = [e for e in detected if e.get("in_flight")]
        aborted = [e for e in in_flight if e.get("aborted")]
        late = [e for e in in_flight if e.get("aborted") is False]
        idle_none = [e for e in aborted if e.get("server_idle_ms") is None]
        lines += ["", "## Pre-emption (FR-6, NFR-17)", "",
                  f"- Triggers with a Branch B decode in flight: {len(in_flight)}/{len(detected)}.",
                  f"- Decode aborted by the trigger: {len(aborted)}; finished anyway (the abort lost "
                  f"the race): {len(late)}, of which discarded by the sequence rule: "
                  f"{sum(bool(e.get('late_b_stale_discarded')) for e in late)}.",
                  f"- Server never reported idle within 10 s after an abort: {len(idle_none)}.",
                  f"- Recoveries above 1,000 ms: "
                  f"{sum(max(e['abort_return_ms'], e['server_idle_ms']) > 1000 for e in aborted if e.get('server_idle_ms') is not None)}"
                  f"/{len(aborted) - len(idle_none)}."]
        if meta.get("loader_requests"):
            lines.append(f"- Loader requests over the phase (incl. warm-up): {meta['loader_requests']}.")
    lines += ["", "## Core 0 frame budget (Table 7)", ""]
    for phase, rows in phases.items():
        frame = [v for r in rows for v in r["frame_ms"]]
        stats = percentiles(frame)
        over = sum(v > 80 for v in frame)
        lines.append(f"- {phase}: {stats['n']} frames, compute p50 {stats['p50']:.1f} ms, p99 "
                     f"{stats['p99']:.1f} ms, max {stats['max']:.1f} ms; over the 80 ms period: {over}.")
    lines += ["", "## SoC", ""]
    for phase, rows in phases.items():
        temps = [r["soc"].get("temp") for r in rows if r["soc"].get("temp") is not None]
        throttled = sum(r["soc"].get("throttled", "0x0") not in ("0x0",) for r in rows)
        if temps:
            lines.append(f"- {phase}: {min(temps):.1f}-{max(temps):.1f} C at trial start; "
                         f"throttle word non-zero on {throttled}/{len(rows)} trials.")
    lines += ["", "## Read before quoting", "",
              "- The operating point (0.999) and the per-class ROC are `results/wake_training.md`'s; "
              "not re-selected here. Ambient false accepts: 2.33/h, 95% CI [0.06, 12.98] "
              "(NFR-15 not demonstrated).",
              "- The bus is loopback on the Pi; the Wi-Fi hop to the workstation is not in these "
              "figures (prd 4.7).",
              "- Prefill runs with `cache_prompt=false`, as the deployed parser does for Surface B "
              "parity; Table 6's prefill line assumes a cached prefix (Exp-1 measured that case).",
              "- Keyword offset is the capture tool's energy-based end of speech, not a forced "
              "alignment."]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--phases", nargs="+", choices=PHASES, default=list(PHASES))
    ap.add_argument("--passes", type=int, default=2, help="passes over the 40 takes per condition")
    ap.add_argument("--limit", type=int, default=None, help="first N takes / utterances (smoke)")
    ap.add_argument("--warmup-seconds", type=float, default=300.0)
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--out", type=Path, default=None,
                    help="write raw, preds, csv and md under this directory (smoke runs)")
    ap.add_argument("--any-governor", action="store_true", help="skip the governor check (off the Pi)")
    args = ap.parse_args(argv)
    if args.out is not None:
        global RESULTS, RAW, PREDS
        RESULTS, RAW, PREDS = args.out, args.out / "exp2_raw", args.out / "exp2_preds"
        RESULTS.mkdir(parents=True, exist_ok=True)
    if not args.analyse_only:
        run(args.phases, args.passes, args.limit, args.warmup_seconds, args.any_governor)
    return analyse()


if __name__ == "__main__":
    sys.exit(main())
