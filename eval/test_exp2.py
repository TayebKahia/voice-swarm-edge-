"""eval/exp2.py -- the analysis arithmetic. The run itself needs the Pi and is exercised
by running it; what is tested here is what could be silently wrong in the numbers."""

from __future__ import annotations

import pytest

from eval.exp2 import Loader, cross_trigger, first_own_event, keyword_rows, stage_rows, verdict


def _trial(cls: str, *intents: str, **event: float) -> dict:
    return {"class": cls, "kw_offset_s": 1.9, "events": [
        {"intent": i, "frame_index": 24, "latency_offset_ms": 110.0, "latency_onset_ms": 700.0,
         "fsm_ms": 1.0, **event} for i in intents]}


def test_a_trial_is_detected_by_its_own_class_only() -> None:
    assert first_own_event(_trial("swarm_hold", "abort")) is None      # a cross-trigger, not a hit
    assert first_own_event(_trial("swarm_hold", "abort", "hover"))["intent"] == "hover"


def test_cross_trigger_matrix_counts_takes_not_events() -> None:
    rows = [_trial("swarm_hold", "hover"), _trial("swarm_hold", "hover", "abort"),
            _trial("swarm_hold"), _trial("swarm_abort", "abort")]
    m = cross_trigger(rows)
    assert m["swarm_hold"] == {"hover": 2, "abort": 1, "missed": 1, "n": 3}
    assert m["swarm_abort"] == {"hover": 0, "abort": 1, "missed": 0, "n": 1}


def test_recovery_is_the_later_of_the_client_return_and_the_server_going_idle() -> None:
    rows = [_trial("swarm_abort", "abort", in_flight=True, aborted=True, abort_return_ms=5.0,
                   server_idle_ms=40.0),
            _trial("swarm_abort", "abort", in_flight=True, aborted=True, abort_return_ms=60.0,
                   server_idle_ms=20.0),
            _trial("swarm_abort", "abort", in_flight=False)]
    recovery = next(r for r in keyword_rows(rows, "loaded") if r["measure"] == "recovery")
    assert recovery["n"] == 2
    assert recovery["max"] == 60.0 and recovery["p50"] == 40.0


def test_idle_rows_have_no_preemption_measures() -> None:
    measures = {r["measure"] for r in keyword_rows([_trial("swarm_hold", "hover")], "idle")}
    assert measures == {"a_offset", "a_onset", "a_algorithmic", "a_system", "a_fsm"}


def test_branch_a_latency_splits_into_the_spotter_and_the_pi() -> None:
    # Frame 24 ends at 25 x 80 ms = 2.00 s; the keyword ended at 1.90 s.
    rows = {r["measure"]: r for r in keyword_rows([_trial("swarm_hold", "hover")], "idle")}
    assert rows["a_algorithmic"]["p50"] == pytest.approx(100.0)
    assert rows["a_system"]["p50"] == pytest.approx(10.0)


def _segment(**kw: float) -> dict:
    base = {"vad_wait_ms": 460.0, "queue_ms": 1.0, "stt_ms": 900.0, "prefill_ms": 200.0,
            "decode_ms": 600.0, "parse_wall_ms": 820.0, "validate_fsm_ms": 2.0,
            "e2e_t0_ms": 1750.0, "e2e_speech_end_ms": 2210.0, "e2e_speech_start_ms": 4000.0}
    return {**base, **kw}


def test_aborted_segments_count_for_the_waits_but_not_for_e2e() -> None:
    aborted = {k: v for k, v in _segment().items()
               if k in ("vad_wait_ms", "queue_ms", "stt_ms", "prefill_ms", "decode_ms", "parse_wall_ms")}
    rows = {r["measure"]: r for r in stage_rows([{"segments": [_segment(), aborted]}])}
    assert rows["stt"]["n"] == 2
    assert rows["e2e_t0"]["n"] == 1
    assert rows["http"]["p50"] == pytest.approx(20.0)
    # The true-end-of-speech figure is judged against the same NFR-2 line.
    assert rows["e2e_speech_end"]["budget_p95_ms"] == 2500


def test_verdict_is_on_the_p95_and_blank_without_a_budget() -> None:
    assert verdict({"budget_p95_ms": 150, "n": 3, "p95": 150.0}) == "MEETS"
    assert verdict({"budget_p95_ms": 150, "n": 3, "p95": 150.1}) == "MISSES"
    assert verdict({"budget_p95_ms": None, "n": 3, "p95": 1.0}) == ""
    assert verdict({"budget_p95_ms": 150, "n": 0, "p95": float("nan")}) == ""


def test_loader_finds_the_request_in_flight_including_an_unfinished_one() -> None:
    loader = Loader(runtime=None, transcripts=["x"])
    loader.requests = [{"seq": 1, "t_req": 1.0, "t_end": 2.0}, {"seq": 2, "t_req": 2.5}]
    assert loader.in_flight(1.5)["seq"] == 1
    assert loader.in_flight(2.2) is None
    assert loader.in_flight(9.0)["seq"] == 2
