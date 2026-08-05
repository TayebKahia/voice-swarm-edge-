#!/usr/bin/env python3
"""The measurement harness Exp-1 through Exp-4 share.

FR-10 asks for **one CSV row per trial** --- not per configuration, not per stage.
Aggregates are computed from that file afterwards, never accumulated in flight, so
every number in a thesis table can be traced back to the individual runs behind it
and a p95 can be recomputed without re-running anything.

Four things are recorded on every trial, because each of them silently invalidates a
latency figure if it is missing:

* **per-stage wall-clock**, against the Table 6 budget (§4.4, NFR-3);
* **peak RSS including child processes** --- `whisper.cpp` and `llama.cpp` are
  subprocesses, so a parent-only reading would report the harness's own footprint and
  NFR-9a's 2.5 GB ceiling would look comfortably met at about 60 MB;
* **SoC temperature**, and
* **throttle flags**. NFR-10 caps throttled trials at 5% and requires them reported
  either way. A Pi that has dropped to 1.5 GHz mid-run produces latencies that are
  real but not the ones the configuration would give when cool --- spike S1 measured
  exactly that. An unflagged throttled trial is an unreproducible number.

Two conventions are inherited rather than re-decided: percentiles are **nearest-rank**
and every aggregate carries its ***n*** (§2.7). `n_accuracy` and `n_latency` differ by
construction --- decoding is greedy under a fixed grammar, so one pass settles accuracy
exactly, while latency needs 200 repetitions --- so the aggregate keeps them apart
rather than printing one *n* that is wrong for one of them.

**Both anchors, always.** Table 6 requires the headline figure (Branch B from
end-of-speech, Branch A from keyword offset) *and* the onset-anchored figure beside
it. Reporting only the first looks evasive; reporting only the second penalises the
system for the length of the operator's sentence.

Usage:
    python eval/bench.py --dry-run --experiment 1      # the Session 04 gate
    python eval/bench.py --aggregate results/exp1.csv
"""

from __future__ import annotations

import argparse
import csv
import platform
import re
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Sequence

import psutil

if __package__ in (None, ""):  # `python eval/bench.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.stats import nearest_rank

__all__ = ["STAGES", "Trial", "Bench", "aggregate", "probe_platform"]

#: Every stage any experiment can time, in pipeline order. The set is fixed so the
#: CSV is rectangular across experiments and one aggregate script reads all of them;
#: a stage an experiment does not run is left empty rather than omitted.
STAGES: tuple[str, ...] = (
    "capture",        # ring buffer -> frame available
    "wake",           # Branch A: openWakeWord spotter
    "vad",            # Silero endpointing, incl. the min_silence wall-clock wait
    "stt",            # whisper.cpp tiny.en
    "slm_prefill",    # cached prefix
    "slm_decode",     # constrained generation
    "validate",       # schema/validate.py, layer 2
    "fsm",            # swarm/fsm.py, layer 3
    "bus",            # runtime/bus.py publish -- T1 for both branches
)

#: Sampling period for the resource monitor. 20 ms is fast enough to catch the RSS
#: peak of a model load without the sampler itself showing up in the latency.
SAMPLE_SECONDS = 0.020

_THROTTLE_BITS = {
    0: "under_voltage_now",
    1: "arm_freq_capped_now",
    2: "currently_throttled",
    3: "soft_temp_limit_now",
    16: "under_voltage_occurred",
    17: "arm_freq_capped_occurred",
    18: "throttling_occurred",
    19: "soft_temp_limit_occurred",
}


# --------------------------------------------------------------------------
# platform


def _read_temperature() -> float | None:
    """SoC temperature in Celsius, or None where nothing reports one."""
    try:
        completed = subprocess.run(
            ["vcgencmd", "measure_temp"], capture_output=True, text=True, timeout=2
        )
        match = re.search(r"([\d.]+)", completed.stdout)
        if match:
            return float(match.group(1))
    except (OSError, subprocess.SubprocessError):
        pass
    for zone in sorted(Path("/sys/class/thermal").glob("thermal_zone*")):
        try:
            return int((zone / "temp").read_text().strip()) / 1000.0
        except (OSError, ValueError):
            continue
    return None


