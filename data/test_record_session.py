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
    METER_WIDTH,
    MIN_SECONDS,
    MIN_SNR_DB,
    FLOOR_PERCENTILE,
    MAINS_SHARE_WARN,
    centred,
    dbfs,
    mains_share,
    noise_floor,
    speech_level,
    live_status,
    meter,
    read_transcripts,
    verify,
)

FLOOR_DBFS = -64.0
FLOOR = 10.0 ** (FLOOR_DBFS / 20.0)


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


# --- DC offset -------------------------------------------------------------

#: S0 measured this chain at a constant +0.0065. It is about -43.7 dBFS, some
#: 20 dB above the room floor the same spike measured.
S0_DC_OFFSET = 0.0065


def test_the_hardware_dc_offset_would_swamp_the_room_floor():
    """The premise of the bug, stated as a number so it is not taken on faith."""
    assert dbfs(S0_DC_OFFSET) > FLOOR_DBFS + 15.0


def test_a_take_with_the_hardware_dc_offset_still_passes():
    """Measured raw, the offset sets both the floor and the speech level, every
    take scores ~0 dB of headroom, and the whole session is refused as too quiet."""
    report = verify("0001", make_take() + S0_DC_OFFSET, FLOOR)
    assert report.ok, report.failures
    assert report.dc_offset == pytest.approx(S0_DC_OFFSET, abs=1e-4)


def test_the_offset_does_not_move_the_measured_levels():
    clean = verify("0001", make_take(), FLOOR)
    biased = verify("0001", make_take() + S0_DC_OFFSET, FLOOR)
    assert biased.snr_db == pytest.approx(clean.snr_db, abs=0.2)
    assert biased.active_dbfs == pytest.approx(clean.active_dbfs, abs=0.2)


def test_clipping_is_counted_on_the_raw_signal_not_the_centred_one():
    """An offset large enough to push peaks into the rail is exactly the case
    that must be caught, and centring first would hide it."""
    audio = make_take()
    audio[2000] = CLIP_LEVEL
    assert not verify("0002", audio + 0.002, FLOOR).ok


def test_centring_an_empty_signal_does_not_raise():
    assert centred(np.zeros(0, dtype=np.float32)).size == 0


# --- the live meter --------------------------------------------------------


def test_the_meter_is_a_fixed_width_bar():
    line = meter(-47.2, -37.5, "OK")
    assert line.count("#") + line.count("-", 0, METER_WIDTH + 2) >= METER_WIDTH
    assert "-47.2 dBFS" in line and "Pk:  -37.5 dB" in line


def test_the_meter_fills_monotonically_with_level():
    widths = [meter(db, db, "x").count("#") for db in (-60.0, -45.0, -30.0, -15.0, 0.0)]
    assert widths == sorted(widths)
    assert widths[0] == 0 and widths[-1] == METER_WIDTH


def test_the_meter_clamps_outside_its_range():
    assert meter(-120.0, -120.0, "x").count("#") == 0
    assert meter(6.0, 6.0, "x").count("#") == METER_WIDTH


def test_live_status_flags_clipping_first():
    """A clipped take is unrecoverable, so it outranks any level reading."""
    assert "CLIP" in live_status(-3.0, FLOOR_DBFS, clipped=1)


def test_live_status_is_relative_to_the_room_floor_not_absolute_dbfs():
    """The BOYA peaks 16 dB under Table 22's target. A fixed "-20 dBFS or it is
    too quiet" rule would condemn every usable take on this chain."""
    assert "OK" in live_status(-36.0, FLOOR_DBFS, clipped=0)
    assert "QUIET" in live_status(-50.0, FLOOR_DBFS, clipped=0)
    assert "TOO QUIET" in live_status(-58.0, FLOOR_DBFS, clipped=0)


# --- the room floor --------------------------------------------------------


def room_tone(seconds: float = 5.0, floor_dbfs: float = FLOOR_DBFS) -> np.ndarray:
    rng = np.random.default_rng(7)
    return rng.normal(0.0, 10.0 ** (floor_dbfs / 20.0), int(seconds * CAPTURE_RATE)).astype(np.float32)


def test_the_floor_estimate_recovers_clean_room_tone():
    assert dbfs(noise_floor(room_tone())) == pytest.approx(FLOOR_DBFS, abs=1.0)


def test_one_transient_does_not_move_the_floor():
    """A live --check-room log in a genuinely quiet room still swung 20 dB window
    to window: a chair creak, a swallow, a keystroke. The session measures its
    floor once, and a floor read 15 dB high makes every take of the next 90
    minutes fail the level check."""
    from data.mix_noise import rms

    rng = np.random.default_rng(3)
    audio = room_tone()
    start, length = 2 * CAPTURE_RATE, int(0.15 * CAPTURE_RATE)
    audio[start : start + length] += rng.normal(0.0, 0.02, length).astype(np.float32)

    assert dbfs(rms(centred(audio))) > FLOOR_DBFS + 10.0  # what a plain RMS would report
    assert dbfs(noise_floor(audio)) == pytest.approx(FLOOR_DBFS, abs=1.0)


