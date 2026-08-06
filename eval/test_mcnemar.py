"""Tests for the paired-comparison runner.

`eval/stats.py` owns whether the test is computed correctly; this file owns whether
the right two vectors reach it. Every failure mode here produces a plausible number
rather than an exception, which is why they are worth a test each: predictions paired
by file position instead of item id, a family corrected at the wrong alpha, or a
recomputed accuracy quietly drifting from the published table.
"""

from __future__ import annotations

import json

import pytest

from eval.mcnemar import (FAMILY_ALPHA, PRIMARY_SPLIT, check_against_surface_b,
                          compare, load_correct, paired)
from eval.stats import bonferroni_alpha


class TestPaired:
    def test_aligns_on_item_id_not_on_insertion_order(self):
        first = {"0002": True, "0001": False}
        second = {"0001": False, "0002": True}
        a, b = paired(first, second)
        assert a == [False, True] == b          # id order 0001, 0002 for both

    def test_a_shuffled_second_file_still_pairs_correctly(self):
        first = {"a": True, "b": False, "c": True}
        second = {"c": True, "a": False, "b": False}
        a, b = paired(first, second)
        assert a == [True, False, True]
        assert b == [False, False, True]

    def test_different_item_sets_are_refused(self):
        with pytest.raises(SystemExit, match="different items"):
            paired({"0001": True}, {"0002": True})


class TestCompare:
    def test_reports_the_cells_and_the_exact_match_of_both_sides(self):
        first = {"1": True, "2": True, "3": False, "4": True}
        second = {"1": True, "2": False, "3": False, "4": False}
        row = compare("A", "B", first, second, family="model", role="primary",
                      split="test_golden", context="Q4_K_M", alpha=0.0167)
        assert (row["both_correct"], row["only_a"], row["only_b"], row["both_wrong"]) \
            == (1, 2, 0, 1)
        assert row["em_a"] == 0.75 and row["em_b"] == 0.25
        assert row["delta"] == 0.5
        assert row["n"] == 4

    def test_delta_follows_the_argument_order(self):
        first, second = {"1": False, "2": False}, {"1": True, "2": True}
        row = compare("A", "B", first, second, family="model", role="primary",
                      split="s", context="c", alpha=0.05)
        assert row["delta"] == -1.0


class TestFamilyCorrection:
    def test_both_confirmatory_families_are_three_wide(self):
        # If a family ever gains a comparison, alpha must move with it; this asserts
        # the pre-registered 0.0167 is derived, not typed in.
        assert bonferroni_alpha(3, family_alpha=FAMILY_ALPHA) == pytest.approx(0.05 / 3)

    def test_the_primary_split_is_the_recorded_speech_one(self):
        assert PRIMARY_SPLIT == "test_golden"


class TestProvenance:
    def test_a_drifted_exact_match_is_reported_not_swallowed(self, tmp_path, monkeypatch):
        import eval.mcnemar as module

        csv_path = tmp_path / "surface_b.csv"
        csv_path.write_text(
            "model,quant,grammar,split,exact_match\n"
            "m,Q4_K_M,on,test_golden,0.5000\n", encoding="utf-8")
        monkeypatch.setattr(module, "SURFACE_B", csv_path)

        matching = {("m", "Q4_K_M", "test_golden"): {"1": True, "2": False}}
        assert check_against_surface_b(matching) == []

        drifted = {("m", "Q4_K_M", "test_golden"): {"1": True, "2": True}}
        problems = check_against_surface_b(drifted)
        assert len(problems) == 1 and "1.0000" in problems[0]

    def test_predictions_with_no_published_row_are_flagged(self, tmp_path, monkeypatch):
        import eval.mcnemar as module

        csv_path = tmp_path / "surface_b.csv"
        csv_path.write_text("model,quant,grammar,split,exact_match\n", encoding="utf-8")
        monkeypatch.setattr(module, "SURFACE_B", csv_path)

        problems = check_against_surface_b({("m", "Q8_0", "test_ood"): {"1": True}})
        assert len(problems) == 1 and "no row in surface_b.csv" in problems[0]

    def test_a_nogrammar_row_is_not_matched_against_a_grammar_on_prediction(
            self, tmp_path, monkeypatch):
        # The ablation writes the same model/quant/split key with grammar=off. Reading
        # it here would compare Surface B against the ablation and call the difference
        # a provenance failure.
        import eval.mcnemar as module

        csv_path = tmp_path / "surface_b.csv"
        csv_path.write_text(
            "model,quant,grammar,split,exact_match\n"
            "m,Q4_K_M,off,test_golden,0.0000\n"
            "m,Q4_K_M,on,test_golden,1.0000\n", encoding="utf-8")
        monkeypatch.setattr(module, "SURFACE_B", csv_path)

        assert check_against_surface_b({("m", "Q4_K_M", "test_golden"): {"1": True}}) == []


class TestLoadCorrect:
    def test_scores_raw_against_gold_the_way_the_sweep_did(self, tmp_path, monkeypatch):
        import eval.mcnemar as module

        gold = '{"intent":"hover"}'
        path = tmp_path / "m-Q4_K_M_test_golden.jsonl"
        path.write_text("\n".join(json.dumps(row) for row in [
            {"id": "0001", "gold": gold, "raw": gold},
            # Key order and float spelling differ; canon() must call this a match.
            {"id": "0002", "gold": '{"intent":"move","dist":4.0}',
             "raw": '{"dist":4,"intent":"move"}'},
            {"id": "0003", "gold": gold, "raw": '{"intent":"land"}'},
        ]) + "\n", encoding="utf-8")
        monkeypatch.setattr(module, "PREDICTIONS", tmp_path)

        assert load_correct("m", "Q4_K_M", "test_golden") == {
            "0001": True, "0002": True, "0003": False}

    def test_a_missing_artefact_names_the_sweep_that_writes_it(self, tmp_path, monkeypatch):
        import eval.mcnemar as module
        monkeypatch.setattr(module, "PREDICTIONS", tmp_path)
        with pytest.raises(SystemExit, match="surface_b.py"):
            load_correct("absent", "Q4_K_M", "test_golden")
