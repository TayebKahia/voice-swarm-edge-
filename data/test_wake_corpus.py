"""Tests for the Branch A wake corpus (`data/wake_corpus.py`).

Two kinds of property. The first is membership: FR-6 fixes Branch A at exactly
two phrases, and a third class added later is a specification change, not a
tuning knob. The second is isolation: Exp-2 reports a per-class ROC with a
declared operating point, and every way that ROC can quietly become a statement
about memorisation is closed here rather than discovered at NFR-16.

The manifest tests run against the corpus on disk and skip when it has not been
built, so a clean clone still passes the suite.
"""

from __future__ import annotations

import json
from collections import Counter

import numpy as np
import pytest

from data.wake_corpus import (
    ADVERSARIAL_PHRASES,
    AUGS_PER_BASE,
    BASES_PER_VOICE,
    CLIP_SAMPLES,
    CLIP_SECONDS,
    MANIFEST_PATH,
    NEGATIVE_HOURS,
    SPLIT_SHARES,
    TARGET_RATE,
    WAKE_CLASSES,
    assign_splits,
    place_in_window,
)


# --- membership (FR-6) -----------------------------------------------------


def test_exactly_two_classes_and_they_are_the_fail_safe_ones():
    """Both qualifying intents make the swarm do *less*, so a false accept is
    always fail-safe. That is contribution C4 and it is why no movement verb may
    ever join this list."""
    assert list(WAKE_CLASSES.values()) == ["swarm hold", "swarm abort"]


def test_no_adversarial_phrase_is_one_of_the_wake_words():
    """A near-miss that *is* the keyword would train the spotter to reject it."""
    assert not set(ADVERSARIAL_PHRASES) & set(WAKE_CLASSES.values())


def test_the_near_misses_cover_what_no_public_corpus_contains():
    """Neither LibriSpeech nor Speech Commands says "swarm", and nothing in
    either begins a phrase with "hold"."""
    phrases = set(ADVERSARIAL_PHRASES)
    assert {"swarm", "hold", "abort"} <= phrases
    assert any(p.startswith("swarm ") for p in phrases)
    assert any(p.startswith("hold ") for p in phrases)


# --- splits ----------------------------------------------------------------


def test_split_shares_sum_to_one():
    assert sum(SPLIT_SHARES.values()) == pytest.approx(1.0)


def test_assign_splits_covers_every_key_exactly_once():
    keys = [f"base/{i:03d}" for i in range(120)]
    assignment = assign_splits(keys, seed=42, salt="t")
    assert set(assignment) == set(keys)
    assert set(assignment.values()) <= set(SPLIT_SHARES)


def test_assign_splits_honours_the_shares():
    keys = [f"base/{i:03d}" for i in range(100)]
    counts = Counter(assign_splits(keys, seed=42, salt="t").values())
    assert counts["train"] == 70 and counts["val"] == 10 and counts["test"] == 20


def test_assign_splits_is_stable_and_salted():
    keys = [f"base/{i:03d}" for i in range(60)]
    assert assign_splits(keys, 42, "a") == assign_splits(keys, 42, "a")
    assert assign_splits(keys, 42, "a") != assign_splits(keys, 42, "b")


def test_adding_a_key_does_not_re_roll_the_others():
    """Ordering by a hash of the key rather than by position means one more
    speaker does not reshuffle a corpus that has already been built."""
    keys = [f"base/{i:03d}" for i in range(200)]
    before = assign_splits(keys, 42, "t")
    after = assign_splits(keys + ["base/999"], 42, "t")
    moved = sum(1 for k in keys if before[k] != after[k])
    assert moved <= 3  # only the largest-remainder boundary may shift


# --- placement -------------------------------------------------------------


def test_the_window_is_always_the_declared_length():
    rng = np.random.default_rng(0)
    for length in (int(0.4 * TARGET_RATE), CLIP_SAMPLES, 3 * CLIP_SAMPLES):
        window, _ = place_in_window(np.ones(length, dtype=np.float32), rng)
        assert window.size == CLIP_SAMPLES


def test_the_keyword_is_not_always_centred():
    """A model trained on centred keywords learns the centring; the deployed
    sliding buffer offers no such guarantee."""
    rng = np.random.default_rng(0)
    audio = np.ones(int(1.0 * TARGET_RATE), dtype=np.float32)
    offsets = {place_in_window(audio, rng)[1] for _ in range(40)}
    assert len(offsets) > 10


