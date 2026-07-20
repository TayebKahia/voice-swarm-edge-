"""Tests for the offline 3:1 resample (`data/resample.py`).

`prd.md` D4 forbids ALSA `plug` and fixes soxr VHQ offline. The risk this file
guards is subtler than a wrong flag: two code paths that each resample correctly
but differently would put different bytes in front of `whisper.cpp` depending on
which one a consumer happened to use, and the WER difference would look like a
model effect.
"""

from __future__ import annotations

import json

import numpy as np
import pytest
import soundfile as sf
import soxr

from data.mix_noise import load_mono
from data.resample import (
    MAX_GAIN_DB,
    PEAK_CEILING_DBFS,
    SOURCE_RATE,
    TARGET_RATE,
    dbfs,
    read_master,
    resample,
    run,
)


def tone(seconds: float, amplitude: float, freq: float = 220.0, rate: int = SOURCE_RATE):
    t = np.arange(int(seconds * rate)) / rate
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def write_master(path, audio, rate=SOURCE_RATE):
    sf.write(str(path), audio, rate, subtype="PCM_16")


def test_the_conversion_is_three_to_one():
    out = resample(tone(1.0, 0.2))
    assert TARGET_RATE * 3 == SOURCE_RATE
    assert out.size == pytest.approx(TARGET_RATE, rel=1e-3)


def test_resample_matches_mix_noise_exactly(tmp_path):
    """`mix_noise.load_mono` is the other door into this corpus. If the two
    disagree, a file's samples depend on which module opened it."""
    path = tmp_path / "0001.wav"
    write_master(path, tone(0.8, 0.3))
    assert np.array_equal(resample(read_master(path)), load_mono(path))


def test_a_master_at_the_wrong_rate_is_refused_not_converted(tmp_path):
    """Recording at 16 kHz is the irreversible mistake (§0.2 conflict 3). This
    path must not quietly paper over it."""
    path = tmp_path / "0001.wav"
    write_master(path, tone(0.5, 0.2, rate=16_000), rate=16_000)
    with pytest.raises(SystemExit, match="expected 48000"):
        read_master(path)


def test_one_gain_for_the_session_preserves_relative_levels(tmp_path):
    source, out = tmp_path / "s1", tmp_path / "s1_16k"
    source.mkdir()
    write_master(source / "0001.wav", tone(1.0, 0.40))
    write_master(source / "0002.wav", tone(1.0, 0.10))  # 12 dB quieter, deliberately

    assert run(["--input", str(source), "--output", str(out)]) == 0
    manifest = json.loads((out / "resample_manifest.json").read_text())
    peaks = {r["id"]: r["peak_dbfs"] for r in manifest["files"]}

    assert peaks["0001"] == pytest.approx(PEAK_CEILING_DBFS, abs=0.2)
    # The 12 dB that separated them at capture is still 12 dB after normalising.
    assert peaks["0001"] - peaks["0002"] == pytest.approx(20 * np.log10(0.40 / 0.10), abs=0.3)


def test_masters_are_never_written_to(tmp_path):
    source, out = tmp_path / "s1", tmp_path / "s1_16k"
    source.mkdir()
    path = source / "0001.wav"
    write_master(path, tone(1.0, 0.25))
    before = path.read_bytes()
    run(["--input", str(source), "--output", str(out)])
    assert path.read_bytes() == before


def test_no_normalise_leaves_the_level_alone(tmp_path):
    source, out = tmp_path / "s1", tmp_path / "s1_16k"
    source.mkdir()
    write_master(source / "0001.wav", tone(1.0, 0.25))
    run(["--input", str(source), "--output", str(out), "--no-normalise"])
    manifest = json.loads((out / "resample_manifest.json").read_text())
    assert manifest["session_gain_db"] == pytest.approx(0.0, abs=1e-6)
    assert manifest["normalised"] is False


def test_an_absurdly_quiet_session_is_reported_not_amplified(tmp_path):
    """A 40 dB lift is a broken capture chain, not a level to correct."""
    source, out = tmp_path / "s1", tmp_path / "s1_16k"
    source.mkdir()
    write_master(source / "0001.wav", tone(1.0, 0.0005))
    with pytest.raises(SystemExit, match="cap"):
        run(["--input", str(source), "--output", str(out)])
    assert MAX_GAIN_DB == 24.0


def test_the_manifest_pins_each_master_by_hash(tmp_path):
    source, out = tmp_path / "s1", tmp_path / "s1_16k"
    source.mkdir()
    write_master(source / "0001.wav", tone(1.0, 0.25))
    run(["--input", str(source), "--output", str(out)])
    record = json.loads((out / "resample_manifest.json").read_text())["files"][0]
    assert len(record["master_sha256"]) == 64
    assert record["active_speech_dbfs"] < 0.0


def test_the_output_is_16_bit_16_khz_mono(tmp_path):
    source, out = tmp_path / "s1", tmp_path / "s1_16k"
    source.mkdir()
    write_master(source / "0001.wav", tone(1.0, 0.25))
    run(["--input", str(source), "--output", str(out)])
    info = sf.info(str(out / "0001.wav"))
    assert (info.samplerate, info.channels, info.subtype) == (TARGET_RATE, 1, "PCM_16")
