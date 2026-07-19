"""Tests for digital SNR mixing (`data/mix_noise.py`).

The claims under test are the ones the Exp-3 causal statement rests on: that the
realised SNR is the requested SNR, that it is measured on the speech-active region
and not on the whole file, that the speech is untouched, and that every level of
one item is mixed from one noise excerpt.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from data.mix_noise import (
    ACTIVE_DYNAMIC_RANGE_DB,
    DEFAULT_SEED,
    PEAK_CEILING,
    SNR_LEVELS,
    MANIFEST_PATH,
    NoiseBank,
    NoiseBankError,
    TARGET_RATE,
    active_speech_rms,
    measure_snr,
    mix_at_snr,
    mix_one,
    rms,
    rng_for_item,
)

SR = TARGET_RATE


def tone(seconds: float, amplitude: float = 0.3, freq: float = 220.0) -> np.ndarray:
    t = np.arange(int(SR * seconds)) / SR
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(SR * seconds), dtype=np.float32)


def white(n: int, seed: int = 0, amplitude: float = 0.1) -> np.ndarray:
    return (np.random.default_rng(seed).standard_normal(n) * amplitude).astype(np.float32)


# --- level measurement -----------------------------------------------------


def test_active_speech_rms_ignores_leading_silence():
    """The whole point of §9.3's definition: run-in must not set the level."""
    speech = tone(1.0)
    padded = np.concatenate([silence(3.0), speech])

    assert active_speech_rms(padded, SR) == pytest.approx(active_speech_rms(speech, SR), rel=1e-3)
    # Full-file RMS, by contrast, is dragged down by a factor of two.
    assert rms(padded) < 0.6 * rms(speech)


def test_active_speech_rms_keeps_frames_within_the_dynamic_range():
    """A quiet-but-real passage counts; a passage below the floor does not."""
    loud = tone(0.5, amplitude=0.5)
    within = tone(0.5, amplitude=0.5 * 10 ** (-20 / 20.0))  # 20 dB down, inside 30
    below = tone(0.5, amplitude=0.5 * 10 ** (-50 / 20.0))  # 50 dB down, outside

    with_quiet = active_speech_rms(np.concatenate([loud, within]), SR)
    with_floor = active_speech_rms(np.concatenate([loud, below]), SR)

    assert with_quiet < active_speech_rms(loud, SR)
    assert with_floor == pytest.approx(active_speech_rms(loud, SR), rel=1e-3)
    assert ACTIVE_DYNAMIC_RANGE_DB == 30.0


def test_active_speech_rms_of_digital_silence_is_zero():
    assert active_speech_rms(silence(1.0), SR) == 0.0


# --- mixing ----------------------------------------------------------------


@pytest.mark.parametrize("snr_db", SNR_LEVELS)
def test_realised_snr_matches_request(snr_db):
    speech = np.concatenate([silence(0.5), tone(1.5), silence(0.5)])
    noise = white(speech.size)

    result = mix_at_snr(speech, noise, snr_db, SR)
    realised = measure_snr(result.audio / result.peak_attenuation, result.noise_gain * noise, SR)

    assert realised == pytest.approx(snr_db, abs=0.01)


def test_speech_is_never_scaled():
    """Exp-3 varies noise and holds everything else fixed, including level."""
    speech = np.concatenate([silence(0.5), tone(1.0)])
    noise = white(speech.size)

    recovered = [
        mix_at_snr(speech, noise, snr, SR).audio / mix_at_snr(speech, noise, snr, SR).peak_attenuation
        - mix_at_snr(speech, noise, snr, SR).noise_gain * noise
        for snr in SNR_LEVELS
    ]
    for got in recovered:
        assert np.allclose(got, speech, atol=1e-5)


def test_clipping_is_attenuated_not_clipped_and_snr_survives():
    speech = tone(1.0, amplitude=0.95)
    noise = white(speech.size, amplitude=0.8)

    result = mix_at_snr(speech, noise, 5, SR)

    assert result.peak_attenuation < 1.0
    assert float(np.max(np.abs(result.audio))) <= PEAK_CEILING + 1e-6
    realised = measure_snr(result.audio / result.peak_attenuation, result.noise_gain * noise, SR)
    assert realised == pytest.approx(5, abs=0.01)