def test_a_clip_longer_than_the_window_is_cropped_not_squeezed():
    rng = np.random.default_rng(0)
    window, offset = place_in_window(np.ones(3 * CLIP_SAMPLES, dtype=np.float32), rng)
    assert offset == 0.0
    assert np.all(window == 1.0)


# --- the built corpus ------------------------------------------------------


@pytest.fixture(scope="module")
def manifest():
    if not MANIFEST_PATH.is_file():
        pytest.skip("wake corpus not built; run `python data/wake_corpus.py`")
    return json.loads(MANIFEST_PATH.read_text())


def test_both_classes_have_the_declared_number_of_clips(manifest):
    expected = 3 * BASES_PER_VOICE * AUGS_PER_BASE
    for label in WAKE_CLASSES:
        assert manifest["summary"][label]["clips"] == expected


def test_there_are_at_least_three_hours_of_negatives(manifest):
    """NFR-15's floor. `01_feasibility_audit.md` and the roadmap both name it."""
    assert manifest["summary"]["neg"]["hours"] >= 3.0
    assert NEGATIVE_HOURS >= 3.0


def test_no_base_rendition_straddles_two_splits(manifest):
    """The augmented variants of one rendition are near-duplicates. Split them
    and the held-out ROC describes memorisation."""
    splits: dict[str, set[str]] = {}
    for clip in manifest["clips"]:
        splits.setdefault(clip["base"], set()).add(clip["split"])
    straddling = {base for base, seen in splits.items() if len(seen) > 1}
    assert not straddling, sorted(straddling)[:5]


def test_the_held_out_split_hears_esc50_clips_the_trained_splits_never_did(manifest):
    """Train/val draw the `aug` partition, test draws `eval` --- the same
    partition `mix_noise.py` defines and `check_leakage.py` gates.

    Only the ESC-50 half is checkable from the keys. DREGON is a single
    continuous flight split by *position* (first 70% augments, last 30%
    evaluates), so both partitions legitimately report the same filename and a
    key-disjointness assertion over it would fail on correct behaviour. The
    byte-level disjointness of those two ranges is asserted where it can be:
    `test_mix_noise.py::TestNoiseBank::test_partitions_are_disjoint`.
    """
    used: dict[str, set[str]] = {"train": set(), "val": set(), "test": set()}
    for clip in manifest["clips"]:
        key = clip.get("noise_key")
        if key and key.startswith("esc50/"):
            used[clip["split"]].add(key)
    trained = used["train"] | used["val"]
    assert trained and used["test"]
    assert not (trained & used["test"])


def test_every_clip_records_which_noise_bank_it_drew_from(manifest):
    """The field the ESC-50 check cannot supply for DREGON. Written from the bank
    that was actually used, so the manifest states the partition rather than
    leaving a reader to infer it from the split."""
    expected = manifest["noise_partition"]
    for clip in manifest["clips"]:
        if clip.get("noise_key"):
            assert clip["noise_partition"] == expected[clip["split"]]


def test_the_held_out_split_hears_rooms_the_trained_splits_never_did(manifest):
    used: dict[str, set[str]] = {"train": set(), "val": set(), "test": set()}
    for clip in manifest["clips"]:
        if clip.get("rir"):
            used[clip["split"]].add(clip["rir"])
    trained = used["train"] | used["val"]
    assert trained and used["test"]
    assert not (trained & used["test"])


def test_negatives_do_not_share_a_speaker_across_splits(manifest):
    """LibriSpeech negatives are grouped by speaker and Speech Commands by its own
    speaker hash: one voice must not appear on both sides of the measurement."""
    splits: dict[str, set[str]] = {}
    for clip in manifest["clips"]:
        if clip["label"] == "neg":
            splits.setdefault(clip["base"], set()).add(clip["split"])
    assert not {g for g, seen in splits.items() if len(seen) > 1}


def test_every_negative_source_is_represented(manifest):
    sources = set(manifest["summary"]["neg"]["sources"])
    assert sources == {"librispeech", "speech_commands", "adversarial"}


def test_the_manifest_records_provenance_for_every_clip(manifest):
    for clip in manifest["clips"][:200]:
        assert clip["seconds"] == CLIP_SECONDS
        assert clip["split"] in SPLIT_SHARES
        assert "gain_db" in clip
