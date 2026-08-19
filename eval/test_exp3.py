"""eval/exp3.py -- the per-item scoring rule and the statistics the analysis quotes.

The run itself needs whisper, llama-server and the mixed audio, and is exercised by
running it. What is tested here is what could be wrong silently: how a split
utterance scores, what counts as a safe failure, and the two claims the analysis
makes in prose about its own tests.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from eval.exp3 import arcsine_anova, cochran_q, endpoint, outcome, outputs


def _seg(correct: bool, dispatched: str) -> dict:
    return {"correct": correct, "dispatched": dispatched}


def test_no_segment_is_a_safe_failure() -> None:
    o = outcome([])
    assert (o.correct, o.safe, o.n_segments) == (False, True, 0)


def test_a_split_item_is_correct_only_if_every_segment_is() -> None:
    # golden 0003 in the smoke run: "proceed." -> takeoff, then the right move.
    o = outcome([_seg(False, "takeoff"), _seg(True, "move")])
    assert not o.correct
    assert o.correct_last          # the sensitivity rule would have credited it
    assert not o.safe              # a takeoff was dispatched


def test_every_segment_correct_is_correct() -> None:
    assert outcome([_seg(True, "abort"), _seg(True, "abort")]).correct


def test_a_failure_is_safe_only_if_nothing_unsafe_was_dispatched() -> None:
    assert outcome([_seg(False, "hover"), _seg(False, "unknown")]).safe
    assert not outcome([_seg(False, "hover"), _seg(False, "move")]).safe


def test_outputs_never_collide_between_the_two_halves(tmp_path: Path) -> None:
    assert outputs(tmp_path / "exp3_preds") == (tmp_path / "exp3.csv", tmp_path / "exp3_analysis.md")
    assert outputs(tmp_path / "exp3_pi_preds")[0] == tmp_path / "exp3_pi.csv"


def test_arcsine_on_binary_outcomes_leaves_the_anova_unchanged() -> None:
    """The analysis says the transform is a rescaling on 0/1 data. Hold it to that."""
    from scipy.stats import f_oneway

    rng = np.random.default_rng(0)
    matrix = (rng.random((200, 5)) < [0.8, 0.75, 0.7, 0.6, 0.5]).astype(int)
    plain = f_oneway(*[matrix[:, j].astype(float) for j in range(5)])
    result = arcsine_anova(matrix, list("abcde"))
    assert result["F"] == pytest.approx(plain.statistic)
    assert result["p"] == pytest.approx(plain.pvalue)
    assert len(result["pairs"]) == 10


def test_cochran_q_matches_statsmodels() -> None:
    contingency = pytest.importorskip("statsmodels.stats.contingency_tables")
    rng = np.random.default_rng(1)
    matrix = (rng.random((200, 5)) < [0.8, 0.75, 0.7, 0.6, 0.5]).astype(int)
    q, df, p = cochran_q(matrix)
    reference = contingency.cochrans_q(matrix)
    assert q == pytest.approx(reference.statistic)
    assert df == reference.df
    assert p == pytest.approx(reference.pvalue)


def test_cochran_q_with_no_discordance_is_not_a_division_by_zero() -> None:
    assert cochran_q(np.ones((10, 5), dtype=int)) == (0.0, 4, 1.0)


class _FakeEndpointer:
    """Records what it was fed; reports one segment once it has seen trailing zeros."""

    def __init__(self) -> None:
        self.fed: list[np.ndarray] = []

    def reset(self) -> None:
        self.fed = []

    def feed(self, chunk: np.ndarray) -> list:
        self.fed.append(chunk)
        return ["segment"] if chunk.size and not chunk.any() and len(self.fed) > 1 and self.fed[-2].any() else []


def test_endpoint_feeds_80_ms_chunks_and_closes_with_silence() -> None:
    fake = _FakeEndpointer()
    audio = np.full(16_000, 1000, dtype=np.int16)          # 1 s of "speech", no tail
    assert endpoint(audio, fake) == ["segment"]
    assert {c.size for c in fake.fed[:-1]} == {1280}
    assert sum(c.size for c in fake.fed) == 16_000 + 24_000  # + TAIL_S of zeros


def _row(segments: list[dict], reference: str = "hover now", gold: str = '{"intent":"hover"}') -> dict:
    return {"reference": reference, "gold": gold, "segments": segments}


def test_failure_causes_are_claimed_in_order() -> None:
    from eval.exp3 import CAUSES, failure_cause

    split = [{"transcript": "hover", "canonical": '{"intent":"hover"}'}] * 2
    # The parser's own error is claimed first, even for a split item.
    assert failure_cause(_row(split), text_correct=False) == CAUSES[0]
    assert failure_cause(_row([]), text_correct=True) == CAUSES[1]
    assert failure_cause(_row(split), text_correct=True) == CAUSES[2]
    perfect = [{"transcript": "Hover, now.", "canonical": '{"intent":"land"}'}]
    assert failure_cause(_row(perfect), text_correct=True) == CAUSES[3]
    misheard = [{"transcript": "hover cow", "canonical": '{"intent":"land"}'}]
    assert failure_cause(_row(misheard), text_correct=True) == CAUSES[4]
    slot = [{"transcript": "hover cow", "canonical": '{"intent":"hover","ids":[1]}'}]
    assert failure_cause(_row(slot), text_correct=True) == CAUSES[5]