def test_mixing_against_silence_is_refused():
    """Dividing by a silent reference would report an SNR that means nothing."""
    with pytest.raises(ValueError, match="no active region"):
        mix_at_snr(silence(1.0), white(SR), 10, SR)
    with pytest.raises(ValueError, match="silent"):
        mix_at_snr(tone(1.0), silence(1.0), 10, SR)


def test_length_mismatch_is_refused():
    with pytest.raises(ValueError, match="length mismatch"):
        mix_at_snr(tone(1.0), white(SR // 2), 10, SR)


# --- determinism and partitioning ------------------------------------------


def test_rng_is_stable_across_processes():
    """`hash()` is salted per process; the excerpt choice must not be."""
    first = rng_for_item("F001-hn01", DEFAULT_SEED).integers(0, 2**31, size=4)
    second = rng_for_item("F001-hn01", DEFAULT_SEED).integers(0, 2**31, size=4)
    other = rng_for_item("F001-hn02", DEFAULT_SEED).integers(0, 2**31, size=4)

    assert np.array_equal(first, second)
    assert not np.array_equal(first, other)


@pytest.mark.skipif(not MANIFEST_PATH.is_file(), reason="noise corpus not fetched")
class TestNoiseBank:
    def test_partitions_are_disjoint(self):
        """No excerpt the model was tuned against is also one it is tested against."""
        aug = NoiseBank(partition="aug")
        evaluation = NoiseBank(partition="eval")

        esc_aug = {k for k in aug.keys if k.startswith("esc50/")}
        esc_eval = {k for k in evaluation.keys if k.startswith("esc50/")}
        assert esc_aug and esc_eval
        assert esc_aug.isdisjoint(esc_eval)

        # DREGON is one file split by position, so the keys overlap but the samples
        # must not.
        n = 4 * SR
        head = aug.draw(n, np.random.default_rng(0))
        tail = evaluation.draw(n, np.random.default_rng(0))
        if head[1] == tail[1] == "dregon/DREGON_hovering_nosource_room2.wav":
            assert not np.array_equal(head[0], tail[0])

    def test_both_corpora_are_represented(self):
        bank = NoiseBank(partition="aug")
        drawn = {bank.draw(SR, np.random.default_rng(i))[1].split("/")[0] for i in range(60)}
        assert drawn == {"dregon", "esc50"}

    def test_one_excerpt_serves_every_snr_level(self):
        """Otherwise the SNR effect in Exp-3 is confounded with excerpt identity."""
        bank = NoiseBank(partition="eval")
        speech = np.concatenate([silence(0.25), tone(1.0), silence(0.25)])

        keys = {mix_one(speech, snr, bank, "0042", sample_rate=SR).noise_key for snr in SNR_LEVELS}
        assert len(keys) == 1

    def test_draw_is_reproducible(self):
        bank = NoiseBank(partition="aug")
        first, key_a = bank.draw(SR, rng_for_item("0042"))
        second, key_b = bank.draw(SR, rng_for_item("0042"))
        assert key_a == key_b
        assert np.array_equal(first, second)

    def test_unknown_partition_is_rejected(self):
        with pytest.raises(ValueError, match="partition must be"):
            NoiseBank(partition="train")

    def test_manifest_records_licence_for_every_noise_asset(self):
        """`dataset_card.md` §6 is only as good as this."""
        assets = json.loads(MANIFEST_PATH.read_text())["assets"]
        noise = {k: v for k, v in assets.items() if v.get("corpus") in {"DREGON", "ESC-50"}}
        assert noise
        for key, entry in noise.items():
            assert entry.get("licence"), key
            assert entry.get("url", "").startswith("http"), key
            assert len(entry.get("sha256", "")) == 64, key


def test_missing_manifest_names_the_fix(tmp_path):
    with pytest.raises(NoiseBankError, match="fetch_assets"):
        NoiseBank(manifest_path=tmp_path / "absent.json")