def _read_throttled() -> tuple[str, bool] | tuple[None, None]:
    """Raspberry Pi throttle word, decoded. `(None, None)` off-Pi.

    The distinction between `_now` and `_occurred` bits matters: `_occurred` is
    sticky since boot, so a trial can be perfectly clean and still report it. Only
    the `_now` bits disqualify a trial; the sticky ones are carried so a run that
    throttled *between* trials is still visible in the record.
    """
    try:
        completed = subprocess.run(
            ["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=2
        )
        match = re.search(r"0x([0-9a-fA-F]+)", completed.stdout)
        if not match:
            return None, None
        word = int(match.group(1), 16)
        flags = [name for bit, name in _THROTTLE_BITS.items() if word & (1 << bit)]
        now = any(word & (1 << bit) for bit in (0, 1, 2, 3))
        return ("|".join(flags) if flags else "clean"), now
    except (OSError, subprocess.SubprocessError):
        return None, None


def probe_platform() -> dict[str, str]:
    """Identify the machine, so a CSV can never be mistaken for one from the other.

    Exp-1/2/3 belong on the Pi; accuracy work runs on the workstation. Both write the
    same schema, and a latency column filled on the wrong machine is the single
    easiest way to publish a wrong headline number.
    """
    model = ""
    for candidate in (Path("/proc/device-tree/model"), Path("/sys/firmware/devicetree/base/model")):
        try:
            model = candidate.read_text().strip("\x00").strip()
            break
        except OSError:
            continue
    return {
        "host": platform.node(),
        "machine": platform.machine(),
        "model": model or platform.platform(),
        "is_pi": str(bool(model and "Raspberry Pi" in model)).lower(),
        "cores": str(psutil.cpu_count(logical=True) or 0),
    }


# --------------------------------------------------------------------------
# resource sampling


class _ResourceMonitor:
    """Sample RSS across the process tree until stopped, keeping the maximum."""

    def __init__(self, pid: int | None = None) -> None:
        self._process = psutil.Process(pid)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.peak_rss_bytes = 0

    def _sample(self) -> int:
        total = 0
        try:
            total = self._process.memory_info().rss
            for child in self._process.children(recursive=True):
                try:
                    total += child.memory_info().rss
                except psutil.Error:
                    continue
        except psutil.Error:
            return total
        return total

    def _loop(self) -> None:
        while not self._stop.is_set():
            self.peak_rss_bytes = max(self.peak_rss_bytes, self._sample())
            self._stop.wait(SAMPLE_SECONDS)
        self.peak_rss_bytes = max(self.peak_rss_bytes, self._sample())

    def __enter__(self) -> "_ResourceMonitor":
        self.peak_rss_bytes = self._sample()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_exc) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)


# --------------------------------------------------------------------------
# a trial


@dataclass
class Trial:
    """One measured run. Becomes exactly one CSV row."""

    experiment: int
    config: str
    item_id: str
    index: int

    #: None where the experiment does not score correctness (a pure timing sweep).
    correct: bool | None = None
    #: Free-text, e.g. the dispatched intent on a failed item -- safe-failure needs it.
    outcome: str = ""
    anchor: str = "end_of_speech"
    stages_ms: dict[str, float] = field(default_factory=dict)
    onset_total_ms: float | None = None
    peak_rss_mb: float = 0.0
    temperature_c: float | None = None
    throttle_flags: str | None = None
    throttled_now: bool | None = None
    note: str = ""
    #: Set by callers that decode tokens (Exp-1's tok/s column). None elsewhere --
    #: a pure timing sweep with no generation has nothing to divide by.
    tokens_predicted: int | None = None
    tokens_evaluated: int | None = None

    @property
    def total_ms(self) -> float:
        """Sum of the timed stages --- the anchored end-to-end figure."""
        return sum(self.stages_ms.values())

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        """Time one stage. Re-entering a stage accumulates rather than overwrites."""
        if name not in STAGES:
            raise ValueError(f"unknown stage {name!r}; add it to STAGES first")
        started = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - started) * 1000.0
            self.stages_ms[name] = self.stages_ms.get(name, 0.0) + elapsed

    def row(self, platform_info: dict[str, str]) -> dict[str, object]:
        row: dict[str, object] = {
            "experiment": self.experiment,
            "config": self.config,
            "item_id": self.item_id,
            "trial": self.index,
            "correct": "" if self.correct is None else int(self.correct),
            "outcome": self.outcome,
            "anchor": self.anchor,
            "total_ms": round(self.total_ms, 3),
            "onset_total_ms": "" if self.onset_total_ms is None else round(self.onset_total_ms, 3),
            "peak_rss_mb": round(self.peak_rss_mb, 2),
            "temperature_c": "" if self.temperature_c is None else round(self.temperature_c, 1),
            "throttle_flags": "" if self.throttle_flags is None else self.throttle_flags,
            "throttled_now": "" if self.throttled_now is None else int(self.throttled_now),
            "note": self.note,
            "tokens_predicted": "" if self.tokens_predicted is None else self.tokens_predicted,
            "tokens_evaluated": "" if self.tokens_evaluated is None else self.tokens_evaluated,
        }
        for name in STAGES:
            value = self.stages_ms.get(name)
            row[f"{name}_ms"] = "" if value is None else round(value, 3)
        row.update({f"host_{k}": v for k, v in platform_info.items()})
        return row


