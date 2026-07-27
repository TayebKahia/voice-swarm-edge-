"""Tests for the shared measurement harness.

The harness is the only thing standing between a six-hour overnight run and a CSV
that cannot be published. These tests pin the properties that would make such a file
quietly wrong rather than obviously broken: a lost trial, a parent-only RSS reading,
an aggregate that conflates the two sample sizes, an interpolated percentile.
"""

from __future__ import annotations

import csv
import subprocess
import sys
import time

import pytest

from eval.bench import (FIELDNAMES, STAGES, Bench, Trial, aggregate, dry_run,
                        probe_platform, read_trials)


@pytest.fixture
def bench(tmp_path):
    with Bench(tmp_path / "trials.csv") as instance:
        yield instance


class TestTrial:
    def test_stage_accumulates_rather_than_overwrites(self):
        trial = Trial(experiment=1, config="c", item_id="i", index=0)
        for _ in range(2):
            with trial.stage("stt"):
                time.sleep(0.005)
        assert trial.stages_ms["stt"] >= 9.0

    def test_unknown_stage_is_rejected(self):
        # A typo would otherwise create a column no aggregate knows about, and the
        # stage's time would vanish from the end-to-end total.
        trial = Trial(experiment=1, config="c", item_id="i", index=0)
        with pytest.raises(ValueError, match="unknown stage"):
            with trial.stage("slm"):
                pass

    def test_total_is_the_sum_of_the_stages(self):
        trial = Trial(experiment=1, config="c", item_id="i", index=0)
        trial.stages_ms = {"stt": 100.0, "slm_decode": 250.0}
        assert trial.total_ms == 350.0

    def test_stage_is_timed_even_when_the_body_raises(self):
        trial = Trial(experiment=1, config="c", item_id="i", index=0)
        with pytest.raises(RuntimeError):
            with trial.stage("stt"):
                time.sleep(0.003)
                raise RuntimeError("boom")
        assert trial.stages_ms["stt"] > 0


class TestBench:
    def test_writes_one_row_per_trial(self, bench):
        for index in range(3):
            with bench.trial(experiment=1, config="c", item_id=f"{index}", index=index) as trial:
                with trial.stage("stt"):
                    time.sleep(0.001)
        bench.close()
        assert len(read_trials(bench.path)) == 3

    def test_row_survives_an_exception_in_the_body(self, bench):
        # A crashed trial is evidence. A silently missing one shifts every aggregate.
        with pytest.raises(RuntimeError):
            with bench.trial(experiment=1, config="c", item_id="x", index=0) as trial:
                with trial.stage("stt"):
                    time.sleep(0.001)
                raise RuntimeError("synthetic")
        bench.close()
        rows = read_trials(bench.path)
        assert len(rows) == 1
        assert "RuntimeError: synthetic" in rows[0]["note"]

    def test_rows_are_flushed_immediately(self, tmp_path):
        # An overnight run that dies at hour five must leave five hours behind.
        instance = Bench(tmp_path / "t.csv")
        with instance.trial(experiment=1, config="c", item_id="a", index=0) as trial:
            with trial.stage("stt"):
                pass
        assert len(read_trials(instance.path)) == 1  # read before close()
        instance.close()

    def test_csv_is_rectangular_across_experiments(self, bench):
        with bench.trial(experiment=2, config="a", item_id="1", index=0) as trial:
            with trial.stage("wake"):
                pass
        with bench.trial(experiment=1, config="b", item_id="2", index=1) as trial:
            with trial.stage("slm_decode"):
                pass
        bench.close()
        with bench.path.open(newline="") as handle:
            reader = csv.reader(handle)
            widths = {len(row) for row in reader}
        assert widths == {len(FIELDNAMES)}

    def test_every_stage_has_a_column(self, bench):
        bench.close()
        assert all(f"{name}_ms" in FIELDNAMES for name in STAGES)

    def test_records_peak_rss_above_zero(self, bench):
        with bench.trial(experiment=1, config="c", item_id="a", index=0) as trial:
            with trial.stage("stt"):
                time.sleep(0.05)
        bench.close()
        assert float(read_trials(bench.path)[0]["peak_rss_mb"]) > 0

    @pytest.mark.slow
    def test_peak_rss_includes_child_processes(self, bench):
        # whisper.cpp and llama.cpp are subprocesses. A parent-only reading would put
        # the full stack at tens of MB and make NFR-9a's 2.5 GB ceiling meaningless.
        with bench.trial(experiment=1, config="parent", item_id="a", index=0) as trial:
            with trial.stage("stt"):
                time.sleep(0.15)
        with bench.trial(experiment=1, config="child", item_id="b", index=1) as trial:
            with trial.stage("stt"):
                subprocess.run(
                    [sys.executable, "-c",
                     "buf = bytearray(300 * 1024 * 1024); "
                     "import time; time.sleep(0.25); len(buf)"],
                    check=True)
        bench.close()
        rows = {row["config"]: float(row["peak_rss_mb"]) for row in read_trials(bench.path)}
        assert rows["child"] > rows["parent"] + 100

    def test_append_does_not_repeat_the_header(self, tmp_path):
        path = tmp_path / "t.csv"
        for index in range(2):
            with Bench(path, append=True) as instance:
                with instance.trial(experiment=1, config="c", item_id=f"{index}", index=index):
                    pass
        assert sum(1 for line in path.read_text().splitlines() if line.startswith("experiment,")) == 1
        assert len(read_trials(path)) == 2

    def test_platform_is_recorded_on_every_row(self, bench):
        # Exp-1/2/3 belong on the Pi; a latency column filled on the workstation is
        # the easiest way to publish a wrong headline number.
        with bench.trial(experiment=1, config="c", item_id="a", index=0):
            pass
        bench.close()
        row = read_trials(bench.path)[0]
        assert row["host_machine"] == probe_platform()["machine"]
        assert row["host_is_pi"] in ("true", "false")


