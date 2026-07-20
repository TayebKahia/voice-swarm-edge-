"""Tests for golden-set capture (`data/record_session.py`).

Every property here exists because getting it wrong costs 320 recordings that
cannot be re-made: the wrong device, a clipped take accepted, a silent take
accepted, or a filename that has drifted off its row in `test_golden.jsonl`.
"""

from __future__ import annotations

import numpy as np
import pytest

from data.record_session import (
    CAPTURE_RATE,
    CLIP_LEVEL,
    GOOD_SNR_DB,
    MIN_SECONDS,
    MIN_SNR_DB,
    dbfs,
    read_transcripts,
    verify,
)

FLOOR = 10.0 ** (-64.0 / 20.0)


def make_take(seconds: float = 3.5, amplitude: float = 0.02, lead: float = 0.6) -> np.ndarray:
    """Room tone with a voiced-looking burst dropped into it."""
    rng = np.random.default_rng(0)
    audio = rng.normal(0.0, FLOOR, int(seconds * CAPTURE_RATE)).astype(np.float32)
    speech_samples = int(min(2.0, seconds - lead - 0.4) * CAPTURE_RATE)
    t = np.arange(speech_samples) / CAPTURE_RATE
    burst = amplitude * np.sin(2 * np.pi * 180 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t))
    start = int(lead * CAPTURE_RATE)
    audio[start : start + speech_samples] += burst.astype(np.float32)
    return audio


def test_a_normal_take_passes():
    report = verify("0001", make_take(), FLOOR)
    assert report.ok, report.failures
    assert report.snr_db > GOOD_SNR_DB


def test_one_clipped_sample_rejects_the_take():
    """Clipping is unrecoverable, so the threshold is one sample, not a fraction."""
    audio = make_take()
    audio[1234] = CLIP_LEVEL
    report = verify("0002", audio, FLOOR)
    assert not report.ok
    assert any("CLIPPED" in f for f in report.failures)


def test_room_tone_alone_is_rejected_as_silence():
    rng = np.random.default_rng(1)
    audio = rng.normal(0.0, FLOOR, 3 * CAPTURE_RATE).astype(np.float32)
    report = verify("0003", audio, FLOOR)
    assert not report.ok


def test_digital_silence_is_rejected_without_dividing_by_it():
    report = verify("0004", np.zeros(3 * CAPTURE_RATE, dtype=np.float32), FLOOR)
    assert not report.ok
    assert any("silence" in f for f in report.failures)


def test_a_mis_trigger_is_too_short():
    report = verify("0005", make_take(seconds=0.2, lead=0.0), FLOOR)
    assert any("too short" in f for f in report.failures)
    assert MIN_SECONDS == 0.5


def test_a_quiet_but_usable_take_warns_and_is_still_written():
    """The BOYA's active-speech RMS sits ~11 dB under its peak, so rejecting at
    20 dB over the floor would reject the whole corpus. Between the two
    thresholds the take is kept with a warning."""
    report = verify("0006", make_take(amplitude=0.010), FLOOR)
    assert report.ok
    assert MIN_SNR_DB < report.snr_db < GOOD_SNR_DB
    assert any("over the floor" in w for w in report.warnings)


def test_no_tail_after_speech_warns_because_the_vad_needs_it():
    # speech spans 0.6-2.6 s; cut the file at 2.65 s so only 50 ms of tone remain
    audio = make_take(seconds=3.5, lead=0.6)[: int(2.65 * CAPTURE_RATE)]
    report = verify("0007", audio, FLOOR)
    assert report.ok
    assert any("after speech offset" in w for w in report.warnings)


def test_reported_levels_are_dbfs_not_linear():
    report = verify("0008", make_take(), FLOOR)
    assert -80.0 < report.active_dbfs < 0.0
    assert report.peak_dbfs == pytest.approx(dbfs(0.02), abs=1.5)


# --- the join key ----------------------------------------------------------


def test_transcripts_parse_as_id_and_text():
    items = read_transcripts()
    assert len(items) == 200
    assert all(item_id.isdigit() and len(item_id) == 4 for item_id, _ in items)
    assert all(text for _, text in items)


def test_transcript_ids_are_the_golden_set_ids_in_order():
    """`0042.wav` is the join key across s1/s2/s3 and line `0042` of
    `test_golden.jsonl`. A skipped or retaken item must not shift the corpus."""
    import json
    from pathlib import Path

    golden = [
        json.loads(line)["id"]
        for line in (Path(__file__).resolve().parent / "test_golden.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert [item_id for item_id, _ in read_transcripts()] == golden