FIELDNAMES: tuple[str, ...] = (
    "experiment", "config", "item_id", "trial", "correct", "outcome", "anchor",
    "total_ms", "onset_total_ms",
    *(f"{name}_ms" for name in STAGES),
    "peak_rss_mb", "temperature_c", "throttle_flags", "throttled_now", "note",
    "tokens_predicted", "tokens_evaluated",
    "host_host", "host_machine", "host_model", "host_is_pi", "host_cores",
)


class Bench:
    """Owns the output file and the per-trial instrumentation.

    Rows are flushed as they are produced. A six-hour Exp-1 that dies at hour five
    must leave five hours of usable trials behind, not an empty buffer.
    """

    def __init__(self, path: Path | str, *, append: bool = False) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.platform = probe_platform()
        exists = self.path.is_file() and self.path.stat().st_size > 0
        self._handle = self.path.open("a" if append else "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._handle, fieldnames=FIELDNAMES, lineterminator="\n")
        if not (append and exists):
            self._writer.writeheader()
            self._handle.flush()
        self.count = 0

    @contextmanager
    def trial(
        self,
        *,
        experiment: int,
        config: str,
        item_id: str,
        index: int,
        anchor: str = "end_of_speech",
        pid: int | None = None,
    ) -> Iterator[Trial]:
        """Run one trial under resource monitoring and write its row on exit.

        The row is written even when the body raises, with the exception in `note`.
        A crashed trial is evidence; a silently missing one shifts every aggregate.
        """
        record = Trial(experiment=experiment, config=config, item_id=item_id,
                       index=index, anchor=anchor)
        monitor = _ResourceMonitor(pid)
        try:
            with monitor:
                yield record
        except Exception as exc:  # noqa: BLE001 -- recorded, then re-raised
            record.note = f"{type(exc).__name__}: {exc}"[:200]
            raise
        finally:
            record.peak_rss_mb = monitor.peak_rss_bytes / (1024 * 1024)
            record.temperature_c = _read_temperature()
            record.throttle_flags, record.throttled_now = _read_throttled()
            self._writer.writerow(record.row(self.platform))
            self._handle.flush()
            self.count += 1

    def close(self) -> None:
        self._handle.close()

    def __enter__(self) -> "Bench":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()


# --------------------------------------------------------------------------
# aggregation


def aggregate(rows: Iterable[dict], *, percentiles: Sequence[float] = (50, 95, 99)) -> list[dict]:
    """Collapse trial rows to one summary row per (experiment, config, stage).

    `n_latency` and `n_accuracy` are separate columns on purpose (§2.7): greedy
    decoding under a fixed grammar settles accuracy in one pass, while latency needs
    repetitions, so a single *n* would misdescribe one of them.
    """
    grouped: dict[tuple, dict] = {}
    for row in rows:
        key = (row["experiment"], row["config"])
        slot = grouped.setdefault(key, {
            "experiment": row["experiment"], "config": row["config"],
            "stages": {name: [] for name in (*STAGES, "total")},
            "correct": [], "items": set(), "rss": [], "temp": [], "throttled": 0,
            "tokens_predicted": 0, "decode_seconds": 0.0,
        })
        for name in (*STAGES, "total"):
            raw = row.get(f"{name}_ms" if name != "total" else "total_ms", "")
            if raw not in ("", None):
                slot["stages"][name].append(float(raw))
        if row.get("correct") not in ("", None):
            slot["correct"].append(int(row["correct"]))
            slot["items"].add(row["item_id"])
        for source, target in (("peak_rss_mb", "rss"), ("temperature_c", "temp")):
            if row.get(source) not in ("", None):
                slot[target].append(float(row[source]))
        if str(row.get("throttled_now", "")) == "1":
            slot["throttled"] += 1
        decode_ms = row.get("slm_decode_ms", "")
        if row.get("tokens_predicted") not in ("", None) and decode_ms not in ("", None):
            slot["tokens_predicted"] += int(row["tokens_predicted"])
            slot["decode_seconds"] += float(decode_ms) / 1000.0

    summaries = []
    for slot in grouped.values():
        n_latency = len(slot["stages"]["total"])
        summary = {
            "experiment": slot["experiment"],
            "config": slot["config"],
            "n_latency": n_latency,
            "n_accuracy": len(slot["items"]),
            "accuracy": round(sum(slot["correct"]) / len(slot["correct"]), 6)
                        if slot["correct"] else "",
            "peak_rss_mb": round(max(slot["rss"]), 2) if slot["rss"] else "",
            "max_temperature_c": round(max(slot["temp"]), 1) if slot["temp"] else "",
            "throttled_trials": slot["throttled"],
            "throttled_fraction": round(slot["throttled"] / n_latency, 4) if n_latency else "",
            #: Tokens summed over decode-seconds summed, not the mean of per-trial
            #: ratios --- the same "resample the right unit" reasoning as stats.py's
            #: bootstrap: a fast short trial should not count equally with a slow long
            #: one when they are averaged into one throughput figure.
            "tokens_per_second": (round(slot["tokens_predicted"] / slot["decode_seconds"], 2)
                                  if slot["decode_seconds"] else ""),
        }
        for name, samples in slot["stages"].items():
            summary[f"{name}_n"] = len(samples)
            for percentile in percentiles:
                summary[f"{name}_p{int(percentile)}"] = (
                    round(nearest_rank(samples, percentile), 2) if samples else ""
                )
        summaries.append(summary)
    return sorted(summaries, key=lambda s: (s["experiment"], s["config"]))


def read_trials(path: Path) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


# --------------------------------------------------------------------------
# dry run


def dry_run(experiment: int, out: Path, trials: int = 12) -> int:
    """Exercise every path with synthetic work --- the Session 04 gate.

    Deliberately not a mock: real sleeps, the real resource monitor, the real CSV
    writer and the real aggregate. What it does not have is a model. If this is green
    the harness is sound and only the payload is missing.
    """
    import random

    stages = {
        0: ("stt",),
        1: ("stt", "slm_prefill", "slm_decode", "validate", "fsm", "bus"),
        2: ("capture", "wake", "bus"),
        3: ("vad", "stt", "slm_prefill", "slm_decode", "validate", "fsm", "bus"),
        4: ("fsm", "bus"),
    }[experiment]
    rng = random.Random(42)

    with Bench(out) as bench:
        for index in range(trials):
            config = f"dry-{experiment}-{'aq'[index % 2]}"
            with bench.trial(experiment=experiment, config=config,
                             item_id=f"{index:04d}", index=index) as trial:
                for name in stages:
                    with trial.stage(name):
                        time.sleep(rng.uniform(0.002, 0.012))
                trial.correct = rng.random() > 0.2
                trial.outcome = "match" if trial.correct else "hover"
                trial.onset_total_ms = trial.total_ms + rng.uniform(600, 900)

        # One deliberate failure: the row must survive the exception.
        try:
            with bench.trial(experiment=experiment, config="dry-fail",
                             item_id="boom", index=999) as trial:
                with trial.stage("stt"):
                    time.sleep(0.001)
                raise RuntimeError("synthetic stage failure")
        except RuntimeError:
            pass

    rows = read_trials(out)
    summaries = aggregate(rows)

    print(f"platform : {probe_platform()}")
    print(f"trials   : {len(rows)} rows -> {out}")
    print(f"columns  : {len(FIELDNAMES)}")
    failed = [r for r in rows if r["note"]]
    print(f"recorded failures: {len(failed)} (expected 1) -- {failed[0]['note'] if failed else ''}")
    print()
    for summary in summaries:
        print(f"  {summary['config']:12s} n_lat={summary['n_latency']:3d} "
              f"n_acc={summary['n_accuracy']:3d} "
              f"acc={summary['accuracy'] or '--':>8} "
              f"total p50/p95/p99 = {summary['total_p50']}/{summary['total_p95']}/{summary['total_p99']} ms "
              f"rss={summary['peak_rss_mb']} MB "
              f"throttled={summary['throttled_fraction']}")

    problems = []
    if len(rows) != trials + 1:
        problems.append(f"expected {trials + 1} rows, got {len(rows)}")
    if len(failed) != 1:
        problems.append(f"expected 1 recorded failure, got {len(failed)}")
    if any(float(r["peak_rss_mb"]) <= 0 for r in rows):
        problems.append("a trial reported no RSS -- the monitor did not run")
    if any(s["total_p95"] == "" for s in summaries):
        problems.append("a config produced no p95")
    if problems:
        print("\nDRY RUN FAILED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("\nDRY RUN GREEN")
    return 0


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--experiment", type=int, choices=range(5), default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--aggregate", type=Path, help="summarise an existing trial CSV")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    if args.aggregate:
        summaries = aggregate(read_trials(args.aggregate))
        if not summaries:
            print("no rows")
            return 1
        writer = csv.DictWriter(sys.stdout, fieldnames=list(summaries[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(summaries)
        return 0

    if args.dry_run:
        out = args.out or Path("results") / f"bench_dryrun_exp{args.experiment}.csv"
        return dry_run(args.experiment, out)

    parser.error("nothing to do: pass --dry-run or --aggregate")
    return 2


if __name__ == "__main__":
    raise SystemExit(run())