def test_the_floor_still_rises_when_the_room_is_genuinely_louder():
    """Robust must not mean blind: a fridge running is stationary, and it is
    exactly what the gate exists to catch."""
    assert dbfs(noise_floor(room_tone(floor_dbfs=-45.0))) == pytest.approx(-45.0, abs=1.0)


def test_the_floor_falls_back_to_rms_on_a_signal_too_short_to_frame():
    from data.mix_noise import rms

    tiny = room_tone(seconds=0.01)
    assert noise_floor(tiny) == pytest.approx(rms(centred(tiny)))


def test_the_percentile_is_low_enough_to_sit_under_speech():
    assert FLOOR_PERCENTILE <= 25.0


# --- mains hum -------------------------------------------------------------


def test_mains_share_separates_pickup_from_a_noisy_room():
    """The two have completely different fixes -- a cable versus a fridge -- and
    the tool has to tell the author which one they have."""
    t = np.arange(2 * CAPTURE_RATE) / CAPTURE_RATE
    broadband = room_tone(seconds=2.0, floor_dbfs=-45.0)
    hum = broadband + (0.01 * np.sin(2 * np.pi * 50.0 * t)).astype(np.float32)

    assert mains_share(broadband) < MAINS_SHARE_WARN
    assert mains_share(hum) > MAINS_SHARE_WARN


def test_mains_share_counts_harmonics_not_just_the_fundamental():
    """A charger's hum lands on 100 and 150 Hz as much as on 50."""
    t = np.arange(2 * CAPTURE_RATE) / CAPTURE_RATE
    harmonic = room_tone(seconds=2.0) + (0.01 * np.sin(2 * np.pi * 100.0 * t)).astype(np.float32)
    assert mains_share(harmonic) > MAINS_SHARE_WARN


def test_mains_share_is_zero_on_a_signal_too_short_to_resolve_50_hz():
    assert mains_share(room_tone(seconds=0.05)) == 0.0


# --- the speech level ------------------------------------------------------


def take_with_trailing_silence(
    total_seconds: float, speech_seconds: float = 2.0, amplitude: float = 0.012
) -> np.ndarray:
    """One fixed utterance, padded to `total_seconds` with room tone."""
    rng = np.random.default_rng(11)
    audio = rng.normal(0.0, FLOOR, int(total_seconds * CAPTURE_RATE)).astype(np.float32)
    n = int(speech_seconds * CAPTURE_RATE)
    t = np.arange(n) / CAPTURE_RATE
    burst = amplitude * np.sin(2 * np.pi * 180 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t))
    start = int(0.4 * CAPTURE_RATE)
    audio[start : start + n] += burst.astype(np.float32)
    return audio


def test_the_speech_level_does_not_depend_on_how_long_the_stream_ran():
    """`active_speech_rms` keeps every frame within 30 dB of the loudest, which on
    a mostly-silent take admits the room tone: the same utterance scored 20 dB in
    a 2.5 s take and 12.5 dB in a 16 s one, and the long take was refused for its
    length. This is the take the author actually lost to it."""
    levels = [dbfs(speech_level(take_with_trailing_silence(s), FLOOR)) for s in (2.5, 4.0, 8.0, 16.0)]
    assert max(levels) - min(levels) < 0.5


def test_a_long_take_now_passes_verification():
    report = verify("0001", take_with_trailing_silence(16.0), FLOOR)
    assert report.ok, report.failures
    assert report.snr_db > GOOD_SNR_DB


def test_the_level_still_reflects_a_genuinely_quiet_speaker():
    """Ignoring the silence must not mean ignoring the level."""
    loud = dbfs(speech_level(take_with_trailing_silence(4.0, amplitude=0.012), FLOOR))
    quiet = dbfs(speech_level(take_with_trailing_silence(4.0, amplitude=0.0012), FLOOR))
    assert loud - quiet == pytest.approx(20.0, abs=2.0)
    assert not verify("0003", take_with_trailing_silence(4.0, amplitude=0.0012), FLOOR).ok


def test_a_take_with_no_speech_reports_a_level_rather_than_raising():
    rng = np.random.default_rng(5)
    tone = rng.normal(0.0, FLOOR, 3 * CAPTURE_RATE).astype(np.float32)
    assert speech_level(tone, FLOOR) > 0.0
    assert not verify("0002", tone, FLOOR).ok