class TestAggregate:
    def _rows(self, bench):
        bench.close()
        return read_trials(bench.path)

    def test_keeps_n_latency_and_n_accuracy_apart(self, bench):
        # Four repetitions of two items: eight timings, two scored items.
        for index in range(8):
            with bench.trial(experiment=1, config="m", item_id=f"item{index % 2}",
                             index=index) as trial:
                with trial.stage("stt"):
                    time.sleep(0.001)
                trial.correct = True
        summary = aggregate(self._rows(bench))[0]
        assert summary["n_latency"] == 8
        assert summary["n_accuracy"] == 2

    def test_percentiles_are_observed_values(self, bench):
        for index in range(10):
            with bench.trial(experiment=1, config="m", item_id=f"{index}", index=index) as trial:
                with trial.stage("stt"):
                    time.sleep(0.001 * (index + 1))
        rows = self._rows(bench)
        totals = sorted(float(row["total_ms"]) for row in rows)
        summary = aggregate(rows)[0]
        assert summary["total_p95"] == pytest.approx(round(totals[-1], 2))

    def test_counts_throttled_trials(self, bench):
        with bench.trial(experiment=1, config="m", item_id="a", index=0):
            pass
        rows = self._rows(bench)
        rows[0]["throttled_now"] = "1"
        summary = aggregate(rows)[0]
        assert summary["throttled_trials"] == 1
        assert summary["throttled_fraction"] == 1.0

    def test_groups_by_config(self, bench):
        for config in ("a", "b"):
            with bench.trial(experiment=1, config=config, item_id="x", index=0) as trial:
                with trial.stage("stt"):
                    pass
        assert {s["config"] for s in aggregate(self._rows(bench))} == {"a", "b"}

    def test_unscored_trials_leave_accuracy_blank_not_zero(self, bench):
        with bench.trial(experiment=1, config="m", item_id="a", index=0) as trial:
            with trial.stage("stt"):
                pass
        assert aggregate(self._rows(bench))[0]["accuracy"] == ""


class TestDryRun:
    @pytest.mark.parametrize("experiment", [0, 1, 2, 3, 4])
    def test_green_for_every_experiment(self, experiment, tmp_path):
        assert dry_run(experiment, tmp_path / f"e{experiment}.csv", trials=4) == 0
