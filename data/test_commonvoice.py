"""Tests for the Exp-0 sample (`data/commonvoice.py`).

Exp-0 reports WER **per accent bucket**, so the bucket label is not decoration:
it is the independent variable. Both bugs guarded here were in the first build
and both corrupted that variable silently.
"""

from __future__ import annotations

import json
from collections import Counter

import pytest

from data.commonvoice import (
    MANIFEST_PATH,
    MIN_BUCKET_ROWS,
    MIN_SECONDS,
    MAX_SECONDS,
    OTHER_BUCKET,
    SAMPLE_SIZE,
    SUMMARY_PATH,
    _first_accent,
    accent_bucket,
    eligible,
    populated_buckets,
    stratified_sample,
)

INDIA = "India and South Asia (India, Pakistan, Sri Lanka)"
AFRICA = "Southern African (South Africa, Zimbabwe, Namibia)"


def test_a_label_containing_commas_inside_parentheses_survives():
    """`split(",")[0]` truncated this to "India and South Asia (India" for 69 of
    the first build's 300 clips, silently inventing an accent group."""
    assert _first_accent(INDIA) == INDIA
    assert _first_accent(AFRICA) == AFRICA


def test_a_genuine_multi_accent_row_takes_the_first():
    """10 rows in this shard tick two accents. Counting the clip in both would
    double-count it in the per-bucket WER."""
    assert _first_accent(f"{INDIA},United States English") == INDIA
    assert _first_accent("United States English,England English") == "United States English"


def test_a_rare_free_text_label_pools_rather_than_becoming_a_stratum():
    """"ohio" and "northern cali" are one person's free text. A bucket of one has
    no reportable WER."""
    known = frozenset({"United States English"})
    assert accent_bucket("ohio", known) == OTHER_BUCKET
    assert accent_bucket("United States English", known) == "United States English"


def test_populated_buckets_applies_the_declared_floor():
    rows = [{"accents": "England English"}] * MIN_BUCKET_ROWS
    rows += [{"accents": "ohio"}] * (MIN_BUCKET_ROWS - 1)
    assert populated_buckets(rows) == frozenset({"England English"})


def test_disputed_or_unvalidated_clips_are_excluded():
    """A transcript with a down-vote has been disputed, and a disputed reference
    makes a meaningless WER."""
    rows = [
        {"accents": "England English", "up_votes": "2", "down_votes": "0"},  # keep
        {"accents": "England English", "up_votes": "1", "down_votes": "0"},  # too few
        {"accents": "England English", "up_votes": "5", "down_votes": "1"},  # disputed
        {"accents": "", "up_votes": "9", "down_votes": "0"},                 # no label
    ]
    assert len(eligible(rows)) == 1


def test_sampling_fills_small_buckets_before_the_large_one():
    """A uniform draw from this shard is 39% United States English and leaves
    several groups at zero --- the sample that would make the author's WER look
    unremarkable for the wrong reason."""
    rows = [{"accents": "United States English", "path": f"us{i}"} for i in range(200)]
    rows += [{"accents": "Welsh English", "path": f"cy{i}"} for i in range(MIN_BUCKET_ROWS)]
    counts = Counter(accent_bucket(r["accents"], populated_buckets(rows))
                     for r in stratified_sample(rows, 40, seed=42))
    assert counts["Welsh English"] == MIN_BUCKET_ROWS
    assert counts["United States English"] == 40 - MIN_BUCKET_ROWS


def test_sampling_is_reproducible():
    rows = [{"accents": "England English", "path": f"p{i}"} for i in range(60)]
    assert stratified_sample(rows, 20, 42) == stratified_sample(rows, 20, 42)


def test_sampling_never_returns_more_than_asked_for():
    rows = [{"accents": "England English", "path": f"p{i}"} for i in range(60)]
    assert len(stratified_sample(rows, 20, 42)) == 20
    assert len(stratified_sample(rows, 500, 42)) == 60  # asks for more than exists


# --- the built sample ------------------------------------------------------


@pytest.fixture(scope="module")
def sample():
    if not MANIFEST_PATH.is_file():
        pytest.skip("Exp-0 sample not built; run `python data/commonvoice.py`")
    return [json.loads(l) for l in MANIFEST_PATH.read_text().splitlines() if l.strip()]


def test_the_sample_is_three_hundred_clips(sample):
    assert len(sample) == SAMPLE_SIZE == 300


def test_every_clip_carries_a_reference_and_a_bucket(sample):
    for clip in sample:
        assert clip["sentence"].strip()
        assert clip["bucket"].strip()
        assert MIN_SECONDS <= clip["seconds"] <= MAX_SECONDS


def test_no_bucket_label_was_truncated_at_a_parenthesis(sample):
    """The regression that made 69 clips claim an accent group that does not exist."""
    for clip in sample:
        assert clip["bucket"].count("(") == clip["bucket"].count(")")


def test_the_sample_spans_many_speakers_not_many_clips_of_a_few(sample):
    """Exp-0 places the author as a percentile *within a multi-speaker
    distribution*; a distribution over ten speakers is not one."""
    assert len({c["client_id"] for c in sample}) > 200


def test_several_accent_buckets_are_populated(sample):
    buckets = Counter(c["bucket"] for c in sample)
    assert len(buckets) >= 10
    assert buckets[OTHER_BUCKET] < len(sample) * 0.1


def test_the_summary_matches_the_manifest(sample):
    summary = json.loads(SUMMARY_PATH.read_text())
    assert summary["clips"] == len(sample)
    assert sum(summary["buckets"].values()) == len(sample)
